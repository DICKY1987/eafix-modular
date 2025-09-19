# indicators/friday_vol_indicator.py
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, Dict, Callable
import pytz

CHI = pytz.timezone("America/Chicago")
UTC = pytz.UTC

@dataclass
class FridayVolIndicatorConfig:
    percent_threshold: float = 1.0       # e.g., 1.0 = 1%
    start_local_hhmm: str = "07:30"      # 07:30 America/Chicago
    end_local_hhmm: str   = "14:00"      # 14:00 America/Chicago

    @property
    def start_local(self) -> time:
        hh, mm = self.start_local_hhmm.split(":")
        return time(int(hh), int(mm))

    @property
    def end_local(self) -> time:
        hh, mm = self.end_local_hhmm.split(":")
        return time(int(hh), int(mm))

class FridayVolIndicator:
    """
    Indicates when the percentage move between 07:30→14:00 America/Chicago on Fridays
    exceeds the configured threshold. This is a pure indicator - it does not execute trades.
    """

    def __init__(self, cfg: FridayVolIndicatorConfig):
        self.cfg = cfg
        # Track when indicator last fired per symbol to provide state info
        self._last_triggered: Dict[str, datetime.date] = {}
        self._last_values: Dict[str, Dict] = {}

    def _current_chicago(self, now_utc: Optional[datetime] = None) -> datetime:
        now_utc = now_utc or datetime.utcnow().replace(tzinfo=UTC)
        return now_utc.astimezone(CHI)

    def _window_bounds_utc(self, ref_utc: Optional[datetime] = None):
        now_chi = self._current_chicago(ref_utc)
        # Ensure we compute for "today" in Chicago
        start_chi = CHI.localize(datetime.combine(now_chi.date(), self.cfg.start_local))
        end_chi   = CHI.localize(datetime.combine(now_chi.date(), self.cfg.end_local))
        return start_chi.astimezone(UTC), end_chi.astimezone(UTC), now_chi

    def _is_friday(self, chi_dt: datetime) -> bool:
        # Monday=0 ... Sunday=6
        return chi_dt.weekday() == 4

    def get_indicator_state(
        self,
        symbol: str,
        get_price_at: Callable[[datetime], float],
        now_utc: Optional[datetime] = None
    ) -> Dict:
        """
        Returns the current indicator state for the symbol.
        
        Parameters
        ----------
        symbol : str
        get_price_at : callable(dt_utc: datetime) -> float
            Price accessor that returns midpoint/close nearest <= dt_utc.
        now_utc : Optional[datetime]
            For testing or deterministic runs.
            
        Returns
        -------
        dict
            Indicator state with status, values, and metadata
        """
        start_utc, end_utc, now_chi = self._window_bounds_utc(now_utc)
        
        # Base state
        state = {
            "indicator": "FridayVolIndicator",
            "symbol": symbol,
            "timestamp_utc": (now_utc or datetime.utcnow().replace(tzinfo=UTC)).isoformat(),
            "status": "WAITING",  # WAITING, MONITORING, TRIGGERED, EXPIRED
            "signal_active": False,
            "values": {},
            "meta": {
                "is_friday": self._is_friday(now_chi),
                "window_local": f"{self.cfg.start_local_hhmm}→{self.cfg.end_local_hhmm} America/Chicago",
                "threshold_pct": self.cfg.percent_threshold,
                "window_start_utc": start_utc.isoformat(),
                "window_end_utc": end_utc.isoformat(),
            }
        }

        # Only process on Fridays
        if not self._is_friday(now_chi):
            state["status"] = "WAITING"
            state["meta"]["reason"] = "Not Friday"
            return state

        end_local_dt = CHI.localize(datetime.combine(now_chi.date(), self.cfg.end_local))
        
        # Before window end - monitoring
        if now_chi < end_local_dt:
            state["status"] = "MONITORING"
            state["meta"]["reason"] = "Window active, monitoring for threshold breach"
            
            # Try to get current values for monitoring
            try:
                p_start = get_price_at(start_utc)
                p_current = get_price_at(now_utc or datetime.utcnow().replace(tzinfo=UTC))
                
                if p_start and p_current and p_start > 0:
                    current_pct = abs((p_current - p_start) / p_start) * 100.0
                    direction = "UP" if p_current > p_start else "DOWN"
                    
                    state["values"] = {
                        "p_start": p_start,
                        "p_current": p_current,
                        "current_pct_change": round(current_pct, 3),
                        "direction": direction,
                        "threshold_met": current_pct >= self.cfg.percent_threshold
                    }
                    
                    # Signal if threshold already breached during monitoring
                    if current_pct >= self.cfg.percent_threshold:
                        state["signal_active"] = True
                        state["status"] = "TRIGGERED"
                        
            except Exception as e:
                state["meta"]["price_error"] = str(e)
                
            return state

        # After window end - check for final signal
        try:
            p_start = get_price_at(start_utc)
            p_end   = get_price_at(end_utc)
            
            if not p_start or not p_end or p_start <= 0:
                state["status"] = "EXPIRED"
                state["meta"]["reason"] = "Insufficient price data"
                return state

            pct = abs((p_end - p_start) / p_start) * 100.0
            direction = "UP" if p_end > p_start else "DOWN"
            
            state["values"] = {
                "p_start": p_start,
                "p_end": p_end,
                "pct_change": round(pct, 3),
                "direction": direction,
                "threshold_met": pct >= self.cfg.percent_threshold
            }
            
            # Check if signal should be active
            if pct >= self.cfg.percent_threshold:
                # Only trigger once per Friday per symbol
                if self._last_triggered.get(symbol) != now_chi.date():
                    state["signal_active"] = True
                    state["status"] = "TRIGGERED"
                    self._last_triggered[symbol] = now_chi.date()
                    self._last_values[symbol] = state["values"].copy()
                else:
                    state["signal_active"] = False
                    state["status"] = "TRIGGERED_PREVIOUSLY"
                    state["meta"]["reason"] = "Already triggered today"
                    # Include previous values
                    if symbol in self._last_values:
                        state["values"].update(self._last_values[symbol])
            else:
                state["signal_active"] = False
                state["status"] = "EXPIRED"
                state["meta"]["reason"] = f"Below threshold: {pct:.3f}% < {self.cfg.percent_threshold}%"
                
        except Exception as e:
            state["status"] = "ERROR"
            state["meta"]["error"] = str(e)

        return state

    def is_signal_active(
        self,
        symbol: str,
        get_price_at: Callable[[datetime], float],
        now_utc: Optional[datetime] = None
    ) -> bool:
        """
        Simple boolean check if the indicator signal is currently active.
        """
        state = self.get_indicator_state(symbol, get_price_at, now_utc)
        return state.get("signal_active", False)

    def get_signal_strength(
        self,
        symbol: str,
        get_price_at: Callable[[datetime], float],
        now_utc: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Returns the signal strength (percentage change) if signal is active, else None.
        """
        state = self.get_indicator_state(symbol, get_price_at, now_utc)
        if state.get("signal_active", False):
            return state.get("values", {}).get("pct_change")
        return None
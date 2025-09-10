
# signals/friday_vol_signal.py
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, Dict, Callable
import pytz

CHI = pytz.timezone("America/Chicago")
UTC = pytz.UTC

@dataclass
class FridayVolSignalConfig:
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

class FridayVolSignal:
    """
    Evaluates the %% move between 07:30→14:00 America/Chicago on Fridays.
    Emits a one-shot EXECUTE signal when |pct_change| >= threshold.
    """

    def __init__(self, cfg: FridayVolSignalConfig):
        self.cfg = cfg
        # Keeps last-triggered Friday date per symbol to avoid re-firing
        self._last_triggered: Dict[str, datetime.date] = {}

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

    def evaluate(
        self,
        symbol: str,
        get_price_at: Callable[[datetime], float],
        now_utc: Optional[datetime] = None
    ) -> Optional[dict]:
        """
        Parameters
        ----------
        symbol : str
        get_price_at : callable(dt_utc: datetime) -> float
            Your price accessor that returns midpoint/close nearest <= dt_utc.
        now_utc : Optional[datetime]
            For testing or deterministic runs.
        Returns
        -------
        dict | None
            Normalized signal message if fired, else None.
        """
        start_utc, end_utc, now_chi = self._window_bounds_utc(now_utc)

        # Only act on Fridays and only after the window end
        end_local_dt = CHI.localize(datetime.combine(now_chi.date(), self.cfg.end_local))
        if not self._is_friday(now_chi):
            return None
        if now_chi < end_local_dt:
            return None

        # One-shot guard
        if self._last_triggered.get(symbol) == now_chi.date():
            return None

        # Pull prices at the boundaries
        p_start = get_price_at(start_utc)
        p_end   = get_price_at(end_utc)
        if not p_start or not p_end or p_start <= 0:
            return None

        pct = abs((p_end - p_start) / p_start) * 100.0
        if pct < self.cfg.percent_threshold:
            return None

        self._last_triggered[symbol] = now_chi.date()
        direction = "BUY" if p_end > p_start else "SELL"

        return {
            "type": "EXECUTE",
            "source": "Signal.FridayMove",
            "symbol": symbol,
            "direction": direction,
            "strength": round(pct, 3),
            "meta": {
                "window_local": f"{self.cfg.start_local_hhmm}→{self.cfg.end_local_hhmm} America/Chicago",
                "pct_change": round(pct, 3),
                "p_start": p_start,
                "p_end": p_end,
            },
            "risk_profile": "FRIDAY_VOL_EDGE_V1",
            "ttl_sec": 300,
        }

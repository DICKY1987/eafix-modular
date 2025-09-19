Love this—here’s how I’d refactor that “Friday 7:30→2:00 CST %-move” concept so it cleanly fits your current architecture (single MT4 Execution Engine EA, Python analytics brain, no Excel, MT4↔Python comms, DDE/price feed into Python, signals out of Python).

Plan (tight + production-oriented)

Shift the logic to Python (Analytics Engine) and keep MT4’s EA as a thin executor.
Python will:

ingest live prices (your DDE/bridge feed),

compute the Friday window return (07:30 → 14:00 America/Chicago),

compare to a configurable threshold,

emit a normalized “EXECUTE” signal to the EA.

MT4 will only listen and execute—no time math or fragile bar lookups in MQL4 anymore.

What this gives you

One truth source for business logic (Python), consistent across all pairs.

Correct timezone handling (America/Chicago with DST) in Python.

Reusability: you can clone this as Signal.FridayMove and later add Signal.FedDayMove, etc.

Observability: Python logs, counters, and a “Signals” panel in your GUI.

No re-triggering: per-Friday/per-symbol guard.

Python side (drop-in module)

Create signals/friday_vol_signal.py:

# signals/friday_vol_signal.py
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional, Dict
import pytz

CHI = pytz.timezone("America/Chicago")
UTC = pytz.UTC

@dataclass
class FridayVolSignalConfig:
    percent_threshold: float = 1.0       # e.g. 1.0 = 1%
    start_local: time = time(7, 30)      # 07:30 America/Chicago
    end_local: time   = time(14, 0)      # 14:00 America/Chicago
    min_bars: int     = 3                # sanity guard for data sufficiency
    bar_tf_secs: int  = 900              # 15m aggregation if you’re bar-based

class FridayVolSignal:
    """
    Evaluates the % move between 07:30→14:00 America/Chicago on Fridays.
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

    def evaluate(self, symbol: str, get_price_at: callable, now_utc: Optional[datetime] = None):
        """
        Parameters
        ----------
        symbol : str
        get_price_at : callable(dt_utc: datetime) -> float
            Your price accessor that returns a midpoint/close near dt_utc.
            Implement it on top of your DDE/tick cache (nearest prior tick).
        now_utc : Optional[datetime]
            For testing or deterministic runs.
        Returns
        -------
        dict | None
            Normalized signal message if fired, else None.
        """
        start_utc, end_utc, now_chi = self._window_bounds_utc(now_utc)

        # Only act on Fridays and only after the window end
        if not self._is_friday(now_chi):
            return None
        if now_chi < CHI.localize(datetime.combine(now_chi.date(), self.cfg.end_local)):
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
        # Normalized signal payload for the Execution Engine EA
        return {
            "type": "EXECUTE",
            "source": "Signal.FridayMove",
            "symbol": symbol,
            "direction": direction,
            "strength": pct,  # you can map this into risk sizing rules
            "meta": {
                "window_local": f"{self.cfg.start_local.strftime('%H:%M')}→{self.cfg.end_local.strftime('%H:%M')} America/Chicago",
                "pct_change": round(pct, 3),
                "p_start": p_start,
                "p_end": p_end,
            },
            "risk_profile": "FRIDAY_VOL_EDGE_V1",
            "ttl_sec": 300,   # optional: message expires if not acted on
        }

Minimal integration in your engine loop

In your indicator_engine.py (or wherever signals poll):

# indicator_engine.py (excerpt)
from signals.friday_vol_signal import FridayVolSignal, FridayVolSignalConfig
from bridge.outbound import send_signal_to_mt4  # your existing socket/named-pipe/CSV sender
from price_store import nearest_price_at_utc    # your accessor over DDE/tick cache

friday_sig = FridayVolSignal(FridayVolSignalConfig(
    percent_threshold=1.0,  # make this user-configurable (settings.json)
))

def poll_signals(now_utc=None):
    for symbol in live_symbols():  # your configured list
        msg = friday_sig.evaluate(
            symbol=symbol,
            get_price_at=lambda dt: nearest_price_at_utc(symbol, dt),
            now_utc=now_utc
        )
        if msg:
            log.info(f"[Signal.FridayMove] {symbol} {msg['direction']} {msg['meta']}")
            send_signal_to_mt4(msg)


Note: nearest_price_at_utc should return the last known price at or before the requested timestamp (use your tick cache / 15m aggregates). If you store OHLC, use the open of the 07:30 bucket and the close of the 14:00 bucket (consistent with your original spec).

MQL4 side (Execution Engine EA)

You already have a one-EA-per-symbol pattern. Add a lightweight “inbox” poll + execute. Example:

// ExecutionEngine.mq4 (excerpt)

// Pseudocode for your existing bridge:
// - BridgePoll() reads next JSON message for this symbol (socket/pipe/file)
// - ExecuteOrder(direction, risk_profile) encapsulates all sizing/SL/TP logic

void OnTick()
{
   // ... your existing engine logic ...

   string msg;
   if (BridgePoll(Symbol(), msg))
   {
      // Parse minimal fields; keep MT4 thin
      string type = json_get_string(msg, "type");
      if (type == "EXECUTE")
      {
         string direction   = json_get_string(msg, "direction");      // "BUY"|"SELL"
         string riskProfile = json_get_string(msg, "risk_profile");    // "FRIDAY_VOL_EDGE_V1"
         // Optional: strength-based sizing handled in Python or here via mapping
         ExecuteOrder(direction, riskProfile);
      }
   }
}


If you currently use CSV drop + file watcher, swap BridgePoll to your CSV reader.

If you use sockets/named pipes DLL, keep it identical to your other signals—this stays consistent.

Config (put in your settings.json)
{
  "signals": {
    "FridayMove": {
      "enabled": true,
      "percent_threshold": 1.0,
      "start_local": "07:30",
      "end_local": "14:00",
      "risk_profile": "FRIDAY_VOL_EDGE_V1"
    }
  }
}


Wire the loader to hydrate FridayVolSignalConfig at startup.

GUI tweaks (Main/Signals tab)

Signals panel row:

Name: FridayMove

State: Waiting / Eligible (after 14:00 CST on Friday) / Fired

Symbol, Direction, %Change, p_start, p_end, last_fired_date

Overlay: A thin shaded band from 07:30→14:00 (Chicago) on intraday charts.

Health indicator: show green when both boundary prices are present; amber if any side missing (data sufficiency check).

Testing (fast + deterministic)

Add unit tests for:

Non-Friday → no signal

Friday < 14:00 CHI → no signal

Friday ≥ 14:00 CHI + pct < threshold → no signal

Friday ≥ 14:00 CHI + pct ≥ threshold → emits once (guard prevents re-fire)

DST cutover weeks (mock America/Chicago dates)

Skeleton:

def test_friday_signal_triggers_once(mock_prices, freeze_time_utc):
    cfg = FridayVolSignalConfig(percent_threshold=1.0)
    sig = FridayVolSignal(cfg)
    # Arrange mock price accessor: returns p_start, p_end to produce > 1%
    msg1 = sig.evaluate("EURUSD", get_price_at=mock_prices, now_utc=freeze_time_utc)
    assert msg1 and msg1["type"] == "EXECUTE"
    msg2 = sig.evaluate("EURUSD", get_price_at=mock_prices, now_utc=freeze_time_utc)
    assert msg2 is None

Optional refinements

Directional filter: only trigger if move up or down (configurable).

Strength→risk: map strength (% change) to position multiplier or SL distance in Python before sending.

Portfolio mode: require N-of-M symbols to align before “global execute”.

Pre-commit drift: add a pre-14:00 heads-up metric in the UI so you can see whether the move is approaching threshold.

TL;DR (drop-in)

Put the business logic in Python (signals/friday_vol_signal.py).

Poll it from your indicator engine, send a normalized EXECUTE message.

Keep the EA thin: just read the message and call ExecuteOrder.

Wire settings.json, add a Signals panel row, and ship.

If you want, I can also emit a ready-to-copy bridge/outbound.py sender stub and a minimal price_store.nearest_price_at_utc example next.

You said:
yes aLL
ChatGPT said:
Thought for a second
Thought for 13s

Perfect — I wired up the full “Friday 7:30→2:00 CST %-move” signal into your current Python↔MT4 architecture (no Excel, thin EA, Python brains). You’ve got new, ready-to-drop-in files plus a minimal integration guide.

What I shipped for you

New Python signal module (production-ready, DST-safe):

signals/friday_vol_signal.py

Tiny test to verify behavior:

tests/test_friday_vol_signal.py

Merge notes / patch steps:

INTEGRATE_FRIDAY_MOVE.md

Safe settings overlay you can merge into your existing settings:

settings.friday_move.overlay.json

Optional outbound stub (if you need a placeholder sender):

bridge/outbound.py

Download the artifacts

signals/friday_vol_signal.py

tests/test_friday_vol_signal.py

INTEGRATE_FRIDAY_MOVE.md

settings.friday_move.overlay.json

bridge/outbound.py

How this fits your system (quick)

Python computes the window return (07:30→14:00 America/Chicago) and checks it against a configurable % threshold. If met, it emits a normalized EXECUTE message with direction + strength.

EA stays thin: just reads the message and calls your existing ExecuteOrder(direction, risk_profile).

Config-driven: add "FridayMove" under signals in settings.json (overlay provided).

UI: add a Signals row to show Waiting/Eligible/Fired + symbol, direction, % change, p_start, p_end, last fired.

Where to hook it (summary)

Config
Merge settings.friday_move.overlay.json into your settings.json to enable and set thresholds.

Indicator loop (indicator_engine.py)
Import and instantiate:

from signals.friday_vol_signal import FridayVolSignal, FridayVolSignalConfig

friday_cfg = FridayVolSignalConfig(
    percent_threshold=settings.signals["FridayMove"]["percent_threshold"],
    start_local_hhmm=settings.signals["FridayMove"]["start_local"],
    end_local_hhmm=settings.signals["FridayMove"]["end_local"],
)
friday_sig = FridayVolSignal(friday_cfg)


Then poll:

msg = friday_sig.evaluate(
    symbol=symbol,
    get_price_at=lambda dt, s=symbol: nearest_price_at_utc(s, dt),
    now_utc=None,  # default uses current UTC
)
if msg:
    send_signal_to_mt4(msg)


Price accessor
Use your DDE/tick cache to implement nearest_price_at_utc(symbol, dt) (return last price at or before dt).
If you maintain 15-min bars, use the open at 07:30 and close at 14:00.

EA
On inbound "type":"EXECUTE": read "direction" (BUY/SELL) + "risk_profile":"FRIDAY_VOL_EDGE_V1" and call your ExecuteOrder.

Tests you can run

The included test checks:

triggers once on a Friday after 14:00 CHI when % ≥ threshold

does not trigger below threshold
Run it with your Python test runner (or quickly adapt run_all_tests.py if you prefer).
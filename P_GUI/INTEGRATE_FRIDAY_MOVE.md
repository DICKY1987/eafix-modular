
### Integration Guide (Friday Move Signal)

1) settings.json (add this block under "signals")
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

2) indicator_engine.py (import + wire up)

from signals.friday_vol_signal import FridayVolSignal, FridayVolSignalConfig
# ensure you have a price accessor like nearest_price_at_utc(symbol, dt_utc)

friday_cfg = FridayVolSignalConfig(
    percent_threshold=settings.signals["FridayMove"]["percent_threshold"],
    start_local_hhmm=settings.signals["FridayMove"]["start_local"],
    end_local_hhmm=settings.signals["FridayMove"]["end_local"],
)
friday_sig = FridayVolSignal(friday_cfg)

def poll_signals(now_utc=None):
    # ... existing signals ...
    if settings.signals["FridayMove"]["enabled"]:
        for symbol in live_symbols():
            msg = friday_sig.evaluate(
                symbol=symbol,
                get_price_at=lambda dt, s=symbol: nearest_price_at_utc(s, dt),
                now_utc=now_utc,
            )
            if msg:
                logger.info(f"[Signal.FridayMove] {msg}")
                send_signal_to_mt4(msg)

3) GUI (main_tab.py): add a row in your Signals table showing:
   - Name: FridayMove
   - Status: Waiting / Eligible / Fired
   - Symbol, Direction, %Change, p_start, p_end, last_fired_date

4) MQL4 EA: keep thin. On message type == "EXECUTE", call ExecuteOrder(direction, risk_profile).

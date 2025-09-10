
# tests/test_friday_vol_signal.py
from datetime import datetime
from signals.friday_vol_signal import FridayVolSignal, FridayVolSignalConfig, UTC

# Freeze to a known Friday after 14:00 Chicago: 2025-08-29 20:10:00 UTC
FRI_UTC = datetime(2025, 8, 29, 20, 10, 0, tzinfo=UTC)

def mock_prices_factory(p_start: float, p_end: float):
    def _get_price_at(_dt):
        # Simple stub: return start before 14:00 and end at/after 14:00
        # We don't distinguish timestamps in this simple mock
        # First call -> start, second call -> end
        if not hasattr(_get_price_at, "_count"):
            _get_price_at._count = 0
        _get_price_at._count += 1
        return p_start if _get_price_at._count == 1 else p_end
    return _get_price_at

def test_triggers_once():
    cfg = FridayVolSignalConfig(percent_threshold=1.0)
    sig = FridayVolSignal(cfg)

    # 1.2% up move
    get_price = mock_prices_factory(1.0000, 1.0120)
    msg1 = sig.evaluate("EURUSD", get_price_at=get_price, now_utc=FRI_UTC)
    assert msg1 and msg1["type"] == "EXECUTE"
    # Guard prevents re-fire
    msg2 = sig.evaluate("EURUSD", get_price_at=get_price, now_utc=FRI_UTC)
    assert msg2 is None

def test_below_threshold_no_trigger():
    cfg = FridayVolSignalConfig(percent_threshold=2.0)
    sig = FridayVolSignal(cfg)

    # 1.2% up move but threshold is 2%
    get_price = mock_prices_factory(1.0000, 1.0120)
    msg = sig.evaluate("EURUSD", get_price_at=get_price, now_utc=FRI_UTC)
    assert msg is None

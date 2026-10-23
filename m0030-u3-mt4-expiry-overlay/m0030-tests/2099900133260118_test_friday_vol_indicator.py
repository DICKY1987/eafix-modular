# doc_id: DOC-TEST-0043
# DOC_ID: DOC-TEST-0003
# tests/test_friday_vol_indicator.py
import pytest
from datetime import datetime
from indicators.friday_vol_indicator import FridayVolIndicator, FridayVolIndicatorConfig, UTC

# Freeze to a known Friday after 14:00 Chicago: 2025-08-29 20:10:00 UTC
FRI_UTC_AFTER = datetime(2025, 8, 29, 20, 10, 0, tzinfo=UTC)
FRI_UTC_DURING = datetime(2025, 8, 29, 17, 30, 0, tzinfo=UTC)  # 12:30 Chicago
WED_UTC = datetime(2025, 8, 27, 20, 10, 0, tzinfo=UTC)  # Wednesday

def mock_prices_factory(p_start: float, p_end: float):
    """Factory for creating mock price functions"""
    def _get_price_at(_dt):
        # Simple stub: return start before 14:00 and end at/after 14:00
        # We don't distinguish timestamps in this simple mock
        # First call -> start, second call -> end
        if not hasattr(_get_price_at, "_count"):
            _get_price_at._count = 0
        _get_price_at._count += 1
        return p_start if _get_price_at._count == 1 else p_end
    return _get_price_at


def test_indicator_triggers_on_friday_after_window():
    """Test that indicator becomes active after Friday window with sufficient move"""
    cfg = FridayVolIndicatorConfig(percent_threshold=1.0)
    indicator = FridayVolIndicator(cfg)

    # 1.2% up move
    get_price = mock_prices_factory(1.0000, 1.0120)
    state = indicator.get_indicator_state("EURUSD", get_price_at=get_price, now_utc=FRI_UTC_AFTER)
    
    assert state["signal_active"] == True
    assert state["status"] == "TRIGGERED"
    assert state["values"]["pct_change"] == 1.2
    assert state["values"]["direction"] == "UP"
    assert state["values"]["threshold_met"] == True


def test_indicator_below_threshold_no_signal():
    """Test that indicator doesn't trigger when below threshold"""
    cfg = FridayVolIndicatorConfig(percent_threshold=2.0)
    indicator = FridayVolIndicator(cfg)

    # 1.2% up move but threshold is 2%
    get_price = mock_prices_factory(1.0000, 1.0120)
    state = indicator.get_indicator_state("EURUSD", get_price_at=get_price, now_utc=FRI_UTC_AFTER)
    
    assert state["signal_active"] == False
    assert state["status"] == "EXPIRED"
    assert state["values"]["pct_change"] == 1.2
    assert state["values"]["threshold_met"] == False


def test_indicator_not_friday():
    """Test that indicator waits when not Friday"""
    cfg = FridayVolIndicatorConfig(percent_threshold=1.0)
    indicator = FridayVolIndicator(cfg)

    get_price = mock_prices_factory(1.0000, 1.0120)
    state = indicator.get_indicator_state("EURUSD", get_price_at=get_price, now_utc=WED_UTC)
    
    assert state["signal_active"] == False
    assert state["status"] == "WAITING"
    assert state["meta"]["is_friday"] == False
    assert state["meta"]["reason"] == "Not Friday"


def test_indicator_friday_during_window():
    """Test that indicator monitors during active window"""
    cfg = FridayVolIndicatorConfig(percent_threshold=1.0)
    indicator = FridayVolIndicator(cfg)

    # 1.2% move during the window
    get_price = mock_prices_factory(1.0000, 1.0120)
    state = indicator.get_indicator_state("EURUSD", get_price_at=get_price, now_utc=FRI_UTC_DURING)
    
    assert state["status"] == "MONITORING"
    assert state["values"]["current_pct_change"] == 1.2
    assert state["values"]["direction"] == "UP"
    assert state["values"]["threshold_met"] == True
    assert state["signal_active"] == True  # Signal can be active during monitoring


def test_indicator_prevents_retrigger():
    """Test that indicator doesn't re-trigger on same Friday"""
    cfg = FridayVolIndicatorConfig(percent_threshold=1.0)
    indicator = FridayVolIndicator(cfg)

    # 1.2% up move
    get_price = mock_prices_factory(1.0000, 1.0120)
    
    # First evaluation - should trigger
    state1 = indicator.get_indicator_state("EURUSD", get_price_at=get_price, now_utc=FRI_UTC_AFTER)
    assert state1["signal_active"] == True
    assert state1["status"] == "TRIGGERED"
    
    # Second evaluation same day - should not trigger again
    get_price2 = mock_prices_factory(1.0000, 1.0150)  # Even bigger move
    state2 = indicator.get_indicator_state("EURUSD", get_price_at=get_price2, now_utc=FRI_UTC_AFTER)
    assert state2["signal_active"] == False
    assert state2["status"] == "TRIGGERED_PREVIOUSLY"


def test_indicator_down_move():
    """Test indicator works for downward moves"""
    cfg = FridayVolIndicatorConfig(percent_threshold=1.0)
    indicator = FridayVolIndicator(cfg)

    # 1.5% down move
    get_price = mock_prices_factory(1.0000, 0.9850)
    state = indicator.get_indicator_state("EURUSD", get_price_at=get_price, now_utc=FRI_UTC_AFTER)
    
    assert state["signal_active"] == True
    assert state["values"]["pct_change"] == 1.5
    assert state["values"]["direction"] == "DOWN"


def test_boolean_convenience_methods():
    """Test the convenience methods for simple checks"""
    cfg = FridayVolIndicatorConfig(percent_threshold=1.0)
    indicator = FridayVolIndicator(cfg)

    # 1.2% up move
    get_price = mock_prices_factory(1.0000, 1.0120)
    
    # Test boolean check
    is_active = indicator.is_signal_active("EURUSD", get_price_at=get_price, now_utc=FRI_UTC_AFTER)
    assert is_active == True
    
    # Test strength getter
    strength = indicator.get_signal_strength("EURUSD", get_price_at=get_price, now_utc=FRI_UTC_AFTER)
    assert strength == 1.2


def test_insufficient_price_data():
    """Test handling when price data is unavailable"""
    cfg = FridayVolIndicatorConfig(percent_threshold=1.0)
    indicator = FridayVolIndicator(cfg)

    # Price function returns None/0
    def bad_prices(_dt):
        return None
    
    state = indicator.get_indicator_state("EURUSD", get_price_at=bad_prices, now_utc=FRI_UTC_AFTER)
    
    assert state["signal_active"] == False
    assert state["status"] == "EXPIRED"
    assert state["meta"]["reason"] == "Insufficient price data"


def test_multiple_symbols_independent():
    """Test that different symbols maintain independent state"""
    cfg = FridayVolIndicatorConfig(percent_threshold=1.0)
    indicator = FridayVolIndicator(cfg)

    # EURUSD triggers
    get_price_eur = mock_prices_factory(1.0000, 1.0120)
    state_eur = indicator.get_indicator_state("EURUSD", get_price_at=get_price_eur, now_utc=FRI_UTC_AFTER)
    assert state_eur["signal_active"] == True
    
    # USDJPY doesn't trigger (below threshold)
    get_price_jpy = mock_prices_factory(150.00, 150.50)  # Only 0.33% move
    state_jpy = indicator.get_indicator_state("USDJPY", get_price_at=get_price_jpy, now_utc=FRI_UTC_AFTER)
    assert state_jpy["signal_active"] == False
    
    # EURUSD is still triggered, USDJPY still not
    state_eur2 = indicator.get_indicator_state("EURUSD", get_price_at=get_price_eur, now_utc=FRI_UTC_AFTER)
    assert state_eur2["status"] == "TRIGGERED_PREVIOUSLY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
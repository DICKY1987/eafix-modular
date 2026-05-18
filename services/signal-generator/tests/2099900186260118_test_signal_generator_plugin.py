# doc_id: DOC-TEST-0205
"""Unit tests for signal-generator plugin."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from shared.plugin_interface import PluginContext


def _load_plugin_class():
    module = importlib.import_module("services.signal_generator.src.plugin")
    return module.SignalGeneratorPlugin


@pytest.mark.asyncio
async def test_signal_generator_initialization():
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    context = PluginContext()

    config = {"strategy": "trend_following", "thresholds": {"rsi_overbought": 70, "rsi_oversold": 30}}
    await plugin.initialize(config, context)
    assert plugin.state.value == "ready"


def test_signal_generation():
    """Test signal generation logic."""
    module = importlib.import_module("services.signal_generator.src.plugin")
    settings = module.Settings()
    processor = module.SignalProcessor(settings)

    indicators = {
        "symbol": "EURUSD",
        "rsi_14": 25,
        "ema_20": 1.2350,
        "ema_50": 1.2340,
        "timestamp": "2026-01-09T19:00:00Z",
    }
    processor.on_calendar_signal({
        "symbol": "EURUSD",
        "calendar_id": "CAL8_USD_NFP_H",
        "proximity_state": "AT_EVENT",
        "confidence_score": 0.75,
        "direction_bias": "BULLISH",
    })
    processor.on_indicator_vector(indicators)

    signal = processor.evaluate("EURUSD")
    assert signal is not None
    assert signal["event_type"] == "Signal"
    assert signal["direction"] == "LONG"
    assert signal["confidence"] > 0

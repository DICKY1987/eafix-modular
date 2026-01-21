# doc_id: DOC-TEST-0204
"""Unit tests for indicator-engine plugin."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from shared.plugin_interface import PluginContext


def _load_plugin_class():
    module = importlib.import_module("services.indicator-engine.src.plugin")
    return module.IndicatorEnginePlugin


@pytest.mark.asyncio
async def test_indicator_plugin_initialization():
    """Test plugin initializes correctly."""
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    context = PluginContext()
    config = {"update_interval_ms": 500, "indicators": ["ema", "rsi"]}

    await plugin.initialize(config, context)
    assert plugin.state.value == "ready"


@pytest.mark.asyncio
async def test_indicator_plugin_start_stop():
    """Test plugin lifecycle."""
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    context = PluginContext()

    await plugin.initialize({}, context)
    await plugin.start()
    assert plugin.state.value == "running"

    await plugin.stop()
    assert plugin.state.value == "stopped"


def test_price_tick_handling():
    """Test handling of price tick events."""
    plugin_class = _load_plugin_class()
    plugin = plugin_class()

    price_data = {
        "symbol": "EURUSD",
        "bid": 1.2345,
        "ask": 1.2346,
        "timestamp": "2026-01-09T19:00:00Z",
    }

    plugin._handle_price_tick("price_tick", price_data, "data-ingestor")

    assert len(plugin._price_buffer) == 1
    assert plugin._price_buffer[0]["symbol"] == "EURUSD"

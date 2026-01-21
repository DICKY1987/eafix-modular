# doc_id: DOC-TEST-0208
"""Unit tests for reporter plugin."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from shared.plugin_interface import PluginContext


def _load_plugin_class():
    module = importlib.import_module("services.reporter.src.plugin")
    return module.ReporterPlugin


@pytest.mark.asyncio
async def test_reporter_initialization():
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    context = PluginContext()

    config = {"report_interval_min": 15}
    await plugin.initialize(config, context)
    assert plugin.state.value == "ready"


def test_trade_tracking():
    """Test trade result tracking."""
    plugin_class = _load_plugin_class()
    plugin = plugin_class()

    plugin._handle_trade_result("trade_result", {"pnl": 100.0}, "execution-engine")
    assert plugin._metrics["winning_trades"] == 1
    assert plugin._metrics["total_pnl"] == 100.0

    plugin._handle_trade_result("trade_result", {"pnl": -50.0}, "execution-engine")
    assert plugin._metrics["losing_trades"] == 1
    assert plugin._metrics["total_pnl"] == 50.0


def test_report_generation():
    """Test report generation."""
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    plugin._metrics = {
        "total_trades": 10,
        "winning_trades": 7,
        "losing_trades": 3,
        "total_pnl": 500.0,
    }

    report = plugin._generate_report()

    assert report["metrics"]["total_trades"] == 10
    assert report["win_rate"] == 70.0
    assert report["average_pnl"] == 50.0

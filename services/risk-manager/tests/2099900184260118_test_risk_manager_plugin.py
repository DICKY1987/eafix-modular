# doc_id: DOC-TEST-0206
"""Unit tests for risk-manager plugin."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from shared.plugin_interface import PluginContext


def _load_plugin_class():
    module = importlib.import_module("services.risk-manager.src.plugin")
    return module.RiskManagerPlugin


@pytest.mark.asyncio
async def test_risk_manager_initialization():
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    context = PluginContext()

    config = {
        "max_position_size": 1.0,
        "max_drawdown_pct": 5.0,
        "daily_loss_limit": 1000.0,
    }

    await plugin.initialize(config, context)
    assert plugin.state.value == "ready"


def test_risk_limit_check():
    """Test risk limit validation."""
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    plugin._daily_loss = 0.0
    plugin._daily_loss_limit = 1000.0
    plugin._current_drawdown = 2.0
    plugin._max_drawdown_pct = 5.0

    signal = {"confidence": 0.8}
    assert plugin._check_risk_limits(signal) is True

    plugin._daily_loss = 1100.0
    assert plugin._check_risk_limits(signal) is False


def test_position_sizing():
    """Test position size calculation."""
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    plugin._max_position_size = 1.0

    signal = {"confidence": 0.75}
    size = plugin._calculate_position_size(signal)

    assert size == 0.75

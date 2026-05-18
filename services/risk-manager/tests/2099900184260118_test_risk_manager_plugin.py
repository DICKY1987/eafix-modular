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
    module = importlib.import_module("services.risk_manager.src.plugin")
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
    module = importlib.import_module("services.risk_manager.src.plugin")
    settings = module.Settings()
    processor = module.RiskProcessor(settings)

    signal = {"symbol": "EURUSD", "confidence": 0.8, "sl_pips": 20.0}
    assert processor.process_signal(signal)["event_type"] == "OrderIntent"

    processor._cumulative_loss_today = settings.account_balance
    assert processor.process_signal(signal)["event_type"] == "RiskRejected"


def test_position_sizing():
    """Test position size calculation."""
    module = importlib.import_module("services.risk_manager.src.plugin")
    settings = module.Settings()
    processor = module.RiskProcessor(settings)

    assert processor._compute_lot_size(sl_pips=20.0) == 1.0

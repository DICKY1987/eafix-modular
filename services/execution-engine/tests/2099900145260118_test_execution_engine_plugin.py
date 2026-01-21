# doc_id: DOC-TEST-0207
"""Unit tests for execution-engine plugin."""

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from shared.plugin_interface import PluginContext


def _load_plugin_class():
    module = importlib.import_module("services.execution-engine.src.plugin")
    return module.ExecutionEnginePlugin


@pytest.mark.asyncio
async def test_execution_engine_initialization():
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    context = PluginContext()

    config = {"broker_api": "mt4", "order_timeout_sec": 30}
    await plugin.initialize(config, context)
    assert plugin.state.value == "ready"


@pytest.mark.asyncio
async def test_order_execution():
    """Test order execution logic."""
    plugin_class = _load_plugin_class()
    plugin = plugin_class()
    context = PluginContext()

    await plugin.initialize({}, context)
    order = {"symbol": "EURUSD", "action": "BUY", "position_size": 0.5}

    await plugin._execute_order(order)

    assert plugin._execution_count == 1

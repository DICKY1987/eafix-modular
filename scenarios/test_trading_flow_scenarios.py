"""Stable wrapper for the ID-prefixed trading flow scenario helper."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

__test__ = False

_IMPL_PATH = Path(__file__).resolve().parents[1] / "tests" / "contracts" / "scenarios" / "2099900233260118_test_trading_flow_scenarios.py"
_MODULE_KEY = "tests.contracts.scenarios._test_trading_flow_scenarios_impl"

if _MODULE_KEY in sys.modules:
    _MODULE = sys.modules[_MODULE_KEY]
else:
    _SPEC = spec_from_file_location(_MODULE_KEY, _IMPL_PATH)
    if _SPEC is None or _SPEC.loader is None:
        raise ImportError(f"Unable to load trading flow scenario helper: {_IMPL_PATH}")
    _MODULE = module_from_spec(_SPEC)
    sys.modules[_MODULE_KEY] = _MODULE
    _SPEC.loader.exec_module(_MODULE)

TradingScenarioTest = _MODULE.TradingScenarioTest

__all__ = ["TradingScenarioTest"]

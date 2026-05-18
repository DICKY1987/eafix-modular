"""Stable wrapper for the ID-prefixed contract testing framework."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

_IMPL_PATH = Path(__file__).resolve().parents[1] / "tests" / "contracts" / "framework" / "2099900230260118_contract_testing.py"
_MODULE_KEY = "framework._contract_testing_impl"

if _MODULE_KEY in sys.modules:
    _MODULE = sys.modules[_MODULE_KEY]
else:
    _SPEC = spec_from_file_location(_MODULE_KEY, _IMPL_PATH)
    if _SPEC is None or _SPEC.loader is None:
        raise ImportError(f"Unable to load contract testing framework: {_IMPL_PATH}")
    _MODULE = module_from_spec(_SPEC)
    sys.modules[_MODULE_KEY] = _MODULE
    _SPEC.loader.exec_module(_MODULE)

__all__ = [name for name in vars(_MODULE) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_MODULE, _name)


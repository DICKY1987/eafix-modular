"""Import wrapper for the ID-prefixed positioning ratio index implementation."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

_IMPL_PATH = Path(__file__).with_name("2099900216260118_positioning_ratio_index.py")
_MODULE_KEY = "shared.positioning._positioning_ratio_index_impl"

if _MODULE_KEY in sys.modules:
    _MODULE = sys.modules[_MODULE_KEY]
else:
    _SPEC = spec_from_file_location(_MODULE_KEY, _IMPL_PATH)
    if _SPEC is None or _SPEC.loader is None:
        raise ImportError(f"Unable to load positioning ratio index implementation: {_IMPL_PATH}")
    _MODULE = module_from_spec(_SPEC)
    sys.modules[_MODULE_KEY] = _MODULE
    _SPEC.loader.exec_module(_MODULE)

__all__ = [name for name in vars(_MODULE) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_MODULE, _name)


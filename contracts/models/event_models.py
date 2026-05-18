"""Import wrapper for the ID-prefixed event model implementation."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_IMPL_PATH = Path(__file__).with_name("2099900017260118_event_models.py")
_SPEC = spec_from_file_location("contracts.models._event_models_impl", _IMPL_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load event model implementation: {_IMPL_PATH}")

_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

__all__ = getattr(_MODULE, "__all__", [name for name in vars(_MODULE) if not name.startswith("_")])

for _name in __all__:
    globals()[_name] = getattr(_MODULE, _name)


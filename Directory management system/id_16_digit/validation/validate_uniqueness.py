"""
Compatibility shim for imports expecting validation.validate_uniqueness.
"""

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_module_path = Path(__file__).with_name("2099900079260118_validate_uniqueness.py")
_spec = spec_from_file_location("validation._validate_uniqueness_impl", _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load uniqueness validator from {_module_path}")

_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)

UniquenessValidator = _module.UniquenessValidator

__all__ = ["UniquenessValidator"]

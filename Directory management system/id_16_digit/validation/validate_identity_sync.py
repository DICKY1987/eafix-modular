"""
Compatibility shim for imports expecting validation.validate_identity_sync.
"""

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_module_path = Path(__file__).with_name("2099900078260118_validate_identity_sync.py")
_spec = spec_from_file_location("validation._validate_identity_sync_impl", _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load identity sync validator from {_module_path}")

_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)

SyncValidator = _module.SyncValidator

__all__ = ["SyncValidator"]

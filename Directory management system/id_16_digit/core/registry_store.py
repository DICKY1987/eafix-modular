"""
Compatibility shim for imports expecting core.registry_store.
"""

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

_module_path = Path(__file__).with_name("2099900074260118_registry_store.py")
_spec = spec_from_file_location("core._registry_store_impl", _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load registry store implementation from {_module_path}")

_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)

AllocationRecord = _module.AllocationRecord
RegistryStore = _module.RegistryStore

__all__ = ["AllocationRecord", "RegistryStore"]

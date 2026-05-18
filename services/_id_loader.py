"""Helpers for exposing ID-prefixed service files as stable modules."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parents[1]


def load_id_module(relative_path: str, module_key: str):
    """Load an ID-prefixed implementation under a stable package module key."""
    if module_key in sys.modules:
        return sys.modules[module_key]

    impl_path = _REPO_ROOT / relative_path
    spec = spec_from_file_location(module_key, impl_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load service implementation: {impl_path}")

    module = module_from_spec(spec)
    sys.modules[module_key] = module
    spec.loader.exec_module(module)
    return module


def export_id_module(namespace: dict, relative_path: str, public_names: Iterable[str] | None = None):
    """Populate a wrapper module namespace with public names from an implementation."""
    package = namespace["__package__"]
    wrapper_name = namespace["__name__"].rsplit(".", 1)[-1]
    module = load_id_module(relative_path, f"{package}._{wrapper_name}_impl")

    names = list(public_names) if public_names is not None else [
        name for name in vars(module) if not name.startswith("_")
    ]

    namespace["_MODULE"] = module
    namespace["__all__"] = names
    for name in names:
        namespace[name] = getattr(module, name)


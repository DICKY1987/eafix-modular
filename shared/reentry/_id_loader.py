"""Helpers for exposing ID-prefixed reentry files as normal modules."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def load_id_module(file_name: str, module_name: str):
    module_key = f"shared.reentry._{module_name}_impl"
    if module_key in sys.modules:
        return sys.modules[module_key]

    impl_path = Path(__file__).resolve().parent / file_name
    spec = spec_from_file_location(module_key, impl_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load reentry implementation: {impl_path}")

    module = module_from_spec(spec)
    sys.modules[module_key] = module
    spec.loader.exec_module(module)
    return module


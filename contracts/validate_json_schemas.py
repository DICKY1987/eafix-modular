"""Import wrapper for the ID-prefixed JSON schema validator."""

import json
import re
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_IMPL_PATH = Path(__file__).with_name("2099900015260118_validate_json_schemas.py")
_SPEC = spec_from_file_location("contracts._validate_json_schemas_impl", _IMPL_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load JSON validator implementation: {_IMPL_PATH}")

_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

__all__ = [name for name in vars(_MODULE) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_MODULE, _name)


class JSONSchemaValidator(_MODULE.JSONSchemaValidator):
    """Validator with aliases for ID-prefixed schema filenames."""

    def load_schemas(self) -> None:
        if not self.schema_dir.exists():
            return

        for schema_file in self.schema_dir.glob("*.json"):
            try:
                with schema_file.open("r", encoding="utf-8") as handle:
                    schema = json.load(handle)
            except Exception:
                continue

            stem = schema_file.stem
            self.schemas[stem] = schema
            self.schemas[re.sub(r"^\d+_", "", stem)] = schema


globals()["JSONSchemaValidator"] = JSONSchemaValidator

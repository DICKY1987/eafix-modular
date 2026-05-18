"""Import wrapper for the ID-prefixed CSV artifact validator."""

import re
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_IMPL_PATH = Path(__file__).with_name("2099900014260118_validate_csv_artifacts.py")
_SPEC = spec_from_file_location("contracts._validate_csv_artifacts_impl", _IMPL_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load CSV validator implementation: {_IMPL_PATH}")

_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

__all__ = [name for name in vars(_MODULE) if not name.startswith("_")]

for _name in __all__:
    globals()[_name] = getattr(_MODULE, _name)


class CSVArtifactValidator(_MODULE.CSVArtifactValidator):
    """CSV validator that recognizes ID-prefixed and tempfile artifact names."""

    def detect_csv_type(self, file_path: Path):
        filename = re.sub(r"^\d+_", "", file_path.name.lower())
        for csv_type in self.schema_models.keys():
            if filename.startswith(csv_type):
                return csv_type
        return None

    def validate_atomic_write_compliance(self, file_path: Path):
        errors = []
        filename = re.sub(r"^\d+_", "", file_path.name.lower())

        if filename.endswith(".tmp"):
            errors.append("File appears to be temporary (.tmp) - may indicate incomplete write")

        csv_types = "|".join(re.escape(csv_type) for csv_type in self.schema_models.keys())
        pattern = rf"^({csv_types})[a-z0-9]*_\d{{8}}_\d{{6}}\.csv$"
        fixture_pattern = rf"^({csv_types})_(valid|invalid)\.csv$"
        if not re.match(pattern, filename) and not re.match(fixture_pattern, filename):
            errors.append(f"Filename does not follow atomic write convention: {file_path.name}")

        try:
            with open(file_path, "r+"):
                pass
        except PermissionError:
            errors.append("File is locked - may indicate ongoing write operation")
        except Exception:
            pass

        return len(errors) == 0, errors


globals()["CSVArtifactValidator"] = CSVArtifactValidator

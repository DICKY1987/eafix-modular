from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

try:
    import jsonschema  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency in runtime
    jsonschema = None  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "schema" / "gdw.spec.schema.json"


def validate_spec(spec_path: Path) -> Tuple[bool, str]:
    """Validate a GDW spec JSON file against the repository schema.

    Returns (ok, message).
    """
    if jsonschema is None:
        return False, "jsonschema not available; install with `pip install jsonschema`"
    try:
        with SCHEMA_PATH.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        with spec_path.open("r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as exc:
        return False, f"load_error: {exc}"

    try:
        jsonschema.validate(instance=doc, schema=schema)
        return True, "valid"
    except Exception as exc:
        return False, f"schema_error: {exc}"


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m schema.validators.python.gdw_validator <spec.json>")
        sys.exit(2)
    ok, msg = validate_spec(Path(sys.argv[1]))
    print(msg)
    sys.exit(0 if ok else 1)


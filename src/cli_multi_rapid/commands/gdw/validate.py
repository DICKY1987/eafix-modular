from __future__ import annotations

from pathlib import Path
from typing import Optional

from schema.validators.python.gdw_validator import validate_spec


def cmd_validate(spec_path: Optional[str], repo_root: Path) -> int:
    if not spec_path:
        # default to primary example GDW if present
        primary = repo_root / "gdw" / "git.commit_push.main" / "v1.0.0" / "spec.json"
        fallback = Path("gdw") / "git.commit_push.main" / "v1.0.0" / "spec.json"
        if primary.exists():
            path = primary
        elif fallback.exists():
            path = fallback
        else:
            print("No spec path provided and default not found", flush=True)
            return 2
    else:
        path = Path(spec_path)
    ok, msg = validate_spec(path)
    print(msg)
    return 0 if ok else 1

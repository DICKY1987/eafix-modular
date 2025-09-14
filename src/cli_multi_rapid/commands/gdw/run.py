from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from lib.gdw_runner import run_gdw


def resolve_spec(repo_root: Path, workflow: str) -> Path:
    # Accept a path to spec.json or a workflow id like git.commit_push.main
    p = Path(workflow)
    if p.exists():
        return p
    candidate = repo_root / "gdw" / workflow / "v1.0.0" / "spec.json"
    if candidate.exists():
        return candidate
    fallback = Path("gdw") / workflow / "v1.0.0" / "spec.json"
    return fallback


def cmd_run(workflow: str, inputs: Optional[str], dry: bool, repo_root: Path) -> int:
    spec_path = resolve_spec(repo_root, workflow)
    if not spec_path.exists():
        print(f"Spec not found: {spec_path}")
        return 2
    payload: Dict[str, Any] = {}
    if inputs:
        try:
            payload = json.loads(inputs)
        except Exception as exc:
            print(f"Invalid inputs JSON: {exc}")
            return 2
    return run_gdw(spec_path, inputs=payload, dry_run=dry)

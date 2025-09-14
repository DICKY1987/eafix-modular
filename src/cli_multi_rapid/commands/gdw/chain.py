from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from lib.gdw_runner import run_gdw


def load_chain(chain_path: Path) -> Dict[str, Any]:
    with chain_path.open("r", encoding="utf-8") as f:
        if chain_path.suffix.lower() in (".yaml", ".yml"):
            import yaml  # type: ignore
            return yaml.safe_load(f) or {}
        return json.load(f)


def cmd_chain(chain_file: str, dry: bool, repo_root: Path) -> int:
    chain_path = Path(chain_file)
    if not chain_path.exists():
        print(f"Chain file not found: {chain_path}")
        return 2
    data = load_chain(chain_path)
    steps: List[Dict[str, Any]] = list(data.get("steps", []))
    rc = 0
    here_root = Path(__file__).resolve().parents[5]
    for idx, step in enumerate(steps, start=1):
        wf = str(step.get("workflow"))
        inputs = step.get("inputs", {})
        candidates = [
            (repo_root / "gdw" / wf / "v1.0.0" / "spec.json").resolve(),
            (here_root / "gdw" / wf / "v1.0.0" / "spec.json").resolve(),
            (Path("gdw") / wf / "v1.0.0" / "spec.json").resolve(),
        ]
        spec = next((p for p in candidates if p.exists()), candidates[0])
        print(f"[CHAIN] {idx}/{len(steps)} workflow={wf} dry={dry}")
        rc = run_gdw(spec, inputs=inputs, dry_run=dry)
        if rc != 0:
            break
    return rc

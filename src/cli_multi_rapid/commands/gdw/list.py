from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict


def discover_gdws(root: Path) -> List[Dict[str, str]]:
    gdw_dir = root / "gdw"
    results: List[Dict[str, str]] = []
    if not gdw_dir.exists():
        return results
    for wf_dir in gdw_dir.iterdir():
        if not wf_dir.is_dir():
            continue
        for ver_dir in wf_dir.iterdir():
            if not ver_dir.is_dir():
                continue
            spec = ver_dir / "spec.json"
            if spec.exists():
                wf_id = wf_dir.name
                results.append({
                    "id": wf_id,
                    "version": ver_dir.name,
                    "spec": str(spec)
                })
    return results


def cmd_list(repo_root: Path) -> int:
    items = discover_gdws(repo_root)
    print(json.dumps(items, indent=2))
    return 0


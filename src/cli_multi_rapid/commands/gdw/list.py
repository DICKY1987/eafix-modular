from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict
import json


def _from_catalog(root: Path) -> List[Dict[str, str]]:
    index = root / "catalog" / "index.json"
    if not index.exists():
        return []
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = []
    for wf in data.get("workflows", []):
        items.append({
            "id": str(wf.get("id")),
            "version": str(wf.get("version")),
            "spec": str(wf.get("path")),
            "domain": wf.get("domain"),
            "maturity": wf.get("maturity"),
            "summary": wf.get("summary"),
        })
    return items


def _scan_filesystem(root: Path) -> List[Dict[str, str]]:
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
                results.append({
                    "id": wf_dir.name,
                    "version": ver_dir.name.lstrip("v"),
                    "spec": str(spec.relative_to(root)),
                })
    return results


def discover_gdws(root: Path) -> List[Dict[str, str]]:
    # Prefer catalog when present; fallback to scanning
    items = _from_catalog(root)
    if items:
        return items
    return _scan_filesystem(root)


def cmd_list(repo_root: Path) -> int:
    items = discover_gdws(repo_root)
    print(json.dumps(items, indent=2))
    return 0

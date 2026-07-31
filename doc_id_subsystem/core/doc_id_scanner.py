#!/usr/bin/env python3
"""
doc_id_scanner.py — scan repository files for EAFIX document-ID prefixes.

A "doc-ID-prefixed" filename matches the pattern:
    <16 decimal digits>_<rest-of-name>
for example: 1299900011260118_doc_id_validation.yml

Usage
-----
    python doc_id_scanner.py --repo-root ../..
    python doc_id_scanner.py --repo-root ../.. --output-json scan_result.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

DOC_ID_PATTERN = re.compile(r"^(\d{16})_(.+)$")

# Directories to always exclude from scanning
EXCLUDE_DIRS: set[str] = {".git", "__pycache__", ".venv", "node_modules", ".mypy_cache"}


def _iter_tracked_files(repo_root: Path):
    """Yield every regular file under *repo_root* that is not in an excluded directory."""
    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Prune excluded dirs in-place so os.walk skips them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            yield Path(dirpath) / fname


def scan(repo_root: Path) -> Dict:
    """Return a summary dict with all doc-ID-prefixed files and duplicate IDs."""
    id_to_paths: Dict[str, List[str]] = {}
    ungoverned: List[str] = []
    total_files = 0

    for fpath in _iter_tracked_files(repo_root):
        total_files += 1
        rel = str(fpath.relative_to(repo_root))
        m = DOC_ID_PATTERN.match(fpath.name)
        if m:
            doc_id = m.group(1)
            id_to_paths.setdefault(doc_id, []).append(rel)
        else:
            ungoverned.append(rel)

    governed = {doc_id: paths for doc_id, paths in id_to_paths.items()}
    duplicates = {doc_id: paths for doc_id, paths in id_to_paths.items() if len(paths) > 1}

    governed_count = sum(len(p) for p in governed.values())
    coverage = governed_count / total_files if total_files else 0.0

    return {
        "repo_root": str(repo_root),
        "total_files": total_files,
        "governed_count": governed_count,
        "ungoverned_count": len(ungoverned),
        "coverage": round(coverage, 6),
        "duplicate_id_count": len(duplicates),
        "duplicates": duplicates,
        "governed": governed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repo for doc-ID-prefixed files.")
    parser.add_argument(
        "--repo-root",
        default="../..",
        help="Path to the repository root (default: ../.. relative to this script).",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="If set, write the full scan result to this JSON file.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    repo_root = (script_dir / args.repo_root).resolve()

    if not repo_root.is_dir():
        print(f"ERROR: repo-root does not exist: {repo_root}", file=sys.stderr)
        return 1

    result = scan(repo_root)

    print(f"Repository root : {result['repo_root']}")
    print(f"Total files     : {result['total_files']}")
    print(f"Governed (with doc-ID prefix) : {result['governed_count']}")
    print(f"Ungoverned                    : {result['ungoverned_count']}")
    print(f"Coverage                      : {result['coverage']:.1%}")
    print(f"Duplicate doc-IDs             : {result['duplicate_id_count']}")

    if result["duplicate_id_count"]:
        print("\nDuplicate doc-ID details:")
        for doc_id, paths in sorted(result["duplicates"].items()):
            print(f"  {doc_id}:")
            for p in paths:
                print(f"    {p}")

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # Omit the full ungoverned list in the JSON to keep it compact
        compact = {k: v for k, v in result.items() if k != "governed"}
        out_path.write_text(json.dumps(compact, indent=2))
        print(f"\nScan result written to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

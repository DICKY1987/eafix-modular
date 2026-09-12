"""Fail when tracked files introduce a duplicate document identifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from doc_id_subsystem.core.doc_id_scanner import scan_repository  # noqa: E402

KNOWN_FILE = Path(__file__).with_name("known_duplicates.json")


def _load_known_duplicates(path: Path) -> dict[str, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        duplicates = payload["duplicates"]
        if not isinstance(duplicates, dict):
            raise TypeError("duplicates must be an object")
        for doc_id, paths in duplicates.items():
            if not isinstance(doc_id, str) or not isinstance(paths, list):
                raise TypeError("duplicates entries must map strings to lists")
            if any(not isinstance(item, str) for item in paths):
                raise TypeError("duplicate paths must be strings")
        return duplicates
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid duplicate baseline: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    if not KNOWN_FILE.is_file():
        print(f"FAIL: committed duplicate baseline is missing: {KNOWN_FILE}", file=sys.stderr)
        return 2

    try:
        known = _load_known_duplicates(KNOWN_FILE)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    current = scan_repository(args.repo_root).duplicate_ids
    new_or_expanded = {
        doc_id: paths
        for doc_id, paths in current.items()
        if doc_id not in known or not set(paths).issubset(set(known[doc_id]))
    }
    if new_or_expanded:
        print(json.dumps(new_or_expanded, indent=2), file=sys.stderr)
        print("FAIL: new or expanded duplicate document IDs", file=sys.stderr)
        return 1
    print(f"PASS: no new duplicates ({len(current)} known duplicate IDs remain)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

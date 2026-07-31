"""
validate_doc_id_uniqueness.py — CI gate: no new duplicate doc-IDs may be introduced.

Behaviour
---------
First run (no saved snapshot):
    Records every existing duplicate ID set as *known* in
    ``known_duplicates.json`` and exits 0.

Subsequent runs:
    Compares the current duplicate set against the known set.
    Exits 0 if no NEW duplicates have been introduced.
    Exits 1 if any new duplicate IDs appear (i.e. IDs with duplicates that
    were not in the known-duplicates snapshot).

Usage
-----
    python validate_doc_id_uniqueness.py [--root DIR]

Options
-------
    --root DIR   Repository root to scan.  Defaults to two levels up from
                 this script (the repo root when this file lives at
                 doc_id_subsystem/validation/).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_SUBSYSTEM_DIR = _THIS_DIR.parent
_REPO_ROOT = _SUBSYSTEM_DIR.parent

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from doc_id_subsystem.core.doc_id_scanner import scan_repository  # noqa: E402

_KNOWN_DUPLICATES_FILE = _THIS_DIR / "known_duplicates.json"


def _load_known() -> dict | None:
    if _KNOWN_DUPLICATES_FILE.exists():
        with _KNOWN_DUPLICATES_FILE.open() as fh:
            return json.load(fh)
    return None


def _save_known(data: dict) -> None:
    with _KNOWN_DUPLICATES_FILE.open("w") as fh:
        json.dump(data, fh, indent=2)
    print(f"[uniqueness] Known-duplicates snapshot saved to {_KNOWN_DUPLICATES_FILE}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate that no new duplicate doc-IDs have been introduced."
    )
    parser.add_argument(
        "--root",
        default=str(_REPO_ROOT),
        help="Repository root directory to scan.",
    )
    args = parser.parse_args()

    result = scan_repository(root=args.root)
    current_dupes: dict[str, list[str]] = result.duplicate_ids

    total_dupe_ids = len(current_dupes)
    print(
        f"[uniqueness] Found {total_dupe_ids} duplicate ID(s) across "
        f"{result.duplicate_count} file(s)."
    )

    saved = _load_known()

    if saved is None:
        # First run — snapshot and pass.
        _save_known(
            {
                "known_duplicate_ids": sorted(current_dupes.keys()),
                "duplicate_details": {k: sorted(v) for k, v in current_dupes.items()},
            }
        )
        if total_dupe_ids:
            print(
                f"[uniqueness] PASS — {total_dupe_ids} pre-existing duplicate(s) "
                "recorded as known; they will not block CI."
            )
        else:
            print("[uniqueness] PASS — no duplicates found; baseline recorded.")
        return 0

    known_ids: set[str] = set(saved.get("known_duplicate_ids", []))
    current_ids: set[str] = set(current_dupes.keys())
    new_ids: set[str] = current_ids - known_ids

    if new_ids:
        print(f"[uniqueness] FAIL — {len(new_ids)} NEW duplicate ID(s) introduced:")
        for doc_id in sorted(new_ids):
            paths = current_dupes[doc_id]
            print(f"  ID {doc_id}:")
            for p in sorted(paths):
                print(f"    {p}")
        return 1

    resolved_ids = known_ids - current_ids
    if resolved_ids:
        print(
            f"[uniqueness] INFO — {len(resolved_ids)} previously-known duplicate(s) "
            "have been resolved (no action required)."
        )

    print(
        f"[uniqueness] PASS — no new duplicates introduced "
        f"({total_dupe_ids} known duplicate(s) remain)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

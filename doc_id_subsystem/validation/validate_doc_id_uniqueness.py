#!/usr/bin/env python3
"""
validate_doc_id_uniqueness.py — detect duplicate document-ID prefixes.

A doc-ID is the 16-digit numeric prefix in filenames of the form:
    <16 decimal digits>_<rest-of-name>

Two files are considered a "collision" when they share the same 16-digit
prefix but live at different paths (same-name duplicates created by archiving
a file to a superseded/ folder are flagged with a lower severity).

Exit codes
----------
    0  No duplicate doc-IDs found (or all found duplicates match the
       known-duplicates list in ``known_duplicates.json``).
    1  One or more NEW duplicate doc-IDs detected that are not recorded in
       ``known_duplicates.json``.
    2  Usage error or repository not found.

On the first run (no ``known_duplicates.json`` present) the script writes a
snapshot of any currently-detected duplicates so that pre-existing collisions
are not treated as new violations.  Subsequent runs compare against that
snapshot.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Resolve paths so this script can be invoked from any working directory
_HERE = Path(__file__).resolve().parent          # doc_id_subsystem/validation
_CORE = _HERE.parent / "core"                    # doc_id_subsystem/core
# Insert core directory so we can do a direct import without needing the package
sys.path.insert(0, str(_CORE))

from doc_id_scanner import scan  # noqa: E402

KNOWN_DUPLICATES_FILE = _HERE / "known_duplicates.json"


def _load_known(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_known(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, indent=2))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate that no NEW duplicate doc-ID prefixes exist in the repository."
    )
    parser.add_argument(
        "--repo-root",
        default="../..",
        help="Path to the repository root relative to this script (default: ../..).",
    )
    parser.add_argument(
        "--update-known",
        action="store_true",
        help=(
            "Update known_duplicates.json with the current set of duplicates "
            "and exit 0.  Use this after deliberately resolving or accepting a duplicate."
        ),
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = (script_dir / args.repo_root).resolve()

    if not repo_root.is_dir():
        print(f"ERROR: repository root not found: {repo_root}", file=sys.stderr)
        return 2

    result = scan(repo_root)
    current_duplicates: dict[str, list[str]] = result["duplicates"]

    print(f"Repository          : {repo_root}")
    print(f"Total files scanned : {result['total_files']}")
    print(f"Duplicate doc-IDs   : {len(current_duplicates)}")

    if args.update_known:
        _save_known(current_duplicates, KNOWN_DUPLICATES_FILE)
        print(
            f"\n[INFO] known_duplicates.json updated with {len(current_duplicates)} "
            f"duplicate(s)."
        )
        return 0

    known = _load_known(KNOWN_DUPLICATES_FILE)

    if not known and current_duplicates:
        # First run with duplicates present — record them so they are not
        # treated as violations going forward.
        _save_known(current_duplicates, KNOWN_DUPLICATES_FILE)
        print(
            f"\n[INFO] No previous known-duplicates snapshot found. "
            f"Recording {len(current_duplicates)} pre-existing duplicate(s) as known."
        )
        for doc_id, paths in sorted(current_duplicates.items()):
            print(f"  KNOWN-DUPLICATE  {doc_id}:")
            for p in paths:
                print(f"    {p}")
        print("\nPASS — known duplicates snapshot established.")
        return 0

    new_duplicates = {
        doc_id: paths
        for doc_id, paths in current_duplicates.items()
        if doc_id not in known
    }

    resolved_duplicates = {
        doc_id: paths
        for doc_id, paths in known.items()
        if doc_id not in current_duplicates
    }

    if resolved_duplicates:
        print(f"\n[INFO] {len(resolved_duplicates)} previously-known duplicate(s) resolved:")
        for doc_id in sorted(resolved_duplicates):
            print(f"  RESOLVED  {doc_id}")

    if current_duplicates:
        print(f"\n[WARN] {len(current_duplicates)} known duplicate(s) still present:")
        for doc_id, paths in sorted(current_duplicates.items()):
            tag = "KNOWN" if doc_id in known else "NEW"
            print(f"  {tag}-DUPLICATE  {doc_id}:")
            for p in paths:
                print(f"    {p}")

    if new_duplicates:
        print(
            f"\nFAIL — {len(new_duplicates)} NEW duplicate doc-ID(s) introduced:",
            file=sys.stderr,
        )
        for doc_id, paths in sorted(new_duplicates.items()):
            print(f"  {doc_id}:", file=sys.stderr)
            for p in paths:
                print(f"    {p}", file=sys.stderr)
        return 1

    print("\nPASS — no new duplicate doc-IDs detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

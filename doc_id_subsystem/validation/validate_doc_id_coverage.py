#!/usr/bin/env python3
"""
validate_doc_id_coverage.py — enforce a minimum doc-ID coverage level.

The script compares the CURRENT ratio of doc-ID-prefixed files to total files
against a SAVED baseline.  On the first run (no baseline file present) it
records the current coverage as the baseline and exits 0.  On subsequent runs
it requires:

    current_coverage >= saved_baseline * baseline_fraction

where ``--baseline`` is the ``baseline_fraction`` (default 0.95, meaning no
more than a 5 % regression from the saved baseline is permitted).

Coverage is measured repository-wide across all regular files (excluding .git
and generated caches).

Usage
-----
    # Run from doc_id_subsystem/validation/
    python validate_doc_id_coverage.py --baseline 0.95

Exit codes
----------
    0  Coverage is acceptable (meets or exceeds the regression floor).
    1  Coverage has regressed below the permitted floor.
    2  Usage error or repository not found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Resolve paths so this script can be invoked from any working directory
_HERE = Path(__file__).resolve().parent          # doc_id_subsystem/validation
_CORE = _HERE.parent / "core"                    # doc_id_subsystem/core
# Insert core directory so we can do a direct import without needing the package
sys.path.insert(0, str(_CORE))

from doc_id_scanner import scan  # noqa: E402

BASELINE_FILE = _HERE / "doc_id_coverage_baseline.json"


def _load_baseline() -> dict | None:
    if BASELINE_FILE.exists():
        try:
            return json.loads(BASELINE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _save_baseline(data: dict) -> None:
    BASELINE_FILE.write_text(json.dumps(data, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that doc-ID coverage has not regressed below the acceptable floor."
        )
    )
    parser.add_argument(
        "--baseline",
        type=float,
        default=0.95,
        help=(
            "Minimum acceptable fraction of the saved coverage baseline "
            "(e.g. 0.95 means current coverage must be >= 95 %% of saved baseline). "
            "Default: 0.95."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default="../..",
        help="Path to the repository root relative to this script (default: ../..).",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = (script_dir / args.repo_root).resolve()

    if not repo_root.is_dir():
        print(f"ERROR: repository root not found: {repo_root}", file=sys.stderr)
        return 2

    result = scan(repo_root)
    current_coverage = result["coverage"]
    total_files = result["total_files"]
    governed_count = result["governed_count"]

    print(f"Repository          : {repo_root}")
    print(f"Total files scanned : {total_files}")
    print(f"Governed files      : {governed_count}")
    print(f"Current coverage    : {current_coverage:.3%}")

    saved = _load_baseline()

    if saved is None:
        # First run — establish the baseline
        baseline_data = {
            "coverage": current_coverage,
            "total_files": total_files,
            "governed_count": governed_count,
        }
        _save_baseline(baseline_data)
        print(
            f"\n[INFO] No previous baseline found. "
            f"Recording current coverage ({current_coverage:.3%}) as the baseline."
        )
        print("PASS — baseline established.")
        return 0

    saved_coverage = saved.get("coverage", 0.0)
    floor = saved_coverage * args.baseline

    print(f"Saved baseline      : {saved_coverage:.3%}")
    print(f"Required floor      : {floor:.3%}  (saved × {args.baseline})")

    if current_coverage >= floor:
        print("PASS — coverage is within the acceptable regression floor.")
        return 0
    else:
        delta = saved_coverage - current_coverage
        print(
            f"FAIL — coverage has regressed by {delta:.3%} "
            f"(floor: {floor:.3%}, current: {current_coverage:.3%}).",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

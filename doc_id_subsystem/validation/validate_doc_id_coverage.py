"""
validate_doc_id_coverage.py — CI gate: doc-ID coverage must not regress.

Behaviour
---------
First run (no saved baseline):
    Records the current coverage as the baseline in ``doc_id_coverage_baseline.json``
    and exits 0.

Subsequent runs:
    Reads the saved baseline and asserts that
        current_coverage >= saved_baseline * threshold
    Exits 0 on pass, 1 on failure.

Usage
-----
    python validate_doc_id_coverage.py [--baseline FLOAT] [--root DIR]

Options
-------
    --baseline FLOAT   Minimum fraction of baseline that must be maintained.
                       Default: 0.95 (i.e. coverage must not drop below 95 %
                       of the recorded baseline value).
    --root DIR         Repository root to scan.  Defaults to the two-levels-up
                       directory relative to this script (i.e. the repo root
                       when this file lives at doc_id_subsystem/validation/).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running both as "python validate_doc_id_coverage.py" from within
# doc_id_subsystem/validation/ and as a module from the repo root.
_THIS_DIR = Path(__file__).resolve().parent
_SUBSYSTEM_DIR = _THIS_DIR.parent
_REPO_ROOT = _SUBSYSTEM_DIR.parent

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from doc_id_subsystem.core.doc_id_scanner import scan_repository  # noqa: E402

_BASELINE_FILE = _THIS_DIR / "doc_id_coverage_baseline.json"


def _load_baseline() -> dict | None:
    if _BASELINE_FILE.exists():
        with _BASELINE_FILE.open() as fh:
            return json.load(fh)
    return None


def _save_baseline(data: dict) -> None:
    with _BASELINE_FILE.open("w") as fh:
        json.dump(data, fh, indent=2)
    print(f"[coverage] Baseline recorded to {_BASELINE_FILE}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate doc-ID coverage regression gate.")
    parser.add_argument(
        "--baseline",
        type=float,
        default=0.95,
        help="Minimum fraction of recorded baseline coverage to enforce (default: 0.95).",
    )
    parser.add_argument(
        "--root",
        default=str(_REPO_ROOT),
        help="Repository root directory to scan.",
    )
    args = parser.parse_args()

    result = scan_repository(root=args.root)
    current_coverage = result.coverage_ratio
    current_prefixed = len(result.prefixed_files)
    current_total = result.total_files

    print(
        f"[coverage] Scanned {current_total} files; "
        f"{current_prefixed} prefixed ({current_coverage:.2%} coverage)."
    )

    saved = _load_baseline()

    if saved is None:
        # First run — record and pass.
        _save_baseline(
            {
                "coverage_ratio": current_coverage,
                "prefixed_files": current_prefixed,
                "total_files": current_total,
            }
        )
        print("[coverage] PASS — baseline established on first run.")
        return 0

    baseline_coverage = saved.get("coverage_ratio", 0.0)
    threshold = args.baseline
    minimum_required = baseline_coverage * threshold

    print(
        f"[coverage] Baseline: {baseline_coverage:.2%}, "
        f"threshold: {threshold:.0%}, "
        f"minimum required: {minimum_required:.2%}."
    )

    if current_coverage < minimum_required:
        print(
            f"[coverage] FAIL — current coverage {current_coverage:.2%} is below "
            f"the required minimum {minimum_required:.2%}."
        )
        return 1

    print(f"[coverage] PASS — {current_coverage:.2%} >= {minimum_required:.2%}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

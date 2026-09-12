"""Fail when tracked-file document-ID coverage regresses from the committed baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from doc_id_subsystem.core.doc_id_scanner import scan_repository  # noqa: E402

BASELINE_FILE = Path(__file__).with_name("doc_id_coverage_baseline.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=float, default=0.95)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    if not 0 < args.baseline <= 1:
        parser.error("--baseline must be greater than 0 and at most 1")
    if not BASELINE_FILE.is_file():
        print(f"FAIL: committed baseline is missing: {BASELINE_FILE}", file=sys.stderr)
        return 2

    saved = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    result = scan_repository(args.repo_root)
    floor = float(saved["coverage_ratio"]) * args.baseline
    print(
        f"tracked={result.total_files} prefixed={len(result.prefixed_files)} "
        f"coverage={result.coverage_ratio:.6%} floor={floor:.6%}"
    )
    if result.coverage_ratio < floor:
        print("FAIL: document-ID coverage regressed below the allowed floor", file=sys.stderr)
        return 1
    print("PASS: document-ID coverage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

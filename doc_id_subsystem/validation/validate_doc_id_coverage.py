#!/usr/bin/env python3
"""
DOC_ID Coverage Validator - CI/CD friendly

Validates doc_id coverage and detects regressions.
Exit code 0: Pass, Exit code 1: Fail

Usage:
    python scripts/validate_doc_id_coverage.py
    python scripts/validate_doc_id_coverage.py --baseline 0.92
    python scripts/validate_doc_id_coverage.py --report coverage_report.json

DOC_ID: DOC-GUIDE-DOC-ID-VALIDATE-DOC-ID-COVERAGE-452
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, ELIGIBLE_PATTERNS, EXCLUDE_PATTERNS
from common.rules import DOC_ID_REGEX, validate_doc_id  # Phase 1: Use centralized rules
from common.config import DEFAULT_COVERAGE_BASELINE

# Event emission (Phase 2: Observability)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "SSOT_System" / "SSOT_SYS_tools"))
    from event_emitter import get_event_emitter
    EVENT_SYSTEM_AVAILABLE = True
except ImportError:
    EVENT_SYSTEM_AVAILABLE = False
    def get_event_emitter():
        return None

def _emit_event(subsystem: str, step_id: str, subject: str, summary: str,
                severity: str = "INFO", details: dict = None):
    """Helper to emit events with graceful degradation if event system unavailable."""
    if EVENT_SYSTEM_AVAILABLE:
        try:
            emitter = get_event_emitter()
            if emitter:
                emitter.emit(
                    subsystem=subsystem,
                    step_id=step_id,
                    subject=subject,
                    summary=summary,
                    severity=severity,
                    details=details or {}
                )
        except Exception:
            pass  # Gracefully degrade if event system fails

# Use DOC_ID_REGEX from common.rules (centralized pattern)
DOC_ID_PATTERN = DOC_ID_REGEX
DOC_ID_SEARCH_PATTERN = re.compile(DOC_ID_PATTERN.pattern.strip("^$"))

def should_scan_file(file_path: Path) -> bool:
    """Check if file should be scanned for doc_id"""
    # Check if in excluded directory
    rel_path = file_path.relative_to(REPO_ROOT)
    rel_path_str = str(rel_path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in rel_path_str:
            return False

    return True


def has_doc_id(file_path: Path) -> bool:
    """Check if file contains a doc_id"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return bool(DOC_ID_SEARCH_PATTERN.search(content))
    except Exception:
        return False


def scan_repository() -> Dict:
    """Scan repository and return coverage statistics"""
    eligible_files = []
    files_with_doc_id = []

    for pattern in ELIGIBLE_PATTERNS:
        for file_path in REPO_ROOT.glob(pattern):
            if not file_path.is_file():
                continue
            if should_scan_file(file_path):
                rel_path = file_path.relative_to(REPO_ROOT)
                eligible_files.append(str(rel_path))
                if has_doc_id(file_path):
                    files_with_doc_id.append(str(rel_path))

    total = len(eligible_files)
    with_id = len(files_with_doc_id)
    coverage = (with_id / total * 100) if total > 0 else 0

    return {
        "total_eligible": total,
        "with_doc_id": with_id,
        "without_doc_id": total - with_id,
        "coverage_percent": round(coverage, 2),
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "files_without_doc_id": sorted(
            [f for f in eligible_files if f not in files_with_doc_id]
        ),
    }


def validate_coverage(baseline: float = DEFAULT_COVERAGE_BASELINE) -> bool:
    """
    Validate coverage meets baseline.

    Args:
        baseline: Minimum acceptable coverage (0.0-1.0)

    Returns:
        True if coverage meets baseline, False otherwise
    """
    # Emit VALIDATION_STARTED event
    _emit_event(
        subsystem="SUB_DOC_ID",
        step_id="VALIDATION_STARTED",
        subject="validate_doc_id_coverage",
        summary=f"Starting doc_id coverage validation (baseline: {baseline * 100}%)",
        severity="INFO",
        details={"baseline_pct": baseline * 100, "validator": "coverage"}
    )

    print("==> Scanning repository for doc_id coverage...")

    results = scan_repository()

    coverage = results["coverage_percent"] / 100
    total = results["total_eligible"]
    with_id = results["with_doc_id"]
    without_id = results["without_doc_id"]

    print(f"\n==> Coverage Results:")
    print(f"   Total eligible files: {total}")
    print(f"   Files with doc_id:    {with_id} ({results['coverage_percent']}%)")
    print(f"   Files without doc_id: {without_id}")
    print(f"   Baseline required:    {baseline * 100}%")

    passed = coverage >= baseline

    if passed:
        print(
            f"\n✓ PASS: Coverage {results['coverage_percent']}% meets baseline {baseline * 100}%"
        )

        # Emit VALIDATION_PASSED event
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="VALIDATION_PASSED",
            subject="validate_doc_id_coverage",
            summary=f"Coverage validation passed: {results['coverage_percent']}% (baseline: {baseline * 100}%)",
            severity="INFO",
            details={
                "coverage_pct": results["coverage_percent"],
                "baseline_pct": baseline * 100,
                "total_files": total,
                "files_with_id": with_id,
                "validator": "coverage"
            }
        )
    else:
        print(
            f"\n✗ FAIL: Coverage {results['coverage_percent']}% below baseline {baseline * 100}%"
        )

        if results["files_without_doc_id"]:
            print(f"\n==> Files missing doc_id (first 10):")
            for file_path in results["files_without_doc_id"][:10]:
                print(f"   - {file_path}")

            if without_id > 10:
                print(f"   ... and {without_id - 10} more")

        # Emit VALIDATION_FAILED event
        _emit_event(
            subsystem="SUB_DOC_ID",
            step_id="VALIDATION_FAILED",
            subject="validate_doc_id_coverage",
            summary=f"Coverage validation failed: {results['coverage_percent']}% < {baseline * 100}%",
            severity="ERROR",
            details={
                "coverage_pct": results["coverage_percent"],
                "baseline_pct": baseline * 100,
                "total_files": total,
                "files_with_id": with_id,
                "files_without_id": without_id,
                "missing_files_sample": results["files_without_doc_id"][:10],
                "validator": "coverage"
            }
        )

    # Emit VALIDATION_COMPLETED event
    _emit_event(
        subsystem="SUB_DOC_ID",
        step_id="VALIDATION_COMPLETED",
        subject="validate_doc_id_coverage",
        summary=f"Coverage validation completed: {'PASSED' if passed else 'FAILED'}",
        severity="NOTICE",
        details={
            "passed": passed,
            "coverage_pct": results["coverage_percent"],
            "validator": "coverage"
        }
    )

    return passed, results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate doc_id coverage")
    parser.add_argument(
        "--baseline",
        type=float,
        default=DEFAULT_COVERAGE_BASELINE,
        help=f"Minimum coverage required (default: {DEFAULT_COVERAGE_BASELINE})",
    )
    parser.add_argument("--report", type=str, help="Output JSON report to file")

    args = parser.parse_args()

    passed, results = validate_coverage(baseline=args.baseline)

    # Write report if requested
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n==> Report written to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

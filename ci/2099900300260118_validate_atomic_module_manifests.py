#!/usr/bin/env python3
# doc_id: DOC-CI-ATOMIC-MANIFEST-0001
"""Fail CI when regenerated atomic manifests violate vNext quality gates."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Timestamp-only fields that differ across runs without semantic change.
_VOLATILE_KEYS = {"generated_at_utc", "last_updated_utc", "last_reconciled_utc"}


def _strip_volatile(obj: object) -> object:
    """Recursively remove volatile timestamp keys from a JSON-like object."""
    if isinstance(obj, dict):
        return {k: _strip_volatile(v) for k, v in obj.items() if k not in _VOLATILE_KEYS}
    if isinstance(obj, list):
        return [_strip_volatile(v) for v in obj]
    return obj


def _has_semantic_drift(path: Path, repo_root: Path) -> bool:
    """Return True if *path* has uncommitted changes that are not timestamp-only."""
    rel = str(path.relative_to(repo_root))
    # Capture the committed version from git HEAD.
    result = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # File is untracked (new); any content counts as drift.
        return path.exists()
    try:
        committed = _strip_volatile(json.loads(result.stdout))
        current = _strip_volatile(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return True
    return committed != current


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "tools.manifest_generation.generate_manifests", "--repo-root", str(repo_root)]
    completed = subprocess.run(cmd, cwd=repo_root, check=False)
    if completed.returncode != 0:
        print("Manifest generation failed", file=sys.stderr)
        return completed.returncode

    # --- Drift detection -------------------------------------------------
    manifests_dir = repo_root / "EAFIX_auth_docs" / "manifests"
    drift_paths = [
        manifests_dir / "manifest_validation_report.json",
        manifests_dir / "eafix_module_manifests_bundle.vNext.schema_valid.json",
    ]
    drifted = [str(p.relative_to(repo_root)) for p in drift_paths if _has_semantic_drift(p, repo_root)]
    if drifted:
        print("FAIL: generated_artifacts_drift_detected", file=sys.stderr)
        for d in drifted:
            print(f"  drift: {d}", file=sys.stderr)
        print(
            "Stale committed manifests detected.  Re-run: "
            "python -m tools.manifest_generation.generate_manifests --repo-root . "
            "and commit the updated EAFIX_auth_docs/manifests outputs.",
            file=sys.stderr,
        )
        return 1

    # --- Quality gates ---------------------------------------------------
    report_path = repo_root / "EAFIX_auth_docs" / "manifests" / "manifest_validation_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    checks = {
        "schema_valid_34_of_34": report["acceptance"]["schema_valid_34_of_34"],
        "bundle_count_valid": report["acceptance"]["bundle_count_valid"],
        "no_stale_alias_primaries": len(report["identity_validation"]["stale_primary_symbols"]) == 0,
        "no_dependency_target_serialization": len(report["dependency_validation"]["issues"]) == 0,
        "no_contract_object_issues": len(report["contract_validation"]["issues"]) == 0,
        "runtime_ports_valid": len(report["runtime_validation"]["issues"]) == 0,
        "file_ownership_index_valid": len(report["file_ownership_validation"]["issues"]) == 0,
        "ui_validation_passed": len(report["ui_validation"]["issues"]) == 0,
        "mt4_validation_passed": len(report["mt4_validation"]["issues"]) == 0,
        "thin_module_validation_passed": len(report["thin_module_validation"]["issues"]) == 0,
        "governance_validation_passed": len(report["governance_validation"]["issues"]) == 0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    if failed:
        print(f"Atomic manifest CI gate failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

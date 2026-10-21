"""Independent progress gate; never authorizes final cutover (DEC-031)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from authority_core import REPO, load, write
from validate_consolidation import validate_repository

PERMITTED = frozenset({"source_review", "independent_reconciliation",
    "evidence_backed_candidate_patches", "offline_validation",
    "validation_tool_repair", "private_review_package"})
HELD = frozenset({"active_authority_cutover", "archive_unreconciled_sources",
    "change_trading_behavior", "external_publication", "claim_final_completion"})


def validate_progress(repo: Path, action: str = "independent_reconciliation") -> dict:
    control = repo / "governance/module_consolidation"
    policy = load(control / "execution_policy.json")
    baseline = load(control / "run/baseline.json")
    authorized = (policy.get("decision_id") == "DEC-031"
        and policy.get("status") == "approved_scoped_suspension"
        and policy.get("full_acceptance_waived") is False
        and policy.get("effective_baseline") == baseline["baseline_commit"]
        and set(policy.get("held_actions", [])) == HELD
        and set(policy.get("permitted_actions", [])) == PERMITTED
        and action in PERMITTED)
    integrity = validate_repository(repo, mode="candidate", structural_only=True)
    return {"status": "PASS" if authorized and integrity["status"] == "PASS" else "BLOCKED",
        "decision_id": "DEC-031", "action": action, "authorized": authorized,
        "validation_scope": "independent_progress_only",
        "execution_status": "ACTIVE_WITH_SCOPED_HOLDS" if authorized else "BLOCKED",
        "integrity_status": integrity["status"],
        "cutover_status": "BLOCKED", "cutover_approved": False,
        "completed": False, "full_acceptance_required": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--action", default="independent_reconciliation")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = validate_progress(args.repo_root.resolve(), args.action)
    except (ValueError, KeyError, OSError, TypeError) as error:
        result = {"status": "BLOCKED", "cutover_approved": False,
            "completed": False, "error": str(error)}
    if args.report:
        write(args.report, result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
apply_migration_map.py

Status write-back and resume-from-checkpoint guard for
EAFIX_physical_file_migration_map_v1_0_0.json.

Background (see DECISION_LOG.md at the repo root, "Migration status write-back"):
the map's 42 operations were all still marked "approved_not_executed" even though
filesystem inspection shows 19 of them were, in fact, already carried out (their
declared outputs exist and their declared sources are gone). This is the
"Partial Success Amnesia" failure mode: a real migration tool re-running the map
as-is would attempt `git mv` on 19 sources that no longer exist and fail closed
per `execution_contract.missing_source_policy`.

This script does NOT perform any file moves. It only:
  1. Verifies each operation's declared sources/outputs against the actual
     filesystem.
  2. In --write-back mode, corrects `status` in the map JSON itself for
     operations that are unambiguously complete (status -> "completed",
     matching the vocabulary already used in `completion_definition`), and
     stamps a `verification_utc` timestamp on those operations.
  3. Always writes a machine-readable verification report to
     tools/migration/migration_verification_report.generated.json, in the
     shape described by the map's own `execution_contract
     .evidence_report_required_fields` (commit_sha is left null for
     operations that predate this tool -- it was not feasible to reconstruct
     history for 19 already-applied operations after the fact; a future
     migration tool that performs new moves should populate it for real).

Resume-from-checkpoint contract for any future executor of this map:
  - Before attempting operation X, check its `status` field. If it is
    "completed", SKIP it -- do not re-run git mv, do not fail on a missing
    source. Only operations still at "approved_not_executed" (or a future
    status added by this tool such as "needs_manual_review") should be
    attempted.

Usage:
  python tools/migration/apply_migration_map.py            # report only, no writes
  python tools/migration/apply_migration_map.py --write-back  # also updates the map JSON
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MAP_PATH = REPO_ROOT / "EAFIX_physical_file_migration_map_v1_0_0.json"
REPORT_PATH = Path(__file__).resolve().parent / "migration_verification_report.generated.json"


def classify(op: dict) -> str:
    srcs = [s.get("path") for s in op.get("sources", []) if s.get("path")]
    outs = [o.get("path") for o in op.get("outputs", []) if o.get("path")]
    src_exist = [(REPO_ROOT / p).exists() for p in srcs]
    out_exist = [(REPO_ROOT / p).exists() for p in outs]

    all_src_gone = all(not e for e in src_exist) if src_exist else True
    all_src_present = all(src_exist) if src_exist else True
    all_out_present = all(out_exist) if out_exist else False
    any_out_present = any(out_exist)

    if all_out_present and all_src_gone:
        return "completed"
    if all_out_present and all_src_present:
        return "duplicated_source_still_present"
    if not any_out_present and all_src_present:
        return "not_started"
    if any_out_present and not all_out_present:
        return "partially_executed"
    return "needs_manual_review"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-back", action="store_true",
                     help="Update status fields in the migration map JSON for verified-complete operations.")
    args = ap.parse_args()

    data = json.loads(MAP_PATH.read_text())
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    evidence_records = []
    write_back_count = 0

    for op in data["operations"]:
        verdict = classify(op)
        prior_status = op.get("status")

        record = {
            "operation_id": op["operation_id"],
            "status": "completed" if verdict == "completed" else prior_status,
            "source_paths": [s.get("path") for s in op.get("sources", [])],
            "output_paths": [o.get("path") for o in op.get("outputs", [])],
            "commit_sha": None,
            "references_updated": None,
            "validations_run": [],
            "validation_results": {"filesystem_verification": verdict},
            "deviations": [
                "Retroactive verification by tools/migration/apply_migration_map.py: "
                "this operation's completion was inferred from filesystem state, not from "
                "a live execution of this tool. commit_sha/references_updated were not "
                "reconstructed."
            ] if verdict == "completed" else [],
            "rollback_performed": False,
        }
        evidence_records.append(record)

        if verdict == "completed" and prior_status != "completed" and args.write_back:
            op["status"] = "completed"
            op["verification_utc"] = now
            op["verification_method"] = "filesystem_check:apply_migration_map.py"
            write_back_count += 1
        elif verdict == "needs_manual_review" and args.write_back and prior_status == "approved_not_executed":
            # Never silently reclassify ambiguous states as anything other than what a human should look at.
            op["status"] = "needs_manual_review"
            op["verification_utc"] = now
            op["verification_method"] = "filesystem_check:apply_migration_map.py"
            write_back_count += 1

    if args.write_back:
        data.setdefault("execution_contract", {})["resume_policy"] = (
            "Operations whose status is 'completed' MUST be skipped by any executor of this "
            "map -- their sources are already gone, so re-attempting git mv will fail closed "
            "per missing_source_policy. Only attempt operations still at 'approved_not_executed'."
        )
        MAP_PATH.write_text(json.dumps(data, indent=2) + "\n")

    REPORT_PATH.write_text(json.dumps({
        "generated_at_utc": now,
        "generated_by": "tools/migration/apply_migration_map.py",
        "write_back_applied": args.write_back,
        "operations": evidence_records,
    }, indent=2) + "\n")

    from collections import Counter
    counts = Counter(classify(op) for op in data["operations"])
    print("Verification verdicts:", dict(counts))
    if args.write_back:
        print(f"Wrote back status for {write_back_count} operation(s) in {MAP_PATH.name}.")
    else:
        print("Dry run (no --write-back) -- map JSON not modified.")
    print(f"Evidence report written to {REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

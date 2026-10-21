"""Record a blocked execution without promoting candidates or archiving sources."""
from __future__ import annotations

import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from authority_core import CONTROL, PROCESS, REGISTRIES, REPO, file_sha, jsonl, load, value_sha, write, write_jsonl


def evidence(path, address=None, lines=None):
    return {"path": path, "sha256": file_sha(REPO / path),
            "json_pointer": address, "lines": lines,
            "source_commit": load(CONTROL / "run/baseline.json")["baseline_commit"]}


def main():
    baseline = load(CONTROL / "run/baseline.json")
    commit = baseline["baseline_commit"]
    universe = load(CONTROL / "module_universe.json")
    sources = jsonl(CONTROL / "run/source_processing_ledger.jsonl")
    source_index = {s["path"]: s for s in sources}
    contracts = jsonl(REPO / REGISTRIES / "contract_registry.jsonl")
    controls = jsonl(REPO / REGISTRIES / "operational_control_registry.jsonl")
    contract_path = REGISTRIES + "/contract_registry.jsonl"
    control_path = REGISTRIES + "/operational_control_registry.jsonl"
    wire_evidence = [evidence(contract_path, f"/{i}") for i, r in enumerate(contracts)
                     if r["contract_name"] in {"BrokerOrderEnvelope", "AdapterAck"}]
    retry_evidence = [evidence(control_path, f"/{i}") for i, r in enumerate(controls)
                      if r["record_id"] in {"CONTROL::FAILURE::S16", "CONTROL::VALIDATION::S16"}]
    bridge_doc = "m0016-b1-mt4-adapter-transport/m0016-docs/architecture/0110000076260118_07_transport_bridge_contracts.md"
    config_path = "services/transport-router/src/2099900197260118_config.py"
    ea_sample = "EAFIX_auth_docs/04_mt4_bridge_and_execution/HUEY_P_EA_ExecutionEngine_8.mql4"
    critical = [
        {"blocker_id": "BLOCK-BRIDGE-WIRE-DEFINITION", "module": "m0016,m0017", "json_pointer": "/contracts",
         "reason": "BrokerOrderEnvelope and AdapterAck resolve by name but the live records contain no required/optional fields, schema, examples, versioned payload or compatibility policy. The historical deep inventory also has no schema/model/field/test candidates for either. This is a boundary-definition gap, not merely a missing executable schema.",
         "missing_evidence_or_decision": "Approved B1/B2 wire protocol: field names/types/units, required versus optional fields, version/compatibility, sequence/hash/idempotency semantics, acknowledgement acceptance and rejection behavior; identify the current EA source or authoritative intended interface.",
         "next_action": "Supply the approved current protocol or a governed source-grounded contract-design decision, then reconcile it into the external contract authority and local manifest usage. Do not infer payload fields from a contract name.",
         "evidence_refs": wire_evidence + [evidence("EAFIX_auth_docs/contracts_registry/deep_contract_evidence_inventory.json", lines=[1957, 2049])]},
        {"blocker_id": "BLOCK-BRIDGE-RETRY-TIMEOUT", "module": "m0016", "json_pointer": "/process_steps/0/retry_timeout_recovery",
         "reason": "The S16 failure rule requires a deterministic retry schedule but gives no numeric schedule or EA acknowledgement timeout. The transport-router defaults of 3 attempts, 2-second delay and 10-second service timeout describe downstream service calls; there is no evidence establishing them as the MT4 acknowledgement protocol. The bridge note says CSV production default and also prefer Socket.",
         "missing_evidence_or_decision": "Approved active transport selection, acknowledgement timeout, retry count/backoff, exhaustion output and recovery behavior for the B1-to-EA boundary.",
         "next_action": "Resolve against the actual current adapter/EA implementation or approve intended bridge policy. Keep observed Python service defaults separate from EA protocol facts.",
         "evidence_refs": retry_evidence + [evidence(bridge_doc, lines=[6, 20]), evidence(config_path, lines=[122, 162])]},
        {"blocker_id": "BLOCK-LEGACY-VALIDATION-UNAVAILABLE", "module": "all", "json_pointer": "/verification_commands",
         "reason": "The existing atomic-manifest CI command fails because tools.manifest_generation.generate_manifests is absent. Repository-wide pytest also has three failing tests that import absent EA-REG generator/validator files. Its existing 85% coverage gate fails. These checks cannot certify a coordinated cutover.",
         "missing_evidence_or_decision": "A working, reviewed replacement validation route for v2, retirement/redirect of old generator and validator callers, and passing required CI checks. New offline structural checks do not waive the existing failures.",
         "next_action": "After specification reconciliation, replace legacy generation callers with read-only authority validation and one-way projection checks; update obsolete tests through a governed retirement decision; rerun the required suite without lowering its gate.",
         "evidence_refs": [evidence("ci/2099900300260118_validate_atomic_module_manifests.py", lines=[34, 40]),
                           evidence("tests/test_generator_update.py", lines=[10, 40]), evidence("tests/test_validator_update.py", lines=[8, 34])]},
        {"blocker_id": "BLOCK-CURRENT-EA-AUTHORITY", "module": "m0017", "json_pointer": "/runtime/entrypoints",
         "reason": "The root's B2 entrypoint points to a Python transport router. The supplied .mql4 example explicitly says the original EA was unavailable and implements a moving-average crossover strategy; it is not evidence of the execution-only intended B2 boundary. Adopting that sample would change the module's trading responsibility.",
         "missing_evidence_or_decision": "Identify the current approved execution EA and its protocol-facing entrypoint, or provide an approved intended execution-only specification. Implementation verification can remain separate.",
         "next_action": "Preserve the original values as historical evidence; review the real EA source and contract. Do not promote the replacement strategy sample to canonical execution behavior.",
         "evidence_refs": [evidence("m0017-b2-mt4-ea-executor/manifest.json", "/process_binding/entrypoint_files"), evidence(ea_sample, lines=[1, 30])]},
    ]
    for b in critical:
        b.update({"severity": "blocking", "resolution_state": "unresolved", "decision_id": "DEC-027",
                  "responsible_decision_maker": "repository owner or delegated specification reviewer",
                  "classification": "reviewed_evidence_blocker"})
    gaps = [g for g in jsonl(CONTROL / "run/blocker_resolution_queue.jsonl") if not g["blocker_id"].startswith("BLOCK-")]
    write_jsonl(CONTROL / "run/blocker_resolution_queue.jsonl", gaps + critical)
    write(CONTROL / "run/critical_blockers.json", {"status": "BLOCKED", "baseline_commit": commit,
          "instructions": "Sections 30, 35 and 38: do not infer absent mandatory facts or improvise past failed required validation.",
          "review_items_are_not_all_proven_missing": True, "blockers": critical})
    claims = [c for c in jsonl(CONTROL / "run/claim_ledger.jsonl") if c.get("claim_type") != "blocker_evidence_observation"]
    observations = []
    for b in critical:
        for ref in b["evidence_refs"]:
            source = source_index[ref["path"]]
            cid = "OBS-" + value_sha([b["blocker_id"], ref])[:22]
            observations.append({"claim_id": cid, "source_id": source["source_id"], "source_path": ref["path"],
                "source_commit": commit, "source_sha256": ref["sha256"], "source_locator": {"json_pointer": ref["json_pointer"], "lines": ref["lines"]},
                "claim_type": "blocker_evidence_observation", "target_module": b["module"], "target_json_pointer": b["json_pointer"],
                "current_authoritative_value": None, "candidate_value": b["reason"], "disposition": "RETAINED_EXTERNAL",
                "retained_active_authority_ref": ref["path"], "conflict_type": "INSUFFICIENT_EVIDENCE",
                "decision_id": "DEC-027", "rationale": "Direct source observation recorded in the blocker report; no missing behavior invented.",
                "evidence_strength": "direct", "status": "source_verified", "approval_actor": "Codex under execution instructions",
                "active_authority_applied": False, "blocker_id": b["blocker_id"]})
    write_jsonl(CONTROL / "run/claim_ledger.jsonl", claims + observations)
    for s in sources:
        rows = [c for c in observations if c["source_id"] == s["source_id"]]
        if rows:
            prior_rows = [c for c in claims if c["source_id"] == s["source_id"]]
            s.update({"extraction_status": "partial", "reconciliation_status": "blocked", "source_status": "partially_reviewed",
                      "relevant_claim_count": len(prior_rows) + len(rows), "unresolved_claim_count": len({c["blocker_id"] for c in rows}),
                      "retained_external_count": len(rows), "fully_scraped": False, "safe_to_archive": False,
                      "retention_reason": "Only cited sections reviewed for blockers; full-source claim reconciliation remains open."})
    write_jsonl(CONTROL / "run/source_processing_ledger.jsonl", sources)
    # Freeze original tracking versions before replacing their derived status view.
    tracking_paths = ["governance/module_consolidation/tracking/build_ssot.py", "governance/module_consolidation/tracking/README.md",
                      "governance/module_consolidation/tracking/eafix_consolidation_ssot.json", ".gitattributes"]
    tracking_readme = CONTROL / "tracking/README.md"
    tracking_readme.write_text(f"""# EAFIX consolidation tracking

Baseline: `{commit}`. Execution status: **BLOCKED**.

This directory holds a derived work-tracking view. The governed decisions,
source ledger, blocker queue and phase report determine its content. Module
specifications remain in the existing active roots until P6 passes.

Run `python governance/module_consolidation/tracking/build_ssot.py` from any
directory. It writes beside its own script and preserves the 76 existing item
IDs. D1-D7 are derived from the owner's DEC policy, not treated as unanswered
questions. The module schema field describes the candidate; the active root
remains v1. The three readiness fields remain independent.

No GitHub Projects or issue statuses were changed by this execution. Existing
`project_sync.py` and `project_bootstrap.py` remain optional projection tools;
their external state is not the execution authority.

See `../CLOSEOUT_REPORT.md`, `../run/phase_status.json`,
`../resolution_decisions.json` and `../run/critical_blockers.json`.
""", encoding="utf-8")
    subprocess.run([sys.executable, str(CONTROL / "tracking/build_ssot.py")], cwd=REPO, check=True, capture_output=True)
    versions = []
    for path in tracking_paths:
        snapshot = CONTROL / "run/baseline_tracking" / ("gitattributes.baseline" if path == ".gitattributes" else Path(path).name)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=REPO))
        versions.append({"path": path, "baseline_sha256": source_index[path]["sha256"], "current_sha256": file_sha(REPO / path),
                         "baseline_snapshot_path": snapshot.relative_to(REPO).as_posix(), "decision_id": "DEC-015" if path == ".gitattributes" else "DEC-018",
                         "reason": "Preserve raw evidence bytes through Git checkout." if path == ".gitattributes" else "Explicit instruction section 13.7: regenerate tracking at the fresh baseline; no module facts changed."})
    write(CONTROL / "run/source_version_lineage.json", {"baseline_commit": commit, "versions": versions})
    # These packages report the work actually done; their state is BLOCKED.
    waves = {"W1": [1, 2, 5, 25], "W2": [3, 4, 6, 7], "W3": [8, 9, 10], "W4": [11, 12, 13, 14, 27],
             "W5": [15, 16, 17, 18, 19, 20], "W6": [21, 22, 23, 24], "W7": [26, 28, 29, 30, 31, 32], "W8": [33, 34]}
    waves["P3-PILOT"] = [9, 16, 29, 34]
    drift = load(CONTROL / "run/root_bundle_drift_report.json")
    for batch, numbers in waves.items():
        modules = [f"m{n:04d}" for n in numbers]
        directory = CONTROL / "batches" / batch
        rows = [c for c in claims + observations if any(m in c["target_module"].split(",") for m in modules)]
        ids = {c["source_id"] for c in rows}
        receipts = [{"source_id": s["source_id"], "path": s["path"], "sha256": s["sha256"], "extraction_status": s["extraction_status"],
                     "fully_scraped": False, "safe_to_archive": False, "coverage": "v1 leaf preservation or cited blocker sections only",
                     "semantic_review_complete": False} for s in sources if s["source_id"] in ids]
        write(directory / "batch_manifest.json", {"batch_id": batch, "baseline_commit": commit, "modules": modules,
              "state": "BLOCKED", "scope_executed": "lossless candidate seeding and reviewed blocker observations",
              "whole_source_reconciliation_executed": False, "source_versions": receipts})
        write_jsonl(directory / "extracted_claims.jsonl", rows)
        write(directory / "module_reconciliation.json", {"module_count": len(modules), "modules": [
            {"short_id": m, "schema_valid": True, "specification_ready": False, "implementation_verified": False,
             "active_root_version": "1.0.0", "candidate_path": f"governance/module_consolidation/staging/{m}/manifest.v2.candidate.json"} for m in modules]})
        write(directory / "conflict_records.json", {"state": "unresolved", "root_bundle_drift": [d for d in drift["modules"] if d["module_short_id"] in modules and d["difference_count"]],
              "reviewed_blockers": [b for b in critical if b["module"] == "all" or set(b["module"].split(",")) & set(modules)]})
        write(directory / "approved_decisions.json", {"decision_ids": ["DEC-007", "DEC-017", "DEC-027", "DEC-028", "DEC-029"],
              "scope": "preservation/reference policy only; no approval of absent bridge behavior"})
        write(directory / "proposed_module_patches.json", {"baseline_commit": commit, "patches": [],
              "reason": "No semantic authority replacement approved before full reconciliation; candidate snapshots already seeded."})
        write(directory / "validation_report.json", {"status": "BLOCKED", "structural_candidates": f"{len(modules)}/{len(modules)}",
              "specification_ready": f"0/{len(modules)}", "full_semantic_gate": "not_passed", "validation_evidence": "../../run/structural_validation.json"})
        write(directory / "source_extraction_receipts.json", {"receipts": receipts, "whole_source_review_complete": False})
        write(directory / "archive_action_manifest.json", {"actions": [], "retired_source_count": 0, "reason": "Both independent archive gates not passed."})
        write(directory / "batch_completion_report.json", {"status": "BLOCKED", "completed": False, "claim_records": len(rows),
              "candidate_preservation_done": True, "full_source_reconciliation_done": False, "active_authority_mutations": 0,
              "unresolved_mandatory_items": sum(g["severity"] == "blocking" and g["module"] in modules for g in gaps), "module_count": len(modules)})
    writer_inventory = load(CONTROL / "run/writer_inventory.json")
    writer_inventory["new_program_writers"] = [
        {"path": "governance/module_consolidation/" + name, "direction": direction,
         "content_sha256": file_sha(CONTROL / name), "review_status": "reviewed", "validation_evidence": "run/fixture_validation.json"}
        for name, direction in [("inventory_sources.py", "inventory_only"), ("prepare_candidates.py", "baseline_to_candidate_only"),
                                ("generate_projections.py", "guarded_root_to_projection"), ("validate_consolidation.py", "read_only_validation_and_report"),
                                ("record_blocked_execution.py", "governance_report_only"), ("authority_core.py", "guarded_primitives")]]
    writer_inventory["new_program_writers_inventory_required_before_cutover"] = False
    write(CONTROL / "run/writer_inventory.json", writer_inventory)
    print({"critical_blockers": len(critical), "reviewed_observation_records": len(observations), "partial_batch_packages": len(waves),
           "source_versions": len(sources), "active_authority_mutations": 0})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

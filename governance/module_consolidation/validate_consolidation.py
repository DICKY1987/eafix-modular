"""Deterministic validation; structural PASS never implies specification readiness."""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path

from authority_core import (BUNDLE, CONTROL, PROCESS, REGISTRIES, REPO, SCHEMA, SHARED,
                            evidence_version, file_sha, jsonl, load, pointer, value_sha, write)


def validate_projection_document(bundle: dict, manifests: list[dict]) -> list[dict]:
    entries = bundle.get("manifests", [])
    projection = {m.get("module_identity", {}).get("module_id"): m for m in entries}
    return [
        {"check_id": "bundle_parity", "status": "PASS" if len(entries) == len(projection) == 34 and all(
            projection.get(m["module_identity"]["module_id"]) == m for m in manifests) else "FAIL",
         "detail": "Projection exactly matches all active roots"},
        {"check_id": "bundle_derived_only", "status": "PASS" if bundle.get("authority_policy") == "generated_from_module_manifests"
         and bundle.get("authority_status") != "canonical" else "FAIL", "detail": "Bundle cannot author module facts"},
    ]


def validate_authority_routing(authority: dict) -> list[str]:
    return [e.get("relative_path") or e.get("filename") for e in authority.get("entries", [])
            if e.get("classification") == "canonical" and e.get("relative_path") in {REGISTRIES + "/module_catalog.json", BUNDLE}]


def validate_manifests(manifests: list[dict], universe: list[dict], repo: Path,
                       shared: dict, *, check_readiness: bool = True) -> dict:
    checks: list[dict] = []
    def add(code, ok, detail, severity="FAIL"):
        checks.append({"check_id": code, "status": "PASS" if ok else severity, "detail": detail})
    try:
        import jsonschema
    except ImportError:
        return {"status": "UNAVAILABLE", "checks": [{"check_id": "schema_validation", "status": "UNAVAILABLE", "detail": "Install jsonschema using the repository dependency workflow."}], "blocking_failure_count": 1}
    schema = load(repo / SCHEMA)
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        add("schema_meta_valid", True, "Draft 2020-12")
    except jsonschema.SchemaError as error:
        add("schema_meta_valid", False, str(error))
    validator = jsonschema.Draft202012Validator(schema)
    ids = [m.get("module_identity", {}).get("module_id") for m in manifests]
    short_ids = [m.get("module_identity", {}).get("short_id") for m in manifests]
    symbols = [m.get("module_identity", {}).get("canonical_symbol") for m in manifests]
    add("manifest_count", len(manifests) == 34, f"{len(manifests)}/34")
    add("unique_permanent_ids", len(ids) == len(set(ids)), "All permanent IDs must be unique")
    add("unique_short_ids", len(short_ids) == len(set(short_ids)), "All short IDs must be unique")
    add("unique_symbols", len(symbols) == len(set(symbols)), "All symbols must be unique")
    add("canonical_universe", set(ids) == {u["module_id"] for u in universe}, "Exact canonical permanent-ID universe")
    process_records = {p["step_id"]: p for p in jsonl(repo / PROCESS)}
    contract_records = {p["contract_id"]: p for p in jsonl(repo / REGISTRIES / "contract_registry.jsonl")}
    shared_records = {p["file_id"]: p for p in shared.get("records", [])}
    baseline_path = repo / "governance/module_consolidation/run/baseline.json"
    baseline = load(baseline_path) if baseline_path.is_file() else None
    owners: dict[str, str] = {}
    source_hash_cache: dict[str, str] = {}
    lineage = repo / "governance/module_consolidation/run/source_version_lineage.json"
    versions = {v["path"]: v for v in load(lineage)["versions"]} if lineage.is_file() else {}
    schema_valid_count = 0
    for manifest in manifests:
        identity = manifest.get("module_identity", {})
        short = identity.get("short_id", "UNKNOWN")
        root = identity.get("canonical_root", "")
        errors = [f"{e.json_path}: {e.message}" for e in validator.iter_errors(manifest)]
        add(short + ":schema", not errors, errors)
        if errors:
            continue
        schema_valid_count += 1
        expected = next((u for u in universe if u["short_id"] == short), None)
        add(short + ":identity", bool(expected and all(identity[k] == expected[e] for k, e in
            [("module_id", "module_id"), ("canonical_symbol", "canonical_symbol"), ("canonical_root", "root")])), "Pinned canonical identity")
        id_file = repo / root / ".module-id"
        add(short + ":module_id_marker", id_file.is_file() and id_file.read_text().strip() == identity["module_id"], "Permanent marker agreement")
        if baseline:
            add(short + ":baseline_commit", manifest["authority"]["effective_baseline_commit"] == baseline["baseline_commit"], "No stale baseline commit")
            add(short + ":original_hash", manifest["migration"]["source_manifest_sha256"] == baseline["original_manifest_hashes"].get(root), "Original root source hash agrees with pinned baseline")
        original_snapshot = repo / manifest["migration"]["original_snapshot_path"]
        add(short + ":original_snapshot_bytes", original_snapshot.is_file() and file_sha(original_snapshot) == manifest["migration"]["source_manifest_sha256"], "Immutable v1 snapshot hash")
        if original_snapshot.is_file():
            add(short + ":lossless_v1", load(original_snapshot) == manifest["migration"]["original_v1"], "All original JSON information preserved")
        evidence = {e["evidence_id"]: e for e in manifest["evidence"]}
        add(short + ":evidence_ids", len(evidence) == len(manifest["evidence"]), "Stable evidence identifiers are unique")
        for e in manifest["evidence"]:
            try:
                approved = pointer(manifest, e["target_json_pointer"])
                if isinstance(approved, list) and e["target_element_id"]:
                    approved = next(v for v in approved if e["target_element_id"] in [v.get("file_id"), v.get("usage_id"), v.get("step_id")])
                target_matches = value_sha(approved) == e["approved_value_sha256"]
            except (KeyError, IndexError, ValueError, TypeError, StopIteration):
                target_matches = False
            add(short + ":approved_value:" + e["evidence_id"], target_matches, "Changed values need a new reviewed evidence record")
            source = evidence_version(repo, e["source_path"], e["source_sha256"], versions)
            key = (e["source_path"], e["source_sha256"])
            if key not in source_hash_cache and source.is_file():
                source_hash_cache[key] = file_sha(source)
            add(short + ":evidence_source:" + e["evidence_id"], source_hash_cache.get(key) == e["source_sha256"], "Source bytes match frozen evidence")
            address = e["source_locator"].get("json_pointer")
            if address is not None and source.is_file():
                try:
                    value = jsonl(source) if source.suffix == ".jsonl" else load(source)
                    pointer(value, address)
                    ok = True
                except (KeyError, IndexError, ValueError, TypeError):
                    ok = False
                add(short + ":evidence_locator:" + e["evidence_id"], ok, "JSON pointer resolves in pinned source")
        def visit(value, address=""):
            if isinstance(value, dict):
                if {"applicability", "knowledge", "evidence_refs", "gap_ids"}.issubset(value):
                    add(short + ":fact_evidence:" + address,
                        all(ref in evidence for ref in value["evidence_refs"]), "Referenced field evidence exists")
                    if value["knowledge"] == "confirmed" and value["applicability"] == "applicable":
                        add(short + ":confirmed_value:" + address, bool(value["evidence_refs"]), "Confirmed meaningful values need evidence")
                    if value["applicability"] == "not_applicable":
                        add(short + ":not_applicable:" + address,
                            bool(value["reason"] and value["decision_id"] and value["evidence_refs"]), "N/A requires a reason, rule and evidence")
                for k, item in value.items():
                    if k not in {"original_v1", "evidence"}:
                        visit(item, address + "/" + str(k))
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    visit(item, address + f"/{index}")
        visit(manifest)
        definition_ids = {f["file_id"] for f in manifest["files"]["definitions"]}
        add(short + ":file_ids_unique", len(definition_ids) == len(manifest["files"]["definitions"]), "File definitions have stable, unique IDs")
        for f in manifest["files"]["definitions"]:
            path = repo / f["path"]
            if f["current_or_proposed_location"] == "current":
                add(short + ":file_exists:" + f["file_id"], path.is_file(), f["path"])
                if f["content_sha256"]:
                    add(short + ":file_hash:" + f["file_id"], path.is_file() and file_sha(path) == f["content_sha256"], "Current owned-file hash")
            add(short + ":file_single_owner:" + f["file_id"], f["path"] not in owners or owners[f["path"]] == short, "Exclusive module ownership")
            owners[f["path"]] = short
        if manifest["files"]["scope_status"] == "closed":
            declared = {f["path"] for f in manifest["files"]["definitions"]}
            runtime_files = {p.relative_to(repo).as_posix() for p in (repo / root).rglob("*") if p.is_file() and p.suffix in {".py", ".mq4", ".mqh", ".dll"}}
            add(short + ":closed_file_scope", runtime_files <= declared, sorted(runtime_files - declared))
        def check_use(use, address, exclusive=False):
            records = {f["file_id"]: f for f in manifest["files"]["definitions"]} if exclusive else shared_records
            f = records.get(use["file_id"])
            add(short + ":file_use:" + address, bool(f and f["path"] == use["path"]), "Local exclusive/global shared reference resolves")
            if f and not exclusive:
                add(short + ":shared_topology:" + address,
                    any(c["module_id"] == identity["module_id"] for c in f["consumers"]), "Local module appears in global consumer topology")
        for use in manifest["files"]["shared_uses"]:
            check_use(use, use["file_id"])
        for step in manifest["process_steps"]:
            record = process_records.get(step["step_id"])
            add(short + ":process_ref:" + step["step_id"], bool(record and record["step_code"] == step["step_code"]), "Live process identity")
            if record:
                add(short + ":process_owner:" + step["step_id"],
                    record["owner_module_id"] == identity["module_id"] if step["participation_role"] == "primary_owner" else identity["module_id"] in record.get("supporting_module_ids", []), "No duplicate or fabricated step ownership")
            for cid in step["contract_refs"]:
                add(short + ":process_contract:" + cid, cid in contract_records, "Step contract registry record resolves")
            exclusive_ids = {u["file_id"] for u in step["exclusive_files"]}
            shared_ids = {u["file_id"] for u in step["shared_files"]}
            add(short + ":usage_partition:" + step["step_id"], not exclusive_ids.intersection(shared_ids), "Exactly two disjoint logical usage groups")
            for use in step["exclusive_files"]:
                check_use(use, step["step_id"] + use["file_id"], True)
            for use in step["shared_files"]:
                check_use(use, step["step_id"] + use["file_id"])
            transition_ids = {t["transition_id"] for t in manifest["state"]["transitions"]}
            add(short + ":transition_refs:" + step["step_id"], set(step["state_transition_refs"]) <= transition_ids, "Module-owned state transition refs resolve")
        for use in manifest["contracts"]:
            authority = use["authority_path"]
            if authority:
                add(short + ":contract_authority:" + use["usage_id"], (repo / authority).is_file(), authority)
            elif check_readiness:
                add(short + ":contract_authority:" + use["usage_id"], False, "Unknown mandatory contract authority")
            if use["contract_id"] and authority and authority.endswith("contract_registry.jsonl"):
                add(short + ":contract_identity:" + use["usage_id"], use["contract_id"] in contract_records, "Exact contract identity")
            if use["schema_path"]:
                add(short + ":contract_schema:" + use["usage_id"], (repo / use["schema_path"]).is_file(), "A schema path must be real")
            else:
                add(short + ":contract_schema_gap:" + use["usage_id"], bool(use["gap_ids"]), "Missing schema must have an explicit tracked gap")
        if check_readiness:
            add(short + ":specification_ready", manifest["reconciliation"]["specification_ready"], "Mandatory gaps and unresolved semantics must be closed before P6")
    failure_count = sum(c["status"] in {"FAIL", "UNAVAILABLE"} for c in checks)
    return {"status": "PASS" if not failure_count else "BLOCKED", "schema_valid_count": schema_valid_count,
            "specification_ready_count": sum(m.get("reconciliation", {}).get("specification_ready", False) for m in manifests),
            "implementation_verified_count": sum(m.get("reconciliation", {}).get("implementation_verified", False) for m in manifests),
            "blocking_failure_count": failure_count, "checks": checks}


def validate_repository(repo: Path, *, mode: str, structural_only: bool = False,
                        check_projection_parity: bool = True) -> dict:
    control = repo / "governance/module_consolidation"
    universe = load(control / "module_universe.json")
    expected_roots = {u["root"] for u in universe}
    actual_roots = {p.name for p in repo.glob("m[0-9][0-9][0-9][0-9]-*") if p.is_dir()}
    paths = [control / "staging" / u["short_id"] / "manifest.v2.candidate.json" if mode == "candidate" else repo / u["root"] / "manifest.json" for u in universe]
    missing = [p.relative_to(repo).as_posix() for p in paths if not p.is_file()]
    shared_path = control / "staging/shared_file_registry.candidate.json" if mode == "candidate" else repo / SHARED
    shared = load(shared_path) if shared_path.is_file() else {"records": []}
    manifests = [load(p) for p in paths if p.is_file()]
    if mode == "active" and any(m.get("schema_version") != "2.0.0" for m in manifests):
        report = {"status": "BLOCKED", "schema_valid_count": 0, "specification_ready_count": 0, "implementation_verified_count": 0,
                  "blocking_failure_count": 1, "checks": [{"check_id": "active_v2_cutover", "status": "FAIL", "detail": "Active roots remain v1; no authority cutover has occurred."}]}
    else:
        report = validate_manifests(manifests, universe, repo, shared, check_readiness=not structural_only)
    def add(code, ok, detail):
        report["checks"].append({"check_id": code, "status": "PASS" if ok else "FAIL", "detail": detail})
    add("root_universe", expected_roots == actual_roots and len(actual_roots) == 34, "Exactly 34 specified canonical roots")
    add("root_manifest_count", sum((repo / r / "manifest.json").is_file() for r in expected_roots) == 34, "34 root manifests")
    add("candidate_or_active_paths", not missing, missing)
    add("shared_registry_present", shared_path.is_file(), shared_path.relative_to(repo).as_posix())
    baseline = load(control / "run/baseline.json")
    if mode == "candidate":
        add("active_roots_unchanged", all(file_sha(repo / r / "manifest.json") == h for r, h in baseline["original_manifest_hashes"].items()), "No active mutation before cutover")
        add("candidate_authority_only", all(m.get("authority", {}).get("status") == "candidate" for m in manifests), "Staging cannot claim active authority")
    source_ledger = jsonl(control / "run/source_processing_ledger.jsonl")
    stale = [s["path"] for s in source_ledger if not (repo / s["path"]).is_file() or file_sha(repo / s["path"]) != s["sha256"]]
    lineage_path = control / "run/source_version_lineage.json"
    lineage = load(lineage_path).get("versions", []) if lineage_path.is_file() else []
    replacement_versions = {s["path"]: s for s in lineage}
    stale = [path for path in stale if not (
        path in replacement_versions and (repo / path).is_file()
        and file_sha(repo / path) == replacement_versions[path]["current_sha256"]
        and replacement_versions[path]["baseline_sha256"] == next(s["sha256"] for s in source_ledger if s["path"] == path)
        and (repo / replacement_versions[path]["baseline_snapshot_path"]).is_file()
        and file_sha(repo / replacement_versions[path]["baseline_snapshot_path"]) == replacement_versions[path]["baseline_sha256"])]
    add("frozen_source_hashes", not stale, stale)
    claim_rows = jsonl(control / "run/claim_ledger.jsonl")
    claim_sources = {}
    claim_errors = []
    for claim in claim_rows:
        path = evidence_version(repo, claim["source_path"], claim["source_sha256"], replacement_versions)
        source_key = (claim["source_path"], claim["source_sha256"])
        if source_key not in claim_sources:
            claim_sources[source_key] = (file_sha(path), jsonl(path) if path.suffix == ".jsonl" else load(path) if path.suffix == ".json" else None) if path.is_file() else (None, None)
        source_hash, contents = claim_sources[source_key]
        locator = claim.get("source_locator", {})
        try:
            if source_hash != claim["source_sha256"]:
                raise ValueError("source hash changed")
            if locator.get("json_pointer") is not None:
                pointer(contents, locator["json_pointer"])
        except (KeyError, IndexError, ValueError, TypeError):
            claim_errors.append(claim["claim_id"])
    add("claim_source_hashes_and_locators", not claim_errors, {"claim_count": len(claim_rows), "invalid_claim_ids": claim_errors})
    impossible = [s["source_id"] for s in source_ledger if (s["safe_to_archive"] and not s["fully_scraped"]) or (s["fully_scraped"] and s["unresolved_claim_count"])]
    add("source_state_axes", not impossible, impossible)
    for receipt_path in (repo / "archive/module-supporting-docs").glob("*/*/receipt.json"):
        receipt = load(receipt_path)
        original = receipt_path.parent / receipt["archive_original_filename"]
        add("archive_receipt:" + str(receipt_path.relative_to(repo)), original.is_file() and file_sha(original) == receipt["original_sha256"] == receipt["archived_sha256"], "Byte-identical archived original")
    if not structural_only:
        gaps = jsonl(control / "run/blocker_resolution_queue.jsonl")
        unresolved = [g["blocker_id"] for g in gaps if g["severity"] == "blocking" and g["resolution_state"] != "resolved"]
        add("mandatory_blockers", not unresolved, {"count": len(unresolved), "ids": unresolved})
        unreviewed = [s["source_id"] for s in source_ledger if s.get("in_scope") is True and not s["fully_scraped"]]
        add("source_reconciliation_complete", not unreviewed, {"count": len(unreviewed), "source_ids": unreviewed})
        undecided_scope = [s["source_id"] for s in source_ledger if s.get("in_scope") is None]
        add("source_scope_review_complete", not undecided_scope, {"count": len(undecided_scope)})
        claims = jsonl(control / "run/claim_ledger.jsonl")
        unapplied = [c["claim_id"] for c in claims if c.get("disposition") in {"MIGRATE", "MERGE"} and not c.get("active_authority_applied")]
        add("accepted_claims_active_and_verified", not unapplied, {"count": len(unapplied)})
    if mode == "active":
        add("active_shared_authority", shared.get("authority_status") == "canonical", "Shared topology must be canonical at cutover")
        bundle = load(repo / BUNDLE)
        if check_projection_parity:
            report["checks"].extend(validate_projection_document(bundle, manifests))
        authority = load(repo / "EAFIX_auth_docs/00_doc_control_and_authority/doc_authority.json")
        shadow = validate_authority_routing(authority)
        add("no_shadow_module_authority", not shadow, shadow)
    writers = load(control / "run/writer_inventory.json")
    add("writer_review_complete", writers.get("pending_review_count") == 0, "All existing writer matches reviewed")
    add("no_reverse_writer", not any(w.get("direction") == "supporting_to_root" for w in writers["writers"]), "No configured reverse generation")
    report.update({"mode": mode, "validation_scope": "structural_only" if structural_only else "full_cutover_gate",
                   "baseline_commit": baseline["baseline_commit"], "module_denominator": 34, "source_version_count": len(source_ledger),
                   "generated_projections_checked": mode == "active" and check_projection_parity, "live_trading_run": False,
                   "unavailable_runtime_validations": ["Windows runtime", "MQL4 compiler and MT4 execution"]})
    report["blocking_failure_count"] = sum(c["status"] in {"FAIL", "UNAVAILABLE"} for c in report["checks"])
    report["status"] = "PASS" if not report["blocking_failure_count"] else "BLOCKED"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--mode", choices=["candidate", "active"], default="active")
    parser.add_argument("--structural-only", action="store_true", help="Partial check only; cannot approve cutover")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = validate_repository(args.repo_root.resolve(), mode=args.mode, structural_only=args.structural_only)
    except (ValueError, KeyError, FileNotFoundError) as error:
        result = {"status": "BLOCKED", "blocking_failure_count": 1, "error": str(error), "validation_scope": "aborted"}
    if args.report:
        write(args.report, result)
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

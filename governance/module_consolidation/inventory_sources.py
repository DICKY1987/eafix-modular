"""Pin and inventory evidence without making semantic or authority mutations."""
from __future__ import annotations

import argparse
import ast
import csv
import mimetypes
import platform
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from authority_core import BUNDLE, CONTROL, REPO, file_sha, git, leaves, load, sha_bytes, value_sha, write, write_jsonl

WRITER_TERMS = re.compile(r"atomic_module_manifest|manifest\.json|eafix_module_manifests_bundle|"
                         r"module_catalog|process_step_catalog|context_packets|module_registry|process_registry|"
                         r"manifest_generation|generate_manifests|registry_core|build_registries|"
                         r"eafix_unified_atomic_module_schema|generated_from_canonical_sources")
WRITER_FILES = {".py", ".ps1", ".sh", ".yaml", ".yml"}
HISTORICAL_PREFIXES = ("Master_Archive/", "branch-archive/", "archive/", "EAFIX_auth_docs/99_archive_")


def drift(a, b, address=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(a.keys() | b.keys()):
            token = key.replace("~", "~0").replace("/", "~1")
            if key not in a or key not in b:
                yield {"json_pointer": address + "/" + token, "root_present": key in a,
                       "bundle_present": key in b, "root_value": a.get(key), "bundle_value": b.get(key)}
            else:
                yield from drift(a[key], b[key], address + "/" + token)
    elif a != b:
        yield {"json_pointer": address, "root_value": a, "bundle_value": b,
               "root_present": True, "bundle_present": True}


def classify(path: str, data: bytes) -> tuple[str, bool, str]:
    if path.startswith(HISTORICAL_PREFIXES):
        return "historical_evidence", False, "Retain historical evidence; not an active specification input."
    if path.endswith(".gitkeep") or not data.strip():
        return "scaffold_placeholder", False, "Empty scaffold contains no specification claims."
    if re.match(r"m\d{4}-[^/]+/manifest\.json$", path):
        return "active_v1_module_manifest", True, "Active until a coordinated P6 cutover passes."
    if path.startswith("context_packets/") or "/generated/" in path or path == BUNDLE:
        return "projection_or_competing_representation", True, "Compare with roots; no independent promotion."
    if path.startswith("contracts/"):
        return "live_shared_contract", True, "Shared contract authority retained outside module manifests."
    if path.startswith("EAFIX_auth_docs/01_canonical_registries/"):
        return "specialized_registry_or_schema", True, "Preserve specialized scope; review authority routing."
    if path.startswith(("EAFIX_auth_docs/", "services/", "shared/", "mt4/", "P_mql4/", "context_packets/",
                        "governance/", "docs/")) or re.match(r"m\d{4}-", path):
        return "supporting_evidence", True, "Retain until claim review and independent archive evaluation."
    return "scope_review_required", None, "Scope not decided by a filename scan."


def writer_review(path: str, text: str) -> dict:
    historical = path.startswith(HISTORICAL_PREFIXES)
    write_calls = []
    if path.endswith(".py"):
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = ast.unparse(node.func)
                    if any(term in name for term in ("write", "dump", "copy", "move", "open")):
                        write_calls.append({"line": node.lineno, "call": name})
        except SyntaxError:
            write_calls.append({"line": None, "call": "UNPARSEABLE_SCRIPT_REQUIRES_REVIEW"})
    matches = [{"line": n, "excerpt": line.strip()[:240]} for n, line in enumerate(text.splitlines(), 1)
               if WRITER_TERMS.search(line)]
    # These classifications follow complete manual reads during this execution.
    reviewed = {
        ".github/workflows/1299900007260118_ci.yml": ("legacy_generation_ci", [], "Calls the atomic manifest validator, whose generator module is absent; replace at coordinated P6 cutover."),
        ".github/workflows/validate-module-structure.yml": ("validator_workflow", [], "Calls a read-only v1 structural validator."),
        "EA-REG/scripts/validate_identifier_map.py": ("legacy_identifier_validator", [], "Read-only compatibility validator; does not write module roots."),
        "ci/2099900300260118_validate_atomic_module_manifests.py": ("legacy_generation_ci", ["EAFIX_auth_docs/manifests/"], "Calls missing tools.manifest_generation.generate_manifests; cannot verify current or v2 generation."),
        "tools/registries/build_registries.py": ("candidate_registry_to_projection", ["EAFIX_auth_docs/generated/registries/"], "CLI forwards to registry_core.run; does not write root manifests."),
        "tools/registries/validate_record_schemas.py": ("read_only_validator", [], "Reads registry records and validates schemas."),
        "tools/registries/validate_registry_authority.py": ("read_only_validator", [], "Reads registry records and validates authority fields."),
        "tools/registries/validate_registry_references.py": ("read_only_validator", [], "Reads registry records and validates cross references."),
        "tools/registries/validate_registry_ids.py": ("read_only_validator", [], "Checks current registry identifiers without writing."),
        "tools/registries/generate_registry_snapshots.py": ("candidate_registry_to_projection", ["EAFIX_auth_docs/generated/registries/"], "Wrapper calls registry_core.run; same one-way output scope."),
        "tools/registries/generate_registry_views.py": ("candidate_registry_to_projection", ["EAFIX_auth_docs/generated/registries/"], "Wrapper calls registry_core.run; same one-way output scope."),
        "tools/registries/report_registry_conflicts.py": ("verification_projection", ["EAFIX_auth_docs/generated/registries/"], "Runs registry_core in report-only mode; no root manifest writes."),
        ".github/workflows/registry-validation.yml": ("candidate_registry_to_projection", ["EAFIX_auth_docs/generated/registries/"], "Regenerates shadow registry reports; must retain candidate status for non-process registries."),
        "tests/registries/test_registry_framework.py": ("test_only", ["temporary test directories"], "Tests current records and no-write check mode; mocks CLI run calls."),
        "tools/validate_module_structure.py": ("read_only_validator", [], "No writes; validates root file ownership."),
        "tools/migration/generate_p20_outputs.py": ("root_to_projection", ["m00*/m00*-context/work-cells/*.json", "docs/reference/generated/indicator_record.schema.json"], "Reads roots and owned schema; writes five work cells and a schema projection only."),
        "tools/registries/registry_core.py": ("candidate_registry_to_projection", ["EAFIX_auth_docs/generated/registries/"], "Preserve shadow registry output; redirect module projections before cutover."),
        "tools/registries/verify_process_consolidation.py": ("process_validator_and_guarded_governance", ["process consolidation verification reports"], "Process authority has separate governance; no module-root generation."),
        "governance/module_consolidation/tracking/build_ssot.py": ("tracking_projection", ["governance/module_consolidation/tracking/eafix_consolidation_ssot.json"], "Replace fixed baseline and read governed decisions/status; never write module facts."),
        "EAFIX_auth_docs/generate_eafix_ssot_registry_verification_package.py": ("verification_projection", ["EAFIX_auth_docs/EAFIX_SSOT_REGISTRY_DELIVERY_OBLIGATION_MATRIX.generated.json", "EAFIX_auth_docs/EAFIX_SSOT_REGISTRY_DELIVERY_CHECKLIST.generated.md", "verification run reports"], "Reads requirements and writes verification package; no root manifest output."),
        "EAFIX_auth_docs/validate_eafix_ssot_registry_verification_package.py": ("verification_report", ["caller-selected JSON verification report"], "Validator report output does not feed module roots."),
    }
    direction, outputs, reason = reviewed.get(path, ("workflow_or_script_requires_review", [], "Static matches are not proof of writer safety."))
    if historical:
        direction, reason = "historical_inactive", "Archived script; not an approved current writer."
    return {"path": path, "content_sha256": file_sha(REPO / path), "direction": direction,
            "purpose": reason, "inputs": sorted(set(WRITER_TERMS.findall(text))), "outputs": outputs,
            "write_calls": write_calls, "matches": matches,
            "required_change_before_cutover": "Resolve unreviewed writers and redirect shadow module projections.",
            "review_status": "reviewed" if path in reviewed or historical else "pending"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attachments", type=Path)
    parser.add_argument("--instructions", type=Path)
    args = parser.parse_args()
    baseline_file = CONTROL / "run/baseline.json"
    roots = sorted(p for p in REPO.glob("m[0-9][0-9][0-9][0-9]-*") if p.is_dir())
    if len(roots) != 34:
        raise ValueError("BLOCKED: canonical universe is not 34")
    head = git("rev-parse", "HEAD")
    if baseline_file.exists():
        baseline = load(baseline_file)
        if baseline["baseline_commit"] != git("rev-parse", "origin/master"):
            raise ValueError("STALE_BASELINE: master changed; new execution baseline required")
    else:
        if head != git("rev-parse", "origin/master"):
            raise ValueError("Start from freshly verified current master")
        baseline = {"schema_version": "1.0.0", "baseline_commit": head,
                    "repository": "https://github.com/DICKY1987/eafix-modular", "default_branch": "master",
                    "branch": git("branch", "--show-current"), "pinned_at_utc": datetime.now(timezone.utc).isoformat(),
                    "remote_baseline_verified": True, "environment": {"os": platform.platform(), "python": sys.version,
                        "windows_runtime": "UNAVAILABLE", "mql4_compiler": "UNAVAILABLE", "live_trading_run": False},
                    "original_manifest_hashes": {p.name: file_sha(p / "manifest.json") for p in roots}}
        write(baseline_file, baseline)
    universe = []
    for root in roots:
        m = load(root / "manifest.json")
        mid = (root / ".module-id").read_text().strip()
        if mid != m["module_identity"]["module_id"] or not re.fullmatch(r"5\d{19}", mid):
            raise ValueError(f"IDENTITY_MISMATCH: {root.name}")
        universe.append({"short_id": root.name[:5], "root": root.name, "module_id": mid,
                         "canonical_symbol": m["module_identity"]["canonical_symbol"]})
    write(CONTROL / "module_universe.json", universe)
    if args.attachments:
        for source in sorted(args.attachments.iterdir()):
            if source.is_file():
                target = CONTROL / "inputs" / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
    if args.instructions:
        target = CONTROL / "inputs/00-execution-instructions.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.instructions, target)
    expected_roots = set(re.findall(r"`(m\d{4}-[^`/]+)`", (CONTROL / "inputs/00-execution-instructions.txt").read_text()))
    if not expected_roots or expected_roots != {u["root"] for u in universe}:
        raise ValueError("BLOCKED: roots do not equal the owner's canonical universe")
    files = subprocess.check_output(["git", "ls-tree", "-rz", "--name-only", baseline["baseline_commit"]], cwd=REPO).decode().rstrip("\0").split("\0")
    changed_paths = set(subprocess.check_output(["git", "diff", "--name-only", "-z", baseline["baseline_commit"]], cwd=REPO).decode().rstrip("\0").split("\0"))
    sources = []
    writers = []
    for relative in files:
        path = REPO / relative
        if not path.is_file():
            continue
        data = subprocess.check_output(["git", "show", f"{baseline['baseline_commit']}:{relative}"], cwd=REPO) if relative in changed_paths else path.read_bytes()
        content_hash = sha_bytes(data)
        authority, in_scope, reason = classify(relative, data)
        record = {"source_id": "SRC-" + value_sha([relative, content_hash])[:20], "path": relative,
                  "source_class": "repository", "source_commit": baseline["baseline_commit"],
                  "acquired_at_utc": baseline["pinned_at_utc"], "sha256": content_hash, "size_bytes": len(data),
                  "mime_type": mimetypes.guess_type(relative)[0] or "application/octet-stream",
                  "authority_classification": authority, "in_scope": in_scope,
                  "source_status": "inventoried", "extraction_status": "not_started" if in_scope is not False else "out_of_scope",
                  "reconciliation_status": "not_started", "relevant_claim_count": 0, "unresolved_claim_count": 0,
                  "accepted_claim_count": 0, "rejected_claim_count": 0, "retained_external_count": 0,
                  "fully_scraped": False, "safe_to_archive": False, "retention": "blocked_from_archival",
                  "retention_reason": reason, "archive_destination": None, "archive_verification_hash": None,
                  "superseded_by": None, "retained_active_authority_ref": relative if authority.startswith("active") else None}
        sources.append(record)
        if path.suffix in WRITER_FILES:
            text = data.decode("utf-8-sig", errors="replace")
            if WRITER_TERMS.search(text) or WRITER_TERMS.search(relative):
                writers.append(writer_review(relative, text))
    for path in sorted((CONTROL / "inputs").glob("*")):
        relative = path.relative_to(REPO).as_posix()
        sources.append({"source_id": "EXT-" + value_sha([relative, file_sha(path)])[:20], "path": relative,
                        "source_class": "external_attachment", "source_commit": None,
                        "acquired_at_utc": baseline["pinned_at_utc"], "sha256": file_sha(path), "size_bytes": path.stat().st_size,
                        "mime_type": mimetypes.guess_type(path.name)[0] or "text/plain", "in_scope": True,
                        "authority_classification": "execution_instruction" if path.name.startswith("00-") else "historical_supporting_evidence",
                        "source_status": "inventoried", "extraction_status": "not_started", "reconciliation_status": "not_started",
                        "relevant_claim_count": 0, "unresolved_claim_count": 0, "accepted_claim_count": 0,
                        "rejected_claim_count": 0, "retained_external_count": 0, "fully_scraped": False, "safe_to_archive": False,
                        "retention": "blocked_from_archival", "retention_reason": "Historical evidence must be revalidated against current master.",
                        "archive_destination": None, "archive_verification_hash": None, "superseded_by": None,
                        "retained_active_authority_ref": None})
    write_jsonl(CONTROL / "run/source_processing_ledger.jsonl", sources)
    write(CONTROL / "run/writer_inventory.json", {"baseline_commit": baseline["baseline_commit"],
          "whole_repository_files_scanned": len(files), "writers": writers,
          "pending_review_count": sum(x["review_status"] == "pending" for x in writers),
          "new_program_writers_inventory_required_before_cutover": True})
    bundle = load(REPO / BUNDLE)
    by_id = {m["module_identity"]["module_id"]: m for m in bundle["manifests"]}
    differences = []
    for module in universe:
        original = load(REPO / module["root"] / "manifest.json")
        other = by_id.get(module["module_id"])
        changes = list(drift(original, other)) if other is not None else [{"error": "MISSING_BUNDLE_ENTRY"}]
        differences.append({"module_short_id": module["short_id"], "module_id": module["module_id"],
                            "difference_count": len(changes), "differences": changes,
                            "disposition": "preserve_root_default_pending_unique_claim_review", "decision_id": "DEC-007"})
    write(CONTROL / "run/root_bundle_drift_report.json", {"baseline_commit": baseline["baseline_commit"],
          "bundle_path": BUNDLE, "bundle_sha256": file_sha(REPO / BUNDLE), "module_count": len(differences),
          "differing_modules": sum(bool(x["difference_count"]) for x in differences), "modules": differences})
    decisions_path = CONTROL / "inputs/13-EAFIX_86_file_module_location_decisions-1-.json"
    if decisions_path.is_file():
        historical = load(decisions_path)
        records = []
        for row in historical["decisions"]:
            path = row.get("source_path") or row.get("path")
            exists = bool(path and (REPO / path).exists())
            old_commit = historical["commit_sha"]
            try:
                old_bytes = subprocess.check_output(["git", "show", f"{old_commit}:{path}"], cwd=REPO, stderr=subprocess.DEVNULL)
                old_hash = __import__("hashlib").sha256(old_bytes).hexdigest()
            except subprocess.CalledProcessError:
                old_hash = None
            current_hash = file_sha(REPO / path) if exists and (REPO / path).is_file() else None
            state = "content_unchanged" if old_hash and old_hash == current_hash else "content_changed" if old_hash and current_hash else "path_missing" if not exists else "historical_bytes_unavailable"
            records.append({"source_path": path, "historical_commit": old_commit, "historical_sha256": old_hash,
                            "current_sha256": current_hash, "revalidation_state": state,
                            "historical_decision": row, "semantic_revalidation": "pending",
                            "physical_action_executed": False, "decision_id": "DEC-017"})
        write(CONTROL / "run/historical_86_revalidation.json", {"record_count": len(records), "records": records})
    print({"baseline": baseline["baseline_commit"], "roots": len(universe), "source_versions": len(sources),
           "drifting_modules": sum(bool(x["difference_count"]) for x in differences),
           "writer_matches": len(writers), "writer_pending": sum(x["review_status"] == "pending" for x in writers),
           "scope_counts": dict(Counter(str(x["in_scope"]) for x in sources))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

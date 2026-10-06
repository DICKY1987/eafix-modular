"""Offline fixtures for structural checks and fail-closed mutation guards.

Positive fixtures do not waive incomplete specification or source reconciliation.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from authority_core import BUNDLE, CONTROL, REPO, archive_copy, file_sha, guarded_replace, load, pointer, write
from generate_projections import projection_outputs
from validate_consolidation import validate_authority_routing, validate_manifests, validate_projection_document


def fixtures():
    universe = load(CONTROL / "module_universe.json")
    manifests = [load(CONTROL / "staging" / u["short_id"] / "manifest.v2.candidate.json") for u in universe]
    shared = load(CONTROL / "staging/shared_file_registry.candidate.json")
    return universe, manifests, shared


def run() -> dict:
    universe, originals, shared = fixtures()
    baseline = validate_manifests(originals, universe, REPO, shared, check_readiness=False)
    checks = [{"fixture": "all_34_structural", "passed": baseline["status"] == "PASS"}]
    import jsonschema
    schema = load(REPO / "EAFIX_auth_docs/01_canonical_registries/eafix_unified_atomic_module_schema_v2_0_0.json")
    validator = jsonschema.Draft202012Validator(schema)
    for path in sorted((CONTROL / "validation/positive").glob("*.json")):
        recipe = load(path)
        manifest = next(m for m in originals if m["module_identity"]["short_id"] == recipe["module"])
        checks.append({"fixture": path.name, "passed": not list(validator.iter_errors(manifest)) and manifest["profile"] == recipe["expected_profile"]
                       and (not recipe.get("zero_process_steps") or manifest["process_steps"] == []),
                       "scope": "structural_only"})
    for path in sorted((CONTROL / "validation/negative").glob("*.json")):
        recipe = load(path)
        manifests = copy.deepcopy(originals)
        changed_shared = copy.deepcopy(shared)
        kind = recipe["mutation"]
        target = manifests[8]
        if kind == "fake_na_step":
            target["process_steps"][0]["step_id"] = "0"
        elif kind == "duplicate_permanent_id":
            target["module_identity"]["module_id"] = manifests[0]["module_identity"]["module_id"]
        elif kind == "fake_external_path":
            target["contracts"][0]["authority_path"] = "contracts/does-not-exist.json"
        elif kind == "missing_evidence":
            target["purpose_and_boundaries"]["purpose"]["value"] = "Unapproved changed purpose"
        elif kind == "missing_global_shared_file":
            use = next(u for m in manifests for u in m["files"]["shared_uses"])
            changed_shared["records"] = [r for r in changed_shared["records"] if r["file_id"] != use["file_id"]]
        elif kind == "stale_baseline":
            target["authority"]["effective_baseline_commit"] = "0" * 40
        elif kind == "invalid_applicability_knowledge":
            target["runtime"]["entrypoints"].update(applicability="not_applicable", knowledge="unknown")
        elif kind == "closed_scope_undeclared_runtime":
            # The indicator schema is owned, but its Python test is deliberately undeclared here.
            target["files"]["scope_status"] = "closed"
            target["files"]["definitions"] = [f for f in target["files"]["definitions"] if not f["path"].endswith(".py")]
        elif kind == "bundle_canonical":
            bundle = projection_outputs(REPO, candidate=True)[BUNDLE]
            bundle["authority_policy"] = "canonical"
            errors = [c["check_id"] for c in validate_projection_document(bundle, manifests) if c["status"] == "FAIL"]
        elif kind == "duplicate_authority":
            errors = ["no_shadow_module_authority"] if validate_authority_routing({"entries": [{"relative_path": BUNDLE, "classification": "canonical"}]}) else []
        else:
            raise ValueError("Unknown fixture mutation " + kind)
        if kind not in {"bundle_canonical", "duplicate_authority"}:
            report = validate_manifests(manifests, universe, REPO, changed_shared, check_readiness=False)
            errors = [c["check_id"] for c in report["checks"] if c["status"] == "FAIL"]
        checks.append({"fixture": path.name, "passed": any(recipe["expected_check"] in error for error in errors),
                       "expected_check": recipe["expected_check"], "observed_failures": errors})
    baseline_commit = load(CONTROL / "run/baseline.json")["baseline_commit"]
    with tempfile.TemporaryDirectory() as directory:
        temp = Path(directory)
        source = temp / "source.json"
        write(source, {"a": 1})
        old = load(source)
        original_hash = file_sha(source)
        guarded_replace(source, original_hash, old, {"a": 2}, baseline_commit)
        before = source.read_bytes()
        try:
            guarded_replace(source, original_hash, old, {"a": 3}, baseline_commit)
            rejected = False
        except ValueError as error:
            rejected = "STALE_BASELINE" in str(error)
        checks.append({"fixture": "stale_patch_rejected_without_write", "passed": rejected and source.read_bytes() == before})
        original_hash = file_sha(source)
        receipt = {"fully_scraped": True, "safe_to_archive": True, "unresolved_claim_count": 0,
                   "original_sha256": original_hash, "source_path": "source.json", "restoration_path": "restored.json",
                   "active_authority": False, "required_live_input": False, "decision_id": "DISPOSABLE-FIXTURE"}
        archive = temp / "archive"
        archive_copy(source, archive, receipt)
        stored = load(archive / "receipt.json")
        restored = temp / stored["restoration_path"]
        restored.write_bytes((archive / stored["archive_original_filename"]).read_bytes())
        checks.append({"fixture": "byte_identical_archive_restore", "passed": file_sha(restored) == original_hash})
        try:
            archive_copy(source, temp / "bad_archive", {**receipt, "safe_to_archive": False})
            rejected = False
        except ValueError:
            rejected = True
        checks.append({"fixture": "fully_scraped_does_not_authorize_archive", "passed": rejected and not (temp / "bad_archive").exists()})
        try:
            archive_copy(source, temp / "live_archive", {**receipt, "required_live_input": True})
            rejected = False
        except ValueError:
            rejected = True
        checks.append({"fixture": "live_required_input_cannot_archive", "passed": rejected})
    hashes = {u["root"]: file_sha(REPO / u["root"] / "manifest.json") for u in universe}
    outputs = projection_outputs(REPO, candidate=True)
    rerun = projection_outputs(REPO, candidate=True)
    checks.append({"fixture": "projection_idempotence_and_no_root_writes", "passed": outputs == rerun and hashes == {
        u["root"]: file_sha(REPO / u["root"] / "manifest.json") for u in universe}, "output_count": len(outputs)})
    checks.append({"fixture": "json_pointer_empty_escaped_and_trailing_keys", "passed": pointer({"": {"": 7}, "a/b": 8}, "//") == 7
                   and pointer({"a/b": 8}, "/a~1b") == 8})
    return {"status": "PASS" if all(c["passed"] for c in checks) else "FAIL", "scope": "offline_structural_and_guard_fixtures",
            "passed_count": sum(c["passed"] for c in checks), "fixture_count": len(checks), "specification_readiness_waived": False,
            "archive_test_location": "disposable temporary directory", "checks": checks}


if __name__ == "__main__":
    result = run()
    write(CONTROL / "run/fixture_validation.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "checks"}, sort_keys=True))
    raise SystemExit(result["status"] != "PASS")

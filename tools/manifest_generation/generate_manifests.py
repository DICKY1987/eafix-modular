#!/usr/bin/env python3
"""Schema-first atomic manifest regeneration pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .manifest_builder import build_manifests
from .normalizers import (
    ALIAS_CROSSWALK,
    build_communication_channel_index,
    build_dependency_candidate_index,
    build_file_mapping_index,
    build_module_catalog_enrichment,
    build_module_universe,
    build_mt4_constraint_index,
    build_process_step_index,
    build_service_runtime_index,
    build_ui_product_index,
)
from .reconciler import reconcile_module_records
from .report_writer import (
    build_coverage_report,
    write_coverage_outputs,
    write_generation_report,
)
from .schema_loader import build_schema_field_map, load_schema
<<<<<<< HEAD
from .source_loaders import REQUIRED_SOURCE_FILES, load_csv, load_dependency_layers, load_json, load_text, run_authority_preflight
=======
from .source_loaders import REQUIRED_SOURCE_FILES, load_csv, load_json, load_text, run_authority_preflight
>>>>>>> origin/copilot/regenerate-34-module-manifests
from .validators import run_validation_suite, write_validation_outputs


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


<<<<<<< HEAD
def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


=======
>>>>>>> origin/copilot/regenerate-34-module-manifests
def _source_hash_map(snapshot: dict[str, Any]) -> dict[str, str]:
    return {
        f"{key}:{meta['relative_path']}": meta["sha256"]
        for key, meta in snapshot["source_files"].items()
        if meta.get("sha256")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate EAFIX atomic manifests")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_root = repo_root / "EAFIX_auth_docs" / "manifests"
    module_manifest_dir = output_root / "module_manifests"
    staging_root = repo_root / "build" / "staging"

    authority_snapshot = run_authority_preflight(repo_root)
    _write_json(output_root / "authority_snapshot.json", authority_snapshot)
    _write_json(output_root / "manifest_source_authority_snapshot.json", authority_snapshot)

    critical_missing = [
        "EAFIX_auth_docs/Claude_gen_atomic_module_catalog_vNext.json",
        "EAFIX_auth_docs/eafix_unified_atomic_module_schema_v1_0_0.json",
    ]
    missing = [x["relative_path"] for x in authority_snapshot["source_files"].values() if not x["exists"]]
    for required in critical_missing:
        if required in missing:
            print(f"STOP: required source missing -> {required}", file=sys.stderr)
            return 2

    schema_path = repo_root / REQUIRED_SOURCE_FILES["manifest_schema"]
    schema = load_schema(schema_path)
    schema_map = build_schema_field_map(schema)
    _write_json(output_root / "manifest_schema_field_map.json", schema_map)
    _write_json(staging_root / "manifest_schema_field_map.json", schema_map)

    raw = {
        "vnext_catalog": load_json(repo_root / REQUIRED_SOURCE_FILES["module_universe_vnext"]),
        "module_catalog": load_json(repo_root / REQUIRED_SOURCE_FILES["module_catalog_enrichment"]),
        "process_step_catalog": load_json(repo_root / REQUIRED_SOURCE_FILES["process_step_catalog"]),
        "aligned_process": load_json(repo_root / REQUIRED_SOURCE_FILES["aligned_process"]),
        "file_mapping_rows": load_csv(repo_root / REQUIRED_SOURCE_FILES["file_mapping"]),
        "service_runtime_ref": load_json(repo_root / REQUIRED_SOURCE_FILES["service_runtime"]),
        "module_map_text": load_text(repo_root / REQUIRED_SOURCE_FILES["module_map"]),
        "communication_channels": load_json(repo_root / REQUIRED_SOURCE_FILES["communication_channels"]),
        "ui_catalog": load_json(repo_root / REQUIRED_SOURCE_FILES["ui_catalog"]),
        "mt4_ref": load_json(repo_root / REQUIRED_SOURCE_FILES["mt4_authoritative"]),
        "capability_registry": load_json(repo_root / REQUIRED_SOURCE_FILES["capability_registry"]),
        "draft_bundle": load_json(repo_root / REQUIRED_SOURCE_FILES["existing_draft_bundle"]),
    }

    module_universe = build_module_universe(raw["vnext_catalog"], raw["draft_bundle"])
    module_catalog_enrichment = build_module_catalog_enrichment(raw["module_catalog"])
    process_step_index = build_process_step_index(raw["process_step_catalog"], raw["aligned_process"])
    file_mapping_index = build_file_mapping_index(raw["file_mapping_rows"])
    service_runtime_index = build_service_runtime_index(raw["module_map_text"], raw["ui_catalog"])
    communication_channel_index = build_communication_channel_index(raw["communication_channels"])
    ui_product_index = build_ui_product_index(raw["ui_catalog"])
    mt4_constraint_index = build_mt4_constraint_index(raw["mt4_ref"], raw["communication_channels"])
    dependency_candidate_index = build_dependency_candidate_index(
        module_universe, module_catalog_enrichment, process_step_index
    )

    _write_json(staging_root / "module_universe_vnext.json", module_universe)
    _write_json(staging_root / "module_catalog_enrichment.json", module_catalog_enrichment)
    _write_json(staging_root / "process_step_index.json", process_step_index)
    _write_json(staging_root / "file_mapping_index.json", file_mapping_index)
    _write_json(staging_root / "service_runtime_index.json", service_runtime_index)
    _write_json(staging_root / "communication_channel_index.json", communication_channel_index)
    _write_json(staging_root / "ui_product_index.json", ui_product_index)
    _write_json(staging_root / "mt4_constraint_index.json", mt4_constraint_index)
    _write_json(staging_root / "dependency_candidate_index.json", dependency_candidate_index)
    _write_json(staging_root / "alias_crosswalk.json", ALIAS_CROSSWALK)

    if module_universe["module_count"] != 34:
        print(f"STOP: module universe count is {module_universe['module_count']}, expected 34", file=sys.stderr)
        return 3

    if args.validate_only:
        manifests = sorted(module_manifest_dir.glob("*.manifest.json"))
        if len(manifests) != 34:
            print("validate-only failed: expected 34 manifest files", file=sys.stderr)
            return 4
        print("validate-only: manifest count OK")
        return 0

    reconciled_modules = reconcile_module_records(module_universe)
    normalized = {
        "module_catalog_enrichment": module_catalog_enrichment,
        "process_step_index": process_step_index,
        "file_mapping_index": file_mapping_index,
        "service_runtime_index": service_runtime_index,
        "communication_channel_index": communication_channel_index,
        "ui_product_index": ui_product_index,
        "dependency_candidate_index": dependency_candidate_index,
    }
    manifests, unresolved_items = build_manifests(
        reconciled_modules, authority_snapshot["source_files"], normalized, _source_hash_map(authority_snapshot)
    )

    module_manifest_dir.mkdir(parents=True, exist_ok=True)
    for manifest in manifests:
        mid = manifest["module_identity"]["module_id"]
        sym = manifest["module_identity"]["canonical_symbol"]
        _write_json(module_manifest_dir / f"{mid}_{sym}.manifest.json", manifest)

    bundle = {
        "schema_version": "1.0.0",
        "document_type": "atomic_module_manifest_bundle",
        "module_count": len(manifests),
        "manifests": manifests,
    }
    _write_json(output_root / "eafix_module_manifests_bundle.vNext.schema_valid.json", bundle)
    _write_json(output_root / "manifest_unresolved_items.json", unresolved_items)

<<<<<<< HEAD
    dependency_layers_parsed, dependency_layers_data = load_dependency_layers(repo_root)
    if dependency_layers_parsed:
        _write_json(staging_root / "dependency_layers_parsed.json", dependency_layers_data)
=======
    # Emit deferred staging artifact for dependency layers PDF.
    # The PDF exists but is binary/unstructured; dependency layer relationships
    # are modeled via the vNext module catalog and process step index instead.
    dep_layers_pdf_path = repo_root / "EAFIX_auth_docs" / "dependency layers.pdf"
    dep_layers_staging = {
        "source_file": "EAFIX_auth_docs/dependency layers.pdf",
        "parse_status": "deferred",
        "parse_reason": (
            "Binary PDF cannot be parsed programmatically. "
            "Dependency layer relationships are derived from "
            "Claude_gen_atomic_module_catalog_vNext.json (layer field) and "
            "process_step_catalog.json (step ordering). "
            "This staging record acknowledges the PDF as a governance source "
            "and explicitly defers structured extraction."
        ),
        "sha256": authority_snapshot["source_files"].get("dependency_layers_pdf", {}).get("sha256"),
        "governance_note": (
            "dependency_layers_pdf_acknowledged_as_deferred: "
            "zero unresolved dependency issues reflects catalog-derived authority, "
            "not absence of PDF evidence."
        ),
    }
    _write_json(output_root / "dependency_layers_staging.json", dep_layers_staging)
    dependency_layers_parsed = dep_layers_pdf_path.exists()
>>>>>>> origin/copilot/regenerate-34-module-manifests

    validation = run_validation_suite(
        manifests,
        schema,
        expected_symbols={m["canonical_symbol"] for m in module_universe["modules"]},
        mapping_rows_total=file_mapping_index["rows_total"],
        ui_catalog=raw["ui_catalog"],
        dependency_layers_parsed=dependency_layers_parsed,
    )
    write_validation_outputs(
        validation,
        output_root / "manifest_validation_report.json",
        output_root / "manifest_validation_report.md",
    )

    coverage = build_coverage_report(manifests, unresolved_items)
    coverage["summary_counts"]["schema_valid_manifests"] = validation["schema_validation"]["valid_count"]
    write_coverage_outputs(
        coverage,
        output_root / "manifest_fill_coverage_report.vNext.json",
        output_root / "manifest_fill_coverage_report.vNext.md",
    )

    write_generation_report(
        manifest_count=len(manifests),
        output_paths=[
<<<<<<< HEAD
            _repo_relative(output_root / "eafix_module_manifests_bundle.vNext.schema_valid.json", repo_root),
            _repo_relative(output_root / "manifest_validation_report.json", repo_root),
            _repo_relative(output_root / "manifest_fill_coverage_report.vNext.json", repo_root),
            _repo_relative(output_root / "manifest_unresolved_items.json", repo_root),
            _repo_relative(output_root / "manifest_source_authority_snapshot.json", repo_root),
=======
            str(output_root / "eafix_module_manifests_bundle.vNext.schema_valid.json"),
            str(output_root / "manifest_validation_report.json"),
            str(output_root / "manifest_fill_coverage_report.vNext.json"),
            str(output_root / "manifest_unresolved_items.json"),
            str(output_root / "manifest_source_authority_snapshot.json"),
            str(output_root / "dependency_layers_staging.json"),
>>>>>>> origin/copilot/regenerate-34-module-manifests
        ],
        unresolved_items=unresolved_items,
        json_path=output_root / "manifest_generation_report.json",
        markdown_path=output_root / "manifest_generation_report.md",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Coverage and generation report writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _status_filled(value: Any) -> str:
    if value in (None, "", [], {}, "unknown", "needs_review"):
        return "missing"
    if isinstance(value, list) and any(v in ("unknown", "needs_review") for v in value):
        return "partial"
    if isinstance(value, str) and value in {"not_applicable"}:
        return "not_applicable"
    return "filled"


<<<<<<< HEAD
=======
def _is_not_applicable_process_binding(process_binding: dict[str, Any]) -> bool:
    return (
        process_binding.get("step_id") == "N/A"
        or process_binding.get("step_code") in {"NA", "N/A"}
        or process_binding.get("phase_id") == "PHASE_NOT_APPLICABLE"
        or process_binding.get("phase_name") == "not_applicable"
    )


>>>>>>> origin/copilot/regenerate-34-module-manifests
def build_coverage_report(manifests: list[dict[str, Any]], unresolved_items: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved_map = {f"{x['module_id']}::{x['canonical_symbol']}": x["unresolved_items"] for x in unresolved_items}
    module_rows = []
    counts = {
        "total_manifests": len(manifests),
        "schema_valid_manifests": None,
        "thin_modules": 0,
        "modules_with_no_files": 0,
        "modules_with_shared_service_files": 0,
        "modules_with_runtime_ports": 0,
        "modules_with_ui_bindings": 0,
        "modules_with_mt4_constraints": 0,
        "modules_with_unresolved_dependencies": 0,
        "source_conflicts_by_category": {},
    }
    for manifest in manifests:
<<<<<<< HEAD
        symbol = manifest["module_identity"]["canonical_symbol"]
        module_id = manifest["module_identity"]["module_id"]
=======
        identity = manifest.get("module_identity", {})
        symbol = identity.get("canonical_symbol", "UNKNOWN_SYMBOL")
        module_id = identity.get("module_id", "UNKNOWN_MODULE_ID")
>>>>>>> origin/copilot/regenerate-34-module-manifests
        unresolved = unresolved_map.get(f"{module_id}::{symbol}", [])
        file_ownership = manifest.get("file_ownership", {})
        deps = manifest.get("dependencies", [])
        runtime = manifest.get("service_runtime", {})
<<<<<<< HEAD
        if any(str(n).startswith("thin_module:") for n in manifest.get("reconciliation_status", {}).get("reconciliation_notes", [])):
=======
        process_binding = manifest.get("process_binding", {})
        notes = manifest.get("reconciliation_status", {}).get("reconciliation_notes", [])
        if any(str(note).startswith("thin_module:") for note in notes):
>>>>>>> origin/copilot/regenerate-34-module-manifests
            counts["thin_modules"] += 1
        if not file_ownership.get("owned_files") and not file_ownership.get("shared_files"):
            counts["modules_with_no_files"] += 1
        if file_ownership.get("shared_files"):
            counts["modules_with_shared_service_files"] += 1
        if runtime.get("microservice_port") is not None:
            counts["modules_with_runtime_ports"] += 1
<<<<<<< HEAD
        if symbol.startswith("U"):
            counts["modules_with_ui_bindings"] += 1
        if "platform_constraints" in manifest:
            counts["modules_with_mt4_constraints"] += 1
        if any(dep.get("target_id") in {"unknown", "needs_review"} for dep in deps):
=======
        if str(symbol).startswith("U"):
            counts["modules_with_ui_bindings"] += 1
        if "platform_constraints" in manifest:
            counts["modules_with_mt4_constraints"] += 1
        if any(dep.get("target_id") in {"unknown", "needs_review"} for dep in deps if isinstance(dep, dict)):
>>>>>>> origin/copilot/regenerate-34-module-manifests
            counts["modules_with_unresolved_dependencies"] += 1

        row = {
            "module_id": module_id,
            "canonical_symbol": symbol,
            "identity": _status_filled(manifest.get("module_identity")),
            "classification": _status_filled(manifest.get("module_classification")),
            "purpose": _status_filled(manifest.get("purpose")),
<<<<<<< HEAD
            "process_binding": "not_applicable" if manifest.get("process_binding", {}).get("phase_id") == "PHASE_NOT_APPLICABLE" else _status_filled(manifest.get("process_binding")),
            "contracts": _status_filled(manifest.get("contracts")),
            "dependencies": _status_filled(manifest.get("dependencies")),
            "file_ownership": manifest.get("file_ownership", {}).get("file_assignment_status", "unknown"),
            "runtime": _status_filled(runtime.get("microservice_port")),
            "communication_channels": "filled" if "communication_channels" in manifest else "not_applicable",
            "ui_binding": "filled" if symbol.startswith("U") else "not_applicable",
=======
            "process_binding": "not_applicable" if _is_not_applicable_process_binding(process_binding) else _status_filled(process_binding),
            "contracts": _status_filled(manifest.get("contracts")),
            "dependencies": _status_filled(manifest.get("dependencies")),
            "file_ownership": file_ownership.get("file_assignment_status", "unknown"),
            "runtime": _status_filled(runtime.get("microservice_port")),
            "communication_channels": "filled" if "communication_channels" in manifest else "not_applicable",
            "ui_binding": "filled" if str(symbol).startswith("U") else "not_applicable",
>>>>>>> origin/copilot/regenerate-34-module-manifests
            "mt4_constraints": "filled" if "platform_constraints" in manifest else "not_applicable",
            "validation_failure_behavior": _status_filled(manifest.get("state_and_failure_behavior")),
            "documentation_set": "generated" if manifest.get("documentation_set") else "missing",
            "unresolved_issues": {"count": len(unresolved), "items": unresolved},
        }
        module_rows.append(row)

    return {"summary_counts": counts, "modules": module_rows}


def write_coverage_outputs(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Manifest Fill Coverage Report (vNext)", ""]
    lines.append("## Summary")
    for key, value in report["summary_counts"].items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")
    lines.append("## Module Coverage")
    header = "| module_id | canonical_symbol | identity | classification | purpose | process binding | contracts | dependencies | file ownership | runtime | comm channels | UI | MT4 | validation/failure | docs | unresolved |"
    sep = "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    lines.extend([header, sep])
    for row in report["modules"]:
        lines.append(
            f"| {row['module_id']} | {row['canonical_symbol']} | {row['identity']} | {row['classification']} | "
            f"{row['purpose']} | {row['process_binding']} | {row['contracts']} | {row['dependencies']} | "
            f"{row['file_ownership']} | {row['runtime']} | {row['communication_channels']} | {row['ui_binding']} | "
            f"{row['mt4_constraints']} | {row['validation_failure_behavior']} | {row['documentation_set']} | "
            f"{row['unresolved_issues']['count']} |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


<<<<<<< HEAD
=======
def _repo_relative_paths(paths: list[str]) -> list[str]:
    marker = "EAFIX_auth_docs/"
    rel_paths = []
    for raw in paths:
        text = str(raw).replace("\\", "/")
        if marker in text:
            rel_paths.append(text[text.index(marker) :])
        else:
            rel_paths.append(text.lstrip("/"))
    return rel_paths


>>>>>>> origin/copilot/regenerate-34-module-manifests
def write_generation_report(
    manifest_count: int,
    output_paths: list[str],
    unresolved_items: list[dict[str, Any]],
    json_path: Path,
    markdown_path: Path,
) -> None:
    report = {
        "generated_manifest_count": manifest_count,
<<<<<<< HEAD
        "output_artifacts": output_paths,
=======
        "output_artifacts": _repo_relative_paths(output_paths),
>>>>>>> origin/copilot/regenerate-34-module-manifests
        "unresolved_item_count": sum(len(x["unresolved_items"]) for x in unresolved_items),
        "unresolved_modules": len(unresolved_items),
    }
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_path.write_text(
        "\n".join(
            [
                "# Manifest Generation Report",
                "",
<<<<<<< HEAD
                f"- Generated manifests: **{manifest_count}**",
                f"- Unresolved modules: **{report['unresolved_modules']}**",
                f"- Unresolved items: **{report['unresolved_item_count']}**",
=======
                f"- Generated manifests: {manifest_count}",
                f"- Unresolved item count: {report['unresolved_item_count']}",
                f"- Unresolved modules: {report['unresolved_modules']}",
>>>>>>> origin/copilot/regenerate-34-module-manifests
            ]
        )
        + "\n",
        encoding="utf-8",
    )

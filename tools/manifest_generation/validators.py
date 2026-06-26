#!/usr/bin/env python3
"""Validation suite for regenerated manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


EXPECTED_PORTS = {
    "D2_CALENDAR_SOURCE_ADAPTER": 8084,
    "D3_CALENDAR_NORMALIZER": 8084,
    "F2_EVENT_LOG": 8084,
    "D4_CALENDAR_TRIGGER_BUILDER": 8084,
    "D1_MARKET_FEED_ADAPTER": 8081,
    "C2_INDICATOR_ENGINE": 8082,
    "S1_SIGNAL_ENGINE": 8083,
    "E1_OUTCOME_BUCKETIZER": 8085,
    "E2_PROXIMITY_EVALUATOR": 8085,
    "E3_MATRIX_LOOKUP": 8085,
    "E4_REENTRY_INTENT_BUILDER": 8085,
    "R1_RISK_EVALUATOR": 8087,
    "R2_ORDER_INTENT_COMPILER": 8087,
    "F4_FLOW_ORCHESTRATOR": 8088,
    "U1_DASHBOARD_BACKEND": 8092,
    "U2_GUI_GATEWAY": 8091,
    "B2_MT4_EA_EXECUTOR": 5001,
}


def _schema_validate_manifests(manifests: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Any]:
    validator = Draft202012Validator(schema)
    errors = []
    for manifest in manifests:
        for err in validator.iter_errors(manifest):
            errors.append(
                {
                    "module_id": manifest["module_identity"]["module_id"],
                    "canonical_symbol": manifest["module_identity"]["canonical_symbol"],
                    "path": list(err.path),
                    "message": err.message,
                }
            )
    invalid_module_ids = {e["module_id"] for e in errors}
    return {
        "valid_count": len(manifests) - len(invalid_module_ids),
        "total_count": len(manifests),
        "errors": errors,
    }


def _identity_validation(manifests: list[dict[str, Any]], expected_symbols: set[str]) -> dict[str, Any]:
    ids = [m["module_identity"]["module_id"] for m in manifests]
    symbols = [m["module_identity"]["canonical_symbol"] for m in manifests]
    stale_primary = [s for s in symbols if s in {"O2_OMS", "O3_PNL_CLASSIFIER", "F1_FLOW_ORCHESTRATOR", "SHARED_LIBS"}]
    return {
        "unique_module_ids": len(set(ids)),
        "unique_symbols": len(set(symbols)),
        "duplicate_module_ids": sorted({x for x in ids if ids.count(x) > 1}),
        "duplicate_symbols": sorted({x for x in symbols if symbols.count(x) > 1}),
        "missing_symbols": sorted(expected_symbols - set(symbols)),
        "unexpected_symbols": sorted(set(symbols) - expected_symbols),
        "stale_primary_symbols": stale_primary,
        "f4_is_canonical": "F4_FLOW_ORCHESTRATOR" in symbols,
        "shared_libs_not_emitted": "SHARED_LIBS" not in symbols,
    }


def _dependency_validation(manifests: list[dict[str, Any]], id_set: set[str]) -> dict[str, Any]:
    issues = []
    for manifest in manifests:
        symbol = manifest["module_identity"]["canonical_symbol"]
        for dep in manifest.get("dependencies", []):
            target_id = str(dep.get("target_id", ""))
            if "{" in target_id or "}" in target_id:
                issues.append({"symbol": symbol, "issue": "serialized_dependency_target", "target_id": target_id})
            if target_id and target_id not in id_set:
                issues.append({"symbol": symbol, "issue": "unknown_target_id", "target_id": target_id})
            if isinstance(dep.get("target_id"), dict):
                issues.append({"symbol": symbol, "issue": "stringified_object_target_id", "target_id": str(dep.get("target_id"))})
    return {"issues": issues}


def _contract_validation(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for manifest in manifests:
        symbol = manifest["module_identity"]["canonical_symbol"]
        for field in ["input_contracts", "output_contracts"]:
            for ref in manifest["contracts"].get(field, []):
                if not isinstance(ref, dict):
                    issues.append({"symbol": symbol, "issue": f"{field}_non_object"})
        if symbol == "R3_CORRELATION_GUARD":
            names = [x["name"] for x in manifest["contracts"]["output_contracts"] if isinstance(x, dict)]
            if "RiskGuardResult" not in names:
                issues.append({"symbol": symbol, "issue": "missing_RiskGuardResult_output"})
        if symbol == "R1_RISK_EVALUATOR":
            names = [x["name"] for x in manifest["contracts"]["input_contracts"] if isinstance(x, dict)]
            if "RiskGuardResult" not in names:
                issues.append({"symbol": symbol, "issue": "missing_RiskGuardResult_input"})
    return {"issues": issues}


def _runtime_validation(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for manifest in manifests:
        symbol = manifest["module_identity"]["canonical_symbol"]
        expected = EXPECTED_PORTS.get(symbol)
        if expected is None:
            continue
        got = manifest.get("service_runtime", {}).get("microservice_port")
        if got != expected:
            issues.append({"symbol": symbol, "expected_port": expected, "actual_port": got})
    return {"issues": issues}


def _file_ownership_validation(manifests: list[dict[str, Any]], mapping_rows_total: int) -> dict[str, Any]:
    issues = []
    all_role_rows = 0
    for manifest in manifests:
        role_index = manifest.get("file_ownership", {}).get("file_role_index", [])
        all_role_rows += len(role_index)
        for row in role_index:
            if "is_test" not in row:
                issues.append({"symbol": manifest["module_identity"]["canonical_symbol"], "issue": "missing_is_test"})
    return {
        "issues": issues,
        "mapped_row_count_in_manifests": all_role_rows,
        "mapping_rows_total": mapping_rows_total,
    }


def _ui_validation(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for symbol in ["U1_DASHBOARD_BACKEND", "U2_GUI_GATEWAY", "U3_MT4_EXPIRY_OVERLAY", "U4_DESKTOP_OPERATOR"]:
        match = next((m for m in manifests if m["module_identity"]["canonical_symbol"] == symbol), None)
        if not match:
            issues.append({"symbol": symbol, "issue": "missing_ui_manifest"})
            continue
        if symbol in {"U1_DASHBOARD_BACKEND", "U2_GUI_GATEWAY"} and match.get("service_runtime", {}).get("microservice_port") is None:
            issues.append({"symbol": symbol, "issue": "missing_ui_port"})
    return {"issues": issues}


def _mt4_validation(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for symbol in ["B2_MT4_EA_EXECUTOR", "U4_DESKTOP_OPERATOR"]:
        m = next((x for x in manifests if x["module_identity"]["canonical_symbol"] == symbol), None)
        if not m:
            issues.append({"symbol": symbol, "issue": "missing_manifest"})
            continue
        if "platform_constraints" not in m:
            issues.append({"symbol": symbol, "issue": "missing_platform_constraints"})
    return {"issues": issues}


def _thin_module_validation(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    required = {
        "R3_CORRELATION_GUARD",
        "F4_FLOW_ORCHESTRATOR",
        "U1_DASHBOARD_BACKEND",
        "U2_GUI_GATEWAY",
        "U3_MT4_EXPIRY_OVERLAY",
        "U4_DESKTOP_OPERATOR",
        "P2_REPORTER",
        "SK1_PLUGIN_INTERFACE",
        "SK2_IDEMPOTENCY",
    }
    issues = []
    for symbol in required:
        m = next((x for x in manifests if x["module_identity"]["canonical_symbol"] == symbol), None)
        if not m:
            issues.append({"symbol": symbol, "issue": "missing_thin_module"})
            continue
        notes = m.get("reconciliation_status", {}).get("reconciliation_notes", [])
        if not any(str(n).startswith("thin_module:") for n in notes):
            issues.append({"symbol": symbol, "issue": "thin_module_reason_missing"})
    return {"issues": issues, "thin_module_count": len(required)}


def run_validation_suite(
    manifests: list[dict[str, Any]],
    schema: dict[str, Any],
    expected_symbols: set[str],
    mapping_rows_total: int,
) -> dict[str, Any]:
    id_set = {m["module_identity"]["module_id"] for m in manifests}
    symbol_set = {m["module_identity"]["canonical_symbol"] for m in manifests}
    schema_result = _schema_validate_manifests(manifests, schema)
    report = {
        "schema_validation": schema_result,
        "bundle_validation": {
            "module_count": len(manifests),
            "module_count_expected": 34,
            "unique_numeric_module_ids": len(id_set),
            "unique_canonical_symbols": len(symbol_set),
        },
        "identity_validation": _identity_validation(manifests, expected_symbols),
        "dependency_validation": _dependency_validation(manifests, id_set),
        "contract_validation": _contract_validation(manifests),
        "runtime_validation": _runtime_validation(manifests),
        "file_ownership_validation": _file_ownership_validation(manifests, mapping_rows_total),
        "ui_validation": _ui_validation(manifests),
        "mt4_validation": _mt4_validation(manifests),
        "thin_module_validation": _thin_module_validation(manifests),
    }
    report["acceptance"] = {
        "schema_valid_34_of_34": schema_result["valid_count"] == 34 and schema_result["total_count"] == 34,
        "bundle_count_valid": len(manifests) == 34 and len(id_set) == 34 and len(symbol_set) == 34,
        "has_no_validation_issues": all(
            len(section.get("issues", [])) == 0
            for key, section in report.items()
            if key.endswith("_validation") and key not in {"schema_validation", "bundle_validation", "identity_validation"}
        ),
    }
    return report


def write_validation_outputs(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Manifest Validation Report", ""]
    lines.append("## Acceptance")
    for key, value in report["acceptance"].items():
        lines.append(f"- **{key}**: {'PASS' if value else 'FAIL'}")
    lines.append("")
    lines.append("## Section Results")
    for key, section in report.items():
        if key == "acceptance":
            continue
        if isinstance(section, dict):
            issue_count = len(section.get("issues", []))
            lines.append(f"- **{key}**: issues={issue_count}" if "issues" in section else f"- **{key}**")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

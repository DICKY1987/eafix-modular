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
}


def _safe_identity(manifest: dict[str, Any]) -> tuple[str, str]:
    """Return (module_id, canonical_symbol) safely, falling back to 'unknown'."""
    identity = manifest.get("module_identity") if isinstance(manifest, dict) else {}
    if not isinstance(identity, dict):
        identity = {}
    return str(identity.get("module_id", "unknown")), str(identity.get("canonical_symbol", "unknown"))


def _schema_validate_manifests(manifests: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Any]:
    validator = Draft202012Validator(schema)
    errors = []
    for manifest in manifests:
        mid, sym = _safe_identity(manifest)
        for err in validator.iter_errors(manifest):
            errors.append(
                {
                    "module_id": mid,
                    "canonical_symbol": sym,
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
    ids = [_safe_identity(m)[0] for m in manifests]
    symbols = [_safe_identity(m)[1] for m in manifests]
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
        _, symbol = _safe_identity(manifest)
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
        _, symbol = _safe_identity(manifest)
        contracts = manifest.get("contracts") if isinstance(manifest.get("contracts"), dict) else {}
        for field in ["input_contracts", "output_contracts"]:
            for ref in contracts.get(field, []):
                if not isinstance(ref, dict):
                    issues.append({"symbol": symbol, "issue": f"{field}_non_object"})
        if symbol == "R3_CORRELATION_GUARD":
            names = [x.get("name") for x in contracts.get("output_contracts", []) if isinstance(x, dict)]
            if "RiskGuardResult" not in names:
                issues.append({"symbol": symbol, "issue": "missing_RiskGuardResult_output"})
        if symbol == "R1_RISK_EVALUATOR":
            names = [x.get("name") for x in contracts.get("input_contracts", []) if isinstance(x, dict)]
            if "RiskGuardResult" not in names:
                issues.append({"symbol": symbol, "issue": "missing_RiskGuardResult_input"})
    return {"issues": issues}


def _runtime_validation(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for manifest in manifests:
        _, symbol = _safe_identity(manifest)
        expected = EXPECTED_PORTS.get(symbol)
        if expected is None:
            continue
        got = manifest.get("service_runtime", {}).get("microservice_port")
        if got != expected:
            issues.append({"symbol": symbol, "expected_port": expected, "actual_port": got})
        runtime_kind = manifest.get("service_runtime", {}).get("runtime_kind")
        if runtime_kind == "mql4_ea" and got == 5001:
            issues.append({"symbol": symbol, "issue": "mql4_ea_runtime_port_semantics_invalid", "actual_port": got})
    return {"issues": issues}


def _file_ownership_validation(manifests: list[dict[str, Any]], mapping_rows_total: int) -> dict[str, Any]:
    issues = []
    all_role_rows = 0
    for manifest in manifests:
        _, symbol = _safe_identity(manifest)
        role_index = manifest.get("file_ownership", {}).get("file_role_index", [])
        all_role_rows += len(role_index)
        for row in role_index:
            if "is_test" not in row:
                issues.append({"symbol": symbol, "issue": "missing_is_test"})
    return {
        "issues": issues,
        "mapped_row_count_in_manifests": all_role_rows,
        "mapping_rows_total": mapping_rows_total,
    }


def _ui_validation(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for symbol in ["U1_DASHBOARD_BACKEND", "U2_GUI_GATEWAY", "U3_MT4_EXPIRY_OVERLAY", "U4_DESKTOP_OPERATOR"]:
        match = next((m for m in manifests if _safe_identity(m)[1] == symbol), None)
        if not match:
            issues.append({"symbol": symbol, "issue": "missing_ui_manifest"})
            continue
        if symbol in {"U1_DASHBOARD_BACKEND", "U2_GUI_GATEWAY"} and match.get("service_runtime", {}).get("microservice_port") is None:
            issues.append({"symbol": symbol, "issue": "missing_ui_port"})
    return {"issues": issues}


def _ui_catalog_product_map(ui_catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    product_map: dict[str, dict[str, Any]] = {}
    for product in ui_catalog.get("ui_products", []):
        if not isinstance(product, dict):
            continue
        name = str(product.get("name", "")).lower()
        service = str(product.get("service_name", "")).lower()
        if "dashboard backend" in name or service == "dashboard-backend":
            product_map["U1_DASHBOARD_BACKEND"] = product
        elif "gui gateway" in name or service == "gui-gateway":
            product_map["U2_GUI_GATEWAY"] = product
        elif "overlay" in name:
            product_map["U3_MT4_EXPIRY_OVERLAY"] = product
        elif "desktop operator" in name:
            product_map["U4_DESKTOP_OPERATOR"] = product
    return product_map


def _governance_validation(
    manifests: list[dict[str, Any]],
    ui_catalog: dict[str, Any],
    dependency_layers_parsed: bool,
    dependency_issue_count: int,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    layer_suffix_matches = 0
    for manifest in manifests:
        module_id, symbol = _safe_identity(manifest)
        layer = manifest.get("module_classification", {}).get("layer")
        process_binding = manifest.get("process_binding", {})

        if process_binding.get("step_number", 0) > 0 and process_binding.get("phase_id") == "PHASE_UNKNOWN":
            issues.append({"symbol": symbol, "issue": "process_bound_phase_unknown"})

        if module_id[-2:].isdigit() and isinstance(layer, int) and layer == int(module_id[-2:]):
            layer_suffix_matches += 1

        for shared in manifest.get("file_ownership", {}).get("shared_files", []):
            if (
                isinstance(shared, dict)
                and str(shared.get("path", "")).startswith("services/")
                and shared.get("sharing_policy") == "shared_kernel"
            ):
                issues.append({"symbol": symbol, "issue": "shared_service_file_labeled_shared_kernel", "path": shared.get("path")})

    if layer_suffix_matches == len(manifests):
        issues.append({"issue": "layer_derived_from_numeric_id_suffix"})

    ui_products = _ui_catalog_product_map(ui_catalog)
    for symbol, product in ui_products.items():
        manifest = next((m for m in manifests if _safe_identity(m)[1] == symbol), None)
        if not manifest:
            continue
        if product.get("purpose") and "needs_review" in str(manifest.get("purpose", "")):
            issues.append({"symbol": symbol, "issue": "ui_purpose_left_needs_review"})

        if product.get("observed_implementation_paths"):
            runtime_home = manifest.get("service_runtime", {}).get("service_home")
            if not runtime_home:
                issues.append({"symbol": symbol, "issue": "ui_service_home_missing"})

        scope = manifest.get("module_scope", {})
        if any("needs_review" in str(v) for v in scope.get("scope_in", []) + scope.get("scope_out", []) + scope.get("responsibilities", [])):
            issues.append({"symbol": symbol, "issue": "ui_scope_or_responsibility_needs_review"})

        contracts = manifest.get("contracts") if isinstance(manifest.get("contracts"), dict) else {}
        if symbol in {"U1_DASHBOARD_BACKEND", "U2_GUI_GATEWAY"}:
            inputs = [str(c.get("name")) for c in contracts.get("input_contracts", []) if isinstance(c, dict)]
            outputs = [str(c.get("name")) for c in contracts.get("output_contracts", []) if isinstance(c, dict)]
            if any(name == "needs_review" for name in inputs + outputs):
                issues.append({"symbol": symbol, "issue": "ui_contracts_needs_review"})

    b2 = next((m for m in manifests if _safe_identity(m)[1] == "B2_MT4_EA_EXECUTOR"), None)
    if b2:
        runtime = b2.get("service_runtime", {})
        if runtime.get("runtime_kind") == "mql4_ea" and runtime.get("microservice_port") == 5001:
            issues.append({"symbol": "B2_MT4_EA_EXECUTOR", "issue": "mql4_ea_uses_channel_port_as_runtime_port"})

    if not dependency_layers_parsed and dependency_issue_count == 0:
        issues.append({"issue": "dependency_layers_pdf_not_parsed"})

    return {"issues": issues}


def _mt4_validation(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for symbol in ["B2_MT4_EA_EXECUTOR", "U4_DESKTOP_OPERATOR"]:
        m = next((x for x in manifests if _safe_identity(x)[1] == symbol), None)
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
        m = next((x for x in manifests if _safe_identity(x)[1] == symbol), None)
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
    ui_catalog: dict[str, Any],
    dependency_layers_parsed: bool,
) -> dict[str, Any]:
    id_set = {_safe_identity(m)[0] for m in manifests}
    symbol_set = {_safe_identity(m)[1] for m in manifests}
    schema_result = _schema_validate_manifests(manifests, schema)
    dependency_result = _dependency_validation(manifests, id_set)
    report = {
        "schema_validation": schema_result,
        "bundle_validation": {
            "module_count": len(manifests),
            "module_count_expected": 34,
            "unique_numeric_module_ids": len(id_set),
            "unique_canonical_symbols": len(symbol_set),
        },
        "identity_validation": _identity_validation(manifests, expected_symbols),
        "dependency_validation": dependency_result,
        "contract_validation": _contract_validation(manifests),
        "runtime_validation": _runtime_validation(manifests),
        "file_ownership_validation": _file_ownership_validation(manifests, mapping_rows_total),
        "ui_validation": _ui_validation(manifests),
        "mt4_validation": _mt4_validation(manifests),
        "thin_module_validation": _thin_module_validation(manifests),
        "governance_validation": _governance_validation(
            manifests,
            ui_catalog,
            dependency_layers_parsed,
            len(dependency_result["issues"]),
        ),
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

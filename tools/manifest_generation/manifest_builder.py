#!/usr/bin/env python3
"""Build schema-valid manifest objects from reconciled normalized data."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from .normalizers import THIN_MODULES


RUNTIME_KIND_BY_PREFIX = {
    "U1": ("dashboard_backend", "python"),
    "U2": ("gui_gateway", "python"),
    "U3": ("desktop_ui", "mql4"),
    "U4": ("desktop_ui", "mixed"),
    "SK1": ("shared_kernel", "python"),
    "SK2": ("shared_kernel", "python"),
    "B2": ("mql4_ea", "mql4"),
}

MODULE_KIND_BY_PREFIX = {
    "F": "INFRA_PLATFORM_MODULE",
    "D": "INTEGRATION_BRIDGE_MODULE",
    "C": "COMPUTE_MODULE",
    "S": "SIGNAL_MODULE",
    "R": "RISK_MODULE",
    "O": "OMS_MODULE",
    "B": "INTEGRATION_BRIDGE_MODULE",
    "E": "REENTRY_MODULE",
    "U": "UI_MODULE",
    "P": "OBSERVABILITY_REPORTING_MODULE",
    "SK": "SHARED_KERNEL_MODULE",
}

DEPLOYABLE_BY_PREFIX = {
    "U1": "dashboard_backend",
    "U2": "gui_gateway",
    "U3": "desktop_ui",
    "U4": "desktop_ui",
    "SK1": "shared_kernel",
    "SK2": "shared_kernel",
    "B2": "mql4_ea",
}


def _prefix(symbol: str) -> str:
    if symbol.startswith("SK"):
        return "SK"
    match = re.match(r"^[A-Z]+", symbol)
    if match:
        return match.group(0)
    return symbol[:1]


def _module_kind(symbol: str) -> str:
    pre = _prefix(symbol)
    return MODULE_KIND_BY_PREFIX.get(pre, "PIPELINE_STAGE_MODULE")


def _deployable_scope(symbol: str) -> str:
    for pre, scope in DEPLOYABLE_BY_PREFIX.items():
        if symbol.startswith(pre):
            return scope
    if symbol.startswith("SK"):
        return "shared_kernel"
    return "python_service"


def _domain_group(symbol: str) -> tuple[str, str]:
    pre = _prefix(symbol)
    mapping = {
        "F": ("G0", "Infrastructure Platform"),
        "D": ("G1", "Data Ingest"),
        "C": ("G2", "Compute Feature"),
        "S": ("G3", "Signal"),
        "R": ("G4", "Risk"),
        "O": ("G5", "Order Management"),
        "B": ("G6", "MT4 Bridge"),
        "E": ("G7", "Reentry"),
        "U": ("G8", "UI Gateway"),
        "P": ("G9", "Observability"),
        "SK": ("G10", "Shared Kernel"),
    }
    return mapping.get(pre, ("GX", "Unknown"))


def _scope_arrays(enriched: dict[str, Any] | None) -> tuple[list[str], list[str], list[str]]:
    if enriched:
        scope_in = [str(v) for v in enriched.get("scope_in", [])] or ["needs_review"]
        scope_out = [str(v) for v in enriched.get("scope_out", [])] or ["needs_review"]
        responsibilities = [str(v) for v in enriched.get("responsibilities", [])] or ["needs_review"]
        return scope_in, scope_out, responsibilities
    return ["needs_review"], ["needs_review"], ["needs_review"]


def _contract_refs(names: list[str], direction: str) -> list[dict[str, Any]]:
    refs = []
    for name in names or ["needs_review"]:
        refs.append(
            {
                "name": name,
                "direction": direction,
                "description": "",
                "required": True,
                "schema_ref": None,
                "version": None,
                "produced_by_module": None,
                "consumed_by_modules": [],
            }
        )
    return refs


def _build_process_binding(module: dict[str, Any], process_idx: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    symbol = module["canonical_symbol"]
    step = process_idx["by_symbol"].get(symbol)
    if step:
        aligned_phase = process_idx.get("phase_binding_by_symbol", {}).get(symbol, {})
        phase_id = (
            str(aligned_phase.get("phase_id", "")).strip()
            or str(step.get("phase_id", "")).strip()
            or "PHASE_UNKNOWN"
        )
        phase_name = (
            str(aligned_phase.get("phase_name", "")).strip()
            or process_idx.get("phase_name_by_id", {}).get(phase_id, "")
            or "needs_review"
        )
        return (
            {
                "process_id": "HUEY_P_EAFIX_END_TO_END",
                "process_version": "2.0.0",
                "phase_id": phase_id,
                "phase_name": phase_name,
                "step_id": step.get("process_step_id"),
                "step_number": int(step.get("step_number", 0)),
                "step_code": step.get("step_code"),
                "step_name": step.get("step_name"),
                "process_order": int(step.get("step_number", 0)),
                "dependency_step_ids": [str(v) for v in step.get("dependency_step_ids", [])],
                "upstream_modules": [],
                "downstream_modules": [],
                "responsible": str(step.get("responsible", "needs_review")),
                "entrypoint_files": [str(v).replace("\\", "/") for v in step.get("entrypoint_files", [])],
                "output_description": str(step.get("output_contract", "")),
                "loop_behavior": None,
                "process_binding_source": "process_step_catalog",
            },
            False,
        )

    return (
        {
            "process_id": "HUEY_P_EAFIX_END_TO_END",
            "process_version": "2.0.0",
            "phase_id": "PHASE_NOT_APPLICABLE",
            "phase_name": "not_applicable",
            "step_id": "N/A",
            "step_number": 0,
            "step_code": "NA",
            "step_name": "not_applicable",
            "process_order": 0,
            "dependency_step_ids": [],
            "upstream_modules": [],
            "downstream_modules": [],
            "responsible": "needs_review",
            "entrypoint_files": [],
            "output_description": "",
            "loop_behavior": None,
            "process_binding_source": "manual_atomic_split",
        },
        True,
    )


def _service_runtime(symbol: str, ports_by_symbol: dict[str, int], file_map_for_symbol: dict[str, Any]) -> dict[str, Any]:
    runtime_kind, language = RUNTIME_KIND_BY_PREFIX.get(_prefix(symbol), ("python_service", "python"))
    scope = _deployable_scope(symbol)
    if scope in {"dashboard_backend", "gui_gateway"}:
        runtime_kind = scope
        language = "python"
    if scope == "mql4_ea":
        runtime_kind = "mql4_ea"
        language = "mql4"
    if scope == "shared_kernel":
        runtime_kind = "shared_kernel"
        language = "python"

    owned = file_map_for_symbol.get("owned_files", [])
    home = None
    if owned:
        top = owned[0].split("/", 2)
        if len(top) >= 2:
            home = "/".join(top[:2])
    port = ports_by_symbol.get(symbol)
    if runtime_kind == "mql4_ea":
        port = None

    return {
        "service_home": home,
        "candidate_service_home": None,
        "runtime_kind": runtime_kind,
        "language": language,
        "microservice_port": port,
        "host": "localhost" if port else None,
        "deployment_unit": scope,
        "runtime_status": "active" if port else ("active" if runtime_kind == "mql4_ea" else "unknown"),
        "startup_entrypoints": [],
        "health_endpoint": f"http://localhost:{port}/healthz" if port else None,
        "metrics_endpoint": f"http://localhost:{port}/metrics" if port else None,
        "external_systems": [],
        "operator_settings_required": [],
    }


def _build_communication_channels(symbol: str, comm_index: dict[str, Any]) -> dict[str, Any] | None:
    channels = comm_index["by_owner_symbol"].get(symbol, [])
    if not channels:
        return None
    owned = []
    for c in channels:
        owned.append(
            {
                "channel_id": c.get("channel_id"),
                "channel_name": c.get("channel_name"),
                "channel_number": c.get("channel_number"),
                "status": c.get("status", "unknown"),
                "enabled_by_default": c.get("enabled_by_default", True),
                "direction": c.get("direction", "unknown"),
                "protocol": c.get("protocol", "unknown"),
                "host": c.get("host"),
                "port": c.get("port"),
                "routes": c.get("routes", []),
                "dde_topic": c.get("dde_topic"),
                "poll_interval_ms": c.get("poll_interval_ms"),
                "outbox_pattern": c.get("outbox_pattern"),
                "redis_topics": [
                    {
                        "topic": t.get("topic"),
                        "purpose": t.get("purpose", "needs_review"),
                        "producer_module_id": t.get("producer_module_id"),
                        "consumer_module_id": t.get("consumer_module_id"),
                        "data_contracts": [],
                    }
                    for t in c.get("redis_topics", [])
                    if isinstance(t, dict)
                ],
                "data_contracts": [str(v) for v in c.get("data_contracts", [])],
                "python_files": [str(v) for v in c.get("python_files", [])],
                "mt4_files": [str(v) for v in c.get("mt4_files", [])],
                "owning_module_id": c.get("owning_module_id"),
                "owning_module_symbol": c.get("owning_module_symbol"),
                "fallback_rank": None,
                "fallback_to_channel_id": None,
                "notes": c.get("notes", ""),
            }
        )
    return {
        "owned_channels": owned,
        "consumed_channels": [],
        "published_topics": [],
        "subscribed_topics": [],
        "fallback_hierarchy": [],
        "channel_notes": [],
    }


def _platform_constraints(symbol: str) -> dict[str, Any] | None:
    if symbol not in {"B1_MT4_ADAPTER_TRANSPORT", "B2_MT4_EA_EXECUTOR", "U4_DESKTOP_OPERATOR", "U3_MT4_EXPIRY_OVERLAY"}:
        return None
    return {
        "platform": "MT4",
        "native_capability_refs": ["MT4-AI-RULE-004", "MT4-AI-RULE-006"],
        "known_limitation_refs": ["no_public_retail_mt4_rest_api"],
        "required_operator_settings": ["desktop_terminal_connected"],
        "broker_variability": True,
        "custom_vs_native_policy": "reuse_native_or_export_native_data",
        "mt4_terminal_must_be_open": True,
        "web_terminal_supported": False,
        "dll_imports_required": symbol in {"B2_MT4_EA_EXECUTOR"},
        "webrequest_required": symbol in {"B2_MT4_EA_EXECUTOR", "U4_DESKTOP_OPERATOR"},
    }


def _normalized_path(path: str) -> str:
    return str(path).replace("\\", "/")


def _to_contract_identifier(raw: str, default: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_]", "_", str(raw or "").strip())
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        text = default
    if not re.match(r"^[A-Za-z]", text):
        text = f"C_{text}"
    return text


def _layer_from_authority(symbol: str, enriched: dict[str, Any] | None) -> tuple[int, bool]:
    if enriched:
        raw_layer = enriched.get("layer")
        if isinstance(raw_layer, int):
            return raw_layer, False
        if isinstance(raw_layer, str) and raw_layer.strip().isdigit():
            return int(raw_layer.strip()), False

    pre = _prefix(symbol)
    fallback = {
        "F": 1,
        "P": 1,
        "D": 2,
        "C": 3,
        "S": 3,
        "R": 4,
        "O": 4,
        "B": 4,
        "E": 4,
        "U": 5,
        "SK": 6,
    }
    return fallback.get(pre, 1), True


def _ui_enrichment(symbol: str, ui_index: dict[str, Any]) -> dict[str, Any] | None:
    if symbol not in ui_index:
        return None
    bundle = ui_index[symbol]
    product = bundle.get("product", {})
    if not isinstance(product, dict):
        return None

    rest_apis = bundle.get("rest_apis", [])
    ws_contracts = bundle.get("websocket_contracts", [])
    observed_paths = [_normalized_path(p) for p in product.get("observed_implementation_paths", [])]
    binding_paths = [
        _normalized_path(b.get("path"))
        for b in bundle.get("implementation_bindings", [])
        if isinstance(b, dict) and b.get("path")
    ]
    implementation_paths = sorted(set(observed_paths + binding_paths))

    service_name = str(bundle.get("service_name") or "")
    purpose = str(product.get("purpose", "")).strip()
    product_id = str(product.get("product_id", "")).strip() or None
    product_name = str(product.get("name", "")).strip() or symbol
    port = product.get("declared_port") if isinstance(product.get("declared_port"), int) else None

    module_root = None
    candidate_root = None
    if implementation_paths:
        # For desktop applications, prefer desktop-ui paths over backend service paths
        desktop_paths = [p for p in implementation_paths if "/desktop-ui/" in p or p.startswith("services/desktop-ui")]
        backend_paths = [p for p in implementation_paths if "/dashboard-backend/" in p or p.startswith("services/dashboard-backend")]
        primary_paths = desktop_paths or implementation_paths
        split = primary_paths[0].split("/", 3)
        if len(split) >= 2:
            module_root = "/".join(split[:2])
        if desktop_paths and backend_paths:
            bsplit = backend_paths[0].split("/", 3)
            if len(bsplit) >= 2:
                candidate_root = "/".join(bsplit[:2])

    rest_inputs = sorted(
        {
            _to_contract_identifier(f"{api.get('api_id', 'REST')}_Request", "REST_Request")
            for api in rest_apis
            if api.get("path")
        }
    )
    rest_outputs = sorted(
        {
            _to_contract_identifier(f"{api.get('api_id', 'REST')}_Response", "REST_Response")
            for api in rest_apis
            if api.get("path")
        }
    )
    ws_outputs = sorted(
        {
            _to_contract_identifier(f"{ws.get('websocket_id', 'WebSocket')}_Event", "WebSocket_Event")
            for ws in ws_contracts
        }
    )
    ws_inputs = sorted(
        {
            _to_contract_identifier(f"{ws.get('websocket_id', 'WebSocket')}_Subscribe", "WebSocket_Subscribe")
            for ws in ws_contracts
        }
    )

    scope_in = sorted(set(rest_inputs + ws_inputs)) or [_to_contract_identifier(f"{product_name}_ClientRequest", "UI_ClientRequest")]
    scope_out = sorted(set(rest_outputs + ws_outputs)) or [_to_contract_identifier(f"{product_name}_Response", "UI_Response")]
    responsibilities = [purpose] if purpose else [f"Deliver {product_name} UX contracts"]

    binding_refs = []
    for binding in bundle.get("implementation_bindings", []):
        if isinstance(binding, dict):
            binding_id = str(binding.get("binding_id", "")).strip()
            if binding_id:
                binding_refs.append(binding_id)

    return {
        "purpose": purpose,
        "plain_summary": purpose or f"{product_name} UI module.",
        "service_name": service_name or None,
        "product_id": product_id,
        "product_name": product_name,
        "declared_port": port,
        "module_root": module_root,
        "candidate_module_root": candidate_root,
        "implementation_paths": implementation_paths,
        "scope_in": scope_in,
        "scope_out": scope_out,
        "responsibilities": responsibilities,
        "input_contracts": scope_in,
        "output_contracts": scope_out,
        "rest_apis": rest_apis,
        "websocket_contracts": ws_contracts,
        "binding_refs": sorted(set(binding_refs)),
    }


def build_manifests(
    reconciled_modules: list[dict[str, Any]],
    sources: dict[str, Any],
    normalized: dict[str, Any],
    source_hashes: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    now = datetime.now(timezone.utc).isoformat()
    manifests: list[dict[str, Any]] = []
    unresolved_report: list[dict[str, Any]] = []

    for module in reconciled_modules:
        symbol = module["canonical_symbol"]
        enriched = normalized["module_catalog_enrichment"].get(symbol)
        process_binding, is_not_applicable_process = _build_process_binding(module, normalized["process_step_index"])
        process_step = normalized["process_step_index"]["by_symbol"].get(symbol, {})
        aligned_step = normalized["process_step_index"]["aligned_by_symbol"].get(symbol, {})
        file_map = normalized["file_mapping_index"]["by_module"].get(
            symbol,
            {"owned_files": [], "shared_service_files": [], "candidate_owned_files": [], "file_role_index": []},
        )
        deps = normalized["dependency_candidate_index"]["by_symbol"].get(symbol, [])
        runtime = _service_runtime(symbol, normalized["service_runtime_index"]["ports_by_symbol"], file_map)
        comm = _build_communication_channels(symbol, normalized["communication_channel_index"])
        scope_in, scope_out, responsibilities = _scope_arrays(enriched)
        ui = _ui_enrichment(symbol, normalized["ui_product_index"])
        layer, layer_fallback_used = _layer_from_authority(symbol, enriched)

        if ui:
            scope_in = ui["scope_in"]
            scope_out = ui["scope_out"]
            responsibilities = ui["responsibilities"]
            if not runtime.get("service_home"):
                runtime["service_home"] = ui["module_root"]
            elif symbol == "U4_DESKTOP_OPERATOR" and ui.get("module_root"):
                # U4 is a mixed desktop runtime: prefer desktop-ui as primary service_home
                runtime["candidate_service_home"] = runtime["service_home"]
                runtime["service_home"] = ui["module_root"]
            if ui.get("candidate_module_root") and not runtime.get("candidate_service_home"):
                runtime["candidate_service_home"] = ui["candidate_module_root"]
            if isinstance(ui.get("declared_port"), int):
                runtime["microservice_port"] = runtime["microservice_port"] or ui["declared_port"]
                if runtime["microservice_port"]:
                    runtime["host"] = "localhost"
                    runtime["health_endpoint"] = f"http://localhost:{runtime['microservice_port']}/healthz"
                    runtime["metrics_endpoint"] = f"http://localhost:{runtime['microservice_port']}/metrics"
                    runtime["runtime_status"] = "active"

        unresolved = list(module["reconciliation"].get("unresolved_items", []))
        if is_not_applicable_process:
            unresolved.append("process_binding:not_applicable")
        if not file_map["owned_files"] and not file_map["shared_service_files"]:
            unresolved.append("file_ownership:unassigned")

        thin_reason = THIN_MODULES.get(symbol)
        if thin_reason and f"thin_module:{thin_reason}" not in unresolved:
            unresolved.append(f"thin_module:{thin_reason}")

        input_contract_names = process_step.get("input_contracts") or []
        output_contract_names = process_step.get("output_contracts") or []
        if ui:
            input_contract_names = ui["input_contracts"]
            output_contract_names = ui["output_contracts"]
        if symbol == "R3_CORRELATION_GUARD" and "RiskGuardResult" not in output_contract_names:
            output_contract_names = [*output_contract_names, "RiskGuardResult"]
        if symbol == "R1_RISK_EVALUATOR" and "RiskGuardResult" not in input_contract_names:
            input_contract_names = [*input_contract_names, "RiskGuardResult"]

        validation_contract = aligned_step.get("validation_contract", {})
        failure_contract = aligned_step.get("failure_contract", {})
        if not validation_contract:
            validation_contract = {
                "validation_id": f"VAL-{symbol}-NEEDS_REVIEW",
                "rule": "needs_review",
                "evidence_required": True,
                "pass_fail_criteria": [],
            }
        if not failure_contract:
            failure_contract = {
                "failure_mode_id": f"FAIL-{symbol}-NEEDS_REVIEW",
                "rule": "needs_review",
                "default_behavior": "CONTINUE",
                "evidence_required": True,
                "operator_alert_required": False,
            }

        manifest = {
            "schema_version": "1.0.0",
            "document_type": "atomic_module_manifest_schema_instance",
            "packet_type": "atomic_module_manifest",
            "manifest_version": "1.0.0",
            "generated_at_utc": now,
            "last_updated_utc": now,
            "source_authority": {
                "authority_policy": "generated_from_canonical_sources",
                "required_reference_documents": [meta["relative_path"] for meta in sources.values()],
                "companion_documents": [
                    "EAFIX_auth_docs/eafix module manifests bundle.json",
                    "EAFIX_auth_docs/EAFIX module reconciliation worksheet.md",
                ],
                "conflict_resolution_order": [
                    "eafix_project_knowledge_reference_routing_instructions.json",
                    "EAFIX_auth_docs/Claude_gen_atomic_module_catalog_vNext.json",
                    "EAFIX_auth_docs/module_catalog.json",
                    "EAFIX_auth_docs/process_step_catalog.json",
                    "EAFIX_auth_docs/updated_trading_process_aligned.json",
                    "EAFIX_auth_docs/communication_channels.json",
                    "EAFIX_auth_docs/ui_catalog.json",
                    "EAFIX_auth_docs/mt4 authoritative reference for ai.json",
                    "EAFIX_auth_docs/file_module_mapping.csv",
                ],
                "generated_from_documents": [meta["relative_path"] for meta in sources.values()],
                "authority_notes": module["reconciliation"]["unresolved_items"],
            },
            "module_identity": {
                "module_id": module["module_id"],
                "numeric_module_id": module["module_id"],
                "canonical_symbol": symbol,
                "module_name": module["module_name"],
                "legacy_aliases": module.get("legacy_aliases_applied", []),
                "supersedes": [],
                "superseded_by": [],
                "identity_status": "canonical",
                "identity_model": "numeric_20_digit",
                "version": "1.0.0",
                "status": "canonical",
            },
            "module_classification": {
                "module_role": "ui_module" if symbol.startswith("U") else ("shared_kernel_module" if symbol.startswith("SK") else "atomic_canonical_module"),
                "module_kind": _module_kind(symbol),
                "domain_group_id": _domain_group(symbol)[0],
                "domain_group_name": _domain_group(symbol)[1],
                "phase_id": process_binding.get("phase_id"),
                "layer": layer,
                "deployable_scope": _deployable_scope(symbol),
                "tags": ["vNext"],
            },
            "purpose": str(
                (ui or {}).get("purpose")
                or (enriched or {}).get("purpose")
                or module.get("purpose")
                or f"{module['module_name']} responsibility needs_review"
            ),
            "plain_language_summary": str(
                (ui or {}).get("plain_summary")
                or (enriched or {}).get("purpose")
                or f"{module['module_name']} ({symbol}) in vNext atomic module set."
            ),
            "process_binding": process_binding,
            "contracts": {
                "input_contracts": _contract_refs(list(input_contract_names), "input"),
                "output_contracts": _contract_refs(list(output_contract_names), "output"),
                "contract_schema_refs": [],
                "contract_files": [],
                "output_description": str(process_step.get("output_contract", "")),
                "module_io_policy": {
                    "may_ingest_only_declared_outputs": True,
                    "private_cross_module_access_allowed": False,
                    "allowed_external_inputs": [],
                    "shared_kernel_access_policy": "stable_domain_neutral_primitives_only",
                    "forbidden_ingestion_sources": [],
                },
                "contract_version_policy": "versioned_contracts_required",
                "idempotency_key_policy": None,
                "hash_or_checksum_required": False,
                "hash_policy": None,
                "schema_validation_required": True,
            },
            "module_scope": {
                "scope_in": scope_in,
                "scope_out": scope_out,
                "responsibilities": responsibilities,
                "forbidden_responsibilities": ["cross_module_private_state_access"],
                "key_functions": [str(v) for v in (enriched or {}).get("key_functions", [])],
                "public_api_surface": [],
                "internal_only_objects": [],
                "shared_kernel_usage": [],
                "atomicity_statement": f"{symbol} is represented as a single atomic manifest record.",
            },
            "file_ownership": {
                "module_root": runtime.get("service_home"),
                "manifest_path": None,
                "owned_files": sorted(file_map["owned_files"]),
                "source_files": sorted([x["path"] for x in file_map["file_role_index"] if not x["is_test"]]),
                "test_files": sorted([x["path"] for x in file_map["file_role_index"] if x["is_test"]]),
                "contract_files": [],
                "documentation_files": [],
                "configuration_files": sorted([x["path"] for x in file_map["file_role_index"] if x["role"] == "config"]),
                "schema_files": [],
                "generated_files": [],
                "evidence_files": [],
                "allowed_files": sorted(file_map["shared_service_files"] + file_map["candidate_owned_files"]),
                "forbidden_files": [],
                "file_role_index": file_map["file_role_index"],
                "unassigned_candidate_files": [],
                "shared_files": [
                    {
                        "path": p,
                        "sharing_policy": "needs_refactor",
                        "allowed_modules": sorted(
                            {
                                m
                                for row in file_map["file_role_index"]
                                if row.get("path") == p
                                for m in row.get("canonical_modules", [])
                            }
                        ),
                        "reason": "Shared service file evidence from file_module_mapping.csv; not shared kernel.",
                    }
                    for p in sorted(file_map["shared_service_files"])
                ],
                "file_assignment_status": (
                    "complete"
                    if file_map["owned_files"] and not file_map["shared_service_files"]
                    else "partial"
                    if (file_map["owned_files"] or file_map["shared_service_files"])
                    else "unassigned"
                ),
                "file_assignment_policy_ref": "module_assignment_policy",
                "ownership_derivation": "file_module_mapping" if file_map["file_role_index"] else "unknown",
            },
            "service_runtime": runtime,
            "dependencies": [
                {
                    "target_type": dep["target_type"],
                    "target_id": dep["target_id"],
                    "target_symbol": dep["target_symbol"],
                    "relationship": dep["relationship"],
                    "consumes_output_contracts": [],
                    "version_constraint": None,
                    "optional": False,
                    "reason": dep["reason"],
                    "allowed_access_mode": "declared_output_contract_only",
                }
                for dep in deps
            ],
            "standards_and_gates": {
                "applicable_rule_ids": [
                    validation_contract.get("validation_id", f"VAL-{symbol}-NEEDS_REVIEW"),
                ],
                "applicable_gate_ids": [
                    f"GATE-{symbol}",
                ],
                "required_gate_commands": [],
                "required_validators": ["jsonschema"],
                "standards_domains": ["module_manifest"],
                "evidence_required": True,
                "evidence_paths": [],
                "blocking_gate_policy": "only_block_when_gate_has_pass_fail_and_evidence",
                "test_coverage_minimum": None,
                "invariants": [],
                "security_scan_required": True,
                "contract_validation_required": True,
                "source_traceability_required": True,
            },
            "state_and_failure_behavior": {
                "validation_contract": {
                    "validation_id": validation_contract["validation_id"],
                    "rule": validation_contract["rule"],
                    "evidence_required": bool(validation_contract.get("evidence_required", True)),
                    "pass_fail_criteria": validation_contract.get("pass_fail_criteria", []),
                },
                "failure_contract": {
                    "failure_mode_id": failure_contract["failure_mode_id"],
                    "rule": failure_contract["rule"],
                    "default_behavior": failure_contract["default_behavior"],
                    "evidence_required": bool(failure_contract.get("evidence_required", True)),
                    "operator_alert_required": bool(failure_contract.get("operator_alert_required", False)),
                },
                "state_machine_ref": None,
                "state_machine_states": [],
                "retry_policy": None,
                "fallback_policy": None,
                "quarantine_policy": None,
                "idempotency_policy": None,
                "timeout_policy": None,
                "time_standard_policy": None,
                "fail_closed_default": False,
                "risk_off_default": False,
            },
            "documentation_set": {
                "required_documents": [
                    {"document_name": "manifest.json", "path": None, "required": True, "status": "generated", "authority_level": None, "notes": ""},
                    {"document_name": "README.md", "path": None, "required": True, "status": "missing", "authority_level": None, "notes": ""},
                    {"document_name": "contracts.md", "path": None, "required": True, "status": "missing", "authority_level": None, "notes": ""},
                ],
                "documentation_completeness": "partial",
                "missing_documents": ["README.md", "contracts.md"],
                "deprecated_submodule_docs": [],
                "plain_language_summary_ref": None,
                "generated_readme_ref": None,
                "verification_matrix_ref": None,
                "implementation_map_ref": None,
                "api_interfaces_ref": None,
                "contracts_ref": None,
                "state_machine_ref": None,
            },
            "reconciliation_status": {
                "service_binding_status": "bound" if runtime.get("service_home") else "needs_review",
                "submodule_doc_status": "deprecated",
                "mapped_file_count": len(file_map["file_role_index"]),
                "owned_channel_ids": [c.get("channel_id") for c in (comm or {}).get("owned_channels", [])],
                "known_flags": sorted(set(["THIN_MODULE"] if thin_reason else []) | set([u.split(":", 1)[0].upper() for u in unresolved])),
                "stale_symbol_tokens": module.get("legacy_aliases_applied", []),
                "kind_mismatch": False,
                "layer_unassigned": layer_fallback_used,
                "prefix_collision": False,
                "reconciliation_notes": sorted(set(unresolved)),
                "last_reconciled_utc": now,
            },
            "staleness_policy": {
                "regenerate_if_changed": [
                    "EAFIX_auth_docs/Claude_gen_atomic_module_catalog_vNext.json",
                    "EAFIX_auth_docs/module_catalog.json",
                    "EAFIX_auth_docs/process_step_catalog.json",
                    "EAFIX_auth_docs/updated_trading_process_aligned.json",
                    "EAFIX_auth_docs/file_module_mapping.csv",
                ],
                "last_generated_from": [
                    "EAFIX_auth_docs/Claude_gen_atomic_module_catalog_vNext.json",
                    "EAFIX_auth_docs/module_catalog.json",
                    "EAFIX_auth_docs/process_step_catalog.json",
                    "EAFIX_auth_docs/updated_trading_process_aligned.json",
                    "EAFIX_auth_docs/file_module_mapping.csv",
                    "EAFIX_auth_docs/communication_channels.json",
                    "EAFIX_auth_docs/ui_catalog.json",
                ],
                "source_hashes": source_hashes,
                "staleness_check_command": "python -m tools.manifest_generation.generate_manifests --repo-root . --validate-only",
                "staleness_status": "fresh",
            },
            "notes": [
                "Schema-first regenerated manifest from normalized staging tables.",
            ],
        }

        if comm:
            manifest["communication_channels"] = comm
        platform = _platform_constraints(symbol)
        if platform:
            manifest["platform_constraints"] = platform
        if symbol in normalized["ui_product_index"]:
            product = normalized["ui_product_index"][symbol].get("product", {})
            manifest["ai_context"] = {
                "context_priority": "canonical",
                "plain_language_summary": f"UI catalog mapping for {product.get('product_id')}",
                "safe_edit_boundary": "ui_catalog_authority_only",
                "forbidden_assumptions": [],
                "common_failure_patterns": [],
                "ai_usage_guidance": {
                    "use_when": "updating UI module metadata",
                    "do_not_use_when": "non-UI module updates",
                    "must_remember": [f"UI product mapping: {product.get('product_id')}"],
                    "lookup_keys": [symbol, product.get("product_id", "")],
                },
            }
        if module.get("legacy_aliases_applied"):
            manifest["migration_traceability"] = {
                "migration_status": "renamed_from_legacy_alias",
                "source_parent_modules": [],
                "promoted_from_work_cells": [],
                "promoted_from_submodules": [],
                "source_atonic_steps": [],
                "source_canonical_steps": [],
                "deprecated_identifiers": module.get("legacy_aliases_applied"),
                "replacement_modules": [symbol],
                "crosswalk_refs": ["build/staging/alias_crosswalk.json"],
                "migration_notes": ["legacy aliases reconciled to canonical symbol"],
            }

        manifests.append(manifest)
        if unresolved:
            unresolved_report.append(
                {
                    "module_id": module["module_id"],
                    "canonical_symbol": symbol,
                    "unresolved_items": unresolved,
                    "thin_module_reason": thin_reason,
                }
            )

    return manifests, unresolved_report

#!/usr/bin/env python3
"""Normalize raw sources into staging datasets."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ALIAS_CROSSWALK = {
    "O2_OMS": "O2_OMS_STATE_MACHINE",
    "O3_PNL_CLASSIFIER": "O3_TRADE_CLOSE_CLASSIFIER",
    "F1_FLOW_ORCHESTRATOR": "F4_FLOW_ORCHESTRATOR",
    "SHARED_LIBS.plugin_interface": "SK1_PLUGIN_INTERFACE",
    "SHARED_LIBS.idempotency": "SK2_IDEMPOTENCY",
    "SHARED_LIBS": "legacy_aggregate_only",
}


KNOWN_PORTS = {
    "D1_MARKET_FEED_ADAPTER": 8081,
    "C2_INDICATOR_ENGINE": 8082,
    "S1_SIGNAL_ENGINE": 8083,
    "D2_CALENDAR_SOURCE_ADAPTER": 8084,
    "D3_CALENDAR_NORMALIZER": 8084,
    "F2_EVENT_LOG": 8084,
    "D4_CALENDAR_TRIGGER_BUILDER": 8084,
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


THIN_MODULES = {
    "R3_CORRELATION_GUARD": "manual_atomic_split",
    "F4_FLOW_ORCHESTRATOR": "manual_atomic_split",
    "U1_DASHBOARD_BACKEND": "ui_module",
    "U2_GUI_GATEWAY": "ui_module",
    "U3_MT4_EXPIRY_OVERLAY": "ui_module",
    "U4_DESKTOP_OPERATOR": "ui_module",
    "P2_REPORTER": "new_module",
    "SK1_PLUGIN_INTERFACE": "promoted_from_shared_libs",
    "SK2_IDEMPOTENCY": "promoted_from_shared_libs",
}


def normalize_symbol(symbol: str) -> str:
    return ALIAS_CROSSWALK.get(symbol, symbol)


def _symbol_from_module_ref(value: str) -> str:
    return normalize_symbol(value.strip())


def _to_relative_repo_path(raw: str) -> str:
    path = raw.replace("\\", "/")
    marker = "/eafix-modular/"
    idx = path.lower().find(marker)
    if idx >= 0:
        return path[idx + len(marker) :]
    return re.sub(r"^[A-Za-z]:/", "", path).lstrip("/")


def build_module_universe(vnext_catalog: dict[str, Any], draft_bundle: dict[str, Any]) -> dict[str, Any]:
    modules = vnext_catalog.get("modules", [])
    unresolved: list[str] = []
    fallback_used = False
    if not modules:
        fallback_used = True
        unresolved.append("vNext catalog has empty modules list; derived module universe from existing draft bundle identities")
        modules = [
            {
                "module_id": manifest["module_identity"].get("numeric_module_id")
                or manifest["module_identity"]["module_id"],
                "canonical_symbol": manifest["module_identity"]["canonical_symbol"],
                "module_name": manifest["module_identity"]["module_name"],
            }
            for manifest in draft_bundle.get("manifests", [])
        ]

    normalized_modules = []
    for item in modules:
        module_id = str(item.get("module_id") or item.get("numeric_module_id") or "")
        canonical_symbol = normalize_symbol(
            str(item.get("canonical_symbol") or item.get("module_symbol") or "")
        )
        if not module_id or not canonical_symbol:
            continue
        normalized_modules.append(
            {
                "module_id": module_id,
                "numeric_module_id": module_id,
                "canonical_symbol": canonical_symbol,
                "module_name": item.get("module_name", canonical_symbol.replace("_", " ").title()),
                "legacy_aliases": [symbol for symbol, target in ALIAS_CROSSWALK.items() if target == canonical_symbol],
            }
        )

    by_symbol = {m["canonical_symbol"]: m for m in normalized_modules}
    by_id = {m["module_id"]: m for m in normalized_modules}
    return {
        "module_count": len(normalized_modules),
        "modules": sorted(normalized_modules, key=lambda x: x["module_id"]),
        "by_symbol": by_symbol,
        "by_id": by_id,
        "fallback_used": fallback_used,
        "unresolved_items": unresolved,
    }


def build_module_catalog_enrichment(module_catalog: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for module in module_catalog.get("modules", []):
        symbol = normalize_symbol(module.get("canonical_symbol", ""))
        if symbol:
            out[symbol] = module
    return out


def build_process_step_index(process_step_catalog: dict[str, Any], aligned_process: dict[str, Any]) -> dict[str, Any]:
    by_symbol: dict[str, Any] = {}
    by_id: dict[str, Any] = {}
    by_step_id: dict[str, Any] = {}
    for step in process_step_catalog.get("steps", []):
        symbol = normalize_symbol(step.get("module_symbol", ""))
        module_id = str(step.get("module_id", ""))
        if symbol:
            by_symbol[symbol] = step
        if module_id:
            by_id[module_id] = step
        by_step_id[str(step.get("process_step_id"))] = step

    aligned_by_symbol: dict[str, Any] = {}
    for step in aligned_process.get("steps", []):
        symbol = normalize_symbol(step.get("module_id", ""))
        if symbol:
            aligned_by_symbol[symbol] = step

    return {
        "by_symbol": by_symbol,
        "by_module_id": by_id,
        "by_step_id": by_step_id,
        "aligned_by_symbol": aligned_by_symbol,
    }


def build_file_mapping_index(rows: list[dict[str, str]]) -> dict[str, Any]:
    by_module: dict[str, dict[str, list[Any]]] = {}
    unmapped_count = 0
    for row in rows:
        modules_cell = (row.get("CanonicalModules") or "").strip()
        role = (row.get("Role") or "other").strip()
        service = (row.get("Service") or "").strip() or None
        rel_path = _to_relative_repo_path(row.get("FullName", ""))
        is_test = str(row.get("IsTest", "0")).strip() in {"1", "true", "True"}
        modules = [normalize_symbol(m.strip()) for m in modules_cell.split(",") if m.strip()]
        if not modules:
            unmapped_count += 1
            continue
        ownership = "owned" if len(modules) == 1 else "shared"
        for module in modules:
            target = by_module.setdefault(
                module,
                {"owned_files": [], "shared_service_files": [], "candidate_owned_files": [], "file_role_index": []},
            )
            if ownership == "owned":
                target["owned_files"].append(rel_path)
            else:
                target["shared_service_files"].append(rel_path)
            target["file_role_index"].append(
                {
                    "path": rel_path,
                    "service": service,
                    "role": role if role else "other",
                    "ownership": ownership,
                    "is_test": is_test,
                    "canonical_modules": modules,
                    "notes": "",
                }
            )

    return {
        "rows_total": len(rows),
        "rows_unmapped": unmapped_count,
        "by_module": by_module,
    }


def build_service_runtime_index(module_map_text: str, ui_catalog: dict[str, Any]) -> dict[str, Any]:
    ui_ports = {}
    for product in ui_catalog.get("ui_products", []):
        if product.get("service_name") == "dashboard-backend":
            ui_ports["U1_DASHBOARD_BACKEND"] = product.get("declared_port")
        if product.get("service_name") == "gui-gateway":
            ui_ports["U2_GUI_GATEWAY"] = product.get("declared_port")

    ports = {**KNOWN_PORTS, **{k: v for k, v in ui_ports.items() if isinstance(v, int)}}
    return {
        "ports_by_symbol": ports,
        "module_map_excerpt_used": bool(module_map_text),
    }


def build_communication_channel_index(communication_channels: dict[str, Any]) -> dict[str, Any]:
    by_owner: dict[str, list[dict[str, Any]]] = {}
    for channel in communication_channels.get("channels", []):
        owner = normalize_symbol(channel.get("owning_module_symbol", "") or "")
        if owner:
            by_owner.setdefault(owner, []).append(channel)
    return {"by_owner_symbol": by_owner, "all_channels": communication_channels.get("channels", [])}


def build_ui_product_index(ui_catalog: dict[str, Any]) -> dict[str, Any]:
    index: dict[str, Any] = {}
    for product in ui_catalog.get("ui_products", []):
        name = str(product.get("name", "")).lower()
        service_name = str(product.get("service_name", "")).lower()
        if "dashboard backend" in name or service_name == "dashboard-backend":
            index["U1_DASHBOARD_BACKEND"] = product
        elif "gui gateway" in name or service_name == "gui-gateway":
            index["U2_GUI_GATEWAY"] = product
        elif "overlay" in name:
            index["U3_MT4_EXPIRY_OVERLAY"] = product
        elif "desktop operator" in name:
            index["U4_DESKTOP_OPERATOR"] = product
    return index


def build_mt4_constraint_index(mt4_ref: dict[str, Any], communication_channels: dict[str, Any]) -> dict[str, Any]:
    ai_rules = mt4_ref.get("authority_model", {}).get("ai_decision_rules", [])
    channels = communication_channels.get("channels", [])
    return {"ai_rules": ai_rules, "channels": channels}


def build_dependency_candidate_index(
    module_universe: dict[str, Any],
    enrichment: dict[str, Any],
    process_step_index: dict[str, Any],
) -> dict[str, Any]:
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    symbol_to_id = {s: m["module_id"] for s, m in module_universe["by_symbol"].items()}
    step_by_id = process_step_index["by_step_id"]

    for symbol, enriched in enrichment.items():
        deps = []
        for dep in enriched.get("dependencies", []):
            dep_symbol = normalize_symbol(str(dep))
            if dep_symbol in symbol_to_id:
                deps.append(
                    {
                        "target_type": "module",
                        "target_symbol": dep_symbol,
                        "target_id": symbol_to_id[dep_symbol],
                        "relationship": "requires",
                        "reason": "module_catalog",
                    }
                )
        by_symbol.setdefault(symbol, []).extend(deps)

    for symbol, step in process_step_index["by_symbol"].items():
        step_deps = []
        for dep_step_id in step.get("dependency_step_ids", []):
            dep_step = step_by_id.get(str(dep_step_id))
            if not dep_step:
                continue
            dep_symbol = normalize_symbol(dep_step.get("module_symbol", ""))
            target_id = symbol_to_id.get(dep_symbol)
            if dep_symbol and target_id:
                step_deps.append(
                    {
                        "target_type": "module",
                        "target_symbol": dep_symbol,
                        "target_id": target_id,
                        "relationship": "consumes_output",
                        "reason": "process_step_catalog.dependency_step_ids",
                    }
                )
        by_symbol.setdefault(symbol, []).extend(step_deps)

    # de-dupe by target_id + relationship
    for symbol, deps in by_symbol.items():
        seen = set()
        compact = []
        for dep in deps:
            key = (dep["target_id"], dep["relationship"])
            if key in seen:
                continue
            seen.add(key)
            compact.append(dep)
        by_symbol[symbol] = compact

    return {"by_symbol": by_symbol}

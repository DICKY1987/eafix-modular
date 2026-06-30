#!/usr/bin/env python3
"""Source loading and authority preflight helpers."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_SOURCE_FILES: dict[str, str] = {
    "routing_authority": "eafix_project_knowledge_reference_routing_instructions.json",
    "module_universe_vnext": "EAFIX_auth_docs/Claude_gen_atomic_module_catalog_vNext.json",
    "manifest_schema": "EAFIX_auth_docs/eafix_unified_atomic_module_schema_v1_0_0.json",
    "fill_doctrine": "EAFIX_auth_docs/eafix_unified_atomic_module_manifest_ai_fill_instructions_v1_0_0.md",
    "existing_draft_bundle": "EAFIX_auth_docs/eafix module manifests bundle.json",
    "module_catalog_enrichment": "EAFIX_auth_docs/module_catalog.json",
    "process_step_catalog": "EAFIX_auth_docs/process_step_catalog.json",
    "aligned_process": "EAFIX_auth_docs/updated_trading_process_aligned.json",
    "file_mapping": "EAFIX_auth_docs/file_module_mapping.csv",
    "service_runtime": "EAFIX_auth_docs/eafix_services_ai_reference_20260510.json",
    "module_map": "EAFIX_auth_docs/EAFIX-Modular — End-to-End Module Map.txt",
    "communication_channels": "EAFIX_auth_docs/communication_channels.json",
    "mt4_python_channels": "EAFIX_auth_docs/MT4_Python communication channels.txt",
    "ui_catalog": "EAFIX_auth_docs/ui_catalog.json",
    "mt4_authoritative": "EAFIX_auth_docs/mt4 authoritative reference for ai.json",
    "capability_registry": "EAFIX_auth_docs/converted_capability_registry.json",
    "dependency_layers_pdf": "EAFIX_auth_docs/dependency layers.pdf",
    "dependency_layers_parsed": "EAFIX_auth_docs/dependency_layers_parsed.json",
}


AUTHORITY_ROLES: dict[str, str] = {
    "routing_authority": "routing_and_conflict_policy",
    "module_universe_vnext": "module_universe_source",
    "manifest_schema": "schema_source",
    "fill_doctrine": "manifest_population_doctrine",
    "existing_draft_bundle": "defect_evidence_and_fallback_universe",
    "module_catalog_enrichment": "module_enrichment",
    "process_step_catalog": "process_contracts_primary",
    "aligned_process": "process_contracts_validation_failure",
    "file_mapping": "file_ownership_evidence",
    "service_runtime": "runtime_evidence",
    "module_map": "architecture_runtime_hint",
    "communication_channels": "transport_channel_evidence",
    "mt4_python_channels": "transport_channel_narrative_evidence",
    "ui_catalog": "ui_authority",
    "mt4_authoritative": "mt4_platform_constraints_authority",
    "capability_registry": "capability_reuse",
    "dependency_layers_pdf": "dependency_graph_evidence",
    "dependency_layers_parsed": "dependency_graph_parsed",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_csv(path: Path) -> list[dict[str, str]]:
    raw = path.read_text(encoding="utf-8-sig").splitlines()
    while raw and not raw[0].strip():
        raw.pop(0)
    if not raw:
        return []
    return list(csv.DictReader(raw))


def run_authority_preflight(repo_root: Path) -> dict[str, Any]:
    files: dict[str, Any] = {}
    missing: list[str] = []
    for key, relative in REQUIRED_SOURCE_FILES.items():
        abs_path = repo_root / relative
        exists = abs_path.exists()
        if not exists:
            missing.append(relative)
        files[key] = {
            "relative_path": relative,
            "exists": exists,
            "sha256": sha256_file(abs_path) if exists else None,
            "authority_role": AUTHORITY_ROLES.get(key, "unknown"),
        }

    conflict_resolution_order = [
        "routing_authority",
        "module_universe_vnext",
        "manifest_schema",
        "module_catalog_enrichment",
        "process_step_catalog",
        "aligned_process",
        "communication_channels",
        "ui_catalog",
        "mt4_authoritative",
        "file_mapping",
        "service_runtime",
        "module_map",
        "existing_draft_bundle",
    ]

    unresolved_conflicts = []
    if missing:
        unresolved_conflicts.append(
            {
                "category": "missing_sources",
                "items": missing,
            }
        )

    return {
        "source_files": files,
        "module_universe_source": "EAFIX_auth_docs/Claude_gen_atomic_module_catalog_vNext.json",
        "schema_source": "EAFIX_auth_docs/eafix_unified_atomic_module_schema_v1_0_0.json",
        "conflict_resolution_order": conflict_resolution_order,
        "unresolved_authority_conflicts": unresolved_conflicts,
    }


def load_dependency_layers(repo_root: Path) -> "tuple[bool, dict[str, Any]]":
    """Load pre-parsed dependency layer data extracted from dependency layers.pdf.

    Returns (parsed, data) where parsed is True when the JSON sidecar exists and
    contains a valid layer list, and data holds the full parsed content.
    """
    json_path = repo_root / REQUIRED_SOURCE_FILES["dependency_layers_parsed"]
    if not json_path.exists():
        return False, {}
    try:
        data = load_json(json_path)
        layers = data.get("layers", [])
        if isinstance(layers, list) and len(layers) > 0:
            return True, data
    except Exception:
        pass
    return False, {}

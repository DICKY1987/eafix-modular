#!/usr/bin/env python3
"""Generate deterministic P20 schema and work-cell projections."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


GENERATED_AT = "2026-07-31T00:00:00Z"

WORK_CELLS = {
    "m0029-u2-gui-gateway/m0029-context/work-cells/UI_GATEWAY_REST_API_GATEWAY.json": {
        "legacy": "services/dashboard-backend/work_cells/UI_GATEWAY_REST_API_GATEWAY.json",
        "manifest": "m0029-u2-gui-gateway/manifest.json",
        "service": "gui-gateway",
        "work_cell_type": "ui_gateway",
        "legacy_parent": "SHARED_LIBS",
        "capability": "ui",
    },
    "m0029-u2-gui-gateway/m0029-context/work-cells/UI_GATEWAY_WEBSOCKET_GATEWAY.json": {
        "legacy": "services/dashboard-backend/work_cells/UI_GATEWAY_WEBSOCKET_GATEWAY.json",
        "manifest": "m0029-u2-gui-gateway/manifest.json",
        "service": "gui-gateway",
        "work_cell_type": "ui_gateway",
        "legacy_parent": "SHARED_LIBS",
        "capability": "ui",
    },
    "m0017-b2-mt4-ea-executor/m0017-context/work-cells/EA_SYSTEM_D_EXECUTION_FEEDBACK__MQL4_ORDER_RESULT.json": {
        "legacy": "services/execution-engine/work_cells/EA_SYSTEM_D_EXECUTION_FEEDBACK__MQL4_ORDER_RESULT.json",
        "manifest": "m0017-b2-mt4-ea-executor/manifest.json",
        "service": "execution-engine",
        "work_cell_type": "ea_side_mql4_system",
        "legacy_parent": "B2_MT4_EA_EXECUTOR",
        "capability": "mql4",
    },
    "m0027-r3-correlation-guard/m0027-context/work-cells/R1_4_CORRELATION_GUARDS.json": {
        "legacy": "services/risk-manager/work_cells/R1_4_CORRELATION_GUARDS.json",
        "manifest": "m0027-r3-correlation-guard/manifest.json",
        "service": "correlation-guard",
        "work_cell_type": "risk_rule_family",
        "legacy_parent": "R1_RISK_EVALUATOR",
        "capability": "python",
    },
    "m0034-sk2-idempotency/m0034-context/work-cells/R1_7_IDEMPOTENCY_DUPLICATE_ORDER_PREVENTION.json": {
        "legacy": "services/risk-manager/work_cells/R1_7_IDEMPOTENCY_DUPLICATE_ORDER_PREVENTION.json",
        "manifest": "m0034-sk2-idempotency/manifest.json",
        "service": "idempotency",
        "work_cell_type": "risk_rule_family",
        "legacy_parent": "R1_RISK_EVALUATOR",
        "capability": "python",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def schema_projection(repo: Path) -> dict[str, Any]:
    canonical = load_json(
        repo
        / "m0009-c2-indicator-engine/m0009-schemas/inputs/1199900011260118_indicator_record.schema.json"
    )
    projection = deepcopy(canonical)
    projection.pop("_doc_id", None)
    projection.pop("doc_id", None)
    projection["$comment"] = (
        "Generated non-authoritative documentation projection; canonical source: "
        "m0009-c2-indicator-engine/m0009-schemas/inputs/"
        "1199900011260118_indicator_record.schema.json"
    )
    return projection


def work_cell(repo: Path, target: str, spec: dict[str, str]) -> dict[str, Any]:
    manifest = load_json(repo / spec["manifest"])
    identity = manifest["module_identity"]
    ownership = manifest["file_ownership"]
    dependencies = [
        item["target_symbol"]
        for item in manifest.get("dependencies", [])
        if item.get("target_symbol")
    ]
    work_cell_id = Path(target).stem
    legacy_service = spec["legacy"].split("/")[1]
    if spec["work_cell_type"] == "ui_gateway":
        forbidden = ["B2_MT4_EA_EXECUTOR", "O1_ORDER_ROUTER", "R2_ORDER_INTENT_COMPILER"]
        references = ["DOC_UI_CATALOG", "DOC_COMM_CHANNELS", "DOC_MODULE_CATALOG", "DOC_PROCESS_STEP_CATALOG", "DOC_ROUTING_INSTRUCTIONS", "DOC_DECOMPOSITION_MODEL"]
    elif spec["work_cell_type"] == "ea_side_mql4_system":
        forbidden = ["C1_BAR_BUILDER", "C2_INDICATOR_ENGINE", "C3_FEATURE_PACKAGER", "D2_CALENDAR_SOURCE_ADAPTER", "D3_CALENDAR_NORMALIZER", "D4_CALENDAR_TRIGGER_BUILDER", "E1_OUTCOME_BUCKETIZER", "E2_PROXIMITY_EVALUATOR", "E3_MATRIX_LOOKUP", "E4_REENTRY_INTENT_BUILDER"]
        references = ["DOC_MODULE_CATALOG", "DOC_PROCESS_STEP_CATALOG", "DOC_ALIGNED_PROCESS", "DOC_ROUTING_INSTRUCTIONS", "DOC_DECOMPOSITION_MODEL", "DOC_COMM_CHANNELS", "DOC_MT4_AUTHORITATIVE_REF", "DOC_MT4_PY_CHANNELS_TXT", "DOC_FILE_MODULE_MAPPING", "DOC_EA_EXECUTION_ENGINE_SAMPLE"]
    else:
        forbidden = ["B2_MT4_EA_EXECUTOR", "B3_EXEC_EVENT_NORMALIZER", "D2_CALENDAR_SOURCE_ADAPTER", "D3_CALENDAR_NORMALIZER", "D4_CALENDAR_TRIGGER_BUILDER"]
        references = ["DOC_MODULE_CATALOG", "DOC_PROCESS_STEP_CATALOG", "DOC_ALIGNED_PROCESS", "DOC_ROUTING_INSTRUCTIONS", "DOC_DECOMPOSITION_MODEL", "DOC_MT4_AUTHORITATIVE_REF", "DOC_ATOMIC_LIFECYCLE_MD", "DOC_FILE_MODULE_MAPPING", "DOC_SERVICES_AI_REFERENCE"]
    return {
        "manifest_type": "canonical_work_cell_binding",
        "generated_at_utc": GENERATED_AT,
        "work_cell_id": work_cell_id,
        "legacy_work_cell_aliases": [work_cell_id],
        "work_cell_type": spec["work_cell_type"],
        "owner_module_id": identity["module_id"],
        "parent_module_symbol": identity["canonical_symbol"],
        "legacy_parent_module_symbol": spec["legacy_parent"],
        "requires_agent_capability": [spec["capability"]],
        "context_packet_path": (
            f"context_packets/{identity['module_id']}/{work_cell_id}/"
            "work_cell_context.json"
        ),
        "service": spec["service"],
        "source_files": ownership.get("source_files", []),
        "test_files": ownership.get("test_files", []),
        "allowed_dependencies": dependencies,
        "forbidden_dependencies": forbidden,
        "required_reference_documents": references,
        "notes": [
            "Regenerated from the canonical module manifest during P20.",
            f"Legacy {legacy_service} binding retained as lineage evidence: {spec['legacy']}.",
        ],
    }


def outputs(repo: Path) -> dict[str, str]:
    result = {
        "docs/reference/generated/indicator_record.schema.json": render_json(
            schema_projection(repo)
        )
    }
    for target, spec in WORK_CELLS.items():
        result[target] = render_json(work_cell(repo, target, spec))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    rendered = outputs(repo)
    stale: list[str] = []
    for relative, content in rendered.items():
        target = repo / relative
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                stale.append(relative)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    if stale:
        print("STALE: " + ", ".join(stale))
        return 1
    print(f"validated {len(rendered)} deterministic P20 outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

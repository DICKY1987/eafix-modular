"""Validation for deterministic P20 regeneration outputs."""

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_p20_outputs_are_current() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "tools/migration/generate_p20_outputs.py",
            "--check",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_indicator_projection_tracks_canonical_schema_semantics() -> None:
    canonical = json.loads(
        (
            REPO_ROOT
            / "m0009-c2-indicator-engine/m0009-schemas/inputs/1199900011260118_indicator_record.schema.json"
        ).read_text(encoding="utf-8")
    )
    projection = json.loads(
        (
            REPO_ROOT / "docs/reference/generated/indicator_record.schema.json"
        ).read_text(encoding="utf-8")
    )
    canonical.pop("_doc_id", None)
    canonical.pop("doc_id", None)
    projection.pop("$comment", None)
    assert projection == canonical


def test_reclassified_work_cells_use_canonical_owners() -> None:
    expected = {
        "m0017-b2-mt4-ea-executor/m0017-context/work-cells/EA_SYSTEM_D_EXECUTION_FEEDBACK__MQL4_ORDER_RESULT.json": "B2_MT4_EA_EXECUTOR",
        "m0027-r3-correlation-guard/m0027-context/work-cells/R1_4_CORRELATION_GUARDS.json": "R3_CORRELATION_GUARD",
        "m0029-u2-gui-gateway/m0029-context/work-cells/UI_GATEWAY_REST_API_GATEWAY.json": "U2_GUI_GATEWAY",
        "m0029-u2-gui-gateway/m0029-context/work-cells/UI_GATEWAY_WEBSOCKET_GATEWAY.json": "U2_GUI_GATEWAY",
        "m0034-sk2-idempotency/m0034-context/work-cells/R1_7_IDEMPOTENCY_DUPLICATE_ORDER_PREVENTION.json": "SK2_IDEMPOTENCY",
    }
    for relative, owner in expected.items():
        record = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
        assert record["parent_module_symbol"] == owner
        assert record["legacy_work_cell_aliases"] == [record["work_cell_id"]]

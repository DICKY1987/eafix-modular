# doc_id: DOC-TEST-MT4-GOV-0001
"""Governance checks for the MT4 authoritative AI reference."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_REFERENCE = REPO_ROOT / "mt4 authoritative reference for ai.json"
OBSOLETE_REFERENCE = REPO_ROOT / "mt4_authoritative_reference_for_ai.json"


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: set[str] = set()
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise DuplicateKeyError(f"Duplicate JSON key: {key}")
        seen.add(key)
        output[key] = value
    return output


def load_reference(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
    )


def test_mt4_json_references_have_no_duplicate_keys() -> None:
    load_reference(ACTIVE_REFERENCE)
    load_reference(OBSOLETE_REFERENCE)


def test_exactly_one_mt4_reference_is_active() -> None:
    active = load_reference(ACTIVE_REFERENCE)
    obsolete = load_reference(OBSOLETE_REFERENCE)

    references = [active, obsolete]
    active_references = [
        ref for ref in references if str(ref.get("status", "")).startswith("active")
    ]

    assert len(active_references) == 1
    assert active["schema_version"] == "2.0.0"
    assert active["status"] == "active_governance_baseline"
    assert obsolete["status"] == "obsolete_historical_baseline"
    assert obsolete["superseded_by"]["reference_path"] == ACTIVE_REFERENCE.name


def test_stable_ids_exist_on_governance_rows() -> None:
    reference = load_reference(ACTIVE_REFERENCE)

    namespaces = {
        item["namespace"]
        for item in reference["stable_identifier_architecture"]["id_namespaces"]
    }
    assert {
        "native_capability_id",
        "gate_id",
        "contract_id",
        "decision_id",
        "field_authority_id",
        "source_pointer_id",
        "broker_profile_id",
        "bridge_channel_id",
        "validation_result_id",
        "traceability_id",
    }.issubset(namespaces)

    field_authority_ids = [
        row["field_authority_id"] for row in reference["ui_data_authority_matrix"]
    ]
    decision_ids = [
        row["decision_id"] for row in reference["custom_development_decision_matrix"]
    ]
    traceability_ids = [
        row["traceability_id"]
        for row in reference["mt4_capability_traceability_matrix"]
    ]

    assert len(field_authority_ids) == len(set(field_authority_ids))
    assert len(decision_ids) == len(set(decision_ids))
    assert len(traceability_ids) == len(set(traceability_ids))


def test_traceability_matrix_references_known_governance_objects() -> None:
    reference = load_reference(ACTIVE_REFERENCE)

    capability_ids = {
        row["capability_id"] for row in reference["native_capability_catalog"]
    }
    gate_ids = {row["gate_id"] for row in reference["validation_gates"]}
    bridge_channel_ids = {
        row["channel_id"]
        for row in reference["huey_p_project_alignment"]["current_bridge_channels"]
    }
    source_ids = {row["source_id"] for row in reference["source_registry"]}

    for row in reference["mt4_capability_traceability_matrix"]:
        assert row["native_capability_id"] in capability_ids
        assert row["bridge_channel_id"] in bridge_channel_ids
        assert set(row["validation_gates"]).issubset(gate_ids)
        assert set(row["source_pointer_ids"]).issubset(source_ids)

        for relative_path in row["files"]:
            assert (REPO_ROOT / relative_path).exists(), relative_path

        if row["status"] == "gap":
            assert row["gap_id"]
            assert row["gap_action_required"]

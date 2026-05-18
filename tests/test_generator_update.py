from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPO_ROOT / "EA-REG" / "generate_three_artifact_catalogs.py"


def load_generator_module():
    spec = importlib.util.spec_from_file_location("ea_reg_generator", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_resolve_module_symbol_maps_aliases_to_canonical_symbols():
    generator = load_generator_module()
    identifier_context = generator.load_identifier_context()

    assert generator.resolve_module_symbol("O2_OMS", identifier_context) == "O2_OMS_STATE_MACHINE"
    assert generator.resolve_module_symbol("O3_PNL_CLASSIFIER", identifier_context) == "O3_TRADE_CLOSE_CLASSIFIER"


def test_process_step_catalog_uses_numeric_module_ids():
    generator = load_generator_module()
    identifier_context = generator.load_identifier_context()
    process_source, process_doc = generator.select_process_source()

    catalog, _module_to_steps = generator.build_process_step_catalog(
        process_doc,
        process_source,
        identifier_context,
    )

    assert len(catalog["steps"]) == 26
    assert all(step["module_id"].startswith("5") and len(step["module_id"]) == 20 for step in catalog["steps"])
    assert all("module_symbol" in step and step["module_symbol"] for step in catalog["steps"])

    loop_step = next(step for step in catalog["steps"] if step["step_number"] == 25)
    assert loop_step["module_symbol"] == "F1_FLOW_ORCHESTRATOR"
    assert loop_step["module_id"] == identifier_context["modules"]["F1_FLOW_ORCHESTRATOR"]["numeric_id"]


def test_file_registry_builder_uses_physical_ids_and_new_columns():
    generator = load_generator_module()
    identifier_context = generator.load_identifier_context()
    classification_rules = generator.load_classification_rules()
    physical_registry_rows = generator.load_physical_registry_rows()
    process_source, process_doc = generator.select_process_source()
    legacy_rows = generator.load_legacy_mapping_rows()

    _catalog, module_to_steps = generator.build_process_step_catalog(
        process_doc,
        process_source,
        identifier_context,
    )
    rows = generator.build_file_registry(
        module_to_steps=module_to_steps,
        legacy_rows=legacy_rows,
        physical_registry_rows=physical_registry_rows,
        classification_rules=classification_rules,
        identifier_context=identifier_context,
        last_verified_utc=str(identifier_context["payload"]["generated_at"]),
    )

    assert rows
    assert list(rows[0].keys()) == generator.CSV_HEADER

    calendar_main = next(
        row for row in rows if row["relative_path"] == "services/calendar-ingestor/src/2099900093260118_main.py"
    )
    assert calendar_main["file_id"].startswith("1") and len(calendar_main["file_id"]) == 20
    assert calendar_main["directory_id"].startswith("2") and len(calendar_main["directory_id"]) == 20
    assert calendar_main["module_id"] == identifier_context["modules"]["D2_CALENDAR_SOURCE_ADAPTER"]["numeric_id"]
    assert calendar_main["assigned_module_name"] == "Calendar Source Adapter"
    assert calendar_main["file_scope_class"] == "module_owned"
    assert calendar_main["process_steps"] == "60000000000000000003"

    remediator = next(
        row for row in rows if row["relative_path"] == "compliance/auto-remediation/2099900012260118_remediation-engine.py"
    )
    assert remediator["file_scope_class"] == "module_owned"
    assert remediator["module_id"] == identifier_context["modules"]["S1_SIGNAL_ENGINE"]["numeric_id"]
    assert remediator["assigned_module_name"] == "Signal Engine"

    assert all(row["module_id"] for row in rows)

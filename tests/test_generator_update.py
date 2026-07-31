from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPO_ROOT / "EA-REG" / "generate_three_artifact_catalogs.py"


def load_generator_module():
    spec = importlib.util.spec_from_file_location("ea_reg_generator", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resolve_module_symbol_maps_aliases_to_canonical_symbols():
    generator = load_generator_module()
    identifier_context = generator.load_identifier_context()

    assert generator.resolve_module_symbol("O2_OMS", identifier_context) == "O2_OMS_STATE_MACHINE"
    assert generator.resolve_module_symbol("O3_PNL_CLASSIFIER", identifier_context) == "O3_TRADE_CLOSE_CLASSIFIER"


def test_legacy_generator_fails_explicitly_when_retired_inputs_are_absent():
    generator = load_generator_module()

    with pytest.raises(FileNotFoundError, match="physical registry not found"):
        generator.load_physical_registry_rows()
    with pytest.raises(FileNotFoundError, match="classification rules not found"):
        generator.load_classification_rules()


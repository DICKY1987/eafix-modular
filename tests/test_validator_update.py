from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "EA-REG" / "validate_three_artifact_alignment.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("ea_reg_validator", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_validator_reports_all_statuses_pass():
    validator_module = load_validator_module()
    validator = validator_module.ArtifactValidator(REPO_ROOT / "EA-REG")

    success, report = validator.validate_all()

    assert success is True
    assert report["physical_status"] == "PASS"
    assert report["alignment_status"] == "PASS"
    assert report["readiness_status"] == "PASS"
    assert report["semantic_coverage_pct"] >= 85.0

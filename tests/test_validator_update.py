from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "EA-REG" / "validate_three_artifact_alignment.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("ea_reg_validator", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_validator_reports_missing_authorities_without_false_pass(tmp_path: Path):
    validator_module = load_validator_module()
    legacy_root = tmp_path / "EA-REG"
    legacy_root.mkdir()
    validator = validator_module.ArtifactValidator(legacy_root)

    success, report = validator.validate_all()

    assert success is False
    assert report["physical_status"] == "FAIL"
    assert report["alignment_status"] == "FAIL"
    assert report["readiness_status"] == "FAIL"
    assert report["physical_errors"]
    assert report["alignment_errors"]

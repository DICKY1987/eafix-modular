"""Preserve alias protection after retirement of the historical generator."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_aliases_resolve_to_canonical_root_symbols():
    identities = [json.loads(p.read_text())["module_identity"]
                  for p in ROOT.glob("m00*/manifest.json")]
    aliases = {alias: item["canonical_symbol"] for item in identities
               for alias in item["legacy_aliases"]}
    assert aliases["O2_OMS"] == "O2_OMS_STATE_MACHINE"
    assert aliases["O3_PNL_CLASSIFIER"] == "O3_TRADE_CLOSE_CLASSIFIER"


def test_retired_generator_is_not_restored_as_authority():
    assert not (ROOT / "EA-REG/generate_three_artifact_catalogs.py").exists()
    assert (ROOT / "Master_Archive/EA-REG/generate_three_artifact_catalogs.py").is_file()
    caller = (ROOT / "ci/2099900300260118_validate_atomic_module_manifests.py").read_text()
    assert "generate_three_artifact_catalogs" not in caller
    assert "tools.manifest_generation" not in caller

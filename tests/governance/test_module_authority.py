"""Regression coverage for specification/structure separation and safe mutations."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "governance/module_consolidation/validation"))
from fixture_runner import run


def test_all_offline_authority_fixtures():
    report = run()
    assert report["status"] == "PASS", [c for c in report["checks"] if not c["passed"]]
    assert report["specification_readiness_waived"] is False

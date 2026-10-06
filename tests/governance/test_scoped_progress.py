from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "governance/module_consolidation"))
from progress_gate import HELD, validate_progress
import progress_gate


def test_independent_progress_is_not_cutover_approval():
    report = validate_progress(ROOT)
    assert report["status"] == "PASS"
    assert report["validation_scope"] == "independent_progress_only"
    assert report["cutover_status"] == "BLOCKED"
    assert report["cutover_approved"] is False
    assert report["completed"] is False


@pytest.mark.parametrize("action", sorted(HELD) + ["unknown_action"])
def test_held_or_unknown_action_fails_closed(action):
    report = validate_progress(ROOT, action)
    assert report["status"] == "BLOCKED"
    assert report["authorized"] is False
    assert report["cutover_approved"] is False


@pytest.mark.parametrize("field,value", [("status", "unapproved"), ("full_acceptance_waived", True), ("effective_baseline", "wrong")])
def test_invalid_policy_cannot_authorize_progress(monkeypatch, field, value):
    real_load = progress_gate.load
    def changed_load(path):
        data = real_load(path)
        if path.name == "execution_policy.json":
            data[field] = value
        return data
    monkeypatch.setattr(progress_gate, "load", changed_load)
    monkeypatch.setattr(progress_gate, "validate_repository", lambda *args, **kwargs: {"status": "PASS"})
    report = validate_progress(ROOT)
    assert report["status"] == "BLOCKED"
    assert report["cutover_approved"] is False

"""The replacement route propagates failures and cannot write authorities."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def caller():
    spec = importlib.util.spec_from_file_location("authority_ci", ROOT / "ci/2099900300260118_validate_atomic_module_manifests.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_gate_propagates_block_without_running_projection(monkeypatch):
    module = caller()
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.main([]) == 1
    assert len(calls) == 1
    assert calls[0][-2:] == ["--mode", "active"]


def test_progress_requires_explicit_scope_and_does_not_certify_projections(monkeypatch):
    module = caller()
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.main(["--scope", "progress"]) == 0
    assert len(calls) == 1
    assert calls[0][-1].endswith("progress_gate.py")


def test_projection_is_checked_only_after_full_acceptance(monkeypatch):
    module = caller()
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0 if len(calls) == 1 else 2)
    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.main([]) == 2
    assert calls[1][-2:] == ["governance/module_consolidation/generate_projections.py", "--check"]

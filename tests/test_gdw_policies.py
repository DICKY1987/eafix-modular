from __future__ import annotations

import os
from pathlib import Path

from lib.gdw_orchestrator import get_deferral_mode, maybe_defer_to_gdw


def test_deferral_mode_config_and_env(tmp_path: Path, monkeypatch):
    # Copy sample policies into tmp
    repo = tmp_path
    (repo / "config").mkdir(parents=True, exist_ok=True)
    sample = Path("config/gdw_policies.json").read_text(encoding="utf-8")
    (repo / "config/gdw_policies.json").write_text(sample, encoding="utf-8")

    # Default from config
    assert get_deferral_mode(repo) in ("prefer", "only", "off")

    # Env overrides
    monkeypatch.setenv("GDW_ONLY", "1")
    assert get_deferral_mode(repo) == "only"
    monkeypatch.delenv("GDW_ONLY", raising=False)
    monkeypatch.setenv("GDW_PREFER", "1")
    assert get_deferral_mode(repo) == "prefer"


def test_maybe_defer_rule_match(tmp_path: Path):
    repo = tmp_path
    (repo / "config").mkdir(parents=True, exist_ok=True)
    (repo / "config/gdw_policies.json").write_text(
        '{"rules":[{"match_substring":"commit and push","workflow_id":"git.commit_push.main"}]}',
        encoding="utf-8",
    )
    decision = maybe_defer_to_gdw("Please commit and push", repo)
    assert decision is not None
    assert decision.workflow_id == "git.commit_push.main"


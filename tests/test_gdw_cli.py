from __future__ import annotations

from src.cli_multi_rapid.cli import main


def test_gdw_list_runs(monkeypatch):
    rc = main(["gdw", "list"])
    assert rc == 0


def test_gdw_validate_default():
    rc = main(["gdw", "validate"])  # use default spec path
    assert rc == 0


def test_gdw_run_dry():
    rc = main(["gdw", "run", "git.commit_push.main", "--dry-run"])
    assert rc == 0


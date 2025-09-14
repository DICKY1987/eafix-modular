from __future__ import annotations

from src.cli_multi_rapid.cli import main


def test_gdw_list_runs(monkeypatch):
    rc = main(["gdw", "list"])
    assert rc == 0


def test_gdw_validate_default():
    rc = main(["gdw", "validate"])  # use default spec path
    assert rc == 0


def test_gdw_run_dry():
    for wf in [
        "git.commit_push.main",
        "build.container.sign",
        "security.scan.trivy",
        "k8s.deploy.rolling",
        "version.bump.semver",
    ]:
        rc = main(["gdw", "run", wf, "--dry-run"])
        assert rc == 0

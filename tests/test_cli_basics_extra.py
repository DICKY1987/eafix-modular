from __future__ import annotations

from pathlib import Path
from src.cli_multi_rapid.cli import main


def test_cli_greet_and_sum():
    assert main(["greet", "World"]) == 0
    assert main(["sum", "2", "3"]) == 0


def test_gdw_chain_dry(tmp_path: Path):
    chain = tmp_path / "chain.json"
    chain.write_text('{"steps": [{"workflow": "git.commit_push.main", "inputs": {}}]}', encoding="utf-8")
    rc = main(["gdw", "chain", str(chain), "--dry-run"])
    assert rc == 0


def test_cli_compliance_and_status():
    assert main(["compliance", "report"]) == 0
    assert main(["compliance", "check"]) == 0
    assert main(["workflow-status"]) in (0, 1)  # tolerate missing deps
    # Exercise phase stream list
    assert main(["phase", "stream", "list"]) in (0, 1)


def test_cli_self_healing_status():
    # Should not raise; returns 0
    assert main(["self-healing", "status"]) == 0
    # Exercise test path for additional coverage
    assert main(["self-healing", "test", "ERR_DISK_SPACE"]) in (0, 1)
    # Exercise config dump path
    assert main(["self-healing", "config"]) == 0


def test_run_job_with_tasks_json(tmp_path: Path, monkeypatch):
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {"label": "echo", "command": "echo", "args": ["hello"], "dependsOn": ["build"]},
            {"label": "build", "command": "python", "args": ["-V"]}
        ]
    }
    (tmp_path / "tasks.json").write_text(__import__("json").dumps(tasks), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["run-job"]) == 0
    assert main(["run-job", "--show", "steps"]) == 0
    assert main(["run-job", "--workflow-validate"]) == 0
    assert main(["run-job", "--compliance-check"]) == 0

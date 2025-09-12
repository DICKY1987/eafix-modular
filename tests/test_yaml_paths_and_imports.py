from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


TEST_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import cli_multi_rapid.cli as cli  # type: ignore


class TestYamlAndSteps(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(argv)
        return code, buf.getvalue()

    def test_steps_print_for_yaml_jobs(self) -> None:
        # Patch YAML loader to simulate a parsed YAML job
        fake_jobs = [
            {
                "source": "agent_jobs.yaml",
                "type": "agent_jobs.yaml",
                "name": "Demo",
                "tool": "toolx",
                "branch": "main",
                "worktree": "/tmp/work",
                "tests": "pytest -q",
            }
        ]
        with patch.object(cli, "_load_agent_jobs_yaml", return_value=fake_jobs):
            code, out = self._run(["run-job", "--file", "fake.yml", "--show", "steps"])
        self.assertEqual(code, 0)
        self.assertIn("worktree:", out)
        self.assertIn("tests:", out)

    def test_yaml_missing_module_short_circuit(self) -> None:
        # Force ImportError when attempting to import yaml in loader
        orig_import = __import__

        def fake_import(name, *args, **kwargs):  # type: ignore
            if name == "yaml":
                raise ImportError("simulated")
            return orig_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            # Using an arbitrary file path; loader returns [] before reading
            code, out = self._run(["run-job", "--file", "nonexistent.yaml"])
        self.assertEqual(code, 0)
        self.assertIn("No jobs matched.", out)


if __name__ == "__main__":
    unittest.main()


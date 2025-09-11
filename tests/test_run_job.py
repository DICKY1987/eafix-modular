from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout

# Ensure src is importable when running via unittest directly
TEST_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, "..", "src"))
if SRC_DIR not in os.sys.path:
    os.sys.path.insert(0, SRC_DIR)

from cli_multi_rapid.cli import main  # type: ignore


class TestRunJob(unittest.TestCase):
    def _run_and_capture(self, argv: list[str]) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(argv)
        self.assertEqual(exit_code, 0)
        return buf.getvalue()

    def test_list_from_tasks_json(self) -> None:
        # Use explicit file path to avoid relying on CWD discovery in CI
        output = self._run_and_capture(["run-job", "--file", "tasks.json"])  # path at repo root
        # Should list at least one known label from tasks.json
        self.assertIn("tasks.json: Job: UI (Aider)", output)

    def test_filter_by_name(self) -> None:
        output = self._run_and_capture(["run-job", "--file", "tasks.json", "--name", "triage"])  # filter substring
        # Expect a triage-related task present
        self.assertIn("triage", output.lower())

    def test_show_steps_flag(self) -> None:
        output = self._run_and_capture([
            "run-job",
            "--file",
            "tasks.json",
            "--name",
            "API (Claude Code)",
            "--show",
            "steps",
        ])
        # Detailed output includes args listing
        self.assertIn("args:", output)


if __name__ == "__main__":
    unittest.main()

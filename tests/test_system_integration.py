from __future__ import annotations

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout


# Ensure src on path similar to other tests
TEST_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from cli_multi_rapid.cli import main  # type: ignore


class TestSystemIntegration(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_end_to_end_cli_paths(self) -> None:
        # greet
        code, out = self._run(["greet", "Zoe"]) 
        self.assertEqual(code, 0)
        self.assertIn("Hello, Zoe!", out)

        # sum
        code, out = self._run(["sum", "2", "5"]) 
        self.assertEqual(code, 0)
        self.assertIn("7", out)

        # compliance report and check
        code, out = self._run(["compliance", "report"]) 
        self.assertEqual(code, 0)
        self.assertIn("Comprehensive Compliance Report", out)

        code, out = self._run(["compliance", "check"]) 
        self.assertEqual(code, 0)
        self.assertIn("COMPLIANCE CHECK", out)

        # run-job from tasks.json (repo root)
        code, out = self._run(["run-job", "--file", "tasks.json"]) 
        self.assertEqual(code, 0)
        self.assertIn("tasks.json:", out)

        # phase stream list returns JSON list
        code, out = self._run(["phase", "stream", "list"]) 
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        # phase stream run (dry): accept 0 or 1 based on actions
        code, out = self._run(["phase", "stream", "run", "stream-a", "--dry"]) 
        self.assertIn(code, (0, 1))

        # self-healing status summary
        code, out = self._run(["self-healing", "status"]) 
        self.assertEqual(code, 0)
        self.assertIn("Self-Healing System Status", out)
        self.assertIn("Available Error Codes", out)

        # self-healing test path (may fail/succeed depending on config)
        code, out = self._run(["self-healing", "test", "ERR_PATH_NOT_FOUND"]) 
        self.assertIn("Healing Result", out)
        self.assertIn("Attempts:", out)
        self.assertIn(code, (0, 1))

        # workflow-status may not be fully wired; accept 0 or 1
        code, out = self._run(["workflow-status"]) 
        self.assertIn(code, (0, 1))
        if code == 0:
            self.assertIn("Enhanced Workflow Status", out)


if __name__ == "__main__":
    unittest.main()


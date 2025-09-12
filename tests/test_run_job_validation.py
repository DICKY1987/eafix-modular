from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout


TEST_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from cli_multi_rapid.cli import main  # type: ignore


class TestRunJobValidationFlags(unittest.TestCase):
    def test_workflow_validation_and_compliance_check(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["run-job", "--file", "tasks.json", "--workflow-validate", "--compliance-check"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("WORKFLOW VALIDATION", out)
        self.assertIn("COMPLIANCE CHECK", out)


if __name__ == "__main__":
    unittest.main()


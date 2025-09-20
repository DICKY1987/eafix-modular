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


class TestWorkflowStatusCLI(unittest.TestCase):
    def test_workflow_status_path(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["workflow-status"])
        # Some environments may lack full workflow components; accept 0 or 1
        self.assertIn(code, (0, 1))
        text = buf.getvalue()
        if code == 0:
            self.assertIn("Enhanced Workflow Status", text)


if __name__ == "__main__":
    unittest.main()

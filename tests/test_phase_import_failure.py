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

from cli_multi_rapid.cli import main  # type: ignore


class TestPhaseImportFailure(unittest.TestCase):
    def test_orchestrator_import_failure_returns_error(self) -> None:
        # Cause import failure only for workflows.orchestrator
        orig_import = __import__

        def fake_import(name, *args, **kwargs):  # type: ignore
            if name.startswith("workflows"):
                raise RuntimeError("boom")
            return orig_import(name, *args, **kwargs)

        out = io.StringIO()
        err = io.StringIO()
        with patch("builtins.__import__", side_effect=fake_import):
            with redirect_stdout(out):
                with patch("sys.stderr", new=err):
                    code = main(["phase", "status"])
        self.assertEqual(code, 1)
        self.assertIn("workflow orchestrator unavailable", err.getvalue())


if __name__ == "__main__":
    unittest.main()

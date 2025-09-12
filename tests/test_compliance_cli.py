from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout


# Ensure src on path for direct unittest runs
TEST_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from cli_multi_rapid.cli import main  # type: ignore


class TestComplianceCLI(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_compliance_report(self) -> None:
        code, out = self._run(["compliance", "report"])
        self.assertEqual(code, 0)
        self.assertIn("Comprehensive Compliance Report", out)

    def test_compliance_check(self) -> None:
        code, out = self._run(["compliance", "check"])
        self.assertEqual(code, 0)
        self.assertIn("COMPLIANCE CHECK", out)


if __name__ == "__main__":
    unittest.main()


from __future__ import annotations

import io
import json
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


class TestPhaseStreamCLI(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_phase_stream_list_json(self) -> None:
        code, out = self._run(["phase", "stream", "list"])
        self.assertEqual(code, 0)
        # Should be valid JSON list
        data = json.loads(out)
        self.assertIsInstance(data, list)

    def test_phase_stream_run_dry(self) -> None:
        # Accept 0 or 1 depending on phase results, but should not crash
        code, _ = self._run(["phase", "stream", "run", "stream-a", "--dry"])
        self.assertIn(code, (0, 1))


if __name__ == "__main__":
    unittest.main()


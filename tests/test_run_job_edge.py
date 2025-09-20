from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from cli_multi_rapid.cli import main  # type: ignore


class TestRunJobEdge(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_nonexistent_manifest_graceful(self) -> None:
        code, out = self._run(["run-job", "--file", "nonexistent.json"])
        self.assertEqual(code, 0)
        self.assertIn("No jobs matched.", out)
        self.assertIn("failed to parse", out)


if __name__ == "__main__":
    unittest.main()


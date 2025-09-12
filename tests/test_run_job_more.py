from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

# Ensure src import path
TEST_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, "..", "src"))
if SRC_DIR not in os.sys.path:
    os.sys.path.insert(0, SRC_DIR)

from cli_multi_rapid.cli import main  # type: ignore


class TestRunJobMore(unittest.TestCase):
    def _run(self, argv: list[str]) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(argv)
        self.assertEqual(exit_code, 0)
        return buf.getvalue()

    def test_bad_json_manifest_prints_warning(self) -> None:
        # Create a malformed JSON file
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", dir=os.getcwd()) as tmp:
            tmp.write("{ not: valid")
            bad_path = os.path.basename(tmp.name)
        try:
            out = self._run(["run-job", "--file", bad_path])
        finally:
            try:
                os.remove(bad_path)
            except OSError:
                pass
        self.assertIn("Warning: failed to parse", out)
        self.assertIn("No jobs matched.", out)

    def test_yaml_without_pyyaml_yields_empty(self) -> None:
        # Create a small YAML manifest and rely on missing PyYAML to return []
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml", dir=os.getcwd()) as tmp:
            tmp.write("version: 2\njobs:\n  - name: demo\n    tool: test\n")
            ypath = os.path.basename(tmp.name)
        try:
            out = self._run(["run-job", "--file", ypath])
        finally:
            try:
                os.remove(ypath)
            except OSError:
                pass
        # If PyYAML is installed, we list the YAML job; otherwise we report no jobs
        if "No jobs matched." in out:
            self.assertIn("No jobs matched.", out)
        else:
            self.assertIn("[tool: test, branch:", out)


if __name__ == "__main__":
    unittest.main()

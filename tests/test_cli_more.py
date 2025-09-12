from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

# Ensure src is importable
TEST_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, "..", "src"))
if SRC_DIR not in os.sys.path:
    os.sys.path.insert(0, SRC_DIR)

from cli_multi_rapid.cli import main  # type: ignore


class TestRunJobDiscovery(unittest.TestCase):
    def test_no_manifests_found(self) -> None:
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = main(["run-job"])  # discover in empty directory
                self.assertEqual(code, 0)
                self.assertIn("No manifests found", buf.getvalue())
            finally:
                os.chdir(cwd)


class TestRunJobDepends(unittest.TestCase):
    def test_tasks_json_depends_on_printed(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["run-job", "--file", "tasks.json", "--name", "Start all jobs (parallel)", "--show", "steps"])  # noqa: E501
        self.assertEqual(code, 0)
        self.assertIn("dependsOn", buf.getvalue())


class TestMainErrorPath(unittest.TestCase):
    def test_main_with_no_args_returns_error(self) -> None:
        # argparse raises SystemExit when required subcommand is missing; capture stderr
        err = io.StringIO()
        with redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                main([])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("error: the following arguments are required: command", err.getvalue())


if __name__ == "__main__":
    unittest.main()

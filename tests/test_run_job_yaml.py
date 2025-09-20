from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from cli_multi_rapid.cli import main  # type: ignore


class TestRunJobYAML(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_yaml_manifest_list_and_steps(self) -> None:
        data = """
        version: 1
        jobs:
          - name: demo YAML
            tool: tester
            branch: demo
            worktree: /tmp/wt
            tests: pytest -q
        """
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml", dir=os.getcwd()) as tmp:
            tmp.write(data)
            ypath = os.path.basename(tmp.name)
        try:
            code, out = self._run(["run-job", "--file", ypath, "--show", "steps"])
        finally:
            try:
                os.remove(ypath)
            except OSError:
                pass
        self.assertEqual(code, 0)
        self.assertIn("demo YAML", out)
        self.assertIn("tool: tester", out)
        self.assertIn("worktree:", out)
        self.assertIn("tests:", out)


if __name__ == "__main__":
    unittest.main()


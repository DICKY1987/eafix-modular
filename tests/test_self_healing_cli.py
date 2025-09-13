from __future__ import annotations

import io
import sys
import types
import unittest
from contextlib import redirect_stdout
from typing import Dict, List

from cli_multi_rapid.cli import main  # type: ignore
from cli_multi_rapid.self_healing_manager import ErrorCode, SelfHealingResult


class _FakeHealingManager:
    def __init__(self) -> None:
        self.config_path = "fake://config.yaml"
        self.config = {
            "self_healing": {
                "max_attempts": 1,
                "base_backoff_seconds": 0,
                "max_backoff_seconds": 0,
                "security_hard_fail": [],
            }
        }
        self.fixers: Dict[ErrorCode, List[object]] = {
            ErrorCode.ERR_PATH_NOT_FOUND: [object()],
            ErrorCode.ERR_SIG_INVALID: [],
        }

    def attempt_healing(self, error_code: ErrorCode, context: dict | None = None) -> SelfHealingResult:
        # Pretend healing always succeeds for test determinism
        return SelfHealingResult(
            success=True,
            error_code=error_code,
            applied_fixes=["fake_fixer"],
            attempts=1,
            total_time=0.0,
            message=f"healed {error_code.value}",
        )


class TestSelfHealingCLI(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_status_prints_summary_and_codes(self) -> None:
        fake = _FakeHealingManager()
        # Patch the factory in the CLI module
        import cli_multi_rapid.cli as cli_mod  # type: ignore

        orig = cli_mod.get_self_healing_manager
        try:
            cli_mod.get_self_healing_manager = lambda: fake  # type: ignore
            code, out = self._run(["self-healing", "status"])
        finally:
            cli_mod.get_self_healing_manager = orig  # type: ignore

        self.assertEqual(code, 0)
        self.assertIn("Self-Healing System Status", out)
        self.assertIn("Available Error Codes", out)

    def test_test_invalid_code_is_error(self) -> None:
        code, out = self._run(["self-healing", "test", "not_a_code"])
        self.assertEqual(code, 1)
        self.assertIn("Available codes:", out)

    def test_test_success_uses_manager(self) -> None:
        fake = _FakeHealingManager()
        import cli_multi_rapid.cli as cli_mod  # type: ignore
        orig = cli_mod.get_self_healing_manager
        try:
            cli_mod.get_self_healing_manager = lambda: fake  # type: ignore
            code, out = self._run(["self-healing", "test", "ERR_PATH_NOT_FOUND"])
        finally:
            cli_mod.get_self_healing_manager = orig  # type: ignore

        self.assertEqual(code, 0)
        self.assertIn("Healing Result", out)
        self.assertIn("Success: True", out)

    def test_config_prints_yaml(self) -> None:
        fake = _FakeHealingManager()
        import cli_multi_rapid.cli as cli_mod  # type: ignore
        orig = cli_mod.get_self_healing_manager
        try:
            cli_mod.get_self_healing_manager = lambda: fake  # type: ignore
            code, out = self._run(["self-healing", "config"])
        finally:
            cli_mod.get_self_healing_manager = orig  # type: ignore

        self.assertEqual(code, 0)
        self.assertIn("Self-Healing Configuration", out)
        self.assertIn("Config file:", out)


if __name__ == "__main__":
    unittest.main()

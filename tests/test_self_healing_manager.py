from __future__ import annotations

import os
import tempfile
import time
import types
import unittest
from unittest.mock import patch

from cli_multi_rapid.self_healing_manager import (
    SelfHealingManager,
    ErrorCode,
)


class TestSelfHealingManager(unittest.TestCase):
    def _write_config(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_security_hard_fail_skips_healing(self) -> None:
        cfg = self._write_config(
            """
            self_healing:
              max_attempts: 3
              base_backoff_seconds: 0
              max_backoff_seconds: 0
              security_hard_fail:
                - ERR_SIG_INVALID
            """
        )
        mgr = SelfHealingManager(config_path=cfg)
        res = mgr.attempt_healing(ErrorCode.ERR_SIG_INVALID)
        self.assertFalse(res.success)
        self.assertEqual(res.attempts, 0)
        self.assertIn("Security hard fail", res.message)

    def test_success_path_creates_missing_parent(self) -> None:
        cfg = self._write_config(
            """
            self_healing:
              max_attempts: 1
              base_backoff_seconds: 0
              max_backoff_seconds: 0
            """
        )
        mgr = SelfHealingManager(config_path=cfg)
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "nested", "file.txt")
            with patch.object(time, "sleep", lambda *_: None):
                res = mgr.attempt_healing(ErrorCode.ERR_PATH_NOT_FOUND, {"path": target})
        self.assertTrue(res.success)
        self.assertGreaterEqual(res.attempts, 1)
        self.assertIn("_fix_create_missing_path", 
                      " ".join(res.applied_fixes))

    def test_no_fixers_then_custom_fixer(self) -> None:
        cfg = self._write_config(
            """
            self_healing:
              max_attempts: 1
              base_backoff_seconds: 0
              max_backoff_seconds: 0
            """
        )
        mgr = SelfHealingManager(config_path=cfg)

        # Pick an error code with no built-in fixers
        code = ErrorCode.ERR_AUDIT_WRITE_FAIL
        with patch.object(time, "sleep", lambda *_: None):
            res1 = mgr.attempt_healing(code, {})
        self.assertFalse(res1.success)
        self.assertIn("No fixers", res1.message)

        # Register a custom fixer and try again
        called = {"flag": False}

        def _custom_fix(ctx: dict) -> bool:
            called["flag"] = True
            return True

        mgr.register_custom_fixer(code, _custom_fix)
        with patch.object(time, "sleep", lambda *_: None):
            res2 = mgr.attempt_healing(code, {})
        self.assertTrue(res2.success)
        self.assertTrue(called["flag"])

    def test_backoff_and_multiple_attempts_with_no_success(self) -> None:
        cfg = self._write_config(
            """
            self_healing:
              max_attempts: 2
              base_backoff_seconds: 0
              max_backoff_seconds: 0
            """
        )
        mgr = SelfHealingManager(config_path=cfg)
        # Choose an error with built-in fixers that always return False
        with patch.object(time, "sleep", lambda *_: None):
            res = mgr.attempt_healing(ErrorCode.ERR_PATH_DENIED, {})
        self.assertFalse(res.success)
        self.assertEqual(res.attempts, 2)
        # Both fixers tried on each attempt
        self.assertGreaterEqual(len(res.applied_fixes), 2)


if __name__ == "__main__":
    unittest.main()

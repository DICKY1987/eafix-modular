"""
Unit tests for the ``cli_multi_rapid.cli`` module.

These tests are written using the built-in :mod:`unittest` framework so that
they are compatible with both ``unittest`` and ``pytest`` runners. They cover
the basic functionality of the CLI, including argument parsing and command
dispatch.
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

# Ensure the src package is importable when running the tests directly via
# ``python -m unittest``. When running under pytest this is not strictly
# necessary because ``pytest`` automatically adds the ``src`` directory to the
# import path when using a standard ``src`` layout. We add it here for
# compatibility with the built-in test runner and to avoid import errors.
TEST_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from cli_multi_rapid.cli import CLIArgs, greet, main, parse_args, sum_numbers


class TestGreet(unittest.TestCase):
    def test_greet_returns_expected_string(self) -> None:
        self.assertEqual(greet("Alice"), "Hello, Alice!")
        # Leading/trailing whitespace should be stripped
        self.assertEqual(greet("  Bob  "), "Hello, Bob!")


class TestSumNumbers(unittest.TestCase):
    def test_sum_numbers_returns_sum(self) -> None:
        self.assertEqual(sum_numbers(3, 4), 7)
        self.assertEqual(sum_numbers(-1, 1), 0)


class TestParseArgs(unittest.TestCase):
    def test_parse_args_greet(self) -> None:
        args = parse_args(["greet", "Bob"])
        self.assertEqual(args.command, "greet")
        self.assertEqual(args.name, "Bob")
        self.assertIsNone(args.a)
        self.assertIsNone(args.b)

    def test_parse_args_sum(self) -> None:
        args = parse_args(["sum", "2", "3"])
        self.assertEqual(args.command, "sum")
        self.assertEqual(args.a, 2)
        self.assertEqual(args.b, 3)
        self.assertIsNone(args.name)


class TestMain(unittest.TestCase):
    def _run_main_and_capture(self, argv: list[str]) -> str:
        """Helper to run main with provided ``argv`` and capture stdout."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(argv)
        # Ensure the command succeeded
        self.assertEqual(exit_code, 0)
        return buf.getvalue()

    def test_main_greet_prints_output(self) -> None:
        output = self._run_main_and_capture(["greet", "Charlie"])
        self.assertEqual(output, "Hello, Charlie!\n")

    def test_main_sum_prints_output(self) -> None:
        output = self._run_main_and_capture(["sum", "5", "7"])
        self.assertEqual(output, "12\n")


if __name__ == "__main__":  # pragma: no cover - only executed when run directly
    unittest.main()
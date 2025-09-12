from __future__ import annotations

import unittest
try:
    from hypothesis import given, strategies as st  # type: ignore
    HYP_AVAILABLE = True
except Exception:  # pragma: no cover - environment may lack hypothesis
    HYP_AVAILABLE = False
    def given(*args, **kwargs):  # type: ignore
        def deco(fn):
            return fn
        return deco
    class _Stub:
        def text(self, *a, **k):  # type: ignore
            return None
    st = _Stub()  # type: ignore

# src import path
import os, sys
TEST_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(TEST_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from cli_multi_rapid.cli import greet  # type: ignore


class TestPropertyGreeting(unittest.TestCase):
    @unittest.skipUnless(HYP_AVAILABLE, "hypothesis not installed")
    @given(st.text(min_size=0, max_size=20))
    def test_greet_is_well_formed(self, name: str) -> None:
        out = greet(name)
        self.assertTrue(out.startswith("Hello, "))
        self.assertTrue(out.endswith("!"))


if __name__ == "__main__":
    unittest.main()

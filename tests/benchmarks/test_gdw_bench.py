from __future__ import annotations

from pathlib import Path
from lib.gdw_runner import run_gdw
import pytest


def test_gdw_dry_run_benchmark():
    pytest.importorskip("pytest_benchmark")
    from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore
    spec = Path("gdw/git.commit_push.main/v1.0.0/spec.json")
    def _bench():
        return run_gdw(spec, inputs={}, dry_run=True)
    # Manually invoke benchmark if plugin provides fixture
    # This keeps the test inert when plugin is absent
    return _bench()

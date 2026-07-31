"""Regression coverage for the P10 dashboard indicator relocation."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dashboard_indicator_adapter_targets_canonical_module() -> None:
    adapter = REPO_ROOT / "services/dashboard-backend/src/advanced_indicators.py"
    canonical = (
        REPO_ROOT
        / "m0009-c2-indicator-engine/m0009-src/c2_indicator_engine/advanced_indicators.py"
    )
    retired = (
        REPO_ROOT
        / "services/dashboard-backend/src/2099900104260118_advanced_indicators.py"
    )

    source = adapter.read_text(encoding="utf-8")
    assert "from c2_indicator_engine.advanced_indicators import *" in source
    assert canonical.is_file()
    assert not retired.exists()


def test_dashboard_entrypoint_keeps_adapter_import() -> None:
    entrypoint = REPO_ROOT / "services/dashboard-backend/src/2099900106260118_main.py"
    source = entrypoint.read_text(encoding="utf-8")
    assert "from .advanced_indicators import AdvancedIndicatorEngine" in source

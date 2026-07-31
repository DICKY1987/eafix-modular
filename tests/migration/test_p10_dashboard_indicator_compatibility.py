"""Regression coverage for the P10 dashboard indicator relocation."""

import importlib.util
import shutil
import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dashboard_indicator_adapter_imports_installed_canonical_package(
    tmp_path: Path, monkeypatch,
) -> None:
    adapter = REPO_ROOT / "services/dashboard-backend/src/advanced_indicators.py"
    canonical_package = (
        REPO_ROOT
        / "m0009-c2-indicator-engine/m0009-src/c2_indicator_engine"
    )
    retired = (
        REPO_ROOT
        / "services/dashboard-backend/src/2099900104260118_advanced_indicators.py"
    )

    installed_site = tmp_path / "site-packages"
    shutil.copytree(canonical_package, installed_site / "c2_indicator_engine")

    dashboard_backend = types.ModuleType("dashboard_backend")
    dashboard_backend.BaseIndicator = type("BaseIndicator", (), {})
    dashboard_backend.SignalStrength = type("SignalStrength", (), {})
    dashboard_backend.IndicatorCategory = type("IndicatorCategory", (), {})
    dashboard_backend.SignalData = type("SignalData", (), {})
    monkeypatch.setitem(sys.modules, "dashboard_backend", dashboard_backend)
    monkeypatch.setitem(sys.modules, "numpy", types.ModuleType("numpy"))
    monkeypatch.setitem(sys.modules, "pandas", types.ModuleType("pandas"))
    monkeypatch.syspath_prepend(str(installed_site))

    spec = importlib.util.spec_from_file_location("dashboard_adapter", adapter)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.AdvancedIndicatorEngine.__module__ == (
        "c2_indicator_engine.advanced_indicators"
    )
    assert module.AdvancedIndicatorEngine().get_available_indicators() == [
        "percent_change",
        "currency_strength",
        "adx_trend_strength",
    ]
    assert not retired.exists()


def test_dashboard_entrypoint_keeps_adapter_import() -> None:
    entrypoint = REPO_ROOT / "services/dashboard-backend/src/2099900106260118_main.py"
    source = entrypoint.read_text(encoding="utf-8")
    assert "from .advanced_indicators import AdvancedIndicatorEngine" in source

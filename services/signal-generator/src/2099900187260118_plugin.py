# doc_id: DOC-SERVICE-0185
"""
Signal Generator Plugin - Evaluates calendar signals and indicator vectors,
emits Signal@1.0 or SignalSuppressed to eafix.signals.generated.

Closes GAP-06.
"""
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict

_src = Path(__file__).parent
sys.path.insert(0, str(_src.parent.parent.parent / "shared"))


def _load_module(fname: str, mname: str):
    spec = importlib.util.spec_from_file_location(mname, _src / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_config_mod = _load_module("2099900185260118_config.py", "sg_config")
_proc_mod = _load_module("2099900186260118_processor.py", "sg_processor")
Settings = _config_mod.Settings
SignalProcessor = _proc_mod.SignalProcessor

from shared.plugin_interface import BasePlugin, PluginMetadata


class SignalGeneratorPlugin(BasePlugin):
    """
    Evaluates feature frames from calendar + indicators, emits Signals.

    Subscribes to: eafix.calendar.signals, eafix.indicators.computed, eafix.system.risk_off
    Emits: eafix.signals.generated (Signal@1.0 | SignalSuppressed)
    """

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="signal-generator",
            version="1.0.0",
            description="Calendar + indicator signal evaluation",
            author="EAFIX Team",
            dependencies=[],
        )
        super().__init__(metadata)
        self._processor: SignalProcessor = None

    async def _on_initialize(self) -> None:
        settings = Settings()
        self._processor = SignalProcessor(settings)

        if self._context:
            self._context.subscribe("eafix.calendar.signals", self._handle_calendar_signal)
            self._context.subscribe("eafix.indicators.computed", self._handle_indicator_vector)
            self._context.subscribe("eafix.system.risk_off", self._handle_risk_off)

    async def _on_start(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    def _handle_calendar_signal(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Update cache and try to evaluate signal."""
        self._processor.on_calendar_signal(data)
        symbol = data.get("symbol")
        if symbol:
            self._try_emit(symbol)

    def _handle_indicator_vector(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Update cache and try to evaluate signal."""
        self._processor.on_indicator_vector(data)
        symbol = data.get("symbol")
        if symbol:
            self._try_emit(symbol)

    def _handle_risk_off(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Propagate risk-off to processor."""
        self._processor.on_risk_off(data)

    def _try_emit(self, symbol: str) -> None:
        """Evaluate signal for symbol and emit if result produced."""
        if not self._processor:
            return
        result = self._processor.evaluate(symbol)
        if result:
            self.emit_event("eafix.signals.generated", result)

    async def health_check(self) -> Dict[str, Any]:
        base = await super().health_check()
        if self._processor:
            base.update({
                "risk_off": self._processor._risk_off,
                "calendar_cache_symbols": list(self._processor._calendar_cache.keys()),
                "indicator_cache_symbols": list(self._processor._indicator_cache.keys()),
            })
        return base


plugin_class = SignalGeneratorPlugin

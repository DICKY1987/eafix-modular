# doc_id: DOC-SERVICE-0206
"""
Risk Manager Plugin - Position sizing and risk checks.
Closes GAP-09, GAP-11.
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


_config_mod = _load_module("2099900184260118_config.py", "rm_config")
_proc_mod = _load_module("2099900185260118_processor.py", "rm_processor")
Settings = _config_mod.Settings
RiskProcessor = _proc_mod.RiskProcessor

from shared.plugin_interface import BasePlugin, PluginMetadata


class RiskManagerPlugin(BasePlugin):
    """
    Validates signals against risk parameters.

    Subscribes to: eafix.signals.generated
    Emits: eafix.orders.validated (OrderIntent@1.2) or eafix.risk.rejected (RiskRejected)
    """

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="risk-manager",
            version="1.0.0",
            description="Position sizing and risk management",
            author="EAFIX Team",
            dependencies=["signal-generator"],
        )
        super().__init__(metadata)
        self._processor: RiskProcessor = None

    async def _on_initialize(self) -> None:
        settings = Settings()
        self._processor = RiskProcessor(settings)

        if self._context:
            self._context.subscribe("eafix.signals.generated", self._handle_signal)

    async def _on_start(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    def _handle_signal(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Route Signal -> RiskProcessor -> emit OrderIntent or RiskRejected."""
        if data.get("event_type") == "SignalSuppressed":
            return
        result = self._processor.process_signal(data)
        if result["event_type"] == "OrderIntent":
            self.emit_event("eafix.orders.validated", result)
        else:
            self.emit_event("eafix.risk.rejected", result)

    async def health_check(self) -> Dict[str, Any]:
        base_health = await super().health_check()
        if self._processor:
            base_health.update({
                "daily_loss": self._processor._cumulative_loss_today,
                "risk_ok": True,
            })
        return base_health


plugin_class = RiskManagerPlugin

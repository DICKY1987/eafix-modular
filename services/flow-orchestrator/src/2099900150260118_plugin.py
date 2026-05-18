# doc_id: DOC-SERVICE-0219
"""
Flow Orchestrator Plugin — wires FlowCoordinator into the plugin lifecycle.
Closes GAP-38, GAP-39, GAP-40, GAP-44, GAP-45, GAP-51.
"""
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict

_src = Path(__file__).parent
sys.path.insert(0, str(_src.parent.parent.parent / "shared"))


def _load(fname: str, mname: str):
    spec = importlib.util.spec_from_file_location(mname, _src / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cfg_mod = _load("2099900148260118_config.py", "fo_config")
_coord_mod = _load("2099900149260118_coordinator.py", "fo_coordinator")
Settings = _cfg_mod.Settings
FlowCoordinator = _coord_mod.FlowCoordinator

from shared.plugin_interface import BasePlugin, PluginMetadata


class FlowOrchestratorPlugin(BasePlugin):
    """
    Orchestrates the reentry loop with velocity limiting and idempotency.
    """

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="flow-orchestrator",
            version="1.0.0",
            description="Reentry loop orchestration with velocity and idempotency controls",
            author="EAFIX Team",
            dependencies=["signal-generator", "reentry-engine"],
        )
        super().__init__(metadata)
        self._coordinator: FlowCoordinator = None

    async def _on_initialize(self) -> None:
        settings = Settings()
        self._coordinator = FlowCoordinator(
            settings=settings,
            emit_fn=self.emit_event,
        )

        if self._context:
            self._context.subscribe("eafix.reentry.decisions", self._handle_decision)
            self._context.subscribe("eafix.system.risk_off", self._handle_risk_off)

    async def _on_start(self) -> None:
        pass

    async def _on_stop(self) -> None:
        pass

    def _handle_decision(self, event_type: str, data: Dict[str, Any],
                          source: str) -> None:
        import asyncio
        asyncio.create_task(self._coordinator.handle_reentry_decision(data))

    def _handle_risk_off(self, event_type: str, data: Dict[str, Any],
                          source: str) -> None:
        self._coordinator.on_risk_off(data)

    async def health_check(self) -> Dict[str, Any]:
        base = await super().health_check()
        if self._coordinator:
            base.update({
                "risk_off": self._coordinator._risk_off,
                "velocity_counts": dict(self._coordinator._velocity_counts),
            })
        return base


plugin_class = FlowOrchestratorPlugin

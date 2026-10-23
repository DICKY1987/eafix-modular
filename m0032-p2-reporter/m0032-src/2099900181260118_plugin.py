# doc_id: DOC-SERVICE-0208
"""
Reporter Plugin - Metrics and P&L reporting
"""

from typing import Any, Dict, Optional
import asyncio
from datetime import datetime, timezone

from shared.plugin_interface import BasePlugin, PluginMetadata


class ReporterPlugin(BasePlugin):
    """
    Collects and reports trading metrics.

    Subscribes to: order_executed, trade_result events
    Emits: report_generated events
    """

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="reporter",
            version="1.0.0",
            description="Metrics and P&L reporting",
            author="EAFIX Team",
            dependencies=["execution-engine"],
        )
        super().__init__(metadata)
        self._report_interval_min = 15
        self._metrics: Dict[str, Any] = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
        }
        self._report_task: Optional[asyncio.Task] = None

    async def _on_initialize(self) -> None:
        """Initialize reporter."""
        self._report_interval_min = int(self.get_config("report_interval_min", 15))

        if self._context:
            self._context.subscribe("order_executed", self._handle_order_executed)
            self._context.subscribe("trade_result", self._handle_trade_result)

    async def _on_start(self) -> None:
        """Start reporting."""
        self._report_task = asyncio.create_task(self._reporting_loop())

    async def _on_stop(self) -> None:
        """Stop reporting."""
        if self._report_task:
            self._report_task.cancel()
            try:
                await self._report_task
            except asyncio.CancelledError:
                pass

    def _handle_order_executed(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Track executed orders."""
        self._metrics["total_trades"] += 1

    def _handle_trade_result(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Track trade results."""
        pnl = float(data.get("pnl", 0.0))
        self._metrics["total_pnl"] += pnl

        if pnl > 0:
            self._metrics["winning_trades"] += 1
        elif pnl < 0:
            self._metrics["losing_trades"] += 1

    async def _reporting_loop(self) -> None:
        """Generate reports periodically."""
        while True:
            try:
                await asyncio.sleep(self._report_interval_min * 60)
                report = self._generate_report()
                self.emit_event("report_generated", report)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                print(f"Reporting error: {exc}")
                await asyncio.sleep(60)

    def _generate_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        total_trades = self._metrics["total_trades"]
        win_rate = (self._metrics["winning_trades"] / total_trades * 100) if total_trades else 0.0
        average_pnl = (self._metrics["total_pnl"] / total_trades) if total_trades else 0.0

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self._metrics.copy(),
            "win_rate": win_rate,
            "average_pnl": average_pnl,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check."""
        base_health = await super().health_check()
        base_health.update(
            {
                "metrics": self._metrics.copy(),
                "reporting_active": self._report_task is not None and not self._report_task.done(),
            }
        )
        return base_health


plugin_class = ReporterPlugin

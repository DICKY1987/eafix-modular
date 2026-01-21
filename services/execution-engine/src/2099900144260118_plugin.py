# doc_id: DOC-SERVICE-0207
"""
Execution Engine Plugin - Order execution to broker
"""

from typing import Any, Dict, Optional
import asyncio
from datetime import datetime, timezone

from shared.plugin_interface import BasePlugin, PluginMetadata


class ExecutionEnginePlugin(BasePlugin):
    """
    Executes approved orders to broker.

    Subscribes to: order_approved events
    Emits: order_executed events
    """

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="execution-engine",
            version="1.0.0",
            description="Order execution to MT4 broker",
            author="EAFIX Team",
            dependencies=["risk-manager"],
        )
        super().__init__(metadata)
        self._broker_api: Optional[str] = None
        self._order_timeout_sec = 30
        self._execution_count = 0
        self._failed_count = 0

    async def _on_initialize(self) -> None:
        """Initialize execution engine."""
        self._broker_api = self.get_config("broker_api", "mt4")
        self._order_timeout_sec = int(self.get_config("order_timeout_sec", 30))

        if self._context:
            self._context.subscribe("order_approved", self._handle_order_approved)

    async def _on_start(self) -> None:
        """Start execution engine."""
        return None

    async def _on_stop(self) -> None:
        """Stop execution engine."""
        return None

    def _handle_order_approved(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Execute approved order asynchronously."""
        asyncio.create_task(self._execute_order(data))

    async def _execute_order(self, order: Dict[str, Any]) -> None:
        """Execute order to broker (stub implementation)."""
        try:
            await asyncio.sleep(0.1)
            self._execution_count += 1

            execution_price = float(order.get("price") or order.get("expected_price") or 1.2345)
            result = {
                **order,
                "order_id": f"ORD-{self._execution_count:06d}",
                "executed_price": execution_price,
                "execution_time": datetime.now(timezone.utc).isoformat(),
                "status": "filled",
            }

            self.emit_event("order_executed", result)
        except Exception as exc:
            self._failed_count += 1
            self.emit_event(
                "order_rejected",
                {
                    **order,
                    "error": str(exc),
                    "status": "failed",
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                },
            )

    async def health_check(self) -> Dict[str, Any]:
        """Health check."""
        base_health = await super().health_check()
        base_health.update(
            {
                "broker_api": self._broker_api,
                "broker_connected": True,
                "executions": self._execution_count,
                "failures": self._failed_count,
            }
        )
        return base_health


plugin_class = ExecutionEnginePlugin

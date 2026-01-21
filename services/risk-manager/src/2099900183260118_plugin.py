# doc_id: DOC-SERVICE-0206
"""
Risk Manager Plugin - Position sizing and risk checks
"""

from typing import Any, Dict

from shared.plugin_interface import BasePlugin, PluginMetadata


class RiskManagerPlugin(BasePlugin):
    """
    Validates signals against risk parameters.

    Subscribes to: signal_generated events
    Emits: order_approved or order_rejected events
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
        self._max_position_size = 1.0
        self._max_drawdown_pct = 5.0
        self._daily_loss_limit = 1000.0
        self._current_drawdown = 0.0
        self._daily_loss = 0.0
        self._approved = 0
        self._rejected = 0

    async def _on_initialize(self) -> None:
        """Initialize risk manager."""
        self._max_position_size = float(self.get_config("max_position_size", 1.0))
        self._max_drawdown_pct = float(self.get_config("max_drawdown_pct", 5.0))
        self._daily_loss_limit = float(self.get_config("daily_loss_limit", 1000.0))

        if self._context:
            self._context.subscribe("signal_generated", self._handle_signal)

    async def _on_start(self) -> None:
        """Start risk management."""
        return None

    async def _on_stop(self) -> None:
        """Stop risk management."""
        return None

    def _handle_signal(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Validate signal against risk parameters."""
        if self._check_risk_limits(data):
            position_size = self._calculate_position_size(data)
            self._approved += 1
            self.emit_event(
                "order_approved",
                {
                    **data,
                    "position_size": position_size,
                    "approved_by": "risk-manager",
                },
            )
        else:
            self._rejected += 1
            self.emit_event(
                "order_rejected",
                {
                    **data,
                    "reason": "Risk limits exceeded",
                    "rejected_by": "risk-manager",
                },
            )

    def _check_risk_limits(self, signal: Dict[str, Any]) -> bool:
        """Check if signal passes risk limits."""
        if self._daily_loss >= self._daily_loss_limit:
            return False
        if self._current_drawdown >= self._max_drawdown_pct:
            return False
        return True

    def _calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """Calculate position size based on confidence and risk."""
        confidence = float(signal.get("confidence", 0.5))
        confidence = max(0.0, min(confidence, 1.0))
        return self._max_position_size * confidence

    async def health_check(self) -> Dict[str, Any]:
        """Health check."""
        base_health = await super().health_check()
        base_health.update(
            {
                "daily_loss": self._daily_loss,
                "current_drawdown": self._current_drawdown,
                "risk_ok": self._daily_loss < self._daily_loss_limit,
                "approved": self._approved,
                "rejected": self._rejected,
            }
        )
        return base_health


plugin_class = RiskManagerPlugin

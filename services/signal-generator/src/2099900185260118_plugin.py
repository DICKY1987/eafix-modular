# doc_id: DOC-SERVICE-0205
"""
Signal Generator Plugin - Trading signal generation
Analyzes indicators and generates trading signals
"""

from typing import Any, Dict, Optional

from shared.plugin_interface import BasePlugin, PluginMetadata


class SignalGeneratorPlugin(BasePlugin):
    """
    Generates trading signals from technical indicators.

    Subscribes to: indicator_update events
    Emits: signal_generated events
    """

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="signal-generator",
            version="1.0.0",
            description="Trading signal generation from indicators",
            author="EAFIX Team",
            dependencies=["indicator-engine"],
        )
        super().__init__(metadata)
        self._strategy = "trend_following"
        self._thresholds: Dict[str, float] = {}
        self._signals_generated = 0

    async def _on_initialize(self) -> None:
        """Initialize signal generator."""
        self._strategy = self.get_config("strategy", "trend_following")
        self._thresholds = self.get_config(
            "thresholds",
            {"rsi_overbought": 70.0, "rsi_oversold": 30.0},
        )

        if self._context:
            self._context.subscribe("indicator_update", self._handle_indicator_update)

    async def _on_start(self) -> None:
        """Start signal generation."""
        return None

    async def _on_stop(self) -> None:
        """Stop signal generation."""
        return None

    def _handle_indicator_update(
        self, event_type: str, data: Dict[str, Any], source: str
    ) -> None:
        """Handle indicator updates and generate signals."""
        signal = self._generate_signal(data)
        if signal:
            self._signals_generated += 1
            self.emit_event("signal_generated", signal)

    def _generate_signal(self, indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal from indicators."""
        rsi = float(indicators.get("rsi_14", 50))
        ema_20 = float(indicators.get("ema_20", 0))
        ema_50 = float(indicators.get("ema_50", 0))

        if rsi < self._thresholds.get("rsi_oversold", 30) and ema_20 > ema_50:
            return {
                "symbol": indicators.get("symbol", "EURUSD"),
                "action": "BUY",
                "confidence": 0.75,
                "reason": "RSI oversold + EMA bullish crossover",
                "timestamp": indicators.get("timestamp"),
            }
        if rsi > self._thresholds.get("rsi_overbought", 70) and ema_20 < ema_50:
            return {
                "symbol": indicators.get("symbol", "EURUSD"),
                "action": "SELL",
                "confidence": 0.75,
                "reason": "RSI overbought + EMA bearish crossover",
                "timestamp": indicators.get("timestamp"),
            }

        return None

    async def health_check(self) -> Dict[str, Any]:
        """Health check."""
        base_health = await super().health_check()
        base_health.update(
            {
                "strategy": self._strategy,
                "signals_generated": self._signals_generated,
            }
        )
        return base_health


plugin_class = SignalGeneratorPlugin

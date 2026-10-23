# doc_id: DOC-SERVICE-0204
"""
Indicator Engine Plugin - Technical indicator calculations
Migrated from Docker microservice to plugin architecture
"""

from typing import Any, Dict, List, Optional
import asyncio

from shared.plugin_interface import BasePlugin, PluginMetadata


class IndicatorEnginePlugin(BasePlugin):
    """
    Calculates technical indicators from price data.

    Subscribes to: price_tick events
    Emits: indicator_update events
    """

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="indicator-engine",
            version="1.0.0",
            description="Technical indicator calculations (EMA, RSI, MACD, Bollinger)",
            author="EAFIX Team",
            dependencies=["data-ingestor"],
        )
        super().__init__(metadata)
        self._indicators_enabled: List[str] = []
        self._price_buffer: List[Dict[str, Any]] = []
        self._calculation_task: Optional[asyncio.Task] = None
        self._update_interval_sec = 0.5
        self._min_points = 50

    async def _on_initialize(self) -> None:
        """Initialize indicators and subscriptions."""
        update_interval_ms = self.get_config("update_interval_ms", 500)
        self._indicators_enabled = list(
            self.get_config("indicators", ["ema", "rsi", "macd", "bollinger"])
        )
        self._update_interval_sec = update_interval_ms / 1000.0

        if self._context:
            self._context.subscribe("price_tick", self._handle_price_tick)

    async def _on_start(self) -> None:
        """Start indicator calculations."""
        self._calculation_task = asyncio.create_task(self._calculation_loop())

    async def _on_stop(self) -> None:
        """Stop calculations."""
        if self._calculation_task:
            self._calculation_task.cancel()
            try:
                await self._calculation_task
            except asyncio.CancelledError:
                pass

    def _handle_price_tick(self, event_type: str, data: Dict[str, Any], source: str) -> None:
        """Handle incoming price ticks."""
        self._price_buffer.append(data)

        if len(self._price_buffer) > 1000:
            self._price_buffer = self._price_buffer[-1000:]

    async def _calculation_loop(self) -> None:
        """Main calculation loop."""
        while True:
            try:
                if len(self._price_buffer) >= self._min_points:
                    indicators = await self._calculate_indicators()
                    if indicators:
                        self.emit_event("indicator_update", indicators)

                await asyncio.sleep(self._update_interval_sec)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                print(f"Indicator calculation error: {exc}")
                await asyncio.sleep(1)

    async def _calculate_indicators(self) -> Dict[str, Any]:
        """Calculate enabled indicators (stub implementation)."""
        latest_price = self._price_buffer[-1]
        base_price = (
            latest_price.get("bid")
            or latest_price.get("price")
            or latest_price.get("close")
            or 0.0
        )
        base_price = float(base_price) if base_price else 1.0

        return {
            "symbol": latest_price.get("symbol", "EURUSD"),
            "timestamp": latest_price.get("timestamp"),
            "ema_20": round(base_price * 0.9995, 5),
            "ema_50": round(base_price * 0.9990, 5),
            "rsi_14": 55.0,
            "macd": {
                "value": round(base_price * 0.0004, 6),
                "signal": round(base_price * 0.0003, 6),
                "histogram": round(base_price * 0.0001, 6),
            },
            "bollinger": {
                "upper": round(base_price * 1.0010, 5),
                "middle": round(base_price, 5),
                "lower": round(base_price * 0.9990, 5),
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check."""
        base_health = await super().health_check()
        base_health.update(
            {
                "price_buffer_size": len(self._price_buffer),
                "indicators_enabled": len(self._indicators_enabled),
            }
        )
        return base_health


plugin_class = IndicatorEnginePlugin

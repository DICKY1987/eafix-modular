# doc_id: DOC-SERVICE-0179
# DOC_ID: DOC-ARCH-0110
"""
Telemetry Daemon Plugin
Collects and exports metrics and telemetry data
"""

from typing import Dict, Any, Optional
import asyncio
import time
import structlog
from prometheus_client import Counter, Histogram, Gauge

from shared.plugin_interface import BasePlugin, PluginMetadata


logger = structlog.get_logger(__name__)


class TelemetryDaemonPlugin(BasePlugin):
    """Telemetry collection and export daemon"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="telemetry-daemon",
            version="1.0.0",
            description="Metrics collection and telemetry export",
            author="EAFIX Team",
            dependencies=[],
        )
        super().__init__(metadata)
        self._task: Optional[asyncio.Task] = None
        self._metrics: Optional[Dict[str, Any]] = None
    
    async def _on_initialize(self) -> None:
        """Initialize the telemetry daemon"""
        if self._metrics is None:
            self._metrics = {
                "events": Counter(
                    "eafix_events_total",
                    "Total events processed",
                    ["event_type", "source"],
                ),
                "event_latency": Histogram(
                    "eafix_event_latency_seconds",
                    "Event processing latency",
                ),
                "plugin_health": Gauge(
                    "eafix_plugin_health",
                    "Plugin health status",
                    ["plugin"],
                ),
            }

        # Subscribe to all events for metrics
        event_types = [
            "price_tick", "indicator_update", "signal_generated",
            "order_approved", "order_rejected", "order_executed",
            "trade_result", "reentry_decision", "calendar_update",
            "validation_failed"
        ]
        
        for event_type in event_types:
            self._context.subscribe(event_type, self._track_event)
        
        logger.info("Telemetry daemon initialized")
    
    async def _on_start(self) -> None:
        """Start the telemetry daemon"""
        logger.info("Starting telemetry daemon")
        self._task = asyncio.create_task(self._collect_metrics())
    
    async def _on_stop(self) -> None:
        """Stop the telemetry daemon"""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Telemetry daemon stopped")
    
    def _track_event(self, event_type: str, data: Any, source: str) -> None:
        """Track event metrics"""
        if self._metrics:
            self._metrics["events"].labels(event_type=event_type, source=source).inc()
    
    async def _collect_metrics(self) -> None:
        """Periodic metrics collection"""
        while True:
            try:
                # Collect plugin health metrics
                all_plugins = self._context.get_all_plugins()
                
                for name, plugin in all_plugins.items():
                    try:
                        health = await plugin.health_check()
                        status_value = 1.0 if health.get("status") == "healthy" else 0.0
                        if self._metrics:
                            self._metrics["plugin_health"].labels(plugin=name).set(status_value)
                    except Exception as e:
                        logger.warning(f"Failed to collect metrics for {name}: {e}")
                        if self._metrics:
                            self._metrics["plugin_health"].labels(plugin=name).set(0.0)
                
                # Wait before next collection
                await asyncio.sleep(15)  # Collect every 15 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(15)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["collecting"] = self._task is not None and not self._task.done()
        return health


plugin_class = TelemetryDaemonPlugin

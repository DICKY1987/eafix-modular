# doc_id: DOC-SERVICE-0209
"""
Transport Router Plugin
Routes CSV files between services with integrity validation.
"""

from typing import Any, Dict, Optional
import structlog

from shared.plugin_interface import BasePlugin, PluginMetadata
from .config import Settings
from .metrics import MetricsCollector
from .health import HealthChecker
from .main import TransportRouterService


logger = structlog.get_logger(__name__)


class TransportRouterPlugin(BasePlugin):
    """Transport router as a plugin."""

    def __init__(self) -> None:
        metadata = PluginMetadata(
            name="transport-router",
            version="1.0.0",
            description="CSV file routing with integrity validation",
            author="EAFIX Team",
            dependencies=[],
        )
        super().__init__(metadata)
        self._service: Optional[TransportRouterService] = None
        self._health_checker: Optional[HealthChecker] = None
        self._metrics: Optional[MetricsCollector] = None

    async def _on_initialize(self) -> None:
        """Initialize transport router service."""
        settings = Settings(
            service_port=self.get_config("service_port", 8090),
            redis_url=self.get_config("redis_url", "redis://localhost:6379"),
        )
        self._metrics = MetricsCollector()
        self._health_checker = HealthChecker(settings, self._metrics)
        self._service = TransportRouterService(settings, self._metrics, self._health_checker)

        logger.info("Transport router initialized")

    async def _on_start(self) -> None:
        """Start transport router service."""
        if not self._service:
            raise RuntimeError("Transport router not initialized")
        await self._service.start()

    async def _on_stop(self) -> None:
        """Stop transport router service."""
        if self._service:
            await self._service.stop()

    async def health_check(self) -> Dict[str, Any]:
        """Health check."""
        health = await super().health_check()
        if self._health_checker:
            health["details"] = await self._health_checker.get_health_status()
        return health


plugin_class = TransportRouterPlugin

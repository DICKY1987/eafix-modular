# doc_id: DOC-SERVICE-0168
# DOC_ID: DOC-ARCH-0105
"""
Reentry Matrix Service Plugin
Provides reentry decision resolution
"""

from typing import Dict, Any, Optional
import structlog

from shared.plugin_interface import BasePlugin, PluginMetadata
from .processor import ReentryProcessor
from .resolver import TieredParameterResolver
from .metrics import MetricsCollector
from .config import Settings


logger = structlog.get_logger(__name__)


class ReentryMatrixPlugin(BasePlugin):
    """Reentry matrix decision service as a plugin"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="reentry-matrix-svc",
            version="1.0.0",
            description="Re-entry decision matrix and resolution",
            author="EAFIX Team",
            dependencies=[],
        )
        super().__init__(metadata)
        self._processor: Optional[ReentryProcessor] = None
        self._resolver: Optional[TieredParameterResolver] = None
        self._metrics: Optional[MetricsCollector] = None
    
    async def _on_initialize(self) -> None:
        """Initialize the reentry matrix service"""
        settings = Settings(
            reentry_window_hours=self.get_config("reentry_window_hours", 4)
        )
        
        self._metrics = MetricsCollector()
        self._resolver = TieredParameterResolver(settings)
        await self._resolver.load_parameter_sets()
        self._processor = ReentryProcessor(settings, self._metrics)
        
        logger.info("Reentry matrix service initialized")
    
    async def _on_start(self) -> None:
        """Start the service"""
        logger.info("Starting reentry matrix service")
    
    async def _on_stop(self) -> None:
        """Stop the service"""
        logger.info("Stopping reentry matrix service")
    
    async def get_decision(self, symbol: str, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get reentry decision parameters for a trade."""
        if not self._resolver:
            raise RuntimeError("Resolver not initialized")
        
        outcome_class = trade_data.get("outcome_class", "BREAKEVEN")
        duration_class = trade_data.get("duration_class", "QUICK")
        proximity_state = trade_data.get("proximity_state", "NONE")
        calendar_id = trade_data.get("calendar_id", "NONE")
        generation = int(trade_data.get("generation", 1))

        return await self._resolver.resolve_parameters(
            outcome_class,
            duration_class,
            proximity_state,
            calendar_id,
            symbol,
            generation,
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["resolver_ready"] = self._resolver is not None
        health["processor_ready"] = self._processor is not None
        return health


plugin_class = ReentryMatrixPlugin

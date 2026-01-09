# DOC_ID: DOC-ARCH-0105
"""
Reentry Matrix Service Plugin
Provides reentry decision resolution
"""

from typing import Dict, Any, Optional
import structlog

from shared.plugin_interface import BasePlugin, PluginMetadata
from .processor import ReentryMatrixProcessor
from .resolver import DecisionResolver
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
        self._processor: Optional[ReentryMatrixProcessor] = None
        self._resolver: Optional[DecisionResolver] = None
    
    async def _on_initialize(self) -> None:
        """Initialize the reentry matrix service"""
        settings = Settings(
            reentry_window_hours=self.get_config("reentry_window_hours", 4)
        )
        
        self._processor = ReentryMatrixProcessor(settings)
        self._resolver = DecisionResolver(settings)
        
        logger.info("Reentry matrix service initialized")
    
    async def _on_start(self) -> None:
        """Start the service"""
        logger.info("Starting reentry matrix service")
    
    async def _on_stop(self) -> None:
        """Stop the service"""
        logger.info("Stopping reentry matrix service")
    
    def get_decision(self, symbol: str, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get reentry decision for a trade"""
        if not self._resolver:
            raise RuntimeError("Resolver not initialized")
        
        return self._resolver.resolve_decision(symbol, trade_data)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["resolver_ready"] = self._resolver is not None
        return health


plugin_class = ReentryMatrixPlugin

# DOC_ID: DOC-ARCH-0104
"""
Reentry Engine Plugin
Processes TradeResult events and generates ReentryDecision events
"""

from typing import Dict, Any, Optional
import asyncio
import structlog

from shared.plugin_interface import BasePlugin, PluginMetadata
from .processor import TradeResultProcessor
from .decision_client import ReentryMatrixClient
from .config import Settings
from .metrics import MetricsCollector
from .health import HealthChecker


logger = structlog.get_logger(__name__)


class ReentryEnginePlugin(BasePlugin):
    """Re-entry engine as a plugin"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="reentry-engine",
            version="1.0.0",
            description="Central re-entry processing engine",
            author="EAFIX Team",
            dependencies=["reentry-matrix-svc"],
        )
        super().__init__(metadata)
        self._processor: Optional[TradeResultProcessor] = None
        self._matrix_client: Optional[ReentryMatrixClient] = None
        self._task: Optional[asyncio.Task] = None
    
    async def _on_initialize(self) -> None:
        """Initialize the reentry engine"""
        settings = Settings()
        
        # Get reentry-matrix plugin
        matrix_plugin = self.get_plugin("reentry-matrix-svc")
        if not matrix_plugin:
            raise RuntimeError("reentry-matrix-svc plugin not found")
        
        # Create components
        metrics = MetricsCollector()
        health_checker = HealthChecker()
        
        self._processor = TradeResultProcessor(settings)
        
        # Subscribe to trade result events
        self._context.subscribe("trade_result", self._handle_trade_result)
        
        logger.info("Reentry engine initialized")
    
    async def _on_start(self) -> None:
        """Start the reentry engine"""
        logger.info("Starting reentry engine")
    
    async def _on_stop(self) -> None:
        """Stop the reentry engine"""
        logger.info("Stopping reentry engine")
    
    def _handle_trade_result(self, event_type: str, data: Any, source: str) -> None:
        """Handle trade result event"""
        try:
            # Get matrix plugin for decision
            matrix_plugin = self.get_plugin("reentry-matrix-svc")
            
            # Process trade result
            decision = self._processor.process_trade_result(data)
            
            if decision:
                # Emit reentry decision event
                self.emit_event("reentry_decision", {
                    "symbol": data.get("symbol"),
                    "decision": decision,
                    "timestamp": data.get("timestamp")
                })
                
                logger.info(
                    "Reentry decision generated",
                    symbol=data.get("symbol"),
                    decision=decision
                )
        except Exception as e:
            logger.error(f"Error processing trade result: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["processor_ready"] = self._processor is not None
        return health


plugin_class = ReentryEnginePlugin

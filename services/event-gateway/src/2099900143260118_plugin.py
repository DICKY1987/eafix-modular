# doc_id: DOC-SERVICE-0141
# DOC_ID: DOC-ARCH-0108
"""
Event Gateway Plugin
Routes events between plugins and external systems
"""

from typing import Dict, Any, Optional, Set
import asyncio
import structlog

from shared.plugin_interface import BasePlugin, PluginMetadata


logger = structlog.get_logger(__name__)


class EventGatewayPlugin(BasePlugin):
    """Event gateway for routing and transforming events"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="event-gateway",
            version="1.0.0",
            description="Event routing and transformation gateway",
            author="EAFIX Team",
            dependencies=[],
        )
        super().__init__(metadata)
        self._event_stats: Dict[str, int] = {}
        self._subscribers: Set[str] = set()
    
    async def _on_initialize(self) -> None:
        """Initialize the event gateway"""
        # Subscribe to all events for routing/logging
        event_types = [
            "price_tick",
            "indicator_update",
            "signal_generated",
            "order_approved",
            "order_rejected",
            "order_executed",
            "trade_result",
            "reentry_decision",
            "calendar_update"
        ]
        
        for event_type in event_types:
            self._context.subscribe(event_type, self._handle_event)
            self._event_stats[event_type] = 0
        
        logger.info("Event gateway initialized")
    
    async def _on_start(self) -> None:
        """Start the event gateway"""
        logger.info("Starting event gateway")
    
    async def _on_stop(self) -> None:
        """Stop the event gateway"""
        logger.info("Stopping event gateway", event_stats=self._event_stats)
    
    def _handle_event(self, event_type: str, data: Any, source: str) -> None:
        """Handle and route events"""
        self._event_stats[event_type] = self._event_stats.get(event_type, 0) + 1
        
        # Log event for monitoring
        logger.debug(
            "Event routed",
            event_type=event_type,
            source=source,
            data_size=len(str(data)) if data else 0
        )
        
        # Could add event transformation, filtering, or external routing here
    
    def get_stats(self) -> Dict[str, int]:
        """Get event statistics"""
        return self._event_stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["total_events"] = sum(self._event_stats.values())
        health["event_types"] = len(self._event_stats)
        return health


plugin_class = EventGatewayPlugin

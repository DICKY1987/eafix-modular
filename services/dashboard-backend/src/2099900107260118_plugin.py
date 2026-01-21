# doc_id: DOC-SERVICE-0145
# DOC_ID: DOC-ARCH-0112
"""
Dashboard Backend Plugin
Provides data aggregation and APIs for dashboard UI
"""

from typing import Dict, Any, Optional, List
import asyncio
import structlog
from datetime import datetime, timedelta

from shared.plugin_interface import BasePlugin, PluginMetadata


logger = structlog.get_logger(__name__)


class DashboardBackendPlugin(BasePlugin):
    """Dashboard backend for UI data aggregation"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="dashboard-backend",
            version="1.0.0",
            description="Dashboard data aggregation and API backend",
            author="EAFIX Team",
            dependencies=["event-gateway", "telemetry-daemon"],
        )
        super().__init__(metadata)
        self._recent_events: List[Dict[str, Any]] = []
        self._max_events = 1000
        self._stats = {
            "trades": 0,
            "signals": 0,
            "orders": 0
        }
    
    async def _on_initialize(self) -> None:
        """Initialize the dashboard backend"""
        # Subscribe to events for dashboard display
        self._context.subscribe("signal_generated", self._track_event)
        self._context.subscribe("order_executed", self._track_event)
        self._context.subscribe("trade_result", self._track_event)
        
        logger.info("Dashboard backend initialized")
    
    async def _on_start(self) -> None:
        """Start the dashboard backend"""
        logger.info("Starting dashboard backend")
    
    async def _on_stop(self) -> None:
        """Stop the dashboard backend"""
        logger.info("Stopping dashboard backend")
    
    def _track_event(self, event_type: str, data: Any, source: str) -> None:
        """Track event for dashboard display"""
        # Add to recent events
        event_record = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "data": data
        }
        
        self._recent_events.append(event_record)
        
        # Keep only recent events
        if len(self._recent_events) > self._max_events:
            self._recent_events = self._recent_events[-self._max_events:]
        
        # Update stats
        if event_type == "signal_generated":
            self._stats["signals"] += 1
        elif event_type == "order_executed":
            self._stats["orders"] += 1
        elif event_type == "trade_result":
            self._stats["trades"] += 1
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events"""
        return self._recent_events[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        return {
            "stats": self._stats,
            "recent_events_count": len(self._recent_events),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get complete system overview for dashboard"""
        # Get all plugin statuses
        all_plugins = self._context.get_all_plugins()
        plugin_statuses = {}
        
        for name, plugin in all_plugins.items():
            try:
                health = await plugin.health_check()
                plugin_statuses[name] = {
                    "state": plugin.state.value,
                    "health": health.get("status"),
                    "details": health
                }
            except Exception as e:
                plugin_statuses[name] = {
                    "state": "error",
                    "error": str(e)
                }
        
        # Get flow orchestrator status
        flow_plugin = self.get_plugin("flow-orchestrator")
        flow_status = {}
        if flow_plugin and hasattr(flow_plugin, "get_flow_status"):
            flow_status = flow_plugin.get_flow_status()
        
        # Get event gateway stats
        event_plugin = self.get_plugin("event-gateway")
        event_stats = {}
        if event_plugin and hasattr(event_plugin, "get_stats"):
            event_stats = event_plugin.get_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "plugins": plugin_statuses,
            "flows": flow_status,
            "events": event_stats,
            "stats": self._stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["events_tracked"] = len(self._recent_events)
        health["stats"] = self._stats
        return health


plugin_class = DashboardBackendPlugin

"""
Health checker for the Data Ingestor service
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any

import structlog

logger = structlog.get_logger(__name__)


class HealthChecker:
    """Health monitoring for the data ingestor service"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_tick_time = None
        self.adapter_status = {}
        self.redis_connected = False
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        uptime = time.time() - self.start_time
        
        # Determine overall status
        status = "healthy"
        if not self.redis_connected:
            status = "unhealthy"
        elif self.last_tick_time and (time.time() - self.last_tick_time) > 60:
            status = "degraded"  # No ticks for over 1 minute
        
        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "uptime_seconds": round(uptime, 2),
            "adapters_status": self.adapter_status.copy(),
            "redis_connected": self.redis_connected,
            "last_tick_timestamp": (
                datetime.fromtimestamp(self.last_tick_time, timezone.utc).isoformat()
                if self.last_tick_time else None
            )
        }
    
    def update_adapter_status(self, adapter_name: str, status: str):
        """Update status for a specific adapter"""
        self.adapter_status[adapter_name] = status
        logger.debug("Updated adapter status", adapter=adapter_name, status=status)
    
    def update_redis_status(self, connected: bool):
        """Update Redis connection status"""
        self.redis_connected = connected
        if connected:
            logger.info("Redis connection established")
        else:
            logger.error("Redis connection lost")
    
    def record_tick_processed(self):
        """Record that a tick was successfully processed"""
        self.last_tick_time = time.time()
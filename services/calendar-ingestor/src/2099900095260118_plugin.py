# doc_id: DOC-SERVICE-0139
# DOC_ID: DOC-ARCH-0106
"""
Calendar Ingestor Plugin
Downloads and processes economic calendar data
"""

from typing import Dict, Any, Optional
import asyncio
import structlog

from shared.plugin_interface import BasePlugin, PluginMetadata
from .ingestor import CalendarIngestor
from .config import Settings
from .metrics import MetricsCollector


logger = structlog.get_logger(__name__)


class CalendarIngestorPlugin(BasePlugin):
    """Calendar ingestor as a plugin"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="calendar-ingestor",
            version="1.0.0",
            description="Economic calendar data ingestion",
            author="EAFIX Team",
            dependencies=[],
        )
        super().__init__(metadata)
        self._ingestor: Optional[CalendarIngestor] = None
        self._task: Optional[asyncio.Task] = None
        self._metrics: Optional[MetricsCollector] = None
    
    async def _on_initialize(self) -> None:
        """Initialize the calendar ingestor"""
        settings = Settings(
            update_interval_hours=self.get_config("update_interval_hours", 24),
            data_source=self.get_config("data_source", "investing.com")
        )
        
        self._metrics = MetricsCollector()
        self._ingestor = CalendarIngestor(settings, self._metrics)
        
        logger.info("Calendar ingestor initialized")
    
    async def _on_start(self) -> None:
        """Start ingesting calendar data"""
        logger.info("Starting calendar ingestor")
        if self._ingestor:
            try:
                await self._ingestor.start()
            except Exception as exc:
                logger.error(f"Calendar ingestor start failed: {exc}")
        self._task = asyncio.create_task(self._run_ingestor())
    
    async def _on_stop(self) -> None:
        """Stop ingesting"""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._ingestor:
            await self._ingestor.stop()
        
        logger.info("Calendar ingestor stopped")
    
    async def _run_ingestor(self) -> None:
        """Main ingestor loop"""
        update_interval_sec = self.get_config("update_interval_hours", 24) * 3600
        
        while True:
            try:
                # Fetch and process calendar events
                events = await self._ingestor.fetch_events()
                
                if events:
                    # Emit calendar events
                    self.emit_event("calendar_update", {
                        "events": events,
                        "count": len(events)
                    })
                    
                    logger.info(f"Calendar updated with {len(events)} events")
                
                # Wait for next update
                await asyncio.sleep(update_interval_sec)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Calendar ingestor error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        
        if self._ingestor:
            health["last_update"] = getattr(self._ingestor, "last_update_time", None)
            health["events_count"] = getattr(self._ingestor, "event_count", 0)
        
        return health


plugin_class = CalendarIngestorPlugin

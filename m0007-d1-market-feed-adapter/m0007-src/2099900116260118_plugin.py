# doc_id: DOC-SERVICE-0128
# DOC_ID: DOC-ARCH-0103
"""
Example plugin adapter for data-ingestor service
Demonstrates how to convert existing service to plugin
"""

from typing import Dict, Any
import asyncio

from shared.plugin_interface import BasePlugin, PluginMetadata, PluginState
from .ingestor import DataIngestor
from .config import Settings


class DataIngestorPlugin(BasePlugin):
    """Data Ingestor as a plugin - adapts existing service"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="data-ingestor",
            version="1.0.0",
            description="Normalizes broker price feeds from MT4/DDE",
            author="EAFIX Team",
            dependencies=[],  # No dependencies - this is a data source
        )
        super().__init__(metadata)
        self._ingestor: Optional[DataIngestor] = None
        self._task: Optional[asyncio.Task] = None
    
    async def _on_initialize(self) -> None:
        """Initialize the ingestor"""
        settings = Settings()
        
        # Create ingestor instance
        self._ingestor = DataIngestor(settings)
    
    async def _on_start(self) -> None:
        """Start ingesting data"""
        if not self._ingestor:
            raise RuntimeError("Ingestor not initialized")
        
        try:
            await self._ingestor.start()
        except Exception as exc:
            print(f"Ingestor start failed: {exc}")
    
    async def _on_stop(self) -> None:
        """Stop ingesting"""
        if self._ingestor:
            await self._ingestor.stop()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for data ingestor"""
        base_health = await super().health_check()
        
        if self._ingestor:
            base_health["last_tick"] = getattr(self._ingestor, "last_tick_time", None)
            base_health["ticks_processed"] = getattr(self._ingestor, "tick_count", 0)
        
        return base_health


# Plugin entry point - registry will discover this
plugin_class = DataIngestorPlugin

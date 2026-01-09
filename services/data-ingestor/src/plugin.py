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
        # Build settings from plugin config
        settings = Settings(
            mt4_dde_path=self.get_config("mt4_dde_path", "C:\\MT4\\Data"),
            tick_buffer_size=self.get_config("tick_buffer_size", 1000),
            publish_interval_ms=self.get_config("publish_interval_ms", 100),
        )
        
        # Create ingestor instance
        self._ingestor = DataIngestor(settings)
        await self._ingestor.initialize()
    
    async def _on_start(self) -> None:
        """Start ingesting data"""
        if not self._ingestor:
            raise RuntimeError("Ingestor not initialized")
        
        # Start background task
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
            await self._ingestor.shutdown()
    
    async def _run_ingestor(self) -> None:
        """Main ingestor loop"""
        while True:
            try:
                # Read tick data
                tick = await self._ingestor.read_tick()
                
                if tick:
                    # Emit tick event to other plugins
                    self.emit_event("price_tick", tick)
                
                # Small delay
                await asyncio.sleep(self.get_config("publish_interval_ms", 100) / 1000)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                print(f"Ingestor error: {e}")
                await asyncio.sleep(1)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for data ingestor"""
        base_health = await super().health_check()
        
        if self._ingestor:
            base_health["last_tick"] = getattr(self._ingestor, "last_tick_time", None)
            base_health["ticks_processed"] = getattr(self._ingestor, "tick_count", 0)
        
        return base_health


# Plugin entry point - registry will discover this
plugin_class = DataIngestorPlugin

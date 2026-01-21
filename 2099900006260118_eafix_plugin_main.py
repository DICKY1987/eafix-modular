#!/usr/bin/env python3
# doc_id: DOC-DOC-0022
# DOC_ID: DOC-ARCH-0102
"""
EAFIX Plugin System - Main Entry Point
Replaces Docker Compose orchestration with in-process plugin management
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Dict, Any
import structlog
import yaml

from shared.plugin_registry import PluginRegistry
from shared.plugin_interface import PluginContext


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class EAFIXPluginSystem:
    """Main EAFIX plugin-based system orchestrator"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.registry: Optional[PluginRegistry] = None
        self._shutdown_event = asyncio.Event()
    
    def load_config(self) -> None:
        """Load system configuration"""
        logger.info(f"Loading configuration from {self.config_path}")
        
        with open(self.config_path) as f:
            self.config = yaml.safe_load(f)
        
        logger.info("Configuration loaded", plugin_count=len(self.config.get("plugins", {})))
    
    async def initialize(self) -> None:
        """Initialize plugin system"""
        logger.info("Initializing EAFIX plugin system")
        
        # Get plugin directories from config
        plugin_dirs = [
            Path(p) for p in self.config.get("plugin_directories", ["./services"])
        ]
        
        # Create registry
        self.registry = PluginRegistry(plugin_dirs)
        
        # Load all plugins
        plugin_configs = self.config.get("plugins", {})
        await self.registry.load_all(plugin_configs)
        
        logger.info("Plugin system initialized")
    
    async def start(self) -> None:
        """Start all plugins"""
        logger.info("Starting EAFIX system")
        
        if not self.registry:
            raise RuntimeError("System not initialized")
        
        await self.registry.start_all()
        
        logger.info("EAFIX system started successfully")
    
    async def stop(self) -> None:
        """Stop all plugins"""
        logger.info("Stopping EAFIX system")
        
        if self.registry:
            await self.registry.stop_all()
        
        logger.info("EAFIX system stopped")
    
    async def run(self) -> None:
        """Run the system until shutdown signal"""
        await self.initialize()
        await self.start()
        
        # Wait for shutdown signal
        logger.info("System running, waiting for shutdown signal...")
        await self._shutdown_event.wait()
        
        await self.stop()
    
    def signal_shutdown(self) -> None:
        """Signal system shutdown"""
        logger.info("Shutdown signal received")
        self._shutdown_event.set()
    
    async def health_check(self) -> Dict[str, Any]:
        """Get system health status"""
        if not self.registry:
            return {"status": "not_initialized"}
        
        plugin_health = await self.registry.health_check_all()
        
        # Determine overall status
        statuses = [h.get("status") for h in plugin_health.values()]
        if all(s == "healthy" for s in statuses):
            overall = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        else:
            overall = "degraded"
        
        return {
            "status": overall,
            "plugins": plugin_health
        }


async def main():
    """Main entry point"""
    # Default config path
    config_path = Path("config/plugins.yaml")
    
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
    
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    # Create system
    system = EAFIXPluginSystem(config_path)
    system.load_config()
    
    # Setup signal handlers (Windows-compatible)
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        system.signal_shutdown()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await system.run()
    except Exception as e:
        logger.error(f"System error: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("EAFIX system shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

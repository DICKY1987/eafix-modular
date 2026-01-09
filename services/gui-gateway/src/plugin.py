# DOC_ID: DOC-ARCH-0107
"""
GUI Gateway Plugin
Provides API gateway for operator UI
"""

from typing import Dict, Any, Optional
import asyncio
import structlog
from fastapi import FastAPI
import uvicorn

from shared.plugin_interface import BasePlugin, PluginMetadata
from .models import SystemStatus


logger = structlog.get_logger(__name__)


class GUIGatewayPlugin(BasePlugin):
    """GUI gateway as a plugin - exposes HTTP/WebSocket API"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="gui-gateway",
            version="1.0.0",
            description="Operator UI API gateway",
            author="EAFIX Team",
            dependencies=[],  # Can query all plugins
        )
        super().__init__(metadata)
        self._app: Optional[FastAPI] = None
        self._server: Optional[uvicorn.Server] = None
        self._server_task: Optional[asyncio.Task] = None
    
    async def _on_initialize(self) -> None:
        """Initialize the GUI gateway"""
        self._app = FastAPI(title="EAFIX GUI Gateway")
        
        # Register routes
        @self._app.get("/status")
        async def get_status():
            """Get system status"""
            all_plugins = self._context.get_all_plugins()
            
            plugin_status = {}
            for name, plugin in all_plugins.items():
                try:
                    health = await plugin.health_check()
                    plugin_status[name] = health
                except Exception as e:
                    plugin_status[name] = {"status": "error", "error": str(e)}
            
            return {
                "status": "running",
                "plugins": plugin_status
            }
        
        @self._app.get("/plugins")
        async def list_plugins():
            """List all loaded plugins"""
            all_plugins = self._context.get_all_plugins()
            return {
                "plugins": [
                    {
                        "name": plugin.metadata.name,
                        "version": plugin.metadata.version,
                        "description": plugin.metadata.description,
                        "state": plugin.state.value
                    }
                    for plugin in all_plugins.values()
                ]
            }
        
        @self._app.get("/health")
        async def health():
            """Health check endpoint"""
            return {"status": "healthy"}
        
        logger.info("GUI gateway initialized")
    
    async def _on_start(self) -> None:
        """Start the HTTP server"""
        port = self.get_config("http_port", 8080)
        
        config = uvicorn.Config(
            self._app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        self._server = uvicorn.Server(config)
        
        # Run server in background
        self._server_task = asyncio.create_task(self._server.serve())
        
        logger.info(f"GUI gateway started on port {port}")
    
    async def _on_stop(self) -> None:
        """Stop the HTTP server"""
        if self._server:
            self._server.should_exit = True
        
        if self._server_task:
            try:
                await asyncio.wait_for(self._server_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Server shutdown timeout")
        
        logger.info("GUI gateway stopped")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        health = await super().health_check()
        health["server_running"] = self._server is not None
        return health


plugin_class = GUIGatewayPlugin

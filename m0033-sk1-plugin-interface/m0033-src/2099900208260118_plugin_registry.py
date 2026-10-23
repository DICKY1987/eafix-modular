# doc_id: DOC-SERVICE-0190
# DOC_ID: DOC-ARCH-0101
"""
Plugin Registry - Dynamic plugin loading and lifecycle management
"""

import asyncio
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type
import structlog

from .plugin_interface import IPlugin, BasePlugin, PluginMetadata, PluginState, PluginContext


logger = structlog.get_logger(__name__)


class PluginRegistry:
    """
    Manages plugin discovery, loading, initialization, and lifecycle
    """
    
    def __init__(self, plugin_dirs: List[Path]):
        self.plugin_dirs = plugin_dirs
        self.context = PluginContext()
        self._plugins: Dict[str, IPlugin] = {}
        self._load_order: List[str] = []
    
    def discover_plugins(self) -> Dict[str, Type[IPlugin]]:
        """
        Discover all available plugins from plugin directories
        
        Returns:
            Dict mapping plugin names to plugin classes
        """
        discovered: Dict[str, Type[IPlugin]] = {}
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory not found: {plugin_dir}")
                continue
            
            for service_dir in plugin_dir.iterdir():
                if not service_dir.is_dir():
                    continue
                
                # Look for plugin.py or main.py
                plugin_file = service_dir / "src" / "plugin.py"
                if not plugin_file.exists():
                    plugin_file = service_dir / "src" / "main.py"
                
                if not plugin_file.exists():
                    continue
                
                try:
                    plugin_class = self._load_plugin_class(plugin_file, service_dir.name)
                    if plugin_class:
                        discovered[service_dir.name] = plugin_class
                        logger.info(f"Discovered plugin: {service_dir.name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {service_dir.name}: {e}")
        
        return discovered
    
    def _load_plugin_class(self, plugin_file: Path, plugin_name: str) -> Optional[Type[IPlugin]]:
        """Load plugin class from file"""
        try:
            # Construct module path
            parts = plugin_file.parts
            services_idx = parts.index("services")
            module_path = ".".join(parts[services_idx:-1]) + ".plugin"
            
            # Import module
            module = importlib.import_module(module_path)
            
            # Find plugin class
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj != BasePlugin and 
                    issubclass(obj, BasePlugin) and 
                    hasattr(obj, 'metadata')):
                    return obj
            
            logger.warning(f"No plugin class found in {plugin_file}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading plugin class from {plugin_file}: {e}")
            return None
    
    async def load_plugin(
        self, 
        plugin_class: Type[IPlugin], 
        config: Dict[str, any]
    ) -> None:
        """
        Load and initialize a single plugin
        
        Args:
            plugin_class: Plugin class to instantiate
            config: Plugin configuration
        """
        plugin = plugin_class()
        plugin_name = plugin.metadata.name
        
        logger.info(f"Loading plugin: {plugin_name}")
        
        try:
            await plugin.initialize(config, self.context)
            self.context.register_plugin(plugin)
            self._plugins[plugin_name] = plugin
            logger.info(f"Plugin loaded: {plugin_name}")
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise
    
    async def load_all(self, configs: Dict[str, Dict[str, any]]) -> None:
        """
        Load all discovered plugins with dependency resolution
        
        Args:
            configs: Dict mapping plugin names to their configs
        """
        discovered = self.discover_plugins()
        
        # Resolve dependency order
        self._load_order = self._resolve_dependencies(discovered)
        
        # Load in order
        for plugin_name in self._load_order:
            if plugin_name not in discovered:
                continue

            plugin_config = configs.get(plugin_name)
            if not plugin_config:
                logger.info(
                    "Skipping plugin not listed in configuration",
                    plugin=plugin_name,
                )
                continue

            if not plugin_config.get("enabled", True):
                logger.info(
                    "Skipping disabled plugin",
                    plugin=plugin_name,
                )
                continue

            plugin_class = discovered[plugin_name]
            await self.load_plugin(plugin_class, plugin_config)
    
    def _resolve_dependencies(self, plugins: Dict[str, Type[IPlugin]]) -> List[str]:
        """
        Resolve plugin loading order based on dependencies
        Simple topological sort
        """
        # Create instances to access metadata
        metadata_map = {}
        for name, cls in plugins.items():
            try:
                instance = cls()
                metadata_map[name] = instance.metadata
            except:
                logger.warning(f"Could not create instance of {name} for dependency resolution")
        
        # Build dependency graph
        ordered = []
        visited = set()
        
        def visit(name: str) -> None:
            if name in visited:
                return
            
            if name not in metadata_map:
                logger.warning(f"Plugin {name} referenced but not found")
                return
            
            visited.add(name)
            
            # Visit dependencies first
            for dep in metadata_map[name].dependencies:
                if dep not in visited and dep in metadata_map:
                    visit(dep)
            
            ordered.append(name)
        
        # Visit all plugins
        for name in metadata_map.keys():
            visit(name)
        
        return ordered
    
    async def start_all(self) -> None:
        """Start all loaded plugins in dependency order"""
        for plugin_name in self._load_order:
            if plugin_name in self._plugins:
                plugin = self._plugins[plugin_name]
                try:
                    logger.info(f"Starting plugin: {plugin_name}")
                    await plugin.start()
                    logger.info(f"Plugin started: {plugin_name}")
                except Exception as e:
                    logger.error(f"Failed to start plugin {plugin_name}: {e}")
                    raise
    
    async def stop_all(self) -> None:
        """Stop all plugins in reverse order"""
        for plugin_name in reversed(self._load_order):
            if plugin_name in self._plugins:
                plugin = self._plugins[plugin_name]
                try:
                    logger.info(f"Stopping plugin: {plugin_name}")
                    await plugin.stop()
                    logger.info(f"Plugin stopped: {plugin_name}")
                except Exception as e:
                    logger.error(f"Error stopping plugin {plugin_name}: {e}")
    
    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """Get loaded plugin by name"""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """Get all loaded plugins"""
        return self._plugins.copy()
    
    async def health_check_all(self) -> Dict[str, Dict[str, any]]:
        """Run health checks on all plugins"""
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = await plugin.health_check()
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        return results

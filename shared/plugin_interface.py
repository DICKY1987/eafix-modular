# DOC_ID: DOC-ARCH-0100
"""
Plugin Interface - Core plugin protocol for modular EAFIX system
Replaces Docker microservices with in-process plugin architecture
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from enum import Enum


class PluginState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """Plugin identification and dependencies"""
    name: str
    version: str
    description: str
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None


@runtime_checkable
class IPlugin(Protocol):
    """Plugin protocol - all plugins must implement this interface"""
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        ...
    
    @property
    def state(self) -> PluginState:
        """Current plugin state"""
        ...
    
    async def initialize(self, config: Dict[str, Any], context: 'PluginContext') -> None:
        """
        Initialize plugin with configuration and shared context
        
        Args:
            config: Plugin-specific configuration
            context: Shared context for inter-plugin communication
        """
        ...
    
    async def start(self) -> None:
        """Start plugin operations"""
        ...
    
    async def stop(self) -> None:
        """Stop plugin operations gracefully"""
        ...
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Return health status
        
        Returns:
            Dict with 'status' (healthy/degraded/unhealthy) and details
        """
        ...


class BasePlugin(ABC):
    """
    Base plugin implementation with common lifecycle management
    Inherit from this for concrete plugins
    """
    
    def __init__(self, metadata: PluginMetadata):
        self._metadata = metadata
        self._state = PluginState.UNLOADED
        self._context: Optional['PluginContext'] = None
        self._config: Dict[str, Any] = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    @property
    def state(self) -> PluginState:
        return self._state
    
    async def initialize(self, config: Dict[str, Any], context: 'PluginContext') -> None:
        """Initialize plugin"""
        self._state = PluginState.LOADING
        self._config = config
        self._context = context
        
        try:
            await self._on_initialize()
            self._state = PluginState.READY
        except Exception as e:
            self._state = PluginState.ERROR
            raise RuntimeError(f"Plugin {self.metadata.name} initialization failed: {e}")
    
    async def start(self) -> None:
        """Start plugin"""
        if self._state != PluginState.READY:
            raise RuntimeError(f"Cannot start plugin in state {self._state}")
        
        self._state = PluginState.RUNNING
        try:
            await self._on_start()
        except Exception as e:
            self._state = PluginState.ERROR
            raise RuntimeError(f"Plugin {self.metadata.name} start failed: {e}")
    
    async def stop(self) -> None:
        """Stop plugin"""
        if self._state not in (PluginState.RUNNING, PluginState.ERROR):
            return
        
        self._state = PluginState.STOPPING
        try:
            await self._on_stop()
        finally:
            self._state = PluginState.STOPPED
    
    async def health_check(self) -> Dict[str, Any]:
        """Default health check implementation"""
        return {
            "status": "healthy" if self._state == PluginState.RUNNING else "unhealthy",
            "state": self._state.value,
            "plugin": self.metadata.name
        }
    
    @abstractmethod
    async def _on_initialize(self) -> None:
        """Plugin-specific initialization logic"""
        pass
    
    @abstractmethod
    async def _on_start(self) -> None:
        """Plugin-specific start logic"""
        pass
    
    @abstractmethod
    async def _on_stop(self) -> None:
        """Plugin-specific stop logic"""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """Get another plugin by name from context"""
        if not self._context:
            return None
        return self._context.get_plugin(name)
    
    def emit_event(self, event_type: str, data: Any) -> None:
        """Emit event to event bus"""
        if self._context:
            self._context.emit_event(event_type, data, source=self.metadata.name)


class PluginContext:
    """
    Shared context for plugin communication
    Replaces network/HTTP calls with in-process communication
    """
    
    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._event_handlers: Dict[str, List[callable]] = {}
        self._shared_data: Dict[str, Any] = {}
    
    def register_plugin(self, plugin: IPlugin) -> None:
        """Register a plugin in the context"""
        self._plugins[plugin.metadata.name] = plugin
    
    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """Get plugin by name"""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """Get all registered plugins"""
        return self._plugins.copy()
    
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to events"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def emit_event(self, event_type: str, data: Any, source: str = "") -> None:
        """Emit event to all subscribers"""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event_type, data, source)
            except Exception as e:
                # Log but don't fail on handler errors
                print(f"Event handler error: {e}")
    
    def set_shared(self, key: str, value: Any) -> None:
        """Set shared data"""
        self._shared_data[key] = value
    
    def get_shared(self, key: str, default: Any = None) -> Any:
        """Get shared data"""
        return self._shared_data.get(key, default)

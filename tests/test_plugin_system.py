# DOC_ID: DOC-TEST-0100
"""
Plugin System Tests
"""

import pytest
import asyncio
from pathlib import Path

from shared.plugin_interface import (
    BasePlugin, PluginMetadata, PluginState, PluginContext
)
from shared.plugin_registry import PluginRegistry


class MockPlugin(BasePlugin):
    """Mock plugin for testing"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="mock-plugin",
            version="1.0.0",
            description="Mock plugin for testing",
            dependencies=[]
        )
        super().__init__(metadata)
        self.initialized = False
        self.started = False
        self.stopped = False
    
    async def _on_initialize(self) -> None:
        self.initialized = True
    
    async def _on_start(self) -> None:
        self.started = True
    
    async def _on_stop(self) -> None:
        self.stopped = True


class DependentPlugin(BasePlugin):
    """Plugin with dependencies for testing"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="dependent-plugin",
            version="1.0.0",
            description="Plugin with dependencies",
            dependencies=["mock-plugin"]
        )
        super().__init__(metadata)
    
    async def _on_initialize(self) -> None:
        pass
    
    async def _on_start(self) -> None:
        pass
    
    async def _on_stop(self) -> None:
        pass


@pytest.mark.unit
class TestPluginInterface:
    """Test plugin interface and lifecycle"""
    
    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """Test plugin can be initialized"""
        plugin = MockPlugin()
        context = PluginContext()
        
        assert plugin.state == PluginState.UNLOADED
        
        await plugin.initialize({}, context)
        
        assert plugin.state == PluginState.READY
        assert plugin.initialized is True
    
    @pytest.mark.asyncio
    async def test_plugin_lifecycle(self):
        """Test full plugin lifecycle"""
        plugin = MockPlugin()
        context = PluginContext()
        
        # Initialize
        await plugin.initialize({}, context)
        assert plugin.state == PluginState.READY
        
        # Start
        await plugin.start()
        assert plugin.state == PluginState.RUNNING
        assert plugin.started is True
        
        # Stop
        await plugin.stop()
        assert plugin.state == PluginState.STOPPED
        assert plugin.stopped is True
    
    @pytest.mark.asyncio
    async def test_plugin_config_access(self):
        """Test plugin can access configuration"""
        plugin = MockPlugin()
        context = PluginContext()
        
        config = {"setting1": "value1", "setting2": 42}
        await plugin.initialize(config, context)
        
        assert plugin.get_config("setting1") == "value1"
        assert plugin.get_config("setting2") == 42
        assert plugin.get_config("missing", "default") == "default"
    
    @pytest.mark.asyncio
    async def test_plugin_health_check(self):
        """Test plugin health check"""
        plugin = MockPlugin()
        context = PluginContext()
        
        await plugin.initialize({}, context)
        await plugin.start()
        
        health = await plugin.health_check()
        
        assert health["status"] == "healthy"
        assert health["state"] == "running"
        assert health["plugin"] == "mock-plugin"


@pytest.mark.unit
class TestPluginContext:
    """Test plugin context and communication"""
    
    def test_plugin_registration(self):
        """Test plugins can be registered in context"""
        context = PluginContext()
        plugin = MockPlugin()
        
        context.register_plugin(plugin)
        
        retrieved = context.get_plugin("mock-plugin")
        assert retrieved is plugin
    
    def test_event_subscription(self):
        """Test event subscription and emission"""
        context = PluginContext()
        
        events_received = []
        
        def handler(event_type, data, source):
            events_received.append((event_type, data, source))
        
        context.subscribe("test_event", handler)
        context.emit_event("test_event", {"key": "value"}, "test_source")
        
        assert len(events_received) == 1
        assert events_received[0][0] == "test_event"
        assert events_received[0][1] == {"key": "value"}
        assert events_received[0][2] == "test_source"
    
    def test_shared_data(self):
        """Test shared data storage"""
        context = PluginContext()
        
        context.set_shared("key1", "value1")
        context.set_shared("key2", 123)
        
        assert context.get_shared("key1") == "value1"
        assert context.get_shared("key2") == 123
        assert context.get_shared("missing", "default") == "default"


@pytest.mark.unit
class TestPluginRegistry:
    """Test plugin registry and loading"""
    
    @pytest.mark.asyncio
    async def test_dependency_resolution(self):
        """Test plugins are loaded in dependency order"""
        registry = PluginRegistry([])
        
        # Create plugins manually for testing
        plugins = {
            "mock-plugin": MockPlugin,
            "dependent-plugin": DependentPlugin
        }
        
        # Resolve order
        order = registry._resolve_dependencies(plugins)
        
        # mock-plugin should come before dependent-plugin
        assert order.index("mock-plugin") < order.index("dependent-plugin")
    
    @pytest.mark.asyncio
    async def test_load_plugin(self):
        """Test loading a single plugin"""
        registry = PluginRegistry([])
        
        config = {"test_setting": "test_value"}
        await registry.load_plugin(MockPlugin, config)
        
        plugin = registry.get_plugin("mock-plugin")
        assert plugin is not None
        assert plugin.state == PluginState.READY
    
    @pytest.mark.asyncio
    async def test_start_stop_all(self):
        """Test starting and stopping all plugins"""
        registry = PluginRegistry([])
        
        # Load plugins
        await registry.load_plugin(MockPlugin, {})
        
        # Manually add to load order since we bypassed load_all
        registry._load_order = ["mock-plugin"]
        
        # Start all
        await registry.start_all()
        
        plugin = registry.get_plugin("mock-plugin")
        assert plugin.state == PluginState.RUNNING
        
        # Stop all
        await registry.stop_all()
        
        assert plugin.state == PluginState.STOPPED
    
    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health check of all plugins"""
        registry = PluginRegistry([])
        
        await registry.load_plugin(MockPlugin, {})
        
        # Manually add to load order
        registry._load_order = ["mock-plugin"]
        
        await registry.start_all()
        
        health = await registry.health_check_all()
        
        assert "mock-plugin" in health
        assert health["mock-plugin"]["status"] == "healthy"


@pytest.mark.integration
class TestPluginCommunication:
    """Test inter-plugin communication"""
    
    @pytest.mark.asyncio
    async def test_plugins_can_communicate(self):
        """Test plugins can find and communicate with each other"""
        context = PluginContext()
        
        plugin1 = MockPlugin()
        plugin2 = DependentPlugin()
        
        await plugin1.initialize({}, context)
        await plugin2.initialize({}, context)
        
        context.register_plugin(plugin1)
        context.register_plugin(plugin2)
        
        # plugin2 should be able to get plugin1
        retrieved = plugin2.get_plugin("mock-plugin")
        assert retrieved is plugin1
    
    @pytest.mark.asyncio
    async def test_event_driven_communication(self):
        """Test event-driven communication between plugins"""
        context = PluginContext()
        
        plugin1 = MockPlugin()
        plugin2 = MockPlugin()
        plugin2._metadata.name = "mock-plugin-2"
        
        await plugin1.initialize({}, context)
        await plugin2.initialize({}, context)
        
        events_received = []
        
        def handler(event_type, data, source):
            events_received.append(data)
        
        context.subscribe("test_event", handler)
        
        # Plugin1 emits event
        plugin1.emit_event("test_event", {"message": "hello"})
        
        # Handler should receive it
        assert len(events_received) == 1
        assert events_received[0]["message"] == "hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

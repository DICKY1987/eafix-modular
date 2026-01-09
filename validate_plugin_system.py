#!/usr/bin/env python3
"""
Plugin System Validation Script
Quick validation that the plugin system is working
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.plugin_interface import BasePlugin, PluginMetadata, PluginContext
from shared.plugin_registry import PluginRegistry


class TestPlugin(BasePlugin):
    """Simple test plugin"""
    
    def __init__(self):
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            description="Test plugin for validation",
            dependencies=[]
        )
        super().__init__(metadata)
    
    async def _on_initialize(self) -> None:
        print("  ✓ Plugin initialized")
    
    async def _on_start(self) -> None:
        print("  ✓ Plugin started")
        self.emit_event("test_event", {"message": "Hello from plugin!"})
    
    async def _on_stop(self) -> None:
        print("  ✓ Plugin stopped")


async def validate_plugin_system():
    """Run validation checks"""
    print("=" * 60)
    print("EAFIX Plugin System Validation")
    print("=" * 60)
    
    # Test 1: Plugin Context
    print("\n[1/6] Testing PluginContext...")
    context = PluginContext()
    
    event_received = []
    context.subscribe("test_event", lambda t, d, s: event_received.append(d))
    context.emit_event("test_event", {"test": "data"}, "validator")
    
    assert len(event_received) == 1, "Event not received"
    assert event_received[0]["test"] == "data", "Event data incorrect"
    print("  ✓ PluginContext working")
    
    # Test 2: Plugin Lifecycle
    print("\n[2/6] Testing Plugin Lifecycle...")
    plugin = TestPlugin()
    
    await plugin.initialize({}, context)
    assert plugin.state.value == "ready", "Plugin not ready"
    
    await plugin.start()
    assert plugin.state.value == "running", "Plugin not running"
    
    await plugin.stop()
    assert plugin.state.value == "stopped", "Plugin not stopped"
    print("  ✓ Plugin lifecycle working")
    
    # Test 3: Plugin Registry
    print("\n[3/6] Testing PluginRegistry...")
    registry = PluginRegistry([])
    
    await registry.load_plugin(TestPlugin, {"setting": "value"})
    plugin = registry.get_plugin("test-plugin")
    
    assert plugin is not None, "Plugin not loaded"
    assert plugin.get_config("setting") == "value", "Config not accessible"
    print("  ✓ PluginRegistry working")
    
    # Test 4: Health Checks
    print("\n[4/6] Testing Health Checks...")
    registry._load_order = ["test-plugin"]
    await registry.start_all()
    
    health = await registry.health_check_all()
    assert "test-plugin" in health, "Health check missing"
    assert health["test-plugin"]["status"] == "healthy", "Plugin not healthy"
    print("  ✓ Health checks working")
    
    # Test 5: Event Communication
    print("\n[5/6] Testing Event Communication...")
    events = []
    
    # Get fresh plugin after restart
    await registry.stop_all()
    registry2 = PluginRegistry([])
    await registry2.load_plugin(TestPlugin, {})
    registry2._load_order = ["test-plugin"]
    
    # Subscribe before starting
    registry2.context.subscribe("test_event", lambda t, d, s: events.append(d))
    
    await registry2.start_all()
    
    plugin = registry2.get_plugin("test-plugin")
    plugin.emit_event("test_event", {"msg": "test"})
    
    assert len(events) > 0, "Events not propagating"
    print("  ✓ Event communication working")
    
    # Cleanup
    await registry2.stop_all()
    
    # Test 6: Configuration Loading
    print("\n[6/6] Testing Configuration...")
    config_path = Path("config/plugins.yaml")
    
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        assert "plugins" in config, "Config missing plugins section"
        assert len(config["plugins"]) > 0, "No plugins configured"
        print(f"  ✓ Configuration valid ({len(config['plugins'])} plugins configured)")
    else:
        print("  ⚠ Configuration file not found (optional)")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL VALIDATION CHECKS PASSED")
    print("=" * 60)
    print("\nPlugin system is working correctly!")
    print("\nNext steps:")
    print("  1. Run the system: python eafix_plugin_main.py config/plugins.yaml")
    print("  2. Check status: curl http://localhost:8080/status")
    print("  3. Run tests: python -m pytest tests/test_plugin_system.py")
    print()
    
    return True


async def main():
    """Main entry point"""
    try:
        success = await validate_plugin_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ VALIDATION FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# Plugin System Migration Guide

## Overview
This guide explains how to migrate from Docker container architecture to the new plugin-based modular design.

## Key Changes

### Architecture
- **Before**: Microservices in separate Docker containers communicating via HTTP/Redis
- **After**: In-process plugins communicating via event bus and shared context

### Benefits
1. **No Docker overhead**: Simpler deployment, faster startup
2. **In-process communication**: Lower latency, no network serialization
3. **Easier debugging**: Single process, standard Python debugging tools
4. **Simplified configuration**: Single YAML file instead of docker-compose
5. **Dynamic loading**: Enable/disable plugins without rebuilding containers

## Migration Steps

### 1. Convert Service to Plugin

Each service needs a `plugin.py` that wraps the existing service logic:

```python
# services/<service-name>/src/plugin.py

from shared.plugin_interface import BasePlugin, PluginMetadata
from .main import YourService  # Import existing service

class YourServicePlugin(BasePlugin):
    def __init__(self):
        metadata = PluginMetadata(
            name="your-service",
            version="1.0.0",
            description="Service description",
            dependencies=["dependency-plugin"]  # List dependencies
        )
        super().__init__(metadata)
        self._service = None
    
    async def _on_initialize(self) -> None:
        """Initialize service with plugin config"""
        config = self.get_config("setting_name", default_value)
        self._service = YourService(config)
        await self._service.initialize()
    
    async def _on_start(self) -> None:
        """Start service operations"""
        await self._service.start()
    
    async def _on_stop(self) -> None:
        """Stop service gracefully"""
        await self._service.stop()

# Export for discovery
plugin_class = YourServicePlugin
```

### 2. Replace Network Calls with Plugin Communication

**Before (HTTP/Redis):**
```python
# Making HTTP call to another service
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://indicator-engine:8082/calculate",
        json={"price": 1.2345}
    )
```

**After (Plugin context):**
```python
# Get plugin directly
indicator_plugin = self.get_plugin("indicator-engine")
if indicator_plugin:
    # Call method directly (if exposed)
    result = await indicator_plugin.calculate(price=1.2345)

# Or emit event and subscribe to results
self.emit_event("price_update", {"price": 1.2345})
```

### 3. Event-Driven Communication

Use events for loose coupling:

```python
# Subscribe to events in _on_initialize
self._context.subscribe("price_tick", self._handle_price_tick)

# Handler method
def _handle_price_tick(self, event_type, data, source):
    price = data.get("price")
    # Process price data
    
# Emit events
self.emit_event("signal_generated", {
    "symbol": "EURUSD",
    "action": "BUY",
    "confidence": 0.85
})
```

### 4. Update Configuration

Add your plugin to `config/plugins.yaml`:

```yaml
plugins:
  your-service:
    enabled: true
    your_setting: value
    another_setting: 123
```

### 5. Handle Shared Resources

**Redis/Database:**
- Keep Redis/Postgres as external services (non-containerized)
- Plugins connect directly to localhost
- Share connection pools via plugin context:

```python
# In _on_initialize
redis_client = self._context.get_shared("redis_client")
if not redis_client:
    # Create and share
    redis_client = redis.Redis(...)
    self._context.set_shared("redis_client", redis_client)
```

## Running the System

### Start all plugins:
```bash
python eafix_plugin_main.py config/plugins.yaml
```

### Development mode (single plugin):
```bash
# Still possible to run individual services for testing
cd services/data-ingestor
poetry run python -m data_ingestor.main
```

## Service-Specific Migration

### Data Ingestor
- ✅ Example plugin created: `services/data-ingestor/src/plugin.py`
- Emits `price_tick` events instead of Redis pub/sub
- Config: `mt4_dde_path`, `tick_buffer_size`, `publish_interval_ms`

### Indicator Engine
- Subscribe to `price_tick` events
- Emit `indicator_update` events
- Dependencies: `["data-ingestor"]`

### Signal Generator
- Subscribe to `indicator_update` events
- Emit `signal_generated` events
- Dependencies: `["indicator-engine"]`

### Risk Manager
- Subscribe to `signal_generated` events
- Emit `order_approved` or `order_rejected` events
- Dependencies: `["signal-generator"]`

### Execution Engine
- Subscribe to `order_approved` events
- Emit `order_executed` events
- Dependencies: `["risk-manager"]`

## Testing Plugins

```python
# tests/test_plugin_system.py
import pytest
from shared.plugin_registry import PluginRegistry
from pathlib import Path

@pytest.mark.asyncio
async def test_plugin_loading():
    registry = PluginRegistry([Path("services")])
    
    config = {"data-ingestor": {"enabled": True}}
    await registry.load_all(config)
    
    plugin = registry.get_plugin("data-ingestor")
    assert plugin is not None
    assert plugin.state == PluginState.READY
```

## Troubleshooting

### Plugin not discovered
- Check `services/<name>/src/plugin.py` exists
- Ensure `plugin_class = YourPlugin` is exported
- Verify plugin inherits from `BasePlugin`

### Dependency errors
- Check `dependencies` list in metadata
- Ensure dependency plugins are enabled in config
- Review load order in logs

### Communication issues
- Use event bus for loose coupling
- Check event subscriptions are registered in `_on_initialize`
- Log event emissions for debugging

## Backward Compatibility

During migration, you can run hybrid mode:
- Keep some services in Docker
- Run others as plugins
- Use Redis as message broker between both

Eventually remove Docker services as plugins are completed.

## Next Steps

1. ✅ Core plugin infrastructure created
2. ✅ Example plugin adapter (data-ingestor)
3. 🔲 Migrate remaining services (indicator-engine, signal-generator, etc.)
4. 🔲 Add plugin hot-reload support
5. 🔲 Create plugin marketplace/discovery UI
6. 🔲 Remove Docker dependencies

## Support Files

- `shared/plugin_interface.py` - Plugin protocol and base class
- `shared/plugin_registry.py` - Plugin discovery and lifecycle
- `eafix_plugin_main.py` - Main entry point
- `config/plugins.yaml` - System configuration

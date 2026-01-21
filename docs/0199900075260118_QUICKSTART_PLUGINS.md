---
doc_id: DOC-DOC-0074
---

# Quick Start Guide - EAFIX Plugin System

## Installation

```bash
# Install dependencies
poetry install

# Add PyYAML if not present
poetry add pyyaml
```

## Running the System

### Start all plugins:
```bash
python eafix_plugin_main.py config/plugins.yaml
```

### View system status:
Open browser to http://localhost:8080/status to see all plugin health.

### Available endpoints (GUI Gateway):
- `GET /status` - System and plugin status
- `GET /plugins` - List all loaded plugins
- `GET /health` - Health check

## Testing

```bash
# Run all tests
poetry run pytest

# Run plugin system tests only
poetry run pytest tests/test_plugin_system.py -v

# Run with coverage
poetry run pytest --cov=shared --cov=services
```

## Configuration

Edit `config/plugins.yaml` to:
- Enable/disable plugins (`enabled: true/false`)
- Configure plugin settings
- Add new plugins

Example:
```yaml
plugins:
  data-ingestor:
    enabled: true
    mt4_dde_path: "C:\\MT4\\Data"
    tick_buffer_size: 1000
```

## Creating a New Plugin

1. Create `services/your-plugin/src/plugin.py`:

```python
from shared.plugin_interface import BasePlugin, PluginMetadata

class YourPlugin(BasePlugin):
    def __init__(self):
        metadata = PluginMetadata(
            name="your-plugin",
            version="1.0.0",
            description="Your plugin description",
            dependencies=[]  # List dependency plugins
        )
        super().__init__(metadata)
    
    async def _on_initialize(self) -> None:
        # Setup code here
        pass
    
    async def _on_start(self) -> None:
        # Start operations
        pass
    
    async def _on_stop(self) -> None:
        # Cleanup
        pass

plugin_class = YourPlugin
```

2. Add to `config/plugins.yaml`:

```yaml
plugins:
  your-plugin:
    enabled: true
    your_setting: value
```

3. Restart the system - plugin will be auto-discovered!

## Event Communication

### Subscribe to events:
```python
async def _on_initialize(self):
    self._context.subscribe("price_tick", self._handle_price)

def _handle_price(self, event_type, data, source):
    price = data.get("price")
    # Process price
```

### Emit events:
```python
self.emit_event("signal_generated", {
    "symbol": "EURUSD",
    "action": "BUY"
})
```

## Available Events

- `price_tick` - New price data from data-ingestor
- `indicator_update` - Indicator calculations updated
- `signal_generated` - Trading signal generated
- `order_approved` - Risk check passed
- `order_rejected` - Risk check failed
- `order_executed` - Order sent to broker
- `trade_result` - Trade completed
- `reentry_decision` - Re-entry decision made
- `calendar_update` - Economic calendar updated
- `validation_failed` - Data validation failed

## Direct Plugin Communication

```python
# Get another plugin
other_plugin = self.get_plugin("other-plugin-name")

# Call methods (if exposed)
result = await other_plugin.some_method()
```

## Shared Resources

### Redis/Database connections:
```python
async def _on_initialize(self):
    # Get or create shared Redis client
    redis_client = self._context.get_shared("redis_client")
    if not redis_client:
        redis_client = redis.Redis(host="localhost", port=6379)
        self._context.set_shared("redis_client", redis_client)
```

## Debugging

### Enable debug logging:
```python
# In eafix_plugin_main.py, change processor:
structlog.processors.JSONRenderer()
# to:
structlog.dev.ConsoleRenderer()
```

### Run single service (development):
```bash
cd services/data-ingestor
poetry run python -m data_ingestor.main
```

## Migrated Plugins Status

✅ **Working Plugins:**
- data-ingestor
- data-validator
- event-gateway
- telemetry-daemon
- flow-orchestrator
- reentry-engine
- reentry-matrix-svc
- calendar-ingestor
- gui-gateway
- dashboard-backend

⏳ **TODO (still as Docker services):**
- indicator-engine
- signal-generator
- risk-manager
- execution-engine
- reporter

See `PLUGIN_MIGRATION_GUIDE.md` for migration instructions.

## Troubleshooting

### Plugin not loading:
- Check `services/<name>/src/plugin.py` exists
- Verify `plugin_class = YourPlugin` is at end of file
- Check plugin inherits from `BasePlugin`
- View logs for import errors

### Events not received:
- Verify subscription in `_on_initialize`
- Check event type matches exactly
- Ensure source plugin is enabled and running

### Dependency errors:
- Check dependencies are listed in metadata
- Ensure dependency plugins are enabled in config
- Dependencies must be loaded first (automatic)

## Next Steps

1. Test the current plugin system: `python eafix_plugin_main.py`
2. Migrate remaining services (see PLUGIN_MIGRATION_GUIDE.md)
3. Remove Docker dependencies
4. Add hot-reload support (future)

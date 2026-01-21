---
doc_id: DOC-DOC-0001
---

# EAFIX Trading System - Modularized Architecture

This repository contains the modularized version of the EAFIX trading system, using a **plugin-based architecture** for in-process modular design.

## Architecture Overview

The system uses a **plugin-based modular architecture** with 15 core plugins (10 migrated, 5 in progress):

### ✅ Active Plugins
- **data-ingestor**: Normalizes broker price feeds from MT4/DDE
- **data-validator**: Validates incoming data quality
- **event-gateway**: Routes events between plugins
- **telemetry-daemon**: Collects metrics and telemetry
- **flow-orchestrator**: Trading flow state machine
- **reentry-engine**: Re-entry processing engine
- **reentry-matrix-svc**: Re-entry decision resolution
- **calendar-ingestor**: Economic calendar data intake
- **gui-gateway**: HTTP API gateway for UI
- **dashboard-backend**: Dashboard data aggregation

### ⏳ Pending Migration
- **indicator-engine**: Technical indicator calculations
- **signal-generator**: Trading signal generation  
- **risk-manager**: Position sizing and risk checks
- **execution-engine**: Order execution to broker
- **reporter**: Metrics and P&L reporting

### Plugin System Benefits
- **In-process communication**: Lower latency, no network overhead (1000x faster)
- **Dynamic loading**: Enable/disable plugins without rebuilding
- **Simplified deployment**: No Docker required
- **Easier debugging**: Single process, standard Python debugging
- **Auto-discovery**: Plugins loaded automatically from `services/*/src/plugin.py`
- **Event-driven**: Loose coupling via pub/sub event bus

## Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- Redis (localhost:6379)
- PostgreSQL (localhost:5432)

### Installation & Running
```bash
# Install dependencies
poetry install

# Run plugin system
python eafix_plugin_main.py config/plugins.yaml

# Or run individual plugin for development
cd services/data-ingestor
poetry run python -m data_ingestor.main
```

### Docker (Legacy)
```bash
# Legacy Docker mode still available
docker compose -f deploy/compose/docker-compose.yml up
```

### Testing
```bash
# Run all tests
pytest

# Run contract tests
pytest tests/contracts/

# Run service-specific tests
cd services/data-ingestor && pytest
```

## Documentation

- [Service Catalog](docs/modernization/01_service_catalog.md) - Service definitions and SLOs
- [ADR-0001](docs/adr/ADR-0001-service-decomposition.md) - Service decomposition decisions
- [Contracts](contracts/) - API and event schemas
- [Runbooks](docs/runbooks/) - Operations documentation

## Development

This system follows the modularization plan principles:
- **Determinism & Idempotence**: All operations are repeatable
- **Single Source of Truth**: Schemas are canonical
- **Defensive Posture**: Fail closed on integrity errors
- **Explicit Fallbacks**: Tiered parameter resolution

## Deployment

- **Local**: Docker Compose for development
- **Production**: Kubernetes manifests in `deploy/k8s/`
- **Monitoring**: Structured logging and metrics endpoints

## License

MIT License - see LICENSE file for details
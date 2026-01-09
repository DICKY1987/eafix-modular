---
doc_id: DOC-DOC-0001
---

# EAFIX Trading System - Modularized Architecture

This repository contains the modularized version of the EAFIX trading system, decomposed from a monolithic application into containerized microservices.

## Architecture Overview

The system consists of 9 core microservices:

- **data-ingestor**: Normalizes broker price feeds from MT4/DDE
- **indicator-engine**: Computes technical indicators  
- **signal-generator**: Applies trading rules and thresholds
- **risk-manager**: Position sizing and risk checks
- **execution-engine**: Sends orders to broker
- **calendar-ingestor**: Economic calendar data intake
- **reentry-matrix-svc**: Re-entry decision management
- **reporter**: Metrics and P&L reporting
- **gui-gateway**: Operator UI API gateway

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Poetry (for development)

### Local Development
```bash
# Start all services
docker compose -f deploy/compose/docker-compose.yml up

# Run specific service in development
cd services/data-ingestor
poetry install
poetry run python -m data_ingestor.main
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
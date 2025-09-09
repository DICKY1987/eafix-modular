# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the **modularized EAFIX trading system** - a complete rewrite of a monolithic trading application into 9 containerized microservices. The system processes real-time financial data, generates trading signals, manages risk, and executes trades through broker interfaces.

**Architecture**: Event-driven microservices with FastAPI/Redis
**Language**: Python 3.11 with Poetry workspace management
**Deployment**: Docker containers with Kubernetes support
**Messaging**: Redis pub/sub for asynchronous events, HTTP for synchronous calls

## Key Development Commands

### Project Setup
```bash
# Install Poetry (if not installed)
pip install poetry

# Install all dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install
```

### Development Workflow
```bash
# Start entire system locally
docker compose -f deploy/compose/docker-compose.yml up

# Start individual service for development
cd services/data-ingestor
poetry install
poetry run python -m src.main

# Run specific service with environment
REDIS_URL=redis://localhost:6379 poetry run python -m src.main
```

### Testing
```bash
# Run all tests across all services
poetry run pytest

# Run tests for specific service
cd services/data-ingestor && poetry run pytest

# Run with coverage
poetry run pytest --cov=services

# Run specific test file
poetry run pytest services/data-ingestor/tests/test_ingestor.py

# Run tests matching pattern
poetry run pytest -k "test_price_tick"

# Contract tests (schema validation)
poetry run pytest tests/contracts/
```

### Code Quality
```bash
# Format code
poetry run black services/
poetry run isort services/

# Lint code
poetry run flake8 services/

# Type checking
poetry run mypy services/data-ingestor/src

# Run all quality checks
poetry run black --check services/
poetry run isort --check-only services/
poetry run flake8 services/
poetry run mypy services/*/src
```

### Docker Development
```bash
# Build specific service image
docker build -t eafix/data-ingestor services/data-ingestor/

# Run service container
docker run -p 8080:8080 -e REDIS_URL=redis://host.docker.internal:6379 eafix/data-ingestor

# View service logs
docker logs eafix-data-ingestor

# Shell into running container
docker exec -it eafix-data-ingestor /bin/bash
```

### Schema Management
```bash
# Validate event schemas
python -c "
import json, jsonschema, os
for f in os.listdir('contracts/events'):
    with open(f'contracts/events/{f}') as file:
        jsonschema.Draft7Validator.check_schema(json.load(file))
    print(f'✓ {f}')
"

# Generate code from schemas (if tooling exists)
# This would be service-specific implementation
```

## Architecture Overview

### Microservices Design

The system follows **event-driven architecture** with clear service boundaries:

**Data Flow**: `data-ingestor` → `indicator-engine` → `signal-generator` → `risk-manager` → `execution-engine`

**9 Core Services**:
- **data-ingestor**: Normalizes MT4/DDE price feeds → `PriceTick@1.0` events
- **indicator-engine**: Computes technical indicators → `IndicatorVector@1.1` events  
- **signal-generator**: Applies trading rules → `Signal@1.0` events
- **risk-manager**: Position sizing/risk checks → `OrderIntent@1.2` (HTTP API)
- **execution-engine**: Broker order execution → `ExecutionReport@1.0` events
- **calendar-ingestor**: Economic calendar processing → `CalendarEvent@1.0` events
- **reentry-matrix-svc**: Re-entry decision logic → `ReentryDecision@1.0` events
- **reporter**: Metrics and P&L analysis
- **gui-gateway**: API gateway for operator UI

### Communication Patterns

**Asynchronous Events** (Redis pub/sub):
- Price data propagation
- Signal generation pipeline  
- Execution reporting
- Calendar notifications

**Synchronous HTTP APIs**:
- Risk validation: `signal-generator` → `risk-manager` 
- Order placement: `risk-manager` → `execution-engine`
- GUI operations: `gui-gateway` → all services

### Service Structure

Each service follows consistent structure:
```
services/<service-name>/
├── src/                 # Core service logic
│   ├── main.py         # FastAPI application entry point
│   ├── config.py       # Pydantic settings
│   ├── models.py       # Data models matching event schemas
│   ├── health.py       # Health check logic
│   └── metrics.py      # Prometheus metrics
├── adapters/           # External system interfaces
├── tests/             # Unit and integration tests
├── Dockerfile         # Container configuration
└── requirements.txt   # Service-specific dependencies
```

### Event Schemas & Contracts

All inter-service communication uses **versioned schemas** in `contracts/events/`:
- **PriceTick@1.0**: Market price data
- **IndicatorVector@1.1**: Technical indicator results
- **Signal@1.0**: Trading signals with confidence scores
- **OrderIntent@1.2**: Risk-approved orders ready for execution
- **ExecutionReport@1.0**: Broker execution results
- **CalendarEvent@1.0**: Economic calendar events
- **ReentryDecision@1.0**: Matrix-based re-entry decisions

Schema validation is enforced in CI/CD pipeline and at runtime.

## Development Patterns

### Service Implementation

**FastAPI Pattern**: All services use FastAPI with:
- Async/await for I/O operations
- Pydantic models for data validation
- Structured logging with contextual information
- Health checks at `/healthz`
- Metrics at `/metrics` (Prometheus format)

**Configuration**: Pydantic Settings with environment variable override:
```python
class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    log_level: str = "INFO"
    
    class Config:
        env_prefix = "SERVICE_"
```

**Error Handling**: Services follow defensive posture:
- Fail closed on data integrity errors
- Circuit breakers for external dependencies  
- Graceful degradation when possible
- Comprehensive error logging

### Testing Strategy

**Unit Tests**: Each service has isolated unit tests
**Contract Tests**: Validate event schema compliance
**Integration Tests**: End-to-end pipeline testing with Docker Compose
**Service Tests**: Health checks and API endpoint validation

Test configuration in `pyproject.toml` enables:
- Async testing with `pytest-asyncio`
- Coverage reporting across all services
- Parallel test execution per service

### Observability

**Structured Logging**: JSON format with correlation IDs
**Metrics**: Prometheus metrics for latency, throughput, errors
**Health Monitoring**: Multi-level health checks (Redis, external APIs, data freshness)
**Distributed Tracing**: Ready for OpenTelemetry integration

## Deployment Architecture

### Local Development
- Docker Compose orchestrates all services
- Redis for message bus
- PostgreSQL for persistent data
- Volume mounts for rapid development iteration

### Production Deployment
- Kubernetes manifests in `deploy/k8s/` (when created)
- Horizontal scaling for stateless services
- Resource limits and requests defined
- Rolling updates with health check validation

### CI/CD Pipeline
- GitHub Actions matrix build per service
- Automated testing, linting, type checking
- Docker image building and pushing
- Contract validation and integration testing

## Key Principles

**Determinism & Idempotence**: All operations are repeatable with identical inputs
**Single Source of Truth**: Event schemas in `contracts/` are canonical
**Defensive Posture**: Fail closed on integrity errors, validate all inputs
**Explicit Fallbacks**: Tiered parameter resolution with audit trails

## Configuration Management

**Environment Variables**: Service configuration via environment variables
**Docker Compose**: Local development environment configuration
**Secrets**: Never commit sensitive data; use environment variables or secret management
**Feature Flags**: Configuration-driven feature enablement per service
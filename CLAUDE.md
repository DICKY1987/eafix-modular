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

# Contract testing specific commands
make contracts-test             # Run all contract and scenario tests
make contracts-consumer         # Consumer contract tests only
make contracts-provider         # Provider verification tests only
make contracts-scenarios        # Scenario-based integration tests
make contracts-properties       # Property-based contract tests
make contracts-coverage         # Contract tests with coverage reporting
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

### Production Operations (Make Targets)
```bash
# Essential production commands
make help                    # Show all available targets
make install                 # Install dependencies and pre-commit hooks
make docker-up              # Start entire system with Docker Compose
make docker-down            # Stop all services
make docker-logs            # Follow container logs

# Testing and validation
make test-all               # Run full test suite across all services
make smoke                  # End-to-end health verification
make contracts-validate     # Validate JSON schemas
make contracts-compat       # Check schema backward compatibility
make replay-test            # Performance testing with tick replay

# Code quality
make format                 # Format code with black and isort
make lint                   # Run linting and type checks

# Production readiness
make gaps-check             # Review production readiness gaps and SLOs
```

### Contract & Schema Management
```bash
# Comprehensive contract validation (JSON + CSV + re-entry library)
make contracts-validate-full

# Individual validation targets
make contracts-validate        # Validate JSON schemas only
make csv-validate             # Validate CSV artifacts
make reentry-validate         # Test shared re-entry library
make contracts-test           # Run contract integration tests
make contracts-compat         # Check schema backward compatibility

# Manual validation tools
python ci/validate_schemas.py                                    # Schema metaschema validation
python contracts/validate_json_schemas.py --report              # Full JSON validation report
python contracts/validate_csv_artifacts.py --directory <path>   # CSV structure validation
python tests/contracts/test_integration.py                      # End-to-end contract tests
```

### Performance Testing
```bash
# Run tick replay performance test
make replay-test

# Custom replay test with options
python scripts/replay/replay_ticks.py data.csv --url http://localhost:8081/ingest/manual --delay 0.001 --verbose
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

### Contract System & Schema Registry

The system uses a **centralized contract registry** with comprehensive validation:

**Contract Structure**:
```
contracts/
├── schemas/json/          # JSON schemas (orders_in/out, indicator_record, hybrid_id)
├── schemas/csv/           # CSV format documentation with atomic write policies
├── identifiers/           # Identifier specifications (hybrid_id, cal8, cal5_legacy) 
├── policies/             # Data integrity policies (csv_atomic_write)
├── models/               # Pydantic models for runtime validation
└── validate_*.py         # Validation tools and fixtures
```

**Event Schemas** (in `contracts/events/` and `contracts/schemas/json/`):
- **PriceTick@1.0**: Market price data
- **IndicatorVector@1.1**: Technical indicator results
- **Signal@1.0**: Trading signals with confidence scores
- **OrderIntent@1.2**: Risk-approved orders ready for execution
- **ExecutionReport@1.0**: Broker execution results
- **CalendarEvent@1.0**: Economic calendar events
- **ReentryDecision@1.0**: Matrix-based re-entry decisions

**Data Integrity**: All CSV files follow atomic write policies with checksums and sequence validation. Schema validation is enforced in CI/CD pipeline and at runtime.

### Shared Libraries

**Shared Re-entry Library** (`shared/reentry/`):
- **hybrid_id.py**: Compose, parse, and validate hybrid IDs with cross-language parity (Python/MQL4)
- **vocab.py**: Canonical vocabulary management for trading outcomes, durations, proximity states
- **indicator_validator.py**: Indicator record validation against JSON schemas

**Usage**:
```python
from shared.reentry import compose, parse, validate_key, comment_suffix_hash

# Compose hybrid ID
hybrid_id = compose('W1', 'QUICK', 'AT_EVENT', 'CAL8_USD_NFP_H', 'LONG', 1)

# Parse and validate
components = parse(hybrid_id)
is_valid = validate_key(hybrid_id)
comment_hash = comment_suffix_hash(hybrid_id)  # 6-char deterministic hash
```

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
**Contract Tests**: Consumer-driven contract testing with Pact-like semantics (`tests/contracts/`)
**Integration Tests**: End-to-end pipeline testing with Docker Compose
**Service Tests**: Health checks and API endpoint validation
**Cross-Language Parity Tests**: Validate Python/MQL4 shared library consistency
**Property-Based Tests**: Hypothesis-driven contract validation with random data generation
**Scenario Tests**: Complete trading flow validation with mock services

**Contract Testing Framework**:
- **Consumer-Driven Contracts**: Services define contracts from consumer perspective
- **Provider Verification**: Providers verify they satisfy consumer contracts
- **Scenario Testing**: End-to-end trading workflows (signal generation → execution)
- **Property-Based Testing**: Domain-specific data generation and invariant testing
- **Flexible Matching**: Regex, type, numeric, datetime, and array matchers

**Test Structure**:
```
tests/contracts/
├── framework/                    # Pact-like contract testing framework
│   └── contract_testing.py      # Core testing infrastructure
├── consumer/                     # Consumer contract definitions
│   ├── test_signal_generator_contracts.py   # Signal generator contracts
│   └── test_execution_engine_contracts.py   # Execution engine contracts
├── provider/                     # Provider contract verification
│   └── test_risk_manager_provider.py        # Risk manager provider tests
├── scenarios/                    # End-to-end scenario tests
│   └── test_trading_flow_scenarios.py       # Complete trading workflows
├── properties/                   # Property-based testing
│   └── test_property_based_contracts.py     # Hypothesis-based validation
├── fixtures/                     # Golden test data and shared fixtures
├── conftest.py                   # Pytest configuration and fixtures
└── README.md                     # Contract testing documentation
```

**Test Configuration Features**:
- Async testing with `pytest-asyncio`
- Coverage reporting across all services  
- Parallel test execution per service
- Contract validation in CI/CD pipeline
- Property-based testing with Hypothesis framework
- Consumer-driven contract verification workflow
- Scenario-based integration testing with mock services

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
**Single Source of Truth**: Contract registry in `contracts/` and shared libraries in `shared/` are canonical
**Defensive Posture**: Fail closed on integrity errors, validate all inputs
**Explicit Fallbacks**: Tiered parameter resolution with audit trails

## Production Readiness & Gap Management

### Gap Analysis Framework
The system includes comprehensive production readiness documentation in `docs/gaps/`:
- **Gap Register**: Active gap tracking with Risk Priority Numbers (RPN scoring)
- **FMEA Analysis**: Failure Mode and Effects Analysis with mitigation strategies
- **SLOs**: Service Level Objectives with specific trading system metrics
- **Invariants**: 6 executable system specifications with monitoring

### Key Production Gaps (Current)
- **G-003**: Position reconciliation (RPN: 105) - *Critical priority*
- **G-001**: Signal TTL enforcement (RPN: 96) - *High priority*
- **G-004**: Duplicate order prevention (RPN: 48) - *Medium priority*

### Service Level Objectives
- **System Availability**: 99.9% uptime during market hours (6 AM - 6 PM EST)
- **Price Feed Latency**: p95 < 100ms from MT4/DDE to ingestion
- **Signal Generation**: p95 < 500ms from price tick to signal
- **Order Execution**: p95 < 2s from signal to broker submission

### Operational Templates
- Incident response template with escalation procedures
- Post-mortem template with root cause analysis framework
- Game day runbook for disaster recovery testing

## Service Port Mapping

**Production Ports** (Docker Compose):
- **gui-gateway**: 8080 (main API gateway)
- **data-ingestor**: 8081 (price feed ingestion)
- **indicator-engine**: 8082 (technical indicators)
- **signal-generator**: 8083 (trading signals)
- **risk-manager**: 8084 (risk validation)
- **execution-engine**: 8085 (order execution)
- **calendar-ingestor**: 8086 (economic calendar)
- **reentry-matrix-svc**: 8087 (re-entry decisions)
- **reporter**: 8088 (reporting and analytics)

**Infrastructure Services**:
- **Redis**: 6379 (message bus)
- **PostgreSQL**: 5432 (persistent storage)
- **Prometheus**: 9090 (metrics)
- **Grafana**: 3000 (monitoring dashboards)

## Configuration Management

**Environment Variables**: Service configuration via environment variables
**Docker Compose**: Local development environment configuration  
**Secrets**: Never commit sensitive data; use environment variables or secret management
**Feature Flags**: Configuration-driven feature enablement per service
**Health Checks**: All services expose `/healthz` (liveness) and `/readyz` (readiness) endpoints

## Data Integrity & Atomic Operations

### CSV Atomic Write Policy

All CSV files follow strict atomic write procedures defined in `contracts/policies/csv_atomic_write.md`:

1. **Temporary File Creation**: Write to `*.tmp` file first
2. **Data Validation**: Compute SHA-256 checksums for integrity
3. **Metadata Columns**: Required `file_seq` (monotonic) and `checksum_sha256` fields
4. **Atomic Rename**: `fsync()` then rename to final filename
5. **Sequence Validation**: Monotonically increasing `file_seq` for ordering

**Implementation**:
```python
from contracts.models.csv_models import BaseCSVModel

# All CSV models inherit atomic write capabilities
class TradeResult(BaseCSVModel):
    # Automatic checksum computation and validation
    def verify_checksum(self) -> bool:
        return self.checksum_sha256 == self.compute_checksum()
```

### Hybrid ID System

**Format**: `{OUTCOME}_{DURATION}_{PROXIMITY}_{CALENDAR}_{DIRECTION}_{GENERATION}[_{SUFFIX}]`

- **Cross-Language Consistency**: Identical results from Python and MQL4 implementations
- **Chain Enforcement**: O(1)→R1(2)→R2(3) re-entry progression
- **Comment Suffixes**: Deterministic 6-character hashes for MT4 trade comments
- **Vocabulary Validation**: All tokens validated against canonical specifications
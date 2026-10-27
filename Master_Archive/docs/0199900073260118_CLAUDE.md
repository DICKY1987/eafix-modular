---
doc_id: DOC-CONFIG-0050
---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the **EAFIX Modular Trading System** - an enterprise-grade financial trading platform with containerized microservices. The system has been transformed from a monolithic application into a production-ready architecture with comprehensive enterprise capabilities.

**Core Architecture**: Event-driven microservices with enterprise service foundation
**Language**: Python 3.11 with Poetry workspace management
**Enterprise Framework**: BaseEnterpriseService (services/common/base_service.py) provides standardized observability
**Deployment**: Docker containers with Kubernetes support, comprehensive monitoring
**Security**: Blocking security gates with SAST, SCA, and vulnerability scanning via pre-commit hooks
**Task Runners**: Both Makefile and Taskfile.yml supported (use either `make` or `task` commands)

## Essential Development Commands

### Project Setup
```bash
# Install dependencies and setup development environment
poetry install                    # Installs all dependencies from pyproject.toml
poetry install --with security    # Also install security tools (bandit, safety, semgrep)
poetry run pre-commit install     # Install git pre-commit hooks

# Start enterprise monitoring stack (Prometheus, Grafana, AlertManager)
docker compose -f deploy/compose/docker-compose.yml up -d
# or: make docker-up (or: task up)

# Verify enterprise infrastructure
make contracts-validate-full

# Format code before committing
make format  # Runs black and isort on services/
# or: task format

# Lint code
make lint    # Runs flake8 and mypy on services/*/src
# or: task lint
```

### Enterprise Service Development
```bash
# Create new service with enterprise capabilities (2-line setup)
cd services/<service-name>
./scripts/integrate-enterprise-service.sh

# Validate enterprise integration
./scripts/validate-enterprise-service.sh

# Test enterprise capabilities
pytest tests/e2e/test_enterprise_system.py
```

### Testing & Quality Gates
```bash
# Run comprehensive test suite with 80% coverage enforcement (BLOCKING)
make test-all  # or: task test
# This runs: pytest with --cov-fail-under=80 and --cov-branch enabled

# Pre-commit hooks (runs automatically on git commit, or manually):
poetry run pre-commit run --all-files
# Includes: ruff, black, isort, mypy --strict, detect-secrets, markdownlint, yamllint

# Run security scanning (use pyproject.toml security group)
poetry install --with security
poetry run bandit -r services/ --severity-level medium --confidence-level medium
poetry run safety check --short-report
poetry run semgrep --config=auto services/ --error --strict

# Contract validation (critical for microservices integration)
make contracts-validate-full  # Comprehensive: JSON schemas + CSV artifacts + re-entry helpers
make contracts-test           # Run contract and scenario tests with pytest
make contracts-compat         # Schema compatibility checking
make contracts-properties     # Property-based contract testing

# Service-specific testing
cd services/<service-name> && pytest --cov=src --cov-fail-under=80

# Test markers available (see pyproject.toml):
pytest -m unit          # Fast, isolated unit tests
pytest -m integration   # Integration tests with external deps
pytest -m e2e          # End-to-end system tests
pytest -m security     # Security-focused tests
pytest -m performance  # Performance benchmarks
```

### Domain Knowledge Integration
```bash
# Validate reentry system integration
make reentry-validate

# Process P_ folder specifications
cd P_project_knowledge && python apf_apply_stub.py
cd P_scripts && python validate_keys_cli.py

# GUI development workflow
cd P_GUI && python expiry_indicator_service.py
cd P_GUI && python friday_vol_indicator.py
```

## Enterprise Architecture

### Architectural Decision Records
**Key ADR**: `docs/adr/ADR-0001-service-decomposition.md` documents the microservices decomposition strategy.

**Core Principles** (from ADR-0001):
- **Determinism & Idempotence**: Identical inputs must produce identical outputs
- **Single Source of Truth**: All components validate against canonical schemas (contracts/)
- **Defensive Posture**: Fail closed on integrity errors, suppress decisions until healthy
- **Explicit Fallbacks**: Tiered parameter resolution with audit trails

**Communication Patterns**:
- **Asynchronous Events** (Redis pub/sub): data-ingestor → indicator-engine → signal-generator
- **Synchronous HTTP APIs**: For risk validation, order placement, UI operations
- **Event Sourcing**: All state changes captured as immutable events with versioned schemas

### BaseEnterpriseService Foundation
The system uses an inheritance-based enterprise architecture where all services inherit from `services/common/base_service.py`:

```python
from services.common.base_service import BaseEnterpriseService

class YourService(BaseEnterpriseService):
    def __init__(self):
        super().__init__(service_name="your-service")

    async def startup(self): # Required implementation
        # Service-specific startup logic

    async def shutdown(self): # Required implementation
        # Graceful shutdown logic

    async def health_check(self) -> dict: # Required implementation
        # Service health validation
```

**Enterprise Capabilities Provided:**
- **RED Metrics**: Request rate, error rate, duration automatically collected
- **Feature Flags**: Environment-based feature toggles with audit logging
- **Health Checks**: `/healthz`, `/readyz`, `/metrics` endpoints
- **Security**: Structured logging with correlation IDs
- **Observability**: Prometheus metrics, Grafana dashboards

### Service Architecture Pattern
Each service follows this structure:
```
services/<service-name>/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── main_enterprise.py      # Enterprise service implementation
│   └── <service>_logic.py     # Business logic
├── tests/
│   ├── unit/                  # Unit tests (70% of test pyramid)
│   ├── integration/           # Integration tests (20%)
│   └── e2e/                   # End-to-end tests (10%)
├── Dockerfile                 # Production container
└── requirements.txt           # Service dependencies
```

## Domain Knowledge Architecture

### P_ Folder Ecosystem
The system includes comprehensive domain knowledge in P_ folders:

- **P_project_knowledge/**: Core trading system specifications and architecture
- **P_GUI/**: Advanced currency strength and conditional probability UI specifications
- **P_techspec/**: Technical specifications, integration guides, and system documentation
- **P_INDICATOR_REENTRY/**: Reentry decision matrix framework and economic calendar integration
- **P_mql4/**: MQL4 integration components for MetaTrader connectivity
- **P_positioning_ratio_index/**: Position sizing and ratio calculation systems
- **P_reentry_helpers/**: Reentry system utilities and validation logic

### Contract System Integration
The system uses a centralized contract registry with domain-driven schemas:

```bash
# Validate all contracts (JSON schemas + CSV artifacts)
make contracts-validate-full

# Test contract compatibility across services
make contracts-compat

# Run property-based contract testing
make contracts-properties
```

**Key Contract Files:**
- `contracts/schemas/json/`: JSON Schema definitions for events
- `P_csv_schemas/`: CSV schema definitions for data interchange
- `P_INDICATOR_REENTRY/`: Domain-specific indicator and reentry schemas

## Microservices Architecture

**Active Services** (in services/ directory):
- **calendar-downloader**: Automated ForexFactory calendar download
- **calendar-ingestor**: Economic calendar data processing and P_techspec integration
- **compliance-monitor**: Regulatory compliance monitoring service
- **dashboard**: Dashboard frontend components
- **dashboard-backend**: Real-time trading dashboard with WebSocket streaming
- **data-ingestor**: Normalizes broker price feeds from MT4/DDE
- **data-validator**: Data quality validation service
- **event-gateway**: Event routing and transformation gateway
- **flow-monitor**: Signal flow monitoring and observability
- **flow-orchestrator**: Workflow orchestration and coordination
- **gui-gateway**: Operator UI API gateway implementing P_GUI specifications
- **indicator-engine** / **indicators**: Technical indicator computation (P_INDICATOR_REENTRY specs)
- **reentry-engine**: Re-entry logic engine
- **reentry-matrix-svc**: Multi-dimensional decision matrix from P_INDICATOR_REENTRY
- **telemetry-daemon**: Centralized telemetry collection and aggregation
- **transport-router**: Message routing and transport layer

**Enterprise Support:**
- **common/**: BaseEnterpriseService foundation (services/common/base_service.py) and shared utilities
- **scripts/**: Service integration, validation, chaos engineering, and replay testing tools

## Production Deployment

### Docker Operations
```bash
# Start all services
make docker-up  # or: task up
# Runs: docker compose -f deploy/compose/docker-compose.yml up -d --build

# Stop all services
make docker-down  # or: task down

# View logs
make docker-logs  # or: task docker-logs
# Runs: docker compose logs -f

# Build service images
make build  # or: task build

# View Docker status
docker compose -f deploy/compose/docker-compose.yml ps --format table
```

### Enterprise Monitoring Stack
```bash
# Deploy complete observability infrastructure
docker compose -f deploy/compose/monitoring.yml up -d
# Includes: Prometheus, Grafana, AlertManager with business-specific alerts

# Access monitoring interfaces
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# AlertManager: http://localhost:9093
```

### Security & Compliance
The system enforces enterprise security through pre-commit hooks and CI/CD gates:

- **Pre-commit Hooks** (.pre-commit-config.yaml):
  - **Code Quality**: Ruff, Black, isort for consistent formatting
  - **Type Safety**: MyPy with --strict mode enabled
  - **SAST**: Bandit static analysis (skips test assertions)
  - **Secret Scanning**: detect-secrets with baseline (.secrets.baseline)
  - **Contract Validation**: Automatic schema validation on contract changes
  - **Docker Security**: Image digest pinning verification (scripts/check-docker-digests.sh)
- **SCA**: Safety dependency vulnerability scanning
- **Semantic Analysis**: Semgrep code pattern analysis
- **Coverage Enforcement**: 80% test coverage requirement with branch coverage (blocking in pyproject.toml)

### Container Security
All services use hardened production containers:
```dockerfile
# Multi-stage builds with security scanning
# Non-root user execution
# Health checks with proper timeouts
# Signal handling with dumb-init
# Minimal attack surface with slim base images
```

## Development Workflow

### Enterprise Service Integration
1. **Create Service**: Use existing service as template or run integration script
2. **Inherit BaseEnterpriseService**: Get all enterprise capabilities automatically
3. **Implement Abstracts**: `startup()`, `shutdown()`, `health_check()` methods
4. **Validate Integration**: Run enterprise validation suite
5. **Deploy**: Automatic enterprise monitoring and security scanning

### Domain-Driven Development
1. **Consult P_ Specifications**: Check P_techspec/ for implementation requirements
2. **Validate Contracts**: Ensure schema compatibility with contract registry
3. **Implement Business Logic**: Use P_project_knowledge/ for domain understanding
4. **Test Integration**: Validate against P_INDICATOR_REENTRY specifications
5. **UI Integration**: Follow P_GUI/ specifications for frontend integration

### Quality Gates
All code must pass enterprise quality gates before commit and in CI:

**Pre-commit (automatic on `git commit`):**
```bash
# Install hooks first (done in setup)
poetry run pre-commit install

# Manual execution
poetry run pre-commit run --all-files
```

**Test Gates (blocking):**
```bash
# 80% coverage enforcement (blocking) - configured in pyproject.toml
make test-all  # Fails if coverage < 80% or branch coverage insufficient

# Contract validation (blocking on contract changes)
make contracts-validate-full

# Integration testing
pytest tests/integration/ -v -m integration

# Security scanning (should be run before release)
poetry install --with security
poetry run bandit -r services/ --severity-level medium
poetry run safety check --short-report
```

**CI Pipeline Gates:**
1. Pre-commit hooks (all)
2. Test suite with coverage (80% threshold)
3. Contract validation
4. Security scanning (SAST + SCA)
5. Docker image building and digest verification

## Configuration Management

### Enterprise Feature Flags
Services support environment-based feature configuration:
```bash
# Enable enterprise features
ENABLE_ENTERPRISE_METRICS=true
ENABLE_FEATURE_FLAGS=true
ENABLE_AUDIT_LOGGING=true

# Configure observability
PROMETHEUS_PORT=8001
GRAFANA_DATASOURCE=prometheus
ALERT_WEBHOOK_URL=http://alertmanager:9093/webhook
```

### Service Configuration Pattern
```python
# Standard enterprise configuration pattern
from services.common.base_service import EnterpriseConfig

config = EnterpriseConfig(
    service_name="your-service",
    enable_metrics=True,
    enable_feature_flags=True,
    prometheus_port=8001
)
```

## Integration Points

### MQL4 Integration
The system includes comprehensive MQL4 integration through P_mql4/:
```bash
# Validate MQL4 helpers
cd P_mql4 && mql4_compiler ReentryHelpers.mq4

# Test MQL4 bridge functionality
python P_tests/test_mql4_integration.py
```

### Economic Calendar Integration
Economic events are processed through calendar-ingestor with P_techspec specifications:
```bash
# Test calendar integration
cd services/calendar-ingestor && python -m src.main

# Validate economic event schemas
make contracts-validate P_INDICATOR_REENTRY/
```

### GUI System Integration
The GUI system follows P_GUI specifications for advanced trading interfaces:
```bash
# Test GUI service components
cd P_GUI && python expiry_indicator_service.py
cd P_GUI && python test_friday_vol_indicator.py

# Validate GUI contract integration
python P_GUI/test_friday_vol_signal.py
```

## Quick Reference

### Key Configuration Files
- **pyproject.toml**: Poetry workspace configuration, dependencies, test configuration (80% coverage threshold), tool configs (black, isort, mypy, bandit, pytest)
- **.pre-commit-config.yaml**: Pre-commit hook configuration (ruff, black, isort, mypy --strict, detect-secrets, contract validation)
- **Makefile**: Primary task runner with comprehensive commands (use `make help` to see all targets)
- **Taskfile.yml**: Alternative task runner (supports Windows better, use `task --list`)
- **deploy/compose/docker-compose.yml**: Docker Compose service definitions
- **contracts/**: Canonical schemas (JSON and CSV) for all events and data interchange
- **VERSION**: Single source of truth for version number

### Important Directories
- **services/**: All microservice implementations
- **services/common/base_service.py**: BaseEnterpriseService foundation class
- **contracts/**: Schema definitions and validation scripts
- **P_*/**: Domain knowledge folders (specifications, GUI, indicators, reentry logic, MQL4)
- **docs/adr/**: Architectural Decision Records
- **docs/runbooks/**: Operational runbooks and incident response procedures
- **docs/gaps/**: Production readiness gaps, SLOs, and FMEA
- **scripts/**: Automation scripts (replay, chaos, integration, validation)
- **tests/**: Test suites (contracts/, e2e/, integration/)
- **shared/**: Shared libraries (reentry helpers, common utilities)

### Getting Help
```bash
# View all Makefile targets
make help

# View Taskfile targets
task --list

# Check production readiness gaps
make gaps-check

# Access runbooks
make runbooks
```

## Operations & Runbooks

### Emergency Operations
```bash
# Emergency trading halt (critical)
make emergency-stop
# Sends POST to http://localhost:8080/emergency/stop-trading

# Emergency system restart (requires CONFIRM)
make emergency-restart
# Stops all services, waits 10s, restarts, runs health check

# Comprehensive health check
make health-check
# Checks all service ports (8080-8088), system resources, Docker status, DB, Redis

# View available runbooks
make runbooks
# Opens docs/runbooks/index.md
# Key runbooks: incident-response.md, trading-incidents.md, common-issues.md, escalation-procedures.md
```

### Performance Testing
```bash
# Tick replay performance testing
make replay-test
# Runs: python scripts/replay/replay_ticks.py scripts/replay/sample_ticks.csv --verbose

# k6 load testing (requires k6 installed)
make perf-k6 K6_TARGET_URL=http://localhost:8080/healthz K6_VUS=5 K6_DURATION=30s

# Locust load testing (requires locust: pip install locust)
make perf-locust LOCUST_HOST=http://localhost:8080 LOCUST_USERS=20 LOCUST_DURATION=1m
```

### Chaos Engineering
```bash
# Chaos testing tools available in scripts/chaos/
# Use to test system resilience and failure modes
```

## Friday Morning Updates Huey P Integration

### Enhanced Signal Flow Testing
The system includes comprehensive signal flow testing from the "Friday Morning Updates Huey P" integration:

**Friday Updates Location**: `Friday Morning Updates Huey P/` directory contains:
- `UPDARE P_Testing_signal/`: Signal flow testing enhancements
- `UPDATE_Economic_calendar/`: Economic calendar updates
- `UPDATEP_Currency strengthen indicator/`: Currency strength indicator improvements
- `UPDATP_Python_huey P_dashboard/`: Python Huey dashboard updates

### Signal Flow Testing Framework
```bash
# End-to-end signal flow testing
make signal-flow-test              # Complete signal validation from source to MT4
make signal-simulation             # Indicator signal simulation and backtesting
make calendar-simulation           # Economic calendar event simulation
make manual-test-panel            # Interactive testing control panel GUI
make test-signal-flow-all         # Run all signal flow tests

# Individual testing components
cd tests/signal_flow_testing && python signal_flow_tester.py --mt4-data "path/to/mt4"
cd tests/signal_flow_testing && python manual_testing_control_panel.py
```

### Economic Calendar Automation
```bash
# Calendar downloader service
cd services/calendar-downloader && python -m src.main

# Manual calendar download trigger
curl -X POST http://localhost:8080/download/manual

# Calendar processing validation
cd P_INDICATOR_REENTRY && python reentry_helpers_cli.py --validate-calendar
```

### Currency Strength Analysis
```bash
# Currency strength calculation
cd services/indicator-engine && python -m src.currency_strength.strength_calculator

# Multi-timeframe strength matrix
python -c "from services.indicator_engine.src.currency_strength.strength_calculator import CurrencyStrengthCalculator; calc = CurrencyStrengthCalculator(); print('Currency strength system loaded')"
```

### Dashboard Modernization
```bash
# Start dashboard backend service
cd services/dashboard-backend && python -m src.main

# Access real-time dashboard
# WebSocket: ws://localhost:8080/ws
# REST API: http://localhost:8080/api/dashboard/data

# Traditional GUI dashboard (if needed)
cd P_GUI && python tkinter_dashboard_gui.py
```

### Integration with Existing Enterprise Framework
All Friday Morning Updates components inherit from BaseEnterpriseService:
- **Automatic RED metrics**: Request rate, error rate, duration
- **Enterprise monitoring**: Prometheus metrics, health checks
- **Security compliance**: SAST, SCA, vulnerability scanning
- **Observability**: Grafana dashboards, AlertManager integration

## DAG-based Verification Framework

### Workstreams and Quality Gates
The system includes a DAG-based verification framework for complex multi-stage processing:

```bash
# Validate DAG configuration
make dag-validate

# Generate DAG execution report
make dag-report

# List workstreams
make dag-workstreams

# List verification patterns
make dag-patterns

# List quality gates
make dag-gates
```

**Key DAG Components:**
- **dag/config/**: Quality gate definitions and DAG configuration
- **dag/workstreams/**: Workstream definitions with SLA budgets
- **dag/patterns/**: Verification pattern registry
- **dag/prompts/**: Prompt templates for verification tasks
- **dag/EXECUTION_REPORT.md**: DAG execution summary and metrics

This enterprise-grade trading system combines production-ready infrastructure with comprehensive domain knowledge to deliver a complete financial trading platform.

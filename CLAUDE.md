# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the **EAFIX Modular Trading System** - an enterprise-grade financial trading platform with 9 containerized microservices. The system has been transformed from a monolithic application into a production-ready architecture with comprehensive enterprise capabilities.

**Core Architecture**: Event-driven microservices with enterprise service foundation
**Language**: Python 3.11 with Poetry workspace management
**Enterprise Framework**: BaseEnterpriseService provides 200x efficiency multiplier
**Deployment**: Docker containers with Kubernetes support, comprehensive monitoring
**Security**: Blocking security gates with SAST, SCA, and vulnerability scanning

## Essential Development Commands

### Project Setup
```bash
# Install dependencies and setup development environment
poetry install
poetry run pre-commit install

# Start enterprise monitoring stack (Prometheus, Grafana, AlertManager)
docker compose -f deploy/compose/docker-compose.yml up -d

# Verify enterprise infrastructure
make contracts-validate-full
```

### Enterprise Service Development
```bash
# Create new service with enterprise capabilities (2-line setup)
cd services/<service-name>
./scripts/integrate-enterprise-service.sh
# Then inherit BaseEnterpriseService and implement 3 abstract methods

# Validate enterprise integration
./scripts/validate-enterprise-service.sh

# Test enterprise capabilities
pytest tests/e2e/test_enterprise_system.py
```

### Testing & Quality Gates
```bash
# Run comprehensive test suite with 80% coverage enforcement
make test-all

# Run security scanning (blocking gates)
make security-scan
bandit -r services/ --severity-level medium --confidence-level medium
safety check --short-report
semgrep --config=auto services/ --error --strict

# Contract validation (critical for microservices integration)
make contracts-validate-full
make contracts-test

# Service-specific testing
cd services/<service-name> && pytest --cov=src --cov-fail-under=80
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

### BaseEnterpriseService Foundation
The system uses a inheritance-based enterprise architecture where all services inherit from `services/common/base_service.py`:

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

**Core Services (9 total):**
- **data-ingestor**: Normalizes broker price feeds from MT4/DDE with enterprise monitoring
- **indicator-engine**: Computes technical indicators using P_INDICATOR_REENTRY specifications
- **signal-generator**: Applies trading rules with P_GUI conditional probability systems
- **risk-manager**: Position sizing using P_positioning_ratio_index calculations
- **execution-engine**: Broker integration with enterprise audit trails
- **calendar-ingestor**: Economic calendar data with P_techspec integration patterns
- **reentry-matrix-svc**: Multi-dimensional decision matrix from P_INDICATOR_REENTRY
- **reporter**: Enterprise metrics and P&L reporting with observability integration
- **gui-gateway**: Operator UI gateway implementing P_GUI specifications

**Enterprise Support Services:**
- **common/**: BaseEnterpriseService foundation and shared enterprise utilities
- **scripts/**: Automated service integration and validation tools

## Production Deployment

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
The system enforces enterprise security through CI/CD gates:

- **SAST**: Bandit static analysis security testing
- **SCA**: Safety dependency vulnerability scanning
- **Semantic Analysis**: Semgrep code pattern analysis
- **Secret Scanning**: Automated detection of committed secrets
- **Coverage Enforcement**: 80% test coverage requirement with branch coverage

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
All code must pass enterprise quality gates:
```bash
# Security gates (blocking)
make security-scan

# Test coverage enforcement (blocking)
pytest --cov=src --cov-fail-under=80

# Contract validation (blocking)
make contracts-validate-full

# Integration testing (required)
pytest tests/integration/ -v
```

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

This enterprise-grade trading system combines production-ready infrastructure with comprehensive domain knowledge to deliver a complete financial trading platform.

## Friday Morning Updates Huey P Integration

### New Enterprise Services
The system has been enhanced with Friday Morning Updates components:

**Enhanced Services (11 total now):**
- **calendar-downloader**: Automated ForexFactory calendar download with enterprise monitoring
- **dashboard-backend**: Real-time trading dashboard with WebSocket streaming and BaseEnterpriseService

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
python -c "from services.indicator_engine.src.currency_strength.strength_calculator import CurrencyStrengthCalculator; calc = CurrencyStrengthCalculator(); print(Currency strength system loaded)"
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

This enhanced system now provides complete trading workflow automation from calendar ingestion through signal generation, testing, and real-time dashboard visualization.

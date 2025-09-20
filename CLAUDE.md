# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **EAFIX Trading System** - a professional trading platform that combines Python intelligence with MT4 execution:

- **EAFIX Core**: Complete trading system with Guardian protection (`src/eafix/`)
- **Trading CLI**: Professional command-line interface for system management
- **Signal Processing**: Advanced technical analysis and pattern recognition
- **Guardian System**: Automated risk management and account protection
- **MT4 Integration**: Direct broker connectivity and order execution

## Common Development Commands

### Testing
```bash
# Run all tests with unittest
python -m unittest discover -s tests -v

# Run tests with pytest (if available)
pytest -q --cov=src --cov-report=term-missing --cov-fail-under=80

# Run specific test file
python -m unittest tests.test_cli.py -v
pytest tests/test_cli.py -v
```

### Code Quality
```bash
# Run all pre-commit hooks (ruff, black, isort, mypy, bandit, yamllint, etc.)
pre-commit run --all-files

# Manual linting and formatting
ruff check src/ tests/ --fix
black src/ tests/
isort src/ tests/ --profile black
mypy src/ --ignore-missing-imports

# Security scanning
bandit -r src/ -f json -o bandit-report.json
```

### Build and Package
```bash
# Install in development mode
pip install -e .

# With optional dependencies
pip install -e .[yaml]

# Build package
python -m build
```

### CLI Usage
```bash
# EAFIX Trading System CLI
python -m eafix.apps.cli.main status
python -m eafix.apps.cli.main trade signals --active --symbol EURUSD
python -m eafix.apps.cli.main guardian status
python -m eafix.apps.cli.main system health --detailed
python -m eafix.apps.cli.main analyze performance --period 30d

# Additional trading commands
python -m eafix.apps.cli.main setup install-dependencies
python -m eafix.apps.cli.main setup configure --broker-settings
python -m eafix.apps.cli.main launch  # Launch GUI interface

# APF (Atomic Process Framework) commands
python -m eafix.apps.cli.main apf status
python -m eafix.apps.cli.main apf run --workflow trading-pipeline
```

### Installation
```bash
# Local editable install
pip install -e .

# With YAML support for enhanced job management
pip install -e .[yaml]

# Use installed CLI
eafix status
eafix trade positions --active
```

## Architecture

### Core Structure
- `src/eafix/`: Trading system core with CLI commands (trading, guardian, system, analysis, setup)
- `src/contracts/`: Trading data models (Signal, Pricetick, OrderIntent, Executionreport, etc.)
- `src/integrations/`: External service connectors (GitHub, Slack, Teams, Jira)
- `src/websocket/`: Event broadcasting and connection management (WebSocket + FastAPI)
- `src/compliance/`: Regulatory compliance and reporting services
- `src/observability/`: Metrics, tracing, and JSON logging
- `src/idempotency/`: State management, queues, and consumer patterns
- `workflows/`: Multi-stream workflow definitions and deployment configurations

### Key Components
- **Health Checker**: System status monitoring (`src/eafix/system/health_checker.py:1`)
- **Trading Commands**: Core trading operations (`src/eafix/apps/cli/commands/trading.py:1`)
- **Guardian System**: Risk management and protection (`src/eafix/apps/cli/commands/guardian.py:1`)
- **System Management**: Health and diagnostics (`src/eafix/apps/cli/commands/system.py:1`)
- **Event Broadcasting**: WebSocket real-time updates (`src/websocket/event_broadcaster.py:1`)
- **Integration Manager**: External service coordination (`src/integrations/integration_manager.py:1`)
- **Compliance Service**: Regulatory reporting (`src/compliance/service.py:1`)

### Configuration
- `config/tools.yaml`: Tool registry and health monitoring definitions
- `config/self_healing/self_healing.yaml`: Self-healing policies and recovery strategies
- `config/policies/policy.yaml`: System-wide operational policies
- `config/profiles/dev.yaml`: Development environment configuration
- `config/integrations.json`: External service integration settings
- `config/failover_maps.yaml`: Failover and redundancy configurations

### Multi-Stream Workflow
The system supports parallel development workflows:
- Stream-based phase execution with conflict prevention
- Kubernetes deployment configurations in `workflows/TONIGHT9325DEPLOY/`
- ArgoCD integration for GitOps deployment patterns
- Tool health monitoring with snapshot generation (`python scripts/ipt_tools_ping.py`)

## Development Workflow

1. **Pre-commit Hooks**: All changes must pass comprehensive quality gates:
   - Code formatting (black, isort, ruff)
   - Type checking (mypy)
   - Security scanning (bandit, detect-secrets)
   - YAML/JSON validation (yamllint)
   - Markdown linting (markdownlint)
2. **Testing**: Maintain 80%+ test coverage with unittest/pytest
3. **Build System**: Uses pyproject.toml with setuptools build backend
4. **Package Structure**: Editable installs with optional dependencies (PyYAML)
5. **CI/CD**: GitHub Actions with automated testing and deployment

## Scripts

Key PowerShell scripts in `scripts/`:
- `emit_tokens.ps1`: Token usage tracking
- `report_costs.ps1`: Cost analysis and reporting
- `install_hooks.ps1`: Git hooks installation
- `run_workflow.ps1`: Workflow execution

## Dependencies

- **Core**: Python 3.9+, typer, FastAPI, uvicorn, pydantic, rich
- **Trading**: CrewAI, LangGraph, LangChain (Anthropic, Google GenAI, Community)
- **Data**: SQLModel, Redis, PyYAML (optional)
- **Monitoring**: prometheus-client, structlog
- **Development**: pre-commit, ruff, black, isort, mypy, bandit, pytest, coverage
- **Security**: detect-secrets, gitleaks, pip-audit, semgrep
- **Optional**: docker, hydra-core, hypothesis, jsonschema
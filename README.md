# EAFIX Trading System

![CI](https://github.com/DICKY1987/eafix-modular/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-80%25%2B-brightgreen)

**EAFIX Trading System** is a production-ready trading platform that combines Python intelligence with MT4 execution power. The system features advanced Guardian protection mechanisms, sophisticated signal generation, and comprehensive risk management for professional forex trading.

The platform is designed for traders who demand reliability, performance, and intelligent automation in their trading operations.

## Quick start

You can run the trading system CLI directly with the Python interpreter without any
installation steps. The examples below assume you are executing commands in
the repository root.

```bash
# Check trading system status
python -m eafix.apps.cli.main status

# View active trading signals
python -m eafix.apps.cli.main trade signals --active

# Monitor Guardian protection system
python -m eafix.apps.cli.main guardian status
```

If you prefer to install the package into your current environment, you can
use a local editable install via `pip`. This step is optional and not
required to run the examples above:

```bash
pip install -e .
eafix status
```

The editable install will register a console script entry point named
`eafix`. This provides access to all trading system functionality through
a unified command-line interface.

## Trading System Features

The EAFIX system provides comprehensive trading functionality:

**Core Trading Operations:**
- Real-time signal generation and analysis
- MT4 integration for order execution
- Advanced risk management and position sizing
- Multi-timeframe technical analysis

**Guardian Protection System:**
- Automated risk monitoring and intervention
- Account protection mechanisms
- Emergency position closure capabilities
- Drawdown and exposure limits

**System Management:**
- Health monitoring and diagnostics
- Configuration management
- Performance analytics and reporting
- Integration with external services (Slack, Teams, Jira)

**Command Examples:**
```bash
# Trading operations
eafix trade signals --symbol EURUSD --export
eafix trade positions --active

# Guardian system
eafix guardian enable --max-drawdown 5.0
eafix guardian rules --list

# System management
eafix system health --detailed
eafix analyze performance --period 30d
```

## Architecture Overview

The EAFIX Trading System follows a modular architecture designed for reliability and maintainability:

**Core Components:**
- `src/eafix/` - Main trading system with signal generation, indicators, and system management
- `src/contracts/` - Trading data models (Signal, PriceTick, OrderIntent, etc.)
- `src/integrations/` - External service connectors (GitHub, Slack, Teams, Jira)
- `src/websocket/` - Event broadcasting and real-time communication
- `src/compliance/` - Regulatory compliance and reporting

**Key Modules:**
- **Signal Processing**: Advanced technical analysis and pattern recognition
- **Guardian System**: Risk management and account protection
- **MT4 Integration**: Direct broker connectivity and order execution
- **Event System**: WebSocket-based real-time updates
- **Health Monitoring**: System diagnostics and performance tracking

## Tool Registry and Event Bus

- Tool registry: define tools in `config/tools.yaml`.
- Probe tools and write health snapshot: `python scripts/ipt_tools_ping.py` → `state/tool_health.json`.
- Event bus (FastAPI + WebSocket): `uvicorn services.event_bus.main:app --reload` then publish JSON to `POST /publish`; subscribers connect to `/ws`.

Hooks setup

- Configure Git to use bundled hooks (merge-safety, optional license gate):
  - POSIX: `bash scripts/install_hooks.sh`
  - PowerShell: `./scripts/install_hooks.ps1`

## Development guide

Development workflows emphasise high code quality, reproducibility and clear
communication. The repository includes a commit message template
(`.gitmessage.txt`) and a sample CI workflow (`.github/workflows/ci.yml`)
that installs common development tools such as `pre-commit`, `ruff` and
`pytest`. Although these tools may not be available in all environments,
they are preconfigured so that continuous integration (CI) pipelines can
enforce formatting, linting, static type checking and unit test execution.

To run the test suite locally using the built‑in Python `unittest` runner:

```bash
python -m unittest discover -s tests -v
```

## Cost Reports

- Emit tokens locally: `powershell -NoProfile -File scripts/emit_tokens.ps1 -Out artifacts/tokens.json`
- Generate report: `powershell -NoProfile -File scripts/report_costs.ps1 -OutDir artifacts/cost`
- CI: uploads cost artifacts and posts a PR summary; a scheduled budget check runs daily.

Alternatively, if you have `pytest` available, you can benefit from its
more expressive output and coverage reporting:

```bash
pytest -q --cov=src --cov-report=term-missing --cov-fail-under=80
```

## Repository structure

| Path                       | Purpose                                                 |
|---------------------------|---------------------------------------------------------|
| `src/eafix/`            | Core trading system with CLI, signals, and indicators   |
| `src/contracts/`        | Trading data models and type definitions                |
| `src/integrations/`     | External service connectors and APIs                    |
| `src/websocket/`        | Real-time event broadcasting system                      |
| `src/compliance/`       | Regulatory compliance and reporting                      |
| `tests/`               | Comprehensive unit and integration tests                 |
| `config/`              | System configuration files (YAML, JSON schemas)         |
| `scripts/`             | Setup, deployment, and utility scripts                  |
| `docs/`                | Trading system documentation                             |
| `workflows/`           | Multi-stream workflow definitions                        |
| `.github/workflows`    | CI/CD pipelines for automated testing and deployment    |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests to
discuss improvements, report bugs, or suggest new features. Please follow the
commit message guidelines defined in `.gitmessage.txt` and aim to include
tests for any new functionality.

## VS Code

See `VSCODE_SETUP.md` for available tasks, debug configurations, and how to optionally merge the Codex configuration package from `CODEX_IMPLEMENTATION/vscode_configuration/` into `.vscode` with a backup.
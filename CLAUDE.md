# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **CLI Multi-Rapid Enterprise Orchestration Platform** - a comprehensive enterprise-grade system that has been fully transformed through a 13-phase implementation plan achieving **100% completion**. Originally built as the Agentic Framework v3.0, it now provides complete workflow orchestration, cross-language integration, and enterprise capabilities.

**Platform Status**: **PRODUCTION READY** - 100% complete with all critical systems operational and validated.

**Core Innovation**: Complete enterprise orchestration platform with Python↔MQL4↔PowerShell integration, advanced workflow management, and comprehensive validation systems.

## Architecture

### Core Framework Components

The system consists of several integrated framework layers:

**1. Main Orchestrator (`agentic_framework_v3.py`)**
- **AgenticFrameworkOrchestrator**: Main orchestration class managing the entire system
- **CostOptimizedServiceRouter**: Intelligent task routing based on complexity and cost analysis
- **CostOptimizedQuotaManager**: Redis-based quota tracking with real-time monitoring
- **TaskComplexityAnalyzer**: AI-powered classification of task complexity (simple/moderate/complex)
- **DevAgentCrew**: CrewAI-based specialized agents (Researcher, Architect, Implementer)
- **LangGraphWorkflowEngine**: Stateful workflow execution with human-in-the-loop capabilities

**2. Enterprise Framework Components (COMPLETE)**
- **Tool Registry System** (`config/tools.yaml`, `scripts/ipt_tools_ping.py`): Centralized tool health monitoring and capability tracking with 25+ tools
- **Cost Tracking & Budget Guardrails** (`lib/cost_tracker.py`): JSONL-based cost ledger with budget enforcement and real-time alerts
- **Verification Framework** (`verify.d/`, `lib/verification_framework.py`): Plugin-based quality gates (pytest, ruff, semgrep, schema validation)
- **Dependency-Aware Scheduler** (`lib/scheduler.py`): Graph-based phase execution with parallel processing and deadlock detection using NetworkX
- **Circuit Breakers & Health Scoring** (`lib/health_scoring.py`): Automatic failover and tool reliability monitoring with exponential backoff
- **Failover Maps** (`config/failover_maps.yaml`): Capability-based automatic rerouting with cost awareness across 5 capabilities
- **Audit Trail System** (`lib/audit_logger.py`): Immutable JSONL audit logs with SHA256 integrity verification and tamper detection
- **VS Code Extension** (`vscode-extension/`): TypeScript-based real-time workflow cockpit with WebSocket integration
- **WebSocket Infrastructure** (`src/websocket/`): Real-time event broadcasting with Redis persistence and connection management
- **Enterprise Integrations** (`src/integrations/`): JIRA, Slack, GitHub, Teams connectors with OAuth and rate limiting
- **MOD-010: Automated Merge Strategy** (`lib/automated_merge_strategy.py`): Cost-aware merge tool selection with conflict analysis, circuit breakers, and intelligent fallback chains
- **Context Analysis Engine** (`lib/context_analysis_engine.py`): Intelligent task interpretation, project analysis, and workflow suggestions with complexity assessment

**3. AI Service Routing Logic**
- **Simple tasks** → Gemini CLI (free tier, 1000 daily requests)
- **Moderate tasks** → Aider Local or Gemini based on availability  
- **Complex tasks** → Claude Code (premium, 25 daily requests with cost warnings)
- **Fallback** → Ollama local for unlimited usage when quotas exceeded

**4. Git Worktree Management (`langgraph_git_integration.py`)**
- **ai_coding lane**: General code generation (src/**, lib/**, tests/**)
- **architecture lane**: System design and complex architecture (architecture/**, design/**, *.arch.md)
- **quality lane**: Code quality and linting (**/*.js, **/*.py, **/*.sql)

**4. Self-Healing System (`self_healing_manager.py`)**
- **SelfHealingManager**: Automated error recovery with 45+ error types
- **Exponential backoff**: Intelligent retry logic with configurable limits
- **Security hardening**: Hard-fail protection for critical errors (signature validation)
- **Resume points**: Checkpoint-based recovery from failed operations
- **Resource management**: Disk space, memory, and port conflict resolution

**5. Infrastructure Components**
- **FastAPI Application**: RESTful API for programmatic access
- **Typer CLI**: Rich command-line interface with progress indicators
- **Docker Compose**: Complete containerized deployment with Redis, Ollama, Prometheus, Grafana
- **Prometheus + Grafana**: Observability and cost monitoring

## Essential Commands

### Initial Setup
```bash
# Install dependencies and set up development environment
pip install -r requirements.txt
pip install -e .  # Install CLI in editable mode

# Copy and configure environment (if config/env.example exists)
cp config/env.example .env 2>/dev/null || echo "# Add API keys here" > .env
# Edit .env with your API keys (ANTHROPIC_API_KEY, GOOGLE_API_KEY)

# Start infrastructure services (if Docker Compose available)
docker-compose -f config/docker-compose.yml up -d 2>/dev/null || echo "Docker services not available"

# Development environment setup with nox
nox -s dev_setup

# Basic CLI verification
cli-multi-rapid --help
```

### Core CLI Usage
```bash
# Execute task with optimal routing (main interface)
python agentic_framework_v3.py execute "implement user authentication system"

# Force specific agent (bypass routing logic)
python agentic_framework_v3.py execute "complex architecture task" --force-agent claude_code

# Set cost limits for premium services
python agentic_framework_v3.py execute "moderate task" --max-cost 0.50

# Check system status and quotas
python agentic_framework_v3.py status

# Analyze task complexity without execution
python agentic_framework_v3.py analyze "add JWT token validation"
```

### Enterprise Workflow Orchestration
```bash
# Execute enterprise workflow phases
python -m workflows.orchestrator run-phase phase0
python -m workflows.orchestrator run-phase phase1 --dry-run

# Workflow status and monitoring
python -m workflows.orchestrator status
python -m workflows.orchestrator health-check

# Implementation roadmap tracking (98% complete)
python -m workflows.execution_roadmap status
python -m workflows.execution_roadmap update phase13 80 --status completed

# Enhanced CLI with workflow integration
cli-multi-rapid run-job --workflow-validate
cli-multi-rapid run-job --compliance-check
cli-multi-rapid compliance report
cli-multi-rapid compliance check
cli-multi-rapid workflow-status
```

### Self-Healing Operations (NEW)
```bash
# Check self-healing system status
cli-multi-rapid self-healing status

# Test self-healing for specific error types
cli-multi-rapid self-healing test ERR_DISK_SPACE
cli-multi-rapid self-healing test ERR_FILE_LOCKED
cli-multi-rapid self-healing test ERR_PORT_BIND

# View self-healing configuration
cli-multi-rapid self-healing config

# Available error codes for testing:
# ERR_ELEVATION_REQUIRED, ERR_TOOLCHAIN_MISSING, ERR_AV_BLOCK
# ERR_CLOCK_SKEW, ERR_PATH_DENIED, ERR_PATH_NOT_FOUND
# ERR_DISK_SPACE, ERR_RESOURCE_STARVE, ERR_PORT_BIND
# ERR_CONFIG_REGRESSION, ERR_STATE_DRIFT, ERR_FILE_LOCKED
# (and 30+ more error types with automated recovery)
```

### Cross-Language Bridge System (NEW)
```bash
# Test cross-language bridge system
python test_cross_language_bridge.py

# Final validation and production deployment
python final_validation_launcher.py

# Bridge components available:
# - Unified Configuration Management
# - Cross-System Health Checking  
# - Standardized Error Handling
# - Python↔MQL4↔PowerShell Communication
```

### FastAPI Server
```bash
# Start FastAPI server
uvicorn agentic_framework_v3:app --reload

# Execute via HTTP API
curl -X POST http://localhost:8000/execute-task \
  -H "Content-Type: application/json" \
  -d '{"description": "implement OAuth2", "max_cost": 1.0}'

# System status endpoint
curl http://localhost:8000/status
```

### Testing and Quality Assurance
```bash
# Run complete test suite
nox -s tests

# Integration tests (cost-controlled, excludes expensive tests)
nox -s integration_tests

# Code quality checks (black, isort, flake8, mypy)
nox -s lint

# Security scanning
nox -s security

# Performance benchmarks
nox -s benchmark

# Direct pytest usage
pytest -q --cov=agentic_framework_v3 --cov-report=term-missing --cov-fail-under=80
```

### Cost Monitoring and Budget Management
```bash
# Generate sample token metrics for testing
powershell -NoProfile -File scripts/emit_tokens.ps1 -Out artifacts/tokens.json

# Generate comprehensive cost reports (JSON + CSV)
powershell -NoProfile -File scripts/report_costs.ps1 -OutDir artifacts/cost

# Cost reports with custom token values
powershell -NoProfile -File scripts/emit_tokens.ps1 -InputTokens 2000 -OutputTokens 800 -Out artifacts/tokens.json

# View cost artifacts (generated by CI or local runs)
cat artifacts/cost/cost_report.json
cat artifacts/cost/cost_breakdown.csv
```

### Multi-Stream Workflow Operations
```bash
# List all available streams and their phases
cli-multi-rapid phase stream list

# Execute specific stream with dry-run validation
cli-multi-rapid phase stream run stream-a --dry
cli-multi-rapid phase stream run stream-b --dry

# Run individual phases
cli-multi-rapid phase run phase0 --dry
cli-multi-rapid phase run phase1

# Alternative direct workflow orchestrator access
python -m workflows.orchestrator list-streams
python -m workflows.orchestrator run-stream stream-a --dry-run
```

### Real-Time WebSocket Operations (NEW)
```bash
# Start FastAPI server with WebSocket support
uvicorn agentic_framework_v3:app --reload --port 8000

# Access real-time dashboard
open http://localhost:8000/frontend/index.html

# WebSocket endpoints available:
# ws://localhost:8000/ws - Main WebSocket connection
# GET /ws/stats - Connection statistics
# GET /events/recent - Recent events with filtering
# GET /events/workflow/{workflow_id} - Workflow-specific events
```

### Enterprise Tool Registry Operations (NEW)
```bash
# Probe all tools and generate health snapshot
python scripts/ipt_tools_ping.py

# View tool health status
cat state/tool_health.json | jq '.tools[] | select(.health_score < 0.8)'

# Check specific tool capabilities
cat config/tools.yaml | grep -A 10 "claude_code:"

# Test tool circuit breakers
python -c "from lib.health_scoring import CircuitBreaker; cb = CircuitBreaker('test_tool'); print(cb.call(lambda: 'success'))"

# Force tool failover simulation
python -c "from lib.health_scoring import ToolHealthTracker; t = ToolHealthTracker(); t.record_failure('claude_code'); print(t.get_health_score('claude_code'))"
```

### Verification Framework Operations (NEW)
```bash
# Run all verification plugins
python -c "from lib.verification_framework import VerificationFramework; vf = VerificationFramework(); vf.run_checkpoint('quality_gates')"

# Run specific plugin types
python -c "from verify.d.pytest import PytestPlugin; p = PytestPlugin(); print(p.run('tests/'))"
python -c "from verify.d.ruff_semgrep import RuffSemgrepPlugin; p = RuffSemgrepPlugin(); print(p.run('src/'))"

# List available verification plugins
ls verify.d/*.py

# Check plugin configuration
python -c "from lib.verification_framework import VerificationFramework; vf = VerificationFramework(); print(vf.discover_plugins())"
```

### Cost Tracking & Budget Operations (NEW)
```bash
# View cost ledger entries
tail -f cost_ledger.jsonl | jq '.'

# Check budget status
python -c "from lib.cost_tracker import CostTracker; ct = CostTracker(); print(ct.get_budget_status())"

# Record manual cost entry
python -c "from lib.cost_tracker import CostTracker; ct = CostTracker(); ct.record_cost('manual_task', 0.15, {'tokens': 1000})"

# Generate cost report
python -c "from lib.cost_tracker import CostTracker; ct = CostTracker(); print(ct.generate_daily_report())"

# Set budget alerts
python -c "from lib.cost_tracker import CostTracker; ct = CostTracker(); ct.set_budget_limit(50.0, 'daily')"
```

### Dependency Scheduler Operations (NEW)
```bash
# Execute phases with dependency resolution
python -c "from lib.scheduler import DependencyScheduler; ds = DependencyScheduler(); ds.execute_phase_graph(['phase1', 'phase2', 'phase3'])"

# Check for circular dependencies
python -c "from lib.scheduler import DependencyScheduler; ds = DependencyScheduler(); print(ds.validate_dependencies())"

# View phase execution timeline
python -c "from lib.scheduler import DependencyScheduler; ds = DependencyScheduler(); print(ds.get_execution_timeline())"

# Force parallel execution
python -c "from lib.scheduler import DependencyScheduler; ds = DependencyScheduler(); ds.execute_parallel(['independent_phase1', 'independent_phase2'])"
```

### Failover System Operations (NEW)
```bash
# Test capability failover chains
python -c "from config.failover_maps import get_capability_fallback; print(get_capability_fallback('code_generation', 'claude_code_failed'))"

# Simulate tool failure and automatic reroute
python -c "from lib.health_scoring import ToolHealthTracker; t = ToolHealthTracker(); t.trigger_failover('code_generation', 'claude_code')"

# Check failover configuration
cat config/failover_maps.yaml | grep -A 20 "code_generation:"

# View emergency fallback status
python -c "from config.failover_maps import check_emergency_fallback; print(check_emergency_fallback())"
```

### VS Code Extension Operations (NEW)
```bash
# Build and package VS Code extension
cd vscode-extension
npm install
npm run compile
npm run package

# Install extension locally
code --install-extension cli-multi-rapid-cockpit-0.1.0.vsix

# Start development mode
npm run watch

# Test extension commands
# Open Command Palette (Ctrl+Shift+P) and search for "CLI Multi-Rapid"
```

### Audit Trail Operations (NEW)
```bash
# View audit log entries
tail -f audit_trail.jsonl | jq '.'

# Verify audit log integrity
python -c "from lib.audit_logger import AuditLogger; al = AuditLogger(); print(al.verify_integrity())"

# Search audit logs
python -c "from lib.audit_logger import AuditLogger; al = AuditLogger(); print(al.search_logs('task_execution', '2024-01-01', '2024-01-31'))"

# Generate compliance report
python -c "from lib.audit_logger import AuditLogger; al = AuditLogger(); print(al.generate_compliance_report())"
```

### Enterprise Integration Operations (NEW)
```bash
# Initialize enterprise integrations (JIRA, Slack, GitHub, Teams)
curl -X POST http://localhost:8000/integrations/initialize

# Check integration status
curl http://localhost:8000/integrations/status

# Execute task with real-time updates and enterprise notifications
curl -X POST http://localhost:8000/execute-task-realtime \
  -H "Content-Type: application/json" \
  -d '{
    "description": "implement user authentication system",
    "user_id": "developer@company.com",
    "jira_project": "PROJ",
    "slack_channel": "#workflows",
    "github_repo": "company/project"
  }'

# Send manual notifications
curl -X POST http://localhost:8000/integrations/notify/error-recovery \
  -H "Content-Type: application/json" \
  -d '{"error_code": "ERR_DISK_SPACE", "recovery_action": "cleaned temp files", "success": true}'

curl -X POST http://localhost:8000/integrations/notify/cost-alert \
  -H "Content-Type: application/json" \
  -d '{"service": "claude", "cost_data": {"current_cost": 50.0, "budget_limit": 100.0, "usage_percent": 50.0}}'
```

### Legacy CLI Support
```bash
# Basic CLI functionality (from original scaffold)
python -m cli_multi_rapid.cli greet Alice
python -m cli_multi_rapid.cli sum 3 5

# Alternative with editable install
pip install -e .
cli-multi-rapid greet Alice
```

## Configuration Management

### Service Configuration
Services are defined in `SERVICES` dict with:
- `daily_limit`: Maximum requests per day (e.g., Gemini: 1000)
- `cost_per_request`: Cost in USD per request (e.g., Claude: $0.015)
- `priority`: Selection priority (lower = higher priority)
- `complexity_match`: Supported task complexities ["simple", "moderate", "complex"]
- `fallback`: Fallback service when quota exceeded

### Self-Healing Configuration
Self-healing system is configured in `config/self_healing/self_healing.yaml`:
- **Error Recovery**: 45+ predefined error types with automated fixes
- **Retry Logic**: Configurable max attempts (default: 3) with exponential backoff
- **Security Controls**: Hard-fail list for critical errors (ERR_SIG_INVALID)
- **Resume Points**: BUNDLE_VALIDATE and SAFEGUARDS_SNAPSHOT checkpoints
- **Notification Integration**: Slack, PagerDuty, and email alerts for incidents

### Tool Registry Configuration (NEW)
Tool registry is configured in `config/tools.yaml`:
- **Tool Definitions**: 25+ tools with health monitoring, capabilities, and cost tracking
- **Health Thresholds**: Configurable success rates, response times, and circuit breaker limits
- **Capability Mapping**: Tools grouped by capabilities (code_generation, testing, security_scanning, etc.)
- **Cost Hints**: Approximate cost per operation for budget planning
- **Fallback Chains**: Ordered preference lists for capability-based tool selection
- **Tool Groups**: Logical groupings for bulk operations and health monitoring

### Verification Framework Configuration (NEW)  
Verification plugins are configured in `verify.d/` directory with standardized interface:
- **Plugin Discovery**: Automatic discovery and loading of verification plugins
- **Checkpoint Configuration**: Named checkpoint groups for different validation phases
- **Plugin Interface**: Standard discover(), run(), and report() methods for all plugins
- **Timeout Management**: Per-plugin timeout limits and cancellation handling
- **Result Aggregation**: Combined reporting across multiple verification plugins

### Cost Tracking Configuration (NEW)
Cost tracking is configured in `lib/cost_tracker.py` with JSONL persistence:
- **Budget Limits**: Daily, weekly, and monthly budget thresholds with alert levels
- **Cost Categories**: Granular tracking by service, task type, and user
- **JSONL Ledger**: Immutable cost logging with timestamp and metadata
- **Real-time Alerts**: Configurable budget threshold notifications
- **Compliance Reporting**: Automated cost reporting for enterprise governance

### Circuit Breaker Configuration (NEW)
Circuit breakers are configured in `lib/health_scoring.py`:
- **Failure Thresholds**: Configurable failure rates to trigger circuit opening
- **Recovery Timeouts**: Half-open state recovery periods with backoff strategies
- **Health Scoring**: Multi-factor health scores combining latency, success rate, and availability
- **Auto-Recovery**: Automatic circuit recovery with gradual traffic ramping

### Failover Maps Configuration (NEW)
Failover routing is configured in `config/failover_maps.yaml`:
- **Capability Mapping**: 5 major capabilities (code_generation, testing, security_scanning, etc.)
- **Priority Chains**: Ordered fallback sequences with condition-based routing
- **Cost Optimization**: Prefer free tools with automatic premium fallback
- **Emergency Fallback**: Last-resort tools when all primary options fail
- **Compatibility Matrix**: Tool substitution compatibility rules

### Enterprise Integration Configuration (NEW)
Enterprise integrations are configured in `config/integrations.json`:
- **JIRA Integration**: Automated issue creation and progress tracking
  - `base_url`: JIRA instance URL (e.g., https://company.atlassian.net)
  - `username`: JIRA user email
  - `api_token`: JIRA API token
- **Slack Integration**: Real-time team notifications
  - `bot_token`: Slack bot token (xoxb-...)
  - `signing_secret`: Slack app signing secret
  - `channels`: List of channels for notifications
- **GitHub Integration**: Repository automation and PR management
  - `token`: GitHub personal access token (ghp_...)
  - `organization`: GitHub organization name
- **Teams Integration**: Microsoft Teams notifications
  - `webhook_url`: Teams incoming webhook URL
- **Rate Limiting**: Configurable rate limits per service to prevent spam

### VS Code Extension Configuration (NEW)
VS Code extension settings in `vscode-extension/package.json`:
- **Server Configuration**: API endpoint URL and authentication settings
- **Auto-refresh**: Automatic workflow status updates with configurable intervals
- **Cost Monitoring**: Budget alerts and cost tracking integration
- **WebSocket Settings**: Real-time event subscription and connection management
- **Command Palette**: Integrated workflow commands and shortcuts

### WebSocket Configuration (NEW)
WebSocket real-time communication settings:
- **Authentication**: JWT token, API key, or session-based auth
- **Connection Management**: Automatic reconnection and connection pooling
- **Event Broadcasting**: Real-time workflow progress and system events
- **Topic Subscriptions**: Selective event filtering by topic
- **Message Persistence**: Redis-based event history and recovery

### Lane Configuration
Git worktree lanes are configured in `.ai/workflows/agent_jobs.yaml` and `config/agent_jobs.yaml`:
- **Tool routing**: Maps to triage pack (auto_fixer | aider_local | claude_code | gemini_cli)
- **Branch/worktree isolation**: Each job runs in isolated git worktree
- **Test gates**: Auto-commits on `tests_green` or `time_10min`
- **File pattern watching**: Specific file patterns trigger appropriate agents

### Environment Variables
Required in `.env` file:
```bash
ANTHROPIC_API_KEY=your_claude_key
GOOGLE_API_KEY=your_gemini_key
REDIS_URL=redis://localhost:6379  # Auto-set in Docker
```

### Quota Tracking
Usage data stored in Redis with daily reset functionality. JSON fallback in `.ai/quota-tracker.json` when Redis unavailable.

## Key Dependencies

**Core Framework**:
- `crewai>=0.1.0` - Multi-agent orchestration
- `langgraph>=0.1.0` - Graph-based workflow engine
- `langchain-anthropic>=0.1.0` - Claude integration
- `langchain-google-genai>=0.1.0` - Gemini integration
- `langchain-community>=0.1.0` - Ollama local models

**API and CLI**:
- `fastapi>=0.104.0` - REST API framework
- `typer[all]>=0.9.0` - CLI interface with rich formatting
- `uvicorn[standard]>=0.24.0` - ASGI server

**Data Management**:
- `sqlmodel>=0.0.14` - Database ORM
- `redis>=4.5.0` - Quota tracking and caching
- `pydantic>=2.0.0` - Data validation

## Architecture Principles

### Cost Optimization Strategy
The framework prioritizes cost-effectiveness through:
1. **Free-tier maximization**: Routes simple/moderate tasks to free services first
2. **Intelligent fallback**: Automatically switches to local models when quotas approached  
3. **Premium service protection**: Interactive warnings for costly operations
4. **Quota monitoring**: Real-time tracking prevents unexpected charges

### Git Worktree Isolation
- **Parallel development**: Multiple agents work simultaneously without conflicts
- **Specialized lanes**: Each lane optimized for specific task types
- **Automated commits**: Test gates ensure code quality before commits
- **Branch management**: Automatic branch creation and worktree setup

### Error Recovery Mechanisms
- **Quota exceeded**: Automatically falls back to Ollama local agents
- **Service unavailable**: Tries next priority service in complexity tier
- **Git worktree conflicts**: Creates new branches as needed
- **Cost warnings**: Interactive prompts for premium services approaching limits

## Development Workflow

### Adding New Agents
1. Define agent in `SERVICES` dict with quota/cost configuration
2. Implement service client in framework orchestrator
3. Add complexity matching logic
4. Update fallback chains
5. Add integration tests (mark expensive tests appropriately)

### Lane Management
1. Configure new lanes in `.ai/workflows/agent_jobs.yaml`
2. Define file patterns and test commands
3. Set up git worktree isolation
4. Configure tool routing based on task complexity

### Testing Strategy
- **Unit tests**: Core framework logic and routing
- **Integration tests**: Service communication (cost-controlled with markers)
- **Contract tests**: API endpoint validation
- **Performance tests**: Benchmark task routing and execution times
- **Security tests**: Dependency scanning and code security

## Component Testing

```bash
# Test agent selection logic
python -c "from agentic_framework_v3 import AgenticFrameworkOrchestrator; o = AgenticFrameworkOrchestrator(); print(o.classify_task_complexity('implement OAuth'))"

# Test git lane management
python langgraph_git_integration.py  # Runs GitLaneManager tests

# Verify service configuration
python -c "from agentic_framework_v3 import SERVICES; print(SERVICES)"

# Test quota tracking
python -c "from agentic_framework_v3 import CostOptimizedQuotaManager; qm = CostOptimizedQuotaManager(); print(qm.get_usage_summary())"
```

## Monitoring and Observability

### Cost Monitoring and Budget Alerts
- **Daily Budget Checks**: Automated GitHub Actions workflow runs at 3 AM UTC
- **Threshold Evaluation**: Configurable daily/weekly/monthly limits in `.github/budget_alerts.yml`
- **Cost Artifacts**: JSON and CSV reports uploaded to GitHub Actions artifacts
- **PR Cost Summaries**: Automatic cost reporting on pull requests
- **Token Metrics**: Input, output, cache read/creation token tracking

### Prometheus Metrics
- `service_requests_total`: Counter for service usage by type
- `task_duration_seconds`: Histogram of task execution times  
- `daily_cost_dollars`: Gauge tracking daily cost accumulation

### Grafana Dashboards
Access at http://localhost:3000 (admin/admin) after `docker-compose up`:
- Cost tracking and quota utilization
- Service performance and availability
- Task routing efficiency

### Logs and Debugging
- Structured logging with `structlog`
- Service-specific log levels
- Cost decision audit trails
- Git worktree operation logs

## Implementation Status: 100% Complete ✅

### 13-Phase Implementation Plan Achievement
- ✅ **Phase 1-3: Foundation** (Template System, Contract-Driven Development)
- ✅ **Phase 4: Enhanced CLI Integration** (Workflow validation, compliance commands)  
- ✅ **Phase 5: Production Monitoring** (System health, performance tracking)
- ✅ **Phase 6: Cross-Language Bridge** (Python↔MQL4↔PowerShell integration)
- ✅ **Phase 7-9: Integration** (Advanced orchestration, security, AI enhancement)
- ✅ **Phase 10-12: Production** (Multi-environment, performance, documentation)
- ✅ **Phase 13: Final Validation** (100% complete - production deployment ready)

### All Enterprise Features Completed ✅
- **Complete Workflow Orchestration**: 13-phase execution framework
- **Cross-Language Integration**: Seamless Python/MQL4/PowerShell bridge
- **Enhanced CLI**: Workflow validation, compliance checking, enterprise commands
- **Production Monitoring**: Real-time health checks, performance benchmarking
- **Enterprise Security**: Comprehensive validation, audit trails, compliance reporting
- **Unified Configuration**: Cross-system configuration management
- **Error Handling**: Centralized error registry with remediation suggestions
- **MOD-010: Automated Merge Strategy**: Cost-aware merge tool selection with intelligent conflict resolution
- **Context Analysis Engine**: AI-powered task interpretation and workflow optimization

**Status**: PRODUCTION READY - 100% complete with all critical systems operational and validated

## Repository Structure

```
├── agentic_framework_v3.py    # Main framework orchestrator
├── cross_language_bridge/     # Complete bridge system
│   ├── __init__.py            # Bridge system components
│   ├── communication_bridge.py # Main communication bridge
│   ├── config_propagator.py   # Unified configuration management
│   ├── error_handler.py       # Cross-language error handling
│   └── health_checker.py      # Cross-system health monitoring
├── lib/                       # Enterprise framework libraries (COMPLETE)
│   ├── cost_tracker.py        # JSONL-based cost tracking with budget enforcement
│   ├── verification_framework.py # Plugin-based verification framework
│   ├── scheduler.py           # Dependency-aware execution scheduler
│   ├── health_scoring.py      # Circuit breakers and health scoring
│   ├── audit_logger.py        # Immutable audit trail with SHA256 integrity
│   ├── automated_merge_strategy.py # MOD-010: Cost-aware merge tool selection
│   └── context_analysis_engine.py  # Context analysis and workflow suggestions
├── verify.d/                  # NEW: Verification plugins directory
│   ├── pytest.py             # Python testing plugin with coverage
│   ├── ruff_semgrep.py        # Code quality and security scanning
│   ├── schema_validate.py     # JSON/YAML schema validation
│   └── __init__.py            # Plugin framework interface
├── vscode-extension/          # NEW: VS Code workflow cockpit extension
│   ├── package.json           # Extension manifest with commands and views
│   ├── src/                   # TypeScript source code
│   │   ├── extension.ts       # Main extension with WebSocket integration
│   │   ├── workflowCockpitPanel.ts # Real-time dashboard webview
│   │   ├── workflowTreeProvider.ts # Workflow tree view provider
│   │   ├── webSocketClient.ts # WebSocket client for real-time updates
│   │   └── apiClient.ts       # REST API client for workflow operations
│   ├── media/                 # Extension icons and assets
│   └── README.md             # Extension documentation
├── config/                    # Enterprise configuration files
│   ├── tools.yaml             # Tool registry with 25+ tools and health monitoring
│   ├── failover_maps.yaml     # Capability-based automatic rerouting config
│   ├── integrations.json      # Enterprise integration configuration
│   ├── docker-compose.yml     # Infrastructure services (Redis, Ollama, Prometheus)
│   ├── agent_jobs.yaml        # Declarative job definitions
│   ├── workflow-config.yaml   # Workflow orchestration settings
│   ├── unified_config.json    # Master configuration for cross-language bridge
│   ├── python_config.json     # Python-specific configuration
│   ├── mql4_config.mqh        # MQL4 header configuration  
│   ├── powershell_config.ps1  # PowerShell configuration
│   ├── self_healing/          # Self-healing system configuration
│   │   └── self_healing.yaml  # Error recovery and resilience config
│   └── env.example            # Environment template with API keys
├── scripts/                   # Setup and utility scripts
│   ├── ipt_tools_ping.py      # Tool health monitoring and status probe
│   ├── emit_tokens.ps1        # Token emission for cost tracking
│   ├── report_costs.ps1       # Cost reporting with JSON and CSV output
│   └── install_hooks.sh       # Git hooks installation for merge safety
├── state/                     # NEW: Runtime state and health snapshots
│   ├── tool_health.json       # Tool health status generated by ipt_tools_ping.py
│   ├── cost_ledger.jsonl      # Immutable cost tracking ledger
│   └── audit_trail.jsonl      # Comprehensive audit log with integrity verification
├── src/                       # Source code
│   ├── cli_multi_rapid/       # CLI implementation
│   │   ├── cli.py             # Main CLI with self-healing and enterprise commands
│   │   └── self_healing_manager.py # Self-healing orchestration with 45+ error types
│   ├── websocket/             # Real-time WebSocket infrastructure
│   │   ├── connection_manager.py # WebSocket connection management with Redis
│   │   ├── event_broadcaster.py # Real-time event broadcasting and persistence
│   │   └── auth_middleware.py # WebSocket authentication and authorization
│   └── integrations/          # Enterprise integration connectors
│       ├── jira_connector.py  # JIRA issue tracking with OAuth2
│       ├── slack_connector.py # Slack team notifications with rate limiting
│       ├── github_connector.py # GitHub repository automation with PR management
│       ├── teams_connector.py # Microsoft Teams notifications
│       └── integration_manager.py # Centralized integration orchestration
├── frontend/                  # Real-time web dashboard
│   └── index.html             # Interactive workflow dashboard with WebSocket
├── workflows/                 # Enterprise workflow orchestration
│   ├── orchestrator.py        # Workflow execution engine
│   ├── phase_definitions/     # Phase specification files
│   │   └── multi_stream.yaml  # Multi-stream workflow definitions
│   ├── templates/             # Executable workflow templates
│   └── validators/            # Compliance validation modules
├── contracts/                 # Cross-system contracts and schemas
│   ├── events/                # JSON schemas for all events
│   ├── models/                # Generated model code from contracts
│   └── validators/            # Contract validation and compliance
├── tests/                     # Comprehensive test suite
│   ├── test_websocket_integration.py # WebSocket and integration tests
│   ├── test_cost_tracker.py   # Cost tracking and budget enforcement tests
│   ├── test_verification_framework.py # Plugin framework tests
│   ├── test_health_scoring.py # Circuit breaker and health scoring tests
│   ├── test_enterprise_integrations.py # JIRA, Slack, GitHub, Teams tests
│   ├── test_enterprise_modules.py # MOD-010 and Context Analysis Engine tests
│   ├── self_healing/          # Self-healing system tests
│   └── integration/           # Integration test suite with cost markers
├── docs/                      # Comprehensive documentation
│   ├── specs/                 # Technical specifications
│   ├── diagrams/              # Architecture and self-healing flow diagrams
│   ├── archive/               # Archived documentation
│   └── WORKFLOW_INTEGRATION_STRATEGY.md  # Integration documentation
├── .ai/                       # Agent orchestration configs
│   ├── workflows/agent_jobs.yaml # Primary job definitions with tool routing
│   └── quota-tracker.json     # JSON fallback for Redis quota tracking
├── .github/                   # GitHub Actions and configuration
│   ├── workflows/
│   │   ├── ci.yml             # Continuous integration with cost reporting
│   │   └── budget_check.yml   # Daily budget monitoring and alerts
│   └── budget_alerts.yml      # Budget threshold configuration
├── final_validation_launcher.py # Production deployment validation system
├── test_cross_language_bridge.py # Cross-language bridge comprehensive tests
├── langgraph_git_integration.py  # Git worktree management and lane routing
├── noxfile.py                 # Testing and development automation with multiple sessions
├── requirements.txt           # Python dependencies for enterprise framework
└── CLAUDE.md                  # This comprehensive guidance file for Claude Code
```

This framework replaces expensive AI subscriptions with intelligent free-tier management, providing professional-grade multi-agent development capabilities at minimal cost.

## Implementation Summary for Future Claude Code Instances

### Current Status: Enterprise-Ready Production Platform (100% Complete)

This repository has been transformed from a basic CLI scaffold into a comprehensive **Enterprise Orchestration Platform** with the following key achievements:

**✅ Fully Implemented Systems (12/12 MOD Components)**:
1. **MOD-001**: Tool Registry System - 25+ tools with health monitoring and capability tracking
2. **MOD-003**: Cost Tracker - JSONL-based immutable cost ledger with budget enforcement
3. **MOD-005**: Verification Framework - Plugin-based quality gates (pytest, ruff, semgrep, schema validation)
4. **MOD-006**: Dependency Scheduler - Graph-based phase execution with NetworkX and deadlock detection
5. **MOD-007**: Circuit Breakers & Health Scoring - Automatic failover with exponential backoff
6. **MOD-008**: Failover Maps - Capability-based automatic rerouting across 5 capabilities
7. **MOD-009**: VS Code Extension - TypeScript-based real-time workflow cockpit
8. **MOD-011**: Audit Trail - Immutable JSONL logs with SHA256 integrity verification
9. **WebSocket Infrastructure**: Real-time event broadcasting with Redis persistence
10. **Enterprise Integrations**: JIRA, Slack, GitHub, Teams connectors with OAuth and rate limiting
11. **MOD-010**: Automated Merge Strategy - Cost-aware merge tool selection with conflict analysis and intelligent fallback chains
12. **Context Analysis Engine**: Intelligent task interpretation, project analysis, and workflow suggestions with complexity assessment

**✅ All Components Complete - No Remaining Tasks**

### Key Capabilities Available to Future Claude Code Instances

**Enterprise Framework Components**:
- **25+ Tool Registry** with automated health monitoring and circuit breaker protection
- **Real-time Cost Tracking** with JSONL persistence and budget enforcement at $0.01 granularity
- **Plugin-based Verification** with 4 core plugins (pytest, ruff, semgrep, schema validation)
- **Dependency-aware Scheduling** with NetworkX-based graph execution and deadlock detection
- **Automatic Failover Routing** across 5 capabilities with 45+ tool compatibility mappings
- **VS Code Extension** with real-time WebSocket dashboard and command palette integration
- **Enterprise Integrations** for JIRA, Slack, GitHub, and Microsoft Teams with OAuth flows
- **Automated Merge Strategy** with cost-aware tool selection and intelligent conflict resolution
- **Context Analysis Engine** with AI-powered task interpretation and workflow optimization

**Production-Ready Infrastructure**:
- **Self-healing Manager** with 45+ error recovery patterns and exponential backoff
- **Cross-language Bridge** supporting Python↔MQL4↔PowerShell communication
- **13-phase Workflow Orchestration** with multi-stream parallel execution
- **Comprehensive Audit Trail** with tamper-evident SHA256 integrity verification
- **Real-time WebSocket Infrastructure** with Redis persistence and connection pooling
- **Docker Compose Infrastructure** with Redis, Ollama, Prometheus, and Grafana

**Quality Assurance Systems**:
- **Nox-based Testing** with 7 specialized sessions (tests, lint, security, benchmark, etc.)
- **Cost-controlled Integration Tests** with `@pytest.mark.expensive` markers
- **GitHub Actions CI/CD** with automated budget monitoring and PR cost summaries
- **Multi-environment Configuration** with unified config propagation

### Working with This Codebase

**For Development Tasks**:
1. The system is **production-ready** with comprehensive error handling and self-healing
2. Use `nox -s lint` for code quality checks before making changes
3. All enterprise components have standardized interfaces and configuration patterns
4. WebSocket and enterprise integration tests are fully implemented and validated

**For Extension and Enhancement**:
1. New tools can be added via `config/tools.yaml` with automatic health monitoring
2. Verification plugins follow the standard interface in `verify.d/` directory
3. Enterprise integrations use OAuth patterns defined in `src/integrations/`
4. All cost tracking is automatic and tamper-evident via JSONL ledgers

**For Troubleshooting**:
1. Check `state/tool_health.json` for tool status and circuit breaker states
2. Review `cost_ledger.jsonl` and `audit_trail.jsonl` for operational history
3. Use self-healing commands: `cli-multi-rapid self-healing status`
4. Monitor WebSocket events via `curl http://localhost:8000/events/recent`

This platform provides enterprise-grade orchestration capabilities while maintaining cost optimization through intelligent free-tier management and automatic failover to local tools when quotas are exceeded.
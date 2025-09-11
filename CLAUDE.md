# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Agentic Framework v3.0** - a cost-optimized multi-agent development framework that intelligently routes AI development tasks based on complexity classification and quota management. Built on proven open-source technologies (CrewAI, LangGraph, FastAPI, Redis) with a focus on maximizing free-tier usage while providing premium service fallbacks.

**Core Innovation**: Cost-first AI development orchestration with intelligent service routing to minimize AI service costs while maintaining professional-grade development capabilities.

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

**2. AI Service Routing Logic**
- **Simple tasks** → Gemini CLI (free tier, 1000 daily requests)
- **Moderate tasks** → Aider Local or Gemini based on availability  
- **Complex tasks** → Claude Code (premium, 25 daily requests with cost warnings)
- **Fallback** → Ollama local for unlimited usage when quotas exceeded

**3. Git Worktree Management (`langgraph_git_integration.py`)**
- **ai_coding lane**: General code generation (src/**, lib/**, tests/**)
- **architecture lane**: System design and complex architecture (architecture/**, design/**, *.arch.md)
- **quality lane**: Code quality and linting (**/*.js, **/*.py, **/*.sql)

**4. Infrastructure Components**
- **FastAPI Application**: RESTful API for programmatic access
- **Typer CLI**: Rich command-line interface with progress indicators
- **Docker Compose**: Complete containerized deployment with Redis, Ollama, Prometheus, Grafana
- **Prometheus + Grafana**: Observability and cost monitoring

## Essential Commands

### Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY, GOOGLE_API_KEY)

# Start infrastructure services (Redis, Ollama, Monitoring)
docker-compose up -d

# Development environment setup with nox
nox -s dev_setup
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

### Lane Configuration
Git worktree lanes are configured in `.ai/workflows/agent_jobs.yaml`:
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

## Repository Structure

```
├── agentic_framework_v3.py    # Main framework orchestrator
├── langgraph_git_integration.py  # Git worktree management
├── noxfile.py                 # Testing and development automation
├── docker-compose.yml         # Infrastructure services
├── requirements.txt           # Python dependencies
├── .ai/                       # Agent orchestration configs
│   └── workflows/agent_jobs.yaml  # Declarative job definitions
├── src/cli_multi_rapid/       # Legacy CLI scaffold
├── tests/                     # Test suite
└── monitoring/                # Prometheus/Grafana configs
```

This framework replaces expensive AI subscriptions with intelligent free-tier management, providing professional-grade multi-agent development capabilities at minimal cost.
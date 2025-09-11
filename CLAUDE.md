# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Agentic Framework v3.0** - a modern, production-ready multi-agent development framework built on proven open-source technologies (CrewAI, LangGraph, FastAPI, Redis). The system provides intelligent, cost-optimized task routing to AI services based on complexity classification and quota management.

## Architecture

The system consists of integrated framework components:

### 1. Core Framework (`agentic_framework_v3.py`)
- **AgenticFrameworkOrchestrator**: Main orchestration class managing the entire system
- **CostOptimizedServiceRouter**: Intelligent task routing based on complexity and cost
- **CostOptimizedQuotaManager**: Redis-based quota tracking with real-time monitoring
- **TaskComplexityAnalyzer**: AI-powered classification of task complexity levels
- **DevAgentCrew**: CrewAI-based specialized agents (Researcher, Architect, Implementer)
- **LangGraphWorkflowEngine**: Stateful workflow execution with human-in-the-loop

### 2. Infrastructure Components
- **FastAPI Application**: RESTful API for programmatic access
- **Typer CLI**: Rich command-line interface with progress indicators
- **Docker Compose**: Complete containerized deployment
- **Prometheus + Grafana**: Observability and cost monitoring

## Key Features

### Agent Routing Logic
- **Simple tasks**: Route to Gemini (free tier, 1000 daily requests)
- **Moderate tasks**: Route to Aider Local or Gemini based on availability  
- **Complex tasks**: Route to Claude Code (premium, 25 daily requests with cost warnings)
- **Fallback**: Ollama local for unlimited usage when quotas exceeded

### Git Worktree Management
- **ai_coding lane**: For general code generation (src/**, lib/**, tests/**)
- **architecture lane**: For system design and complex architecture (architecture/**, design/**, *.arch.md)
- **quality lane**: For code quality and linting (**/*.js, **/*.py, **/*.sql)

## Common Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Start infrastructure (Redis, Ollama, Monitoring)
docker-compose up -d

# Development environment setup
nox -s dev_setup
```

### CLI Usage
```bash
# Execute a task with optimal routing
python agentic_framework_v3.py execute "implement user authentication system"

# Force specific agent (bypass routing)
python agentic_framework_v3.py execute "complex architecture task" --force-agent claude_code

# Set cost limits
python agentic_framework_v3.py execute "moderate task" --max-cost 0.50

# Check system status and quotas
python agentic_framework_v3.py status

# Analyze task complexity (no execution)
python agentic_framework_v3.py analyze "add JWT token validation"
```

### API Usage
```bash
# Start FastAPI server
uvicorn agentic_framework_v3:app --reload

# Execute via HTTP
curl -X POST http://localhost:8000/execute-task \
  -H "Content-Type: application/json" \
  -d '{"description": "implement OAuth2", "max_cost": 1.0}'

# System status
curl http://localhost:8000/status
```

### Testing and Quality
```bash
# Run full test suite
nox -s tests

# Integration tests (cost-controlled)
nox -s integration_tests

# Code quality checks
nox -s lint security

# Performance benchmarks
nox -s benchmark
```

## Dependencies

The framework requires these Python packages:
- `langgraph` - Core graph orchestration
- `langchain-anthropic` - Claude integration
- `langchain-google-genai` - Gemini integration  
- `langchain-community` - Ollama integration
- `click` - CLI interface
- `pathlib` - File system operations

## Configuration

### Service Configuration
Services are defined in `SERVICES` dict with:
- `daily_limit`: Maximum requests per day
- `cost_per_request`: Cost in USD per request
- `priority`: Selection priority (lower = higher priority)
- `complexity_match`: Supported task complexities

### Lane Configuration
Stored in `.ai/framework-config.json` with worktree paths, branch names, allowed file patterns, and agent assignments.

### Quota Tracking
Usage data stored in `.ai/quota-tracker.json` with daily reset functionality.

## Development Notes

- The system replaces a complex PowerShell orchestrator with pure Python
- All agents are LangGraph-compatible and use the same state management
- Git worktrees allow parallel development in different contexts without conflicts
- Cost optimization prevents unexpected charges from premium AI services
- Local agents (Ollama) provide unlimited fallback capacity

## Error Handling

The framework includes several error recovery mechanisms:
- **Quota exceeded**: Automatically falls back to local agents (Ollama)
- **Service unavailable**: Tries next priority service in the complexity tier
- **Git worktree conflicts**: Creates new branches as needed
- **Cost warnings**: Interactive prompts for premium services approaching limits

## Testing

To test individual components:
```bash
# Test agent selection logic
python -c "from langgraph_cli import CostOptimizedOrchestrator; o = CostOptimizedOrchestrator(); print(o.classify_task_complexity('implement OAuth'))"

# Test git lane setup
python langgraph_git_integration.py  # Run as script to test GitLaneManager

# Verify service configuration
python -c "from langgraph_cli import SERVICES; print(SERVICES)"
```
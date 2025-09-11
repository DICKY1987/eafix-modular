# Agentic Framework v3.0

A modern, cost-optimized multi-agent development framework built on proven open-source technologies.

## Core Innovation

**Cost-First AI Development** - Intelligent routing of tasks to optimal AI services based on complexity, cost, and availability:

- **Simple tasks** → Free Gemini CLI (1000 requests/day)
- **Moderate tasks** → Local Aider or Gemini (unlimited/free)  
- **Complex tasks** → Premium Claude Code (controlled quotas)
- **Fallback** → Local Ollama (unlimited capacity)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ User Interface: Typer CLI + Rich + FastAPI Web Interface    │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ Orchestration: CrewAI Agents + LangGraph Workflows          │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ Cost Control: Redis Quotas + Prometheus Metrics            │
│ Service Router: Complexity Classification + Fallback       │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ Data Layer: SQLModel + Redis + Prometheus                  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
# Clone and setup
git clone <repository>
cd langchain

# Install dependencies  
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose up -d
```

### Basic Usage

```bash
# Execute a task with optimal agent selection
python agentic_framework_v3.py execute "implement user authentication system"

# Force specific agent
python agentic_framework_v3.py execute "refactor database layer" --force-agent claude_code

# Check system status and quotas
python agentic_framework_v3.py status

# Analyze task complexity
python agentic_framework_v3.py analyze "add JWT token validation"
```

### API Usage

```python
import asyncio
from agentic_framework_v3 import AgenticFrameworkOrchestrator, TaskRequest

async def main():
    orchestrator = AgenticFrameworkOrchestrator()
    await orchestrator.initialize()
    
    request = TaskRequest(
        description="Create a REST API for user management",
        max_cost=0.50  # Cost limit
    )
    
    result = await orchestrator.execute_task(request)
    print(f"Task completed by: {result['result']['service_used']}")

asyncio.run(main())
```

### Web API

```bash
# Start the FastAPI server
uvicorn agentic_framework_v3:app --reload

# Execute via HTTP POST
curl -X POST http://localhost:8000/execute-task \
  -H "Content-Type: application/json" \
  -d '{"description": "implement OAuth2 login", "max_cost": 1.0}'

# Check system status
curl http://localhost:8000/status
```

## Framework Components

### 1. Cost-Optimized Service Router
- **TaskComplexityAnalyzer**: Classifies tasks as simple/moderate/complex
- **CostOptimizedServiceRouter**: Routes to cheapest capable service
- **Quota Management**: Redis-based usage tracking with daily limits

### 2. Multi-Agent Orchestration
- **CrewAI Agents**: Specialized roles (Researcher, Architect, Implementer)
- **LangGraph Workflows**: Stateful execution with human-in-the-loop capability
- **Research-Plan-Code Pattern**: Structured development workflow

### 3. Infrastructure
- **Redis**: Real-time quota tracking and caching
- **Prometheus**: Metrics collection and cost monitoring
- **Grafana**: Visualization dashboards
- **SQLModel**: Type-safe data persistence

## Service Configuration

| Service | Daily Limit | Cost/Request | Use Cases |
|---------|-------------|--------------|-----------|
| Gemini CLI | 1000 | $0.00 | Simple tasks, research |
| Claude Code | 25 | $0.15 | Complex architecture, premium |
| Aider Local | Unlimited | $0.00 | Moderate coding tasks |
| Ollama Local | Unlimited | $0.00 | Fallback, offline |

Target cost: **< $5/day** typical usage

## Development

### Testing

```bash
# Install nox
pip install nox

# Run full test suite
nox -s tests

# Integration tests (cost-controlled)
nox -s integration_tests

# Linting and formatting
nox -s lint

# Security checks
nox -s security
```

### Monitoring

Access monitoring dashboards:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

Key metrics:
- `service_requests_total`: Requests per service
- `task_duration_seconds`: Execution times
- `daily_cost_dollars`: Real-time cost tracking

### Configuration

Environment variables in `.env`:

```env
# Required API keys
ANTHROPIC_API_KEY=your_key
GOOGLE_API_KEY=your_key

# Optional customization
MAX_DAILY_COST=5.00
CLAUDE_QUOTA_WARNING=0.6
REDIS_URL=redis://localhost:6379
```

## Key Features

### 🎯 Intelligent Task Routing
Automatically classifies tasks and routes to the most cost-effective capable service.

### 💰 Cost Optimization
- Real-time quota tracking
- Cost warnings for premium services
- Automatic fallback to free alternatives

### 🔄 Multi-Agent Workflows
- Research → Plan → Code structured workflows
- Specialized agents for different development phases
- Human-in-the-loop for critical decisions

### 📊 Comprehensive Monitoring
- Real-time cost tracking
- Service usage analytics
- Performance metrics

### 🐳 Production Ready
- Docker containerization
- Redis for scalable state management
- Prometheus + Grafana observability

## Roadmap

### Phase 1 (Current): Core Framework ✅
- [x] Multi-service orchestration
- [x] Cost-optimized routing
- [x] CLI and API interfaces
- [x] Basic monitoring

### Phase 2: Advanced Features
- [ ] Git worktree integration for parallel development lanes
- [ ] Advanced workflow patterns (TDD, iterative refinement)
- [ ] Plugin system for custom agents
- [ ] Enhanced human-in-the-loop workflows

### Phase 3: Enterprise Features  
- [ ] Multi-tenant support
- [ ] Advanced cost analytics
- [ ] Compliance and audit logging
- [ ] Advanced security controls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `nox -s tests lint`
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

---

**Built with**: CrewAI • LangGraph • FastAPI • Redis • Prometheus
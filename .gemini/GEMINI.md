# Project context for Gemini CLI

You are operating inside the **CLI Multi-Rapid Enterprise Orchestration Platform** repo. This is a comprehensive enterprise-grade system that provides complete workflow orchestration, cross-language integration, and enterprise capabilities.

## System Overview

**Platform Status**: PRODUCTION READY - 98% complete with all critical systems operational and validated.

**Core Innovation**: Complete enterprise orchestration platform with Python↔MQL4↔PowerShell integration, advanced workflow management, and comprehensive validation systems.

## Priorities & Guidelines

- Respect schema-locked outputs and existing architectural patterns
- Prefer deterministic, testable changes; propose unit tests with each patch
- Never execute shell or write files without explicit user confirmation
- When editing code, create a new git branch: `feature/ai-enhancement/<short-task>` and stage minimal diffs
- If a task spans multiple files, produce a concise plan first, then apply edits in small commits with clear messages

## Repository Structure & Roles

### **Core Framework**
- `agentic_framework_v3.py` - Main orchestration class managing the entire system
- `langgraph_git_integration.py` - Git worktree management with specialized lanes
- `cross_language_bridge/` - Complete bridge system for Python↔MQL4↔PowerShell integration
- `final_validation_launcher.py` - Production deployment system

### **CLI & Integration**
- `src/cli_multi_rapid/` - Enhanced CLI with workflow validation, compliance checking
- `.vscode/` - Comprehensive VS Code integration with 50+ tasks and debug configurations
- `workflow-vscode.code-workspace` - Specialized workspace for workflow operations

### **Enterprise Features**
- `workflows/` - Enterprise workflow orchestration with 13-phase execution framework
- `contracts/` - Cross-system contracts with JSON schemas and validation
- `config/` - Unified configuration management across languages
- `tests/` - Comprehensive test suite with compliance and workflow validation

## Service Architecture

### **AI Service Routing Logic**
- **Simple tasks** → Gemini CLI (free tier, 1000 daily requests)
- **Moderate tasks** → Aider Local or Gemini based on availability  
- **Complex tasks** → Claude Code (premium, 25 daily requests with cost warnings)
- **Fallback** → Ollama local for unlimited usage when quotas exceeded

### **Git Worktree Lanes**
- **ai_coding lane**: General code generation (src/**, lib/**, tests/**)
- **architecture lane**: System design and complex architecture (architecture/**, design/**, *.arch.md)
- **quality lane**: Code quality and linting (**/*.js, **/*.py, **/*.sql)

## Development Guardrails

### **Quality Gates**
- **Local (pre-commit)**: Format, lint, schema validate, secret scan, license check
- **CI**: Re-run all local gates; run unit tests & dry-run workflows; publish reports
- **Runtime**: Enforce timeouts, retries, idempotency, and artifact signatures
- **Audit**: Every run logs inputs/outputs, component versions, and approvals

### **Cost Optimization**
- Free-tier maximization with intelligent fallback chains
- Interactive warnings for premium services approaching limits
- Real-time quota monitoring prevents unexpected charges
- Per-job cost tags and budget thresholds

### **Security & Compliance**
- Least privilege access patterns
- Short-lived tokens and secret rotation
- Comprehensive validation and audit trails
- Cross-language error handling with remediation suggestions

## Essential Commands

```bash
# Core CLI operations
cli-multi-rapid phase stream list
cli-multi-rapid phase stream run stream-a --dry
cli-multi-rapid workflow-status
cli-multi-rapid compliance check

# Framework operations
python agentic_framework_v3.py execute "task description"
python agentic_framework_v3.py status
python final_validation_launcher.py

# Cross-language bridge testing
python test_cross_language_bridge.py
```

## Integration Notes

This system integrates with:
- **VS Code**: Complete workflow system with specialized tasks and debug configurations
- **Docker**: Containerized deployment with Redis, Ollama, Prometheus, Grafana
- **GitHub Actions**: Cost monitoring, budget alerts, and automated workflows
- **FastAPI**: RESTful API for programmatic access to all framework capabilities

When making changes, ensure compatibility with the existing 98% complete system and maintain the enterprise-grade quality standards established throughout the platform.
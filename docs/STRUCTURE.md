# Repository Structure Guide

This document explains the organized file structure of the cli_multi_rapid_DEV repository.

## Directory Structure

### `/config/` - Configuration Files
- `docker-compose.yml` - Infrastructure services (Redis, Ollama, Prometheus, Grafana)
- `agent_jobs.yaml` - Job definitions for automated workflows
- `env.example` - Environment variable template
- `autonomous_cli_workflow.yaml` - Workflow automation configuration
- `pre-commit-config.yaml` - Git pre-commit hooks
- `config.schema.json` - JSON schema definitions
- `free_tier_framework.json` - Free-tier service configuration
- `openapi_*.yaml` - API specifications

### `/scripts/` - Utilities and Setup
- `cross_platform_setup.sh` - Cross-platform development setup
- `free_tier_setup.sh` - Free-tier service initialization
- `practical_implementation.sh` - Implementation utilities
- `commit_guard.sh` - Git commit validation
- `install_hooks.py` - Git hooks installer
- `INS_*.ps1` - Windows installer scripts
- `INS_*.md` - Installation documentation
- `install_all.ps1` - Complete installation script

### `/docs/` - Documentation
- `framework-overview.md` - Main framework documentation
- `ai-tools-guide.md` - AI tools integration guide
- `cost-optimization-guide.md` - Cost optimization strategies
- `workflow-guide.md` - Workflow usage documentation
- `setup-guide.md` - Setup and installation guide
- `routing-logic.md` - Task routing decision tree

### `/docs/specs/` - Technical Specifications
- `system-specification.md` - Core system specification
- `cyclesync-specification.md` - CycleSync technical spec
- `SOP_TEMPLATE.atomic.md` - Standard operating procedure template
- `User_Authentication_Flow.atomic.md` - Authentication flow specification

### `/docs/archive/` - Archived Documentation
- Legacy documentation and outdated specifications
- Implementation work notes and development history
- Archived workflow documentation

## Core Files (Root Level)

### Framework Core
- `agentic_framework_v3.py` - Main framework orchestrator
- `langgraph_git_integration.py` - Git worktree management
- `langgraph_cli.py` - LangGraph CLI utilities
- `server.py` - FastAPI server implementation

### Project Configuration
- `requirements.txt` - Python dependencies
- `noxfile.py` - Testing and development automation
- `pyproject.toml` - Python project configuration
- `pytest.ini` - Test configuration
- `tasks.json` - Task definitions for VS Code/editors

### Project Management
- `README.md` - Main project documentation
- `CLAUDE.md` - Claude Code guidance
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - MIT license
- `SECURITY.md` - Security policy

## Key Principles

### User Recognition Priority
- Directory and file names use clear, descriptive terms
- Related files are grouped logically
- Duplicate files have been removed
- Configuration is centralized in `/config/`
- Documentation is organized by purpose

### Maintenance Benefits
- Easy to locate specific file types
- Clear separation of concerns
- Reduced repository clutter
- Improved navigation and discovery
- Better CI/CD integration paths

## Migration Notes

Files were reorganized from a flat structure to this hierarchical organization:
- Binary files (PDFs, PNGs, ZIPs) were removed from git tracking
- Duplicate configuration files were consolidated
- Documentation was renamed for clarity and grouped by purpose
- Scripts were centralized for easier maintenance

This structure supports the framework's evolution while maintaining clarity for both human developers and automated tooling.
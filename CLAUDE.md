# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **CLI Orchestrator** - a deterministic, schema-driven CLI orchestrator that stitches together multiple developer tools and AI agents into predefined, auditable workflows. It prioritizes scripts first, escalates to AI only where judgment is required, and emits machine-readable artifacts with gates and verification at every hop.

## Core Architecture

### Key Components
- **Workflow Runner**: Executes schema-validated YAML workflows (`src/cli_multi_rapid/workflow_runner.py:1`)
- **Router System**: Routes steps between deterministic tools and AI adapters (`src/cli_multi_rapid/router.py:1`)
- **Adapter Framework**: Unified interface for tools and AI services (`src/cli_multi_rapid/adapters/`)
- **Schema Validation**: JSON Schema validation for workflows and artifacts (`.ai/schemas/`)
- **Cost Tracking**: Token usage and budget enforcement (`src/cli_multi_rapid/cost_tracker.py:1`)
- **Gate System**: Verification and quality gates (`src/cli_multi_rapid/verifier.py:1`)

### Directory Structure
- `src/cli_multi_rapid/`: Core orchestrator implementation
- `.ai/workflows/`: YAML workflow definitions (schema-validated)
- `.ai/schemas/`: JSON Schema definitions for validation
- `adapters/`: Tool and AI adapter implementations
- `artifacts/`: Workflow execution artifacts (patches, reports)
- `logs/`: JSONL execution logs and telemetry
- `cost/`: Token usage tracking and budget reports

## Common Development Commands

### Installation and Setup
```bash
# Install in development mode
pip install -e .

# Install with AI tools support
pip install -e .[ai]

# Install with development tools
pip install -e .[dev]
```

### CLI Usage
```bash
# Run a workflow with dry-run
cli-orchestrator run .ai/workflows/PY_EDIT_TRIAGE.yaml --files "src/**/*.py" --lane lane/ai-coding/fix-imports --dry-run

# Execute workflow
cli-orchestrator run .ai/workflows/PY_EDIT_TRIAGE.yaml --files "src/**/*.py"

# Verify an artifact against schema
cli-orchestrator verify artifacts/diagnostics.json --schema .ai/schemas/diagnostics.schema.json

# Create PR from artifacts
cli-orchestrator pr create --from artifacts/ --title "Auto triage & fixes" --lane lane/ai-coding/fix-imports

# Generate cost report
cli-orchestrator cost report --last-run
```

### Development Tools
```bash
# Run tests
python -m pytest tests/ -v --cov=src

# Run code quality checks
ruff check src/ tests/ --fix
black src/ tests/
isort src/ tests/ --profile black
mypy src/ --ignore-missing-imports

# Run pre-commit hooks
pre-commit run --all-files
```

## Workflow Development

### Creating Workflows
Workflows are defined in `.ai/workflows/*.yaml` and validated against `.ai/schemas/workflow.schema.json`:

```yaml
name: "Python Edit + Triage"
inputs:
  files: ["src/**/*.py"]
  lane: "lane/ai-coding/fix-imports"
policy:
  max_tokens: 120000
  prefer_deterministic: true
steps:
  - id: "1.001"
    name: "VS Code Diagnostic Analysis"
    actor: vscode_diagnostics
    with:
      analyzers: ["python", "ruff", "mypy"]
    emits: ["artifacts/diagnostics.json"]
```

### Available Actors
- **vscode_diagnostics**: Run diagnostic analysis (ruff, mypy, etc.)
- **code_fixers**: Apply deterministic fixes (black, isort, ruff --fix)
- **ai_editor**: AI-powered code editing (aider, claude, gemini)
- **pytest_runner**: Run tests with coverage reporting
- **verifier**: Check gates and validate artifacts
- **git_ops**: Git operations and PR creation

### Gate Types
- **tests_pass**: Verify tests pass from test report
- **diff_limits**: Check diff size within bounds
- **schema_valid**: Validate artifacts against schemas

## Architecture Principles

1. **Determinism First**: Prefer scripts and static analyzers over AI
2. **Schema-Driven**: All workflows validated by JSON Schema
3. **Idempotent & Safe**: Dry-run, patch previews, rollback support
4. **Auditable**: Every step emits structured artifacts and logs
5. **Cost-Aware**: Track token spend, enforce budgets
6. **Git Integration**: Lane-based development, signed commits

## Extending the System

### Adding New Adapters
1. Extend `BaseAdapter` in `src/cli_multi_rapid/adapters/base_adapter.py`
2. Implement `execute()` method returning `AdapterResult`
3. Register in `Router._initialize_adapters()`
4. Add actor to workflow schema enum

### Adding New Gate Types
1. Add gate logic to `Verifier._check_single_gate()`
2. Update workflow schema with new gate type
3. Create corresponding JSON schema for artifacts

## Testing Strategy

- Unit tests for core components (`tests/`)
- Integration tests for workflow execution
- Schema validation tests for all artifacts
- Mock adapters for isolated testing

## Dependencies

- **Core**: typer, pydantic, rich, PyYAML, jsonschema
- **Optional AI**: aider-chat (for AI-powered editing)
- **Development**: pytest, black, isort, ruff, mypy
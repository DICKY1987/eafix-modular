# Repository Guidelines

## Project Structure & Module Organization
- Source code: `src/cli_multi_rapid` (primary CLI orchestrator). Supporting libs preserved: `src/integrations`, `src/websocket`, `src/observability`, `src/idempotency`.
- Workflows: `.ai/workflows/` (YAML workflow definitions), `.ai/schemas/` (JSON Schema validation).
- Tests: `tests/` (unit/pytest). Runtime outputs: `artifacts/`, `logs/`, `cost/`.
- Configuration: `config/` (tool configs), `scripts/` (development helpers).

## Build, Test, and Development Commands
- Run CLI orchestrator: `cli-orchestrator run .ai/workflows/PY_EDIT_TRIAGE.yaml --files "src/**/*.py"`
- Entry point commands: `cli-orchestrator verify artifacts/diagnostics.json --schema .ai/schemas/diagnostics.schema.json`
- Workflow execution: `cli-orchestrator run .ai/workflows/CODE_QUALITY.yaml --dry-run`
- Cost tracking: `cli-orchestrator cost report --last-run`
- Tests: `pytest -q --cov=src` (coverage gate) | `python -m unittest -v`
- Git operations: `cli-orchestrator pr create --from artifacts/ --title "Auto fixes"`

## Coding Style & Naming Conventions
- Python 3.9+, 4-space indents, prefer type hints.
- Naming: snake_case modules/functions; PascalCase classes.
- Lint/format/type: `ruff`, `black`, `isort`, `mypy`. Security/SAST: `bandit`, `detect-secrets` (run locally or via CI).

## Testing Guidelines
- Frameworks: `pytest` and `unittest`; schema validation with `jsonschema`.
- Coverage: ≥ 85% (enforced by pytest configuration). Run `pytest -q --cov=src` before PRs.
- Naming: files `tests/test_*.py`, classes `Test*`, functions `test_*`.

## Workflow Development Guidelines
- All workflows must validate against `.ai/schemas/workflow.schema.json`
- Prefer deterministic tools over AI when possible (policy: `prefer_deterministic: true`)
- Implement proper cost tracking for AI operations
- Use gates for quality control (`tests_pass`, `diff_limits`, `schema_valid`)
- Emit structured artifacts for all steps

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat:`, `fix:`, `chore:`) with clear scope.
- PRs: concise description, linked issues, include artifact summaries when relevant.
- Rebase on `main` before merge; CI must pass (lint, type, tests, schema validation).

## CLI Orchestrator Architecture
- **Deterministic → AI Routing**: Scripts first, escalate to AI only when judgment required
- **Schema-Driven**: All workflows validated by JSON Schema before execution
- **Cost-Aware**: Token tracking, budget enforcement, prefer cheaper deterministic tools
- **Gate System**: Quality gates with artifact validation at each step
- **Lane-based Git**: Structured branching for conflict-free parallel development

## Agent-Specific Notes
- Keep changes minimal and aligned with workflow-driven patterns.
- Validate workflows locally: `cli-orchestrator run workflow.yaml --dry-run`
- Test schema compliance: `cli-orchestrator verify artifact.json --schema schema.json`
- Scope: This `AGENTS.md` applies to the CLI orchestrator repository; direct user instructions take precedence.

## Available Actors
- `vscode_diagnostics`: Run diagnostic analysis (ruff, mypy, python)
- `code_fixers`: Apply deterministic fixes (black, isort, ruff --fix)
- `ai_editor`: AI-powered editing (aider, claude, gemini)
- `pytest_runner`: Run tests with coverage reporting
- `verifier`: Check gates and validate artifacts
- `git_ops`: Git operations and PR creation
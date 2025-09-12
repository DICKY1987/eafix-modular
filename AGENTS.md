# Repository Guidelines

## Project Structure & Module Organization
- Source code: `src/cli_multi_rapid` (primary CLI). Supporting libs in `src/observability`, `src/idempotency`, `src/compliance`, and `src/contracts`.
- Tests: `tests/` (unit and property tests). Sample scenarios under `P_tests/fixtures/`.
- Workflows: `workflows/` (phase orchestrator, phase specs). Deployment assets in `deploy/` (e.g., `deploy/k8s/`).
- Agentic bundle: `agentic/`. Dev scripts and helpers in `scripts/`.

## Build, Test, and Development Commands
- Run CLI (module): `python -m cli_multi_rapid.cli greet Alice`
- Run CLI (entry point): `cli-multi-rapid greet Alice`
- Orchestrator status: `python -m workflows.orchestrator status`
- List streams: `python -m workflows.orchestrator list-streams`
- Run a stream (dry): `python -m workflows.orchestrator run-stream stream-a --dry-run`
- CLI equivalents: `cli-multi-rapid phase stream list` | `cli-multi-rapid phase run phase1 --dry`
- Tests (pytest+cov): `pytest -q --cov=src`
- Tests (unittest): `python -m unittest -v`
- Git hooks: `bash scripts/install_hooks.sh` (POSIX) | `./scripts/install_hooks.ps1` (Windows)

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indents, prefer type hints.
- Lint/format/type: `ruff`, `mypy`. Security/SAST: `bandit`, `semgrep`, `gitleaks`.
- Filenames: snake_case for modules; PascalCase for classes; snake_case for functions.

## Testing Guidelines
- Frameworks: `unittest` and `pytest`; optional `hypothesis` (tests skip if missing).
- Coverage gate ≥ 85% (see `pytest.ini`). Run: `pytest -q --cov=src`.
- Naming: files `tests/test_*.py`, classes `Test*`, functions `test_*`.

## Commit & Pull Request Guidelines
- Conventional Commits (e.g., `feat:`, `fix:`, `chore:`). Keep messages clear and scoped.
- PRs: concise description, linked issues, and before/after notes or screenshots when relevant. Rebase on `main` before merge.
- CI must pass (lint, type, tests, compliance gates). Auto-merge available when checks pass; merged branches are auto-cleaned.

## Security & Configuration Tips
- Never commit secrets; `.env*` is ignored. Compliance gate and CodeQL run in CI.
- Server metrics: `server.py` exposes `/metrics` (Prometheus). `/save` requires `DROP_TOKEN` auth.
- Pin tool versions where possible; prefer deterministic builds. Use `PYTHONPATH=src` for local runs.

## Agent-Specific Notes
- Keep changes minimal and focused; follow existing patterns. Prefer updating specs in `workflows/phase_definitions/` and invoke via orchestrator.
- Validate locally before PR: `pytest -q --cov=src` and `python -m workflows.orchestrator status`.

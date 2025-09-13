# Repository Guidelines

## Project Structure & Module Organization
- Source code: `src/cli_multi_rapid` (primary CLI). Supporting libs in `src/observability`, `src/idempotency`, `src/compliance`, `src/contracts`.
- Workflows: `workflows/` (phase orchestrator, phase specs). Deployment assets in `deploy/` (e.g., `deploy/k8s/`).
- Tests: `tests/` (unit/pytest) and `P_tests/fixtures/` (sample scenarios). Agent bundle: `agentic/`. Dev helpers: `scripts/`.
- Server: `server.py` exposes `/metrics` and `/save` (see Security).

## Build, Test, and Development Commands
- Run CLI (module): `python -m cli_multi_rapid.cli greet Alice`
- Run CLI (entry point): `cli-multi-rapid greet Alice`
- Orchestrator: `python -m workflows.orchestrator status` | `list-streams` | `run-stream stream-a --dry-run`
- CLI equivalents: `cli-multi-rapid phase stream list` | `cli-multi-rapid phase run phase1 --dry`
- Tests: `pytest -q --cov=src` (coverage gate) | `python -m unittest -v`
- Git hooks: `bash scripts/install_hooks.sh` (POSIX) | `./scripts/install_hooks.ps1` (Windows)

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indents, prefer type hints.
- Naming: snake_case modules/functions; PascalCase classes.
- Lint/format/type: `ruff`, `mypy`. Security/SAST: `bandit`, `semgrep`, `gitleaks` (run locally or via CI).

## Testing Guidelines
- Frameworks: `pytest` and `unittest`; optional `hypothesis` (tests skip if missing).
- Coverage: ≥ 85% (enforced by `pytest.ini`). Run `pytest -q --cov=src` before PRs.
- Naming: files `tests/test_*.py`, classes `Test*`, functions `test_*`.

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat:`, `fix:`, `chore:`) with clear scope.
- PRs: concise description, linked issues, before/after notes or screenshots when relevant.
- Rebase on `main` before merge; CI must pass (lint, type, tests, compliance). Auto-merge may be enabled; merged branches auto-cleaned.

## Security & Configuration Tips
- Never commit secrets; `.env*` is ignored. Compliance gates and CodeQL run in CI.
- `server.py`: `/metrics` (Prometheus). `/save` requires `DROP_TOKEN` auth.
- Prefer pinned tool versions; deterministic builds. Use `PYTHONPATH=src` for local runs.

## Agent-Specific Notes
- Keep changes minimal and aligned with existing patterns. Prefer updating specs in `workflows/phase_definitions/` and invoke via the orchestrator.
- Validate locally before PR: `pytest -q --cov=src` and `python -m workflows.orchestrator status`.
- Scope: An `AGENTS.md` applies to the directory tree it’s in; deeper files override shallower ones. Direct user instructions take precedence.


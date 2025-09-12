# Repository Guidelines

## Project Structure & Module Organization
- Source code: `src/cli_multi_rapid` (primary CLI), supporting libs in `src/observability`, `src/idempotency`, `src/compliance`.
- Tests: `tests/` (unit and property tests). Sample scenarios in `P_tests/fixtures/`.
- Workflows: `workflows/` (phase orchestrator, phase specs). Deployment assets in `deploy/k8s/`.
- Agentic bundle: `agentic/`, orchestration scripts in `scripts/`.

## Build, Test, and Development Commands
- Run CLI locally: `python -m cli_multi_rapid.cli greet Alice`
- List jobs: `cli-multi-rapid run-job [--file tasks.json] [--name triage] --show steps`
- Orchestrator: `cli-multi-rapid phase status` | `cli-multi-rapid phase run phase1 --dry`
- Tests: `pytest -q` (coverage gate ≥ 85%) or `python -m unittest -v`
- Hooks: `bash scripts/install_hooks.sh` or `./scripts/install_hooks.ps1`
- Build + SBOM (via CI release): tag `vX.Y.Z` and push.

## Coding Style & Naming Conventions
- Python 3.11+. Use 4‑space indents; prefer type hints.
- Lint/format/type: `ruff`, `pre-commit`, `mypy`. Security/SAST: `bandit`, `semgrep`, `gitleaks`.
- Filenames: snake_case for modules, PascalCase for classes, snake_case for functions.

## Testing Guidelines
- Frameworks: `unittest` and `pytest`; optional `hypothesis` (tests skip if missing).
- Naming: test files `tests/test_*.py`, classes `Test*`, functions `test_*`.
- Coverage: enforced at ≥ 85% (see `pytest.ini`). Run `pytest -q --cov=src` locally.

## Commit & Pull Request Guidelines
- Conventional Commits (e.g., `feat:`, `fix:`, `chore:`). Use clear, scoped messages.
- Open PRs with: concise description, linked issues, before/after notes or screenshots when UI/devtools involved.
- CI must pass (lint, type, tests, compliance-gate). Rebase on `main` before merge.

## Security & Configuration Tips
- Secrets: never commit; `.env*` ignored. Compliance gate and CodeQL run in CI.
- Server metrics: `server.py` exposes `/metrics` (Prometheus). Auth for `/save` via `DROP_TOKEN`.
- The `.ai/` audit log is ignored by Git; tail with VS Code task “Agent: Audit Tail”.

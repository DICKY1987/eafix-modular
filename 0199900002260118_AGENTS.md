---
doc_id: DOC-CONFIG-0049
---

# Repository Guidelines

This repo hosts the modular EAFIX trading system. Services are Python 3.11 (FastAPI, Redis, Postgres) managed with Poetry and orchestrated via Docker Compose.

## Project Structure & Module Organization
- `services/<service>/src`: Service source (e.g., `services/data-ingestor/src/main.py`).
- `services/<service>/tests`: Unit/integration tests (e.g., `services/calendar-ingestor/tests`).
- `services/common`: Shared helpers (e.g., `base_service.py`).
- `deploy/compose`: Compose files for local stack (Redis, Postgres, services).
- `docs/runbooks`: Ops and incident runbooks.
- `observability`: Prometheus/Alertmanager config.
- Top-level helpers: `pyproject.toml`, `Makefile`, `Taskfile.yml`.

## Build, Test, and Development Commands
- `poetry install`: Install deps. First-time dev setup. (or `make install`)
- `poetry run pytest`: Run tests. Full suite is `make test-all` or `task test`.
- `make docker-up` / `make docker-down`: Start/stop the full stack locally.
- `make lint`: Flake8 + mypy over `services/*/src`.
- `make format`: Black + isort over `services/`.
- Examples:
  - `poetry run pytest -m "unit" services/data-ingestor/tests/unit -q`
  - `docker compose -f deploy/compose/docker-compose.yml logs -f`

## Coding Style & Naming Conventions
- Python 3.11, Black (line length 88), isort (profile=black), Flake8, mypy (strict).
- Indentation: 4 spaces. Naming: `snake_case` for modules/functions, `PascalCase` for classes, `UPPER_CASE` for constants.
- Keep service APIs small and typed; prefer pure functions in `src/` with thin FastAPI adapters.

## Testing Guidelines
- Framework: `pytest` with markers: `unit`, `integration`, `e2e`, `security`, `performance`.
- Coverage: project-wide ≥ 80% (branch coverage on); reports under `reports/coverage`.
- Test layout: `services/<service>/tests/{unit,integration}` and `tests/e2e/`.
- Naming: files `test_*.py`; tests isolated and deterministic (no real network/DB in unit tests).

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat`, `fix`, `docs`, `chore`, `ci`, `refactor` with optional scope, e.g., `feat(risk-manager): add position limiter`.
- Subject in imperative, ≤ 72 chars; explain what/why in body.
- PRs: clear description, linked issues (e.g., `Fixes #123`), test coverage evidence (output or screenshots), and note config/DB/ports changes. Include UI screenshots for dashboard changes.

## Security & Configuration Tips
- Never commit secrets. Copy `.env.template` to `.env` locally when present.
- Images are pinned by digest; keep them updated in PRs that bump bases.
- Install security tools as needed: `poetry install --with security` (bandit, safety, semgrep).
- Local ports: services expose 8081–8087; start stack with `make docker-up` and verify health endpoints (`/healthz`, `/readyz`).


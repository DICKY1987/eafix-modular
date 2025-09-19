# Gaps Pack — How to Apply

1. Extract this ZIP into the **root** of your repo.
2. Commit and push a branch (e.g., `gaps/init`).
3. Open a PR and ensure CI passes.

## What you get
- `docs/gaps/` — Gap Register, Invariants, FMEA, SLOs, incident + postmortem templates.
- `.github/workflows/` — Schema compatibility check and smoke e2e boot test.
- `ci/` — Python scripts for schema validation and a simple compatibility checker, plus a smoke test.
- `scripts/chaos/` — Kill/restart helpers; game day checklist.
- `scripts/replay/` — Tick replay scaffold (CSV in, HTTP out) for future performance tests.
- `.github/CODEOWNERS` — Ownership starter.

## Makefile targets
- `make contracts-validate` — Validate JSON Schemas.
- `make smoke` — Run local smoke test against Compose ports.

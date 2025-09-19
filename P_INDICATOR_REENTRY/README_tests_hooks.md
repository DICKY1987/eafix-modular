\
# Tests & Hooks for Reentry Helpers

## Pytest
Place `reentry_helpers/` at repo root (or install as a package), then run:
```bash
pytest -q
```

## Pre-commit
If you already have `.pre-commit-config.yaml`, merge the blocks from `.pre-commit-config.reentry.yaml`.
Otherwise, copy it to `.pre-commit-config.yaml` and enable:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Hooks:
- **pytest** — runs unit tests.
- **validate-indicators** — validates `indicator_records_full.json` with `indicator_record.schema.json` via `reentry_helpers_cli.py`.
- **validate-reentry-keys** — scans `runtime/` and `registries/` for cells that look like `SIG~TB~OB~PB~G` and validates tokens.

## Scripted CSV key validation
`python scripts/validate_keys_cli.py runtime registries`

# Reentry CI Pack

This pack contains:
- **GitHub Actions workflow**: `.github/workflows/reentry_ci.yml` → runs `pytest`, indicator validation, CSV key validation, and optional `pre-commit`.
- **CSV Schemas**: `csv_schemas/orders_out.schema.json` and `csv_schemas/orders_in.schema.json` → describe bridge contracts (including `comment_prefix` + `comment_suffix` wiring).
- **Exporter**: `exporters/export_orders_out.py` → composes `reentry_key`, computes Base32 suffix, and writes `orders_out.csv` with a final `comment` that fits MT4 limits.

## Install

Copy the contents of this pack into your repo root (preserve folder structure). Ensure you also committed:
- `reentry_helpers/` package (or available on PYTHONPATH)
- `scripts/validate_keys_cli.py` (provided in the previous add-on pack)
- `reentry_helpers_cli.py` (previous pack)
- `indicator_record.schema.json` + `indicator_records_full.json`
- `runtime/signals_inbox.csv` + `registries/matrix_map.csv`

## Run exporter

```bash
python exporters/export_orders_out.py
# outputs runtime/ea_bridge/orders_out.csv with comment_prefix+suffix wired
```

## CI behavior

- If test/validator inputs are missing, steps are skipped (won’t fail your PRs).
- When present, failures in tests or validators fail the workflow (good!).

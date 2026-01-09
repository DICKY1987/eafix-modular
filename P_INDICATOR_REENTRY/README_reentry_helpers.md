---
doc_id: DOC-DOC-0005
---

# Reentry Helpers (Python)

Stdlib-only utilities for the Reentry Trading System.

## Modules

- `reentry_helpers.vocab` — Load canonical vocab (duration/proximity/outcome/direction/generation).
- `reentry_helpers.hybrid_id` — Compose/parse/validate hybrid reentry keys; short Base32 hash for EA comments.
- `reentry_helpers.indicator_validator` — Validate indicator records against `indicator_record.schema.json` (uses `jsonschema` if available, falls back to a built-in validator).

## Quick Start

```bash
# Option A: Use as a package (copy the folder into your repo)
cp -r reentry_helpers/ your_repo/packages/reentry_helpers/

# Option B: Run CLI directly
python reentry_helpers_cli.py make-key --sig NFP_BREAKOUT --tb FLASH --ob W1 --pb AT_EVENT --gen 1 --comment-prefix RNT
python reentry_helpers_cli.py parse-key --key NFP_BREAKOUT~FLASH~W1~AT_EVENT~1
python reentry_helpers_cli.py validate-key --key CPI_REVERSAL~QUICK~BE~POST_30M~2
python reentry_helpers_cli.py validate-indicators --records indicator_records.json --schema indicator_record.schema.json
```

## Vocab

The helpers will auto-discover `reentry_vocab.json` in `./` or `./config/`. If not present, sensible defaults are used.

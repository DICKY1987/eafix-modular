---
doc_id: DOC-REG-0000
---
# EAFIX Canonical Registry Candidate System

This directory now contains JSONL-authored registry records and deterministic generated snapshots.

## Authority state

The registries are **canonical candidates**, not canonical authorities. Current authorities remain active until each registry passes parity review and is cut over in its own governed pull request.

## Build

```bash
python -m pip install jsonschema
python tools/registries/build_registries.py
python tools/registries/build_registries.py --check
```

## Rules

- Edit JSONL records, never `.current.json` snapshots.
- Keep records sorted by `record_id`.
- Record unknown facts explicitly; do not invent them.
- Resolve high-severity conflicts before cutover.
- Do not update routing or `doc_authority.json` until registry-specific cutover.

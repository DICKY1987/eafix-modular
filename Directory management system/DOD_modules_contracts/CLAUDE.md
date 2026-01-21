# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repository defines a **module contract system** for making "done" checkable. The core idea: code does not define completion—contracts define completion. A module is only done when its manifest validates, all required files exist, and all acceptance tests pass.

## Key Concepts

- **module.manifest.yaml** is the SSOT (single source of truth) for what a module must contain and produce
- **Contracts are machine-enforceable**: if a human must interpret pass/fail, it doesn't belong in the contract
- **Evidence-based validation**: every validator and acceptance test emits JSON evidence to `evidence/`
- **Contract tiers**: tier1 (policy/governance), tier2 (domain modules), tier3 (utilities)

## Architecture

```
module.manifest.yaml          # Contract definition (validates against schema)
schemas/
  module.manifest.schema.json # JSON Schema defining valid manifests
scripts/
  validate_structure.ps1      # Validates required paths exist
  validate_manifest_schema.ps1  # (planned) Validates manifest against schema
  run_acceptance.ps1          # (planned) Runs acceptance test suite
  run_validators.ps1          # (planned) Orchestrates all validators
evidence/
  validation/                 # Validator output reports
  acceptance/                 # Acceptance test reports
  runs/                       # Per-run metadata logs
```

## Commands

Run structure validation:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_structure.ps1 -Mode validation
```

Run structure acceptance:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_structure.ps1 -Mode acceptance
```

All validators should exit 0 on success and produce a JSON report in the appropriate `evidence/` subdirectory.

## Contract Schema Structure

The manifest schema (`schemas/module.manifest.schema.json`) enforces:
- `module_id`: uppercase with underscores, 3-64 chars
- `module_type`: system | library | service | data | tool
- `inputs`/`outputs`: typed artifacts with path, freshness, direction
- `required_files`: role-based file requirements (entrypoint, validator, io_schema, etc.)
- `validators`: executable checks with expected exit codes and produced artifacts
- `acceptance_tests`: final gate checks
- `side_effects`: declared mutations (required for system modules)
- `dependency_rules`: allowed and disallowed module dependencies

## Working with This Repository

1. **Contract changes**: Edit `module.manifest.yaml`, then run validators to verify
2. **Schema changes**: Proposed additions are tracked in `SCHEMA_ADDITIONS.md`
3. **New validators**: Add to `scripts/`, register in `module.manifest.yaml` under `validators`
4. **Evidence**: All validation runs must emit JSON to `evidence/` subdirectories

## Key Files

- `WORKFLOW.md`: Step-by-step process for writing module contracts
- `DEEP_DIVE.md`: Rationale for why contracts make AI modifications safer
- `SYSTEM_ARTIFACTS.md`: Pre-coding artifact plan (what must exist before implementation is complete)

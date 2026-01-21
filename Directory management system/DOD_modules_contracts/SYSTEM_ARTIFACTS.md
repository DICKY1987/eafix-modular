# System Artifact List (Pre-Coding)

Scope: This list covers the full planned artifact set for the DOD_modules_contracts module before implementation work starts.
Module root: C:\Users\richg\eafix-modular\Directory management system\DOD_modules_contracts

Legend:
- Required: must exist for the module to be considered done.
- Optional: recommended but not required.
- Generated: produced by automation (validators/tests).
- Status: existing | planned | generated

## Function

- Define and validate module contracts so done is checkable.
- Provide schema and evidence outputs to enforce compliance.

## Deliverables

- module.manifest.yaml ? Required ? existing ? Module contract for this module.
- schemas/module.manifest.schema.json ? Required ? existing ? JSON Schema for module manifests.
- scripts/validate_structure.ps1 ? Required ? existing ? Structure validator.
- scripts/validate_manifest_schema.ps1 ? Required ? planned ? Manifest schema validator.
- scripts/run_acceptance.ps1 ? Required ? planned ? Acceptance runner.
- evidence/validation/structure_validation.json ? Generated ? planned ? Structure validation report.
- evidence/validation/manifest_schema_validation.json ? Generated ? planned ? Manifest schema report.
- evidence/acceptance/structure_acceptance.json ? Generated ? planned ? Structure acceptance report.
- evidence/acceptance/contract_acceptance.json ? Generated ? planned ? Contract acceptance report.
- evidence/runs/run_YYYYMMDDTHHMMSS.json ? Generated ? planned ? Per-run metadata and results.

## Inputs (source artifacts)

- ChatGPT-Contracts for Checkable !Done!.md ? Required ? existing ? Primary source document.
- comprehensive inventory of a module.txt ? Optional ? existing ? Inventory reference excerpt.

## Contract and governance

- module.manifest.yaml ? Required ? existing ? Module contract and definition of done.
- schemas/module.manifest.schema.json ? Required ? existing ? JSON Schema for module.manifest.yaml.
- SYSTEM_ARTIFACTS.md ? Required ? existing ? Pre-coding system artifact list (this file).
- ARTIFACTS.md ? Required ? existing ? Current file inventory for this module.
- FILE_TREE.txt ? Required ? existing ? Current file tree for this module.

## Documentation

- README.md ? Optional ? existing ? Overview and scaffold notes.
- DEEP_DIVE.md ? Optional ? existing ? Contract and done rationale.
- WORKFLOW.md ? Optional ? existing ? Step-by-step workflow.
- SCHEMA_ADDITIONS.md ? Optional ? existing ? Proposed schema additions.
- ARTIFACT_INVENTORY.md ? Optional ? existing ? Inventory of contract artifacts.
- CHANGELOG.md ? Optional ? planned ? Track contract version changes.

## Validators and automation

- scripts/validate_structure.ps1 ? Required ? existing ? Validates required structure and emits evidence.
- scripts/validate_manifest_schema.ps1 ? Required ? planned ? Validates module.manifest.yaml against schema.
- scripts/run_acceptance.ps1 ? Required ? planned ? Runs acceptance checks and emits evidence.
- scripts/run_validators.ps1 ? Optional ? planned ? Orchestrates full validation suite.

## Tests and fixtures

- tests/acceptance/ ? Required ? planned ? Acceptance tests for contract compliance.
- tests/fixtures/ ? Optional ? planned ? Sample inputs for tests.

## Library and implementation

- src/ ? Required ? planned ? Shared implementation code for validators/generators (if needed).
- config/config.yaml ? Optional ? planned ? Configuration for validators.
- config/config_schema.json ? Optional ? planned ? Schema for config.yaml.

## Evidence directories (required structure)

- evidence/ ? Required ? existing ? Evidence root.
- evidence/validation/ ? Required ? existing ? Validation evidence outputs.
- evidence/acceptance/ ? Required ? existing ? Acceptance evidence outputs.
- evidence/runs/ ? Required ? existing ? Per-run logs and metadata.

## Evidence outputs (generated)

- evidence/validation/structure_validation.json ? Generated ? planned ? Structure validation report.
- evidence/validation/manifest_schema_validation.json ? Generated ? planned ? Schema validation report.
- evidence/acceptance/structure_acceptance.json ? Generated ? planned ? Structure acceptance report.
- evidence/acceptance/contract_acceptance.json ? Generated ? planned ? Contract acceptance report.
- evidence/runs/run_YYYYMMDDTHHMMSS.json ? Generated ? planned ? Per-run metadata and results.

# Manifest Population Pass 2 Report

Task ID: MANIFEST-POP-PASS2-V1  
Generated: 2026-07-01T23:30:00Z  
Manifests updated: 34

## Precondition Results

| ID | Check | Result |
|----|-------|--------|
| P1 | Manifest count == 34 | PASS |
| P2 | Schema file parses | PASS |
| P3 | All 10 source files present and parse | PASS |
| P4 | All 34 manifests schema-valid pre-change | PASS |
| P5 | file_module_mapping.csv header correct | PASS |
| P6 | updated_trading_process_aligned.json keys present | PASS |

## Source File SHA-256 Hashes

| Source ID | Path | SHA-256 |
|-----------|------|---------|
| S1 | `EAFIX_auth_docs/01_canonical_registries/updated_trading_process_aligned.json` | `f794a0814e2699ac633e7ec1d4c9a1c0a8d5dccec3f466989c5264b577c77097` |
| S10 | `EAFIX_auth_docs/10_services_source_inventory_and_file_mapping/eafix_services_ai_reference_20260510.json` | `b99c1011451b699c3eb4368567c973df1af25e15deea931130eb629f058bcd1c` |
| S2 | `EAFIX_auth_docs/01_canonical_registries/process_step_catalog.json` | `3695f03160d6827ad889724d32923b175112706d4c163ad52eb382a82443b9f5` |
| S3 | `EAFIX_auth_docs/01_canonical_registries/module_catalog.json` | `1cdd67b6a0485f65d4c9f9617984a7c54e1f1a397e946a87beb04c15cc066288` |
| S4 | `EAFIX_auth_docs/01_canonical_registries/communication_channels.json` | `b65fc3ff84b7f89cd5eab499842e86a97dc99e0d4d26f839dd983948161ded14` |
| S5 | `EAFIX_auth_docs/01_canonical_registries/module_registry.json` | `768d92546751ca8e02c837f6b7a2c0f448ef25874ca82356b400efb7f1a99065` |
| S6 | `EAFIX_auth_docs/10_services_source_inventory_and_file_mapping/file_module_mapping.csv` | `7441ba8a0e25db2f8a28b58d96ea462208bd0959e8c99db9e33488c45a1e2b7d` |
| S7 | `EAFIX_auth_docs/02_module_architecture_and_atomic_migration/EAFIX module reconciliation worksheet.csv` | `fcb54428a2f330dd1815e2fffa2be50885e411e678a4e186e6efa65b25215a24` |
| S8 | `EAFIX_auth_docs/03_process_lifecycle_and_crosswalks/atonic to canonical crosswalk.csv` | `bf24ed1a3709e249566a9ebb981a7d766d5672590e67bb5d5bd1e281ea1139cf` |
| S9 | `EAFIX_auth_docs/00_doc_control_and_authority/active_project_standards_registry.json` | `bcd61d78a657c2a6df14b4fd3af3733cee79e3b77b5c99bb6709f40e0068fb83` |

## Per-Field Fill Counts

| Field | Populated (≥1 value) | Empty/null |
|-------|---------------------|------------|
| `dependencies` | 25 | 9 |
| `service_runtime.service_home` | 26 | 8 |
| `service_runtime.startup_entrypoints` | 18 | 16 |
| `file_ownership.owned_files` | 6 | 28 |
| `file_ownership.shared_files` | 11 | 23 |
| `process_binding.upstream_modules` | 25 | 9 |
| `process_binding.downstream_modules` | 23 | 11 |
| `communication_channels` | 4 | 30 |
| `migration_traceability` | 34 | 0 |
| `service_runtime.microservice_port` | 18 | 16 |

## Drift Observations

*No drift observations recorded.*

## Conflicts Encountered

*No conflicts encountered.*

## Gate Results

| Gate | Result |
|------|--------|
| G1: Schema validation 34/34 | PASS |
| G2: Still exactly 34 files | PASS |
| G3: No forbidden fields | PASS |
| G4: No Windows paths in manifests | PASS |
| G5: diff surface inside allowlist only | PASS |
| G6: manifest_version 1.1.0, identical last_updated_utc | PASS |

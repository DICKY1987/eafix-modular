# EAFIX Registry Ingestion Matrix — Skeleton (v0.1.0)

- Repository: `DICKY1987/eafix-modular`  ·  Pinned commit: `e846d04a6eede56e6b790701d0fa762fe90297d6`
- Generated: 2026-07-20T23:34:44Z  ·  Status: **skeleton_pending_owner_review**
- Extends: `registry_source_inventory.jsonl` (do **not** fork a parallel authority)

## Destination registries (authored .jsonl = write targets)

| registry | current records | authored path |
|---|---|---|
| module_registry | 34 | `EAFIX_auth_docs/01_canonical_registries/module_registry.jsonl` |
| contract_registry | 97 | `EAFIX_auth_docs/01_canonical_registries/contract_registry.jsonl` |
| process_registry | 26 | `EAFIX_auth_docs/01_canonical_registries/process_registry.jsonl` |
| integration_registry | 9 | `EAFIX_auth_docs/01_canonical_registries/integration_registry.jsonl` |
| configuration_registry | 7 | `EAFIX_auth_docs/01_canonical_registries/configuration_registry.jsonl` |
| operational_control_registry | 52 | `EAFIX_auth_docs/01_canonical_registries/operational_control_registry.jsonl` |
| operator_registry | 7 | `EAFIX_auth_docs/01_canonical_registries/operator_registry.jsonl` |
| decision_registry | 7 | `EAFIX_auth_docs/01_canonical_registries/decision_registry.jsonl` |
| reuse_registry | 12 | `EAFIX_auth_docs/01_canonical_registries/reuse_registry.jsonl` |
| artifact_registry | 40 | `EAFIX_auth_docs/01_canonical_registries/artifact_registry.jsonl` |
| registry_source_inventory (gov) | 13 | `EAFIX_auth_docs/01_canonical_registries/registry_source_inventory.jsonl` |
| registry_conflict_queue (gov) | 11 | `EAFIX_auth_docs/01_canonical_registries/registry_conflict_queue.jsonl` |

## Candidate source rows (new — not yet in source inventory)

| source_id | path | exists | priority | → registries | evidence | disposition | human gate |
|---|---|:---:|:---:|---|:---:|---|:---:|
| SRC-CONTRACT-EVENTS | `contracts/events/ (7)` | OK | P1 | contract | E2 | evidence_primary_authored_candidate | no |
| SRC-CONTRACT-MODELS | `contracts/models/ (8)` | OK | P1 | contract | E1 | evidence_primary | no |
| SRC-CONTRACT-SNAPSHOT | `EAFIX_auth_docs/generated/registries/contract_registry.current.json` | OK | P1 | contract | E2 | generated_projection_never_write_target | yes |
| SRC-CONTRACT-TRIGGERS | `contracts/triggers/ (8)` | OK | P1 | operational_control,contract | E2 | evidence_reference | no |
| SRC-CTX-SCHEMA | `context_packet_schema.json` | OK | P1 | module,contract,artifact,process,operational_control,integration | E2 | evidence_reference | no |
| SRC-CTX-PACKETS | `context_packets/*/context_packet.json (27)` | OK | P1 | module,contract,artifact,process,operational_control,integration,reuse | E2 | evidence_stale_regenerate_first | yes |
| SRC-DAG-CONFIG | `dag/config/ + dag/patterns/ (3)` | OK | P1 | process,operational_control,integration,reuse,module | E2 | evidence_needs_crosswalk | yes |
| SRC-MANIFEST-GAP-REPORT | `EAFIX_auth_docs/contracts_registry/manifest_generator_gap_report.md` | OK | P3 | contract,module,artifact,integration | E4 | design_evidence_reference_only | no |
| SRC-MANIFESTS-BUNDLE | `EAFIX_auth_docs/manifests/ (6)` | OK | P1 | module | E2 | evidence_primary | no |
| SRC-REPO-AUTOOPS | `config/repo_autoops.yaml` | OK | P2 | configuration,operational_control | E2 | evidence_reference | no |
| SRC-EAREG-GENERATOR | `EA-REG/generate_three_artifact_catalogs.py` | OK | P2 | reuse | E1 | reuse_logic_only_not_authority | no |
| SRC-CONTRACT-VALIDATORS | `contracts/validate_*.py (2)` | OK | P2 | reuse | E1 | reuse_logic_only_not_authority | no |
| SRC-EAREG-SUPERSEDED | `EA-REG/superseded/ (7)` | OK | EXCLUDE | — | E4 | superseded_excluded | no |
| SRC-ARCHIVE-DNR | `EAFIX_auth_docs/99_archive_superseded_do_not_route/` | OK | EXCLUDE | — | E4 | excluded_do_not_route | no |

## Open owner decisions

- OD-1: IndicatorVector vs IndicatorSnapshot naming/version conflict (contracts/events)
- OD-2: OrderIntent.side vocabulary conflict
- OD-3: two divergent ReentryDecision definitions
- OD-4: regenerate 27 context_packets (stale 2026-05-18, backslash paths) before ingest? y/n
- OD-5: DAG node-id -> process_step_catalog crosswalk ownership
- OD-6: component identity - distinct entity, derived, or retired? (no component registry found)
- OD-7: promote any generated snapshot record to authored .jsonl? (cutover gate)

## Existence-check findings
- Path correction: `context_packets/context_packet_schema.json` (404) → actual `context_packet_schema.json` at repo root.
- Duplicate pattern: `contracts/models/` has numeric-prefixed **and** plain copies — dedup before ingest.
- 13 existing inventory entries pinned to stale `32694cac` — re-verify on ingestion.

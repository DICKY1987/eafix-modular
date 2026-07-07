# Source Priority Recommendation

**Repository:** DICKY1987/eafix-modular
**Commit SHA:** `86fda07c6af16a52a679fb3cd6af2552b9eda32e`
**Branch:** `claude/eafix-deep-repository-search`
**Generated:** 2026-07-04 (UTC)

This report recommends the authority precedence for the manifest generator when populating contract fields. It refines the ordering already present in `tools/manifest_generation/source_loaders.py:95-109` (`conflict_resolution_order`).

## Current Ordering (as-is)

`tools/manifest_generation/source_loaders.py:95-109` defines:

1. `routing_authority`
2. `module_universe_vnext`
3. `manifest_schema`
4. `module_catalog_enrichment`
5. `process_step_catalog`
6. `aligned_process`
7. `communication_channels`
8. `ui_catalog`
9. `mt4_authoritative`
10. `file_mapping`
11. `service_runtime`
12. `module_map`
13. `existing_draft_bundle`

This list does not include `contracts/events/` or `contracts/models/`, which explains why event contracts cannot be resolved.

## Recommended Ordering (per-field)

Authority precedence must be evaluated **per manifest field**, not once for the whole document. The following table specifies the ordering per contract-field.

### For `contracts.output_contracts[].name` (contract name resolution)

1. `process_step_catalog` (`EAFIX_auth_docs/01_canonical_registries/process_step_catalog.json`) — canonical process step contract names.
2. `existing_draft_bundle` — validate producer/consumer graph consistency.
3. `communication_channels` — check for `_v<n>` versioned aliases (e.g., `PriceTick_v1`).
4. `ui_catalog` — for UI surfaces only.

### For `contracts.output_contracts[].schema_ref` and `.version`

1. **`contracts/events/*.json`** (new source) — canonical JSON schema. `schema_ref = "contracts/events/<file>"`, `version = <parsed from filename>`.
2. `contracts/models/*.py` (new source) — if no JSON schema, use the Pydantic model file as `schema_ref` and mark `version = "pydantic-only"`.
3. `ui_catalog` — for UI-DATA-*, UI-API-*, UI-WS-* only. `schema_ref = ui_catalog contract_id` and `version = "(ui surface)"`.
4. If none of the above → `schema_ref = null`; add to unresolved conflicts.

### For `contracts.output_contracts[].description`

1. JSON schema `title` / `description` field (from `contracts/events/*.json`).
2. Pydantic class docstring (from `contracts/models/*.py`).
3. `process_step_catalog` step description.
4. `ui_catalog` contract description.

### For `produced_by_module` and `consumed_by_modules`

1. `existing_draft_bundle` (already-computed producer/consumer graph — 56 contracts fully mapped).
2. `process_step_catalog` (cross-check against `input_contracts` / `output_contracts` fields).
3. `communication_channels` (transport-level producer/consumer bindings).

### For `contracts.output_contracts[].file_ownership`

1. `file_mapping` (`EAFIX_auth_docs/10_services_source_inventory_and_file_mapping/file_module_mapping.csv`).
2. `eafix_module_files_ai_reference.json` — narrative fallback only.
3. `service_runtime` — runtime evidence when the above are silent.

## Recommended Full Ordering (for `conflict_resolution_order`)

Update `tools/manifest_generation/source_loaders.py:95-109` `conflict_resolution_order` to:

1. `routing_authority`
2. `module_universe_vnext`
3. `manifest_schema`
4. **`contracts_events_dir`** *(new)* — canonical JSON schemas
5. **`contracts_models_dir`** *(new)* — Pydantic runtime models
6. `module_catalog_enrichment`
7. `process_step_catalog`
8. `aligned_process`
9. `communication_channels`
10. `ui_catalog`
11. `mt4_authoritative`
12. `file_mapping`
13. `service_runtime`
14. `module_map`
15. `existing_draft_bundle`
16. **`contracts_tests_fixtures`** *(new, evidence-only)* — for `example_candidates`

## Placement Rationale

- **`contracts_events_dir` at position 4** — outranks module catalogs because the JSON schema is the runtime contract. Any conflict with a catalog description must resolve in favor of the schema.
- **`contracts_models_dir` at position 5** — Pydantic model reflects live runtime behavior. Placed second only to the JSON schema.
- **`ui_catalog` remains at position 10** — authoritative only for external surfaces, not internal events.
- **`existing_draft_bundle` last** — used only as evidence of what was previously emitted; must never override an authoritative source.
- **`contracts_tests_fixtures` at position 16** — evidence-only; provides `example_candidates` but must not be used to resolve schema conflicts.

## Conflict Resolution Rules

For each contract, once a `schema_ref` is chosen from position ≤5, all lower-priority sources are treated as advisory:

- If `process_step_catalog` disagrees with `contracts_events_dir` on producer, emit an `unresolved_conflict` entry citing both — schema wins for the manifest field but the conflict must be logged for reviewer.
- If `existing_draft_bundle` field disagrees with the schema, override in the new manifest and log the diff.
- Placeholder tokens (`Either`, `needs_review`) are filtered before ranking.

## Application to Known Conflicts

| Contract | Conflict | Resolution under recommended ordering |
|---|---|---|
| `OrderIntent` | JSON says BUY/SELL, Pydantic says LONG/SHORT | JSON schema wins (position 4). Log conflict for review. Pydantic model must be aligned separately before shipping. |
| `CalendarEvent` | Canonical schema uses MEDIUM; some CSV artifacts use MED | JSON schema wins. All non-schema references must be normalized. |
| `ReentryDecision` | Event vs CSV dual definition | Event schema `1199900008260118_ReentryDecision@1.0.json` wins for the event field. CSV model is persistence-layer contract; recommend renaming CSV class to `ReentryDecisionRow`. |
| `IndicatorVector` vs `IndicatorSnapshot` | Schema name differs from bundle/process name | Schema (`IndicatorVector@1.1`) wins for schema_ref. Manifest contract_name preserves `IndicatorSnapshot` if reviewer approves; otherwise rename bundle. |
| `PositionSummary` (gui) | GUI-specific model vs bundle input contract | These are distinct contracts (different domains). Manifest for U2_GUI_GATEWAY should reference the GUI variant; manifest for S1_SIGNAL_ENGINE should reference the core-domain variant. |

## Non-Content Modifications Only

This report is evidence and recommendation only; it does not modify:

- `tools/manifest_generation/source_loaders.py`
- `tools/manifest_generation/manifest_builder.py`
- Any manifest under `EAFIX_auth_docs/manifests/module_manifests/`
- Any schema under `contracts/events/`
- Any Pydantic model under `contracts/models/`

Adoption of the recommendation is a separate, reviewer-approved change.

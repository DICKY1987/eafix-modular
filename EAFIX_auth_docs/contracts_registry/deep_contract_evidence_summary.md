# Deep Contract Evidence Summary

**Repository:** DICKY1987/eafix-modular
**Commit SHA:** `86fda07c6af16a52a679fb3cd6af2552b9eda32e`
**Branch:** `claude/eafix-deep-repository-search`
**Generated:** 2026-07-04 (UTC)

This report accompanies `deep_contract_evidence_inventory.json` and interprets its findings for the 34 atomic-module manifests.

## Scope

The manifest bundle in `EAFIX_auth_docs/02_module_architecture_and_atomic_migration/eafix module manifests bundle.json` declares 34 modules with 56 distinct input/output contract names, plus additional UI, persistence, and MT4-bridge contracts that appear in the process step catalog, UI catalog, and Pydantic models. The current manifest generator (`tools/manifest_generation/manifest_builder.py`) emits contract entries with empty `schema_ref`, empty `description`, empty `version`, empty `produced_by_module`, and empty `consumed_by_modules`. This inventory identifies which contracts have enough authoritative evidence to populate these fields and which do not.

## Headline Counts

| Status | Count | Meaning |
|---|---|---|
| `already_schema_defined` | 4 | JSON schema present under `contracts/events/` |
| `conflict` | 3 | Divergent authoritative definitions (see below) |
| `model_defined_no_schema` | 7 | Pydantic model exists but no JSON schema |
| `ui_catalog_defined` | 27 | Declared authoritatively in `ui_catalog.json` |
| `source_defined_only` | 37 | Referenced by process step catalog / bundle but no schema or model |
| `underivable` | 15 | Referenced but no field-level authority anywhere |
| `placeholder_error` | 2 | `Either`, `needs_review` — not real contracts |
| **Total** | **95** | |

## Confirmed Canonical Event Schemas (7 files)

Under `contracts/events/`:

- `1199900003260118_CalendarEvent@1.0.json`
- `1199900004260118_ExecutionReport@1.0.json`
- `1199900005260118_IndicatorVector@1.1.json`
- `1199900006260118_OrderIntent@1.2.json`
- `1199900007260118_PriceTick@1.0.json`
- `1199900008260118_ReentryDecision@1.0.json`
- `1199900009260118_Signal@1.0.json`

All are Draft-07 JSON schemas and are validated at CI-time via `contracts/2099900015260118_validate_json_schemas.py:1-267` using `Draft202012Validator`. Corresponding Pydantic models live in `contracts/models/2099900017260118_event_models.py:26-177` (event models), `2099900016260118_csv_models.py:52-200` (CSV models) and `2099900018260118_json_models.py:100-276` (JSON models with `IndicatorRecord`, `OrderIn`, `OrderOut`, `HybridId`).

## Confirmed Naming/Value Conflicts

1. **OrderIntent.side enum divergence** — JSON schema `1199900006260118_OrderIntent@1.2.json:26-33` uses `[BUY, SELL]`. Pydantic `event_models.py:75-88` uses `OrderSide=[LONG, SHORT]` on `OrderIntent.side`. This is a semantic conflict, not a mere alias.
2. **CalendarEvent projections** — Canonical `contracts/events/1199900003260118_CalendarEvent@1.0.json` uses `impact` enum `[LOW, MEDIUM, HIGH]`. Some downstream artifacts reference `MED`. The gui-gateway defines its own `CalendarEvent` for dashboard rendering in `services/gui-gateway/src/2099900157260118_models.py:94-104`. These should be labeled projections, not rival contracts.
3. **ReentryDecision dual definition** — `event_models.py:162-177` defines it as a matrix decision event (`reentry_key/generation/should_reenter/matrix_outcome`). `csv_models.py:86-132` defines it as a CSV row (`trade_id/hybrid_id/outcome_class/duration_class/reentry_action`). Fields do not overlap. Split into `ReentryDecisionEvent` and `ReentryDecisionRow` (or explicitly document the CSV as persistence layer of the event).
4. **IndicatorVector vs IndicatorSnapshot naming** — Canonical schema is `IndicatorVector@1.1`; process step catalog and bundle refer to `IndicatorSnapshot`. Choose one authoritative name; document the alias.
5. **PositionSummary** — Referenced by `S1_SIGNAL_ENGINE` input, but gui-gateway defines its own `PositionSummary` in `services/gui-gateway/src/2099900157260118_models.py:50-62` with dashboard-specific fields. These are semantically different contracts.

## Placeholder / Non-Contract Tokens

- **`Either`** — Confirmed placeholder promoted from narrative text `Either (a) new RoutedOrderIntent executed via O1_ORDER_ROUTER, or (b) suppression/cooldown state update`. Appears in `EAFIX_auth_docs/10_services_source_inventory_and_file_mapping/eafix_module_files_ai_reference.json:1946-1959` as `contract_type: "Either"`. Must be excluded from generator inputs.
- **`needs_review`** — Filler token; not a contract.

## UI Catalog Authority

`EAFIX_auth_docs/01_canonical_registries/ui_catalog.json` (1,977 lines) is the single source of truth for external UI surfaces. It defines:

- 8 UI-DATA-* data contracts (lines 1426–1556) — projections of core events for dashboard consumption.
- 8 UI-API-DASHBOARD-* REST endpoints (lines 1556–1642) served by U1_DASHBOARD_BACKEND (port 8092).
- 6 UI-API-GUI-* REST endpoints (lines 1642–1713) served by U2_GUI_GATEWAY (port 8091).
- UI-WS-GUI-GATEWAY (line 1713) and UI-WS-DASHBOARD-BACKEND (line 1734) websocket endpoints.
- UI-WS-SIGNALS / UI-WS-POSITIONS / UI-WS-ALERTS channel definitions (lines 1749–1780).

These are not event contracts in the `contracts/events/` sense; they are external surface contracts. Manifest generator should reference the `ui_catalog contract_id` and set `schema_ref="(UI surface, not event schema)"`.

## Producer / Consumer Mapping

The manifest bundle (already recorded) gives a complete producer/consumer graph for all 56 event contracts across modules `50000000000000000001`–`50000000000000000034`. The generator needs only to join this graph with the schema files under `contracts/events/` to populate `produced_by_module` / `consumed_by_modules` / `schema_ref` per module manifest. See `deep_contract_evidence_inventory.json:contract_inventory[*].{candidate_producer_modules,candidate_consumer_modules}` for the join keys.

## Modules With Zero Contracts in Bundle

- `50000000000000000033` (SK1_PLUGIN_INTERFACE)
- `50000000000000000034` (SK2_IDEMPOTENCY)

These are shared-kernel modules with empty `input_contracts` and `output_contracts` in the bundle. They should be declared as infrastructure modules, not contract producers.

## Test Evidence

Contract-conformance test fixtures exist for a subset:

- `tests/contracts/fixtures/1099900002260118_active_calendar_signals_valid.csv`
- `tests/contracts/fixtures/1099900003260118_reentry_decisions_valid.csv`
- `tests/contracts/fixtures/1199900032260118_hybrid_id_valid.json`
- `tests/contracts/fixtures/1199900033260118_indicator_record_valid.json`
- `tests/contracts/fixtures/1199900034260118_orders_in_valid.json`
- `tests/contracts/fixtures/1199900035260118_orders_out_valid.json`

Only a small fraction of the 95 catalogued contracts have test fixtures. Fixtures should be added for every `already_schema_defined` and `model_defined_no_schema` contract before the manifest generator is trusted to fill `schema_ref` end-to-end.

## Recommended Next Actions (Evidence Only)

See `manifest_generator_gap_report.md` for the generator-side changes required to populate manifests, and `source_priority_recommendation.md` for the recommended authority-precedence order to feed the generator.

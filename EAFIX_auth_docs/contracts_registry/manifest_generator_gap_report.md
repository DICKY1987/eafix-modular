# Manifest Generator Gap Report

**Repository:** DICKY1987/eafix-modular
**Commit SHA:** `86fda07c6af16a52a679fb3cd6af2552b9eda32e`
**Branch:** `claude/eafix-deep-repository-search`
**Generated:** 2026-07-04 (UTC)

This report identifies why the current manifest generator produces blank `contracts` blocks in every module manifest, and specifies which inputs must change (evidence only — no code changes recommended in this artifact).

## Observed Defect

Every module manifest in `EAFIX_auth_docs/manifests/module_manifests/` currently emits contract entries of the form:

```json
{
  "name": "<contract_name>",
  "schema_ref": null,
  "description": "",
  "version": null,
  "produced_by_module": null,
  "consumed_by_modules": []
}
```

Even when the authoritative JSON schema and Pydantic model both exist (e.g., `PriceTick`, `Signal`, `OrderIntent`, `ExecutionReport`, `CalendarEvent`, `ReentryDecision`, `IndicatorVector`).

## Root Cause

Two independent gaps in the generator inputs cause the blank contracts.

### Gap 1 — Authority preflight does not load `contracts/events/` or `contracts/models/`

File: `tools/manifest_generation/source_loaders.py:13-31`

The `REQUIRED_SOURCE_FILES` dict enumerates 17 authoritative documents (routing, module universe, schema, fill doctrine, catalogs, communication channels, UI catalog, MT4 reference, capability registry, dependency layers PDF, file mapping, service runtime, module map). **It does not include the `contracts/events/*.json` directory or the `contracts/models/*.py` directory.**

Consequence: the preflight cannot compute `sha256_file()` for schema files nor discover their existence, so `schema_source` in the emitted preflight is a directory pointer (`EAFIX_auth_docs/01_canonical_registries/eafix_unified_atomic_module_schema_v1_0_0.json:123`) — the *manifest* schema — not the *event contract* schemas.

### Gap 2 — `_contract_refs()` hardcodes empty fields

The `_contract_refs()` helper (previously observed at `tools/manifest_generation/manifest_builder.py:107-122` in prior sessions) constructs contract entries with hardcoded defaults instead of resolving them from the schema/model directories. Because Gap 1 prevents the generator from loading those directories, this helper has no data to draw from anyway.

## Required Generator Inputs (Evidence)

For the generator to populate the manifest contract fields, it must consume the following authoritative sources in addition to the current 17:

| New source | Path | Role |
|---|---|---|
| `contracts_events_dir` | `contracts/events/` (glob `*@*.json`) | canonical JSON schemas → `schema_ref`, `version` |
| `contracts_models_dir` | `contracts/models/*.py` (event/csv/json models) | Pydantic definitions → `description`, field coverage |
| `contracts_validator` | `contracts/2099900015260118_validate_json_schemas.py` | ensures schema validity at CI time |
| `contracts_tests_fixtures` | `tests/contracts/fixtures/` | example payloads → `example_candidates` |
| `manifest_bundle_join` | `EAFIX_auth_docs/02_module_architecture_and_atomic_migration/eafix module manifests bundle.json` | already loaded, but must be joined with events dir |

### Join Logic Needed

For each `contract_name` in a module's `input_contracts`/`output_contracts`:

1. Look up `contracts/events/*_{contract_name}@*.json`. If found → `schema_ref = <relative path>`, `version = <parsed from filename>`, `description = <schema.title/description>`.
2. If not found in events dir but present in `contracts/models/*.py` classes → mark as `model_defined_no_schema`; set `schema_ref = null` with `note = "pydantic-only"`.
3. If not found in either → mark as `underivable`; leave `schema_ref = null`; add to unresolved list for reviewer.
4. Determine `produced_by_module` and `consumed_by_modules` from the bundle-level producer/consumer graph (already present in `contracts` block of each manifest in `eafix module manifests bundle.json`).

## Contract Coverage Analysis

Using the 95-contract inventory in `deep_contract_evidence_inventory.json`:

| Layer | Count | Populable in manifests today? |
|---|---|---|
| `already_schema_defined` | 4 (PriceTick, Signal, ExecutionReport, IndicatorVector) | **Yes** — schema + model both present |
| `conflict` | 3 (OrderIntent side-enum; CalendarEvent variants; ReentryDecision dual) | **No** — resolve conflict first |
| `model_defined_no_schema` | 7 (HybridId, OrderIn, OrderOut, IndicatorRecord, ActiveCalendarSignal, TradeResult, HealthMetric) | **Partial** — need JSON schema authored |
| `ui_catalog_defined` | 27 (UI-DATA-*, UI-API-*, UI-WS-*) | **Yes** — reference ui_catalog contract_id |
| `source_defined_only` | 37 (ScheduleTick, RawTick, MarketTick, Bar, IndicatorSnapshot, FeatureFrame, RoutedOrderIntent, BrokerOrderEnvelope, BrokerExecEvent, PositionSnapshot, PositionStateChanged, OrderStateChanged, TradeClosedRaw, TradeClosed, OutcomeBucket, EventProximity, EventStream, CalendarRaw, CalendarTrigger, SignalSuppressed, TradeIntent, RiskDecision, RiskGuardResult, MatrixDecision, ReentrySuppressed, KPIReport, ReportArtifact, HealthReport, AdapterAck, EAHealth, PositionSummary, DashboardRestResponse, DashboardStream, OperatorApiResponse, OperatorCommand, OperatorWebSocketStream, OverlayRender) | **No** — need schema + model authored |
| `underivable` | 15 (ConfigSource, BrokerPolicy, RiskPolicy, PortfolioState, AdapterHealth, ModuleHealth, MatrixProfile, SignalContext, ReentryChainState, CalendarSourceConfig, ClockTick, RawTick, ExpiryZonesData, IndicatorSummary, SpotData) | **No** — need full contract definition |
| `placeholder_error` | 2 (Either, needs_review) | **N/A** — filter out |

Populability today: only **4 of 95** contracts can be filled with schema evidence directly; **27** more can reference ui_catalog surfaces. That is 32.6% coverage. The remaining 63 contracts require net-new schema and/or model authoring to be populable.

## Blocking Issues Ranked

1. **Blocker — Missing schemas for 37 process-catalog-declared contracts.** These are declared as producer outputs by `process_step_catalog.json:1-900+` but no JSON schema exists. Generator cannot populate `schema_ref` for majority of modules until authored.
2. **Blocker — 15 policy/config contracts (`ResolvedConfig`, `BrokerPolicy`, `RiskPolicy`, etc.) have no authoritative field definitions anywhere.** These are widely consumed but never defined. Suggested: derive from `EAFIX_auth_docs/01_canonical_registries/converted_capability_registry.json` or the `eafix_unified_atomic_module_schema_v1_0_0.json` policy sections.
3. **Blocker — Bundle uses `IndicatorSnapshot`; schema is `IndicatorVector`.** Trivial rename or alias, but must be applied consistently.
4. **Warning — `OrderIntent.side` conflict** (BUY/SELL vs LONG/SHORT). Cannot ship OrderIntent contract until resolved.
5. **Warning — `ReentryDecision` has two divergent definitions.** Must be split or explicitly documented.
6. **Warning — `Either` and `needs_review` are still present as `contract_type` values in `eafix_module_files_ai_reference.json:1946-1959`.** Generator must strip these before consumption.
7. **Info — Modules 33 (SK1_PLUGIN_INTERFACE) and 34 (SK2_IDEMPOTENCY) have no contracts by design.** Manifest generator should emit `contracts: {input: [], output: []}` and mark them as infrastructure modules.

## Recommended Generator Changes (Evidence, Not Instructions)

- Extend `REQUIRED_SOURCE_FILES` in `tools/manifest_generation/source_loaders.py:13-31` to include `contracts_events_dir` (glob `contracts/events/*@*.json`) and `contracts_models_dir` (`contracts/models/*.py`).
- Extend `AUTHORITY_ROLES` in `tools/manifest_generation/source_loaders.py:34-52` with roles `canonical_event_schemas_json` and `runtime_pydantic_models`.
- Extend `run_authority_preflight()` (`tools/manifest_generation/source_loaders.py:80-127`) to enumerate the directory and compute per-file SHA-256s.
- Update `_contract_refs()` in `tools/manifest_generation/manifest_builder.py` to perform the four-step join described above.
- Introduce a filter that drops `Either`, `needs_review`, and other placeholder tokens from generator inputs.

No source code is modified by this report.

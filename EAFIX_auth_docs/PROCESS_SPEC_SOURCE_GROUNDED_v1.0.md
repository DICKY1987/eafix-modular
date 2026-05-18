# HUEY_P / EAFIX — Source-Grounded End-to-End Process Specification
**Document version**: 1.0
**Derived from**: process_version 2.0.0 (HUEY_P_EAFIX_END_TO_END)
**Evidence base**: source files read March 2026
**Status of this document**: DRAFT — replaces updated_trading_process_aligned.yaml + 2026012201113002_updated_trading_process_v2.yaml as the authoritative, gap-annotated process record

---

## IMPORTANT PREAMBLE — THREE OVERLAPPING SYSTEM REALITIES

The source evidence reveals three partially-disjoint architectural layers that MUST NOT be silently merged:

| Layer | Description | Evidence Basis |
|---|---|---|
| **Layer A — Canonical contract/process flow** | 26-step process in updated_trading_process_aligned.yaml / v2.yaml, aligned to MODULE_REGISTRY v1.0.0 | YAML process files |
| **Layer B — EAFIX microservice runtime** | 20+ Python FastAPI/async services, Redis pub/sub, CSV transport, HTTP routing | services/ source files |
| **Layer C — HUEY_P / MT4 bridge & EA** | 7000+ line MQL4 straddle EA, DLL socket bridge, CSV signal files | tactical spec, mt4/ source, docs |

Where these layers conflict, this document marks the conflict explicitly and does not resolve it silently.

---

## SECTION 1 — SOURCE ANALYSIS SUMMARY

### 1.1 System Realities Found

**Layer A (Canonical process)** describes a linear 26-step chain. All steps have `module_id` labels and `responsible` file names. Most `entrypoint_files` fields either point to wrong services or are empty. The responsible file names are aspirational (e.g., `configuration_service.py`, `bar_builder.py`, `feature_packager.py`) — none confirmed present as implemented source.

**Layer B (EAFIX microservice runtime)** is partially implemented. Confirmed services with substantive source code:
- `services/calendar-ingestor/` — has main, config, ingestor, ff_auto_downloader
- `services/transport-router/` — has main, config, watcher, validator, router, metrics
- `services/event-gateway/` — has main, config, router, filter, transformer
- `services/reentry-engine/` — has main, config, processor, decision_client, metrics
- `services/reentry-matrix-svc/` — has main, config, processor, resolver, metrics
- `shared/reentry/` — has hybrid_id.py, vocab.py, indicator_validator.py (confirmed implemented)
- `contracts/models/` — has csv_models.py (confirmed implemented with checksum logic)
- `contracts/events/` — has JSON schemas for 7 event types

Services with only stub/plugin files (no main processor):
- `services/signal-generator/src/` — directory exists, contains only `__pycache__`, no confirmed source
- `services/risk-manager/src/` — contains only `2099900183260118_plugin.py`, no main
- `services/execution-engine/src/` — contains only `2099900144260118_plugin.py`, no main
- `services/flow-orchestrator/src/` — directory exists, contains only `__pycache__`, no confirmed source
- `services/flow-monitor/`, `services/indicator-engine/`, `services/data-ingestor/`, `services/dashboard-backend/`, `services/gui-gateway/`, `services/reporter/`, `services/telemetry-daemon/` — not confirmed with substantive source

**Layer C (HUEY_P/MT4)** is documented extensively in `0299900001260118_CURRENT_huey_p_tactical_spec.txt` (v2.1, Aug 2025) and `0199900003260118_HUEY_P_EA_ExecutionEngine_8.md`. The actual EA file present in repo (`HUEY_P_EA_ExecutionEngine_8.mql4`) is explicitly a functional replacement SMA crossover EA (164 lines), NOT the real 7000+ line straddle system. The real EA is referenced as `EAFIX.mq4` — not present in repo. The DLL bridge (`MQL4_DLL_SocketBridge.dll`) is described in the tactical spec but not present in repo as a compiled artifact.

### 1.2 Confirmed Runtime Artifacts

| Artifact | Path | Confirmed By |
|---|---|---|
| Calendar ingestor main | `services/calendar-ingestor/src/2099900093260118_main.py` | YAML entrypoint_files (Steps 2–6) |
| Transport router main | `services/transport-router/src/2099900199260118_main.py` | YAML entrypoint_files (Steps 14–17, 25) |
| Event gateway main | `services/event-gateway/src/2099900141260118_main.py` | YAML entrypoint_files (Steps 18, 22) |
| Reentry matrix svc main | `services/reentry-matrix-svc/src/2099900174260118_main.py` | YAML entrypoint_files (Step 23) |
| Reentry matrix processor | `services/reentry-matrix-svc/src/2099900177260118_processor.py` | Direct read — full implementation |
| Reentry matrix resolver | `services/reentry-matrix-svc/src/2099900178260118_resolver.py` | Direct read — confirmed |
| Reentry engine main | `services/reentry-engine/src/2099900166260118_main.py` | YAML entrypoint_files (Step 24) |
| Reentry engine processor | `services/reentry-engine/src/2099900169260118_processor.py` | Direct read — full implementation |
| Reentry engine decision client | `services/reentry-engine/src/2099900164260118_decision_client.py` | Direct read — confirmed |
| hybrid_id Python impl | `shared/reentry/2099900218260118_hybrid_id.py` | Direct read — full implementation |
| ReentryHelpers MQL4 | `mt4/2299900001260118_ReentryHelpers.mq4` | Direct read — full implementation |
| CSV models | `contracts/models/2099900016260118_csv_models.py` | Direct read — confirmed |
| Hybrid ID spec | `contracts/identifiers/0199900025260118_hybrid_id.md` | Confirmed |
| CSV atomic write policy | `contracts/policies/0199900026260118_csv_atomic_write.md` | Confirmed |
| Parameter sets config | `config/1199900002260118_parameter_sets.json` | Confirmed |
| Reentry vocabulary | `shared/reentry/1199900031260118_reentry_vocab.json` | Confirmed |
| Risk manager plugin | `services/risk-manager/src/2099900183260118_plugin.py` | Plugin only — no main |
| Execution engine plugin | `services/execution-engine/src/2099900144260118_plugin.py` | Plugin only — no main |

### 1.3 Planned / Conceptual Artifacts

| Artifact | Evidence |
|---|---|
| `EAFIX.mq4` (7000+ line straddle EA) | Referenced in YAML step 17, tactical spec; NOT in repo |
| `MQL4_DLL_SocketBridge.dll` | Referenced in tactical spec; NOT in repo |
| `flow-orchestrator` service (full) | Directory + `__pycache__` only; no confirmed source |
| `signal-generator` service (full) | Directory + `__pycache__` only; no confirmed source |
| `configuration_service.py` | Named in Step 1; not confirmed in repo |
| `scheduler.py` | Named in Step 2; not confirmed in repo |
| `market_feed_adapter.py` | Named in Step 7; not confirmed in repo |
| `bar_builder.py` | Named in Step 8; not confirmed in repo |
| `indicator_engine.py` | Named in Step 9; not confirmed in repo |
| `feature_packager.py` | Named in Step 10; not confirmed in repo |
| `signal_generator.py` | Named in Step 11; not confirmed in repo |
| `intent_builder.py` | Named in Step 12; not confirmed in repo |
| `risk_manager.py` | Named in Step 13; not confirmed (only plugin.py) |
| `order_intent_compiler.py` | Named in Step 14; not confirmed in repo |
| `order_router.py` | Named in Step 15; not confirmed in repo |
| `transport_service.py` | Named in Step 16; not confirmed (transport-router main is different) |
| `oms.py` | Named in Step 19; not confirmed in repo |
| `trade_close_classifier.py` | Named in Step 20; not confirmed in repo |
| `outcome_bucketizer.py` | Named in Step 21; not confirmed in repo |
| `proximity_evaluator.py` | Named in Step 22; not confirmed in repo |
| `health_service.py` | Named in Step 26; not confirmed in repo |
| Redis streams (production) | Configured in event-gateway; not confirmed as active production store |
| Postgres | Mentioned as optional enterprise; NOT currently active per source |
| SQLite (per-symbol) | Confirmed in tactical spec (Python GUI); not confirmed in microservice layer |

### 1.4 Source Conflicts and Ambiguities

**CONFLICT-01: EA file identity**
- Process doc (Step 17) names responsible file as `EAFIX.mq4`
- Repo contains `HUEY_P_EA_ExecutionEngine_8.mql4` which is a 164-line SMA crossover EA with internal comment stating it is "a functional replacement" because "the original file was not available"
- Tactical spec describes a 7000+ line straddle EA
- RESOLUTION: `EAFIX.mq4` / 7000-line straddle EA is the canonical EA; it is NOT present in repo; the `.mql4` file in repo is a placeholder

**CONFLICT-02: hybrid_id format — Python vs MQL4**
- Python (`hybrid_id.py`): underscore-delimited — `OUTCOME_DURATION_PROXIMITY_CALENDAR_DIRECTION_GENERATION[_SUFFIX]`
- MQL4 (`ReentryHelpers.mq4`): tilde-delimited — `SIG~TB~OB~PB~G`
- MQL4 field order: SIG (signal_id), TB (time_bucket), OB (outcome_bucket), PB (proximity_bucket), G (generation) — DIFFERENT field ordering from Python and DIFFERENT field semantics (SIG maps to calendar/signal_id, not outcome)
- RESOLUTION: These are two different identifier formats serving different purposes. Python hybrid_id is the canonical external identifier. MQL4 reentry_key is an internal EA-side key. Parity mapping is UNDEFINED in source.

**CONFLICT-03: comment_suffix hash algorithm mismatch**
- Python: SHA-256 based (confirmed in `hybrid_id.py` line 233)
- MQL4: FNV32→Base32 (confirmed in `ReentryHelpers.mq4` lines 59–88)
- MQL4 file itself states: "NOT identical to SHA1"; "prefer using suffix from Python in CSV"
- RESOLUTION: Python is authoritative for suffix. MQL4 local computation is a fallback only. Cross-language parity is NOT guaranteed for suffix field.

**CONFLICT-04: entrypoint_files mapping errors in process YAML**
- Step 11 (Signal Engine, S1_SIGNAL_ENGINE) has `entrypoint_files` pointing to `compliance/auto-remediation/2099900012260118_remediation-engine.py` — clearly wrong
- Step 17 (EA Executor, B2_MT4_EA_EXECUTOR) has `entrypoint_files` pointing to `services/transport-router/src/2099900199260118_main.py` — wrong service
- Steps 1, 8, 10, 12, 13, 19, 20, 21, 25 have empty `entrypoint_files`
- RESOLUTION: Marked per step in Section 3

**CONFLICT-05: flow-orchestrator ownership vs. implementation**
- Process doc Step 25 names `orchestrator` as responsible
- Process docs claim flow-orchestrator owns signal receipt, calendar gate, reentry coordination
- `services/flow-orchestrator/src/` contains only `__pycache__` — no confirmed source
- RESOLUTION: flow-orchestrator is PLANNED, not implemented

**CONFLICT-06: proximity_state derivation in reentry-engine**
- Process doc (Steps 22–23) describes E2_PROXIMITY_EVALUATOR as a dedicated module consuming `CalendarEvent + ClockTick`
- Confirmed source (`reentry-engine/processor.py` lines 278–291) uses hardcoded time-of-day heuristics (hour-of-day ranges) with no calendar service integration
- RESOLUTION: Real-time calendar-driven proximity is PLANNED; current implementation uses time-of-day approximation only

**CONFLICT-07: calendar_id derivation in reentry-engine**
- Process docs imply calendar_id flows from CalendarEvent through the chain into reentry
- Confirmed source (`reentry-engine/processor.py` lines 293–303) uses hardcoded heuristic: "USD" in symbol AND pips > 20 → "CAL8_USD_UNKNOWN_H", else "NONE"
- RESOLUTION: Real calendar_id carry-through is PLANNED; current implementation uses stub

---

## SECTION 2 — EVIDENCE TABLE

| Step ID | Step Name | Confirmed Owner | entrypoint_files (confirmed) | Status | Identifiers Generated | Identifiers Consumed | Confirmed Stores | Evidence Note |
|---|---|---|---|---|---|---|---|---|
| S1 | Resolve config snapshot | UNMAPPED — configuration_service.py not found | UNMAPPED | planned | ResolvedConfig snapshot | ConfigSource | UNKNOWN | No source confirmed |
| S2 | Emit schedule tick | calendar-ingestor | `services/calendar-ingestor/src/2099900093260118_main.py` | partial | ScheduleTick | ResolvedConfig | UNKNOWN | File confirmed; internal scheduler class unknown |
| S3 | Poll calendar source | calendar-ingestor | `services/calendar-ingestor/src/2099900093260118_main.py` | partial | CalendarRaw | CalendarSourceConfig + ScheduleTick | UNKNOWN | ff_auto_downloader.py confirmed |
| S4 | Normalize calendar entries | calendar-ingestor | `services/calendar-ingestor/src/2099900093260118_main.py` | partial | CalendarEvent (calendar_id) | CalendarRaw | Redis: eafix.calendar.events | Event schema CalendarEvent@1.0 confirmed |
| S5 | Persist calendar events | calendar-ingestor | `services/calendar-ingestor/src/2099900093260118_main.py` | partial | EventStream | CalendarEvent | Redis pub/sub; CSV ./data/calendar-ingestor/ | Redis schema confirmed; CSV atomic write policy confirmed |
| S6 | Build anticipation triggers | calendar-ingestor | `services/calendar-ingestor/src/2099900093260118_main.py` | partial | CalendarTrigger, ActiveCalendarSignal | CalendarEvent + ScheduleTick | Redis: eafix.calendar.signals; CSV | ActiveCalendarSignal schema confirmed |
| S7 | Ingest market ticks | UNMAPPED — data-ingestor has no confirmed main | UNMAPPED | planned | MarketTick | RawTick | UNKNOWN | data-ingestor: no confirmed source |
| S8 | Aggregate ticks into bars | UNMAPPED — no bar_builder.py found | UNMAPPED | planned | Bar | MarketTick | UNKNOWN | No source confirmed |
| S9 | Compute indicators | UNMAPPED — indicator-engine src unknown | UNMAPPED | planned | IndicatorSnapshot | Bar | UNKNOWN | desktop-ui expiry_indicator_service.py referenced in YAML — likely wrong |
| S10 | Assemble feature frame | UNMAPPED — no feature_packager.py found | UNMAPPED | planned | FeatureFrame | IndicatorSnapshot + CalendarTrigger | UNKNOWN | No source confirmed |
| S11 | Generate signal | UNMAPPED — signal-generator src has only __pycache__ | UNMAPPED — compliance path in YAML is wrong | planned | Signal / SignalSuppressed | FeatureFrame + PositionSummary | Redis: eafix.signals.generated | Signal@1.0 schema confirmed; service not implemented |
| S12 | Convert signal to trade intent | UNMAPPED — no intent_builder.py found | UNMAPPED | planned | TradeIntent | Signal | UNKNOWN | No source confirmed |
| S13 | Evaluate risk and size | risk-manager (plugin only) | UNMAPPED — risk-manager has plugin only, no main | planned | RiskDecision | TradeIntent + PortfolioState | Redis: eafix.orders.validated | OrderIntent@1.2 schema confirmed; processor not confirmed |
| S14 | Compile order intent | UNMAPPED — no order_intent_compiler.py found | `services/transport-router/src/2099900199260118_main.py` (wrong — transport-router is not order compiler) | planned | OrderIntent (client_order_id, idempotency_key) | RiskDecision | UNKNOWN | entrypoint_files wrong in YAML |
| S15 | Route order to broker | UNMAPPED — no order_router.py found | `services/transport-router/src/2099900199260118_main.py` (partially correct — transport-router does routing) | partial | RoutedOrderIntent | OrderIntent | UNKNOWN | transport-router confirmed as CSV router; broker routing logic UNMAPPED |
| S16 | Serialize and send to MT4 | transport-router | `services/transport-router/src/2099900199260118_main.py` | partial | BrokerOrderEnvelope; file_seq; checksum_sha256 | RoutedOrderIntent | CSV: ./data/[service]/; atomic write | CSV atomic write confirmed; DLL socket bridge described but not in repo |
| S16a | Decision Serialization | transport-router | `services/transport-router/src/2099900199260118_main.py` | partial | serialized payload | RoutedOrderIntent | none | Pydantic model serialization confirmed |
| S16b | Transport Selection | transport-router | `services/transport-router/src/2099900199260118_main.py` | partial | transport mode selection | BrokerPolicy | none | CSV primary; socket/DLL secondary per tactical spec |
| S16c | CSV Atomic Write | transport-router | `services/transport-router/src/2099900202260118_router.py` (inferred) | partial | BrokerOrderEnvelope CSV row; file_seq; checksum_sha256; hybrid_id (if present); timestamp | RoutedOrderIntent | CSV .tmp → rename | Atomic write pattern confirmed in processor.py |
| S16d | Adapter Ack Validation | transport-router | `services/transport-router/src/2099900203260118_validator.py` | partial | AdapterAck | CSV file | none | IntegrityValidator confirmed; SHA-256 checksum; sequence validation |
| S17 | EA executes broker order | EAFIX.mq4 (not in repo) | UNMAPPED — EAFIX.mq4 not in repo; placeholder SMA EA present | conceptual | BrokerExecEvent; EAHealth | BrokerOrderEnvelope CSV | MQL4 internal state | Real EA absent; placeholder EA present |
| S17a | Trade result ingestion | UNMAPPED | UNMAPPED | conceptual | BrokerExecEvent CSV / socket response | EA output | CSV: ./data/execution-engine/ | execution-engine has plugin only |
| S17b | Payload validation + hybrid_id match | transport-router IntegrityValidator | `services/transport-router/src/2099900203260118_validator.py` | partial | validated payload | BrokerExecEvent; hybrid_id; file_seq | none | Checksum + sequence validation confirmed |
| S18 | Normalize broker events | event-gateway | `services/event-gateway/src/2099900141260118_main.py` | partial | ExecutionReport; PositionSnapshot | BrokerExecEvent | Redis: eafix.execution.completed | ExecutionReport@1.0 schema confirmed |
| S19 | Apply reports to OMS | UNMAPPED — no oms.py found | UNMAPPED | planned | OrderStateChanged; PositionStateChanged; TradeClosedRaw | RoutedOrderIntent + ExecutionReport | UNKNOWN | No source confirmed |
| S20 | Classify trade close + PnL | UNMAPPED — no trade_close_classifier.py | UNMAPPED | planned | TradeClosed | TradeClosedRaw | UNKNOWN | No source confirmed |
| S21 | Bucketize outcome | UNMAPPED — no outcome_bucketizer.py | UNMAPPED | planned | OutcomeBucket (WIN/LOSS/BREAKEVEN → W1/W2/L1/L2/BE) | TradeClosed | CSV: ./data/execution-engine/ (inferred) | Outcome classification confirmed in reentry-engine processor (lines 240–249) but as part of reentry, not dedicated service |
| S22 | Compute event proximity | STUB in reentry-engine | `services/reentry-engine/src/2099900169260118_processor.py` lines 278–291 | partial — stub | EventProximity (PRE_1H / AT_EVENT / POST_30M) | CalendarEvent (not actually used); ClockTick (time-of-day heuristic) | none | CONFLICT-06: uses hour-of-day heuristic, not real calendar |
| S23 | Lookup matrix decision | reentry-matrix-svc | `services/reentry-matrix-svc/src/2099900174260118_main.py` | implemented | MatrixDecision; parameter_set_id; resolved_tier | OutcomeBucket + EventProximity + calendar_id + generation | CSV: ./data/reentry-matrix/ | Tiered parameter resolver confirmed |
| S24 | Build reentry trade intent | reentry-engine | `services/reentry-engine/src/2099900166260118_main.py` | implemented | hybrid_id; ReentryDecision CSV; chain_position | MatrixDecision + ReentryChainState | CSV: ./data/reentry-engine/ | hybrid_id.py compose() confirmed; atomic write confirmed |
| S25 | Loop: reentry intent → risk chain | UNMAPPED — flow-orchestrator not implemented | UNMAPPED | planned | new TradeIntent | TradeIntent from S24 | UNKNOWN | flow-orchestrator src empty |
| S26 | Health aggregation + SLO | UNMAPPED — no health_service.py | `services/telemetry-daemon/src/2099900192260118_main.py` (listed in YAML; not read) | planned | HealthReport | AdapterHealth + ModuleHealth | UNKNOWN | telemetry-daemon not confirmed read |

---

## SECTION 3 — REVISED PROCESS DOCUMENT

### META

```
process_id: HUEY_P_EAFIX_END_TO_END
process_version: 3.0.0-source-grounded
derived_from: process_version 2.0.0
evidence_date: 2026-03-09
canonical_chain: >
  FeatureFrame -> Signal -> TradeIntent -> RiskDecision -> OrderIntent
  -> RoutedOrderIntent -> Transport -> EA -> BrokerExecEvent
  -> (ExecutionReport, PositionSnapshot) -> OMS -> TradeClosedRaw
  -> TradeClosed -> OutcomeBucket -> (EventProximity + MatrixDecision)
  -> Reentry TradeIntent
module_registry: MODULE_REGISTRY_version_1.0.0.txt
```

---

### FLOW-ORCHESTRATOR CONTROL PLANE (PLANNED)

**Status**: PLANNED — `services/flow-orchestrator/src/` contains only `__pycache__`; no source implementation confirmed.

The following block describes the intended ownership of the orchestration layer per architecture docs. It is NOT currently implemented as a running service.

```
flow-orchestrator (PLANNED, port 8093) owns, in order:
  1. Signal receipt (from eafix.signals.generated Redis topic)
  2. Calendar gate check (query calendar-ingestor or local CalendarEvent cache)
  3. Reentry state check (query reentry-engine chain state)
  4. Risk validation handoff (forward TradeIntent to risk-manager)
  5. Execution handoff (forward approved OrderIntent to transport-router)

Publishes: eafix.orchestrator.flows (FlowEvent@1.0)
Subscribes: eafix.orchestrator.status (OrchestratorStatus@1.0)
```

CURRENT REALITY: Steps 13–16 (risk → order → route → transport) are handled by transport-router and risk-manager plugin without a confirmed orchestrator coordinating them.

---

### PHASE A — CONFIGURATION & SCHEDULING

---

#### Step S1 — Resolve Configuration Snapshot

```
step_id: S1
name: Resolve configuration snapshot
module_id: F1_CONFIG_PREFERENCES
purpose: Load all config sources, apply override hierarchy, produce immutable snapshot
  for all downstream steps
owner: configuration_service.py
status: planned
entrypoint_files:
  - UNMAPPED — configuration_service.py not confirmed in repo

inputs:
  - ConfigSource (defaults + overrides)

outputs:
  - ResolvedConfig (immutable snapshot, hash-stable)

identifiers_generated:
  - config_snapshot_hash: UNMAPPED — generation mechanism not confirmed

identifiers_consumed: none

validations:
  - Schema validate all fields
  - Stable ordering of config keys
  - Hash snapshot matches declared schema version

persistence:
  - UNKNOWN — data store not confirmed

failure_branch:
  - detection: Schema validation failure on startup
  - handling: Reject invalid config; continue using last known good snapshot
  - halt_retry: UNDEFINED — not specified in source

notes:
  - "configuration_service.py" named in process YAML but not found in repo
  - config/1199900002260118_parameter_sets.json confirmed as parameter-set config
  - config/1299900021260118_plugins.yaml confirmed as plugin config
  - Relationship between ResolvedConfig and parameter_sets.json is UNDEFINED in source
```

---

#### Step S2 — Emit Schedule Tick

```
step_id: S2
name: Emit schedule tick (calendar polling cadence)
module_id: F3_CLOCK_SCHEDULER
purpose: Drive periodic polling of calendar sources at configured cadence
owner: calendar-ingestor (scheduler within)
status: partial
entrypoint_files:
  - services/calendar-ingestor/src/2099900093260118_main.py

inputs:
  - ResolvedConfig

outputs:
  - ScheduleTick

identifiers_generated:
  - tick_timestamp: UNMAPPED — exact field name not confirmed

identifiers_consumed:
  - config_snapshot_hash (from S1): consumed as cadence configuration

validations:
  - Frozen-time mode supported for tests

persistence:
  - UNKNOWN — tick is ephemeral event, not persisted

failure_branch:
  - detection: Scheduler stall
  - handling: Emit HealthReport alert; pause polling
  - halt_retry: UNDEFINED — not specified in source
```

---

### PHASE B — ECONOMIC CALENDAR INTAKE → TRIGGERS

---

#### Step S3 — Poll Calendar Source(s)

```
step_id: S3
name: Poll calendar source(s)
module_id: D2_CALENDAR_SOURCE_ADAPTER
purpose: Fetch raw calendar data from ForexFactory or other configured sources
owner: calendar-ingestor (ff_auto_downloader.py)
status: partial
entrypoint_files:
  - services/calendar-ingestor/src/2099900090260118_ff_auto_downloader.py
  - services/calendar-ingestor/src/2099900092260118_ingestor.py
  - services/calendar-ingestor/src/2099900093260118_main.py

inputs:
  - CalendarSourceConfig + ScheduleTick

outputs:
  - CalendarRaw

identifiers_generated:
  - source_event_id: UNMAPPED — exact generation point not confirmed in source

identifiers_consumed:
  - ScheduleTick (from S2)

validations:
  - HTTP 200 required
  - Payload parsable
  - source_event_id present

persistence:
  - UNKNOWN — raw fetch not confirmed persisted before normalization

failure_branch:
  - detection: HTTP error or unparsable payload
  - handling: Retry with deterministic backoff
  - halt_retry: On persistent failure, emit IngestError and skip cycle
    UNDEFINED — retry count and backoff parameters not confirmed in source
```

---

#### Step S4 — Normalize Raw Calendar Entries

```
step_id: S4
name: Normalize raw calendar entries
module_id: D3_CALENDAR_NORMALIZER
purpose: Convert raw calendar rows to CalendarEvent with UTC timestamps, standardized
  impact levels, and deduplication keys
owner: calendar-ingestor (calendar_service.py::normalize_events)
status: partial
entrypoint_files:
  - services/calendar-ingestor/src/2099900092260118_ingestor.py
  - services/calendar-ingestor/src/2099900093260118_main.py

inputs:
  - CalendarRaw + ResolvedConfig

outputs:
  - CalendarEvent (UTC timestamps; impact in enum: CAL8_* or CAL5_* or NONE; dedup keys)

identifiers_generated:
  - calendar_id: Format CAL8_* (high impact) or CAL5_* (medium impact) per
      contracts/identifiers/0199900024260118_cal8.md,
      contracts/identifiers/0199900023260118_cal5_legacy.md
  - message_id: for idempotency; UNMAPPED — exact generation not confirmed

identifiers_consumed:
  - source_event_id (from S3): consumed for dedup

validations:
  - UTC conversion success
  - impact in enum (CAL8 or CAL5)
  - dedup policy applied

persistence:
  - Redis topic: eafix.calendar.events (CalendarEvent@1.0)
    schema confirmed: contracts/events/1199900003260118_CalendarEvent@1.0.json

failure_branch:
  - detection: Malformed row; UTC conversion failure; impact not in enum
  - handling: Emit NormalizationError; continue with valid CalendarEvents
  - halt_retry: UNDEFINED — NormalizationError destination not confirmed
```

---

#### Step S5 — Persist Calendar Events

```
step_id: S5
name: Persist calendar events (append-only)
module_id: F2_EVENT_LOG
purpose: Durably publish CalendarEvents to event stream for downstream consumers
owner: calendar-ingestor (event_log.py)
status: partial
entrypoint_files:
  - services/calendar-ingestor/src/2099900093260118_main.py

inputs:
  - CalendarEvent (from S4)

outputs:
  - EventStream (eafix.calendar.events)

identifiers_generated:
  - message_id: for idempotency; UNMAPPED — exact field not confirmed

identifiers_consumed:
  - calendar_id (from S4): forwarded
  - message_id (from S4): validated for idempotency

validations:
  - Idempotent by message_id
  - Ordered by created_utc + tie-breaker

persistence:
  - Redis pub/sub topic: eafix.calendar.events
  - CSV: ./data/calendar-ingestor/ActiveCalendarSignal records
    schema confirmed: contracts/schemas/csv/0199900027260118_active_calendar_signals.csv.md

failure_branch:
  - detection: Redis publish failure
  - handling: Rollback and retry once
  - halt_retry: On persistent failure, halt calendar pipeline
    UNDEFINED — halt scope not specified
```

---

#### Step S6 — Build Anticipation Triggers

```
step_id: S6
name: Build anticipation triggers from calendar
module_id: D4_CALENDAR_TRIGGER_BUILDER
purpose: Generate time-windowed CalendarTriggers and ActiveCalendarSignals for
  signal engine consumption
owner: calendar-ingestor (calendar_anticipator.py)
status: partial
entrypoint_files:
  - services/calendar-ingestor/src/2099900093260118_main.py

inputs:
  - CalendarEvent + ScheduleTick + ResolvedConfig

outputs:
  - CalendarTrigger (symbol set + window + suppression metadata)
  - ActiveCalendarSignal (calendar_id, symbol, impact_level, proximity_state,
      confidence_score)

identifiers_generated:
  - calendar_id: forwarded from S4
  - proximity_state: PRE_1H | AT_EVENT | POST_30M (generated here per event timing)

identifiers_consumed:
  - calendar_id (from S4)
  - ScheduleTick (from S2)

validations:
  - No duplicate trigger for event+offset
  - TTL rules applied
  - proximity_state in allowed enum

persistence:
  - Redis topic: eafix.calendar.signals (ActiveCalendarSignal@1.0)
  - CSV: ./data/calendar-ingestor/ (atomic write)

failure_branch:
  - detection: Duplicate trigger detected; TTL expired
  - handling: Default to conservative suppression metadata; emit error event
  - halt_retry: UNDEFINED — error event destination not confirmed
```

---

### PHASE C — MARKET DATA → FEATURES

**PHASE STATUS: PLANNED** — Steps S7–S10 have no confirmed source implementations.

---

#### Step S7 — Ingest Market Ticks

```
step_id: S7
name: Ingest market ticks
module_id: D1_MARKET_FEED_ADAPTER
purpose: Receive raw price ticks from broker feed and emit as normalized MarketTick
owner: UNMAPPED — data-ingestor has no confirmed main source
status: planned
entrypoint_files:
  - UNMAPPED — services/data-ingestor/src/2099900112260118_main.py referenced in YAML
      but not confirmed read

inputs:
  - RawTick + ResolvedConfig

outputs:
  - MarketTick

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - UNKNOWN

validations:
  - Timestamp freshness
  - Symbol normalization
  - Reject malformed ticks

persistence:
  - UNKNOWN — data store not confirmed

failure_branch:
  - detection: Malformed tick
  - handling: Emit IngestError; skip malformed tick
  - halt_retry: UNDEFINED
```

---

#### Step S8 — Aggregate Ticks Into Bars

```
step_id: S8
name: Aggregate ticks into bars
module_id: C1_BAR_BUILDER
purpose: Combine ticks into OHLCV bars at configured timeframes
owner: UNMAPPED — bar_builder.py not confirmed in repo
status: planned
entrypoint_files:
  - UNMAPPED — source not confirmed

inputs:
  - MarketTick + ResolvedConfig

outputs:
  - Bar (OHLCV + timeframe + symbol)

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - MarketTick timestamp (for bar boundary)

validations:
  - Deterministic bar boundaries
  - Tie-breaker rules for simultaneous ticks

persistence:
  - UNKNOWN

failure_branch:
  - detection: Out-of-order tick
  - handling: Drop per policy
  - halt_retry: UNDEFINED
```

---

#### Step S9 — Compute Indicators

```
step_id: S9
name: Compute indicators
module_id: C2_INDICATOR_ENGINE
purpose: Calculate technical indicator values from Bar series
owner: UNMAPPED — indicator-engine src not confirmed; YAML incorrectly points to
  desktop-ui expiry_indicator_service.py
status: planned
entrypoint_files:
  - UNMAPPED — source not confirmed
  - NOTE: YAML entrypoint services/desktop-ui/2099900128260118_expiry_indicator_service.py
      is likely wrong (UI service ≠ indicator computation engine)

inputs:
  - Bar + ResolvedConfig

outputs:
  - IndicatorSnapshot

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - UNKNOWN

validations:
  - Deterministic rounding
  - Indicator params pinned by config snapshot

persistence:
  - UNKNOWN
  - Redis: eafix.indicators.computed (IndicatorVector@1.1) — schema confirmed;
      producer not confirmed

failure_branch:
  - detection: Computation error; partial snapshot
  - handling: Emit indicator error; do not emit partial snapshot unless flagged
  - halt_retry: UNDEFINED
```

---

#### Step S10 — Assemble Strategy Feature Frame

```
step_id: S10
name: Assemble strategy feature frame
module_id: C3_FEATURE_PACKAGER
purpose: Combine IndicatorSnapshot + CalendarTrigger into a complete FeatureFrame
  for signal evaluation
owner: UNMAPPED — feature_packager.py not confirmed in repo
status: planned
entrypoint_files:
  - UNMAPPED — source not confirmed

inputs:
  - IndicatorSnapshot + CalendarTrigger + ResolvedConfig

outputs:
  - FeatureFrame

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - calendar_id (from S6, via CalendarTrigger)
  - proximity_state (from S6, via CalendarTrigger)

validations:
  - Exact declared feature set present
  - Stable ordering

persistence:
  - UNKNOWN

failure_branch:
  - detection: Missing required features in FeatureFrame
  - handling: Emit packaging error; do not emit FeatureFrame
  - halt_retry: UNDEFINED
```

---

### PHASE D — SIGNAL → INTENT → RISK → ORDER

**PHASE STATUS: PLANNED** — Steps S11–S15 have no confirmed full implementations; risk-manager and signal-generator have plugin stubs only.

---

#### Step S11 — Generate Signal (or Suppression)

```
step_id: S11
name: Generate signal (or suppression)
module_id: S1_SIGNAL_ENGINE
purpose: Evaluate FeatureFrame against strategy rules; emit Signal or SignalSuppressed
owner: signal-generator (PLANNED — src directory has __pycache__ only)
status: planned
entrypoint_files:
  - UNMAPPED — signal-generator/src contains only __pycache__
  - NOTE: YAML entrypoint compliance/auto-remediation/2099900012260118_remediation-engine.py
      is WRONG — that is a compliance service

inputs:
  - FeatureFrame + PositionSummary + ResolvedConfig

outputs:
  - Signal (OR SignalSuppressed)

identifiers_generated:
  - correlation_id: per Signal; UNMAPPED — generation point not confirmed in source

identifiers_consumed:
  - calendar_id (from S6, via FeatureFrame)
  - proximity_state (from S6, via FeatureFrame)

validations:
  - Suppression reasons enumerated
  - Signal contains no sizing or broker specifics

persistence:
  - Redis: eafix.signals.generated (Signal@1.0)
    schema confirmed: contracts/events/1199900009260118_Signal@1.0.json

failure_branch:
  - detection: Internal signal engine error
  - handling: Emit SignalSuppressed with deterministic reason code
  - halt_retry: UNDEFINED
```

---

#### Step S12 — Convert Signal to Trade Intent

```
step_id: S12
name: Convert signal to trade intent
module_id: S2_INTENT_BUILDER
purpose: Translate Signal into actionable TradeIntent with constraints and rationale
owner: UNMAPPED — intent_builder.py not confirmed in repo
status: planned
entrypoint_files:
  - UNMAPPED — source not confirmed

inputs:
  - Signal + ResolvedConfig

outputs:
  - TradeIntent

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - correlation_id (from S11, via Signal): forwarded
  - calendar_id (from S11, via Signal): forwarded

validations:
  - Stable correlation_id from Signal
  - Constraints + rationale attached

persistence:
  - UNKNOWN

failure_branch:
  - detection: Signal cannot be converted to valid intent
  - handling: Reject intent; emit error event
  - halt_retry: UNDEFINED
```

---

#### Step S13 — Evaluate Risk and Size

```
step_id: S13
name: Evaluate risk and size
module_id: R1_RISK_EVALUATOR
purpose: Apply risk policy to TradeIntent; compute position size; emit RiskDecision
owner: risk-manager (plugin only — no main confirmed)
status: planned
entrypoint_files:
  - UNMAPPED — services/risk-manager/src/2099900183260118_plugin.py exists but
      is plugin interface only; no main/processor confirmed

inputs:
  - TradeIntent + PortfolioState + RiskPolicy + ResolvedConfig

outputs:
  - RiskDecision (APPROVE/REJECT + reason codes + sized params)

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - correlation_id (from S12, via TradeIntent): forwarded
  - calendar_id (from S12, via TradeIntent): forwarded

validations:
  - Idempotent for same inputs
  - Deterministic sizing + rounding
  - Max risk: 2% per trade per tactical spec (0199900015260118_SS_HUEY_P)
  - Max reentry risk cap: 3.50% per tactical spec (FR-P2)
  - Daily drawdown limit: 5% per tactical spec

persistence:
  - Redis: eafix.orders.validated (OrderIntent@1.2) on APPROVE
    schema confirmed: contracts/events/1199900006260118_OrderIntent@1.2.json

failure_branch:
  - detection: Rule engine failure
  - handling: Default to REJECT with SAFETY_FAIL reason
  - halt_retry: UNDEFINED
```

---

#### Step S14 — Compile Order Intent

```
step_id: S14
name: Compile order intent
module_id: R2_ORDER_INTENT_COMPILER
purpose: Translate approved RiskDecision into OrderIntent with idempotency key
owner: UNMAPPED — order_intent_compiler.py not confirmed in repo
status: planned
entrypoint_files:
  - UNMAPPED — transport-router listed in YAML entrypoint_files but order compilation
      is a different concern from transport routing

inputs:
  - RiskDecision + ResolvedConfig

outputs:
  - OrderIntent (client_order_id + idempotency_key)

identifiers_generated:
  - client_order_id: UNMAPPED — generation point not confirmed
  - idempotency_key: UNMAPPED — generation point not confirmed

identifiers_consumed:
  - correlation_id (from S13, via RiskDecision): forwarded

validations:
  - client_order_id assigned per policy
  - idempotency_key assigned per policy

persistence:
  - UNKNOWN

failure_branch:
  - detection: Compilation failure
  - handling: Emit error; do not proceed to routing
  - halt_retry: UNDEFINED
```

---

#### Step S15 — Route Order to Broker

```
step_id: S15
name: Route order to broker
module_id: O1_ORDER_ROUTER
purpose: Select broker route for OrderIntent; preserve OrderIntent hash
owner: transport-router (routing component)
status: partial
entrypoint_files:
  - services/transport-router/src/2099900202260118_router.py (CSVRouter confirmed)
  - services/transport-router/src/2099900199260118_main.py

inputs:
  - OrderIntent + BrokerPolicy + ResolvedConfig

outputs:
  - RoutedOrderIntent

identifiers_generated:
  - UNKNOWN — RoutedOrderIntent additions not confirmed

identifiers_consumed:
  - client_order_id (from S14): forwarded
  - idempotency_key (from S14): forwarded

validations:
  - Routing deterministic
  - Preserves OrderIntent hash

persistence:
  - UNKNOWN

failure_branch:
  - detection: No valid route available
  - handling: Emit error and reject
  - halt_retry: UNDEFINED
```

---

### PHASE E — TRANSPORT → EA → NORMALIZE

---

#### Step S16 — Serialize and Send to MT4 Adapter

**This step is decomposed into four discrete substeps (S16a–S16d).**

```
step_id: S16
name: Serialize and send to MT4 adapter (PARENT)
module_id: B1_MT4_ADAPTER_TRANSPORT
purpose: Transport RoutedOrderIntent to MT4 EA via CSV or socket bridge
owner: transport-router
status: partial
entrypoint_files:
  - services/transport-router/src/2099900199260118_main.py
```

---

##### Step S16a — Decision Serialization

```
step_id: S16a
name: Decision Serialization
purpose: Serialize RoutedOrderIntent to wire format for transport
owner: transport-router
status: partial
entrypoint_files:
  - services/transport-router/src/2099900199260118_main.py

inputs:
  - RoutedOrderIntent

outputs:
  - serialized_payload (JSON or CSV row encoding of BrokerOrderEnvelope)

identifiers_generated:
  - file_seq: integer ≥1, monotonically increasing per transport-router instance
      (confirmed: self.csv_sequence in processor.py)
  - checksum_sha256: SHA-256 of sorted pipe-delimited field values excluding
      checksum field (confirmed: compute_checksum() in csv_models.py)
  - timestamp: UTC ISO format

identifiers_consumed:
  - client_order_id (from S14)
  - idempotency_key (from S14)
  - hybrid_id (from S24, if reentry loop): forwarded into payload
  - correlation_id: forwarded

validations:
  - All required fields present before serialization
  - Pydantic model validation (confirmed: csv_models.py)

persistence:
  - none (intermediate state)

failure_branch:
  - detection: Pydantic validation failure; missing required field
  - handling: Reject and emit error; do not write to transport
  - halt_retry: UNDEFINED
```

---

##### Step S16b — Transport Selection

```
step_id: S16b
name: Transport Selection
purpose: Select transport mechanism (CSV file or DLL socket) based on broker policy
  and connection health
owner: transport-router
status: partial
entrypoint_files:
  - services/transport-router/src/2099900199260118_main.py

inputs:
  - BrokerPolicy + connection health state

outputs:
  - selected_transport: CSV | SOCKET

identifiers_generated: none

identifiers_consumed:
  - idempotency_key (from S14): used for dedup on retry

validations:
  - Transport tier selection (per tactical spec: DLL socket primary, CSV fallback)

persistence:
  - UNKNOWN — health state store not confirmed

failure_branch:
  - detection: Primary transport unavailable
  - handling: Demote to next tier (socket → CSV); UNDEFINED — demotion logic
      not confirmed in transport-router source (tactical spec describes 3-tier
      fallback but transport-router CSV router is the only confirmed implementation)
  - halt_retry: UNDEFINED

notes:
  - Tactical spec (Layer C) describes 3-tier: Socket/FastAPI → Enhanced CSV
      → Static CSV profile
  - Transport-router (Layer B) confirms only CSV watching and HTTP routing;
      DLL socket bridge not confirmed in Layer B source
  - CONFLICTING SOURCE EVIDENCE on transport tier mapping between layers
```

---

##### Step S16c — CSV Atomic Write (if CSV transport selected)

```
step_id: S16c
name: CSV Atomic Write
purpose: Write BrokerOrderEnvelope to CSV using atomic tmp→rename protocol
owner: transport-router (router.py)
status: partial
entrypoint_files:
  - services/transport-router/src/2099900202260118_router.py (CSVRouter, inferred)
  - services/reentry-engine/src/2099900169260118_processor.py (atomic write
      pattern confirmed here; same pattern applies to transport)

inputs:
  - serialized_payload (from S16a)
  - selected_transport = CSV (from S16b)

outputs:
  - CSV file in ./data/[service]/ directory
  - AdapterAck (file existence = implicit ack)

required_csv_fields:
  - file_seq: integer ≥1 (confirmed)
  - checksum_sha256: 64-char hex SHA-256 (confirmed)
  - hybrid_id: if reentry trade (confirmed carried in ReentryDecision CSV)
  - timestamp: UTC ISO (confirmed)
  - trade_id / client_order_id: UNMAPPED — exact field name in BrokerOrderEnvelope
      not confirmed in transport-router source

atomic_write_protocol:
  1. Write to .tmp file (tempfile.NamedTemporaryFile, suffix='.tmp', delete=False)
  2. flush() + fsync() to ensure durability
  3. os.rename() / Path.rename() atomic rename to target path
  (confirmed: processor.py lines 280–343)

identifiers_generated:
  - file_seq: generated here (confirmed)
  - checksum_sha256: generated here (confirmed)

identifiers_consumed:
  - hybrid_id (if reentry): forwarded from S24 chain
  - client_order_id: forwarded
  - idempotency_key: forwarded

validations:
  - checksum_sha256 must verify before write (compute then verify — confirmed)
  - file_seq must be monotonically increasing

persistence:
  - CSV: ./data/[service]/  (atomic .tmp → rename)

failure_branch:
  - detection: fsync failure; checksum verification failure; disk full
  - handling: UNDEFINED — not specified in transport-router source
    (reentry-engine logs error and raises; no retry confirmed)
  - halt_retry: UNDEFINED

for_socket_transport:
  - S16c is bypassed; socket send is used instead
  - Socket protocol: TCP JSON per tactical spec (port 5555/9999)
  - Heartbeat: SocketSendHeartbeat() per DLL API
  - Ack semantics: UNDEFINED — not confirmed in Python-side source
  - Retry/fail: UNDEFINED — not confirmed in Python-side source
```

---

##### Step S16d — Adapter Ack Validation

```
step_id: S16d
name: Adapter Ack Validation
purpose: Validate that transport was received and file integrity is intact
owner: transport-router (IntegrityValidator)
status: partial
entrypoint_files:
  - services/transport-router/src/2099900203260118_validator.py (IntegrityValidator
      confirmed)

inputs:
  - CSV file from S16c (or socket ack from socket path)

outputs:
  - AdapterAck (valid | invalid)

validations:
  - checksum_sha256: recomputed and compared (confirmed)
  - file_seq: checked for monotonic continuity (confirmed)
  - Schema validation against Pydantic model (confirmed)
  - Caching: TTL 5 minutes for repeated validation (confirmed)

identifiers_generated: none
identifiers_consumed:
  - file_seq (from S16c): validated
  - checksum_sha256 (from S16c): recomputed and validated

persistence:
  - UNKNOWN — validation result not confirmed persisted

failure_branch:
  - Sequence gap detected:
      detection: file_seq discontinuity
      handling: UNDEFINED — not specified in source
      halt_retry: UNDEFINED
  - Checksum mismatch:
      detection: computed sha256 ≠ stored sha256
      handling: UNDEFINED — not specified in source
      halt_retry: UNDEFINED

notes:
  - IntegrityValidator confirmed with checksum, sequence, schema validation
  - Retry count: 3 per CSVRouter (confirmed); backoff: exponential (confirmed)
```

---

#### Step S17 — EA Executes Broker Order

```
step_id: S17
name: EA executes broker order
module_id: B2_MT4_EA_EXECUTOR
purpose: MQL4 Expert Advisor reads BrokerOrderEnvelope, places broker order,
  emits BrokerExecEvent
owner: EAFIX.mq4 (NOT in repo)
status: conceptual
entrypoint_files:
  - UNMAPPED — EAFIX.mq4 not present in repo
  - NOTE: HUEY_P_EA_ExecutionEngine_8.mql4 present in repo is a 164-line SMA
      crossover placeholder; internal comment confirms it is "a functional
      replacement" because "the original file was not available"
  - NOTE: YAML entrypoint services/transport-router/src/2099900199260118_main.py
      is WRONG for this step

inputs:
  - BrokerOrderEnvelope (CSV file or DLL socket message)

outputs:
  - BrokerExecEvent (accept / fill / reject / close)
  - EAHealth (heartbeat / status)

identifiers_generated:
  - trade_id / ticket_number: assigned by broker / MT4 on fill (confirmed concept
      in tactical spec)

identifiers_consumed:
  - hybrid_id: read from BrokerOrderEnvelope; embedded in MT4 trade comment
      using MQL4 ComposeReentryKey() or decompose_for_comment() (confirmed in
      ReentryHelpers.mq4 and hybrid_id.py)
  - file_seq: UNMAPPED — whether EA validates file_seq not confirmed
  - client_order_id: UNMAPPED — field name in BrokerOrderEnvelope not confirmed

validations:
  - EA contains no strategy or risk logic per process contract (Layer A)
  - CONFLICTING SOURCE EVIDENCE: tactical spec (Layer C) describes EA with embedded
      ATR-based sizing, dynamic SL/TP, and StateManager — i.e., non-trivial
      strategy logic within the EA itself

persistence:
  - UNKNOWN — EA-side persistence not confirmed in Python-readable source
    (tactical spec mentions SQLite on Python side; EA state in MQL4 globals)

failure_branch:
  - Broker rejection:
      detection: OrderSend() error code from broker
      handling: UNDEFINED — error handling in EAFIX.mq4 not confirmed (original EA absent)
      halt_retry: UNDEFINED
  - EA not running / offline:
      detection: UNDEFINED
      handling: UNDEFINED
      halt_retry: UNDEFINED

notes:
  - CONFLICT-01 applies: real EA is absent from repo
  - DLL socket bridge (MQL4_DLL_SocketBridge.dll) described in tactical spec
      but not present in repo
  - MT4 terminal ID: F2262CFAFF47C27887389DAB2852351A (Forex.com Live Account)
      per tactical spec
```

---

### POST-EA INGESTION BLOCK (Steps S17a–S17b)

---

#### Step S17a — Trade Result Ingestion from MT4

```
step_id: S17a
name: Trade result ingestion from MT4
purpose: Receive trade execution result from MT4 EA via CSV or socket;
  route into Python-side processing
owner: execution-engine (PLANNED — has plugin only)
status: planned
entrypoint_files:
  - UNMAPPED — services/execution-engine/src/2099900144260118_plugin.py exists
      but is plugin interface only

inputs:
  - BrokerExecEvent via CSV in ./data/execution-engine/ (inferred from transport-router
      routing config: "TradeResult" → ["reentry-engine", "reporter"])
  - OR socket message from MQL4 (per tactical spec)

outputs:
  - TradeResult record (CSV, confirmed schema:
      contracts/schemas/csv/0199900030260118_trade_results.csv.md)

required_payload_fields:
  - trade_id
  - symbol
  - direction
  - lot_size
  - open_price
  - close_price
  - profit_loss_pips
  - open_time
  - close_time
  - comment (contains hybrid_id abbreviation)
  - file_seq
  - checksum_sha256
  - timestamp

identifiers_generated:
  - file_seq: for TradeResult CSV row
  - checksum_sha256: for TradeResult CSV row

identifiers_consumed:
  - trade_id (assigned by broker at S17): received
  - hybrid_id (from S17, in MT4 comment): extracted by reentry-engine
      _extract_hybrid_id_from_comment() (confirmed in processor.py lines 264–276)

validations:
  - Pydantic TradeResult model validation (confirmed in csv_models.py)
  - checksum_sha256 recomputed and verified

persistence:
  - CSV: ./data/execution-engine/ (inferred)
  - Redis: eafix.execution.completed (ExecutionReport@1.0)
    schema confirmed: contracts/events/1199900004260118_ExecutionReport@1.0.json

timeout_path:
  - UNDEFINED — timeout or no-result handling not confirmed in source
    (reentry-engine proceeds only on explicit TradeResult; no timeout path found)

failure_branch:
  - detection: No result received; timeout
  - handling: UNDEFINED — not specified in source
  - halt_retry: UNDEFINED
```

---

#### Step S17b — Payload Validation + hybrid_id Match

```
step_id: S17b
name: Payload validation + hybrid_id match
purpose: Validate ingested trade result; verify hybrid_id continuity with originating
  signal chain
owner: transport-router (IntegrityValidator) + reentry-engine (processor)
status: partial
entrypoint_files:
  - services/transport-router/src/2099900203260118_validator.py
  - services/reentry-engine/src/2099900169260118_processor.py (hybrid_id extraction
      confirmed)

inputs:
  - TradeResult CSV record

outputs:
  - validated TradeResult object
  - extracted hybrid_id (if present in comment)
  - derived generation number

validations:
  - checksum_sha256: recomputed against all fields (excluding checksum)
  - file_seq: monotonic continuity check
  - hybrid_id: extracted from comment via validate_key() (confirmed)
  - generation derived from parsed hybrid_id or defaults to 1
    (confirmed: _determine_generation() in processor.py lines 306–316)

identifiers_generated: none

identifiers_consumed:
  - file_seq: validated
  - checksum_sha256: validated
  - hybrid_id: parsed and validated

persistence:
  - UNKNOWN — validation result not persisted separately

failure_branch:
  - Checksum mismatch:
      detection: recomputed sha256 ≠ stored sha256
      handling: UNDEFINED — not specified in source
      halt_retry: UNDEFINED
  - Sequence gap:
      detection: file_seq discontinuity
      handling: UNDEFINED — not specified in source
      halt_retry: UNDEFINED
  - Invalid hybrid_id format:
      detection: validate_key() returns False
      handling: logged as warning (confirmed); processing continues with fallback
        (confirmed: _compose_hybrid_id fallback in processor.py lines 164–167)
      halt_retry: does NOT halt; uses fallback composition
```

---

#### Step S18 — Normalize Broker Events to Canonical Reports

```
step_id: S18
name: Normalize broker events to canonical reports
module_id: B3_EXEC_EVENT_NORMALIZER
purpose: Translate raw BrokerExecEvent into canonical ExecutionReport and PositionSnapshot
owner: event-gateway
status: partial
entrypoint_files:
  - services/event-gateway/src/2099900141260118_main.py

inputs:
  - BrokerExecEvent + ResolvedConfig

outputs:
  - ExecutionReport (schema: ExecutionReport@1.0)
  - PositionSnapshot

identifiers_generated:
  - UNKNOWN — normalization adds canonical fields; exact additions not confirmed

identifiers_consumed:
  - trade_id (from S17a): forwarded
  - hybrid_id (from S17b): forwarded if present

validations:
  - Dedup + ordering policy (EventFilter confirmed)
  - Canonical rounding (EventTransformer confirmed)
  - Conditional routing: confidence_score > 0.8 (confirmed in event-gateway config)

persistence:
  - Redis: eafix.execution.completed (ExecutionReport@1.0) — confirmed schema
  - Redis DLQ: eafix.execution.completed.dlq (max 3 retries, confirmed)

failure_branch:
  - detection: Malformed BrokerExecEvent
  - handling: Quarantine to DLQ (max 3 retries then dead-letter, confirmed)
  - halt_retry: After 3 retries, message goes to DLQ; processing continues
```

---

### PHASE F — OMS → CLOSE → OUTCOME BUCKET

**PHASE STATUS: PLANNED** — Steps S19–S21 have no confirmed source implementations.

---

#### Step S19 — Apply Execution Reports to OMS State

```
step_id: S19
name: Apply execution reports to OMS state
module_id: O2_OMS_STATE_MACHINE
purpose: Update internal order/position state machine from ExecutionReport;
  detect trade close events
owner: UNMAPPED — oms.py not confirmed in repo
status: planned
entrypoint_files:
  - UNMAPPED — source not confirmed

inputs:
  - RoutedOrderIntent + ExecutionReport + PositionSnapshot + ResolvedConfig

outputs:
  - OrderStateChanged
  - PositionStateChanged
  - TradeClosedRaw

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - trade_id (from S17): forwarded
  - client_order_id (from S14): matched
  - idempotency_key (from S14): validated for dedup

validations:
  - Idempotent fills (idempotency_key)
  - Out-of-order handling per policy (UNDEFINED — policy not confirmed)
  - Stable final state

persistence:
  - UNKNOWN — OMS state store not confirmed

failure_branch:
  - detection: OMS state inconsistency; order mismatch
  - handling: Quarantine stream; halt new orders
  - halt_retry: UNDEFINED

explicit_persistence_substep:
  - Decision audit log: UNKNOWN — data store not confirmed
  - Execution result storage: UNKNOWN — data store not confirmed
```

---

#### Step S20 — Classify Trade Close and Compute Canonical PnL

```
step_id: S20
name: Classify trade close and compute canonical PnL
module_id: O3_TRADE_CLOSE_CLASSIFIER
purpose: Assign close reason enum; compute canonical PnL with deterministic rounding
owner: UNMAPPED — trade_close_classifier.py not confirmed in repo
status: planned
entrypoint_files:
  - UNMAPPED — source not confirmed

inputs:
  - TradeClosedRaw + ResolvedConfig

outputs:
  - TradeClosed (close_reason enum + canonical PnL + profit_loss_pips)

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - trade_id (from S17): forwarded
  - hybrid_id (from S17b): forwarded

validations:
  - Close reason in enum
  - Deterministic PnL rounding rules (UNDEFINED — rounding rules not confirmed
      in source)

persistence:
  - UNKNOWN — data store not confirmed

failure_branch:
  - detection: PnL computation error
  - handling: Emit TradeClosed with COMPUTATION_ERROR flag
  - halt_retry: UNDEFINED
```

---

#### Step S21 — Bucketize Outcome

```
step_id: S21
name: Bucketize outcome
module_id: E1_OUTCOME_BUCKETIZER
purpose: Map TradeClosed PnL to canonical outcome bucket for matrix lookup
owner: UNMAPPED as dedicated service; outcome classification CONFIRMED in
  reentry-engine processor (lines 240–249) but as part of reentry, not prior step
status: planned (as dedicated service); partial (as inline in reentry-engine)
entrypoint_files:
  - UNMAPPED — standalone outcome_bucketizer.py not confirmed
  - services/reentry-engine/src/2099900169260118_processor.py (inline classification
      confirmed here)

inputs:
  - TradeClosed + ResolvedConfig

outputs:
  - OutcomeBucket: WIN | LOSS | BREAKEVEN (coarse)
    mapped further to: W2 | W1 | BE | L1 | L2 (fine-grained vocab token)
    (confirmed: _map_outcome_to_token() in reentry-matrix-svc processor.py)

identifiers_generated:
  - outcome_class: WIN | LOSS | BREAKEVEN (confirmed in reentry-engine processor)

identifiers_consumed:
  - profit_loss_pips (from S20): used as classification threshold
    (confirmed: settings.profit_threshold_pips, settings.loss_threshold_pips)

validations:
  - Only enumerated buckets allowed
  - Bucket thresholds: configurable via settings

persistence:
  - UNKNOWN — as dedicated service output store not confirmed
  - In reentry-engine: outcome_class written to ReentryDecision CSV (confirmed)

failure_branch:
  - detection: PnL outside expected range
  - handling: UNKNOWN bucket, quarantine for review (per process contract;
      not confirmed in reentry-engine source — inline classification has no
      quarantine path confirmed)
  - halt_retry: UNDEFINED

outcome_mapping_confirmed:
  - threshold: settings.profit_threshold_pips (confirmed field name)
  - WIN → W1 (default; W2 not implemented in current mapping — confirmed stub
      in processor.py line 172)
  - LOSS → L1 (default; L2 not implemented in current mapping)
  - BREAKEVEN → BE
  - NOTE: WIN/LOSS sub-ranking (W2 vs W1, L2 vs L1) is UNDEFINED in current
      source — mapping returns W1 or L1 only
```

---

### PHASE G — REENTRY DECISION → REENTRY INTENT

---

#### Step S22 — Compute Event Proximity

```
step_id: S22
name: Compute event proximity
module_id: E2_PROXIMITY_EVALUATOR
purpose: Determine proximity state of current time relative to calendar events
  (PRE_1H | AT_EVENT | POST_30M)
owner: reentry-engine (inline stub — not dedicated service)
status: partial — STUB implementation only
entrypoint_files:
  - services/reentry-engine/src/2099900169260118_processor.py
    lines 278–291 (_determine_proximity_state method)
  - NOTE: YAML also lists services/event-gateway/src/2099900141260118_main.py
      for this step; proximity logic not confirmed in event-gateway source

inputs:
  - CLAIMED: CalendarEvent + ClockTick + ResolvedConfig
  - ACTUAL (confirmed): trade_result.open_time (hour-of-day heuristic only)

outputs:
  - proximity_state: PRE_1H | AT_EVENT | POST_30M

identifiers_generated:
  - proximity_state: generated here (stub)

identifiers_consumed:
  - calendar_id (from S6): NOT ACTUALLY CONSUMED in current implementation
    (CONFLICT-06)
  - trade open_time: used as proxy

validations:
  - proximity_state in allowed vocabulary (confirmed via vocab validation)
  - Frozen-time supported: UNDEFINED — not confirmed in stub

persistence:
  - none

failure_branch:
  - detection: UNDEFINED in stub
  - handling: Defaults to "POST_30M" implicitly (time-of-day logic has no
      explicit default or error path)
  - halt_retry: UNDEFINED

CRITICAL GAP:
  - Real proximity computation requires live CalendarEvent lookup
  - Current implementation uses hour-of-day heuristic (8–10h = AT_EVENT,
      7–11h = PRE_1H, else POST_30M — hardcoded in processor.py lines 286–291)
  - This will produce incorrect proximity_state for any trade not in common
      news hours
  - UNDEFINED — integration with calendar-ingestor or live event store not planned
      in confirmed source
```

---

#### Step S23 — Lookup Matrix Decision

```
step_id: S23
name: Lookup matrix decision
module_id: E3_MATRIX_LOOKUP
purpose: Resolve parameter set and action type from 4D matrix keyed on
  (OutcomeBucket × EventProximity × SignalContext × MatrixProfile)
owner: reentry-matrix-svc
status: implemented
entrypoint_files:
  - services/reentry-matrix-svc/src/2099900174260118_main.py
  - services/reentry-matrix-svc/src/2099900177260118_processor.py
  - services/reentry-matrix-svc/src/2099900178260118_resolver.py

inputs:
  - OutcomeBucket (outcome_class: WIN | LOSS | BREAKEVEN)
  - EventProximity (proximity_state: PRE_1H | AT_EVENT | POST_30M)
  - SignalContext (calendar_id, duration_class, direction, generation)
  - MatrixProfile (parameter sets from config/1199900002260118_parameter_sets.json)
  - ResolvedConfig

outputs:
  - MatrixDecision:
      - parameter_set_id: resolved parameter set identifier
      - resolved_tier: GLOBAL | TIER3 | TIER2 | TIER1 | EXACT
      - reentry_enabled: bool
      - generation_allowed: bool
      - max_generation: int (max 3)
      - lot_size_multiplier: float
      - stop_loss_pips: int
      - take_profit_pips: int
      - confidence_threshold: float
      - specificity_score: float
  - MatrixFallbackUsed: bool (when exact match absent)

resolution_tiers_confirmed:
  - GLOBAL: default parameters (lowest specificity)
  - TIER3: calendar-type specific (e.g., CAL8_HIGH_IMPACT)
  - TIER2: outcome-class specific (WIN_OUTCOMES, LOSS_OUTCOMES)
  - TIER1: duration-class specific (FLASH, QUICK, LONG, EXTENDED)
  - EXACT: full key match (highest specificity)
  (confirmed: config/1199900002260118_parameter_sets.json + resolver.py)

identifiers_generated:
  - parameter_set_id: resolved from config; forwarded
  - resolved_tier: generated here

identifiers_consumed:
  - outcome_class (from S21)
  - proximity_state (from S22): STUB value — see CONFLICT-06
  - calendar_id (from S22 stub): STUB value — see CONFLICT-07
  - duration_class (from S17a/S21)
  - direction (from S17a)
  - generation (from S17b)

validations:
  - Deterministic fallback hierarchy (confirmed: tiered resolver)
  - Matrix version pinned (UNMAPPED — pinning mechanism not confirmed)
  - generation ≤ max_generation (confirmed: generation_allowed check)

persistence:
  - Matrix lookup result: UNKNOWN — lookup history not confirmed persisted
  - CSV: ./data/reentry-matrix/ (ReentryDecision written by processor.py)

failure_branch:
  - Matrix missing for all tiers:
      detection: No parameter set matches any tier
      handling: Use GLOBAL fallback (lowest tier always present per config)
      halt_retry: GLOBAL tier fallback prevents halt
  - generation exceeds max:
      detection: request.generation >= resolved_params["max_generation"]
      handling: reentry_action = "NO_REENTRY" (confirmed in processor.py line 188)
      halt_retry: does not retry; returns NO_REENTRY decision

explicit_persistence_substep:
  - Matrix lookup history: UNKNOWN — data store not confirmed
  - KPI / health metric emission: UNKNOWN — metrics recorded but store not confirmed
```

---

#### Step S24 — Build Reentry Trade Intent (or Suppress)

```
step_id: S24
name: Build reentry trade intent (or suppress)
module_id: E4_REENTRY_INTENT_BUILDER
purpose: Generate hybrid_id; write ReentryDecision CSV; determine next action
  (R1 | R2 | NO_REENTRY | HOLD)
owner: reentry-engine
status: implemented
entrypoint_files:
  - services/reentry-engine/src/2099900166260118_main.py
  - services/reentry-engine/src/2099900169260118_processor.py

inputs:
  - MatrixDecision (from S23, via decision_client HTTP call)
  - ReentryChainState (current generation, cooldown state, daily attempt counts)
  - ResolvedConfig

outputs:
  - ReentryDecision CSV record (confirmed)
  - reentry_action: R1 | R2 | NO_REENTRY | HOLD
  - hybrid_id (newly composed)
  - OR ReentrySuppressed (cooldown, daily limit, eligibility failure)

identifiers_generated:
  - hybrid_id: composed by HybridIdHelper.compose() via shared/reentry/
      2099900218260118_hybrid_id.py (confirmed)
    format: OUTCOME_DURATION_PROXIMITY_CALENDAR_DIRECTION_GENERATION[_SUFFIX]
    components:
      - outcome: W1 | W2 | BE | L1 | L2 (mapped from WIN/LOSS/BREAKEVEN;
          NOTE: W2 and L2 mapping is stub — see S21 note)
      - duration: FLASH | QUICK | LONG | EXTENDED
      - proximity: PRE_1H | AT_EVENT | POST_30M (from stub at S22)
      - calendar: CAL8_* | CAL5_* | NONE (from stub at S22/S23)
      - direction: LONG | SHORT | ANY
      - generation: 1 | 2 | 3
    MT4 comment form: abbreviated via decompose_for_comment() (31 char limit)
      (confirmed: hybrid_id.py lines 310–337)
  - file_seq: for ReentryDecision CSV (confirmed: self.csv_sequence)
  - checksum_sha256: for ReentryDecision CSV (confirmed: compute_checksum())
  - chain_position: O | R1 | R2 (confirmed: get_chain_position(generation))

identifiers_consumed:
  - trade_id (from S17): carried through
  - outcome_class (from S21): consumed for hybrid_id composition
  - duration_class (from S21): consumed for hybrid_id composition
  - proximity_state (from S22): consumed for hybrid_id composition
  - calendar_id (from S22 stub): consumed for hybrid_id composition
  - direction (from S17a): consumed for hybrid_id composition
  - generation (from S17b): consumed; determines chain position

validations:
  - Hard cap: generation ≤ 3 (R2 is maximum) (confirmed: min(current+1, 3))
  - Cooldown check before processing (confirmed: _check_reentry_eligibility)
  - Daily attempt limit check (confirmed: max_reentry_attempts_per_day)
  - hybrid_id vocabulary validation (confirmed: validate_key())
  - checksum verification after compute (confirmed: verify_checksum())

persistence:
  - CSV: ./data/reentry-engine/ (atomic write confirmed)
    schema: contracts/schemas/csv/0199900029260118_reentry_decisions.csv.md
  - In-memory: recent_decisions list (last 100, confirmed)
  - In-memory: symbol_cooldowns dict (confirmed)
  - In-memory: daily_attempt_counts dict (confirmed)
  - NOTE: In-memory state is NOT durable — lost on service restart

failure_branch:
  - Cooldown active:
      detection: now < cooldown_end (confirmed)
      handling: return {"status": "skipped", "reason": "cooldown_period_active"}
      halt_retry: skips; does not retry
  - Daily limit exceeded:
      detection: count ≥ max_reentry_attempts_per_day (confirmed)
      handling: return {"status": "skipped", "reason": "daily_limit_exceeded"}
      halt_retry: skips until next day reset
  - Max generation reached:
      detection: generation ≥ max_generation (confirmed)
      handling: reentry_action = "NO_REENTRY" | "HOLD"
      halt_retry: terminal for this chain
  - hybrid_id composition failure:
      detection: ValueError from compose()
      handling: fallback to manual string join (confirmed: lines 164–167)
      halt_retry: does not halt; uses fallback
  - CSV write failure:
      detection: exception in _write_reentry_decision_csv
      handling: logs error; raises (caller must handle)
      halt_retry: UNDEFINED — no retry confirmed in processor

chain_history_persistence:
  - UNKNOWN — no confirmed durable chain history store
  - In-memory only (lost on restart)
```

---

#### Step S25 — Loop: Reentry Intent → Risk Chain

```
step_id: S25
name: Loop: reentry intent follows same risk→order→route→transport→execute chain
module_id: (loop)
purpose: Feed ReentryDecision (when action = R1 or R2) back into risk evaluation
  chain for execution as a new trade
owner: UNMAPPED — flow-orchestrator (PLANNED); no confirmed implementation
status: planned
entrypoint_files:
  - UNMAPPED — flow-orchestrator/src has no confirmed source
  - YAML lists services/transport-router/src/2099900199260118_main.py — wrong for
      loop coordination

inputs:
  - TradeIntent derived from ReentryDecision (from S24)
  - reentry_action: R1 | R2

outputs:
  - Either: new RoutedOrderIntent entering S13→S14→S15→S16 chain
  - Or: suppression / cooldown state update

identifiers_generated:
  - new hybrid_id (generation+1): generated at S24 for next iteration
  - new file_seq: generated at S16c for next transport

identifiers_consumed:
  - hybrid_id (from S24): forwarded into new TradeIntent
  - chain_position (from S24): used to enforce R2 cap

validations:
  - Chain depth < configured max (hard cap at generation 3 = R2)
  - Velocity limits: UNDEFINED — not confirmed in source
  - Idempotency keys enforced: UNDEFINED — loop idempotency not confirmed

persistence:
  - UNKNOWN — loop iteration state not confirmed in durable store

failure_branch:
  - Loop prevention triggered:
      detection: generation > 3 (enforced at S24)
      handling: terminal cooldown; stop (enforced at S24)
      halt_retry: confirmed terminal at R2
  - Orchestrator unavailable:
      detection: UNDEFINED
      handling: UNDEFINED
      halt_retry: UNDEFINED
```

---

### PHASE H — CROSS-CUTTING CONTROLS

---

#### Step S26 — Health Aggregation + SLO Evaluation

```
step_id: S26
name: Health aggregation + SLO evaluation
module_id: P1_HEALTH_AGGREGATOR
purpose: Aggregate health signals from all services; evaluate SLOs; emit HealthReport;
  enforce risk-off posture if health unknown
owner: UNMAPPED — health_service.py not confirmed; telemetry-daemon listed in YAML
status: planned
entrypoint_files:
  - UNMAPPED — services/telemetry-daemon/src/2099900192260118_main.py listed in YAML;
      not confirmed read; contents unknown

inputs:
  - AdapterHealth (from transport-router IntegrityValidator health checks)
  - ModuleHealth (from each service /healthz endpoint — confirmed pattern)
  - ResolvedConfig

outputs:
  - HealthReport

identifiers_generated:
  - UNKNOWN

identifiers_consumed:
  - UNKNOWN

validations:
  - Deterministic thresholds
  - Stable report format

persistence:
  - CSV: ./data/telemetry-daemon/HealthMetric records
    schema confirmed: contracts/schemas/csv/0199900028260118_health_metrics.csv.md

failure_branch:
  - detection: Health unknown or service unreachable
  - handling: Default to risk-off posture; suppress new intents
  - halt_retry: UNDEFINED — how risk-off is enforced upstream not confirmed

explicit_persistence_substep:
  - HealthMetric CSV: ./data/telemetry-daemon/ (schema confirmed; atomic write assumed)
  - KPI emission: UNKNOWN — KPI store not confirmed
```

---

### IDENTIFIER GENERATION AND PARAMETER-SET RESOLUTION (NEW SECTIONS)

---

#### Identifier Generation Summary

| Identifier | Format | Generated By | Generation Step | Consumed By | Consumption Steps |
|---|---|---|---|---|---|
| calendar_id | CAL8_* or CAL5_* or NONE | calendar-ingestor (ingestor.py) | S4 | signal-generator, reentry-engine, reentry-matrix-svc | S11, S22, S23, S24 |
| proximity_state | PRE_1H \| AT_EVENT \| POST_30M | calendar-ingestor (S6) THEN stub in reentry-engine (S22) | S6, S22 | reentry-engine, reentry-matrix-svc | S23, S24 |
| correlation_id | UNMAPPED | UNMAPPED | S11 (planned) | S12–S15 | S12–S15 |
| client_order_id | UNMAPPED | UNMAPPED | S14 (planned) | S15–S19 | S15–S19 |
| idempotency_key | UNMAPPED | UNMAPPED | S14 (planned) | S14–S17 | S14–S17 |
| file_seq | integer ≥1 per service instance | CSV-writing services (reentry-engine, reentry-matrix-svc, transport-router) | S16c, S24 | IntegrityValidator (transport-router) | S16d, S17b |
| checksum_sha256 | SHA-256 hex 64-char | CSV-writing services | S16c, S24 | IntegrityValidator | S16d, S17b |
| trade_id | assigned by broker/MT4 | EAFIX.mq4 at OrderSend() | S17 | reentry-engine, reentry-matrix-svc | S17a, S21, S23, S24 |
| hybrid_id (Python) | OUTCOME_DURATION_PROXIMITY_CALENDAR_DIRECTION_GENERATION[_SUFFIX] | reentry-engine (hybrid_id.py compose()) | S24 | reentry-engine, reentry-matrix-svc, MT4 comment | S24, S25, S17 (next iteration) |
| hybrid_id (MQL4 reentry_key) | SIG~TB~OB~PB~G (tilde-delimited) | EAFIX.mq4 (ReentryHelpers.mq4) | S17 | EAFIX.mq4 internal | S17 internal |
| parameter_set_id | config key string | reentry-matrix-svc (resolver.py) | S23 | reentry-engine | S24 |
| resolved_tier | GLOBAL\|TIER3\|TIER2\|TIER1\|EXACT | reentry-matrix-svc (resolver.py) | S23 | reentry-engine | S24 |
| chain_position | O \| R1 \| R2 | reentry-engine (get_chain_position()) | S24 | reporter, downstream | S24, S25 |
| comment_suffix | 6-char alphanumeric | Python: SHA-256 (hybrid_id.py); MQL4: FNV32→Base32 (ReentryHelpers.mq4 — fallback only) | S24 (Python authoritative) | MT4 trade comment | S17 |
| strategy_id | UNMAPPED | UNMAPPED | UNMAPPED | UNMAPPED | UNMAPPED |
| decision_id | UNMAPPED | UNMAPPED | UNMAPPED | UNMAPPED | UNMAPPED |

---

#### Parameter-Set Resolution (S23 Detail)

```
parameter_set_resolution:
  config_file: config/1199900002260118_parameter_sets.json
  tier_hierarchy:
    1. EXACT match: calendar_id + outcome_class + duration_class + generation
    2. TIER1: duration_class match
    3. TIER2: outcome_class match (WIN_OUTCOMES | LOSS_OUTCOMES)
    4. TIER3: calendar_id type match (CAL8_HIGH_IMPACT)
    5. GLOBAL: default parameters (always present)
  max_generation: 3 (hard cap; R2 = generation 3)
  confirmed_parameter_fields_per_set:
    - parameter_set_id
    - reentry_enabled: bool
    - generation_allowed: bool
    - max_generation: int
    - lot_size_multiplier: float
    - stop_loss_pips: int
    - take_profit_pips: int
    - confidence_threshold: float
    - specificity_score: float
  unconfirmed_fields_from_matrix_doc (0199900012260118_most_acurate_matirx_doc.md):
    - action_type: NO_REENTRY | SAME_TRADE | REVERSE | INCREASE_SIZE
    - size_multiplier
    - confidence_adjustment
    - delay_minutes
    - max_attempts
    - performance_tracking (execution counts, PnL, success rates)
    NOTE: These fields appear in matrix documentation but are NOT confirmed
    present in confirmed implementation source (resolver.py, parameter_sets.json)
```

---

#### Risk Overlay Application (S13 Detail)

```
risk_overlay_confirmed_parameters (from tactical spec + plugin):
  - max_risk_percent_per_trade: 2.0% (tactical spec)
  - max_risk_cap_percent (reentry): 3.50% (FR-P2 from 0199900015260118)
  - daily_drawdown_limit: 5.0% (tactical spec)
  - max_portfolio_correlation: UNDEFINED — not confirmed in source
  - position_sizing_method: risk-based on account equity (confirmed: plugin.py)
risk_overlay_status: PLANNED — risk-manager has plugin only; main processor not confirmed
```

---

#### Transport Acknowledgment Lifecycle

```
transport_ack_lifecycle:
  csv_path:
    1. Write to .tmp (tempfile, delete=False)
    2. fsync() for durability
    3. os.rename() / Path.rename() to target
    4. Ack = file present and readable
    5. IntegrityValidator recomputes checksum and sequence (confirmed)
    retry_count: 3 (CSVRouter confirmed)
    backoff: exponential (confirmed)
    on_persistent_failure: UNDEFINED

  socket_path (DLL bridge):
    protocol: TCP JSON (confirmed in tactical spec)
    ports: EA=5555, Python=9999 (confirmed)
    heartbeat: SocketSendHeartbeat() (DLL API confirmed in tactical spec)
    ack: UNDEFINED — Python-side ack handling not confirmed in repo source
    health_demotion: UNDEFINED — demotion logic not confirmed in Python source
    retry_fail: UNDEFINED — not confirmed in Python source
    fallback: demote to CSV (per tactical spec 3-tier; implementation UNDEFINED)
```

---

#### Health and Monitoring Emission

```
health_monitoring:
  per_service_health_endpoint: GET /healthz (confirmed pattern in transport-router)
  transport_router_health_checks_confirmed:
    - Redis connectivity
    - File system access + disk space
    - Watched directory accessibility
    - Downstream service health (HTTP)
    - Contract system availability
    - Configuration validity
  health_metric_csv:
    schema: contracts/schemas/csv/0199900028260118_health_metrics.csv.md
    confirmed_fields: service_name, metric_name, health_status, cpu_usage,
      memory_usage, file_seq, checksum_sha256, timestamp
    destination: ./data/telemetry-daemon/
  redis_health_topic: eafix.orchestrator.status (OrchestratorStatus@1.0) — planned
  aggregator: UNMAPPED — telemetry-daemon confirmed referenced but not read
```

---

#### Startup / Bootstrap Ordering

```
bootstrap_ordering:
  confirmed: UNDEFINED — no startup/boot sequencing document found in repo
  inferred_from_dependencies:
    1. Redis must be running (all services depend on it)
    2. calendar-ingestor (no upstream service deps)
    3. transport-router (watches ./data/ directories; upstream-agnostic)
    4. event-gateway (depends on Redis topics being populated)
    5. risk-manager (depends on signals from signal-generator)
    6. signal-generator (depends on calendar-ingestor output)
    7. reentry-engine (depends on trade results from execution-engine)
    8. reentry-matrix-svc (depends on reentry-engine requests via HTTP)
    9. MT4 EA (must start after Python socket listener is ready)
  service_discovery: UNDEFINED — no service registry confirmed
  health_gate: UNDEFINED — whether services wait for upstream health before
    processing is not confirmed
```

---

#### Multi-Symbol and Portfolio Coordination

```
multi_symbol_coordination:
  confirmed:
    - Per-symbol cooldown tracking in reentry-engine (symbol_cooldowns dict)
    - Per-symbol daily attempt counts (daily_attempt_counts dict)
    - Symbol field present in all CSV schemas (confirmed)
    - CalendarTrigger includes symbol set (confirmed in process YAML)
  planned:
    - Portfolio correlation monitoring (referenced in tactical spec + risk plugin)
    - Multi-symbol portfolio-level position limits
  unconfirmed:
    - Mechanism for cross-symbol position correlation check
    - Portfolio-level drawdown aggregation
```

---

#### Manual Override / Emergency Stop / Risk-Off Suppression

```
manual_override_emergency_stop:
  confirmed:
    - risk-off posture: triggered by unknown health (Step S26 failure branch)
    - StateManager STATE_PAUSED: described in tactical spec for EA-side pause
    - FR-OPS2 freezing logic: referenced in 0199900015260118_SS_HUEY_P
      (EA freezes on detected anomaly)
    - Compliance auto-remediation engine: compliance/auto-remediation/
      2099900012260118_remediation-engine.py — confirmed to exist;
      relationship to trading flow is UNMAPPED
  unconfirmed:
    - Manual override endpoint or command
    - Emergency stop propagation from Python to MT4 EA
    - Risk-off signal format and path
    - How risk-off suppression is received by signal-generator or flow-orchestrator
  status: UNDEFINED — emergency stop mechanism not confirmed end-to-end in source
```

---

## SECTION 4 — DATA STORE MAP

| Stage | Step(s) | Store Type | Location / Topic | Schema | Confirmed |
|---|---|---|---|---|---|
| Calendar events | S4–S5 | Redis pub/sub | eafix.calendar.events | CalendarEvent@1.0 | Yes — schema confirmed |
| Calendar signals | S5–S6 | Redis pub/sub | eafix.calendar.signals | ActiveCalendarSignal@1.0 | Yes — schema implied |
| Calendar signals | S5–S6 | CSV (atomic) | ./data/calendar-ingestor/ | active_calendar_signals.csv.md | Yes — schema confirmed |
| Market ticks | S7 | Redis pub/sub | eafix.price.tick | PriceTick@1.0 | Schema confirmed; producer UNMAPPED |
| Indicators | S9 | Redis pub/sub | eafix.indicators.computed | IndicatorVector@1.1 | Schema confirmed; producer UNMAPPED |
| Signals | S11 | Redis pub/sub | eafix.signals.generated | Signal@1.0 | Schema confirmed; producer UNMAPPED |
| Order intents | S13 | Redis pub/sub | eafix.orders.validated | OrderIntent@1.2 | Schema confirmed; producer UNMAPPED |
| Broker orders | S16c | CSV (atomic) | ./data/[service]/ | BrokerOrderEnvelope (UNMAPPED) | Atomic write confirmed; schema UNMAPPED |
| Execution results | S17a–S18 | Redis pub/sub | eafix.execution.completed | ExecutionReport@1.0 | Schema confirmed; producer UNMAPPED |
| Execution results | S17a | CSV | ./data/execution-engine/ | trade_results.csv.md | Schema confirmed; writer UNMAPPED |
| OMS state | S19 | UNKNOWN | UNKNOWN | UNKNOWN | Not confirmed |
| Trade closed | S20 | UNKNOWN | UNKNOWN | UNKNOWN | Not confirmed |
| Outcome bucket | S21 | CSV (inline) | ./data/reentry-engine/ (inferred) | reentry_decisions.csv.md (combined) | Partial — inline in S24 |
| Reentry decisions | S23–S24 | CSV (atomic) | ./data/reentry-matrix/ | reentry_decisions.csv.md | Yes — processor.py confirmed |
| Reentry decisions | S24 | CSV (atomic) | ./data/reentry-engine/ | reentry_decisions.csv.md | Yes — processor.py confirmed |
| Reentry decisions | S23–S24 | Redis pub/sub | eafix.reentry.decisions | ReentryDecision@1.0 | Schema confirmed |
| Health metrics | S26 | CSV | ./data/telemetry-daemon/ | health_metrics.csv.md | Schema confirmed; writer UNMAPPED |
| Health metrics | S26 | Redis pub/sub | eafix.orchestrator.status | OrchestratorStatus@1.0 | Planned |
| SQLite (GUI/analytics) | All | SQLite | per-symbol .db files | UNKNOWN | Tactical spec only; not in microservice layer |
| Postgres | All | Postgres | UNKNOWN | UNKNOWN | Optional enterprise; NOT currently active |
| Dead-letter queue | S18 | Redis DLQ | eafix.*.dlq | same as topic | Confirmed — max 3 retries |
| Parameter sets | S23 | JSON file | config/1199900002260118_parameter_sets.json | UNKNOWN — no JSON schema for this file | Yes — file confirmed |
| Reentry vocabulary | S24 | JSON file | shared/reentry/1199900031260118_reentry_vocab.json | UNKNOWN | Yes — file confirmed |
| Audit log | All | UNKNOWN | UNKNOWN | UNKNOWN | Not confirmed |
| Chain history | S24–S25 | In-memory dict | reentry-engine RAM | N/A | Confirmed in-memory; not durable |

---

## SECTION 5 — GAP REGISTER

| ID | Type | Location | Description |
|---|---|---|---|
| GAP-01 | UNMAPPED | S1 | configuration_service.py not found in repo; ResolvedConfig generation point unconfirmed |
| GAP-02 | UNMAPPED | S7 | data-ingestor has no confirmed main source; market tick ingestion unimplemented <!-- STATUS: implemented — data-ingestor main + ingestor confirmed --> |
| GAP-03 | UNMAPPED | S8 | bar_builder.py not found; Bar aggregation unimplemented |
| GAP-04 | UNMAPPED | S9 | indicator-engine src has no confirmed source; YAML entrypoint is wrong service |
| GAP-05 | UNMAPPED | S10 | feature_packager.py not found; FeatureFrame assembly unimplemented |
| GAP-06 | UNMAPPED | S11 | signal-generator/src has __pycache__ only; Signal@1.0 producer unimplemented <!-- closed: Phase 2 --> |
| GAP-07 | UNMAPPED | S11 | YAML entrypoint for S11 is compliance/auto-remediation — wrong service <!-- STATUS: doc-correction — S11 entrypoint_files is UNMAPPED; compliance path reference was incorrect --> |
| GAP-08 | UNMAPPED | S12 | intent_builder.py not found; TradeIntent construction unimplemented |
| GAP-09 | UNMAPPED | S13 | risk-manager has plugin only; risk evaluation processor unimplemented <!-- closed: Phase 2 --> |
| GAP-10 | UNMAPPED | S14 | order_intent_compiler.py not found; OrderIntent compilation unimplemented |
| GAP-11 | UNMAPPED | S14 | client_order_id and idempotency_key generation point not confirmed <!-- closed: Phase 2 --> |
| GAP-12 | UNMAPPED | S15 | order_router.py not found; broker routing logic unimplemented as standalone |
| GAP-13 | UNMAPPED | S16c | BrokerOrderEnvelope CSV schema not confirmed (transport-router output schema) |
| GAP-14 | CONFLICTING | S17 | EAFIX.mq4 (real 7000-line EA) not present in repo; placeholder SMA EA present <!-- STATUS: DEFERRED_EA — requires MQL4 development (EAFIX.mq4) --> |
| GAP-15 | UNMAPPED | S17 | MQL4_DLL_SocketBridge.dll not in repo; DLL bridge unconfirmed as artifact <!-- STATUS: DEFERRED_EA — requires C++ DLL (MQL4_DLL_SocketBridge.dll) --> |
| GAP-16 | UNMAPPED | S17 | YAML entrypoint for S17 is transport-router — wrong service <!-- STATUS: doc-correction — S17 entrypoint_files is UNMAPPED; transport-router reference was incorrect --> |
| GAP-17 | UNDEFINED | S17 | EA-side broker rejection handling; error code behavior; retry policy <!-- STATUS: DEFERRED_EA — EA-side broker rejection handling --> |
| GAP-18 | UNMAPPED | S17a | execution-engine has plugin only; TradeResult ingestion unimplemented |
| GAP-19 | UNDEFINED | S17a | Timeout / no-result path when EA produces no BrokerExecEvent <!-- closed: Phase 3 --> |
| GAP-20 | UNDEFINED | S16c–S16d | Socket transport ack semantics; heartbeat response handling; demotion logic <!-- STATUS: DEFERRED_EA — full socket ack/heartbeat/demotion requires DLL --> |
| GAP-21 | CONFLICTING | S16b | Transport tier selection: tactical spec (3-tier) vs transport-router (CSV only confirmed) <!-- closed: Phase 3 --> |
| GAP-22 | UNMAPPED | S19 | oms.py not found; OMS state machine unimplemented <!-- closed: Phase 3 --> |
| GAP-23 | UNMAPPED | S19 | Decision audit log data store not confirmed <!-- closed: Phase 3 --> |
| GAP-24 | UNMAPPED | S19 | Execution result persistent storage (beyond ephemeral Redis) not confirmed <!-- closed: Phase 3 --> |
| GAP-25 | UNMAPPED | S20 | trade_close_classifier.py not found; TradeClosed PnL classification unimplemented <!-- closed: Phase 3 --> |
| GAP-26 | UNDEFINED | S20 | Deterministic PnL rounding rules not specified in source |
| GAP-27 | UNMAPPED | S21 | outcome_bucketizer.py not found as standalone; inline in reentry-engine only |
| GAP-28 | UNDEFINED | S21 | W2 vs W1 and L2 vs L1 ranking logic: current code always maps WIN→W1, LOSS→L1 <!-- closed: Phase 3 --> |
| GAP-29 | CONFLICTING | S22 | proximity_state computed via time-of-day stub; real calendar integration absent <!-- closed: Phase 1 --> |
| GAP-30 | CONFLICTING | S22 | calendar_id derivation uses hardcoded heuristic ("USD" + pips > 20); real lookup absent <!-- closed: Phase 1 --> |
| GAP-31 | UNDEFINED | S22 | Frozen-time support for proximity evaluator not confirmed in stub |
| GAP-32 | UNKNOWN | S23 | Matrix lookup history data store not confirmed |
| GAP-33 | UNDEFINED | S23 | action_type (SAME_TRADE | REVERSE | INCREASE_SIZE) not confirmed in resolver source <!-- closed: Phase 4 --> |
| GAP-34 | UNDEFINED | S23 | delay_minutes and max_attempts fields not confirmed in resolver source <!-- closed: Phase 4 --> |
| GAP-35 | UNDEFINED | S23 | performance_tracking (execution counts, PnL, success rates) not confirmed in source <!-- closed: Phase 4 --> |
| GAP-36 | UNDEFINED | S24 | Durable chain history store: in-memory only; lost on restart <!-- closed: Phase 4 --> |
| GAP-37 | UNDEFINED | S24 | CSV write retry logic not confirmed in reentry-engine processor |
| GAP-38 | UNMAPPED | S25 | flow-orchestrator/src has no confirmed source; loop coordination unimplemented <!-- closed: Phase 5 --> |
| GAP-39 | UNDEFINED | S25 | Velocity limits for reentry loop not confirmed <!-- closed: Phase 5 --> |
| GAP-40 | UNDEFINED | S25 | Loop idempotency enforcement mechanism not confirmed <!-- closed: Phase 5 --> |
| GAP-41 | UNMAPPED | S26 | health_service.py / telemetry-daemon source not confirmed read |
| GAP-42 | UNDEFINED | S26 | KPI data store and SLO evaluation logic not confirmed |
| GAP-43 | UNDEFINED | All | Manual override / emergency stop propagation path not confirmed end-to-end |
| GAP-44 | UNDEFINED | All | Strategy startup / bootstrap ordering not documented <!-- closed: Phase 5 --> |
| GAP-45 | UNDEFINED | All | Service discovery and inter-service health gating not confirmed <!-- closed: Phase 5 --> |
| GAP-46 | CONFLICTING | S17/S24 | hybrid_id format: Python uses underscore (_), MQL4 uses tilde (~); parity mapping UNDEFINED <!-- closed: Phase 5 --> |
| GAP-47 | CONFLICTING | S16c/S24 | comment_suffix: Python uses SHA-256; MQL4 uses FNV32→Base32; cross-language parity NOT guaranteed <!-- closed: Phase 5 --> |
| GAP-48 | UNMAPPED | All | strategy_id identifier: not found in any source implementation <!-- closed: Phase 5 --> |
| GAP-49 | UNMAPPED | All | decision_id identifier: not found in any source implementation <!-- closed: Phase 5 --> |
| GAP-50 | CONFLICTING | S17 | Tactical spec (Layer C) describes EA with embedded risk/strategy logic; process contract (Layer A) says EA must contain no strategy/risk logic <!-- STATUS: DEFERRED_EA — EA strategy/risk conflict is architectural, not Python code --> |
| GAP-51 | UNDEFINED | S13 | Risk-off enforcement propagation: how S26 risk-off posture reaches S11/S13 not confirmed <!-- closed: Phase 5 --> |
| GAP-52 | UNDEFINED | All | Postgres activation path: mentioned as optional enterprise; no migration or schema confirmed <!-- STATUS: no-action — Postgres declared optional enterprise; deferred --> |

---

## SECTION 6 — FINAL ASSESSMENT

### What Appears Implemented Now

The following components have confirmed source code and substantive logic:

1. **calendar-ingestor** — polling, normalization, trigger building, Redis publishing, CSV output (partial)
2. **transport-router** — CSV watching, integrity validation (checksum + sequence), HTTP routing to downstream services
3. **event-gateway** — Redis event routing, filtering, transformation, DLQ handling
4. **reentry-matrix-svc** — tiered parameter resolution, MatrixDecision computation, CSV atomic write
5. **reentry-engine** — TradeResult processing, outcome/duration classification, hybrid_id composition, decision CSV atomic write, cooldown/limit enforcement
6. **shared/reentry** — HybridIdHelper (compose/parse/validate/comment suffix), ReentryVocabulary, confirmed cross-language parity specification
7. **mt4/ReentryHelpers.mq4** — MQL4-side reentry key compose/parse/validate (lightweight; tilde-delimited format)
8. **contracts/models** — CSV model classes with checksum computation and verification (Pydantic)
9. **contracts/schemas** — JSON event schemas (7 confirmed) and CSV schemas (4 confirmed)
10. **config/parameter_sets.json** — Tiered parameter configuration (GLOBAL through EXACT)

### What Appears Planned

The following components are referenced in process docs, ports are configured, service directories exist, but source is absent or stub-only:

1. **flow-orchestrator** — directory exists, `__pycache__` only; port 8093 configured
2. **signal-generator** — directory exists, `__pycache__` only
3. **risk-manager main** — plugin stub only; no risk evaluation processor
4. **execution-engine main** — plugin stub only; no trade ingestion processor
5. **data-ingestor** — referenced; not confirmed
6. **OMS state machine** (S19) — named in process YAML; no source
7. **trade-close classifier** (S20) — named in process YAML; no source
8. **outcome-bucketizer** (S21) — named; inline stub in reentry-engine only
9. **proximity evaluator** (S22) — named; time-of-day stub in reentry-engine only
10. **health aggregator / telemetry-daemon** — referenced; not confirmed
11. **Loop orchestration** (S25) — named; no orchestrator implementation confirmed

### What Remains Conceptual

The following are described in architecture documents but have no source artifacts in repo:

1. **EAFIX.mq4 (7000+ line straddle EA)** — extensively documented; not present in repo
2. **MQL4_DLL_SocketBridge.dll** — described in tactical spec; not present in repo
3. **DLL socket transport path** (full Python ↔ MT4 socket lifecycle)
4. **Multi-dimensional 4D matrix with 652 combinations** per symbol (documented in matrix doc; resolver uses tiered config, not a full 4D matrix)
5. **action_type enumeration** (SAME_TRADE | REVERSE | INCREASE_SIZE) — in matrix doc; not in resolver source
6. **Postgres enterprise store** — mentioned; no schema or activation path
7. **Statistical significance gating** (N≥30) — mentioned in matrix doc; not confirmed in resolver
8. **Performance tracking feedback loop** — described; not confirmed in source

### Gaps That Block a Reliable Production-Grade Process Document

The following gaps, if unresolved, make this process document insufficient as a production specification:

| Priority | Gap | Impact |
|---|---|---|
| CRITICAL | GAP-14: Real EA (EAFIX.mq4) absent | Steps S17–S17b cannot be specified; entire execution path is undefined <!-- STATUS: DEFERRED_EA — requires MQL4 development (EAFIX.mq4) --> |
| CRITICAL | GAP-29/30: Proximity and calendar_id are stubs | hybrid_id components will be wrong; matrix lookup will return wrong parameter sets |
| CRITICAL | GAP-22: OMS absent | Trade close detection, PnL computation, and outcome classification cannot be confirmed |
| CRITICAL | GAP-06: signal-generator absent | No confirmed signal generation; flow cannot start |
| CRITICAL | GAP-38: flow-orchestrator absent | No confirmed coordination between signal→risk→transport→reentry loop |
| HIGH | GAP-36: chain history not durable | Reentry generation tracking lost on restart; hard cap enforcement fails on restart |
| HIGH | GAP-46/47: hybrid_id format conflict and comment_suffix mismatch | Cross-language hybrid_id matching will fail if Python SHA-256 suffix ≠ MQL4 FNV32 suffix |
| HIGH | GAP-20: socket ack/heartbeat/demotion undefined in Python source | Transport reliability undefined for socket path <!-- STATUS: DEFERRED_EA — full socket ack/heartbeat/demotion requires DLL --> |
| HIGH | GAP-48/49: strategy_id and decision_id absent | These identifiers referenced in architecture prose cannot be traced |
| MEDIUM | GAP-28: W2/L2 sub-ranking not implemented | Outcome classification coarser than 4D matrix requires |
| MEDIUM | GAP-33/34/35: action_type, delay, performance_tracking undefined in resolver | Matrix behavior described in docs differs from confirmed implementation |
| MEDIUM | GAP-44/45: bootstrap ordering undefined | Production deployment sequencing unreliable |
| LOW | GAP-52: Postgres path undefined | Enterprise scaling path incomplete <!-- STATUS: no-action — Postgres declared optional enterprise; deferred --> |

---

*End of document. Total confirmed sources read: 18+ implementation files. Total gaps identified: 52.*

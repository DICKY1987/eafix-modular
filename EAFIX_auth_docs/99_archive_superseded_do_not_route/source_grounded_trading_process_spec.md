# Source-Grounded Trading Process Specification

Canonical source reviewed: `updated_trading_process_aligned.yaml`

Scope preserved without silent reconciliation:

- canonical contract/process flow
- current modular EAFIX runtime/source tree
- HUEY_P / MT4 bridge and EA artifacts

Requested `checksum` field note:

- runtime source uses `checksum_sha256`

## SECTION 1 - SOURCE ANALYSIS SUMMARY

Short summary of system realities found:

- The repository does not contain one coherent end-to-end runtime. It contains a canonical process contract, a partially implemented modular Python runtime, and separate MT4/HUEY_P artifacts that contradict each other in key places.
- The strongest implemented Python path is the post-trade reentry side: `reentry-engine` -> HTTP call to `reentry-matrix-svc` -> CSV decision write -> optional Redis publish.
- The strongest implemented transport/persistence path is CSV artifact production with `.tmp` + flush + rename in `calendar-ingestor`, `reentry-matrix-svc`, `reentry-engine`, and `telemetry-daemon`.
- The actual checked-in EA source file does execute broker orders, but it does so as an autonomous SMA crossover EA. It does not implement the documented CSV/socket bridge.
- Several source-present services are not runtime-clean in the current tree because they import contract modules that do not exist under the expected filenames.

Confirmed runtime artifacts:

- `services\calendar-ingestor\src\2099900092260118_ingestor.py`
- `services\calendar-ingestor\src\2099900093260118_main.py`
- `services\data-ingestor\src\2099900111260118_ingestor.py`
- `services\data-ingestor\src\2099900112260118_main.py`
- `services\indicator-engine\src\2099900159260118_plugin.py`
- `services\reentry-engine\src\2099900166260118_main.py`
- `services\reentry-engine\src\2099900169260118_processor.py`
- `services\reentry-engine\src\2099900164260118_decision_client.py`
- `services\reentry-matrix-svc\src\2099900174260118_main.py`
- `services\reentry-matrix-svc\src\2099900177260118_processor.py`
- `services\reentry-matrix-svc\src\2099900178260118_resolver.py`
- `services\transport-router\src\2099900199260118_main.py`
- `services\transport-router\src\2099900202260118_router.py`
- `services\transport-router\src\2099900203260118_validator.py`
- `services\transport-router\src\2099900204260118_watcher.py`
- `services\telemetry-daemon\src\2099900189260118_collector.py`
- `services\telemetry-daemon\src\2099900187260118_aggregator.py`
- `services\risk-manager\src\2099900183260118_plugin.py`
- `services\execution-engine\src\2099900144260118_plugin.py`
- `services\event-gateway\src\2099900139260118_gateway.py`
- `shared\reentry\2099900218260118_hybrid_id.py`
- `shared\reentry\2099900221260118_vocab.py`
- `contracts\models\2099900016260118_csv_models.py`
- `contracts\models\2099900017260118_event_models.py`
- `HUEY_P_EA_ExecutionEngine_8.mql4`
- `mt4\2299900001260118_ReentryHelpers.mq4`
- `mt4\helpers\2299900002260118_contract_parsers.mq4`
- `config\1199900002260118_parameter_sets.json`
- `data\3099900005260118_signals.db`

Planned or conceptual artifacts evidenced only by docs, tests, deleted files, or configuration:

- `flow-orchestrator` control plane runtime
- `signal-generator` runtime source
- MT4 CSV/socket bridge inside the checked-in EA
- socket heartbeat, demotion, promotion, and adapter ack handling
- Postgres-backed compliance/audit storage
- Redis Streams based service topology
- matrix lookup history persistence
- durable chain ledger / reentry ledger
- execution result writer/reader path from actual EA back into Python
- startup ordering and DB hydration as a live orchestrated sequence
- portfolio-level coordination and risk-off suppression in the modular runtime

Source conflicts or ambiguities:

- `HUEY_P_EA_ExecutionEngine_8.mql4` is a simple SMA crossover EA; `0199900003260118_HUEY_P_EA_ExecutionEngine_8.md` describes a much richer CSV + DLL socket bridge EA.
- `shared\reentry\2099900218260118_hybrid_id.py` uses underscore-delimited hybrid IDs; `mt4\2299900001260118_ReentryHelpers.mq4` uses `SIG~TB~OB~PB~G`; `docs\techspec\0110000067260118_03_identifier_systems.md` defines a hyphenated CAL8-first format.
- `services\calendar-ingestor\src\2099900092260118_ingestor.py` emits `PRE_1H`, `AT_EVENT`, `POST_30M`; `contracts\models\2099900016260118_csv_models.py` defines `ActiveCalendarSignal.proximity_state` as `IMMEDIATE`, `NEAR`, `FAR`.
- `services\data-ingestor\src\2099900109260118_config.py` publishes to `price_ticks`; `services\event-gateway\src\2099900138260118_config.py` expects `eafix.price.tick`.
- `services\calendar-ingestor\src\2099900092260118_ingestor.py` publishes `calendar_events`; `services\event-gateway\src\2099900138260118_config.py` expects `eafix.calendar.events`.
- `services\reentry-engine\src\2099900163260118_config.py` subscribes to `eafix.trades.results`; `services\event-gateway\src\2099900138260118_config.py` defines `eafix.trade.results`.
- `services\reentry-matrix-svc\src\2099900172260118_config.py` writes to `.\data\reentry`; `services\transport-router\src\2099900197260118_config.py` watches `.\data\reentry-matrix`.
- `contracts\models\2099900016260118_csv_models.py` and `contracts\models\2099900019260118___init__.py` assume unprefixed module names (`csv_models`, `event_models`, `json_models`) that are not present in the current tree.

## SECTION 2 - EVIDENCE TABLE

| Step ID | Step Name | Confirmed Owner | entrypoint_files | status | Key identifiers generated | Key identifiers consumed | Confirmed stores used | Evidence note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | Resolve service-local config snapshot | Service-local `Settings` classes | `services\calendar-ingestor\src\2099900089260118_config.py`<br>`services\data-ingestor\src\2099900109260118_config.py`<br>`services\reentry-engine\src\2099900163260118_config.py`<br>`services\reentry-matrix-svc\src\2099900172260118_config.py`<br>`services\transport-router\src\2099900197260118_config.py`<br>`services\telemetry-daemon\src\2099900190260118_config.py`<br>`services\event-gateway\src\2099900138260118_config.py` | implemented | none | none | env /.env only | No global config service; per-service settings only |
| S02 | Bootstrap runtime and scheduler context | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | none | none | none | Runtime order exists in docs only; tests start services individually |
| S03 | Poll calendar source(s) | `CalendarIngestor.fetch_events` | `services\calendar-ingestor\src\2099900092260118_ingestor.py` | planned | none | none | none | Method exists but returns `[]` |
| S04 | Normalize calendar event context and derive `calendar_id` | `CalendarIngestor.process_calendar_event` | `services\calendar-ingestor\src\2099900092260118_ingestor.py` | implemented | `calendar_id` | none | in-memory `active_signals` candidate list | Derives `calendar_id`, proximity, bias, confidence, symbol applicability |
| S05 | Validate and persist `active_calendar_signals` CSV | `CalendarIngestor.process_calendar_event` + `_write_signals_to_csv` | `services\calendar-ingestor\src\2099900092260118_ingestor.py` | implemented | `file_seq`, `checksum_sha256`, `timestamp` | `calendar_id` | `.\data\calendar\active_calendar_signals_*.csv` | Source writes atomically, but current proximity tokens conflict with CSV contract |
| S05a | Publish calendar event summary | `CalendarIngestor._publish_calendar_event` | `services\calendar-ingestor\src\2099900092260118_ingestor.py` | implemented | none | `calendar_id` | Redis pub/sub channel `calendar_events` | Publishes stringified event data, not the event-gateway topic contract |
| S06 | Build active trigger set and symbol filter | `CalendarIngestor.process_calendar_event` | `services\calendar-ingestor\src\2099900092260118_ingestor.py` | implemented | `anticipation_event` flag | `calendar_id` | in-memory `active_signals` | Filters unrelated symbols and skips `FAR` events |
| S07 | Ingest market ticks | `DataIngestor.process_price_tick` | `services\data-ingestor\src\2099900111260118_ingestor.py` | implemented | none | none | Redis pub/sub channel `price_ticks` | Normalization loop exists; adapter modules are missing from current tree |
| S08 | Compute indicators | `IndicatorEnginePlugin` | `services\indicator-engine\src\2099900159260118_plugin.py` | implemented | none | none | in-memory `price_buffer` | Plugin stub emits `indicator_update`; no standalone service main confirmed |
| S09 | Generate signal | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | UNKNOWN | UNKNOWN | UNKNOWN - data store not confirmed | Tests reference a plugin source file that is missing from the current tree |
| S10 | Assemble signal context | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | UNKNOWN | UNKNOWN | UNKNOWN - data store not confirmed | Canonical feature/signal packager exists in process docs, not in runtime source |
| S11 | Signal receipt (flow-orchestrator control plane) | `flow-orchestrator` (docs/tests only) | UNMAPPED - source not confirmed | planned | UNKNOWN | UNKNOWN | UNKNOWN - data store not confirmed | Current tracked `services\flow-orchestrator\src\*.py` files are deleted |
| S12 | Calendar gate check | `flow-orchestrator` (docs/tests only) | UNMAPPED - source not confirmed | planned | none | `calendar_id` or active calendar context | UNKNOWN - data store not confirmed | Docs require this gate; no runtime source confirms it |
| S13 | Reentry state check | `flow-orchestrator` (docs/tests only) | UNMAPPED - source not confirmed | planned | none | `hybrid_id` / prior chain state | UNKNOWN - data store not confirmed | Current runtime only has post-close in-memory cooldown state in `reentry-engine` |
| S14 | Risk validation | `flow-orchestrator` target + `risk-manager` plugin | `services\risk-manager\src\2099900183260118_plugin.py` | planned | none | UNKNOWN | in-memory plugin fields only | Risk logic exists only as plugin subscription, not as HTTP control-plane service |
| S15 | Execution handoff | `flow-orchestrator` target + execution stub | `services\execution-engine\src\2099900144260118_plugin.py` | planned | UNKNOWN | UNKNOWN | none | Stub emits `order_executed`; no MT4 handoff confirmed |
| S15a | Decision audit log persistence | `compliance-monitor` (docs only) | UNMAPPED - source not confirmed | planned | `decision_id` UNKNOWN | `hybrid_id` UNKNOWN | UNKNOWN - data store not confirmed | Docs describe audit behavior; no source entrypoint exists |
| S16a | Decision serialization | `reentry-matrix-svc` / `reentry-engine` processors | `services\reentry-matrix-svc\src\2099900177260118_processor.py`<br>`services\reentry-engine\src\2099900169260118_processor.py` | implemented | none | `trade_id`, `hybrid_id` | in-memory row objects only | Current runtime serializes inside processors, not in `transport-router` |
| S16b | Transport selection | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | none | none | UNKNOWN - data store not confirmed | Socket/CSV selection exists in docs only |
| S16c | Socket send / CSV atomic write | `ReentryProcessor._write_reentry_decision_csv` and `TradeResultProcessor._write_reentry_decision_csv` | `services\reentry-matrix-svc\src\2099900177260118_processor.py`<br>`services\reentry-engine\src\2099900169260118_processor.py` | implemented | `file_seq`, `checksum_sha256`, `timestamp` | `hybrid_id`, `trade_id` | `.\data\reentry\reentry_decisions_*.csv`<br>`.\data\reentry-engine\reentry_decisions_*.csv` | CSV write path is implemented; socket send path is not |
| S16d | Adapter ack validation | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | none | `hybrid_id`, `file_seq`, `checksum_sha256` | UNKNOWN - data store not confirmed | No Python-side ack consumer exists in current source |
| S17a | EA external decision intake | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | none | `hybrid_id`, `file_seq`, `checksum_sha256` | planned `reentry_decisions.csv` or socket | HUEY_P docs describe it; checked-in EA source does not implement it |
| S17b | Broker order execution | `HUEY_P_EA_ExecutionEngine_8.mql4` | `HUEY_P_EA_ExecutionEngine_8.mql4` | implemented | broker ticket only | autonomous SMA crossover signal | broker-side MT4 order state only | Real EA executes orders, but not from Python decisions |
| S18a | Persist trade result artifact from EA | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | planned `file_seq`, planned `checksum_sha256`, planned `trade_id` | planned `hybrid_id` from comment | planned `trade_results_*.csv` or socket reply | Docs/contracts describe it; checked-in EA source does not |
| S18b | Trade result receipt and payload validation | `TransportRouterService` + `IntegrityValidator` | `services\transport-router\src\2099900199260118_main.py`<br>`services\transport-router\src\2099900203260118_validator.py` | implemented | none | `file_seq`, `checksum_sha256`, `trade_id` | source file itself only | Validates file if a `trade_results_*.csv` appears |
| S18c | `hybrid_id` match and continuity gate | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | none | `hybrid_id`, `file_seq` | UNKNOWN - data store not confirmed | No pending-order match source confirmed |
| S18d | Timeout / no-result path and normalization gate | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | none | UNKNOWN | UNKNOWN - data store not confirmed | No runtime timeout manager found |
| S19 | Normalize execution result into `TradeResult` | `TradeResultProcessor._validate_trade_result` | `services\reentry-engine\src\2099900169260118_processor.py` | implemented | temporary placeholder `file_seq`, `checksum_sha256`, `timestamp` | `trade_id`, `comment` | in-memory `TradeResult` object only | Source exists, but placeholder values violate the CSV model constraints |
| S20 | Outcome and duration classification | `TradeResultProcessor` | `services\reentry-engine\src\2099900169260118_processor.py` | implemented | `outcome_class`, `duration_class` | `profit_loss_pips`, `duration_minutes` | none | Produces `WIN/LOSS/BREAKEVEN` and `FLASH/QUICK/LONG/EXTENDED` |
| S21 | Hybrid outcome bucket resolution | `ReentryProcessor._map_outcome_to_token` | `services\reentry-matrix-svc\src\2099900177260118_processor.py` | implemented | `W1` / `L1` / `BE` token | `outcome_class` | none | No confirmed runtime derivation for `W2` or `L2` |
| S22 | Compute event proximity for reentry | `TradeResultProcessor._determine_proximity_state` | `services\reentry-engine\src\2099900169260118_processor.py` | implemented | `proximity_state` | trade open time | none | Heuristic by trade open hour, not by actual calendar join |
| S22a | Resolve `calendar_id` for closed trade | `TradeResultProcessor._get_associated_calendar_id` | `services\reentry-engine\src\2099900169260118_processor.py` | implemented | `calendar_id` | symbol, `profit_loss_pips` | none | Heuristic returns `CAL8_USD_UNKNOWN_H` or `NONE` |
| S22b | Derive next generation / carry prior `hybrid_id` | `TradeResultProcessor._extract_hybrid_id_from_comment` + `_determine_generation` | `services\reentry-engine\src\2099900169260118_processor.py` | implemented | `generation` | `hybrid_id` from trade comment | none | Comment must already contain a parseable hybrid ID |
| S23 | Parameter-set resolution / matrix lookup | `TieredParameterResolver.resolve_parameters` | `services\reentry-matrix-svc\src\2099900178260118_resolver.py`<br>`config\1199900002260118_parameter_sets.json` | implemented | `parameter_set_id`, `resolved_tier` | `calendar_id`, outcome, duration, proximity, symbol, generation | JSON file `config\1199900002260118_parameter_sets.json` | Hierarchy is `EXACT -> TIER1 -> TIER2 -> TIER3 -> GLOBAL` |
| S23a | Risk overlay / reentry eligibility application | `TradeResultProcessor._check_reentry_eligibility` | `services\reentry-engine\src\2099900169260118_processor.py` | implemented | skip reason only | `trade_id`, symbol | in-memory `symbol_cooldowns`, `daily_attempt_counts` | Only cooldown/manual-close/daily-attempt logic is confirmed |
| S24 | Compose `hybrid_id` and build reentry decision | `ReentryProcessor.process_reentry_decision` | `services\reentry-matrix-svc\src\2099900177260118_processor.py` | implemented | `hybrid_id`, `chain_position` | `trade_id`, `calendar_id`, `generation` | in-memory decision dict | No `decision_id` or `strategy_id` is generated here |
| S24a | Reentry decision CSV + Redis persistence | `ReentryProcessor._write_reentry_decision_csv` + `ReentryMatrixService._publish_reentry_decision` | `services\reentry-matrix-svc\src\2099900177260118_processor.py`<br>`services\reentry-matrix-svc\src\2099900174260118_main.py` | implemented | `file_seq`, `checksum_sha256`, `timestamp` | `hybrid_id`, `trade_id` | `.\data\reentry\reentry_decisions_*.csv`<br>Redis topic `eafix.reentry.decisions` | Output path conflicts with transport-router watch config; contract validator is also mismatched |
| S24b | Matrix lookup history persistence | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | planned | none | `parameter_set_id`, `resolved_tier`, `hybrid_id` | UNKNOWN - data store not confirmed | Runtime architecture doc mentions `mapping_audit`; current source does not |
| S24c | Chain history persistence | `TradeResultProcessor` partial in-memory tracking | `services\reentry-engine\src\2099900169260118_processor.py` | implemented | none | `trade_id`, `hybrid_id` | in-memory `recent_decisions`, `symbol_cooldowns`, `daily_attempt_counts` | No durable ledger confirmed |
| S25 | Reentry loop handoff to execution chain | `flow-orchestrator` target + current reentry emitters | UNMAPPED - source not confirmed | planned | none | `hybrid_id`, decision artifact | UNKNOWN - data store not confirmed | No confirmed runtime path reconnects reentry decision output back into MT4 execution |
| S26 | Health and monitoring emission | `HealthMetricsCollector`, `SystemHealthAggregator`, `AlertManager` | `services\telemetry-daemon\src\2099900189260118_collector.py`<br>`services\telemetry-daemon\src\2099900187260118_aggregator.py`<br>`services\telemetry-daemon\src\2099900188260118_alerting.py` | implemented | `file_seq`, `checksum_sha256`, `timestamp` | service names, health responses | `.\data\telemetry-daemon\health_metrics_*.csv`<br>Redis topics `eafix.telemetry.health`, `eafix.telemetry.alerts`<br>in-memory histories | Collector is real; aggregator uses simulated service data in several paths |
| S26a | Multi-symbol and portfolio coordination | UNMAPPED - source not confirmed | UNMAPPED - source not confirmed | conceptual | none | UNKNOWN | UNKNOWN - data store not confirmed | No confirmed portfolio state manager or cross-symbol scheduler exists |
| S26b | Manual override / emergency stop / risk-off suppression | legacy calendar system only | `services\calendar-ingestor\src\2099900096260118_python_calendar_system.py` | conceptual | none | none | none | Legacy file has `/api/emergency-stop`; current modular runtime has no confirmed equivalent |

## SECTION 3 - REVISED PROCESS DOCUMENT

Identifier flow notation used below:

- `G` = generated
- `C` = consumed
- `F` = forwarded
- `V` = validated
- `N/A` = not applicable in current source

### S01

- step_id: S01
- name: Resolve service-local config snapshot
- purpose: Load runtime configuration into each source-present service.
- owner: service-local `Settings` classes
- inputs: Environment variables, `.env`, hard-coded defaults
- outputs: Per-service configuration objects
- identifiers_generated: none
- identifiers_consumed: none
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: Pydantic field validation in each settings class
- persistence: none
- failure_branch: Detection point is service startup config parse; handling action is exception on invalid settings; halt/retry behavior is service start failure
- entrypoint_files: `services\calendar-ingestor\src\2099900089260118_config.py`; `services\data-ingestor\src\2099900109260118_config.py`; `services\reentry-engine\src\2099900163260118_config.py`; `services\reentry-matrix-svc\src\2099900172260118_config.py`; `services\transport-router\src\2099900197260118_config.py`; `services\telemetry-daemon\src\2099900190260118_config.py`; `services\event-gateway\src\2099900138260118_config.py`
- status: implemented
- notes: The canonical `Resolve configuration snapshot` step exists only as per-service config loading. A single immutable global snapshot or snapshot hash is UNMAPPED - source not confirmed.

### S02

- step_id: S02
- name: Bootstrap runtime and scheduler context
- purpose: Establish process start order, service readiness, and polling cadence.
- owner: UNMAPPED - source not confirmed
- inputs: Service binaries, config, operator startup
- outputs: Running services with independent lifespans
- identifiers_generated: none
- identifiers_consumed: none
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: Integration tests poll `/healthz`; docs define a startup order
- persistence: none
- failure_branch: Detection point is startup health failure; handling action is test harness timeout or manual operator action; halt/retry behavior is test/process stop
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: `docs\techspec\0110000066260118_02_runtime_architecture.md` defines the intended startup order. `tests\integration\2099900241260118_conftest.py` starts services individually and even tests reverse-order startup. No source confirms a live bootstrap orchestrator.

### S03

- step_id: S03
- name: Poll calendar source(s)
- purpose: Fetch raw economic calendar events from configured upstream sources.
- owner: `CalendarIngestor.fetch_events`
- inputs: `calendar_sources`, `data_source`, update cadence
- outputs: Raw event list
- identifiers_generated: none
- identifiers_consumed: none
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: none confirmed in current source
- persistence: none
- failure_branch: Detection point is source fetch; handling action is UNDEFINED - source behavior not specified; halt/retry behavior is UNDEFINED - source behavior not specified
- entrypoint_files: `services\calendar-ingestor\src\2099900092260118_ingestor.py`
- status: planned
- notes: `fetch_events()` currently returns an empty list. Source polling is therefore not implemented even though the service has source configuration for it.

### S04

- step_id: S04
- name: Normalize calendar event context and derive `calendar_id`
- purpose: Convert an input event into source-level calendar context suitable for signal generation.
- owner: `CalendarIngestor.process_calendar_event`
- inputs: Manual event dict OR future S03 output
- outputs: `calendar_id`, `proximity_state`, `direction_bias`, `confidence_score`, symbol-scoped signal candidates
- identifiers_generated: `calendar_id`
- identifiers_consumed: none
- identifier_flow: `strategy_id=N/A (legacy-only elsewhere)`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: `datetime.fromisoformat(...)`; event currency must appear in the candidate symbol; `FAR` events are skipped
- persistence: in-memory signal candidate list before CSV validation
- failure_branch: Detection point is event parse or candidate generation; handling action is exception logging and event rejection; halt/retry behavior is UNDEFINED - source behavior not specified
- entrypoint_files: `services\calendar-ingestor\src\2099900092260118_ingestor.py`
- status: implemented
- notes: The actual identifier generated here is `calendar_id`. No current modular runtime source generates `strategy_id` here. `strategy_id` appears only in legacy calendar/downloader files.

### S05

- step_id: S05
- name: Validate and persist `active_calendar_signals` CSV
- purpose: Validate symbol-scoped calendar signals against the CSV contract and write the artifact atomically.
- owner: `CalendarIngestor.process_calendar_event` and `CalendarIngestor._write_signals_to_csv`
- inputs: S04 signal candidates
- outputs: `active_calendar_signals_YYYYMMDD_HHMMSS.csv`
- identifiers_generated: `file_seq`, `checksum_sha256`, `timestamp`
- identifiers_consumed: `calendar_id` from S04
- identifier_flow: `strategy_id=N/A (UNMAPPED in current modular runtime)`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=G`; `checksum_sha256=G+V`
- validations: SHA-256 row checksum generation; attempted `ActiveCalendarSignal` Pydantic validation
- persistence: `.\data\calendar\active_calendar_signals_*.csv`
- failure_branch: Detection point is contract validation or file write; handling action is log-and-continue on row validation failure, exception on file write failure; halt/retry behavior is no row retry and write retry is UNDEFINED - source behavior not specified
- entrypoint_files: `services\calendar-ingestor\src\2099900092260118_ingestor.py`
- status: implemented
- notes: Current source is blocked by a direct contract mismatch. The ingestor emits `PRE_1H`, `AT_EVENT`, `POST_30M`, but `contracts\models\2099900016260118_csv_models.py` defines `ActiveCalendarSignal.proximity_state` as `IMMEDIATE`, `NEAR`, `FAR`. The source attempts validation anyway.

### S05a

- step_id: S05a
- name: Publish calendar event summary to Redis
- purpose: Emit a Redis-side notification that calendar signals were generated.
- owner: `CalendarIngestor._publish_calendar_event`
- inputs: Source event dict and generated signal rows
- outputs: Stringified event payload on Redis
- identifiers_generated: none
- identifiers_consumed: `calendar_id` from S04
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=F from S05`; `checksum_sha256=F from S05`
- validations: none beyond publish success/failure
- persistence: Redis pub/sub channel `calendar_events`
- failure_branch: Detection point is Redis publish exception; handling action is warning log; halt/retry behavior is continue without publish
- entrypoint_files: `services\calendar-ingestor\src\2099900092260118_ingestor.py`
- status: implemented
- notes: The emitted channel is `calendar_events`, which conflicts with the event-gateway configuration topic `eafix.calendar.events`.

### S06

- step_id: S06
- name: Build active trigger set and symbol filter
- purpose: Derive symbol-scoped trigger candidates and maintain current active signal state.
- owner: `CalendarIngestor.process_calendar_event`
- inputs: S04 calendar context plus `currency_pairs`
- outputs: Symbol-filtered trigger rows with `anticipation_event`
- identifiers_generated: none
- identifiers_consumed: `calendar_id` from S04
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=F to S05`; `checksum_sha256=F to S05`
- validations: event currency must appear in the symbol; only non-`FAR` events continue
- persistence: in-memory `CalendarIngestor.active_signals`
- failure_branch: Detection point is candidate validation per symbol; handling action is skip invalid symbols/rows; halt/retry behavior is continue
- entrypoint_files: `services\calendar-ingestor\src\2099900092260118_ingestor.py`
- status: implemented
- notes: This is the closest source-confirmed equivalent to the canonical trigger-builder step. No append-only calendar event store is confirmed in the active modular service path.

### S07

- step_id: S07
- name: Ingest market ticks
- purpose: Normalize raw price ticks and publish them into the runtime.
- owner: `DataIngestor.process_price_tick`
- inputs: Adapter-provided raw price data
- outputs: Normalized tick JSON
- identifiers_generated: none
- identifiers_consumed: none
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: symbol format; bid/ask positive; ask greater than bid; spread bounds
- persistence: Redis pub/sub channel `price_ticks`
- failure_branch: Detection point is normalization or schema validation; handling action is log-and-skip invalid ticks; halt/retry behavior is main loop continues with backoff on processor errors
- entrypoint_files: `services\data-ingestor\src\2099900111260118_ingestor.py`
- status: implemented
- notes: `services\data-ingestor\src\2099900111260118_ingestor.py` tries to import MT4, CSV, and socket adapters, but those adapter modules are absent in the current tree. The service can therefore start with zero active adapters.

### S08

- step_id: S08
- name: Compute indicators
- purpose: Turn recent price history into indicator outputs for signal generation.
- owner: `IndicatorEnginePlugin`
- inputs: `price_tick` events
- outputs: `indicator_update` events
- identifiers_generated: none
- identifiers_consumed: none
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: minimum price buffer length before emit
- persistence: in-memory `IndicatorEnginePlugin._price_buffer`
- failure_branch: Detection point is calculation loop exception; handling action is print error and sleep; halt/retry behavior is retry on next loop iteration
- entrypoint_files: `services\indicator-engine\src\2099900159260118_plugin.py`
- status: implemented
- notes: This is a plugin stub, not a confirmed standalone microservice runtime.

### S09

- step_id: S09
- name: Generate signal
- purpose: Turn indicator state into a directional trade signal.
- owner: UNMAPPED - source not confirmed
- inputs: Indicator outputs and strategy thresholds
- outputs: Signal dict OR suppression
- identifiers_generated: UNKNOWN
- identifiers_consumed: UNKNOWN
- identifier_flow: `strategy_id=UNMAPPED - source not confirmed`; `hybrid_id=N/A`; `decision_id=UNMAPPED - source not confirmed`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: UNKNOWN - source not confirmed
- persistence: UNKNOWN - data store not confirmed
- failure_branch: Detection point is UNMAPPED - source not confirmed; handling action is UNDEFINED - source behavior not specified; halt/retry behavior is UNDEFINED - source behavior not specified
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: Only `services\signal-generator\tests\2099900186260118_test_signal_generator_plugin.py` remains. The source file referenced by the tests is missing from the current tree.

### S10

- step_id: S10
- name: Assemble signal context
- purpose: Combine market signal state with calendar context before handing off to execution control.
- owner: UNMAPPED - source not confirmed
- inputs: S06 calendar trigger context and S09 signal output
- outputs: Signal context package
- identifiers_generated: UNKNOWN
- identifiers_consumed: UNKNOWN
- identifier_flow: `strategy_id=UNMAPPED - source not confirmed`; `hybrid_id=N/A`; `decision_id=UNMAPPED - source not confirmed`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: UNKNOWN - source not confirmed
- persistence: UNKNOWN - data store not confirmed
- failure_branch: Detection point is UNMAPPED - source not confirmed; handling action is UNDEFINED - source behavior not specified; halt/retry behavior is UNDEFINED - source behavior not specified
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: The canonical feature-packager and intent-builder chain is not source-confirmed in the current runtime tree.

### FLOW-ORCHESTRATOR CONTROL PLANE

Control-plane ownership required by the canonical process and docs:

- signal receipt
- calendar gate check
- reentry state check
- risk validation
- execution handoff

Current source status:

- planned
- tracked `flow-orchestrator` source files are deleted from the current tree
- tests and docs still assume the service exists on port `8093`

### S11

- step_id: S11
- name: Signal receipt
- purpose: Open a control-plane flow instance for a new signal context.
- owner: `flow-orchestrator` (docs/tests only)
- inputs: S10 signal context OR direct signal event
- outputs: Flow execution state
- identifiers_generated: UNKNOWN
- identifiers_consumed: UNKNOWN
- identifier_flow: `strategy_id=C from S10 if present, otherwise UNMAPPED`; `hybrid_id=N/A for original-entry path`; `decision_id=UNMAPPED - source not confirmed`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: UNKNOWN - source not confirmed
- persistence: UNKNOWN - data store not confirmed
- failure_branch: Detection point is service absence or flow creation error; handling action is test timeout or operator intervention; halt/retry behavior is UNDEFINED - source behavior not specified
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: `tests\integration\2099900241260118_conftest.py` and `tests\integration\2099900244260118_test_end_to_end_flows.py` assume `/orchestrator/flows/*` endpoints, but current runtime source is missing.

### S12

- step_id: S12
- name: Calendar gate check
- purpose: Suppress or allow execution based on current calendar state.
- owner: `flow-orchestrator` (docs/tests only)
- inputs: S11 flow state plus active calendar context
- outputs: Gate allow/deny decision
- identifiers_generated: none
- identifiers_consumed: `calendar_id` context if present
- identifier_flow: `strategy_id=F from S11 if present`; `hybrid_id=N/A`; `decision_id=UNMAPPED`; `file_seq=C from S05 if CSV path is used`; `checksum_sha256=V from S05 if CSV path is used`
- validations: stale scheduler/calendar freshness check is required by the requested process, but UNMAPPED - source not confirmed
- persistence: UNKNOWN - data store not confirmed
- failure_branch: Detection point is stale scheduler/calendar data; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: Runtime source offers `calendar_events` Redis publish and CSV artifact generation, but no confirmed control-plane consumer.

### S13

- step_id: S13
- name: Reentry state check
- purpose: Check whether the symbol/trade is already in a reentry chain or cooldown state.
- owner: `flow-orchestrator` (required by canonical flow; not source-confirmed)
- inputs: S11 flow state plus prior chain state
- outputs: Allow, suppress, or defer
- identifiers_generated: none
- identifiers_consumed: `hybrid_id` if prior chain exists
- identifier_flow: `strategy_id=F from S11 if present`; `hybrid_id=C from prior chain if present, otherwise N/A`; `decision_id=UNMAPPED`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: UNKNOWN - source not confirmed
- persistence: UNKNOWN - data store not confirmed
- failure_branch: Detection point is chain-state lookup failure; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: The only source-confirmed reentry state today is post-close in-memory cooldown tracking inside `services\reentry-engine\src\2099900169260118_processor.py`, not a signal-time control-plane state check.

### S14

- step_id: S14
- name: Risk validation
- purpose: Apply risk checks before execution handoff.
- owner: control-plane target `risk-manager`; source-level implementation only exists as plugin logic
- inputs: Signal or order candidate with confidence
- outputs: Approved or rejected candidate
- identifiers_generated: none
- identifiers_consumed: UNKNOWN
- identifier_flow: `strategy_id=C if caller provides it, otherwise UNMAPPED`; `hybrid_id=N/A on original-entry path`; `decision_id=UNMAPPED`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: daily loss limit; drawdown limit; confidence-based size calculation
- persistence: in-memory plugin fields only
- failure_branch: Detection point is failed risk check; handling action is emit `order_rejected`; halt/retry behavior is halt for that signal
- entrypoint_files: `services\risk-manager\src\2099900183260118_plugin.py`
- status: planned
- notes: The logic exists, but not in the documented synchronous `flow-orchestrator -> risk-manager` service call shape. No HTTP risk API is source-confirmed.

### S15

- step_id: S15
- name: Execution handoff
- purpose: Convert an approved signal into an execution-ready handoff.
- owner: control-plane target `execution-engine`; current source contains only a plugin stub
- inputs: Risk-approved order candidate
- outputs: Execution request / stub `order_executed`
- identifiers_generated: UNKNOWN
- identifiers_consumed: UNKNOWN
- identifier_flow: `strategy_id=F if caller provided it`; `hybrid_id=N/A or future-generated`; `decision_id=UNMAPPED - source not confirmed`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: none beyond plugin execution stub path
- persistence: none
- failure_branch: Detection point is execution stub exception; handling action is emit `order_rejected`; halt/retry behavior is halt for that request
- entrypoint_files: `services\execution-engine\src\2099900144260118_plugin.py`
- status: planned
- notes: No source-confirmed MT4 bridge handoff exists in `execution-engine`.

### S15a

- step_id: S15a
- name: Decision audit log persistence
- purpose: Persist an audit record for the pre-execution decision.
- owner: `compliance-monitor` (docs only)
- inputs: S15 handoff candidate
- outputs: Audit record
- identifiers_generated: `decision_id` UNKNOWN
- identifiers_consumed: `hybrid_id` UNKNOWN
- identifier_flow: `strategy_id=C if present`; `hybrid_id=C if present`; `decision_id=G UNKNOWN`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: UNKNOWN - source not confirmed
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is audit write failure; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: The trade-placement docs describe audit behavior, but no compliance-monitor runtime source is present in the current tree.

### S16a

- step_id: S16a
- name: Decision serialization
- purpose: Materialize a decision object into CSV row fields for MT4 transport.
- owner: `ReentryProcessor.process_reentry_decision` and `TradeResultProcessor._write_reentry_decision_csv`
- inputs: Decision dict with `trade_id`, `hybrid_id`, action, sizing, SL/TP
- outputs: Row-level decision payload
- identifiers_generated: none
- identifiers_consumed: `trade_id`, `hybrid_id`
- identifier_flow: `strategy_id=N/A (UNMAPPED in current modular runtime)`; `hybrid_id=C`; `decision_id=N/A (UNMAPPED)`; `file_seq=generated later in S16c`; `checksum_sha256=generated later in S16c`
- validations: Attempts `ReentryDecision` Pydantic validation
- persistence: in-memory row object before file write
- failure_branch: Detection point is model construction/validation; handling action is exception and error log; halt/retry behavior is halt for that decision
- entrypoint_files: `services\reentry-matrix-svc\src\2099900177260118_processor.py`; `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: The current runtime serializes in the processors. `transport-router` validates and routes files after creation; it does not create the decision artifact.

### S16b

- step_id: S16b
- name: Transport selection
- purpose: Select CSV or socket delivery for the MT4 bridge.
- owner: UNMAPPED - source not confirmed
- inputs: S16a serialized decision and transport health
- outputs: Selected transport mode
- identifiers_generated: none
- identifiers_consumed: `hybrid_id`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C from S16a`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: planned socket health / heartbeat logic only
- persistence: UNKNOWN - data store not confirmed
- failure_branch: Detection point is socket disconnect; handling action is demote to CSV per docs; halt/retry behavior is retry/promotion after healthy window per docs only
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: `docs\techspec\0110000076260118_07_transport_bridge_contracts.md` and `0199900003260118_HUEY_P_EA_ExecutionEngine_8.md` define selection logic. Current `transport-router` source does not.

### S16c

- step_id: S16c
- name: Socket send / CSV atomic write
- purpose: Deliver the serialized decision artifact to the bridge layer.
- owner: current CSV path in `reentry-matrix-svc` and `reentry-engine`; socket path UNMAPPED
- inputs: S16a serialized decision
- outputs: CSV artifact OR planned socket payload
- identifiers_generated: `file_seq`, `checksum_sha256`, `timestamp`
- identifiers_consumed: `hybrid_id`, `trade_id`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C+F from S16a`; `decision_id=N/A`; `file_seq=G`; `checksum_sha256=G+V`
- validations: `.tmp` file creation; header + row write; `flush`; `os.fsync`; atomic rename; checksum verification before write
- persistence: `.\data\reentry\reentry_decisions_*.csv`; `.\data\reentry-engine\reentry_decisions_*.csv`
- failure_branch: Detection point is checksum verification failure or file I/O error; handling action is error log and exception; halt/retry behavior is halt for that decision write, retry UNDEFINED - not specified in source
- entrypoint_files: `services\reentry-matrix-svc\src\2099900177260118_processor.py`; `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: The requested CSV requirements are source-confirmed here: `.tmp` write, atomic rename, `file_seq`, `checksum_sha256`, `hybrid_id`, and `timestamp`. Socket delivery is not source-confirmed. `transport-router` watches `.\data\reentry-matrix`, but `reentry-matrix-svc` writes to `.\data\reentry`.

### S16d

- step_id: S16d
- name: Adapter ack validation
- purpose: Confirm that the MT4 bridge accepted the decision artifact.
- owner: UNMAPPED - source not confirmed
- inputs: Planned adapter ack OR EA-side successful read
- outputs: Acked / not-acked status
- identifiers_generated: none
- identifiers_consumed: `hybrid_id`, `file_seq`, `checksum_sha256`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C from S16c`; `decision_id=N/A`; `file_seq=C+V from S16c`; `checksum_sha256=C+V from S16c`
- validations: planned heartbeat, ack semantics, retry/fail behavior only
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is missing ack or heartbeat loss; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: No current Python source validates an MT4 adapter ack. This entire step remains documentary.

### S17a

- step_id: S17a
- name: EA external decision intake
- purpose: Accept a Python-produced execution decision inside the MT4 bridge or EA runtime.
- owner: `UNMAPPED - source not confirmed`
- inputs: S16d acked decision artifact or S16c CSV payload
- outputs: EA-local order candidate
- identifiers_generated: none
- identifiers_consumed: `hybrid_id`, `file_seq`, `checksum_sha256`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C+V from S16c`; `decision_id=N/A`; `file_seq=C+V from S16c`; `checksum_sha256=C+V from S16c`
- validations: Planned CSV/socket field parse, integrity checks, and bridge-side acceptance only
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is planned adapter-side checksum mismatch or sequence gap; handling action is reject artifact before broker submission per docs only; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: `0199900003260118_HUEY_P_EA_ExecutionEngine_8.md` describes this step. The checked-in EA source does not implement it.

### S17b

- step_id: S17b
- name: Broker order execution
- purpose: Submit trade orders to the broker inside MT4.
- owner: `HUEY_P_EA_ExecutionEngine_8.mql4`
- inputs: Autonomous SMA crossover conditions inside the EA
- outputs: MT4 broker ticket or rejected order
- identifiers_generated: broker ticket only
- identifiers_consumed: autonomous SMA crossover signal only
- identifier_flow: `strategy_id=UNMAPPED - source not confirmed`; `hybrid_id=UNMAPPED - external decision intake not implemented in checked-in EA`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: SMA crossover condition check and MT4 `OrderSend` return-code check
- persistence: broker-side MT4 open/closed order state only
- failure_branch: Detection point is broker rejection when `OrderSend(...) < 0`; handling action is `Print("OrderSend ... failed", GetLastError())`; halt/retry behavior is halt for that tick/signal in the checked-in EA
- entrypoint_files: `HUEY_P_EA_ExecutionEngine_8.mql4`
- status: implemented
- notes: Real broker execution is source-confirmed, but it is not driven by Python decision artifacts. The checked-in EA comments orders as `SMA Crossover Buy` / `SMA Crossover Sell`, not with `hybrid_id`.

### POST-EA INGESTION BLOCK

### S18a

- step_id: S18a
- name: Persist trade result artifact from EA
- purpose: Materialize an execution result for downstream Python ingestion.
- owner: `UNMAPPED - source not confirmed`
- inputs: Broker execution/close state from S17b
- outputs: Planned result artifact for Python-side ingestion
- identifiers_generated: planned `file_seq`, planned `checksum_sha256`, planned `trade_id`
- identifiers_consumed: planned `hybrid_id` from order comment
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C from MT4 comment if present`; `decision_id=N/A`; `file_seq=G planned`; `checksum_sha256=G planned`
- validations: Docs/contracts imply atomic CSV or socket reply, but runtime behavior is `UNMAPPED - source not confirmed`
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is result-artifact write or response-send failure; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: `contracts\models\2099900016260118_csv_models.py` defines `TradeResult`, and `transport-router` can validate `trade_results_*.csv` if it appears, but the checked-in EA does not emit this artifact.

### S18b

- step_id: S18b
- name: Trade result receipt and payload validation
- purpose: Receive a result artifact and validate it before normalization.
- owner: `TransportRouterService` + `IntegrityValidator`
- inputs: `trade_results_*.csv` file if one appears in a watched directory
- outputs: Validation result and routed file payload
- identifiers_generated: none
- identifiers_consumed: `file_seq`, `checksum_sha256`, `trade_id`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=UNMAPPED - source not confirmed`; `decision_id=N/A`; `file_seq=C+V`; `checksum_sha256=C+V`
- validations: Header check, contract-schema check, SHA-256 checksum validation, and sequence validation
- persistence: source CSV file on disk plus in-memory validation cache
- failure_branch: Detection point is checksum mismatch in `IntegrityValidator`; handling action is validation failure plus error log; halt/retry behavior is halt for routing of that file. Detection point is sequence gap; handling action is warning only; halt/retry behavior is continue because the validator marks sequence issues as warnings, not hard failures
- entrypoint_files: `services\transport-router\src\2099900199260118_main.py`; `services\transport-router\src\2099900203260118_validator.py`
- status: implemented
- notes: This step is source-confirmed only as a file watcher/validator. No checked-in producer creates a `trade_results_*.csv` in the current runtime.

### S18c

- step_id: S18c
- name: `hybrid_id` match and continuity gate
- purpose: Correlate an execution result back to the originating decision before downstream classification.
- owner: `UNMAPPED - source not confirmed`
- inputs: S16c decision context and S18b validated result payload
- outputs: Matched result or rejected mismatch
- identifiers_generated: none
- identifiers_consumed: `hybrid_id`, `file_seq`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C+V from decision context and result comment/payload if present`; `decision_id=N/A`; `file_seq=C+V from S16c and S18b`; `checksum_sha256=F from S18b`
- validations: Planned `hybrid_id` match, file-sequence continuity, and pending-order correlation
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is `hybrid_id` mismatch or sequence discontinuity; handling action is block normalization; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: No source-confirmed pending-order registry or decision/result correlator exists in the current runtime.

### S18d

- step_id: S18d
- name: Timeout / no-result path and normalization gate
- purpose: Gate entry into normalization until result ingestion succeeds, or divert to a timeout path if it does not.
- owner: `UNMAPPED - source not confirmed`
- inputs: Pending execution context and elapsed time since S17b
- outputs: Permission to enter S19 or timeout/no-result branch
- identifiers_generated: none
- identifiers_consumed: UNKNOWN
- identifier_flow: `strategy_id=UNKNOWN`; `hybrid_id=UNKNOWN`; `decision_id=UNKNOWN`; `file_seq=UNKNOWN`; `checksum_sha256=UNKNOWN`
- validations: Planned timeout threshold and success-before-normalization gate only
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is no result before timeout; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: No runtime timeout manager or no-result recovery path was found in the current source tree.

### S19

- step_id: S19
- name: Normalize execution result into `TradeResult`
- purpose: Coerce inbound result payloads into the canonical result contract used by the reentry engine.
- owner: `TradeResultProcessor._validate_trade_result`
- inputs: Trade result payload dict
- outputs: In-memory `TradeResult` object
- identifiers_generated: placeholder `file_seq`, placeholder `checksum_sha256`, placeholder `timestamp`
- identifiers_consumed: `trade_id`, `comment`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=UNMAPPED at this step; extracted later from comment in S22b`; `decision_id=N/A`; `file_seq=G placeholder`; `checksum_sha256=G placeholder`
- validations: Attempts Pydantic `TradeResult` validation
- persistence: in-memory `TradeResult` object only
- failure_branch: Detection point is model-construction or validation failure; handling action is exception plus error logging; halt/retry behavior is halt for that payload
- entrypoint_files: `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: Source exists, but it currently injects `file_seq=0` and `checksum_sha256="placeholder"` before validation. Those placeholder values violate the CSV model constraints.

### S20

- step_id: S20
- name: Outcome and duration classification
- purpose: Derive reentry-driving outcome and duration classes from the normalized result.
- owner: `TradeResultProcessor`
- inputs: S19 normalized `TradeResult`
- outputs: `outcome_class`, `duration_class`
- identifiers_generated: `outcome_class`, `duration_class`
- identifiers_consumed: `profit_loss_pips`, `duration_minutes`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=F from S19 payload context if present`; `decision_id=N/A`; `file_seq=F from S19`; `checksum_sha256=F from S19`
- validations: Threshold-based classification into `WIN` / `LOSS` / `BREAKEVEN` and `FLASH` / `QUICK` / `LONG` / `EXTENDED`
- persistence: none
- failure_branch: Detection point is missing numeric result fields; handling action is exception via upstream normalization/classification path; halt/retry behavior is halt for that payload
- entrypoint_files: `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: This step is implemented and materially drives the downstream matrix request.

### S21

- step_id: S21
- name: Hybrid outcome bucket resolution
- purpose: Convert outcome class into the vocabulary token used by `hybrid_id` composition.
- owner: `ReentryProcessor._map_outcome_to_token`
- inputs: `outcome_class`
- outputs: Outcome token such as `W1`, `L1`, or `BE`
- identifiers_generated: outcome token
- identifiers_consumed: `outcome_class`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A until S24`; `decision_id=N/A`; `file_seq=UNMAPPED - source not confirmed`; `checksum_sha256=UNMAPPED - source not confirmed`
- validations: Mapping table lookup only
- persistence: none
- failure_branch: Detection point is unsupported or missing `outcome_class`; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `services\reentry-matrix-svc\src\2099900177260118_processor.py`
- status: implemented
- notes: Current runtime maps `WIN -> W1`, `LOSS -> L1`, `BREAKEVEN -> BE`. No source-confirmed refinement to `W2` or `L2` exists.

### S22

- step_id: S22
- name: Compute event proximity for reentry
- purpose: Derive a proximity bucket for matrix lookup.
- owner: `TradeResultProcessor._determine_proximity_state`
- inputs: S19 normalized trade result
- outputs: `proximity_state`
- identifiers_generated: `proximity_state`
- identifiers_consumed: trade open time
- identifier_flow: `strategy_id=N/A`; `hybrid_id=F if existing comment context is preserved`; `decision_id=N/A`; `file_seq=F from S19`; `checksum_sha256=F from S19`
- validations: Time-of-day heuristic only
- persistence: none
- failure_branch: Detection point is missing trade-open timestamp; handling action is exception via processor path; halt/retry behavior is halt for that payload
- entrypoint_files: `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: This is not a real calendar join. The code comments explicitly say the production version would query a calendar service.

### S22a

- step_id: S22a
- name: Resolve `calendar_id` for closed trade
- purpose: Associate the closed trade with a calendar bucket for matrix lookup.
- owner: `TradeResultProcessor._get_associated_calendar_id`
- inputs: S19 normalized trade result
- outputs: `calendar_id`
- identifiers_generated: `calendar_id`
- identifiers_consumed: symbol and trade characteristics
- identifier_flow: `strategy_id=N/A`; `hybrid_id=F if existing comment context is preserved`; `decision_id=N/A`; `file_seq=F from S19`; `checksum_sha256=F from S19`
- validations: Heuristic-only association
- persistence: none
- failure_branch: Detection point is inability to infer a calendar association; handling action is return fallback value such as `NONE`; halt/retry behavior is continue with fallback
- entrypoint_files: `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: The function comments state it would query a calendar service in a fuller implementation. Current source returns heuristic values such as `CAL8_USD_UNKNOWN_H` or `NONE`.

### S22b

- step_id: S22b
- name: Derive next generation / carry prior `hybrid_id`
- purpose: Recover prior chain identity from the trade comment and compute the next generation number.
- owner: `TradeResultProcessor._extract_hybrid_id_from_comment` + `_determine_generation`
- inputs: S19 normalized trade result comment
- outputs: existing `hybrid_id` carry-forward candidate and `generation`
- identifiers_generated: `generation`
- identifiers_consumed: `hybrid_id` from trade comment
- identifier_flow: `strategy_id=UNMAPPED - source not confirmed`; `hybrid_id=C+F from trade comment`; `decision_id=N/A`; `file_seq=F from S19`; `checksum_sha256=F from S19`
- validations: Simplified underscore-split parse of the trade comment
- persistence: none
- failure_branch: Detection point is missing or unparseable `hybrid_id` in comment; handling action is `generation=1` fallback when no valid prior ID is recovered; halt/retry behavior is continue as a first-generation path
- entrypoint_files: `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: The current extractor is explicitly marked as simplified. It splits the entire comment on `_`, which is fragile against comment formats not dedicated to `hybrid_id`.

### S23

- step_id: S23
- name: Parameter-set resolution / matrix lookup
- purpose: Resolve reentry parameters from the tiered parameter matrix.
- owner: `TieredParameterResolver.resolve_parameters`
- inputs: `calendar_id`, outcome, duration, proximity, symbol, generation
- outputs: `parameter_set_id`, `resolved_tier`, resolved sizing/SL/TP inputs
- identifiers_generated: `parameter_set_id`, `resolved_tier`
- identifiers_consumed: `calendar_id`, outcome, duration, proximity, symbol, generation
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A until S24`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: Tiered lookup across `EXACT -> TIER1 -> TIER2 -> TIER3 -> GLOBAL`
- persistence: JSON file `config\1199900002260118_parameter_sets.json`
- failure_branch: Detection point is parameter-resolution failure; handling action is exception/error path in processor; halt/retry behavior is halt for that request
- entrypoint_files: `services\reentry-matrix-svc\src\2099900178260118_resolver.py`; `config\1199900002260118_parameter_sets.json`
- status: implemented
- notes: This is one of the clearer implemented parts of the current reentry path.

### S23a

- step_id: S23a
- name: Risk overlay / reentry eligibility application
- purpose: Apply the source-confirmed reentry suppressions before or during matrix invocation.
- owner: `TradeResultProcessor._check_reentry_eligibility`
- inputs: S19 normalized result and processor-local state
- outputs: eligible / ineligible result plus skip reason
- identifiers_generated: skip reason only
- identifiers_consumed: `trade_id`, `symbol`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=F from S22b if present`; `decision_id=N/A`; `file_seq=F from S19`; `checksum_sha256=F from S19`
- validations: completed-trade check, minimum-duration check, manual-close exclusion, cooldown check, and daily-attempt limit
- persistence: in-memory `symbol_cooldowns` and `daily_attempt_counts`
- failure_branch: Detection point is failed eligibility rule; handling action is skip reentry and log `reason`; halt/retry behavior is halt for that trade result
- entrypoint_files: `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: This is the only source-confirmed risk overlay on the reentry path. It is not the broader portfolio risk layer described in architectural docs.

### S24

- step_id: S24
- name: Compose `hybrid_id` and build reentry decision
- purpose: Produce the reentry decision payload that can be persisted and forwarded.
- owner: `ReentryProcessor.process_reentry_decision`
- inputs: S21 outcome token, S22 proximity, S22a `calendar_id`, S22b generation, S23 resolved parameters
- outputs: In-memory reentry decision dict
- identifiers_generated: `hybrid_id`, `chain_position`
- identifiers_consumed: `trade_id`, `calendar_id`, `generation`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=G`; `decision_id=UNMAPPED - source not confirmed`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: `shared.reentry.compose()` plus `validate_key()` on the composed ID
- persistence: in-memory decision dict only
- failure_branch: Detection point is `hybrid_id` composition failure; handling action is error log and manual string-composition fallback; halt/retry behavior is continue with fallback string in current source
- entrypoint_files: `services\reentry-matrix-svc\src\2099900177260118_processor.py`; `shared\reentry\2099900218260118_hybrid_id.py`
- status: implemented
- notes: No `strategy_id` or `decision_id` is generated here. The fallback manual composition still uses underscore-delimited IDs.

### S24a

- step_id: S24a
- name: Reentry decision CSV + Redis persistence
- purpose: Persist the reentry decision artifact and publish it for downstream consumption.
- owner: `ReentryProcessor._write_reentry_decision_csv` + `ReentryMatrixService._publish_reentry_decision`
- inputs: S24 decision dict
- outputs: CSV artifact and Redis publication
- identifiers_generated: `file_seq`, `checksum_sha256`, `timestamp`
- identifiers_consumed: `hybrid_id`, `trade_id`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C+F from S24`; `decision_id=UNMAPPED - source not confirmed`; `file_seq=G`; `checksum_sha256=G+V`
- validations: Attempts `ReentryDecision` contract validation; performs atomic CSV write when enabled
- persistence: `.\data\reentry\reentry_decisions_*.csv`; Redis topic `eafix.reentry.decisions`
- failure_branch: Detection point is contract-validation, CSV-write, or Redis-publish failure; handling action is exception plus error logging; halt/retry behavior is halt for that decision write/publish attempt
- entrypoint_files: `services\reentry-matrix-svc\src\2099900177260118_processor.py`; `services\reentry-matrix-svc\src\2099900174260118_main.py`
- status: implemented
- notes: The current `ReentryDecision.hybrid_id` validator is incompatible with underscore-bearing IDs, so the source-confirmed write path is present but contract-broken. Output location also conflicts with `transport-router` watch configuration.

### S24b

- step_id: S24b
- name: Matrix lookup history persistence
- purpose: Persist an audit trail of parameter resolution decisions.
- owner: `UNMAPPED - source not confirmed`
- inputs: `parameter_set_id`, `resolved_tier`, `hybrid_id`
- outputs: Lookup-history record
- identifiers_generated: none
- identifiers_consumed: `parameter_set_id`, `resolved_tier`, `hybrid_id`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C from S24`; `decision_id=UNMAPPED - source not confirmed`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: UNKNOWN - source not confirmed
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is audit-write failure; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: Runtime-architecture docs mention mapping audit behavior, but no current runtime file persists it.

### S24c

- step_id: S24c
- name: Chain history persistence
- purpose: Track chain-local cooldown and recent decision history.
- owner: `TradeResultProcessor` partial in-memory tracking
- inputs: `trade_id`, `hybrid_id`, `symbol`
- outputs: Updated in-memory chain/cooldown state
- identifiers_generated: none
- identifiers_consumed: `trade_id`, `hybrid_id`
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C from S22b and S24`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: Cooldown and daily-attempt accounting only
- persistence: in-memory `recent_decisions`, `symbol_cooldowns`, `daily_attempt_counts`
- failure_branch: Detection point is process restart or memory loss; handling action is no durable recovery in current source; halt/retry behavior is continue with empty in-memory state after restart
- entrypoint_files: `services\reentry-engine\src\2099900169260118_processor.py`
- status: implemented
- notes: No durable ledger or append-only chain history store is confirmed.

### S25

- step_id: S25
- name: Reentry loop handoff to execution chain
- purpose: Feed a reentry decision back into the execution path.
- owner: `flow-orchestrator` target + current reentry emitters
- inputs: S24a persisted/published reentry decision
- outputs: Planned reentry execution restart or dead-end artifact
- identifiers_generated: none
- identifiers_consumed: `hybrid_id`, decision artifact
- identifier_flow: `strategy_id=N/A`; `hybrid_id=C+F from S24a`; `decision_id=UNMAPPED - source not confirmed`; `file_seq=C from S24a`; `checksum_sha256=C from S24a`
- validations: No confirmed downstream consumer validates or accepts the emitted reentry decision in the current runtime
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is no downstream consumer, watch-path mismatch, or absent orchestrator; handling action is leave artifact on disk / Redis only; halt/retry behavior is halt because no source-confirmed reconnect path exists
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: planned
- notes: No current source-confirmed runtime path reconnects `reentry-matrix-svc` output back into MT4 execution.

### S26

- step_id: S26
- name: Health and monitoring emission
- purpose: Emit service health, routing health, and alert telemetry for the runtime.
- owner: `HealthMetricsCollector`, `SystemHealthAggregator`, `AlertManager`
- inputs: Service names, health responses, collector metrics, routing/processing state
- outputs: Health metrics CSV, Redis health events, Redis alert events
- identifiers_generated: `file_seq`, `checksum_sha256`, `timestamp`
- identifiers_consumed: service names and health responses
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=G`; `checksum_sha256=G+V`
- validations: Health-response parsing, threshold evaluation, and alert-rule checks
- persistence: `.\data\telemetry-daemon\health_metrics_*.csv`; Redis topics `eafix.telemetry.health`, `eafix.telemetry.alerts`; in-memory histories
- failure_branch: Detection point is collection or publish exception; handling action is log warning/error and continue next interval; halt/retry behavior is retry on next collection cycle
- entrypoint_files: `services\telemetry-daemon\src\2099900189260118_collector.py`; `services\telemetry-daemon\src\2099900187260118_aggregator.py`; `services\telemetry-daemon\src\2099900188260118_alerting.py`
- status: implemented
- notes: Telemetry emission is source-present, but the aggregator uses simulated service data in several paths.

### S26a

- step_id: S26a
- name: Multi-symbol and portfolio coordination
- purpose: Coordinate trading and reentry decisions across multiple symbols and shared portfolio limits.
- owner: `UNMAPPED - source not confirmed`
- inputs: Portfolio-wide exposures, symbol states, and concurrent trade intents
- outputs: Coordinated allow/suppress decisions
- identifiers_generated: none
- identifiers_consumed: UNKNOWN
- identifier_flow: `strategy_id=UNKNOWN`; `hybrid_id=UNKNOWN`; `decision_id=UNKNOWN`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: UNKNOWN - source not confirmed
- persistence: `UNKNOWN - data store not confirmed`
- failure_branch: Detection point is portfolio-level conflict or cross-symbol limit breach; handling action is UNDEFINED - not specified in source; halt/retry behavior is UNDEFINED - not specified in source
- entrypoint_files: `UNMAPPED - source not confirmed`
- status: conceptual
- notes: No confirmed portfolio state manager, cross-symbol scheduler, or shared exposure store exists in the modular runtime.

### S26b

- step_id: S26b
- name: Manual override / emergency stop / risk-off suppression
- purpose: Provide operator-driven suppression or emergency stop controls.
- owner: legacy calendar system only
- inputs: Operator/API command
- outputs: Suppression or emergency-stop state
- identifiers_generated: none
- identifiers_consumed: none
- identifier_flow: `strategy_id=N/A`; `hybrid_id=N/A`; `decision_id=N/A`; `file_seq=N/A`; `checksum_sha256=N/A`
- validations: Legacy route presence only
- persistence: none
- failure_branch: Detection point is operator stop or override command; handling action is UNDEFINED - not specified in the modular runtime source; halt/retry behavior is conceptual relative to the current modular runtime
- entrypoint_files: `services\calendar-ingestor\src\2099900096260118_python_calendar_system.py`
- status: conceptual
- notes: The legacy file contains `/api/emergency-stop`, but no equivalent control path is confirmed in the current modular runtime.

## SECTION 4 - DATA STORE MAP

| Stage | Confirmed storage mechanism | Confirmed store/path/topic/table | Notes |
| --- | --- | --- | --- |
| S01 | Environment-backed settings | OS environment / optional `.env` via per-service `Settings` | No shared config database or config service is confirmed |
| S02 | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | Startup order is documented/test-driven, not centrally persisted |
| S03 | none | none | `fetch_events()` currently returns `[]` |
| S04 | in-memory list | `CalendarIngestor.active_signals` candidate list | Non-durable pre-persistence state |
| S05 | CSV file | `.\data\calendar\active_calendar_signals_*.csv` | `.tmp` write plus atomic rename is implemented |
| S05a | Redis pub/sub | `calendar_events` | Pub/sub only; no Redis Streams confirmed |
| S06-S10 | Mixed in-memory / pub-sub / `UNKNOWN` | `price_ticks` is confirmed from `data-ingestor`; downstream durable stores are not confirmed | Signal-chain persistence is incomplete in current runtime |
| S11-S15 | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | Flow-orchestrator control-plane runtime is missing |
| S15a | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | No compliance/audit runtime store is confirmed |
| S16a | in-memory object | processor-local decision dict / CSV row object | Pre-write state only |
| S16b | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | Socket transport selection is documentary only |
| S16c | CSV files | `.\data\reentry\reentry_decisions_*.csv`; `.\data\reentry-engine\reentry_decisions_*.csv` | Both writers use `.tmp` plus atomic rename |
| S16d-S17a | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | No source-confirmed adapter ack or EA bridge intake store exists |
| S17b | MT4 terminal / broker state | MT4 order book and broker ticket state | Broker-side only; not bridged back to Python in checked-in EA |
| S18a | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | No checked-in producer writes trade-result artifacts |
| S18b | Source file on disk + in-memory cache | Result CSV file if present; transport-router validation cache | Watcher/validator exists even though producer is missing |
| S18c-S18d | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | Match gate and timeout manager are not implemented |
| S19-S22b | in-memory objects only | `TradeResult` object and processor-local variables | No durable result-normalization store is confirmed |
| S23 | JSON parameter matrix | `config\1199900002260118_parameter_sets.json` | This is the confirmed parameter-resolution source of truth |
| S23a | in-memory dictionaries | `symbol_cooldowns`; `daily_attempt_counts` | Reentry suppression state is not durable |
| S24 | in-memory dict | processor-local reentry decision dict | Pre-persistence state only |
| S24a | CSV + Redis pub/sub | `.\data\reentry\reentry_decisions_*.csv`; `eafix.reentry.decisions` | CSV path conflicts with transport-router watch config |
| S24b | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | No lookup-history persistence file/table is confirmed |
| S24c | in-memory lists/dicts | `recent_decisions`; `symbol_cooldowns`; `daily_attempt_counts` | No durable chain ledger is confirmed |
| S25 | `UNKNOWN - data store not confirmed` | `UNKNOWN - data store not confirmed` | No reentry-to-execution consumer is confirmed |
| S26 | CSV + Redis pub/sub + in-memory histories | `.\data\telemetry-daemon\health_metrics_*.csv`; `eafix.telemetry.health`; `eafix.telemetry.alerts` | Health emission is implemented |
| Ancillary legacy/side store | SQLite | `data\3099900005260118_signals.db` with tables `signals`, `aggregated_signals`, `sqlite_sequence` | Confirmed on disk, but not mapped into the active modular end-to-end flow |
| Unconfirmed stores | `UNKNOWN - not confirmed in source` | Postgres tables; Redis Streams; append-only trade ledger | Docs mention some of these, current runtime does not confirm them |

## SECTION 5 - GAP REGISTER

| Gap Type | Item | Affected step(s) | Evidence / note |
| --- | --- | --- | --- |
| `CONFLICTING SOURCE EVIDENCE` | Actual EA runtime vs documented HUEY_P bridge EA | S17a-S18a | `HUEY_P_EA_ExecutionEngine_8.mql4` is autonomous SMA logic; `0199900003260118_HUEY_P_EA_ExecutionEngine_8.md` describes CSV/socket bridge behavior |
| `UNMAPPED - source not confirmed` | `flow-orchestrator` runtime ownership and entrypoints | S11-S15, S25 | Only tests/docs reference orchestrator endpoints; runtime source is missing/deleted |
| `UNMAPPED - source not confirmed` | `signal-generator` runtime source | S08-S10 | Tests remain, service runtime files are absent |
| `UNMAPPED - source not confirmed` | MT4 bridge intake, adapter ack, heartbeat, socket demotion/promotion | S16b-S17a | Documentary only; no checked-in Python or MQL4 runtime implements it |
| `UNMAPPED - source not confirmed` | Trade-result artifact writer from MT4 back into Python | S18a | `TradeResult` contract exists, producer does not |
| `UNKNOWN` | `strategy_id` lineage in active modular runtime | S10-S25 | Only legacy calendar files use `strategy_id`; no active modular path carries it end-to-end |
| `UNMAPPED - source not confirmed` | `decision_id` generation and consumption | S11-S25 | No current modular runtime file generates or consumes `decision_id` |
| `CONFLICTING SOURCE EVIDENCE` | `hybrid_id` format definitions conflict | S22b-S24a | Python shared library uses `_`; MT4 helper uses `SIG~...`; identifier tech spec uses hyphenated CAL8-first format |
| `CONFLICTING SOURCE EVIDENCE` | Calendar proximity vocabulary conflicts with contract | S04-S05, S22 | Runtime emits `PRE_1H` / `AT_EVENT` / `POST_30M`; CSV model expects `IMMEDIATE` / `NEAR` / `FAR` |
| `CONFLICTING SOURCE EVIDENCE` | Redis topic names differ across services | S05a, S06-S07, S18-S24a | `calendar_events`, `price_ticks`, and `eafix.trades.results` conflict with event-gateway config topics |
| `CONFLICTING SOURCE EVIDENCE` | Reentry output path differs from transport-router watch path | S16c, S24a, S25 | `reentry-matrix-svc` writes `.\data\reentry`; transport-router watches `.\data\reentry-matrix` |
| `CONFLICTING SOURCE EVIDENCE` | Contract package imports do not match filename layout | Global | `contracts\models\2099900019260118___init__.py` expects unprefixed modules not present in the tree |
| `CONFLICTING SOURCE EVIDENCE` | Test import paths assume underscore package names; runtime dirs are hyphenated | Global | Example: tests refer to `services.calendar_ingestor...`, tree uses `services\calendar-ingestor` |
| `CONFLICTING SOURCE EVIDENCE` | `ReentryDecision.hybrid_id` validator rejects current underscore-bearing IDs | S16a, S24a | Validator splits on `_`, but valid IDs already contain `_` tokens |
| `CONFLICTING SOURCE EVIDENCE` | `TradeResult` normalization uses placeholder values that violate model constraints | S19 | `_validate_trade_result()` injects `file_seq=0` and invalid checksum placeholder |
| `UNDEFINED - not specified in source` | Stale scheduler/calendar freshness handling | S12 | Required by target process, but no source-confirmed freshness gate exists |
| `UNDEFINED - not specified in source` | Recovery policy after sequence gap detection | S17a, S18b, S18c | Current validator warns only; no runtime recovery or halt escalation is defined |
| `UNDEFINED - not specified in source` | Recovery policy after checksum mismatch beyond validation failure | S16c, S17a, S18b | Validation exists, but bridge/runtime retry semantics are not specified |
| `UNDEFINED - not specified in source` | Timeout / no-result recovery path | S18d | No timeout manager or compensating action source was found |
| `UNDEFINED - not specified in source` | Reentry-to-execution retry behavior | S25 | No consumer exists, so retry semantics are absent |
| `UNKNOWN` | Decision audit log store | S15a | Docs describe audit behavior; no confirmed runtime store exists |
| `UNKNOWN` | Execution-result storage store from actual EA | S18a | No confirmed CSV/socket result store from MT4 exists in current runtime |
| `UNKNOWN` | Matrix lookup history store | S24b | No file/table/topic persists it |
| `UNKNOWN` | Durable chain ledger / append-only reentry history | S24c | Only in-memory dictionaries/lists are confirmed |
| `UNKNOWN` | Postgres trade-flow tables | Global | No inspected active service writes to Postgres |
| `UNKNOWN` | Redis Streams usage | Global | Current runtime uses Redis pub/sub, not streams |
| `UNKNOWN` | Append-only trade or decision logs | Global | No confirmed append-only log file/table is present for the active flow |
| `PLANNED` | Calendar source polling is stubbed | S03 | `fetch_events()` exists but returns `[]` |
| `UNMAPPED - source not confirmed` | Data-ingestor adapter modules | S06 | `mt4_adapter`, `csv_adapter`, and `socket_adapter` imports are referenced but missing |
| `UNKNOWN` | Cross-service startup/bootstrap ordering | S02 | Service mains exist, but no source-confirmed central ordering or dependency hydration exists |
| `UNMAPPED - source not confirmed` | `hybrid_id` continuity gate and pending-order correlator | S18c | No current runtime file performs result-to-decision correlation |
| `CONCEPTUAL` | Multi-symbol / portfolio coordination | S26a | No source-confirmed portfolio manager or shared exposure state exists |
| `CONCEPTUAL` | Manual override / emergency stop / risk-off in modular runtime | S26b | Only legacy calendar system file exposes `/api/emergency-stop` |

## SECTION 6 - FINAL ASSESSMENT

- What appears implemented now: service-local config loading; calendar event normalization plus atomic CSV writes; Redis pub/sub notifications; `data-ingestor` tick publish path; indicator/risk/execution plugin stubs; transport-router file watching and validation; reentry-engine normalization/classification/eligibility heuristics; tiered parameter resolution from JSON; `hybrid_id` composition in `reentry-matrix-svc`; reentry decision CSV persistence plus Redis publish; telemetry CSV/alert emission; and the autonomous SMA-based MT4 EA broker execution path.
- What appears planned: the `flow-orchestrator` control plane; synchronous signal-time calendar/reentry/risk/execution coordination; MT4 socket bridge, CSV bridge intake, adapter ack lifecycle, heartbeat, and failover; trade-result artifact emission from MT4 back into Python; decision audit persistence; matrix lookup history persistence; and a real reentry decision consumer that routes back into execution.
- What remains conceptual: one reconciled canonical end-to-end trading runtime across the canonical process doc, modular microservices, and HUEY_P/MT4 artifacts; portfolio-wide coordination; modular-runtime emergency stop / risk-off suppression; and a production-grade, fully mapped identifier lineage that includes `strategy_id` and `decision_id`.
- Which gaps block a reliable production-grade process document: the missing `flow-orchestrator` runtime; the absence of a source-confirmed MT4 bridge in the checked-in EA; the absence of a source-confirmed execution-result bridge back from MT4; identifier lineage breaks for `strategy_id` and `decision_id`; contract/runtime conflicts around `hybrid_id`, `proximity_state`, topic names, and import paths; and the lack of durable audit, chain-history, and production-grade result stores.

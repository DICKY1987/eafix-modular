# EAFIX / HUEY_P — Module Reconciliation Worksheet

**Process:** `HUEY_P_EAFIX_END_TO_END` v2.0.0  |  **Canonical modules:** 27 (26 pipeline + SHARED_LIBS)  |  **Generated from:** module_catalog.json, process_step_catalog.json, updated_trading_process_aligned.json, EAFIX-Modular End-to-End Module Map.txt, file_module_mapping.csv, module_checklist.json, communication_channels.json, eafix_services_ai_reference.

> Authoritative spine = `module_catalog.json` (kind/layer/identity) + `process_step_catalog.json` (step/handoff) + `updated_trading_process_aligned.json` (phase). The **map_kind_label**, **service_home**, **mapped files**, and **submodule doc** columns are the layers that drift from that spine — flags mark each divergence.

## Worksheet

|# |Numeric ID          |Symbol                     |Catalog Kind|Layer     |Map Grp|Map Kind Label|Step|Phase|Responsible File                     |Service Home (authoritative)            |Candidate Svc (INFERRED)             |Owned Channels                                          |Files|Stale CSV Sym    |Submodule Doc|Flags                                                                          |
|--|--------------------|---------------------------|------------|----------|-------|--------------|----|-----|-------------------------------------|----------------------------------------|-------------------------------------|--------------------------------------------------------|-----|-----------------|-------------|-------------------------------------------------------------------------------|
|1 |50000000000000000001|F1_CONFIG_PREFERENCES      |INFRA       |1         |G0     |INFRA         |S01 |A    |configuration_service.py             |services/calendar-ingestor or standalone|common?                              |—                                                       |0    |—                |MISSING      |NO_FILES | SUBMODULE_UNDOC | PREFIX_COLLISION_F1                               |
|2 |50000000000000000002|F3_CLOCK_SCHEDULER         |INFRA       |1         |G0     |INFRA         |S02 |A    |scheduler.py                         |services/calendar-ingestor              |calendar-ingestor                    |—                                                       |0    |—                |MISSING      |NO_FILES | SUBMODULE_UNDOC                                                     |
|3 |50000000000000000003|D2_CALENDAR_SOURCE_ADAPTER |BRIDGE      |2         |G1     |BRIDGE        |S03 |B    |calendar_service.py::poll_scheduler  |UNBOUND (not in map)                    |calendar-ingestor                    |—                                                       |11   |—                |YES (3 subs) |SERVICE_UNBOUND                                                                |
|4 |50000000000000000004|D3_CALENDAR_NORMALIZER     |BRIDGE      |2         |G1     |BRIDGE        |S04 |B    |calendar_service.py::normalize_events|UNBOUND (not in map)                    |calendar-ingestor                    |—                                                       |11   |—                |YES (3 subs) |SERVICE_UNBOUND                                                                |
|5 |50000000000000000005|F2_EVENT_LOG               |INFRA       |1         |G0     |INFRA         |S05 |B    |event_log.py                         |Postgres via event_log.py               |(Postgres - infra)                   |—                                                       |11   |—                |MISSING      |SUBMODULE_UNDOC                                                                |
|6 |50000000000000000006|D4_CALENDAR_TRIGGER_BUILDER|BRIDGE      |2         |G1     |BRIDGE        |S06 |B    |calendar_anticipator.py              |UNBOUND (not in map)                    |calendar-ingestor                    |—                                                       |11   |—                |MISSING      |SUBMODULE_UNDOC | SERVICE_UNBOUND                                              |
|7 |50000000000000000007|D1_MARKET_FEED_ADAPTER     |BRIDGE      |2         |G1     |BRIDGE        |S07 |C    |market_feed_adapter.py               |UNBOUND (not in map)                    |data-ingestor                        |dde_price_feed                                          |12   |—                |MISSING      |SUBMODULE_UNDOC | SERVICE_UNBOUND                                              |
|8 |50000000000000000008|C1_BAR_BUILDER             |PIPELINE    |3         |G2     |COMPUTE       |S08 |C    |bar_builder.py                       |UNBOUND (not in map)                    |indicator-engine                     |—                                                       |0    |—                |MISSING      |KIND_MISMATCH | NO_FILES | SUBMODULE_UNDOC | SERVICE_UNBOUND                   |
|9 |50000000000000000009|C2_INDICATOR_ENGINE        |PIPELINE    |3         |G2     |COMPUTE       |S09 |C    |indicator_engine.py                  |UNBOUND (not in map)                    |indicator-engine                     |—                                                       |4    |—                |MISSING      |KIND_MISMATCH | SUBMODULE_UNDOC | SERVICE_UNBOUND                              |
|10|50000000000000000010|C3_FEATURE_PACKAGER        |PIPELINE    |3         |G2     |COMPUTE       |S10 |D    |feature_packager.py                  |UNBOUND (not in map)                    |indicator-engine                     |—                                                       |0    |—                |MISSING      |KIND_MISMATCH | NO_FILES | SUBMODULE_UNDOC | SERVICE_UNBOUND                   |
|11|50000000000000000011|S1_SIGNAL_ENGINE           |PIPELINE    |4         |G3     |SIGNAL        |S11 |E    |signal_generator.py                  |UNBOUND (not in map)                    |signal-generator                     |—                                                       |1    |—                |MISSING      |KIND_MISMATCH | SUBMODULE_UNDOC | SERVICE_UNBOUND                              |
|12|50000000000000000012|S2_INTENT_BUILDER          |PIPELINE    |4         |G3     |SIGNAL        |S12 |E    |intent_builder.py                    |UNBOUND (not in map)                    |signal-generator?                    |—                                                       |0    |—                |MISSING      |KIND_MISMATCH | NO_FILES | SUBMODULE_UNDOC | SERVICE_UNBOUND                   |
|13|50000000000000000013|R1_RISK_EVALUATOR          |PIPELINE    |4         |G4     |RISK          |S13 |E    |risk_manager.py                      |UNBOUND (not in map)                    |risk-manager                         |—                                                       |2    |—                |YES (3 subs) |KIND_MISMATCH | SERVICE_UNBOUND | CHECKLIST_KEY_FMT                            |
|14|50000000000000000014|R2_ORDER_INTENT_COMPILER   |PIPELINE    |4         |G4     |RISK          |S14 |F    |order_intent_compiler.py             |UNBOUND (not in map)                    |risk-manager                         |—                                                       |10   |—                |MISSING      |KIND_MISMATCH | SUBMODULE_UNDOC | SERVICE_UNBOUND                              |
|15|50000000000000000015|O1_ORDER_ROUTER            |PIPELINE    |4         |G5     |OMS           |S15 |G    |order_router.py                      |UNBOUND (not in map)                    |transport-router? / execution-engine?|—                                                       |10   |—                |MISSING      |KIND_MISMATCH | SUBMODULE_UNDOC | SERVICE_UNBOUND                              |
|16|50000000000000000016|B1_MT4_ADAPTER_TRANSPORT   |BRIDGE      |4         |G6     |BRIDGE        |S16 |G    |transport_service.py                 |UNBOUND (not in map)                    |transport-router                     |jsonl_outbox;csv_transport;tcp_socket_fallback(disabled)|10   |—                |YES (3 subs) |SERVICE_UNBOUND                                                                |
|17|50000000000000000017|B2_MT4_EA_EXECUTOR         |BRIDGE      |4         |G6     |BRIDGE        |S17 |G    |EAFIX.mq4                            |UNBOUND (not in map)                    |(EA-side MQL4)                       |http_rest_primary(5001)                                 |2    |—                |MISSING      |SUBMODULE_UNDOC | SERVICE_UNBOUND                                              |
|18|50000000000000000018|B3_EXEC_EVENT_NORMALIZER   |BRIDGE      |4         |G6     |BRIDGE        |S18 |H    |result_processor.py                  |UNBOUND (not in map)                    |execution-engine                     |redis_pubsub_bus                                        |0    |—                |MISSING      |NO_FILES | SUBMODULE_UNDOC | SERVICE_UNBOUND                                   |
|19|50000000000000000019|O2_OMS_STATE_MACHINE       |PIPELINE    |4         |G5     |OMS           |S19 |I    |oms.py                               |UNBOUND (not in map)                    |execution-engine                     |—                                                       |2    |O2_OMS           |YES (3 subs) |KIND_MISMATCH | STALE_CSV_SYMBOL | SERVICE_UNBOUND                             |
|20|50000000000000000020|O3_TRADE_CLOSE_CLASSIFIER  |PIPELINE    |4         |G5     |OMS           |S20 |I    |trade_close_classifier.py            |UNBOUND (not in map)                    |execution-engine                     |—                                                       |2    |O3_PNL_CLASSIFIER|MISSING      |KIND_MISMATCH | STALE_CSV_SYMBOL | SUBMODULE_UNDOC | SERVICE_UNBOUND           |
|21|50000000000000000021|E1_OUTCOME_BUCKETIZER      |PIPELINE    |4         |G7     |REENTRY       |S21 |I    |outcome_bucketizer.py                |UNBOUND (not in map)                    |reentry-engine                       |—                                                       |9    |—                |MISSING      |KIND_MISMATCH | SUBMODULE_UNDOC | SERVICE_UNBOUND                              |
|22|50000000000000000022|E2_PROXIMITY_EVALUATOR     |PIPELINE    |4         |G7     |REENTRY       |S22 |I    |proximity_evaluator.py               |UNBOUND (not in map)                    |reentry-engine                       |—                                                       |9    |—                |MISSING      |KIND_MISMATCH | SUBMODULE_UNDOC | SERVICE_UNBOUND                              |
|23|50000000000000000023|E3_MATRIX_LOOKUP           |PIPELINE    |4         |G7     |REENTRY       |S23 |I    |matrix_lookup.py                     |UNBOUND (not in map)                    |reentry-matrix-svc                   |—                                                       |9    |—                |YES (3 subs) |KIND_MISMATCH | SERVICE_UNBOUND                                                |
|24|50000000000000000024|E4_REENTRY_INTENT_BUILDER  |PIPELINE    |4         |G7     |REENTRY       |S24 |I    |reentry_intent_builder.py            |UNBOUND (not in map)                    |reentry-engine                       |—                                                       |9    |—                |MISSING      |KIND_MISMATCH | SUBMODULE_UNDOC | SERVICE_UNBOUND                              |
|25|50000000000000000025|F1_FLOW_ORCHESTRATOR       |INFRA       |unassigned|G0     |INFRA         |S25 |J    |orchestrator                         |flow-orchestrator (port 8088)           |flow-orchestrator                    |—                                                       |0    |—                |MISSING      |NO_FILES | SUBMODULE_UNDOC | LAYER_UNASSIGNED | PREFIX_COLLISION_F1            |
|26|50000000000000000026|P1_HEALTH_AGGREGATOR       |OBSERV      |1         |G0     |INFRA         |S26 |J    |health_service.py                    |telemetry-daemon / flow-monitor         |telemetry-daemon                     |—                                                       |12   |—                |MISSING      |KIND_MISMATCH | SUBMODULE_UNDOC                                                |
|27|50000000000000000099|SHARED_LIBS                |PIPELINE    |unassigned|G10    |SHARED        |—   |—    |—                                    |UNBOUND (not in map)                    |common                               |—                                                       |0    |—                |MISSING      |KIND_MISMATCH | NO_FILES | SUBMODULE_UNDOC | SERVICE_UNBOUND | LAYER_UNASSIGNED|

## Flag legend

- **KIND_MISMATCH** — Map’s kind label for this module’s group differs from the catalog’s `module_kind`. The map invents COMPUTE/SIGNAL/RISK/OMS/REENTRY kinds; catalog stores them all as PIPELINE_STAGE_MODULE (and P1 as OBSERVABILITY_REPORTING vs map’s INFRA).
- **SERVICE_UNBOUND** — No authoritative service home exists. The map states a service home only for the 5 Group-0 modules; for everyone else the home is unstated. `candidate_service_INFERRED` is a best-guess, NOT canonical — needs a binding decision.
- **SUBMODULE_UNDOC** — Module is absent from module_checklist.json, so it has no submodule decomposition or the 6 per-module contract docs.
- **NO_FILES** — Zero implementation files mapped to this module in file_module_mapping.csv.
- **STALE_CSV_SYMBOL** — CSV maps files to this module only under a non-canonical/deprecated symbol (O2_OMS -> O2_OMS_STATE_MACHINE; O3_PNL_CLASSIFIER -> O3_TRADE_CLOSE_CLASSIFIER).
- **LAYER_UNASSIGNED** — catalog `layer` = ‘unassigned’ (FLOW_ORCHESTRATOR, SHARED_LIBS).
- **PREFIX_COLLISION_F1** — Symbol prefix `F1` is reused by two modules: F1_CONFIG_PREFERENCES and F1_FLOW_ORCHESTRATOR.
- **CHECKLIST_KEY_FMT** — module_checklist.json keys this module as `<numericID>_<symbol>` while the other 5 entries use the bare symbol.

## Summary counts

|Flag               |Modules affected|
|-------------------|----------------|
|KIND_MISMATCH      |16              |
|SERVICE_UNBOUND    |22              |
|SUBMODULE_UNDOC    |21              |
|NO_FILES           |8               |
|STALE_CSV_SYMBOL   |2               |
|LAYER_UNASSIGNED   |2               |
|PREFIX_COLLISION_F1|2               |
|CHECKLIST_KEY_FMT  |1               |

## Module-count reconciliation (map vs catalog)

|Source                  |Pipeline    |SHARED_LIBS  |Stated total                              |Actual total  |
|------------------------|------------|-------------|------------------------------------------|--------------|
|module_catalog.json     |26          |1            |—                                         |**27**        |
|Map header (line 5)     |—           |+ SHARED_LIBS|‘28 canonical modules + SHARED_LIBS’ (=29)|27            |
|Map total row (line 453)|27 (claimed)|1            |‘28’                                      |rows sum to 27|

**Resolution:** correct the map to 27 (26 pipeline + SHARED_LIBS) and replace the COMPUTE/SIGNAL/RISK/OMS/REENTRY group-kind labels with the catalog’s 4 real kinds, or add those 5 names to the catalog’s kind enum if the finer taxonomy is intended. Pick one source of truth for `module_kind`.

## Kind taxonomy crosswalk

|Map kind label           |Catalog kind                                    |Modules                                        |
|-------------------------|------------------------------------------------|-----------------------------------------------|
|INFRA_PLATFORM_MODULE    |INFRA_PLATFORM_MODULE ✓ (except P1)             |F1_CONFIG, F3_CLOCK, F2_EVENT_LOG, F1_FLOW_ORCH|
|INFRA_PLATFORM_MODULE    |**OBSERVABILITY_REPORTING_MODULE** (P1 conflict)|P1_HEALTH_AGGREGATOR                           |
|INTEGRATION_BRIDGE_MODULE|INTEGRATION_BRIDGE_MODULE ✓                     |D1–D4, B1–B3                                   |
|COMPUTE_MODULE           |**PIPELINE_STAGE_MODULE**                       |C1, C2, C3                                     |
|SIGNAL_MODULE            |**PIPELINE_STAGE_MODULE**                       |S1, S2                                         |
|RISK_MODULE              |**PIPELINE_STAGE_MODULE**                       |R1, R2                                         |
|OMS_MODULE               |**PIPELINE_STAGE_MODULE**                       |O1, O2, O3                                     |
|REENTRY_MODULE           |**PIPELINE_STAGE_MODULE**                       |E1–E4                                          |
|SHARED_LIBS              |PIPELINE_STAGE_MODULE                           |SHARED_LIBS                                    |
# Manifest Fill Coverage Report (vNext)

## Summary
- **total_manifests**: 34
- **schema_valid_manifests**: 34
- **thin_modules**: 0
- **modules_with_no_files**: 15
- **modules_with_shared_service_files**: 13
- **modules_with_runtime_ports**: 16
- **modules_with_ui_bindings**: 4
- **modules_with_mt4_constraints**: 4
- **modules_with_unresolved_dependencies**: 0
- **source_conflicts_by_category**: {}

## Module Coverage
| module_id | canonical_symbol | identity | classification | purpose | process binding | contracts | dependencies | file ownership | runtime | comm channels | UI | MT4 | validation/failure | docs | unresolved |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 50000000000000000001 | F1_CONFIG_PREFERENCES | filled | filled | filled | filled | filled | missing | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 1 |
| 50000000000000000002 | F3_CLOCK_SCHEDULER | filled | filled | filled | filled | filled | filled | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 1 |
| 50000000000000000003 | D2_CALENDAR_SOURCE_ADAPTER | filled | filled | filled | filled | filled | filled | partial | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000004 | D3_CALENDAR_NORMALIZER | filled | filled | filled | filled | filled | filled | partial | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000005 | F2_EVENT_LOG | filled | filled | filled | filled | filled | filled | partial | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000006 | D4_CALENDAR_TRIGGER_BUILDER | filled | filled | filled | filled | filled | filled | partial | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000007 | D1_MARKET_FEED_ADAPTER | filled | filled | filled | filled | filled | filled | complete | filled | filled | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000008 | C1_BAR_BUILDER | filled | filled | filled | filled | filled | filled | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 1 |
| 50000000000000000009 | C2_INDICATOR_ENGINE | filled | filled | filled | filled | filled | filled | complete | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000010 | C3_FEATURE_PACKAGER | filled | filled | filled | filled | filled | filled | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 1 |
| 50000000000000000011 | S1_SIGNAL_ENGINE | filled | filled | filled | filled | filled | filled | complete | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000012 | S2_INTENT_BUILDER | filled | filled | filled | filled | filled | filled | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 1 |
| 50000000000000000013 | R1_RISK_EVALUATOR | filled | filled | filled | filled | filled | filled | complete | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000014 | R2_ORDER_INTENT_COMPILER | filled | filled | filled | filled | filled | filled | partial | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000015 | O1_ORDER_ROUTER | filled | filled | filled | filled | filled | filled | partial | missing | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000016 | B1_MT4_ADAPTER_TRANSPORT | filled | filled | filled | filled | filled | filled | partial | missing | filled | not_applicable | filled | filled | generated | 0 |
| 50000000000000000017 | B2_MT4_EA_EXECUTOR | filled | filled | filled | filled | filled | filled | partial | missing | filled | not_applicable | filled | filled | generated | 0 |
| 50000000000000000018 | B3_EXEC_EVENT_NORMALIZER | filled | filled | filled | filled | filled | filled | unassigned | missing | filled | not_applicable | not_applicable | filled | generated | 1 |
| 50000000000000000019 | O2_OMS_STATE_MACHINE | filled | filled | filled | filled | filled | filled | partial | missing | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000020 | O3_TRADE_CLOSE_CLASSIFIER | filled | filled | filled | filled | filled | filled | partial | missing | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000021 | E1_OUTCOME_BUCKETIZER | filled | filled | filled | filled | filled | filled | partial | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000022 | E2_PROXIMITY_EVALUATOR | filled | filled | filled | filled | filled | filled | partial | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000023 | E3_MATRIX_LOOKUP | filled | filled | filled | filled | filled | filled | complete | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000024 | E4_REENTRY_INTENT_BUILDER | filled | filled | filled | filled | filled | filled | partial | filled | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000025 | F4_FLOW_ORCHESTRATOR | filled | filled | filled | filled | filled | filled | unassigned | filled | not_applicable | not_applicable | not_applicable | filled | generated | 2 |
| 50000000000000000026 | P1_HEALTH_AGGREGATOR | filled | filled | filled | filled | filled | filled | complete | missing | not_applicable | not_applicable | not_applicable | filled | generated | 0 |
| 50000000000000000027 | R3_CORRELATION_GUARD | filled | filled | filled | filled | filled | missing | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 3 |
| 50000000000000000028 | U1_DASHBOARD_BACKEND | filled | filled | filled | filled | filled | missing | unassigned | filled | not_applicable | filled | not_applicable | filled | generated | 3 |
| 50000000000000000029 | U2_GUI_GATEWAY | filled | filled | filled | filled | filled | missing | unassigned | filled | not_applicable | filled | not_applicable | filled | generated | 3 |
| 50000000000000000030 | U3_MT4_EXPIRY_OVERLAY | filled | filled | filled | filled | filled | missing | unassigned | missing | not_applicable | filled | filled | filled | generated | 3 |
| 50000000000000000031 | U4_DESKTOP_OPERATOR | filled | filled | filled | filled | filled | missing | unassigned | missing | not_applicable | filled | filled | filled | generated | 3 |
| 50000000000000000032 | P2_REPORTER | filled | filled | filled | filled | filled | missing | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 3 |
| 50000000000000000033 | SK1_PLUGIN_INTERFACE | filled | filled | filled | filled | filled | missing | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 3 |
| 50000000000000000034 | SK2_IDEMPOTENCY | filled | filled | filled | filled | filled | missing | unassigned | missing | not_applicable | not_applicable | not_applicable | filled | generated | 3 |

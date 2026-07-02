# EAFIX Module Manifest — First-Pass Fill Coverage

Generated 2026-06-24T06:56:42.646771+00:00

34 canonical modules (vNext LOCKED_PASS_1). Identity + classification + purpose are fully populated for **all 34**.
Richer sections depend on source coverage below.

| # | Symbol | Module | Scope/Resp | Steps | Files | Service | Flags |
|---|--------|--------|:---:|:---:|:---:|--------|-------|
| 1 | `F1_CONFIG_PREFERENCES` | Configuration Service | Y | 1 | 0 | - | NO_FILES,SUBMODULE_UNDOC |
| 2 | `F3_CLOCK_SCHEDULER` | Clock Scheduler | Y | 1 | 0 | - | NO_FILES,SUBMODULE_UNDOC |
| 3 | `D2_CALENDAR_SOURCE_ADAPTER` | Calendar Source Adapter | Y | 1 | 11 | calendar-ingestor | SERVICE_UNBOUND |
| 4 | `D3_CALENDAR_NORMALIZER` | Calendar Normalizer | Y | 1 | 11 | calendar-ingestor | SERVICE_UNBOUND |
| 5 | `F2_EVENT_LOG` | Event Log | Y | 1 | 11 | calendar-ingestor | SUBMODULE_UNDOC |
| 6 | `D4_CALENDAR_TRIGGER_BUILDER` | Calendar Trigger Builder | Y | 1 | 11 | calendar-ingestor | SERVICE_UNBOUND,SUBMODULE_UNDOC |
| 7 | `D1_MARKET_FEED_ADAPTER` | Market Feed Adapter | Y | 1 | 12 | data-ingestor | SERVICE_UNBOUND,SUBMODULE_UNDOC |
| 8 | `C1_BAR_BUILDER` | Bar Builder | Y | 1 | 0 | - | NO_FILES,SERVICE_UNBOUND |
| 9 | `C2_INDICATOR_ENGINE` | Indicator Engine | Y | 1 | 4 | indicator-engine | SERVICE_UNBOUND |
| 10 | `C3_FEATURE_PACKAGER` | Feature Packager | Y | 1 | 0 | - | NO_FILES,SERVICE_UNBOUND |
| 11 | `S1_SIGNAL_ENGINE` | Signal Engine | Y | 1 | 1 | signal-generator | SERVICE_UNBOUND |
| 12 | `S2_INTENT_BUILDER` | Intent Builder | Y | 1 | 0 | - | NO_FILES,SERVICE_UNBOUND |
| 13 | `R1_RISK_EVALUATOR` | Risk Evaluator | Y | 1 | 2 | risk-manager | SCOPE_NARROWED,SERVICE_UNBOUND |
| 14 | `R3_CORRELATION_GUARD` | Correlation Guard | - | 0 | 0 | - | NO_FILES |
| 15 | `R2_ORDER_INTENT_COMPILER` | Order Intent Compiler | Y | 1 | 10 | transport-router | SERVICE_UNBOUND,SUBMODULE_UNDOC |
| 16 | `O1_ORDER_ROUTER` | Order Router | Y | 1 | 10 | transport-router | SERVICE_UNBOUND,SUBMODULE_UNDOC |
| 17 | `B1_MT4_ADAPTER_TRANSPORT` | MT4 Adapter Transport | Y | 1 | 10 | transport-router | SERVICE_UNBOUND |
| 18 | `B2_MT4_EA_EXECUTOR` | MT4 EA Executor | Y | 1 | 2 | execution-engine | EA_SECOND_PASS,SERVICE_UNBOUND,SUBMODULE_UNDOC |
| 19 | `B3_EXEC_EVENT_NORMALIZER` | Exec Event Normalizer | Y | 1 | 0 | - | NO_FILES,SERVICE_UNBOUND |
| 20 | `O2_OMS_STATE_MACHINE` | OMS State Machine | Y | 1 | 2 | execution-engine | SERVICE_UNBOUND,STALE_FILE_SYMBOL |
| 21 | `O3_TRADE_CLOSE_CLASSIFIER` | Trade Close Classifier | Y | 1 | 2 | execution-engine | SERVICE_UNBOUND,STALE_FILE_SYMBOL,SUBMODULE_UNDOC |
| 22 | `E1_OUTCOME_BUCKETIZER` | Outcome Bucketizer | Y | 1 | 9 | reentry-engine | SERVICE_UNBOUND,SUBMODULE_UNDOC |
| 23 | `E2_PROXIMITY_EVALUATOR` | Proximity Evaluator | Y | 1 | 9 | reentry-engine | SERVICE_UNBOUND,SUBMODULE_UNDOC |
| 24 | `E3_MATRIX_LOOKUP` | Matrix Lookup | Y | 1 | 9 | reentry-matrix-svc | SERVICE_UNBOUND |
| 25 | `E4_REENTRY_INTENT_BUILDER` | Reentry Intent Builder | Y | 1 | 9 | reentry-engine | SERVICE_UNBOUND,SUBMODULE_UNDOC |
| 26 | `F4_FLOW_ORCHESTRATOR` | Flow Orchestrator | - | 0 | 0 | - | NO_FILES |
| 27 | `P1_HEALTH_AGGREGATOR` | Health Aggregator | Y | 1 | 12 | telemetry-daemon | SUBMODULE_UNDOC |
| 28 | `U1_DASHBOARD_BACKEND` | Dashboard Backend | - | 0 | 0 | - | NEW_MODULE,NO_FILES,UI_DATA_MOCK_TO_RECONCILE |
| 29 | `U2_GUI_GATEWAY` | GUI Gateway | - | 0 | 0 | - | NEW_MODULE,NO_FILES |
| 30 | `U3_MT4_EXPIRY_OVERLAY` | MT4 Expiry Zones Overlay | - | 0 | 0 | - | NEW_MODULE,NO_FILES,OWNS_CHANNEL_HTTP5001 |
| 31 | `U4_DESKTOP_OPERATOR` | Desktop Operator UI | - | 0 | 0 | - | NEW_MODULE,NO_FILES,SAFETY_CONTROLS |
| 32 | `P2_REPORTER` | Reporter | - | 0 | 0 | - | NEW_MODULE,NOT_IN_PRIOR_CATALOG,NO_FILES |
| 33 | `SK1_PLUGIN_INTERFACE` | Plugin Interface | - | 0 | 0 | - | NEW_MODULE,NO_FILES,PROMOTED_FROM_SHARED_LIBS |
| 34 | `SK2_IDEMPOTENCY` | Idempotency | - | 0 | 0 | - | NEW_MODULE,NO_FILES,PROMOTED_FROM_SHARED_LIBS |

**9 thin modules** (identity/classification only — need scope, steps, files): `R3_CORRELATION_GUARD`, `F4_FLOW_ORCHESTRATOR`, `U1_DASHBOARD_BACKEND`, `U2_GUI_GATEWAY`, `U3_MT4_EXPIRY_OVERLAY`, `U4_DESKTOP_OPERATOR`, `P2_REPORTER`, `SK1_PLUGIN_INTERFACE`, `SK2_IDEMPOTENCY`

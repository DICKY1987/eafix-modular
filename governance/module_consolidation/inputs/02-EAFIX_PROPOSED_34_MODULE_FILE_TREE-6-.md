# EAFIX Proposed 34-Module Repository File Tree

**Status:** Proposed target structure; not yet implemented.
**Repository:** `DICKY1987/eafix-modular`
**Module count:** 34

## Governing interpretation

- Module roots use `<locator>-<canonical-symbol-as-kebab-case>`.
- First-level governed containers use `<locator>-<role>`.
- Hidden module state uses `.<locator>-state`.
- Nested folders remain conventional and are not prefixed.
- Python package directories and MQL4 runtime-constrained directories remain conventional.
- `.module-id` contains the full 20-digit canonical module ID.
- The baseline containers shown here are proposed. `module_container_inventory.json` must confirm which optional containers each module actually instantiates before physical migration.

## Proposed tree

```text
eafix-modular/
├── m0001-f1-config-preferences/
│   ├── .module-id
│   ├── m0001-src/
│   │   └── f1_config_preferences/
│   ├── m0001-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0001-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0001-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0001-config/
│   ├── m0001-scripts/
│   ├── m0001-context/
│   ├── .m0001-state/
│   ├── 50000000000000000001_F1_CONFIG_PREFERENCES.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0002-f3-clock-scheduler/
│   ├── .module-id
│   ├── m0002-src/
│   │   └── f3_clock_scheduler/
│   ├── m0002-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0002-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0002-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0002-config/
│   ├── m0002-scripts/
│   ├── m0002-context/
│   ├── .m0002-state/
│   ├── 50000000000000000002_F3_CLOCK_SCHEDULER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0003-d2-calendar-source-adapter/
│   ├── .module-id
│   ├── m0003-src/
│   │   └── d2_calendar_source_adapter/
│   ├── m0003-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0003-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0003-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0003-config/
│   ├── m0003-scripts/
│   ├── m0003-context/
│   ├── .m0003-state/
│   ├── 50000000000000000003_D2_CALENDAR_SOURCE_ADAPTER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0004-d3-calendar-normalizer/
│   ├── .module-id
│   ├── m0004-src/
│   │   └── d3_calendar_normalizer/
│   ├── m0004-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0004-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0004-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0004-config/
│   ├── m0004-scripts/
│   ├── m0004-context/
│   ├── .m0004-state/
│   ├── 50000000000000000004_D3_CALENDAR_NORMALIZER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0005-f2-event-log/
│   ├── .module-id
│   ├── m0005-src/
│   │   └── f2_event_log/
│   ├── m0005-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0005-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0005-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0005-config/
│   ├── m0005-scripts/
│   ├── m0005-context/
│   ├── .m0005-state/
│   ├── 50000000000000000005_F2_EVENT_LOG.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0006-d4-calendar-trigger-builder/
│   ├── .module-id
│   ├── m0006-src/
│   │   └── d4_calendar_trigger_builder/
│   ├── m0006-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0006-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0006-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0006-config/
│   ├── m0006-scripts/
│   ├── m0006-context/
│   ├── .m0006-state/
│   ├── 50000000000000000006_D4_CALENDAR_TRIGGER_BUILDER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0007-d1-market-feed-adapter/
│   ├── .module-id
│   ├── m0007-src/
│   │   └── d1_market_feed_adapter/
│   ├── m0007-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0007-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0007-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0007-config/
│   ├── m0007-scripts/
│   ├── m0007-context/
│   ├── .m0007-state/
│   ├── 50000000000000000007_D1_MARKET_FEED_ADAPTER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0008-c1-bar-builder/
│   ├── .module-id
│   ├── m0008-src/
│   │   └── c1_bar_builder/
│   ├── m0008-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0008-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0008-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0008-config/
│   ├── m0008-scripts/
│   ├── m0008-context/
│   ├── .m0008-state/
│   ├── 50000000000000000008_C1_BAR_BUILDER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0009-c2-indicator-engine/
│   ├── .module-id
│   ├── m0009-src/
│   │   └── c2_indicator_engine/
│   ├── m0009-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0009-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0009-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0009-config/
│   ├── m0009-scripts/
│   ├── m0009-context/
│   ├── .m0009-state/
│   ├── 50000000000000000009_C2_INDICATOR_ENGINE.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0010-c3-feature-packager/
│   ├── .module-id
│   ├── m0010-src/
│   │   └── c3_feature_packager/
│   ├── m0010-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0010-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0010-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0010-config/
│   ├── m0010-scripts/
│   ├── m0010-context/
│   ├── .m0010-state/
│   ├── 50000000000000000010_C3_FEATURE_PACKAGER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0011-s1-signal-engine/
│   ├── .module-id
│   ├── m0011-src/
│   │   └── s1_signal_engine/
│   ├── m0011-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0011-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0011-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0011-config/
│   ├── m0011-scripts/
│   ├── m0011-context/
│   ├── .m0011-state/
│   ├── 50000000000000000011_S1_SIGNAL_ENGINE.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0012-s2-intent-builder/
│   ├── .module-id
│   ├── m0012-src/
│   │   └── s2_intent_builder/
│   ├── m0012-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0012-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0012-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0012-config/
│   ├── m0012-scripts/
│   ├── m0012-context/
│   ├── .m0012-state/
│   ├── 50000000000000000012_S2_INTENT_BUILDER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0013-r1-risk-evaluator/
│   ├── .module-id
│   ├── m0013-src/
│   │   └── r1_risk_evaluator/
│   ├── m0013-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0013-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0013-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0013-config/
│   ├── m0013-scripts/
│   ├── m0013-context/
│   ├── .m0013-state/
│   ├── 50000000000000000013_R1_RISK_EVALUATOR.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0014-r2-order-intent-compiler/
│   ├── .module-id
│   ├── m0014-src/
│   │   └── r2_order_intent_compiler/
│   ├── m0014-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0014-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0014-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0014-config/
│   ├── m0014-scripts/
│   ├── m0014-context/
│   ├── .m0014-state/
│   ├── 50000000000000000014_R2_ORDER_INTENT_COMPILER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0015-o1-order-router/
│   ├── .module-id
│   ├── m0015-src/
│   │   └── o1_order_router/
│   ├── m0015-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0015-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0015-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0015-config/
│   ├── m0015-scripts/
│   ├── m0015-context/
│   ├── .m0015-state/
│   ├── 50000000000000000015_O1_ORDER_ROUTER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0016-b1-mt4-adapter-transport/
│   ├── .module-id
│   ├── m0016-src/
│   │   ├── python/
│   │   ├── Experts/
│   │   ├── Indicators/
│   │   └── Include/
│   ├── m0016-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0016-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0016-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0016-config/
│   ├── m0016-scripts/
│   ├── m0016-context/
│   ├── .m0016-state/
│   ├── 50000000000000000016_B1_MT4_ADAPTER_TRANSPORT.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0017-b2-mt4-ea-executor/
│   ├── .module-id
│   ├── m0017-src/
│   │   ├── Experts/
│   │   ├── Indicators/
│   │   └── Include/
│   ├── m0017-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0017-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0017-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0017-config/
│   ├── m0017-scripts/
│   ├── m0017-context/
│   ├── .m0017-state/
│   ├── 50000000000000000017_B2_MT4_EA_EXECUTOR.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0018-b3-exec-event-normalizer/
│   ├── .module-id
│   ├── m0018-src/
│   │   └── b3_exec_event_normalizer/
│   ├── m0018-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0018-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0018-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0018-config/
│   ├── m0018-scripts/
│   ├── m0018-context/
│   ├── .m0018-state/
│   ├── 50000000000000000018_B3_EXEC_EVENT_NORMALIZER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0019-o2-oms-state-machine/
│   ├── .module-id
│   ├── m0019-src/
│   │   └── o2_oms_state_machine/
│   ├── m0019-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0019-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0019-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0019-config/
│   ├── m0019-scripts/
│   ├── m0019-context/
│   ├── .m0019-state/
│   ├── 50000000000000000019_O2_OMS_STATE_MACHINE.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0020-o3-trade-close-classifier/
│   ├── .module-id
│   ├── m0020-src/
│   │   └── o3_trade_close_classifier/
│   ├── m0020-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0020-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0020-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0020-config/
│   ├── m0020-scripts/
│   ├── m0020-context/
│   ├── .m0020-state/
│   ├── 50000000000000000020_O3_TRADE_CLOSE_CLASSIFIER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0021-e1-outcome-bucketizer/
│   ├── .module-id
│   ├── m0021-src/
│   │   └── e1_outcome_bucketizer/
│   ├── m0021-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0021-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0021-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0021-config/
│   ├── m0021-scripts/
│   ├── m0021-context/
│   ├── .m0021-state/
│   ├── 50000000000000000021_E1_OUTCOME_BUCKETIZER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0022-e2-proximity-evaluator/
│   ├── .module-id
│   ├── m0022-src/
│   │   └── e2_proximity_evaluator/
│   ├── m0022-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0022-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0022-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0022-config/
│   ├── m0022-scripts/
│   ├── m0022-context/
│   ├── .m0022-state/
│   ├── 50000000000000000022_E2_PROXIMITY_EVALUATOR.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0023-e3-matrix-lookup/
│   ├── .module-id
│   ├── m0023-src/
│   │   └── e3_matrix_lookup/
│   ├── m0023-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0023-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0023-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0023-config/
│   ├── m0023-scripts/
│   ├── m0023-context/
│   ├── .m0023-state/
│   ├── 50000000000000000023_E3_MATRIX_LOOKUP.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0024-e4-reentry-intent-builder/
│   ├── .module-id
│   ├── m0024-src/
│   │   └── e4_reentry_intent_builder/
│   ├── m0024-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0024-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0024-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0024-config/
│   ├── m0024-scripts/
│   ├── m0024-context/
│   ├── .m0024-state/
│   ├── 50000000000000000024_E4_REENTRY_INTENT_BUILDER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0025-f4-flow-orchestrator/
│   ├── .module-id
│   ├── m0025-src/
│   │   └── f4_flow_orchestrator/
│   ├── m0025-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0025-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0025-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0025-config/
│   ├── m0025-scripts/
│   ├── m0025-context/
│   ├── .m0025-state/
│   ├── 50000000000000000025_F4_FLOW_ORCHESTRATOR.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0026-p1-health-aggregator/
│   ├── .module-id
│   ├── m0026-src/
│   │   └── p1_health_aggregator/
│   ├── m0026-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0026-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0026-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0026-config/
│   ├── m0026-scripts/
│   ├── m0026-context/
│   ├── .m0026-state/
│   ├── 50000000000000000026_P1_HEALTH_AGGREGATOR.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0027-r3-correlation-guard/
│   ├── .module-id
│   ├── m0027-src/
│   │   └── r3_correlation_guard/
│   ├── m0027-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0027-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0027-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0027-config/
│   ├── m0027-scripts/
│   ├── m0027-context/
│   ├── .m0027-state/
│   ├── 50000000000000000027_R3_CORRELATION_GUARD.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0028-u1-dashboard-backend/
│   ├── .module-id
│   ├── m0028-src/
│   │   └── u1_dashboard_backend/
│   ├── m0028-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0028-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0028-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0028-config/
│   ├── m0028-scripts/
│   ├── m0028-context/
│   ├── .m0028-state/
│   │   ├── rest/
│   │   └── websocket/
│   ├── 50000000000000000028_U1_DASHBOARD_BACKEND.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0029-u2-gui-gateway/
│   ├── .module-id
│   ├── m0029-src/
│   │   └── u2_gui_gateway/
│   ├── m0029-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0029-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0029-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0029-config/
│   ├── m0029-scripts/
│   ├── m0029-context/
│   ├── .m0029-state/
│   │   ├── rest/
│   │   └── websocket/
│   ├── 50000000000000000029_U2_GUI_GATEWAY.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0030-u3-mt4-expiry-overlay/
│   ├── .module-id
│   ├── m0030-src/
│   │   ├── Experts/
│   │   ├── Indicators/
│   │   └── Include/
│   ├── m0030-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0030-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0030-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0030-config/
│   ├── m0030-scripts/
│   ├── m0030-context/
│   ├── .m0030-state/
│   ├── 50000000000000000030_U3_MT4_EXPIRY_OVERLAY.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0031-u4-desktop-operator/
│   ├── .module-id
│   ├── m0031-src/
│   │   ├── backend/
│   │   └── frontend/
│   ├── m0031-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0031-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0031-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0031-config/
│   ├── m0031-scripts/
│   ├── m0031-context/
│   ├── .m0031-state/
│   ├── 50000000000000000031_U4_DESKTOP_OPERATOR.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0032-p2-reporter/
│   ├── .module-id
│   ├── m0032-src/
│   │   └── p2_reporter/
│   ├── m0032-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0032-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0032-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0032-config/
│   ├── m0032-scripts/
│   ├── m0032-context/
│   ├── .m0032-state/
│   ├── m0032-templates/
│   ├── 50000000000000000032_P2_REPORTER.manifest.json
│   ├── AGENTS.md
│   └── README.md
├── m0033-sk1-plugin-interface/
│   ├── .module-id
│   ├── m0033-src/
│   │   └── sk1_plugin_interface/
│   ├── m0033-tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── contract/
│   │   └── acceptance/
│   ├── m0033-docs/
│   │   ├── architecture/
│   │   ├── decisions/
│   │   ├── runbook/
│   │   └── failure-modes/
│   ├── m0033-schemas/
│   │   ├── inputs/
│   │   ├── outputs/
│   │   └── examples/
│   ├── m0033-config/
│   ├── m0033-scripts/
│   ├── m0033-context/
│   ├── .m0033-state/
│   ├── m0033-examples/
│   ├── 50000000000000000033_SK1_PLUGIN_INTERFACE.manifest.json
│   ├── AGENTS.md
│   └── README.md
└── m0034-sk2-idempotency/
    ├── .module-id
    ├── m0034-src/
    │   └── sk2_idempotency/
    ├── m0034-tests/
    │   ├── unit/
    │   ├── integration/
    │   ├── contract/
    │   └── acceptance/
    ├── m0034-docs/
    │   ├── architecture/
    │   ├── decisions/
    │   ├── runbook/
    │   └── failure-modes/
    ├── m0034-schemas/
    │   ├── inputs/
    │   ├── outputs/
    │   └── examples/
    ├── m0034-config/
    ├── m0034-scripts/
    ├── m0034-context/
    ├── .m0034-state/
    ├── 50000000000000000034_SK2_IDEMPOTENCY.manifest.json
    ├── AGENTS.md
    └── README.md
│
├── architecture/
├── contracts/
├── governance/
├── integration-tests/
├── tools/
├── EAFIX_auth_docs/
├── .github/
├── .state/
├── eafix_project_knowledge_reference_routing_instructions.json
├── README.md
└── pyproject.toml
```

## Migration-use constraints

1. This is a proposed target tree, not evidence that these folders already exist.
2. The 34-module authority must be repaired or replaced before renaming.
3. The `M0001`–`M0034` locator mapping must be ratified explicitly.
4. A per-module container inventory must confirm optional containers.
5. Every existing repository path must be mapped to exactly one proposed destination.
6. Runtime, packaging, CI, test, documentation, PowerShell, Docker, and MT4 path references must be updated through an approved rename map.
7. Pilot migrations must precede repository-wide movement.
8. Naming validation begins report-only and becomes blocking after a clean baseline.

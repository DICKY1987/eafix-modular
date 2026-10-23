# R1_RISK_EVALUATOR Context Packet

Module ID: `50000000000000000013`
Module name: `Risk Evaluator`
File scope resolution: `canonical_module_mapping`

Use this packet as derived AI context only. Canonical documents listed in `required_reference_documents` remain authoritative.

## Required Documents
- `DOC_ALIGNED_PROCESS`
- `DOC_ATOMIC_LIFECYCLE_MD`
- `DOC_DECOMPOSITION_MODEL`
- `DOC_FILE_MODULE_MAPPING`
- `DOC_MODULE_CATALOG`
- `DOC_MT4_AUTHORITATIVE_REF`
- `DOC_PROCESS_STEP_CATALOG`
- `DOC_ROUTING_INSTRUCTIONS`
- `DOC_SERVICES_AI_REFERENCE`

## Allowed Files
- `services\risk-manager\src\2099900183260118_plugin.py`

## Test Files
- `services\risk-manager\tests\2099900184260118_test_risk_manager_plugin.py`

## Work Cells
- `R1_1_POSITION_LIMIT_CHECKS`
- `R1_2_PORTFOLIO_EXPOSURE_CHECKS`
- `R1_3_MARGIN_FREE_MARGIN_CHECKS`
- `R1_4_CORRELATION_GUARDS`
- `R1_5_SPREAD_SLIPPAGE_GUARDS`
- `R1_6_CIRCUIT_BREAKERS`
- `R1_7_IDEMPOTENCY_DUPLICATE_ORDER_PREVENTION`
- `R1_8_DETERMINISTIC_SIZING_ENGINE`
- `R1_9_RISK_DECISION_ASSEMBLER`

# Order Intent Compiler (R2_ORDER_INTENT_COMPILER)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000014` &nbsp;|&nbsp; **Kind:** `RISK_MODULE` &nbsp;|&nbsp; **Domain:** Risk (G4) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 14: Compile order intent.

## Process binding

Owns process step **S14: Compile order intent** (step 14 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_F -- ORDER INTENT COMPILATION).

## Scope

**In scope:**
- RiskDecision
- ResolvedConfig

**Out of scope / produces:**
- OrderIntent

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** RiskDecision, ResolvedConfig
**Produces:** OrderIntent

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `R1_RISK_EVALUATOR` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0014-r2-order-intent-compiler`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (0):**
(none yet -- see shared_files below; this module's code has not been physically split out of a shared service directory)

**Shared / not-yet-refactored files this module depends on (10):**
- services/transport-router/src/2099900197260118_config.py
- services/transport-router/src/2099900198260118_health.py
- services/transport-router/src/2099900199260118_main.py
- services/transport-router/src/2099900200260118_metrics.py
- services/transport-router/src/2099900201260118_plugin.py
- services/transport-router/src/2099900202260118_router.py
- services/transport-router/src/2099900203260118_validator.py
- services/transport-router/src/2099900204260118_watcher.py
- services/transport-router/src/2099900205260118___init__.py
- services/transport-router/tests/2099900206260118_test_integration.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `active` on `localhost:8087`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

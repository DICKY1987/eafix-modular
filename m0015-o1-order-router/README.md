# Order Router (O1_ORDER_ROUTER)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000015` &nbsp;|&nbsp; **Kind:** `OMS_MODULE` &nbsp;|&nbsp; **Domain:** Order Management (G5) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 15: Route order to broker.

## Process binding

Owns process step **S15: Route order to broker** (step 15 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_G -- ORDER ROUTING -> TRANSPORT -> EA EXECUTION).

## Scope

**In scope:**
- OrderIntent
- BrokerPolicy
- ResolvedConfig

**Out of scope / produces:**
- RoutedOrderIntent

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** OrderIntent, BrokerPolicy, ResolvedConfig
**Produces:** RoutedOrderIntent

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `R2_ORDER_INTENT_COMPILER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0015-o1-order-router`
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
- Runtime: `unknown` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

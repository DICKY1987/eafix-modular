# MT4 EA Executor (B2_MT4_EA_EXECUTOR)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000017` &nbsp;|&nbsp; **Kind:** `INTEGRATION_BRIDGE_MODULE` &nbsp;|&nbsp; **Domain:** MT4 Bridge (G6) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 17: EA executes broker order.

## Process binding

Owns process step **S17: EA executes broker order** (step 17 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_G -- ORDER ROUTING -> TRANSPORT -> EA EXECUTION).

## Scope

**In scope:**
- BrokerOrderEnvelope

**Out of scope / produces:**
- BrokerExecEvent
- EAHealth

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** BrokerOrderEnvelope
**Produces:** BrokerExecEvent, EAHealth

## Dependencies

- `B1_MT4_ADAPTER_TRANSPORT` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0017-b2-mt4-ea-executor`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (1):**
- m0017-b2-mt4-ea-executor/m0017-context/work-cells/EA_SYSTEM_D_EXECUTION_FEEDBACK__MQL4_ORDER_RESULT.json

**Shared / not-yet-refactored files this module depends on (2):**
- services/execution-engine/src/2099900144260118_plugin.py
- services/execution-engine/tests/2099900145260118_test_execution_engine_plugin.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `active` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

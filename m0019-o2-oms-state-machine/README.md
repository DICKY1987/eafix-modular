# OMS State Machine (O2_OMS_STATE_MACHINE)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000019` &nbsp;|&nbsp; **Kind:** `OMS_MODULE` &nbsp;|&nbsp; **Domain:** Order Management (G5) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 19: Apply execution reports to OMS state.

## Process binding

Owns process step **S19: Apply execution reports to OMS state** (step 19 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_I -- OMS -> TRADE CLOSE -> REENTRY DECISION).

## Scope

**In scope:**
- RoutedOrderIntent
- ExecutionReport
- PositionSnapshot
- ResolvedConfig

**Out of scope / produces:**
- OrderStateChanged
- PositionStateChanged
- TradeClosedRaw

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** RoutedOrderIntent, ExecutionReport, PositionSnapshot, ResolvedConfig
**Produces:** OrderStateChanged, PositionStateChanged, TradeClosedRaw

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `O1_ORDER_ROUTER` (consumes_output, declared_output_contract_only)
- `B3_EXEC_EVENT_NORMALIZER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0019-o2-oms-state-machine`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (0):**
(none yet -- see shared_files below; this module's code has not been physically split out of a shared service directory)

**Shared / not-yet-refactored files this module depends on (2):**
- services/execution-engine/src/2099900144260118_plugin.py
- services/execution-engine/tests/2099900145260118_test_execution_engine_plugin.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `unknown` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

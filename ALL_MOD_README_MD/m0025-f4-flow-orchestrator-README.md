# Flow Orchestrator (F4_FLOW_ORCHESTRATOR)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000025` &nbsp;|&nbsp; **Kind:** `INFRA_PLATFORM_MODULE` &nbsp;|&nbsp; **Domain:** Infrastructure Platform (G0) &nbsp;|&nbsp; **Layer:** 1

## Purpose

Owns process step 25: Loop: reentry intent follows same risk->order->route->transport->execute chain.

## Process binding

Owns process step **S25: Loop: reentry intent follows same risk->order->route->transport->execute chain** (step 25 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_J -- ORCHESTRATION + HEALTH & SLO).

## Scope

**In scope:**
- TradeIntent

**Out of scope / produces:**
- Either
- RoutedOrderIntent
- OutcomeBucket

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** TradeIntent
**Produces:** Either, RoutedOrderIntent, OutcomeBucket

## Dependencies

- `S2_INTENT_BUILDER` (consumes_output, declared_output_contract_only)
- `E4_REENTRY_INTENT_BUILDER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0025-f4-flow-orchestrator`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (0):**
(none yet -- see shared_files below; this module's code has not been physically split out of a shared service directory)

**Shared / not-yet-refactored files this module depends on (12):**
- services/flow-monitor/src/2099900146260118_config.py
- services/flow-monitor/src/2099900147260118_monitor.py
- services/telemetry-daemon/src/2099900187260118_aggregator.py
- services/telemetry-daemon/src/2099900188260118_alerting.py
- services/telemetry-daemon/src/2099900189260118_collector.py
- services/telemetry-daemon/src/2099900190260118_config.py
- services/telemetry-daemon/src/2099900191260118_health.py
- services/telemetry-daemon/src/2099900192260118_main.py
- services/telemetry-daemon/src/2099900193260118_metrics.py
- services/telemetry-daemon/src/2099900194260118_plugin.py
- services/telemetry-daemon/src/2099900195260118___init__.py
- services/telemetry-daemon/tests/2099900196260118_test_telemetry_daemon.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `active` on `localhost:8088`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

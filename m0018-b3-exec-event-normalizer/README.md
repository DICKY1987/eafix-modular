# Exec Event Normalizer (B3_EXEC_EVENT_NORMALIZER)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000018` &nbsp;|&nbsp; **Kind:** `INTEGRATION_BRIDGE_MODULE` &nbsp;|&nbsp; **Domain:** MT4 Bridge (G6) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 18: Normalize broker events to canonical reports.

## Process binding

Owns process step **S18: Normalize broker events to canonical reports** (step 18 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_H -- BROKER EVENT NORMALIZATION).

## Scope

**In scope:**
- BrokerExecEvent
- ResolvedConfig

**Out of scope / produces:**
- ExecutionReport
- PositionSnapshot

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** BrokerExecEvent, ResolvedConfig
**Produces:** ExecutionReport, PositionSnapshot

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `B2_MT4_EA_EXECUTOR` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `services/event-gateway`
- `service_home`: `services/event-gateway`
- `file_assignment_status`: `complete`

**Owned files (6):**
- services/event-gateway/src/2099900138260118_config.py
- services/event-gateway/src/2099900139260118_gateway.py
- services/event-gateway/src/2099900140260118_health.py
- services/event-gateway/src/2099900141260118_main.py
- services/event-gateway/src/2099900142260118_metrics.py
- services/event-gateway/src/2099900143260118_plugin.py

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `unknown` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

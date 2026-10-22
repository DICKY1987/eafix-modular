# Health Aggregator (P1_HEALTH_AGGREGATOR)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000026` &nbsp;|&nbsp; **Kind:** `OBSERVABILITY_REPORTING_MODULE` &nbsp;|&nbsp; **Domain:** Observability (G9) &nbsp;|&nbsp; **Layer:** 1

## Purpose

Owns process step 26: Health aggregation + SLO evaluation.

## Process binding

Owns process step **S26: Health aggregation + SLO evaluation** (step 26 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_J -- ORCHESTRATION + HEALTH & SLO).

## Scope

**In scope:**
- AdapterHealth
- ModuleHealth
- ResolvedConfig

**Out of scope / produces:**
- HealthReport

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** AdapterHealth, ModuleHealth, ResolvedConfig
**Produces:** HealthReport

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `services/flow-monitor`
- `service_home`: `services/flow-monitor`
- `file_assignment_status`: `complete`

**Owned files (12):**
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

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `unknown` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

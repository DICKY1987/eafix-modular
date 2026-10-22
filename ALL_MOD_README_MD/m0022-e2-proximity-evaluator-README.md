# Proximity Evaluator (E2_PROXIMITY_EVALUATOR)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000022` &nbsp;|&nbsp; **Kind:** `REENTRY_MODULE` &nbsp;|&nbsp; **Domain:** Reentry (G7) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 22: Compute event proximity.

## Process binding

Owns process step **S22: Compute event proximity** (step 22 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_I -- OMS -> TRADE CLOSE -> REENTRY DECISION).

## Scope

**In scope:**
- CalendarEvent
- ClockTick
- ResolvedConfig

**Out of scope / produces:**
- EventProximity

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** CalendarEvent, ClockTick, ResolvedConfig
**Produces:** EventProximity

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `D3_CALENDAR_NORMALIZER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0022-e2-proximity-evaluator`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (0):**
(none yet -- see shared_files below; this module's code has not been physically split out of a shared service directory)

**Shared / not-yet-refactored files this module depends on (9):**
- services/reentry-engine/src/2099900163260118_config.py
- services/reentry-engine/src/2099900164260118_decision_client.py
- services/reentry-engine/src/2099900165260118_health.py
- services/reentry-engine/src/2099900166260118_main.py
- services/reentry-engine/src/2099900167260118_metrics.py
- services/reentry-engine/src/2099900168260118_plugin.py
- services/reentry-engine/src/2099900169260118_processor.py
- services/reentry-engine/src/2099900170260118___init__.py
- services/reentry-engine/tests/2099900171260118_test_integration.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `active` on `localhost:8085`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

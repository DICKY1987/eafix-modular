# Event Log (F2_EVENT_LOG)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000005` &nbsp;|&nbsp; **Kind:** `INFRA_PLATFORM_MODULE` &nbsp;|&nbsp; **Domain:** Infrastructure Platform (G0) &nbsp;|&nbsp; **Layer:** 1

## Purpose

Owns process step 5: Persist calendar events (append-only).

## Process binding

Owns process step **S05: Persist calendar events (append-only)** (step 5 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_B -- ECONOMIC CALENDAR INTAKE -> TRIGGERS).

## Scope

**In scope:**
- CalendarEvent

**Out of scope / produces:**
- EventStream

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** CalendarEvent
**Produces:** EventStream

## Dependencies

- `D3_CALENDAR_NORMALIZER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0005-f2-event-log`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (0):**
(none yet -- see shared_files below; this module's code has not been physically split out of a shared service directory)

**Shared / not-yet-refactored files this module depends on (8):**
- services/calendar-ingestor/src/2099900089260118_config.py
- services/calendar-ingestor/src/2099900091260118_health.py
- services/calendar-ingestor/src/2099900092260118_ingestor.py
- services/calendar-ingestor/src/2099900093260118_main.py
- services/calendar-ingestor/src/2099900094260118_metrics.py
- services/calendar-ingestor/src/2099900095260118_plugin.py
- services/calendar-ingestor/src/2099900098260118___init__.py
- services/calendar-ingestor/tests/2099900099260118_test_ingestor.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `active` on `localhost:8084`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

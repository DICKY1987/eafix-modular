# Calendar Source Adapter (D2_CALENDAR_SOURCE_ADAPTER)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000003` &nbsp;|&nbsp; **Kind:** `INTEGRATION_BRIDGE_MODULE` &nbsp;|&nbsp; **Domain:** Data Ingest (G1) &nbsp;|&nbsp; **Layer:** 2

## Purpose

Owns process step 3: Poll calendar source(s).

## Process binding

Owns process step **S03: Poll calendar source(s)** (step 3 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_B -- ECONOMIC CALENDAR INTAKE -> TRIGGERS).

## Scope

**In scope:**
- CalendarSourceConfig
- ScheduleTick

**Out of scope / produces:**
- CalendarRaw

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** CalendarSourceConfig, ScheduleTick
**Produces:** CalendarRaw

## Dependencies

- `F3_CLOCK_SCHEDULER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0003-d2-calendar-source-adapter`
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

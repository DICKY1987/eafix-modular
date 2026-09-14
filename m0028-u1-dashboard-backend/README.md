# Dashboard Backend (U1_DASHBOARD_BACKEND)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000028` &nbsp;|&nbsp; **Kind:** `UI_MODULE` &nbsp;|&nbsp; **Domain:** UI Gateway (G8) &nbsp;|&nbsp; **Layer:** 5

## Purpose

Aggregate trading, market, signal, position, calendar, metric, and audit data into UI-friendly REST and streaming responses.

## Process binding

Owns process step **NA: not_applicable** (step 0 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_NOT_APPLICABLE -- not_applicable).

## Scope

**In scope:**
- UI_API_DASHBOARD_AUDIT_Request
- UI_API_DASHBOARD_CALENDAR_Request
- UI_API_DASHBOARD_INDICATOR_CONFIG_Request
- UI_API_DASHBOARD_METRICS_Request
- UI_API_DASHBOARD_POSITIONS_Request
- UI_API_DASHBOARD_SIGNALS_Request
- UI_API_DASHBOARD_SIGNAL_DETAIL_Request
- UI_API_DASHBOARD_TRADES_Request
- UI_WS_DASHBOARD_BACKEND_Subscribe

**Out of scope / produces:**
- UI_API_DASHBOARD_AUDIT_Response
- UI_API_DASHBOARD_CALENDAR_Response
- UI_API_DASHBOARD_INDICATOR_CONFIG_Response
- UI_API_DASHBOARD_METRICS_Response
- UI_API_DASHBOARD_POSITIONS_Response
- UI_API_DASHBOARD_SIGNALS_Response
- UI_API_DASHBOARD_SIGNAL_DETAIL_Response
- UI_API_DASHBOARD_TRADES_Response
- UI_WS_DASHBOARD_BACKEND_Event

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** UI_API_DASHBOARD_AUDIT_Request, UI_API_DASHBOARD_CALENDAR_Request, UI_API_DASHBOARD_INDICATOR_CONFIG_Request, UI_API_DASHBOARD_METRICS_Request, UI_API_DASHBOARD_POSITIONS_Request, UI_API_DASHBOARD_SIGNALS_Request, UI_API_DASHBOARD_SIGNAL_DETAIL_Request, UI_API_DASHBOARD_TRADES_Request, UI_WS_DASHBOARD_BACKEND_Subscribe
**Produces:** UI_API_DASHBOARD_AUDIT_Response, UI_API_DASHBOARD_CALENDAR_Response, UI_API_DASHBOARD_INDICATOR_CONFIG_Response, UI_API_DASHBOARD_METRICS_Response, UI_API_DASHBOARD_POSITIONS_Response, UI_API_DASHBOARD_SIGNALS_Response, UI_API_DASHBOARD_SIGNAL_DETAIL_Response, UI_API_DASHBOARD_TRADES_Response, UI_WS_DASHBOARD_BACKEND_Event

## Dependencies

(none declared)

## File ownership

- `module_root`: `services/dashboard-backend`
- `service_home`: `services/dashboard-backend`
- `file_assignment_status`: `complete`

**Owned files (3):**
- services/dashboard-backend/src/2099900105260118_dashboard_backend.py
- services/dashboard-backend/src/2099900106260118_main.py
- services/dashboard-backend/src/2099900107260118_plugin.py

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `active` on `localhost:8092`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

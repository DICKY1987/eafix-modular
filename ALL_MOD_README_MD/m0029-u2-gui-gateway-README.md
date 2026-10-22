# GUI Gateway (U2_GUI_GATEWAY)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000029` &nbsp;|&nbsp; **Kind:** `UI_MODULE` &nbsp;|&nbsp; **Domain:** UI Gateway (G8) &nbsp;|&nbsp; **Layer:** 5

## Purpose

Expose operator API and real-time UI subscriptions for system status, dashboard summaries, positions, signals, orders, calendar events, and alerts.

## Process binding

Owns process step **NA: not_applicable** (step 0 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_NOT_APPLICABLE -- not_applicable).

## Scope

**In scope:**
- UI_API_GUI_CALENDAR_EVENTS_Request
- UI_API_GUI_DASHBOARD_Request
- UI_API_GUI_LIVE_SIGNALS_Request
- UI_API_GUI_ORDER_HISTORY_Request
- UI_API_GUI_POSITIONS_Request
- UI_API_GUI_SYSTEM_STATUS_Request
- UI_WS_GUI_GATEWAY_Subscribe

**Out of scope / produces:**
- UI_API_GUI_CALENDAR_EVENTS_Response
- UI_API_GUI_DASHBOARD_Response
- UI_API_GUI_LIVE_SIGNALS_Response
- UI_API_GUI_ORDER_HISTORY_Response
- UI_API_GUI_POSITIONS_Response
- UI_API_GUI_SYSTEM_STATUS_Response
- UI_WS_GUI_GATEWAY_Event

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** UI_API_GUI_CALENDAR_EVENTS_Request, UI_API_GUI_DASHBOARD_Request, UI_API_GUI_LIVE_SIGNALS_Request, UI_API_GUI_ORDER_HISTORY_Request, UI_API_GUI_POSITIONS_Request, UI_API_GUI_SYSTEM_STATUS_Request, UI_WS_GUI_GATEWAY_Subscribe
**Produces:** UI_API_GUI_CALENDAR_EVENTS_Response, UI_API_GUI_DASHBOARD_Response, UI_API_GUI_LIVE_SIGNALS_Response, UI_API_GUI_ORDER_HISTORY_Response, UI_API_GUI_POSITIONS_Response, UI_API_GUI_SYSTEM_STATUS_Response, UI_WS_GUI_GATEWAY_Event

## Dependencies

(none declared)

## File ownership

- `module_root`: `services/gui-gateway`
- `service_home`: `services/gui-gateway`
- `file_assignment_status`: `complete`

**Owned files (6):**
- services/gui-gateway/src/2099900155260118_config.py
- services/gui-gateway/src/2099900156260118_main.py
- services/gui-gateway/src/2099900157260118_models.py
- services/gui-gateway/src/2099900158260118_plugin.py
- m0029-u2-gui-gateway/m0029-context/work-cells/UI_GATEWAY_REST_API_GATEWAY.json
- m0029-u2-gui-gateway/m0029-context/work-cells/UI_GATEWAY_WEBSOCKET_GATEWAY.json

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `active` on `localhost:8091`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

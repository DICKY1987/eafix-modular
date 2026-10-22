# Desktop Operator UI (U4_DESKTOP_OPERATOR)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000031` &nbsp;|&nbsp; **Kind:** `UI_MODULE` &nbsp;|&nbsp; **Domain:** UI Gateway (G8) &nbsp;|&nbsp; **Layer:** 5

## Purpose

Provide live trading visibility, signal review, configuration, safety intervention, history, analytics, diagnostics, and reentry controls.

## Process binding

Owns process step **NA: not_applicable** (step 0 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_NOT_APPLICABLE -- not_applicable).

## Scope

**In scope:**
- Desktop_Operator_UI_ClientRequest

**Out of scope / produces:**
- Desktop_Operator_UI_Response

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** Desktop_Operator_UI_ClientRequest
**Produces:** Desktop_Operator_UI_Response

## Dependencies

(none declared)

## File ownership

- `module_root`: `services/desktop-ui`
- `service_home`: `services/desktop-ui`
- `file_assignment_status`: `complete`

**Owned files (8):**
- services/desktop-ui/2099900130260118_friday_vol_indicator.py
- services/desktop-ui/2099900131260118_friday_vol_signal.py
- services/desktop-ui/2099900132260118_outbound.py
- services/desktop-ui/2099900133260118_test_friday_vol_indicator.py
- services/desktop-ui/2099900134260118_test_friday_vol_signal.py
- services/desktop-ui/2099900135260118_tkinter_dashboard_gui.py
- services/desktop-ui/dashboard/2099900136260118_tkinter_dashboard_gui.py
- m0031-u4-desktop-operator/m0031-src/frontend/tkinter_dashboard_gui.py

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `unknown` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

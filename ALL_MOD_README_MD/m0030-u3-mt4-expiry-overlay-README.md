# MT4 Expiry Zones Overlay (U3_MT4_EXPIRY_OVERLAY)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000030` &nbsp;|&nbsp; **Kind:** `UI_MODULE` &nbsp;|&nbsp; **Domain:** UI Gateway (G8) &nbsp;|&nbsp; **Layer:** 5

## Purpose

Display expiry zones, indicator summaries, spot data, and MT4-facing UI data served over local HTTP.

## Process binding

Owns process step **NA: not_applicable** (step 0 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_NOT_APPLICABLE -- not_applicable).

## Scope

**In scope:**
- MT4_Expiry_Zones_Overlay_ClientRequest

**Out of scope / produces:**
- MT4_Expiry_Zones_Overlay_Response

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** MT4_Expiry_Zones_Overlay_ClientRequest
**Produces:** MT4_Expiry_Zones_Overlay_Response

## Dependencies

(none declared)

## File ownership

- `module_root`: `services/desktop-ui`
- `service_home`: `services/desktop-ui`
- `file_assignment_status`: `complete`

**Owned files (2):**
- services/desktop-ui/2099900128260118_expiry_indicator_service.py
- services/desktop-ui/2099900129260118_expiry_service.py

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `unknown` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

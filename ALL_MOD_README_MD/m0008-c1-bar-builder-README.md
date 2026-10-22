# Bar Builder (C1_BAR_BUILDER)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000008` &nbsp;|&nbsp; **Kind:** `COMPUTE_MODULE` &nbsp;|&nbsp; **Domain:** Compute Feature (G2) &nbsp;|&nbsp; **Layer:** 3

## Purpose

Owns process step 8: Aggregate ticks into bars.

## Process binding

Owns process step **S08: Aggregate ticks into bars** (step 8 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_C -- MARKET DATA -> BARS -> INDICATORS).

## Scope

**In scope:**
- MarketTick
- ResolvedConfig

**Out of scope / produces:**
- Bar

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** MarketTick, ResolvedConfig
**Produces:** Bar

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `D1_MARKET_FEED_ADAPTER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0008-c1-bar-builder`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (0):**
(none yet -- see shared_files below; this module's code has not been physically split out of a shared service directory)

**Shared / not-yet-refactored files this module depends on (4):**
- services/indicator-engine/src/2099900159260118_plugin.py
- services/indicator-engine/src/currency_strength/2099900160260118_strength_calculator.py
- services/indicator-engine/src/indicators/2099900161260118_advanced_indicators.py
- services/indicator-engine/tests/2099900162260118_test_indicator_plugin.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `unknown` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

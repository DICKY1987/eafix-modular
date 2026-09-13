# Indicator Engine (C2_INDICATOR_ENGINE)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000009` &nbsp;|&nbsp; **Kind:** `COMPUTE_MODULE` &nbsp;|&nbsp; **Domain:** Compute Feature (G2) &nbsp;|&nbsp; **Layer:** 3

## Purpose

Owns process step 9: Compute indicators.

## Process binding

Owns process step **S09: Compute indicators** (step 9 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_C -- MARKET DATA -> BARS -> INDICATORS).

## Scope

**In scope:**
- Bar
- ResolvedConfig

**Out of scope / produces:**
- IndicatorSnapshot

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** Bar, ResolvedConfig
**Produces:** IndicatorSnapshot

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `C1_BAR_BUILDER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `services/indicator-engine`
- `service_home`: `services/indicator-engine`
- `file_assignment_status`: `complete`

**Owned files (9):**
- services/indicator-engine/src/2099900159260118_plugin.py
- services/indicator-engine/src/currency_strength/2099900160260118_strength_calculator.py
- services/indicator-engine/src/indicators/2099900161260118_advanced_indicators.py
- services/indicator-engine/tests/2099900162260118_test_indicator_plugin.py
- m0009-c2-indicator-engine/m0009-schemas/inputs/1199900011260118_indicator_record.schema.json
- m0009-c2-indicator-engine/m0009-config/indicator_records_full.json
- m0009-c2-indicator-engine/m0009-schemas/examples/indicator_records_sample.json
- m0009-c2-indicator-engine/m0009-src/c2_indicator_engine/advanced_indicators.py
- m0009-c2-indicator-engine/m0009-tests/contract/fixtures/indicator_record_valid.json

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `active` on `localhost:8082`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

# Signal Engine (S1_SIGNAL_ENGINE)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000011` &nbsp;|&nbsp; **Kind:** `SIGNAL_MODULE` &nbsp;|&nbsp; **Domain:** Signal (G3) &nbsp;|&nbsp; **Layer:** 3

## Purpose

Owns process step 11: Generate signal (or suppression).

## Process binding

Owns process step **S11: Generate signal (or suppression)** (step 11 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_E -- SIGNAL -> INTENT -> RISK DECISION).

## Scope

**In scope:**
- FeatureFrame
- PositionSummary
- ResolvedConfig

**Out of scope / produces:**
- Signal
- SignalSuppressed

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** FeatureFrame, PositionSummary, ResolvedConfig
**Produces:** Signal, SignalSuppressed

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `C3_FEATURE_PACKAGER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `services/signal-generator`
- `service_home`: `services/signal-generator`
- `file_assignment_status`: `complete`

**Owned files (4):**
- services/signal-generator/tests/2099900186260118_test_signal_generator_plugin.py
- services/signal-generator/src/2099900185260118_config.py
- services/signal-generator/src/2099900186260118_processor.py
- services/signal-generator/src/2099900187260118_plugin.py

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `active` on `localhost:8083`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

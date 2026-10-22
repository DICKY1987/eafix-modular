# Intent Builder (S2_INTENT_BUILDER)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000012` &nbsp;|&nbsp; **Kind:** `SIGNAL_MODULE` &nbsp;|&nbsp; **Domain:** Signal (G3) &nbsp;|&nbsp; **Layer:** 3

## Purpose

Owns process step 12: Convert signal to trade intent.

## Process binding

Owns process step **S12: Convert signal to trade intent** (step 12 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_E -- SIGNAL -> INTENT -> RISK DECISION).

## Scope

**In scope:**
- Signal
- ResolvedConfig

**Out of scope / produces:**
- TradeIntent

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** Signal, ResolvedConfig
**Produces:** TradeIntent

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `S1_SIGNAL_ENGINE` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0012-s2-intent-builder`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (0):**
(none yet -- see shared_files below; this module's code has not been physically split out of a shared service directory)

**Shared / not-yet-refactored files this module depends on (1):**
- services/signal-generator/tests/2099900186260118_test_signal_generator_plugin.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `unknown` on `n/a:n/a`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

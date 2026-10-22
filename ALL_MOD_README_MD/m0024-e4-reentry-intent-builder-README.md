# Reentry Intent Builder (E4_REENTRY_INTENT_BUILDER)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000024` &nbsp;|&nbsp; **Kind:** `REENTRY_MODULE` &nbsp;|&nbsp; **Domain:** Reentry (G7) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 24: Build reentry trade intent (or suppress).

## Process binding

Owns process step **S24: Build reentry trade intent (or suppress)** (step 24 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_I -- OMS -> TRADE CLOSE -> REENTRY DECISION).

## Scope

**In scope:**
- MatrixDecision
- ReentryChainState
- ResolvedConfig

**Out of scope / produces:**
- TradeIntent
- ReentrySuppressed

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** MatrixDecision, ReentryChainState, ResolvedConfig
**Produces:** TradeIntent, ReentrySuppressed

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `E3_MATRIX_LOOKUP` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `m0024-e4-reentry-intent-builder`
- `service_home`: `(not yet bound)`
- `file_assignment_status`: `partial`

**Owned files (1):**
- m0024-e4-reentry-intent-builder/m0024-context/work-cells/E4_REENTRY_INTENT_BUILDER__CHAIN_LIMITS_AND_SUPPRESSION.json

**Shared / not-yet-refactored files this module depends on (9):**
- services/reentry-engine/src/2099900163260118_config.py
- services/reentry-engine/src/2099900164260118_decision_client.py
- services/reentry-engine/src/2099900165260118_health.py
- services/reentry-engine/src/2099900166260118_main.py
- services/reentry-engine/src/2099900167260118_metrics.py
- services/reentry-engine/src/2099900168260118_plugin.py
- services/reentry-engine/src/2099900169260118_processor.py
- services/reentry-engine/src/2099900170260118___init__.py
- services/reentry-engine/tests/2099900171260118_test_integration.py

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `needs_review`
- Runtime: `active` on `localhost:8085`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

# Matrix Lookup (E3_MATRIX_LOOKUP)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000023` &nbsp;|&nbsp; **Kind:** `REENTRY_MODULE` &nbsp;|&nbsp; **Domain:** Reentry (G7) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 23: Lookup matrix decision.

## Process binding

Owns process step **S23: Lookup matrix decision** (step 23 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_I -- OMS -> TRADE CLOSE -> REENTRY DECISION).

## Scope

**In scope:**
- OutcomeBucket
- EventProximity
- SignalContext
- MatrixProfile
- ResolvedConfig

**Out of scope / produces:**
- MatrixDecision

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** OutcomeBucket, EventProximity, SignalContext, MatrixProfile, ResolvedConfig
**Produces:** MatrixDecision

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `E1_OUTCOME_BUCKETIZER` (consumes_output, declared_output_contract_only)
- `E2_PROXIMITY_EVALUATOR` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `services/reentry-matrix-svc`
- `service_home`: `services/reentry-matrix-svc`
- `file_assignment_status`: `complete`

**Owned files (12):**
- services/reentry-matrix-svc/src/2099900172260118_config.py
- services/reentry-matrix-svc/src/2099900173260118_health.py
- services/reentry-matrix-svc/src/2099900174260118_main.py
- services/reentry-matrix-svc/src/2099900175260118_metrics.py
- services/reentry-matrix-svc/src/2099900176260118_plugin.py
- services/reentry-matrix-svc/src/2099900177260118_processor.py
- services/reentry-matrix-svc/src/2099900178260118_resolver.py
- services/reentry-matrix-svc/src/2099900179260118___init__.py
- services/reentry-matrix-svc/tests/2099900180260118_test_processor.py
- m0023-e3-matrix-lookup/m0023-docs/architecture/0110000074260118_06_signal_model_mapping.md
- m0023-e3-matrix-lookup/m0023-config/reentry_vocab.json
- m0023-e3-matrix-lookup/m0023-tests/contract/test_hybrid_id_parity.py

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `active` on `localhost:8085`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

# Risk Evaluator (R1_RISK_EVALUATOR)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000013` &nbsp;|&nbsp; **Kind:** `RISK_MODULE` &nbsp;|&nbsp; **Domain:** Risk (G4) &nbsp;|&nbsp; **Layer:** 4

## Purpose

Owns process step 13: Evaluate risk and size.

## Process binding

Owns process step **S13: Evaluate risk and size** (step 13 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_E -- SIGNAL -> INTENT -> RISK DECISION).

## Scope

**In scope:**
- TradeIntent
- PortfolioState
- RiskPolicy
- ResolvedConfig

**Out of scope / produces:**
- RiskDecision

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** TradeIntent, PortfolioState, RiskPolicy, ResolvedConfig, RiskGuardResult
**Produces:** RiskDecision

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)
- `S2_INTENT_BUILDER` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `services/risk-manager`
- `service_home`: `services/risk-manager`
- `file_assignment_status`: `complete`

**Owned files (2):**
- services/risk-manager/src/2099900183260118_plugin.py
- services/risk-manager/tests/2099900184260118_test_risk_manager_plugin.py

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `active` on `localhost:8087`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

# Market Feed Adapter (D1_MARKET_FEED_ADAPTER)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-07-02T15:52:15.513625+00:00.
> This file is a human-readable projection of the manifest. If the two ever disagree, `manifest.json` is authoritative --
> edit the manifest and regenerate this file, don't edit this file by hand and let it drift.

**Module ID:** `50000000000000000007` &nbsp;|&nbsp; **Kind:** `INTEGRATION_BRIDGE_MODULE` &nbsp;|&nbsp; **Domain:** Data Ingest (G1) &nbsp;|&nbsp; **Layer:** 2

## Purpose

Owns process step 7: Ingest market ticks.

## Process binding

Owns process step **S07: Ingest market ticks** (step 7 of `HUEY_P_EAFIX_END_TO_END`, phase PHASE_C -- MARKET DATA -> BARS -> INDICATORS).

## Scope

**In scope:**
- RawTick
- ResolvedConfig

**Out of scope / produces:**
- MarketTick

**Forbidden responsibilities:**
- cross_module_private_state_access

## Contracts

**Consumes:** RawTick, ResolvedConfig
**Produces:** MarketTick

## Dependencies

- `F1_CONFIG_PREFERENCES` (consumes_output, declared_output_contract_only)

## File ownership

- `module_root`: `services/data-ingestor`
- `service_home`: `services/data-ingestor`
- `file_assignment_status`: `complete`

**Owned files (12):**
- services/data-ingestor/src/2099900109260118_config.py
- services/data-ingestor/src/2099900110260118_health.py
- services/data-ingestor/src/2099900111260118_ingestor.py
- services/data-ingestor/src/2099900112260118_main.py
- services/data-ingestor/src/2099900113260118_main_enterprise.py
- services/data-ingestor/src/2099900114260118_metrics.py
- services/data-ingestor/src/2099900115260118_models.py
- services/data-ingestor/src/2099900116260118_plugin.py
- services/data-ingestor/tests/integration/2099900117260118___init__.py
- services/data-ingestor/tests/unit/2099900118260118_test_data_ingestor_enterprise.py
- services/data-ingestor/tests/unit/2099900119260118_test_data_ingestor_service.py
- services/data-ingestor/tests/unit/2099900120260118___init__.py

**Shared / not-yet-refactored files this module depends on (0):**
(none)

## Status

- Identity: `canonical` (v1.0.0)
- Service binding: `bound`
- Runtime: `active` on `localhost:8081`

See `manifest.json` in this directory for the complete, authoritative record (contracts, gates, staleness policy, etc.).

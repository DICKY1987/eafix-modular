# ALVT Pilot Trigger Selection

**Created:** 2026-01-23T18:44:00Z  
**Status:** Phase 0 - Scope Locked

## Pilot Trigger Selection

**Selected Trigger ID:** `FILE_IDENTITY_CREATE`

### Rationale
- Clear, atomic operation (file identity allocation)
- Well-defined inputs (file path, metadata)
- Well-defined outputs (16-digit ID, registry entry)
- Existing reference implementation to verify against
- Minimal external dependencies

## Definition of Done (DoD) Checklist

### Phase 0: Assumptions & Scope Lock
- [x] Pilot trigger_id locked (`FILE_IDENTITY_CREATE`)
- [x] DoD checklist written and stored
- [x] Repository directories created (`contracts/`, `tools/alvt/`, `reports/alvt/`, `tests/`)

### Phase 1: Architecture & Plan
- [ ] Architecture doc committed (`automation_verification_architecture.md`)
- [ ] Workspace-safe rule explicit (no global writes during tests)
- [ ] Compile check passes (`python -m compileall src tools`)

### Phase 2: Contract/Interfaces
- [ ] `contracts/triggers/trigger_contract_template.yaml` exists
- [ ] `contracts/triggers/trigger.FILE_IDENTITY_CREATE.yaml` exists and validates
- [ ] Contract validator tool created (`tools/alvt/validate_contract.py`)
- [ ] Contract validation passes (exit 0)

### Phase 3: Implementation (Test-First)
- [ ] `tools/alvt/layer0_static.py` implemented (outputs `reports/alvt/static.<trigger>.json`)
- [ ] `tools/alvt/layer1_graph.py` implemented (outputs `reports/alvt/graph.<trigger>.json`)
- [ ] `tests/test_alvt_layer0.py` created and runnable
- [ ] `tests/test_alvt_layer1.py` created and runnable
- [ ] Evidence query helpers implemented
- [ ] Run-level events emitted
- [ ] Registry path policy: workspace-relative in tests

### Phase 4: Validation Gates (Fix-Validate-Repeat)
- [ ] `reports/alvt/static.FILE_IDENTITY_CREATE.json` with status=PASS
- [ ] `reports/alvt/graph.FILE_IDENTITY_CREATE.json` with status=PASS
- [ ] Issue log created (`alvt_pilot_findings.md`)
- [ ] Two consecutive runs PASS without changes

### Phase 5: Packaging & Runbooks
- [ ] CLI wrapper: `tools/alvt/alvt_cli.py` created
- [ ] Runbook: `run_alvt_pilot.md` documented
- [ ] Template: `new_trigger_checklist.md` created

### Phase 6: Final Completion
- [ ] Pilot declared stable baseline (L0/L1 proven)
- [ ] `pilot_baseline_locked.md` created
- [ ] `layer2_plus_backlog.md` created (deferred implementation)

## Scope Boundaries

### In Scope
- ONE trigger pilot: `FILE_IDENTITY_CREATE`
- ALVT Layer 0 (static integrity): file existence, config validity, stub detection
- ALVT Layer 1 (graph connectivity): node/edge verification
- ACC table generation and reconciliation
- Fix loop until L0+L1 pass repeatedly
- Pytest test coverage for verification tools

### Out of Scope (Explicitly Deferred)
- ALVT Layer 2+ (plan determinism, sandbox execution, negative paths, idempotency)
- Multiple trigger conversion
- Self-healing auto-fix PR pipeline
- Full automation orchestration (separate from verification)

## Exit Criteria for Phase 0
- [x] Pilot trigger ID chosen and documented
- [x] DoD checklist accepted as internal target
- [x] Directory footprint established
- [x] Validation gate passed: `python -c "print('scope_locked')"` → exit 0

**Phase 0 Status:** ✅ COMPLETE

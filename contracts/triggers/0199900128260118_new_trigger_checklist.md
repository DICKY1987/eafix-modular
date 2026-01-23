# New Trigger Checklist
# doc_id: 0199900128260118

**Created:** 2026-01-23T19:06:00Z  
**Version:** 1.0  

## Purpose

This checklist guides the process of adding a new automation trigger to the ALVT verification system after the FILE_IDENTITY_CREATE pilot has been completed and frozen as the baseline.

## Prerequisites

- [ ] FILE_IDENTITY_CREATE pilot baseline is frozen (Phase 6 complete)
- [ ] ALVT tools are installed and working
- [ ] You have identified the trigger to add (trigger ID, purpose, scope)

---

## Step 1: Trigger Identification

### 1.1 Define Trigger Identity
- [ ] Trigger ID chosen (e.g., `FILE_METADATA_UPDATE`, `REGISTRY_WRITE`, `GIT_COMMIT_AUTO`)
- [ ] Trigger purpose documented (1-2 sentences)
- [ ] Trigger owner/responsible team identified
- [ ] Trigger dependencies identified (other triggers, services, tools)

### 1.2 Scope Definition
- [ ] Inputs defined (what events/data trigger this automation?)
- [ ] Outputs defined (what artifacts/changes does this produce?)
- [ ] Side effects documented (what else changes when this runs?)
- [ ] Idempotency policy decided (run-once, safe-rerun, conditional)
- [ ] Rollback strategy defined (if applicable)

---

## Step 2: Contract Creation

### 2.1 Create Contract File
- [ ] Copy template: `cp contracts/triggers/0199900117260118_trigger_contract_template.yaml contracts/triggers/trigger.<TRIGGER_ID>.yaml`
- [ ] Assign doc_id to new contract file
- [ ] Rename file to include doc_id: `<doc_id>_trigger.<TRIGGER_ID>.yaml`

### 2.2 Populate Contract Metadata
- [ ] Fill `metadata.trigger_id` with your trigger ID
- [ ] Fill `metadata.description` with purpose
- [ ] Fill `metadata.created_utc` with current timestamp
- [ ] Fill `metadata.owner` with team/module name
- [ ] Fill `metadata.doc_id` with assigned doc_id

### 2.3 Define Required Files
- [ ] List entrypoint file (where trigger is detected/received)
- [ ] List dispatcher file (routing logic)
- [ ] List handler file (core automation logic)
- [ ] List gate files (validation/preconditions)
- [ ] List evidence files (logging/recording)
- [ ] List config files (configuration)

### 2.4 Define Required Config Keys
- [ ] List all config keys used by trigger
- [ ] Document expected types for each key
- [ ] Document purpose/description for each key

### 2.5 Define Required Nodes
- [ ] Identify entrypoint class/function
- [ ] Identify dispatcher class/function/method
- [ ] Identify handler class/function/method
- [ ] Identify gate functions/methods
- [ ] Identify evidence recording functions
- [ ] Document location for each node (file::class::method format)

### 2.6 Define Required Edges
- [ ] Map entrypoint → dispatcher edge
- [ ] Map dispatcher → handler edge
- [ ] Map handler → gate edges
- [ ] Map handler → evidence edges
- [ ] Document edge types (calls, imports, triggers, emits)

### 2.7 Define Forbidden Patterns
- [ ] Include standard patterns (TODO, FIXME, NotImplementedError, stubs)
- [ ] Add trigger-specific forbidden patterns if needed

### 2.8 Define Completion Gates
- [ ] List all Layer 0 gates (file existence, config keys, no forbidden patterns)
- [ ] List all Layer 1 gates (nodes exist, edges exist, no orphans)
- [ ] Document which layer verifies each gate

### 2.9 Optional Sections
- [ ] Add evidence requirements (if specific evidence format needed)
- [ ] Add idempotency section (if Layer 5 verification planned)
- [ ] Add rollback section (if Layer 4 verification planned)
- [ ] Add dependencies section (if trigger depends on others)

---

## Step 3: Contract Validation

### 3.1 Run Validator
- [ ] Run: `python tools/alvt/2099900119260118_validate_contract.py --trigger <TRIGGER_ID>`
- [ ] Exit code is 0
- [ ] Output says "VALID"

### 3.2 Fix Validation Errors
If validation fails:
- [ ] Review error messages
- [ ] Check YAML syntax
- [ ] Verify all required sections present
- [ ] Ensure edges reference declared nodes
- [ ] Ensure file paths are resolvable (or document as expected to be created)
- [ ] Re-run validator until PASS

---

## Step 4: Layer 0 Verification

### 4.1 Run Layer 0
- [ ] Run: `python tools/alvt/2099900121260118_layer0_static.py --trigger <TRIGGER_ID>`
- [ ] Review report: `reports/alvt/static.<TRIGGER_ID>.json`

### 4.2 Analyze Layer 0 Results
- [ ] Check `status` field (PASS or FAIL)
- [ ] Review failed checks (if any)
- [ ] For each failed `file_exists_*` check: Verify file path is correct or create missing file
- [ ] For each failed `config_exists_*` check: Add missing config key or update contract
- [ ] For each failed `no_pattern_*` check: Remove forbidden pattern from code

### 4.3 Fix-Validate Loop
- [ ] Apply fixes for any failures
- [ ] Re-run Layer 0 verification
- [ ] Repeat until status is PASS
- [ ] Document any issues in findings log

---

## Step 5: Layer 1 Verification

### 5.1 Run Layer 1
- [ ] Run: `python tools/alvt/2099900122260118_layer1_graph.py --trigger <TRIGGER_ID>`
- [ ] Review report: `reports/alvt/graph.<TRIGGER_ID>.json`

### 5.2 Analyze Layer 1 Results
- [ ] Check `status` field (PASS or FAIL)
- [ ] Review failed checks (if any)
- [ ] For each failed `node_exists_*` check: Verify node location is correct or implement missing node
- [ ] For each failed `edge_exists_*` check: Verify call relationship exists or add missing wiring

### 5.3 Fix-Validate Loop
- [ ] Apply fixes for any failures
- [ ] Re-run Layer 1 verification
- [ ] Repeat until status is PASS
- [ ] Document any issues in findings log

---

## Step 6: Stability Verification

### 6.1 Consecutive Run Test
- [ ] Run Layer 0 twice consecutively (no changes between runs)
- [ ] Run Layer 1 twice consecutively (no changes between runs)
- [ ] Verify both runs produce identical check results (excluding timestamps)

### 6.2 Document Results
- [ ] Create findings log: `reports/alvt/<doc_id>_alvt_<trigger_id>_findings.md`
- [ ] Document any issues encountered and resolutions applied
- [ ] Document known limitations or placeholder implementations
- [ ] Document stability verification results

---

## Step 7: Test Coverage (Optional but Recommended)

### 7.1 Create Trigger-Specific Tests
- [ ] Create test file: `tests/test_alvt_<trigger_id>.py`
- [ ] Write tests for trigger-specific contract validation
- [ ] Write tests for trigger-specific Layer 0 checks
- [ ] Write tests for trigger-specific Layer 1 checks

### 7.2 Run Tests
- [ ] Run: `pytest tests/test_alvt_<trigger_id>.py -v`
- [ ] All tests pass

---

## Step 8: Documentation

### 8.1 Update Registry (if applicable)
- [ ] Add trigger contract to documentation registry
- [ ] Add ALVT reports to evidence registry
- [ ] Update trigger inventory/catalog

### 8.2 Create Runbook (Optional)
- [ ] Create trigger-specific runbook: `contracts/triggers/<doc_id>_run_alvt_<trigger_id>.md`
- [ ] Document exact commands for verification
- [ ] Document expected outputs
- [ ] Document troubleshooting steps

### 8.3 Update Architecture Docs
- [ ] Add trigger to automation architecture diagram (if exists)
- [ ] Document trigger in system overview docs

---

## Step 9: Commit and Push

### 9.1 Git Operations
- [ ] Stage changes: `git add contracts/triggers/ reports/alvt/ tests/`
- [ ] Commit: `git commit -m "Add ALVT contract for <TRIGGER_ID> - Layer 0/1 PASS"`
- [ ] Push: `git push origin HEAD`

### 9.2 Verification
- [ ] Verify commit appears in remote repository
- [ ] Verify CI/CD pipeline runs (if configured)

---

## Step 10: Baseline Freeze (After Multiple Triggers)

When adding triggers beyond the first few:

### 10.1 Multi-Trigger Verification
- [ ] Run ALVT verification for all active triggers
- [ ] Ensure all triggers pass Layer 0/1
- [ ] Document any cross-trigger dependencies or conflicts

### 10.2 Bulk Runbook
- [ ] Create or update bulk verification script
- [ ] Document batch execution workflow
- [ ] Add to CI/CD pipeline (if applicable)

---

## Common Issues and Solutions

### Issue: File paths in contract don't match actual files
**Solution:** Use repo-relative paths consistently. Verify paths with `ls <path>` before adding to contract.

### Issue: Node locations are ambiguous
**Solution:** Use full path format: `path/to/file.py::ClassName::method_name`. For top-level functions: `path/to/file.py::function_name`.

### Issue: Edge verification fails but code looks correct
**Solution:** Remember Layer 1 uses simplified edge detection. If both nodes exist, edge is assumed. For now, focus on node existence.

### Issue: Config validation shows placeholder behavior
**Solution:** This is expected. Config validation is documented as placeholder in current ALVT version. Document in findings log.

### Issue: Layer 0/1 pass but trigger doesn't work at runtime
**Solution:** ALVT verifies wiring completeness, not runtime behavior. Add Layer 2 (plan determinism) and Layer 3 (sandbox execution) tests for runtime validation.

---

## References

- Contract Template: `contracts/triggers/0199900117260118_trigger_contract_template.yaml`
- Architecture: `contracts/triggers/0199900116260118_automation_verification_architecture.md`
- Pilot Runbook: `contracts/triggers/0199900127260118_run_alvt_pilot.md`
- Pilot Findings: `reports/alvt/0199900125260118_alvt_pilot_findings.md`
- CLI Tool: `tools/alvt/2099900126260118_alvt_cli.py`

---

## Completion Criteria

All checklist items above marked as complete:
- [ ] Contract created and validated
- [ ] Layer 0 verification PASS
- [ ] Layer 1 verification PASS
- [ ] Stability verified (2 consecutive runs)
- [ ] Findings log created
- [ ] Changes committed and pushed

**Status:** Ready for baseline inclusion

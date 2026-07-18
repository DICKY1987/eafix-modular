# EAFIX SSOT Registry Delivery Verification Checklist

> **Generated, non-authoritative artifact. Do not hand-edit.**
> Regenerate from the canonical verification specification and bound final plan.

## Document binding

- **Target plan:** `EAFIX-SSOT-REGISTRY-SYSTEM-MASTER-V2` version `2.0.0`
- **Target plan file:** `EAFIX_SSOT_REGISTRY_SYSTEM_FINAL_MERGED_IMPLEMENTATION_PLAN_v2_0_0.json`
- **Target plan SHA-256:** `1fc42c139e0a290942a393fe22e0022f6e72cee32d221921bd0143c29513b7d8`
- **Verification specification:** `EAFIX-SSOT-DELIVERY-VERIFICATION-001` version `1.0.0`
- **Verification specification file:** `EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_SPEC_v1_0_0.json`
- **Verification specification SHA-256:** `430de6a09bb808ff22f0047c48288752b8fb55b4c34101d77e40e8ab270e5cdd`
- **Obligation matrix:** `EAFIX_SSOT_REGISTRY_DELIVERY_OBLIGATION_MATRIX.generated.json`
- **Expected plan obligations:** `1405`
- **Verification gates:** `11`
- **Verification checks:** `86`

## Use rules

- Execute gates in numeric order and only after all declared dependencies pass.
- Record each check verdict in a separate run-specific verification report; do not edit this checklist to become the result authority.
- Use only `pass`, `fail`, `blocked`, or `not_applicable` as verdicts.
- `blocked` is not a pass. `not_applicable` requires plan-based rationale and approval when required.
- Every pass must cite fresh evidence bound to the target commit, target-plan hash, and verification-specification hash.
- Do not rely on the implementing agent's summary as evidence.
- Run negative tests, mutations, and rollback rehearsals only in isolated fixtures or disposable worktrees.
- Stop downstream completion claims when a blocker or high-severity check fails or is blocked.

## Obligation coverage summary

| Obligation class | Expected | Generated | Status |
|---|---:|---:|---|
| `source_entry` | 13 | 13 | PASS |
| `phase` | 17 | 17 | PASS |
| `task` | 195 | 195 | PASS |
| `task_acceptance_clause` | 551 | 551 | PASS |
| `task_output` | 219 | 219 | PASS |
| `task_evidence_requirement` | 129 | 129 | PASS |
| `phase_exit_gate` | 17 | 17 | PASS |
| `phase_exit_gate_condition` | 90 | 90 | PASS |
| `validation_rule` | 60 | 60 | PASS |
| `human_decision` | 18 | 18 | PASS |
| `write_scope` | 14 | 14 | PASS |
| `definition_of_done` | 27 | 27 | PASS |
| `global_constraint` | 22 | 22 | PASS |
| `failure_condition` | 20 | 20 | PASS |
| `agent_execution_rule` | 13 | 13 | PASS |
| **Total** | **1405** | **1405** | **PASS** |

## Run header

- [ ] **Run ID:** `____________________________`
- [ ] **Repository:** `____________________________`
- [ ] **Target branch:** `____________________________`
- [ ] **Target commit SHA:** `____________________________`
- [ ] **Verifier identity:** `____________________________`
- [ ] **Started at UTC:** `____________________________`
- [ ] **Completed at UTC:** `____________________________`
- [ ] **Working tree clean:** `____________________________`
- [ ] **Evidence root:** `____________________________`
- [ ] **Final report path:** `____________________________`

## Gate summary

| Order | Gate | Title | Dependency | Blocker/high pass required | Verdict |
|---:|---|---|---|---|---|
| 0 | `VERIFY-GATE-00` | Input and scope integrity | None | Yes | `not_run` |
| 1 | `VERIFY-GATE-01` | Plan coverage completeness | VERIFY-GATE-00 | Yes | `not_run` |
| 2 | `VERIFY-GATE-02` | Task and phase delivery | VERIFY-GATE-01 | Yes | `not_run` |
| 3 | `VERIFY-GATE-03` | Artifact and registry integrity | VERIFY-GATE-02 | Yes | `not_run` |
| 4 | `VERIFY-GATE-04` | Authority and governance | VERIFY-GATE-03 | Yes | `not_run` |
| 5 | `VERIFY-GATE-05` | Parity, conflict, and evidence quality | VERIFY-GATE-04 | Yes | `not_run` |
| 6 | `VERIFY-GATE-06` | Determinism and drift resistance | VERIFY-GATE-05 | Yes | `not_run` |
| 7 | `VERIFY-GATE-07` | Negative and mutation testing | VERIFY-GATE-06 | Yes | `not_run` |
| 8 | `VERIFY-GATE-08` | Migration and rollback | VERIFY-GATE-07 | Yes | `not_run` |
| 9 | `VERIFY-GATE-09` | CI, clean clone, and operational readiness | VERIFY-GATE-08 | Yes | `not_run` |
| 10 | `VERIFY-GATE-10` | Final declaration and evidence seal | VERIFY-GATE-09 | Yes | `not_run` |

## VERIFY-GATE-00 — Input and scope integrity

**Purpose:** Bind the run to the exact plan and repository state before implementation claims are examined.

**Depends on:** None

**Target-plan phases:** `PHASE-00`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Stop the verification run. Do not evaluate downstream delivery claims against an unbound or unresolved input set.

### [ ] VER-G00-001 — Bind verification to the exact final plan

- **Category:** `input_scope`  
- **Severity:** `blocker`  
- **Control type:** `preventive`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `64`

- **Phase references:** `PHASE-00`
- **Procedure:**
  - [ ] Compute SHA-256 of the target plan file.
  - [ ] Parse the plan and compare plan_id, plan_version, and document_type to the bound values in this specification.
- **Commands:**
  - [ ] `python tools/verification/verify_target_binding.py --spec EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_SPEC_v1_0_0.json --plan EAFIX_SSOT_REGISTRY_SYSTEM_FINAL_MERGED_IMPLEMENTATION_PLAN_v2_0_0.json`
- **Expected results:**
  - [ ] sha256 == 1fc42c139e0a290942a393fe22e0022f6e72cee32d221921bd0143c29513b7d8
  - [ ] plan_id == EAFIX-SSOT-REGISTRY-SYSTEM-MASTER-V2
  - [ ] plan_version == 2.0.0
  - [ ] JSON parsing succeeds
- **Required evidence:**
  - [ ] `target_binding` — Target plan identity, path, byte size, and SHA-256 (minimum: 1; freshness required: true)
  - [ ] `schema_validation` — Successful target-plan JSON parse result (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Change one byte in a temporary copy of the plan.
  - [ ] Expected failure: Target-binding check exits nonzero and reports a hash mismatch.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G00-002 — Resolve mandatory routing and authority references

- **Category:** `input_scope`  
- **Severity:** `blocker`  
- **Control type:** `preventive`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `64`

- **Phase references:** `PHASE-00`
- **Procedure:**
  - [ ] Read the routing authority first.
  - [ ] Resolve every required reference from the plan against the target commit.
  - [ ] Record each reference as resolved, missing, stale, moved, ambiguous, or not applicable.
  - [ ] Block only conclusions and checks that depend on unresolved references.
- **Expected results:**
  - [ ] Every required reference has an explicit resolution status.
  - [ ] No lower-authority source is silently substituted.
  - [ ] The authority priority applied matches the target plan.
- **Required evidence:**
  - [ ] `routing_resolution` — Per-reference resolution report (minimum: 1; freshness required: true)
  - [ ] `authority_map` — Authority-priority and conflict-resolution record (minimum: 1; freshness required: true)
  - [ ] `commit_record` — Target commit SHA (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G00-003 — Freeze repository and verification context

- **Category:** `input_scope`  
- **Severity:** `blocker`  
- **Control type:** `preventive`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `64`

- **Phase references:** `PHASE-00`
- **Procedure:**
  - [ ] Record repository full name, target branch, target commit SHA, default branch, ruleset state, required checks, submodules, and clean-tree status.
  - [ ] Record verifier tool versions and operating system.
- **Commands:**
  - [ ] `git rev-parse --show-toplevel`
  - [ ] `git rev-parse HEAD`
  - [ ] `git status --short`
  - [ ] `git remote -v`
- **Expected results:**
  - [ ] Repository is DICKY1987/eafix-modular.
  - [ ] Target commit is immutable for the verification run.
  - [ ] Working tree is clean before evidence collection.
  - [ ] Default-branch writes are not used.
- **Required evidence:**
  - [ ] `repository_state` — Repository baseline and clean-tree proof (minimum: 1; freshness required: true)
  - [ ] `commit_record` — Target commit SHA (minimum: 1; freshness required: true)
  - [ ] `command_transcript` — Git baseline commands (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G00-004 — Verify source-plan consolidation inventory

- **Category:** `input_scope`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `80`

- **Phase references:** `PHASE-00`
- **Procedure:**
  - [ ] Hash each source entry available in the repository or evidence bundle.
  - [ ] Verify the declared duplicate naming-plan relationship.
  - [ ] Verify remediation v1.1.0 supersedes v1.0.0 and the amendment is provenance only.
- **Expected results:**
  - [ ] 13 source entries are represented.
  - [ ] 12 unique content hashes are represented.
  - [ ] No source plan remains an active sequencing dependency after final-plan approval.
- **Required evidence:**
  - [ ] `source_hash_inventory` — Source file hashes, versions, IDs, and dispositions (minimum: 1; freshness required: true)
  - [ ] `supersession_record` — Duplicate and supersession verification (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Remove one source-inventory row from a temporary generated matrix.
  - [ ] Expected failure: Coverage validator reports the source entry as unmapped.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G00-005 — Verify verification specification schema conformance

- **Category:** `input_scope`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `0`

- **Phase references:** `PHASE-00`
- **Procedure:**
  - [ ] Validate this specification against its companion JSON Schema using Draft 2020-12.
  - [ ] Run the semantic validation rules declared by this specification.
- **Commands:**
  - [ ] `python -m jsonschema -i EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_SPEC_v1_0_0.json EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_SPEC.schema.json`
- **Expected results:**
  - [ ] JSON Schema validation errors == 0.
  - [ ] Semantic validation errors == 0.
- **Required evidence:**
  - [ ] `schema_validation` — Schema validator output (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Semantic validator output (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Delete a required field from a temporary copy of the verification specification.
  - [ ] Expected failure: Schema validation exits nonzero.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G00-006 — Verify evidence storage is isolated and immutable by run

- **Category:** `input_scope`  
- **Severity:** `high`  
- **Control type:** `preventive`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `0`

- **Phase references:** `PHASE-00`, `PHASE-16`
- **Procedure:**
  - [ ] Create a unique run_id and evidence root.
  - [ ] Prevent prior-run evidence from being overwritten.
  - [ ] Record hashes for every evidence object in the run manifest.
- **Expected results:**
  - [ ] Run-specific evidence root exists.
  - [ ] No evidence object is referenced without a hash.
  - [ ] Evidence from other commits is marked stale and excluded.
- **Required evidence:**
  - [ ] `artifact` — Verification context file (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Evidence manifest with hashes (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G00-007 — Verify environmental blockers are explicit

- **Category:** `input_scope`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `when_ci_available`  
- **Fail closed:** `true`  
- **Mapped obligations:** `20`

- **Phase references:** `PHASE-00`, `PHASE-16`
- **Procedure:**
  - [ ] Check CI account state, required tool availability, repository permissions, and platform constraints.
  - [ ] Classify unavailable execution as blocked, never pass.
- **Expected results:**
  - [ ] No skipped, neutral, startup-blocked, or unavailable check is recorded as passing.
  - [ ] All blocked checks name the blocker and affected scope.
- **Required evidence:**
  - [ ] `ci_run` — CI execution or blocker evidence (minimum: 1; freshness required: true)
  - [ ] `manual_review_record` — Environmental blocker classification (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-00 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-01 — Plan coverage completeness

**Purpose:** Prove that the verification package covers the complete final plan rather than a selected subset.

**Depends on:** `VERIFY-GATE-00`

**Target-plan phases:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Stop. A verification report with incomplete obligation coverage is invalid regardless of implementation quality.

### [ ] VER-G01-001 — Generate the complete plan-obligation inventory

- **Category:** `coverage`  
- **Severity:** `blocker`  
- **Control type:** `preventive`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `1405`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Traverse the target plan using the obligation-generation rules in this specification.
  - [ ] Emit one obligation record per counted source element with exact JSON pointer and stable obligation_id.
- **Commands:**
  - [ ] `python tools/verification/generate_plan_obligation_matrix.py --spec EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_SPEC_v1_0_0.json --plan EAFIX_SSOT_REGISTRY_SYSTEM_FINAL_MERGED_IMPLEMENTATION_PLAN_v2_0_0.json`
- **Expected results:**
  - [ ] expected_total_obligations == 1405
  - [ ] No duplicate obligation_id.
  - [ ] Every JSON pointer resolves.
- **Required evidence:**
  - [ ] `coverage_matrix` — Generated plan-obligation inventory (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Obligation extractor summary (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Delete one generated obligation record from a temporary matrix.
  - [ ] Expected failure: Coverage validator reports an exact count mismatch and the missing plan pointer.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G01-002 — Verify exact obligation category counts

- **Category:** `coverage`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `17`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Compare generated category counts to target-plan-derived expected counts bound in this specification.
- **Expected results:**
  - [ ] source_entries == 13
  - [ ] phases == 17
  - [ ] tasks == 195
  - [ ] task_acceptance_clauses == 551
  - [ ] task_outputs == 219
  - [ ] task_evidence_requirements == 129
  - [ ] phase_exit_gates == 17
  - [ ] phase_exit_gate_conditions == 90
  - [ ] validation_rules == 60
  - [ ] human_decisions == 18
  - [ ] write_scopes == 14
  - [ ] definition_of_done_criteria == 27
  - [ ] global_constraints == 22
  - [ ] failure_conditions == 20
  - [ ] agent_execution_rules == 13
- **Required evidence:**
  - [ ] `coverage_matrix` — Category count table (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Count comparison output (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Increment one expected category count in a temporary specification copy.
  - [ ] Expected failure: Semantic validation reports a count mismatch.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G01-003 — Map every obligation to verification checks

- **Category:** `coverage`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `1405`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Assign one or more verification_check_ids to every obligation.
  - [ ] Require explicit rationale when multiple checks cover one obligation.
- **Expected results:**
  - [ ] unmapped == 0
  - [ ] invalid_source_pointer == 0
  - [ ] mapped_multiple_explained contains rationale for every occurrence
- **Required evidence:**
  - [ ] `coverage_matrix` — Obligation-to-check coverage matrix (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Coverage validation output (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Clear verification_check_ids for one obligation in a temporary matrix.
  - [ ] Expected failure: Coverage validator exits nonzero and identifies the unmapped obligation.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G01-004 — Verify task acceptance clauses are not collapsed into task-level claims

- **Category:** `coverage`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `551`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Confirm each acceptance clause has its own obligation record and evidence mapping.
  - [ ] Reject a single generic task-complete record that does not enumerate acceptance clauses.
- **Expected results:**
  - [ ] task_acceptance_clauses == 551
  - [ ] Each acceptance obligation has at least one verification mapping.
- **Required evidence:**
  - [ ] `coverage_matrix` — Acceptance-clause coverage rows (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G01-005 — Verify outputs are checked across required dimensions

- **Category:** `coverage`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `219`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] For each output obligation, require applicable checks for existence, validity, provenance, integration, and enforcement.
  - [ ] Permit dimension not_applicable only with explicit rationale and approval policy.
- **Expected results:**
  - [ ] Every output has five dimension statuses.
  - [ ] No output passes on existence alone.
- **Required evidence:**
  - [ ] `coverage_matrix` — Output dimension coverage rows (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G01-006 — Verify human decisions and write scopes are fully mapped

- **Category:** `coverage`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `32`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Generate one obligation per human decision and per write scope.
  - [ ] Map each blocking decision to approval evidence and each write scope to diff-scope verification.
- **Expected results:**
  - [ ] human_decisions == 18
  - [ ] write_scopes == 14
  - [ ] Unmapped decisions == 0
  - [ ] Unmapped write scopes == 0
- **Required evidence:**
  - [ ] `coverage_matrix` — Decision and write-scope coverage rows (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G01-007 — Verify definition-of-done coverage

- **Category:** `coverage`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `27`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Generate one obligation for each definition-of-done criterion.
  - [ ] Map each criterion to one or more independent checks and evidence types.
- **Expected results:**
  - [ ] definition_of_done_criteria == 27
  - [ ] Unmapped definition-of-done criteria == 0
- **Required evidence:**
  - [ ] `coverage_matrix` — Definition-of-done coverage rows (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G01-008 — Verify no excluded obligation classes

- **Category:** `coverage`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `22`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Compare extracted obligation classes to the complete generation-rule registry.
  - [ ] Reject undocumented exclusions.
- **Expected results:**
  - [ ] All 15 declared obligation classes are present.
  - [ ] Exclusion count == 0 unless approved by an explicit plan amendment.
- **Required evidence:**
  - [ ] `coverage_matrix` — Obligation-class summary (minimum: 1; freshness required: true)
  - [ ] `approval_record` — Any approved exclusion record (minimum: 0; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-01 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-02 — Task and phase delivery

**Purpose:** Verify that all planned work was executed in order, within scope, with outputs and evidence.

**Depends on:** `VERIFY-GATE-01`

**Target-plan phases:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Mark the affected tasks and phases incomplete. Do not infer completion from later successful phases.

### [ ] VER-G02-001 — Verify task dependency order

- **Category:** `execution`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `195`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Build phase and task dependency graphs.
  - [ ] Verify every completed task has evidence that predecessors were complete before execution.
  - [ ] Detect cycles and missing references.
- **Expected results:**
  - [ ] Dependency cycles == 0
  - [ ] Missing dependency references == 0
  - [ ] Out-of-order completed tasks == 0
- **Required evidence:**
  - [ ] `raw_validator_output` — Dependency graph validation (minimum: 1; freshness required: true)
  - [ ] `artifact` — Execution ledger with timestamps and IDs (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Create a synthetic dependency cycle in a temporary plan fixture.
  - [ ] Expected failure: Dependency validator exits nonzero.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G02-002 — Verify every task has a completion record

- **Category:** `execution`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `208`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Match every task_id to exactly one execution-ledger record.
  - [ ] Require status, commit/PR references, changed files, evidence IDs, and acceptance results.
- **Expected results:**
  - [ ] task completion records == 195
  - [ ] Missing task records == 0
  - [ ] Duplicate task records == 0
- **Required evidence:**
  - [ ] `artifact` — Execution ledger (minimum: 1; freshness required: true)
  - [ ] `coverage_matrix` — Task-to-execution-record mapping (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G02-003 — Verify task preconditions and human gates

- **Category:** `execution`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `213`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] For each task, verify listed preconditions were true before execution.
  - [ ] For tasks or phases requiring human approval, verify approval predates the governed action.
- **Expected results:**
  - [ ] Unsatisfied preconditions == 0
  - [ ] Missing blocking approvals == 0
  - [ ] Post-dated approvals == 0
- **Required evidence:**
  - [ ] `approval_record` — Human approvals with decision IDs and timestamps (minimum: 1; freshness required: true)
  - [ ] `artifact` — Task precondition evidence (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G02-004 — Verify task actions and commands were executed or validly superseded

- **Category:** `execution`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `208`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Compare each task action and command to transcripts and changed artifacts.
  - [ ] When a historical literal was replaced, require an evidence-backed substitution record.
- **Expected results:**
  - [ ] Every required action is executed or governed as superseded.
  - [ ] Every command substitution cites live repository evidence.
- **Required evidence:**
  - [ ] `command_transcript` — Commands and exit codes (minimum: 1; freshness required: true)
  - [ ] `manual_review_record` — Action-completion review (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Command substitution decisions (minimum: 0; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G02-005 — Verify task outputs satisfy content and provenance requirements

- **Category:** `execution`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `414`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Resolve every output path or artifact ID.
  - [ ] Validate content, schema, source linkage, generating task, commit, and hash.
  - [ ] Reject placeholder or empty outputs unless explicitly allowed.
- **Expected results:**
  - [ ] Missing outputs == 0
  - [ ] Invalid outputs == 0
  - [ ] Outputs without provenance == 0
  - [ ] Unauthorized placeholders == 0
- **Required evidence:**
  - [ ] `artifact` — Delivered outputs (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Output hashes (minimum: 1; freshness required: true)
  - [ ] `schema_validation` — Output schema validation (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G02-006 — Verify every acceptance clause has direct evidence

- **Category:** `execution`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `1025`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Evaluate each acceptance obligation independently.
  - [ ] Link each verdict to evidence IDs and prohibit unsupported inherited pass status.
- **Expected results:**
  - [ ] Acceptance clauses with pass and evidence == expected count or valid not_applicable.
  - [ ] Unsupported pass count == 0
  - [ ] Blocked acceptance clauses prevent affected task and phase completion.
- **Required evidence:**
  - [ ] `coverage_matrix` — Acceptance verdict matrix (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Referenced evidence hashes (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G02-007 — Verify phase exit gates controlled progression

- **Category:** `execution`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `124`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Verify each exit gate condition separately.
  - [ ] Confirm downstream phase work did not begin before predecessor gate approval.
  - [ ] Record gate decision and evidence.
- **Expected results:**
  - [ ] phase exit gates evaluated == 17
  - [ ] gate conditions evaluated == 90
  - [ ] Premature downstream starts == 0
- **Required evidence:**
  - [ ] `approval_record` — Phase gate decisions (minimum: 1; freshness required: true)
  - [ ] `coverage_matrix` — Gate-condition results (minimum: 1; freshness required: true)
  - [ ] `artifact` — Execution timeline (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G02-008 — Verify write-scope compliance for every task and PR

- **Category:** `execution`  
- **Severity:** `blocker`  
- **Control type:** `preventive`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `209`

- **Phase references:** `PHASE-00`, `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-06`, `PHASE-07`, `PHASE-08`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] For each task/PR, compare changed paths with the referenced write_scope_id.
  - [ ] Treat a forbidden or unlisted path as blocking unless an approved plan amendment exists.
- **Expected results:**
  - [ ] Unauthorized changed paths == 0
  - [ ] Missing write_scope_id == 0
  - [ ] Approved exceptions have decision records.
- **Required evidence:**
  - [ ] `diff` — Per-task or per-PR changed-file list (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Write-scope validator output (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Approved scope amendments (minimum: 0; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Add an unlisted file path to a temporary changed-file fixture.
  - [ ] Expected failure: Write-scope validator exits nonzero.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-02 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-03 — Artifact and registry integrity

**Purpose:** Verify structural validity, provenance, managed outputs, registry graph integrity, and non-duplication of authority.

**Depends on:** `VERIFY-GATE-02`

**Target-plan phases:** `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-05`, `PHASE-07`, `PHASE-08`, `PHASE-11`, `PHASE-13`, `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Reject completion for affected registry or artifact domains and preserve exact invalid records and paths.

### [ ] VER-G03-001 — Validate all authored registry files and schemas

- **Category:** `artifact_integrity`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `446`

- **Phase references:** `PHASE-01`, `PHASE-03`, `PHASE-05`, `PHASE-07`
- **Procedure:**
  - [ ] Run all registry schema, ID, reference, and authority validators.
  - [ ] Capture exact record and error counts.
- **Commands:**
  - [ ] `python tools/registries/validate_record_schemas.py`
  - [ ] `python tools/registries/validate_registry_ids.py`
  - [ ] `python tools/registries/validate_registry_references.py`
  - [ ] `python tools/registries/validate_registry_authority.py`
- **Expected results:**
  - [ ] schema_errors == 0
  - [ ] duplicate_id_errors == 0
  - [ ] enabled_foreign_reference_errors == 0
  - [ ] authority_state_errors == 0
- **Required evidence:**
  - [ ] `raw_validator_output` — All registry validator outputs (minimum: 1; freshness required: true)
  - [ ] `test_report` — Registry validation tests (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Inject a duplicate ID and invalid foreign reference into temporary fixtures.
  - [ ] Expected failure: Relevant validators exit nonzero and identify registry, record, field, and target.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G03-002 — Verify all ten registries and generated current views

- **Category:** `artifact_integrity`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `235`

- **Phase references:** `PHASE-01`, `PHASE-07`
- **Procedure:**
  - [ ] Inventory authored registries, schemas, current views, graph, reports, and build manifest.
  - [ ] Verify authored and generated classifications.
- **Expected results:**
  - [ ] Authored registry count == 10
  - [ ] Generated current view count == 10
  - [ ] Unexpected authored duplicates == 0
  - [ ] Missing managed outputs == 0
- **Required evidence:**
  - [ ] `artifact` — Registry and generated-output inventory (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Build manifest (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G03-003 — Verify registry build manifest integrity

- **Category:** `artifact_integrity`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `409`

- **Phase references:** `PHASE-01`, `PHASE-02`, `PHASE-07`
- **Procedure:**
  - [ ] Verify every listed input and output hash.
  - [ ] Verify POSIX repository-relative keys.
  - [ ] Verify the manifest does not hash itself.
- **Expected results:**
  - [ ] Hash mismatches == 0
  - [ ] Absolute paths == 0
  - [ ] Backslash path keys == 0
  - [ ] Manifest self-hash absent
- **Required evidence:**
  - [ ] `artifact_hash_manifest` — Verified registry build manifest (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Manifest verifier output (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Alter one managed output byte in a temporary worktree.
  - [ ] Expected failure: Manifest verification and --check both fail without rewriting the file.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G03-004 — Verify generated artifacts are non-authoritative and non-editable

- **Category:** `artifact_integrity`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `227`

- **Phase references:** `PHASE-01`, `PHASE-03`, `PHASE-08`, `PHASE-13`, `PHASE-16`
- **Procedure:**
  - [ ] Compare generated files to deterministic render output.
  - [ ] Inspect authority records to confirm generated files are not active authored authorities.
  - [ ] Check repository protections or CI enforcement.
- **Expected results:**
  - [ ] Generated drift == 0
  - [ ] Generated files marked generated/non-authoritative
  - [ ] Manual edit detection is blocking where required
- **Required evidence:**
  - [ ] `raw_validator_output` — Generated-output drift check (minimum: 1; freshness required: true)
  - [ ] `authority_map` — Authority classification (minimum: 1; freshness required: true)
  - [ ] `ci_run` — Generated-file protection check (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G03-005 — Verify stable IDs and cross-registry graph completeness

- **Category:** `artifact_integrity`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `386`

- **Phase references:** `PHASE-03`, `PHASE-07`, `PHASE-08`
- **Procedure:**
  - [ ] Validate stable ID formats, uniqueness, non-reuse, and cross-registry references.
  - [ ] Compare graph edges to declared relationships.
- **Expected results:**
  - [ ] Duplicate or reused stable IDs == 0
  - [ ] Unresolved required graph edges == 0
  - [ ] Unknown reference types == 0
- **Required evidence:**
  - [ ] `raw_validator_output` — ID and graph validation (minimum: 1; freshness required: true)
  - [ ] `artifact` — Cross-registry graph report (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Create a temporary record that reuses an ID or points to a nonexistent target.
  - [ ] Expected failure: Validation exits nonzero.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G03-006 — Verify registry completeness without hiding planned or unknown states

- **Category:** `artifact_integrity`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `233`

- **Phase references:** `PHASE-04`, `PHASE-05`, `PHASE-07`
- **Procedure:**
  - [ ] Inspect completeness, conflict, and orphan reports.
  - [ ] Verify planned modules use explicit planned status rather than fabricated implementation data.
  - [ ] Verify residual unknowns are visible and block only affected scope.
- **Expected results:**
  - [ ] Unexplained empty required fields == 0
  - [ ] Fabricated facts detected == 0
  - [ ] Residual unknowns have scope and disposition
- **Required evidence:**
  - [ ] `artifact` — Completeness, conflict, and orphan reports (minimum: 1; freshness required: true)
  - [ ] `manual_review_record` — Evidence-quality review (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G03-007 — Verify specialized schemas remain single-home authorities

- **Category:** `artifact_integrity`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `161`

- **Phase references:** `PHASE-03`, `PHASE-05`, `PHASE-11`
- **Procedure:**
  - [ ] Inventory canonical cross-module schemas and module-local schema content.
  - [ ] Detect duplicate authoritative shapes.
  - [ ] Verify local content is reference, example, projection, or private schema.
- **Expected results:**
  - [ ] Duplicate canonical contract shapes == 0
  - [ ] Every schema has one declared authority owner
  - [ ] Local duplicates are non-authoritative or rejected
- **Required evidence:**
  - [ ] `artifact` — Schema ownership inventory (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Schema placement approval (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Duplicate-shape detector (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G03-008 — Verify operational process is a registry-backed projection

- **Category:** `artifact_integrity`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `75`

- **Phase references:** `PHASE-08`
- **Procedure:**
  - [ ] Inspect process registry ownership and operational-process outputs.
  - [ ] Trace every projected fact to registry or registered external authority.
  - [ ] Verify no independently editable current process authority was introduced.
- **Expected results:**
  - [ ] Operational process artifact is generated.
  - [ ] Process registry remains identity/relationship owner.
  - [ ] Parallel editable process authority count == 0
- **Required evidence:**
  - [ ] `artifact` — Operational process projection (minimum: 1; freshness required: true)
  - [ ] `authority_map` — Process authority mapping (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Projection provenance (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-03 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-04 — Authority and governance

**Purpose:** Prove the SSOT authority model, decisions, cutovers, routing, and supersession are correct and auditable.

**Depends on:** `VERIFY-GATE-03`

**Target-plan phases:** `PHASE-00`, `PHASE-03`, `PHASE-05`, `PHASE-06`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Do not declare canonical authority or completed governance for any affected fact group or registry.

### [ ] VER-G04-001 — Verify one active canonical owner per governed fact group

- **Category:** `authority_governance`  
- **Severity:** `blocker`  
- **Control type:** `preventive`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `304`

- **Phase references:** `PHASE-03`, `PHASE-10`
- **Procedure:**
  - [ ] Validate authority manifest coverage and overlap rules.
  - [ ] Verify every governed fact group has exactly one active canonical source after applicable cutover.
- **Expected results:**
  - [ ] duplicate_active_owner_count == 0
  - [ ] unowned_fact_group_count == 0
  - [ ] ambiguous_pointer_count == 0
- **Required evidence:**
  - [ ] `authority_map` — Authority manifest and coverage matrix (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Authority manifest validator output (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Assign a second active owner to one fact group in a fixture.
  - [ ] Expected failure: Authority validator exits nonzero.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G04-002 — Verify pre-cutover and post-cutover authority ordering

- **Category:** `authority_governance`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `323`

- **Phase references:** `PHASE-03`, `PHASE-09`, `PHASE-10`
- **Procedure:**
  - [ ] For each registry and fact group, determine cutover state at the target commit.
  - [ ] Apply the correct authority priority and verify routing/doc authority agree.
- **Expected results:**
  - [ ] No candidate overrides current authority before cutover.
  - [ ] No superseded authority remains selected after cutover.
  - [ ] Routing and doc authority are consistent.
- **Required evidence:**
  - [ ] `routing_resolution` — Resolved routing state (minimum: 1; freshness required: true)
  - [ ] `authority_map` — Fact-group authority state (minimum: 1; freshness required: true)
  - [ ] `supersession_record` — Cutover supersession records (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G04-003 — Verify human decisions are authentic, timely, and scoped

- **Category:** `authority_governance`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `manual`  
- **Automation:** `manual`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `80`

- **Phase references:** `PHASE-00`, `PHASE-03`, `PHASE-06`, `PHASE-09`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-16`
- **Procedure:**
  - [ ] Verify each blocking decision has an identifiable approver, decision ID, rationale, selected option, timestamp, and affected scope.
  - [ ] Verify approval predates irreversible action.
- **Expected results:**
  - [ ] Missing blocking decisions == 0
  - [ ] Ambiguous approvals == 0
  - [ ] Approval-after-action count == 0
- **Required evidence:**
  - [ ] `approval_record` — Owner approval records (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Decision registry records (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G04-004 — Verify source plans and duplicate documents are superseded correctly

- **Category:** `authority_governance`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `417`

- **Phase references:** `PHASE-00`, `PHASE-10`, `PHASE-16`
- **Procedure:**
  - [ ] Inspect doc authority, routing, banners, archive location, and references.
  - [ ] Verify one final implementation plan remains active.
  - [ ] Verify duplicate naming document is non-authoritative.
- **Expected results:**
  - [ ] Active sequencing plan count == 1
  - [ ] Superseded source plans do not remain active
  - [ ] Duplicate naming authority count == 0
- **Required evidence:**
  - [ ] `supersession_record` — Plan and document supersession state (minimum: 1; freshness required: true)
  - [ ] `routing_resolution` — Routing pointers (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G04-005 — Verify cutover occurred only per registry and with rollback evidence

- **Category:** `authority_governance`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `82`

- **Phase references:** `PHASE-09`, `PHASE-10`
- **Procedure:**
  - [ ] For each cutover registry, verify qualification evidence, sustained green state, approval, atomic metadata changes, and tested rollback.
  - [ ] Reject global or partial inconsistent cutover.
- **Expected results:**
  - [ ] Every canonical registry has a cutover decision and qualification report.
  - [ ] No unqualified registry is canonical.
  - [ ] Rollback was executed successfully in an isolated test.
- **Required evidence:**
  - [ ] `stability_report` — Sustained green report (minimum: 1; freshness required: true)
  - [ ] `approval_record` — Cutover approval (minimum: 1; freshness required: true)
  - [ ] `rollback_result` — Cutover rollback test (minimum: 1; freshness required: true)
  - [ ] `diff` — Atomic cutover diff (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G04-006 — Verify retired or superseded artifacts remain auditable

- **Category:** `authority_governance`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `149`

- **Phase references:** `PHASE-10`, `PHASE-16`
- **Procedure:**
  - [ ] Verify superseded artifacts are retained or archived according to policy, contain pointers, and are excluded from routing.
  - [ ] Verify no archived content is used as current authority.
- **Expected results:**
  - [ ] Superseded artifacts have replacement pointers.
  - [ ] Archived current-authority references == 0
  - [ ] Unauthorized archive modifications == 0
- **Required evidence:**
  - [ ] `supersession_record` — Supersession inventory (minimum: 1; freshness required: true)
  - [ ] `routing_resolution` — Excluded-path and pointer verification (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G04-007 — Verify born-canonical and no-declared-authority registries have substitute evidence

- **Category:** `authority_governance`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `112`

- **Phase references:** `PHASE-05`, `PHASE-10`
- **Procedure:**
  - [ ] For each registry lacking a predecessor authority, verify a governed basis: declared authority, born-canonical with substitute validators, or retirement.
  - [ ] Run substitute validators against implementation/configuration evidence.
- **Expected results:**
  - [ ] Registries with unresolved authority basis == 0
  - [ ] Born-canonical registries have passing external evidence checks
  - [ ] Retired registries have decision records
- **Required evidence:**
  - [ ] `authority_map` — Per-registry authority basis (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Substitute evidence validators (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Born-canonical or retirement decisions (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G04-008 — Verify current routing file and document authority agree

- **Category:** `authority_governance`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `413`

- **Phase references:** `PHASE-00`, `PHASE-10`, `PHASE-16`
- **Procedure:**
  - [ ] Cross-validate every active routing reference against doc authority and authority manifest.
  - [ ] Detect missing, duplicate, or stale paths.
- **Expected results:**
  - [ ] Routing/doc-authority conflicts == 0
  - [ ] Missing active authority paths == 0
  - [ ] Stale current pointers == 0
- **Required evidence:**
  - [ ] `raw_validator_output` — Routing/authority cross-validation (minimum: 1; freshness required: true)
  - [ ] `routing_resolution` — Resolved reference inventory (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Point a fixture route to a superseded document.
  - [ ] Expected failure: Cross-validator exits nonzero.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-04 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-05 — Parity, conflict, and evidence quality

**Purpose:** Verify the registry facts were reconciled honestly, with deterministic parity and traceable evidence.

**Depends on:** `VERIFY-GATE-04`

**Target-plan phases:** `PHASE-02`, `PHASE-04`, `PHASE-05`, `PHASE-07`, `PHASE-09`, `PHASE-10`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Block cutover for affected registries and restore any improperly removed baseline entries.

### [ ] VER-G05-001 — Verify parity authority map coverage and doc-authority consistency

- **Category:** `parity_evidence`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `314`

- **Phase references:** `PHASE-02`, `PHASE-05`
- **Procedure:**
  - [ ] Validate parity authority map schema.
  - [ ] Cross-validate mapped authorities with doc authority.
  - [ ] Verify every registry has an explicit coverage classification or substitute evidence basis.
- **Expected results:**
  - [ ] Unclassified registries == 0
  - [ ] Invalid authority mappings == 0
  - [ ] Unavailable authorities are explicit and fail closed
- **Required evidence:**
  - [ ] `authority_map` — Parity authority map (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Parity map validation (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G05-002 — Verify parity engine is deterministic, read-only, and closed-taxonomy

- **Category:** `parity_evidence`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `161`

- **Phase references:** `PHASE-02`
- **Procedure:**
  - [ ] Run parity twice against identical inputs.
  - [ ] Verify stable parity IDs and verdict taxonomy.
  - [ ] Monitor authored files for writes.
- **Commands:**
  - [ ] `python tools/registries/validate_authority_parity.py --check`
- **Expected results:**
  - [ ] Parity outputs byte-identical.
  - [ ] Authored-file writes == 0
  - [ ] Unknown verdicts == 0
  - [ ] Parity IDs stable across value changes where identity is unchanged
- **Required evidence:**
  - [ ] `parity_report` — Two parity reports (minimum: 1; freshness required: true)
  - [ ] `clean_tree_proof` — No authored-file changes (minimum: 1; freshness required: true)
  - [ ] `test_report` — Parity unit and mutation tests (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Remove an authority fixture or inject an unsupported comparison.
  - [ ] Expected failure: Result is authority_unavailable or blocking tooling error, never agree.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G05-003 — Verify baseline ratchet integrity

- **Category:** `parity_evidence`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `358`

- **Phase references:** `PHASE-02`, `PHASE-04`, `PHASE-09`, `PHASE-10`
- **Procedure:**
  - [ ] Compare baseline changes to resolution records and parity IDs.
  - [ ] Detect new, known, resolved, and stale entries.
  - [ ] Verify tooling never auto-appends.
- **Expected results:**
  - [ ] New unapproved divergences == 0
  - [ ] Stale baseline entries == 0
  - [ ] Baseline removals equal evidenced resolutions
  - [ ] Automatic baseline writes == 0
- **Required evidence:**
  - [ ] `baseline_report` — Baseline before/after and disposition ledger (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Approved baseline changes (minimum: 1; freshness required: true)
  - [ ] `diff` — Baseline diff (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Delete a still-divergent parity ID or add a nonexistent ID in a fixture baseline.
  - [ ] Expected failure: Baseline hygiene check exits nonzero.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G05-004 — Verify conflict burn-down evidence quality

- **Category:** `parity_evidence`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `239`

- **Phase references:** `PHASE-04`
- **Procedure:**
  - [ ] For every resolved divergence and closed conflict item, inspect evidence class, path, commit SHA, locator, observation time, and parity linkage.
  - [ ] Enforce confidence ceilings and authority-only labeling.
- **Expected results:**
  - [ ] Resolved items without evidence == 0
  - [ ] E3-only records marked derived_from_authority_only and not high confidence
  - [ ] Baseline removals have one-for-one resolution links
- **Required evidence:**
  - [ ] `artifact` — Resolution evidence records (minimum: 1; freshness required: true)
  - [ ] `manual_review_record` — Evidence-quality audit (minimum: 1; freshness required: true)
  - [ ] `baseline_report` — Resolution-to-baseline reconciliation (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G05-005 — Verify real code defects were not hidden as documentation fixes

- **Category:** `parity_evidence`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `102`

- **Phase references:** `PHASE-04`
- **Procedure:**
  - [ ] Inspect contract and integration conflict resolutions.
  - [ ] Verify genuine producer/consumer mismatches are recorded and referred as code defects rather than normalized away.
- **Expected results:**
  - [ ] Known real integration defects have code issue references.
  - [ ] No conflicting implementation states are collapsed into false agreement.
  - [ ] Affected cutover scope remains explicit.
- **Required evidence:**
  - [ ] `decision_record` — Disposition records (minimum: 1; freshness required: true)
  - [ ] `pr_record` — Linked code issues or PRs (minimum: 1; freshness required: true)
  - [ ] `manual_review_record` — Contract evidence review (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G05-006 — Verify schema and comparison gaps are closed or explicitly accepted

- **Category:** `parity_evidence`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `60`

- **Phase references:** `PHASE-05`
- **Procedure:**
  - [ ] Review unrepresentable and not_comparable verdicts.
  - [ ] Verify schema extensions or deterministic comparisons were implemented where required.
  - [ ] Verify accepted differences have written rationale and approval.
- **Expected results:**
  - [ ] unrepresentable == 0 for cutover registries
  - [ ] Every not_comparable item is resolved or approved
  - [ ] No not_comparable item is counted as agree
- **Required evidence:**
  - [ ] `parity_report` — Verdict counts and records (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Accepted comparison limitations (minimum: 1; freshness required: true)
  - [ ] `schema_validation` — Schema extensions (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G05-007 — Verify sustained green evidence is per registry

- **Category:** `parity_evidence`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `30`

- **Phase references:** `PHASE-09`
- **Procedure:**
  - [ ] Inspect generated stability report and commit sequence.
  - [ ] Verify the threshold is met with normal repository activity and no hidden baseline resets.
- **Expected results:**
  - [ ] Each cutover registry meets configured consecutive-green threshold.
  - [ ] Green streak is tied to commit SHAs.
  - [ ] Baseline was not regenerated during streak.
- **Required evidence:**
  - [ ] `stability_report` — Per-registry green streak (minimum: 1; freshness required: true)
  - [ ] `commit_record` — Commit sequence (minimum: 1; freshness required: true)
  - [ ] `baseline_report` — Baseline history (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G05-008 — Run anti-transcription honesty audit

- **Category:** `parity_evidence`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `363`

- **Phase references:** `PHASE-04`, `PHASE-05`, `PHASE-07`
- **Procedure:**
  - [ ] Calculate resolution evidence-class distribution.
  - [ ] Review suspicious clusters of authority-only resolutions.
  - [ ] Sample records to verify implementation or artifact evidence where claimed.
- **Expected results:**
  - [ ] Evidence-class distribution is published.
  - [ ] Unsupported high-confidence claims == 0
  - [ ] Authority-copying patterns are explained or remediated.
- **Required evidence:**
  - [ ] `manual_review_record` — Honesty audit (minimum: 1; freshness required: true)
  - [ ] `artifact` — Evidence-class metrics (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-05 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-06 — Determinism and drift resistance

**Purpose:** Prove repeatable generation, complete no-write checking, cross-version compatibility, and clean-clone reproducibility.

**Depends on:** `VERIFY-GATE-05`

**Target-plan phases:** `PHASE-01`, `PHASE-02`, `PHASE-04`, `PHASE-07`, `PHASE-08`, `PHASE-13`, `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Reject deterministic-delivery claims and block cutover or final completion until byte stability is restored.

### [ ] VER-G06-001 — Prove two-build byte determinism

- **Category:** `determinism`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `488`

- **Phase references:** `PHASE-01`, `PHASE-02`, `PHASE-08`, `PHASE-13`, `PHASE-16`
- **Procedure:**
  - [ ] Run the complete generation pipeline twice from unchanged approved inputs.
  - [ ] Hash all managed outputs after each run.
- **Commands:**
  - [ ] `python tools/registries/build_registries.py`
  - [ ] `python tools/registries/build_registries.py`
  - [ ] `git diff --exit-code`
- **Expected results:**
  - [ ] Managed output hash set is identical.
  - [ ] Second build produces no Git diff.
- **Required evidence:**
  - [ ] `command_transcript` — Two generation runs (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Output hashes for both runs (minimum: 1; freshness required: true)
  - [ ] `clean_tree_proof` — No-diff proof (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Introduce a nondeterministic fixture field such as current time into a test renderer.
  - [ ] Expected failure: Determinism test detects differing bytes.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G06-002 — Prove no-write check mode covers every managed output

- **Category:** `determinism`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `419`

- **Phase references:** `PHASE-01`, `PHASE-02`, `PHASE-13`
- **Procedure:**
  - [ ] Snapshot file hashes and mtimes.
  - [ ] Run check mode.
  - [ ] Compare hashes, mtimes, and working tree.
  - [ ] Mutate one file from each output class and repeat.
- **Commands:**
  - [ ] `python tools/registries/build_registries.py --check`
- **Expected results:**
  - [ ] Clean check exits zero.
  - [ ] Check mode writes zero files.
  - [ ] Each mutated output class causes nonzero exit without rewrite.
- **Required evidence:**
  - [ ] `command_transcript` — Check-mode runs (minimum: 1; freshness required: true)
  - [ ] `mutation_result` — Per-output-class drift tests (minimum: 1; freshness required: true)
  - [ ] `clean_tree_proof` — No-write proof (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `true`
  - [ ] Mutation: Tamper each managed output class one at a time.
  - [ ] Expected failure: Check mode fails and leaves the tampered file unchanged.
  - [ ] Isolation: Run only in a disposable fixture, temporary worktree, or test repository; restore and prove clean state afterward.
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G06-003 — Verify cross-platform path and newline normalization

- **Category:** `determinism`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `272`

- **Phase references:** `PHASE-01`, `PHASE-13`
- **Procedure:**
  - [ ] Inspect manifests and generated content for absolute paths, backslashes, host-specific paths, or inconsistent newlines.
  - [ ] Compare supported-platform outputs where CI evidence exists.
- **Expected results:**
  - [ ] Absolute generated paths == 0
  - [ ] Backslash path keys == 0
  - [ ] Line endings are LF
  - [ ] Supported-platform output bytes match
- **Required evidence:**
  - [ ] `raw_validator_output` — Path/newline scan (minimum: 1; freshness required: true)
  - [ ] `ci_run` — Cross-platform jobs (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Platform hash comparison (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G06-004 — Verify Python 3.9 and 3.11 execution evidence

- **Category:** `determinism`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `when_runtime_available`  
- **Fail closed:** `true`  
- **Mapped obligations:** `356`

- **Phase references:** `PHASE-01`, `PHASE-02`, `PHASE-16`
- **Procedure:**
  - [ ] Run required registry and verification tests under Python 3.9 and 3.11.
  - [ ] Compare generated bytes and results.
- **Expected results:**
  - [ ] Python 3.9 failures == 0
  - [ ] Python 3.11 failures == 0
  - [ ] Generated output differences between versions == 0
- **Required evidence:**
  - [ ] `test_report` — Python 3.9 test results (minimum: 1; freshness required: true)
  - [ ] `test_report` — Python 3.11 test results (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Cross-version output hashes (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G06-005 — Verify dynamic counts are governed rather than hardcoded

- **Category:** `determinism`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `71`

- **Phase references:** `PHASE-01`, `PHASE-04`, `PHASE-07`, `PHASE-16`
- **Procedure:**
  - [ ] Scan validators, plans, and CI for prohibited mutable count literals used as permanent acceptance constants.
  - [ ] Verify governed expected-count files or computed counts are used.
- **Expected results:**
  - [ ] Unjustified hardcoded mutable counts == 0
  - [ ] Intentional count changes have evidence and review
- **Required evidence:**
  - [ ] `raw_validator_output` — Hardcoded-count scan (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Approved expected-count changes (minimum: 0; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G06-006 — Verify clean-clone reproducibility

- **Category:** `determinism`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Create a fresh clone at the target commit.
  - [ ] Install declared dependencies only.
  - [ ] Run generation, validation, tests, and check mode.
  - [ ] Verify no uncommitted required inputs.
- **Expected results:**
  - [ ] Clean clone completes all required commands.
  - [ ] Generated outputs match committed bytes.
  - [ ] No hidden local dependency is required.
- **Required evidence:**
  - [ ] `command_transcript` — Clean-clone transcript (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Committed versus regenerated hashes (minimum: 1; freshness required: true)
  - [ ] `clean_tree_proof` — Clean clone status (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G06-007 — Verify deterministic verification artifacts

- **Category:** `determinism`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Generate the obligation matrix and Markdown checklist twice from the same plan and specification.
  - [ ] Compare bytes and manifests.
- **Expected results:**
  - [ ] Obligation matrix is byte-identical.
  - [ ] Generated checklist is byte-identical.
  - [ ] No runtime timestamp appears in deterministic content unless supplied as input.
- **Required evidence:**
  - [ ] `artifact_hash_manifest` — Verification artifact hashes (minimum: 1; freshness required: true)
  - [ ] `command_transcript` — Two generation runs (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-06 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-07 — Negative and mutation testing

**Purpose:** Prove that the controls detect invalid states rather than merely passing the current repository.

**Depends on:** `VERIFY-GATE-06`

**Target-plan phases:** `PHASE-01`, `PHASE-02`, `PHASE-03`, `PHASE-04`, `PHASE-06`, `PHASE-07`, `PHASE-10`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Treat the corresponding positive control as unproven and block the affected completion claim.

### [ ] VER-G07-001 — Verify registry structural controls fail correctly

- **Category:** `mutation`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `485`

- **Phase references:** `PHASE-01`, `PHASE-07`
- **Procedure:**
  - [ ] Run isolated mutations for malformed JSONL, duplicate IDs, invalid IDs, unresolved references, and authority-state violations.
- **Expected results:**
  - [ ] Every mutation produces the expected nonzero result and diagnostic.
  - [ ] Restored clean state passes.
- **Required evidence:**
  - [ ] `mutation_result` — Registry structural mutation results (minimum: 1; freshness required: true)
  - [ ] `clean_tree_proof` — Post-mutation restoration proof (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G07-002 — Verify parity and baseline controls fail correctly

- **Category:** `mutation`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `263`

- **Phase references:** `PHASE-02`, `PHASE-04`
- **Procedure:**
  - [ ] Mutate authority availability, registry-only/authority-only records, field divergence, unrepresentable fields, new divergence, resolved divergence, and stale baseline cases.
- **Expected results:**
  - [ ] Expected verdict and blocking behavior occur for every case.
  - [ ] No mutation is silently normalized to agree.
- **Required evidence:**
  - [ ] `mutation_result` — Parity and baseline mutation results (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G07-003 — Verify authority overlap and routing drift controls fail correctly

- **Category:** `mutation`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `101`

- **Phase references:** `PHASE-03`, `PHASE-10`
- **Procedure:**
  - [ ] Introduce duplicate active owner, missing fact owner, stale routing pointer, and routing/doc-authority conflict in fixtures.
- **Expected results:**
  - [ ] Each condition blocks with a specific diagnostic.
- **Required evidence:**
  - [ ] `mutation_result` — Authority and routing mutation results (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G07-004 — Verify write-scope and generated-file protections fail correctly

- **Category:** `mutation`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `254`

- **Phase references:** `PHASE-01`, `PHASE-13`, `PHASE-16`
- **Procedure:**
  - [ ] Add an unauthorized path to a fixture diff.
  - [ ] Hand-edit generated artifacts.
  - [ ] Run scope and drift validators.
- **Expected results:**
  - [ ] Unauthorized path blocks.
  - [ ] Manual generated edit blocks.
  - [ ] Validators do not auto-repair during check.
- **Required evidence:**
  - [ ] `mutation_result` — Scope and generated-drift mutation results (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G07-005 — Verify module naming and folder controls fail correctly

- **Category:** `mutation`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `200`

- **Phase references:** `PHASE-06`, `PHASE-11`, `PHASE-13`
- **Procedure:**
  - [ ] Mutate locator, symbol rendering, .module-id, container role, manifest name, and cross-module nesting in fixture trees.
- **Expected results:**
  - [ ] Every invalid structure blocks with module/path-specific diagnostics.
- **Required evidence:**
  - [ ] `mutation_result` — Folder naming mutation results (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G07-006 — Verify path coverage and migration-map controls fail correctly

- **Category:** `mutation`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `242`

- **Phase references:** `PHASE-12`, `PHASE-13`, `PHASE-15`
- **Procedure:**
  - [ ] Remove a tracked path from the destination matrix.
  - [ ] Add a move outside the approved rename map.
  - [ ] Create a path-consumer mismatch.
- **Expected results:**
  - [ ] Unmapped tracked path blocks.
  - [ ] Unauthorized move blocks.
  - [ ] Unresolved path consumer blocks.
- **Required evidence:**
  - [ ] `mutation_result` — Path and migration map mutation results (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G07-007 — Verify rollback controls detect incomplete reversibility

- **Category:** `mutation`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `180`

- **Phase references:** `PHASE-10`, `PHASE-14`, `PHASE-15`
- **Procedure:**
  - [ ] Remove or corrupt one rollback entry in a fixture.
  - [ ] Run rollback validator and simulated rollback.
- **Expected results:**
  - [ ] Missing inverse mapping blocks.
  - [ ] Incomplete rollback leaves detectable diff and fails.
- **Required evidence:**
  - [ ] `mutation_result` — Rollback mutation result (minimum: 1; freshness required: true)
  - [ ] `rollback_result` — Simulated rollback output (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G07-008 — Verify downstream consumer dependency is real

- **Category:** `mutation`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Delete or invalidate a required registry record in an isolated branch/fixture.
  - [ ] Run the declared downstream consumer CI or build.
- **Expected results:**
  - [ ] Consumer fails for the expected reason.
  - [ ] Restoring the record restores success.
  - [ ] Failure is not caused by unrelated test setup.
- **Required evidence:**
  - [ ] `consumer_failure_proof` — Consumer break-and-restore evidence (minimum: 1; freshness required: true)
  - [ ] `mutation_result` — Registry consumer mutation result (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-07 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-08 — Migration and rollback

**Purpose:** Verify the 34-module physical migration is complete, evidence-backed, bounded, behavior-preserving, and reversible.

**Depends on:** `VERIFY-GATE-07`

**Target-plan phases:** `PHASE-06`, `PHASE-11`, `PHASE-12`, `PHASE-13`, `PHASE-14`, `PHASE-15`, `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Block migration completion and isolate the affected module, path, or wave. Use the tested rollback path where necessary.

### [ ] VER-G08-001 — Verify 34-module identity and locator ratification

- **Category:** `migration_rollback`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `105`

- **Phase references:** `PHASE-06`
- **Procedure:**
  - [ ] Validate active module count, ID/symbol/locator uniqueness, aliases, F4 governance, and owner approval.
  - [ ] Verify older catalogs are explicitly classified.
- **Expected results:**
  - [ ] Active modules == 34
  - [ ] Unique IDs == 34
  - [ ] Unique symbols == 34
  - [ ] Unique locators == 34
  - [ ] Unresolved identity conflicts == 0
- **Required evidence:**
  - [ ] `approval_record` — Module identity and locator ratification (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Identity uniqueness validation (minimum: 1; freshness required: true)
  - [ ] `supersession_record` — Old catalog classifications (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G08-002 — Verify module structure policies are complete and consistent

- **Category:** `migration_rollback`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `94`

- **Phase references:** `PHASE-11`
- **Procedure:**
  - [ ] Validate container inventories, profiles, root artifacts, packaging, schema placement, state contract, and global-root policy.
  - [ ] Verify every module has exactly one primary profile and evidence-backed extensions.
- **Expected results:**
  - [ ] Modules with missing profile == 0
  - [ ] Unsupported empty folders == 0
  - [ ] Unresolved packaging decisions == 0
  - [ ] Unowned global roots == 0
- **Required evidence:**
  - [ ] `artifact` — Policy and inventory artifacts (minimum: 1; freshness required: true)
  - [ ] `approval_record` — Policy decisions (minimum: 1; freshness required: true)
  - [ ] `schema_validation` — Policy schema validation (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G08-003 — Verify every tracked repository path has one approved disposition

- **Category:** `migration_rollback`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `191`

- **Phase references:** `PHASE-12`
- **Procedure:**
  - [ ] Compare Git tracked-file inventory to the file-destination matrix.
  - [ ] Verify multi-owner, unmapped, generated, runtime-only, archive, and global paths have governed dispositions.
- **Expected results:**
  - [ ] Tracked paths missing from matrix == 0
  - [ ] Duplicate unexplained source paths == 0
  - [ ] needs_review dispositions at migration completion == 0
- **Required evidence:**
  - [ ] `migration_map` — Complete file-destination matrix (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Tracked-path coverage validation (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G08-004 — Verify target tree and migration artifacts are generated from approved inputs

- **Category:** `migration_rollback`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `181`

- **Phase references:** `PHASE-13`
- **Procedure:**
  - [ ] Regenerate target tree, rename map, impact report, rollback map, and validation report.
  - [ ] Trace inputs to approved identity, policy, and destination records.
- **Expected results:**
  - [ ] Generated artifacts match committed bytes.
  - [ ] Hand-authored proposed tree is non-authoritative.
  - [ ] Every move has an inverse rollback entry.
- **Required evidence:**
  - [ ] `migration_map` — Generated rename and target maps (minimum: 1; freshness required: true)
  - [ ] `path_impact_report` — Path consumer report (minimum: 1; freshness required: true)
  - [ ] `rollback_result` — Rollback map validation (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Generation provenance (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G08-005 — Verify path consumers and runtime-constrained names

- **Category:** `migration_rollback`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `221`

- **Phase references:** `PHASE-13`, `PHASE-14`, `PHASE-15`
- **Procedure:**
  - [ ] Scan code, CI, packaging, docs, Docker, PowerShell, MT4 deployment, MQL4 includes, and runtime file references.
  - [ ] Verify runtime-constrained folders remain conventional.
- **Expected results:**
  - [ ] Unresolved path consumers == 0
  - [ ] Invalid renamed runtime-constrained folders == 0
  - [ ] Hardcoded obsolete paths == 0
- **Required evidence:**
  - [ ] `path_impact_report` — Complete path-consumer report (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Post-migration stale-path scan (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G08-006 — Verify representative pilot migrations

- **Category:** `migration_rollback`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `80`

- **Phase references:** `PHASE-14`
- **Procedure:**
  - [ ] Confirm pilot set covers pure Python, Python/MT4, UI/backend, and shared-kernel or low-implementation classes.
  - [ ] Verify imports, tests, packaging, CI paths, MT4 paths where applicable, structure validation, and rollback.
- **Expected results:**
  - [ ] All required pilot classes represented.
  - [ ] Pilot validations pass.
  - [ ] Every pilot rollback was executed successfully.
- **Required evidence:**
  - [ ] `test_report` — Pilot test results (minimum: 1; freshness required: true)
  - [ ] `rollback_result` — Pilot rollback results (minimum: 1; freshness required: true)
  - [ ] `pr_record` — Pilot PRs (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G08-007 — Verify bounded wave execution and no-big-bang discipline

- **Category:** `migration_rollback`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `193`

- **Phase references:** `PHASE-15`
- **Procedure:**
  - [ ] Review wave maps, PRs, changed paths, validations, and rollback checkpoints.
  - [ ] Verify each wave began from green master and did not exceed approved scope.
- **Expected results:**
  - [ ] Unauthorized cross-wave paths == 0
  - [ ] Each wave has independent validation and rollback evidence
  - [ ] No big-bang migration PR
- **Required evidence:**
  - [ ] `migration_map` — Wave definitions (minimum: 1; freshness required: true)
  - [ ] `pr_record` — Wave PRs (minimum: 1; freshness required: true)
  - [ ] `rollback_result` — Wave rollback checkpoints (minimum: 1; freshness required: true)
  - [ ] `diff` — Wave changed files (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G08-008 — Verify post-migration repository structure and behavior

- **Category:** `migration_rollback`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `57`

- **Phase references:** `PHASE-15`, `PHASE-16`
- **Procedure:**
  - [ ] Run final structure validators, tracked-path coverage, stale-path scan, imports, packaging, tests, deployment checks, and MT4-specific checks where applicable.
- **Expected results:**
  - [ ] Structure validation errors == 0
  - [ ] Unmapped tracked paths == 0
  - [ ] Runtime compatibility regressions == 0
  - [ ] Rollback maps remain valid
- **Required evidence:**
  - [ ] `raw_validator_output` — Final structure validation (minimum: 1; freshness required: true)
  - [ ] `test_report` — Full runtime/build test results (minimum: 1; freshness required: true)
  - [ ] `rollback_result` — Final rollback-map verification (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-08 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-09 — CI, clean clone, and operational readiness

**Purpose:** Verify the delivered registry system is enforced, reproducible, consumed, supportable, and resistant to future drift.

**Depends on:** `VERIFY-GATE-08`

**Target-plan phases:** `PHASE-01`, `PHASE-02`, `PHASE-09`, `PHASE-10`, `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Do not declare the registry system ready for normal operation.

### [ ] VER-G09-001 — Verify required CI checks executed and passed

- **Category:** `operational_readiness`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `when_ci_available`  
- **Fail closed:** `true`  
- **Mapped obligations:** `616`

- **Phase references:** `PHASE-01`, `PHASE-02`, `PHASE-10`, `PHASE-16`
- **Procedure:**
  - [ ] Resolve required check names from current ruleset.
  - [ ] Verify checks ran on the target commit and completed successfully.
  - [ ] Reject skipped, neutral, cancelled, or startup-blocked jobs.
- **Expected results:**
  - [ ] All required checks executed.
  - [ ] All required checks concluded success.
  - [ ] No missing or renamed required check is silently ignored.
- **Required evidence:**
  - [ ] `ci_run` — Required check runs and job details (minimum: 1; freshness required: true)
  - [ ] `repository_state` — Ruleset-required check names (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G09-002 — Verify CI controls are blocking at the correct maturity state

- **Category:** `operational_readiness`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `639`

- **Phase references:** `PHASE-01`, `PHASE-02`, `PHASE-09`, `PHASE-10`, `PHASE-16`
- **Procedure:**
  - [ ] Inspect workflow configuration and registry maturity/cutover state.
  - [ ] Verify structural and parity regression checks are blocking, and canonical registries have no report-only escape path.
- **Expected results:**
  - [ ] Blocking checks use no continue-on-error.
  - [ ] Canonical registries have no report-only bypass.
  - [ ] Advisory findings are limited to explicitly nonblocking scope.
- **Required evidence:**
  - [ ] `artifact` — Workflow files (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — CI policy scan (minimum: 1; freshness required: true)
  - [ ] `authority_map` — Registry maturity state (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G09-003 — Verify at least one real downstream registry consumer

- **Category:** `operational_readiness`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `119`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Identify downstream consumers and their registry inputs.
  - [ ] Trace build-manifest provenance.
  - [ ] Use mutation evidence from Gate 07 to prove dependency.
- **Expected results:**
  - [ ] At least one CI or build consumer uses registry output.
  - [ ] Consumer provenance chain resolves.
  - [ ] Consumer break-and-restore proof passes.
- **Required evidence:**
  - [ ] `artifact` — Consumer configuration or generated artifact (minimum: 1; freshness required: true)
  - [ ] `consumer_failure_proof` — Break-and-restore test (minimum: 1; freshness required: true)
  - [ ] `ci_run` — Consumer CI job (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G09-004 — Verify registry operations runbook is executable

- **Category:** `operational_readiness`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `119`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Follow the runbook in a disposable branch to add, change, and retire fixture records.
  - [ ] Verify schema, reference, generation, PR evidence, and non-deletion retirement rules.
- **Expected results:**
  - [ ] Runbook alone is sufficient.
  - [ ] Add/change/retire walkthrough passes.
  - [ ] No undocumented mandatory step is required.
- **Required evidence:**
  - [ ] `runbook` — Registry operations runbook (minimum: 1; freshness required: true)
  - [ ] `command_transcript` — Runbook walkthrough (minimum: 1; freshness required: true)
  - [ ] `mutation_result` — Add/change/retire fixture results (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G09-005 — Verify CODEOWNERS and PR templates enforce registry workflow

- **Category:** `operational_readiness`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `119`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Inspect CODEOWNERS and PR templates.
  - [ ] Verify authored registry paths require appropriate review and templates request generated diff/evidence.
- **Expected results:**
  - [ ] Canonical authored registry paths are covered.
  - [ ] Required review cannot be bypassed under normal rules.
  - [ ] Registry PR template contains evidence and generated-diff sections.
- **Required evidence:**
  - [ ] `artifact` — CODEOWNERS and PR template files (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Coverage scan (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G09-006 — Verify clean-clone and disaster recovery instructions

- **Category:** `operational_readiness`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `119`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Execute clean-clone workflow and documented recovery/rollback steps in isolation.
  - [ ] Verify authoritative inputs can regenerate outputs and status.
- **Expected results:**
  - [ ] Clean-clone verification passes.
  - [ ] Recovery instructions restore a valid system.
  - [ ] No hidden workstation state is required.
- **Required evidence:**
  - [ ] `command_transcript` — Clean-clone and recovery transcript (minimum: 1; freshness required: true)
  - [ ] `rollback_result` — Recovery test (minimum: 1; freshness required: true)
  - [ ] `runbook` — Recovery instructions (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G09-007 — Verify final supersession sweep

- **Category:** `operational_readiness`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Audit architecture, module, process, contract, registry, migration, and plan documents against doc authority.
  - [ ] Classify each as current authority, registered retained authority, superseded with pointer, archived, or generated.
- **Expected results:**
  - [ ] Undispositioned legacy documents == 0
  - [ ] Parallel active authorities == 0
  - [ ] Superseded documents have pointers
- **Required evidence:**
  - [ ] `supersession_record` — Final document authority sweep (minimum: 1; freshness required: true)
  - [ ] `routing_resolution` — Routing validation (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G09-008 — Verify ongoing drift prevention after completion

- **Category:** `operational_readiness`  
- **Severity:** `high`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Review scheduled/triggered validation, required checks, ownership, change policy, and generated artifacts.
  - [ ] Verify future changes must pass the same controls.
- **Expected results:**
  - [ ] Ongoing validation is integrated into normal PR flow.
  - [ ] No manual-only critical drift control remains without assigned owner.
  - [ ] Change policy names escalation and rollback paths.
- **Required evidence:**
  - [ ] `artifact` — Ongoing governance configuration (minimum: 1; freshness required: true)
  - [ ] `ci_run` — Normal PR validation evidence (minimum: 1; freshness required: true)
  - [ ] `runbook` — Change policy (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-09 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## VERIFY-GATE-10 — Final declaration and evidence seal

**Purpose:** Make the final completion decision only after complete coverage, passing controls, honest claims, and sealed evidence.

**Depends on:** `VERIFY-GATE-09`

**Target-plan phases:** `PHASE-16`

**Pass policy:**
- `blocking_checks_must`: `pass`
- `high_checks_must`: `pass`
- `blocked_counts_as_failure`: `true`
- `not_applicable_requires_approval`: `true`

**On failure:** Publish verified_incomplete or verification_blocked. Never publish verified_complete.

### [ ] VER-G10-001 — Reconcile all blocking and high-severity verdicts

- **Category:** `final_declaration`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Aggregate check verdicts by severity and gate.
  - [ ] Validate required evidence references and freshness.
- **Expected results:**
  - [ ] Blocking fail == 0
  - [ ] Blocking blocked == 0
  - [ ] High fail == 0
  - [ ] High blocked == 0
  - [ ] Missing required evidence == 0
- **Required evidence:**
  - [ ] `artifact` — Aggregated verification report (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Evidence reference validation (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G10-002 — Verify 100 percent obligation coverage and resolution

- **Category:** `final_declaration`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Validate coverage matrix and per-obligation verdicts.
  - [ ] Require every obligation to be pass or validly approved not_applicable.
- **Expected results:**
  - [ ] Total obligations == 1405
  - [ ] Unmapped obligations == 0
  - [ ] Invalid pointers == 0
  - [ ] Unsupported not_applicable == 0
- **Required evidence:**
  - [ ] `coverage_matrix` — Final obligation matrix (minimum: 1; freshness required: true)
  - [ ] `raw_validator_output` — Coverage validator (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G10-003 — Run anti-false-completion audit

- **Category:** `anti_false_completion`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `139`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Evaluate every anti-false-completion control against repository and evidence.
  - [ ] Sample high-risk claims: authority, parity, determinism, CI, cutover, migration, consumer use, and supersession.
- **Expected results:**
  - [ ] Detected unresolved false-completion patterns == 0
  - [ ] Every sampled claim has direct evidence
- **Required evidence:**
  - [ ] `manual_review_record` — Anti-false-completion audit (minimum: 1; freshness required: true)
  - [ ] `coverage_matrix` — Control-to-evidence mapping (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G10-004 — Verify residual findings are scoped and do not contradict completion

- **Category:** `final_declaration`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `117`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Inventory all open issues, warnings, accepted exceptions, and not_applicable verdicts.
  - [ ] Determine whether any contradicts target-plan definition of done or claimed cutover/migration scope.
- **Expected results:**
  - [ ] Residual blockers affecting declared completion == 0
  - [ ] Accepted residuals have owner, rationale, scope, and follow-up
- **Required evidence:**
  - [ ] `manual_review_record` — Residual findings assessment (minimum: 1; freshness required: true)
  - [ ] `decision_record` — Accepted exception decisions (minimum: 0; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G10-005 — Verify final report is evidence-backed and schema-valid

- **Category:** `final_declaration`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `237`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Validate final verification report schema.
  - [ ] Resolve every evidence_id to the evidence manifest and hash.
  - [ ] Verify no result is embedded only as unsupported prose.
- **Expected results:**
  - [ ] Report schema errors == 0
  - [ ] Broken evidence references == 0
  - [ ] Unhashed evidence objects == 0
- **Required evidence:**
  - [ ] `schema_validation` — Verification report validation (minimum: 1; freshness required: true)
  - [ ] `artifact_hash_manifest` — Evidence manifest (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G10-006 — Verify owner completion approval

- **Category:** `final_declaration`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `manual`  
- **Automation:** `manual`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Present the final report, coverage, residuals, hashes, and rollback status to the repository owner.
  - [ ] Record explicit approve, reject, or defer decision.
- **Expected results:**
  - [ ] Final approval exists for a completed status.
  - [ ] Approval identifies target plan hash, target commit, verification spec hash, and report hash.
- **Required evidence:**
  - [ ] `approval_record` — Owner completion decision (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G10-007 — Seal the verification evidence bundle

- **Category:** `final_declaration`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `automated`  
- **Automation:** `fully_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Compute hashes for all run artifacts.
  - [ ] Write final evidence manifest and verify it.
  - [ ] Mark the bundle immutable by policy or release tag.
- **Expected results:**
  - [ ] All evidence files hashed.
  - [ ] Manifest verification passes.
  - [ ] Target commit, plan hash, spec hash, and report hash recorded.
- **Required evidence:**
  - [ ] `artifact_hash_manifest` — Sealed evidence manifest (minimum: 1; freshness required: true)
  - [ ] `commit_record` — Release tag or immutable commit reference (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VER-G10-008 — Publish an honest final status

- **Category:** `final_declaration`  
- **Severity:** `blocker`  
- **Control type:** `detective`  
- **Verification mode:** `hybrid`  
- **Automation:** `partially_automated`  
- **Applicability:** `always`  
- **Fail closed:** `true`  
- **Mapped obligations:** `97`

- **Phase references:** `PHASE-16`
- **Procedure:**
  - [ ] Compare final status language to actual verdicts, cutover states, parity baselines, CI execution, and migration scope.
  - [ ] Reject overstated claims.
- **Expected results:**
  - [ ] Published status is one of verified_complete, verified_incomplete, or verification_blocked.
  - [ ] Every material claim is supported by a report field and evidence IDs.
- **Required evidence:**
  - [ ] `manual_review_record` — Final claim audit (minimum: 1; freshness required: true)
  - [ ] `artifact` — Published verification summary (minimum: 1; freshness required: true)
- **Allowed verdicts:** `pass`, `fail`, `blocked`, `not_applicable`
- **Negative test required:** `false`
- **Remediation on failure:** Stop verification for the affected scope, preserve evidence, and open a focused remediation item before re-running the check.
- **Run result:**
  - [ ] Verdict recorded in run-specific report
  - [ ] Evidence IDs linked
  - [ ] Evidence freshness verified
  - [ ] Findings and remediation owner recorded when not `pass`

### [ ] VERIFY-GATE-10 gate decision

- [ ] All dependency gates passed.
- [ ] All blocker checks passed.
- [ ] All high-severity checks passed.
- [ ] No blocked check remains.
- [ ] Any `not_applicable` verdict has required rationale and approval.
- [ ] Gate verdict and evidence references are recorded in the run report.

## Final completion decision

- [ ] All verification gates pass in order.
- [ ] All blocker and high checks pass.
- [ ] No blocked check remains.
- [ ] All 1405 obligations are mapped and resolved.
- [ ] Every definition-of-done criterion passes.
- [ ] All required evidence is fresh and hash-resolvable.
- [ ] Anti-false-completion controls detect no unresolved blocking pattern.
- [ ] Owner completion approval is recorded.
- [ ] Verification evidence bundle is sealed.

### Allowed final status

- [ ] `verified_complete`
- [ ] `verified_incomplete`
- [ ] `verification_blocked`

### Final declaration controls

- [ ] Exactly one allowed final status is selected.
- [ ] The selected status is supported by the run-specific report.
- [ ] Every evidence reference resolves and is fresh.
- [ ] The evidence bundle is sealed.
- [ ] Owner approval, rejection, or deferral is recorded.
- [ ] No completion claim relies on unsupported prose.

## Integrity note

This checklist is generated from the canonical verification specification. Its check text, ordering, severity, procedure, expected results, evidence requirements, and gate rules must match that specification. Verification results belong in the run-specific report and evidence bundle, not in this file.

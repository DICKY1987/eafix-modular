# EAFIX Process Consolidation Executable Runbook

**Document ID:** `EAFIX-PROCESS-CONSOLIDATION-RUNBOOK`  
**Version:** `1.1.0`  
**Status:** `authored_candidate`  
**Repository:** `DICKY1987/eafix-modular`  
**Baseline commit:** `a5c950410bebee93f6a13632dbcb0ad4577d1d73`  
**Execution controller:** `EAFIX_PROCESS_CONSOLIDATION_COPILOT_CLI_EXECUTION_PLAN_v1_1_0.json`

## 1. Objective

Repair process-authority lineage, freeze the existing S01-S26 top-level spine for this consolidation pass, extract and adjudicate process knowledge, apply only approved field mutations, preserve detailed information as linked record candidates, generate all process projections, and perform an atomic authority cutover without information loss.

This runbook does not authorize a new top-level process step. Evidence for a missing top-level responsibility must enter a governed process change request. It does permit child activities, decisions, states, failure modes, scenarios, variants, and schema-extension candidates.

## 2. Mandatory invariants

1. `process_registry.jsonl` remains exactly 26 top-level records during this pass.
2. Identity fields and module bindings are immutable unless a separate approved decision explicitly changes them.
3. Authority is resolved per fact class, not by one global source tier.
4. No source may populate a field unless the source manifest authorizes that source for the field's fact class.
5. No non-empty value may be overwritten by consolidation automation.
6. Every extraction remains traceable to a source hash and locator.
7. Every applied mutation has a mutation-evidence record and field-level provenance evidence.
8. Conflicts are persisted per source before registry mutation and then routed to the existing conflict queue.
9. Every missing governed cell is populated, lifecycle-exempt, removed by approved schema change, or represented by its exact gap ID.
10. Generated files are projections and must be reproducible from authored sources.
11. Sources are not archived until projection parity, source-consumption verification, and cutover approval pass.
12. Human gates halt automation. Copilot may prepare ballots and evidence but may not choose or approve decisions.

## 3. Sequence

### BOOTSTRAP — Install candidate tooling without authority changes

- Create a `copilot/` branch.
- Copy the v1.1.0 runbook, verifier, source manifest, schemas, and decision templates into their destination paths.
- Do not append DEC-REG-022, modify `process_registry.jsonl`, or regenerate outputs.
- Compile the verifier and parse all JSON/JSONL files.

### AUTH-00 — Establish the verified baseline

- Checkout the baseline commit or an explicitly approved successor.
- Calculate SHA-256 and byte size of `process_registry.jsonl`.
- Bind those values into `process_consolidation_source_manifest_v1_1_0.json` and set `binding_status` to `BOUND`.
- Verify S01-S26 identity, ordering, module bindings, and current generated artifacts.
- Record the baseline evidence report.

Exit gate:

```bash
python tools/registries/verify_process_consolidation.py --repo-root . --gate AUTH-00 --json .state/evidence/process-consolidation/AUTH-00.json
```

### AUTH-01 — Repair and approve authority lineage — HUMAN GATE

Copilot must:

1. search history for the two declared YAML sources;
2. verify available hashes and document the declared-hash mismatch;
3. classify every process artifact as authored authority, generated projection, supporting evidence, historical evidence, or superseded source;
4. resolve the S25 `(loop)` to `F1_FLOW_ORCHESTRATOR` transformation as an approved ownership decision, projection normalization, or unsupported inference;
5. present P1-A, P1-B, and P1-C;
6. obtain an explicit human selection and cutover mode;
7. write `PROCESS_AUTHORITY_LINEAGE_DECISION.json` with status `APPROVED`.

Automation stops until approval exists.

### STEP-00 — Freeze the top-level spine for this pass

- Commit the revised runbook, verifier, manifest, schemas, and proposed `DEC-REG-022`.
- Append `DEC-REG-022` only after AUTH-01 approval and human approval of the decision itself.
- Do not modify the process registry or generated outputs.

### STEP-01 — Adjudicate field policy — HUMAN GATE

- Generate `HD-PC-01_field_adjudication.json` from the template.
- Human selects one disposition for every field.
- Four lifecycle fields should normally be `lifecycle_exempt`.
- `required_for_baseline` means a value is mandatory; a gap ID does not satisfy it without a separate waiver.
- `deferred_with_gap_id` requires an exact per-record gap ID for every missing cell.
- `removed_from_schema` requires an approved schema migration.

Automation stops until the ballot is `APPROVED`.

### STEP-02 — Validate and freeze the source corpus

- Validate the source manifest structurally.
- Verify all 11 active paths, hashes, byte sizes, merge order, and fact-class authority maps.
- Lineage evidence sources are not merge contributors.
- Any new contributing source requires a manifest-version increment and decision amendment.

### STEP-03 — Extract one source per PR

Each extraction PR creates exactly one extraction JSONL file and no registry changes.

Every record must validate against `process_extraction_record.schema.json` and classify its target as one of:

- existing step field mutation;
- linked child record;
- schema-extension candidate;
- top-level process-change candidate;
- conflict candidate;
- non-process information.

### STEP-04 — Produce and apply deterministic mutation sets

For each source in merge order:

1. validate the extraction file;
2. compile a mutation proposal and per-source conflict-candidate file;
3. authorize each candidate by target fact class;
4. apply only empty-to-filled mutations or corroborating provenance appends;
5. write field-level mutation evidence;
6. never overwrite a non-empty value;
7. preserve linked-record and schema-extension candidates outside the step registry until adjudicated.

A source PR may change the registry, its mutation-evidence file, its field-provenance evidence file, and its conflict-candidate file. It may not modify another source's artifacts.

### STEP-05 — Route and adjudicate material process conflicts

- Compile per-source conflict candidates into `registry_conflict_queue.jsonl`.
- Preserve existing queue records.
- Material process conflicts block canonical projection and cutover; unrelated repository conflicts do not.
- Human review resolves, defers, rejects, or waives each material conflict.

### STEP-06 — Close every governed missing cell

For each record and each adjudicated field:

- `required_for_baseline`: value must be populated;
- `deferred_with_gap_id`: value or exact `GAP::PROCESS::<STEP_CODE>::<FIELD>` must exist;
- `lifecycle_exempt`: empty is accepted;
- `removed_from_schema`: field must be absent after approved schema migration.

Validation is per record and field. Aggregate fill percentages are informational only.

### STEP-07 — Generate and validate projections

- Fix `build_registries.py` so a missing `jsonschema` dependency exits nonzero.
- Extend the process Markdown generator to emit the enriched fields and linked views.
- Generate current JSON, Markdown, build manifest, completeness report, conflict report, module views, subsystem views, and approved diagrams.
- Confirm authored/generated identity parity and complete S01-S26 Markdown coverage.
- Run the generator twice and require a clean diff.

### STEP-08 — Atomic authority cutover and source relocation — HUMAN GATE

After human acceptance of STEP-07:

- set the 26 records to the approved authority status;
- record supersession paths and decisions;
- update document authority and AI routing;
- move only approved legacy sources to their declared archive paths without content changes;
- preserve live registries;
- rebind generated artifacts to the approved source hash;
- run cutover validation in the same commit.

The verifier expects archived paths after this step and verifies unchanged content hashes.

### STEP-09 — Post-cutover source-consumption and drift verification

- Prove every substantive source statement has a disposition.
- Prove no active competing process authority remains.
- Prove generated files reproduce from the approved authored source.
- Publish residual gaps, approved deferrals, linked-record backlog, and any future process-change requests.

## 4. Required Copilot behavior

- Use one branch and PR per runbook step unless a step explicitly requires one PR per source.
- Always pass `--base-ref` to the verifier in PR validation so mutation scope is checked against the target branch.
- Never use `--no-verify`, force push, direct default-branch changes, or automated human approvals.
- Never invent source values or silently normalize contradictions.
- Stop on exit code 1 or 2.
- Stop at every human gate and output a concise decision packet.
- Store command output and JSON gate reports under `.state/evidence/process-consolidation/`; do not treat runtime evidence as authored process authority.

## 5. Definition of complete

The work is complete only when STEP-09 passes, the final process source is formally approved, all material conflicts are resolved or explicitly waived, every governed missing cell has a valid disposition, generated projections are deterministic, archived source hashes remain unchanged, and normal AI routing exposes only the approved authority and its generated views.

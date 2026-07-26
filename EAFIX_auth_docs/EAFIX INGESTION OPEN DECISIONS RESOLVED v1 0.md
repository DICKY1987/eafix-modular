# EAFIX Ingestion Matrix — Open Decisions, Resolved

- Repository: `DICKY1987/eafix-modular` · Evidence pinned at commit `e846d04a6eede56e6b790701d0fa762fe90297d6`
- Companion to: `EAFIX_REGISTRY_INGESTION_MATRIX_SKELETON_v0_1_0.json`
- Status: **recommended dispositions for owner ratification**

Each decision below states the choice, the options considered, the reasoning, a confidence
level, and the concrete action it triggers. Confidence reflects how much the call is driven by
verifiable evidence versus my architectural judgment on your behalf:

- **Evidence-forced** — the repo data determines the answer; low room for opinion.
- **Judgment** — a defensible design choice I'm making for you; reversible.

The governing rule throughout is the project's own evidence hierarchy: a real schema or code
(E1/E2, primary) outranks a name used in a document or process step (E3, corroboration only),
and a generated projection is never authority over an authored source.

---

## OD-1 — IndicatorVector vs IndicatorSnapshot · **Choice: canonicalize `IndicatorVector`; make `IndicatorSnapshot` an alias**

**Plain terms:** one data structure (the bundle of indicator values a step emits) is referred to
by two different names in different places. We need one canonical name.

**Options:** (a) IndicatorVector is canonical; (b) IndicatorSnapshot is canonical; (c) keep both
as separate contracts.

**Decision: (a).** `IndicatorVector` wins. Confidence: **Evidence-forced.**

**Why:** `IndicatorVector` has an actual JSON Schema on disk
(`contracts/events/…_IndicatorVector@1.1.json`) and is already `canonical_candidate` in the
contract registry. `IndicatorSnapshot` has no schema and no model — it is `source_defined_only`,
appearing only as the output-contract label of process step **S09** and in a manifest bundle.
Under the E1/E2-over-E3 rule, a versioned schema (primary artifact) beats a name used in a
process document (authority reference). Option (c) is wrong because both names denote the same
payload — keeping two contracts would manufacture a phantom divergence.

**Triggers:** update `process_step_catalog.json` step **S09** `output_contract`
`IndicatorSnapshot → IndicatorVector`; add `IndicatorSnapshot` to the IndicatorVector record's
`aliases[]` so historical references still resolve; close the registry conflict.

---

## OD-2 — OrderIntent.side vocabulary · **Choice: `BUY`/`SELL` is canonical; fix the model**

**Plain terms:** the order's direction field is defined two ways — the schema says `BUY`/`SELL`,
the Python model says `LONG`/`SHORT`. We need one vocabulary.

**Options:** (a) BUY/SELL; (b) LONG/SHORT; (c) allow both / map between them.

**Decision: (a) BUY/SELL.** The Pydantic model is the defect and must be corrected. Confidence:
**Evidence-forced.**

**Why — three independent lines all point the same way:**
1. **Contract-first authority.** The published, versioned schema (`OrderIntent@1.2`) is the
   interface; the model must conform to it, not the reverse.
2. **Domain semantics.** `BUY`/`SELL` describes an *order* (an instruction you send); `LONG`/`SHORT`
   describes a *position* (net exposure). An `OrderIntent` is an order instruction, so BUY/SELL is
   the correct concept. `OrderSide=LONG/SHORT` conflates position-side with order-side.
3. **Execution boundary.** This system executes through the MT4/MQL4 bridge, where order ops are
   `OP_BUY`/`OP_SELL`. BUY/SELL is what actually crosses the execution boundary.

The fix is also cheap and low-risk: the same model file **already defines** a
`TradingSide` enum = `BUY`/`SELL` (used for signals). `OrderIntent.side` should point at that,
not at the anomalous `OrderSide=LONG/SHORT`.

**Triggers:** repoint `OrderIntent.side` to the BUY/SELL enum in
`contracts/models/…_event_models.py`; audit whether `OrderSide` (LONG/SHORT) has any legitimate
consumer or is dead code to delete; re-run contract validators; close the registry conflict.

---

## OD-3 — Two divergent `ReentryDecision` definitions · **Choice: split into two contracts**

**Plain terms:** two genuinely different data shapes share the name `ReentryDecision`. One is the
decision the re-entry logic produces (an event); the other is the row persisted to the CSV
matrix. They are not the same thing — they only collided on a name.

**Options:** (a) pick one, delete the other; (b) merge into one superset contract; (c) split into
two distinctly-named contracts.

**Decision: (c) split.** Confidence: **Evidence-forced on "they're different"; Judgment on the naming.**

**Why:** the event model (`reentry_key`, `generation`, `should_reenter`, `matrix_outcome`,
`confidence_score`) is a decision-event; the CSV model (`trade_id`, `hybrid_id`, `outcome_class`,
`duration_class`, `reentry_action`) is a persistence row for the matrix lookup. These map to two
different modules/steps in the system (the matrix-lookup step vs the re-entry-intent step), so
both are real and both are needed — options (a) and (b) would destroy or muddle real information.
The name `ReentryDecision` stays with the **event/decision** contract, because that is what the
versioned schema `ReentryDecision@1.0` is modeling (id/timestamp/symbol/state/action/rationale/
confidence — a decision-event shape). The CSV shape is renamed to its own contract (suggested:
`ReentryMatrixOutcome`, or `ReentryDecisionRow` if you prefer literalness) and gets its own schema.

Note: the schema and the event model have **also** drifted from each other, so this isn't just a
rename — reconcile the event model to the schema (schema is authority as the published contract),
and author a schema for the newly-split CSV contract.

**Triggers:** rename the CSV-model contract; author its schema; reconcile the event model to
`ReentryDecision@1.0`; update producer/consumer step links for both; close the conflict. This one
benefits from a quick sanity check on the naming from you, since it encodes intent.

---

## OD-4 — Regenerate the 27 context packets before ingest? · **Choice: Yes, regenerate first**

**Plain terms:** the context packets (module enrichment data) were generated on 2026-05-18, use
Windows backslash paths, and carry over-broad "forbidden files" lists. Do we ingest them as-is or
rebuild them from current sources first?

**Options:** (a) ingest as-is (fast); (b) regenerate from current catalogs at HEAD, then ingest;
(c) skip packets entirely.

**Decision: (b) regenerate first.** Confidence: **Evidence-forced.**

**Why:** ingesting them as-is would import three known defects directly into the registries:
Windows backslash paths (break path normalization on Linux/CI), over-broad `forbidden` lists
(which violate your own established rule that forbidden ownership is a *derived complement*, not an
enumerated list), and provenance pinned to a two-month-old commit. That is exactly the
"stale projection → authored data" contamination the SSOT design exists to prevent. Skipping them
(c) throws away genuinely useful module-level enrichment. Regeneration keeps the value and drops
the rot.

**Dependency to flag:** "regenerate" presumes a working packet generator pinned to HEAD. If that
generator doesn't currently exist or run clean, building/fixing it becomes a prerequisite task —
but that does not change the decision; it just means stale packets stay quarantined until
regeneration is possible.

**Triggers:** confirm/repair the packet generator; regenerate all 27 against current
`module_registry` + file inventory at HEAD with POSIX path normalization and derived-complement
forbidden lists; then ingest.

---

## OD-5 — DAG node-id → process-step crosswalk ownership · **Choice: an explicit authored crosswalk artifact; `process_step_catalog` remains authority**

**Plain terms:** the DAG graph uses descriptive node names; the canonical process catalog uses
step IDs (S01, S09, …). Before the DAG can feed the process/integration registries, its nodes must
be mapped to canonical step IDs. Where does that mapping live and who owns it?

**Options:** (a) map inline inside the ingestion script (implicit); (b) author a standalone,
governed crosswalk artifact; (c) exclude the DAG until a crosswalk exists.

**Decision: (b) explicit crosswalk artifact.** Confidence: **Judgment (high).**

**Why:** the project already uses exactly this pattern for module aliases
(`identity_crosswalk.json`), so a `dag_process_crosswalk` artifact is consistent, auditable, and
reusable — whereas an inline mapping (a) buries a set of judgment calls inside a script where they
can't be reviewed or ratified. `process_step_catalog` stays the authority: canonical step IDs win,
the DAG is evidence that maps onto them. Unmapped DAG nodes go to `needs_review`, never silently
dropped. Option (c) is unnecessarily blocking — the DAG's edges, gates, and SLAs are valuable and
can be ingested incrementally as nodes are crosswalked.

**Triggers:** create `dag_process_crosswalk` (DAG node → canonical step ID, with a
`mapping_basis` per row); route ambiguous rows to you for ratification; ingest DAG edges/gates only
for crosswalked nodes.

---

## OD-6 — Component identity · **Choice: retire "component" as a distinct governed entity**

**Plain terms:** there is no component registry in the canonical set, and "component" shows up only
as a reserved field from the older EA-REG design. Do we make components a real governed entity,
derive them, or drop the concept?

**Options:** (a) stand up a distinct component registry (11th registry); (b) derive components from
module/work-cell records if ever needed; (c) retire the concept.

**Decision: (c) retire, with (b) as the fallback if a real need appears.** Confidence:
**Judgment (high).**

**Why:** the only `components/` artifact on master is `components/registry.yaml`, and it is a
catalog for a **different platform** ("CLI Multi-Rapid Enterprise Orchestration Platform") — it has
nothing to do with the 34 EAFIX trading modules. There is no EAFIX component authority anywhere in
the canonical registries; `component_id` appears only in `ui_catalog.json` in an unrelated UI
sense. Standing up a governed component registry (a) would be over-engineering a concept nothing
currently uses — the exact kind of disproportionate solution to avoid; the module + work-cell model
already provides the needed granularity. If a genuine component-level grouping is ever required, it
should be **derived** from module/work-cell records, not authored as a parallel authority.

**Triggers:** archive `components/registry.yaml` to the superseded/do-not-route area (or confirm
it's out-of-project and remove it); drop the reserved `component_ids` column when reusing EA-REG
generator logic; record "component = retired, derive-if-needed" as a decision so it doesn't
resurface.

---

## OD-7 — Promote generated-snapshot records into the authored registry? · **Choice: No**

**Plain terms:** the generated `contract_registry.current.json` snapshot is populated. Should any of
its records be copied up into the authored `contract_registry.jsonl`?

**Options:** (a) yes, promote snapshot records; (b) no, snapshot is a diff/parity baseline only.

**Decision: (b) No.** Confidence: **Evidence-forced (and empirically moot).**

**Why — principle:** a generated projection is downstream of authored authority; promoting it back
up would invert the SSOT direction and let a machine-rendered artifact become the source of truth.
Any gap must be re-derived from primary source (E1/E2) and authored explicitly; a snapshot-only
record with no primary backing goes to `needs_review`, never straight into the authored registry.
**Why — empirical:** it's also moot here — I diffed the two, and the authored registry and the
snapshot cover the **identical 97 contracts, zero delta in either direction.** There is literally
nothing to promote.

**Triggers:** keep the snapshot classified `generated_projection_never_write_target` in the matrix;
use it only as a parity/diff baseline during burndown; treat any future divergence as a signal to
author from source.

---

## Summary

| ID | Decision | Confidence |
|----|----------|-----------|
| OD-1 | `IndicatorVector` canonical; `IndicatorSnapshot` → alias; fix step S09 | Evidence-forced |
| OD-2 | `OrderIntent.side` = BUY/SELL (schema); fix the LONG/SHORT model | Evidence-forced |
| OD-3 | Split into two contracts (event keeps name; CSV row renamed + schema'd) | Evidence-forced / naming = judgment |
| OD-4 | Regenerate the 27 context packets before ingest | Evidence-forced |
| OD-5 | Author an explicit DAG→step crosswalk; catalog stays authority | Judgment (high) |
| OD-6 | Retire "component" as a governed entity; derive if ever needed | Judgment (high) |
| OD-7 | Do not promote snapshot records (and there's a zero delta anyway) | Evidence-forced |

Five of seven are settled by the repository's own evidence. The two judgment calls (OD-5, OD-6)
are both low-risk and reversible, and both follow patterns the project already uses
(explicit crosswalk artifacts; proportionality over speculative governance). OD-3's only genuinely
discretionary part is the name of the split-out CSV contract.

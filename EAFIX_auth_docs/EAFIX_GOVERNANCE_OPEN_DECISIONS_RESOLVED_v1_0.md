# EAFIX Governance Remediation — Six Open Decisions, Resolved

- Repository: `DICKY1987/eafix-modular` · Evidence pinned at commit `43f096239a492130f20e864418b0996df09439f1` (current `origin/master`)
- Companion to: `EAFIX_GOVERNANCE_DEFECT_REMEDIATION_PLAN_v1_0_0.json` (plan id `EAFIX-GOVERNANCE-DEFECT-REMEDIATION-001`)
- Registry additions: `EAFIX_governance_decision_registry_additions.jsonl` (`DEC-REG-015` … `DEC-REG-021`)
- Status: **recommended dispositions for owner ratification** — every HD gate remains formally open until you record a decision

Same convention as the ingestion decisions: each entry states the choice, the options considered,
the reasoning, a confidence level, and the concrete action it triggers.

- **Evidence-forced** — the repo data determines the answer; low room for opinion.
- **Judgment** — a defensible design choice made on your behalf; reversible.

The governing rule throughout is the project's own evidence hierarchy (E1/E2 primary, E3 corroboration
only) and its derive-don't-fabricate principle.

> **Numbering dependency.** These records are numbered `DEC-REG-015` onward on the assumption that the
> ingestion decisions `DEC-REG-008`…`014` are appended first. If they are not, renumber this block to
> start at `DEC-REG-008`. The registry currently holds `DEC-REG-001`…`007`.

> **Three of these recommendations changed** from the versions embedded in the remediation plan, because
> verification produced evidence the plan did not have. Those are flagged **[REVISED]**.

---

## HD-01 — MASTER-V2 cites two source documents that never existed · **Choice: recover first; if that fails, mark unverifiable *in place* (new option D)** **[REVISED]**

**Plain terms:** the master plan's provenance record says it absorbed two documents — a v1.1.0
remediation plan and its amendment — and gives exact hashes for both. Neither has ever existed in the
repository. We have to make the provenance truthful without wrecking the plan.

**Options:** (a) locate and commit the files; (b) delete the two entries and fix the counts;
(c) ratify with a standing exception, leaving plan bytes untouched; **(d) new** — keep both entries in
place but mark them unverifiable.

**Decision: (a) first, time-boxed; then (d).** Confidence: **Evidence-forced on the cost of (b);
Judgment on preferring (d) over (c).**

**Why:** full-history search (`git log --all --diff-filter=ADMR`) returns no commit on any ref that ever
touched either filename. They were almost certainly produced in a chat session and never committed.
Recovery is cheap and is the only path that fully preserves provenance, so it must be attempted — but
it's a search, not a decision. The real decision is the fallback.

**Option (b) is disproportionately expensive, and this is the finding that changed my recommendation.**
The obligation matrix carries **13 positional JSON pointers** of the form
`/source_plan_consolidation/sources/N` — one per source, indices 0–12. The two unverifiable sources sit
at **indices 2 and 3**. Deleting them shifts indices 4–12 down by two and leaves `/sources/11` and
`/sources/12` dangling — **corrupting 11 of 13 pointers** and forcing a full obligation-matrix
regeneration. That is a large blast radius for a two-entry correction.

Option (c) is structurally safe but leaves a false assertion standing in the root authority document.
Option (d) gets both: keep the array shape so every pointer still resolves, while changing the entries
to say what is actually true. Both (b) and (d) change plan bytes and therefore require the verification
spec `target_plan` to be re-bound **in the same commit** — under (d) that's one mechanical edit.

**Also required under (d):** `GATE-AUTHORITY-PARITY-TOOL` currently carries the note *"parity mismatches
are advisory in v1.1.0."* That's live gate logic resting on the unverifiable document. Its basis must be
restated from evidence that exists, or the gate flagged re-derivation-required.

**Triggers:** time-boxed search of chat exports / local downloads; on failure, set both entries'
`disposition` to `unverifiable_absent_from_repository_history` with the absence evidence attached, keep
indices 2 and 3 occupied, rewrite the parity-gate note, recompute the plan hash, and update
`target_plan.sha256` and `byte_size` in the same commit. Re-run the package validator.

---

## HD-02 — Canonical filename and archive destination · **Choice: the bare filename; archive to `99_archive_superseded_do_not_route/`**

**Plain terms:** five identical copies of the master plan sit in the docs root, and eleven superseded
source plans sit next to the active one with nothing marking them as superseded.

**Options:** (a) retain the spec-named bare filename; (b) bind to some other filename.
Archive sub-options: ARC-A `99_archive_superseded_do_not_route/`; ARC-B `superseded/`; ARC-C metadata only.

**Decision: (a) + ARC-A.** Confidence: **Evidence-forced.**

**Why:** the verification spec's `target_plan.filename` already names
`EAFIX_SSOT_REGISTRY_SYSTEM_FINAL_MERGED_IMPLEMENTATION_PLAN_v2_0_0.json`. Selecting it produces zero
reference churn; any other choice forces a coordinated spec update for no benefit. Deleting the other
four is lawful only because their bytes are provably identical — the plan requires re-verifying hash
equality at the moment of deletion, not trusting this document.

On the destination: `99_archive_superseded_do_not_route/` is the *governed* archive — it carries
`archive_manifest.json` and an explicit `routing_policy: do_not_route_by_default`, and it belongs to the
numbered folder scheme. `superseded/` holds four files but has **no manifest and no routing policy**, so
it cannot actually enforce non-routing. ARC-C is rejected because metadata alone doesn't stop a
path-based consumer from resolving a superseded plan.

**Adjunct, offered separately rather than folded in:** the repo currently has *two* archive locations.
Consolidating `superseded/`'s four files into `99_archive/` would leave one. Small and useful, but it is
scope beyond the finding — take it or leave it deliberately.

**Triggers:** re-hash all five, retain the bare filename, `git rm` the other four, grep for dangling
references; move superseded plans to `99_archive/`, register each in `archive_manifest.json`, and resolve
the manifest entries currently sitting at `reviewer_decision: pending`.

---

## HD-03 — Which `doc_authority.json` is canonical · **Choice: merge into one, at the `00_` location** **[REVISED]**

**Plain terms:** two files both act like the document that decides which documents win. One says it's the
only one and that the other was deleted; the other still exists and is dated a day later.

**Options:** (a) `00_doc_control_and_authority/` copy wins; (b) root copy wins; (c) merge into one.

**Decision: (c) merge, canonical at `00_doc_control_and_authority/doc_authority.json`.**
Confidence: **Evidence-forced on feasibility; Judgment on the location.**

**Why — the plan assumed these had incompatible schemas and that merging was the high-effort option.
Verification shows the opposite.** Both files use the same core entry fields (`authority_level`,
`classification`, `description`); the `00_` schema is a **strict superset**, adding `relative_path`,
`path_status`, `supersedes`, `superseded_by`. Entry overlap is **exactly one document** — the routing
instructions — and the two files **agree** on it (both `authority_level 1`, `canonical`). The union is
**28 entries with zero conflicts**. The merge is close to mechanical.

More importantly, they are **functionally complementary, not duplicative**. The root file carries policy
the `00_` file has *none* of: `decision_rule` (the precedence chain the supersession checklist actually
cites), `control_files`, and `subject_authorities`. The `00_` file carries the 24-entry document inventory
the root file almost entirely lacks. Choosing either alone discards a whole functional half — which is
why (a) and (b) are both wrong. The `00_` location is preferred because it sits in the folder named for
document control and its schema is the superset that can absorb the other without loss.

**Triggers:** produce the entry-level reconciliation, merge into the `00_` file adopting its entry schema
plus the root's three policy blocks, archive the root copy with supersession metadata, and repoint
`authority_and_supersession_checklist.md` step 1.

---

## HD-03 adjunct — Canonical documents living in the do-not-route archive · **Choice: restore or downgrade; a canonical document may not sit in the archive**

**Plain terms:** two documents are declared top-authority *and* stored in the folder that means
"never route to this."

**Decision: resolve each — restore to a routable location, or downgrade the classification.**
Confidence: **Evidence-forced.**

**Why:** four `doc_authority` entries don't resolve. Two of them are `authority_level 1, canonical`:
`eafix_project_knowledge_reference_routing_instructions.json` and
`EAFIX_auth_docs/Y_module governance glossary.json` — **both now physically in
`99_archive_superseded_do_not_route/`**. The routing-instructions file was moved there by commit
`e846d04a` (*"Archive project knowledge routing instructions"*, PR #83) while its authority record still
describes it as *"Canonical routing instructions for AI agents… Single authoritative copy at repository
root."* That copy is gone; the record was never updated.

This is a **systematic pattern, not a one-off** — two separate L1 canonical documents were archived
without write-back to `doc_authority`. Worth fixing the process, not just the two records. The remaining
two broken entries are the EA-REG references already self-documented in-file as *FILE NOT FOUND as of
2026-06-26*; `ALIGNMENT_VALIDATION_REPORT.md` is classified `generated`, so it should carry a generation
instruction rather than a path claim.

**Triggers:** decide restore-vs-downgrade per document; convert the generated artifact's entry to a
generation instruction; add an archival write-back step so future moves update `doc_authority`.

---

## HD-04 — The 34-module identity universe · **Choice: registry's 34 is the universe; `SHARED_LIBS` sits outside it** **[REVISED]**

**Plain terms:** three sources disagree about how many modules exist — 27, 34, or zero. Before anything
can ratify "the 34-module universe," that has to resolve.

**Options:** (a) populate the vNext catalog from `module_registry.jsonl`; (b) populate from an
owner-supplied external source; (c) retire the vNext catalog.

**Decision: (a)**, with the universe defined as registry ids `…0001`–`…0034`, and `SHARED_LIBS`
(`…0099`) classified as a non-atomic bucket **outside** the 34.
Confidence: **Evidence-forced on the arithmetic; Judgment on excluding `SHARED_LIBS`.**

**Why — the "27 vs 34" conflict dissolves under set comparison.** The catalog's 27 ids are **26 atomic
modules** (`…0001`–`…0026`), *all* present in the registry, **plus one outlier** `…0099` = `SHARED_LIBS`.
The registry's 34 are `…0001`–`…0034` — a clean superset with **eight modules added** (`…0027`–`…0034`).
So the real comparison is *26 atomic + 1 non-atomic bucket* versus *34 atomic*, not 27 versus 34.

Two independent corroborations: `CONFLICT::PROCESS_COVERAGE` records that the process catalog models
**26 of 34** modules, and `process_registry.jsonl` holds **exactly 26** records. The 26 are the original
universe; eight were added later. Everything lines up.

`SHARED_LIBS` is excluded because it is a **different kind of entity** — `layer: unassigned`, empty
`scope_in`/`scope_out`, purpose *"owns cross-cutting shared libraries used across canonical modules."*
It's a catch-all for shared code, not an atomic trading module. Folding it in would corrupt the semantics
that MASTER-V2 PHASE-06 ratifies. Option (c) is rejected because the catalog schema carries enrichment
fields the registry doesn't.

**This also resolves `CONFLICT::MODULE_UNIVERSE`** — one of the nine conflicts your ingestion decisions
left open.

**Triggers:** author the field-mapping record, populate the vNext `modules[]` to 34 with every field
traced to a named registry field, classify `SHARED_LIBS` separately, flag `module_catalog.json` for
regeneration from the registry, and close `CONFLICT::MODULE_UNIVERSE`.

---

## HD-05 — Disposition of the stale `.state` tree · **Choice: annotate in place — archiving would break the verification package** **[REVISED]**

**Plain terms:** `.state` holds completed evidence from an old workstream with someone's local Windows
paths baked in. Annotate it, move it, or ignore it?

**Options:** (a) annotate in place; (b) archive the tree; (c) accept the risk and do nothing.

**Decision: (a).** Confidence: **Evidence-forced** — upgraded from "cautious default" in the plan.

**Why:** option (b) is **disqualified by direct evidence**, not by caution. `.state` is a **live write
target** for the verification package MASTER-V2 depends on. The evidence manifest's `run_root_contract`
declares the template `.state/verification/{run_id}/` with eight required subdirectories, and
`generate_eafix_ssot_registry_verification_package.py` line 588 computes
`run_root = root / ".state" / "verification" / run_id`. Relocating `.state` would break the verification
run root before it's ever exercised. Eleven files across the repo reference `.state` paths.

Option (c) leaves a real misreading risk — a future agent seeing `PASS` statuses in `.state` could mistake
completed 2026-05 migration work for current SSOT execution status. Option (a) is minimal, reversible,
preserves the audit trail intact, and is the only option compatible with the verification package. The
absolute Windows paths are historical record: **annotated, never edited.**

**Triggers:** add `.state/WORKSTREAM_PROVENANCE.md` recording the workstream identity, the
2026-03-17→2026-05-18 date range, the completed status, and an explicit statement that it is unrelated to
any SSOT plan phase id. Modify nothing else; confirm via `git status`.

---

## HD-06 — Ratification of MASTER-V2 · **Choice: cannot be pre-decided — pre-commit the *rule* instead**

**Plain terms:** the last gate is "is the master plan ratified?" That answer is the *output* of doing the
work, so it can't be chosen now. What can be chosen now is what would make the answer yes.

**Decision: pre-commit the decision rule.** Confidence: **Judgment (procedural).**

**Ratify (HD-06-A) only if all four hold:**
1. Every finding closed or waived, each waiver carrying a rationale and a review date.
2. All twelve validations in the plan's `validation_catalog` pass.
3. The verification spec `target_plan` hash binding matches the canonical plan bytes.
4. The supersession checklist passes all ten steps, including a zero-hit dangling-reference scan.

**Ratify-with-exceptions (HD-06-B)** requires each exception to name the finding, the rationale, and a
review date. **Withhold (HD-06-C)** if any validation fails or the hash binding is broken.

**Two conditions are non-waivable** — the `target_plan` hash binding and the dangling-reference scan —
because waiving either silently invalidates the verification apparatus itself. Everything else is waivable
on the record.

**Why pre-commit:** it converts the final gate from a judgment call made under completion pressure into a
mechanical check, which is the same fail-closed discipline applied everywhere else in the system. The
honesty-audit ratio (E1/E2 closures versus E3-only and E5-only) must be reported **before** the decision,
so a plan closed largely on authority assertion is visible as such at the moment of ratification.

---

## Summary

| Gate | Decision | Confidence |
|---|---|---|
| HD-01 | Recover first; else mark both sources unverifiable **in place** (new option D) — deleting them corrupts 11 of 13 obligation pointers | Evidence-forced on cost / judgment on choice |
| HD-02 | Bare filename (spec already names it); archive to `99_archive_superseded_do_not_route/` | Evidence-forced |
| HD-03 | **Merge** both `doc_authority` files at the `00_` location — schemas are compatible, union is 28, zero conflicts | Evidence-forced on feasibility / judgment on location |
| HD-03 adj. | No canonical document may live in the do-not-route archive — restore or downgrade both L1 entries | Evidence-forced |
| HD-04 | Universe = registry ids `…0001`–`…0034`; `SHARED_LIBS` sits outside it; also closes `CONFLICT::MODULE_UNIVERSE` | Evidence-forced on arithmetic / judgment on `SHARED_LIBS` |
| HD-05 | Annotate in place — `.state` is the verification package's live run root, so archiving would break it | Evidence-forced |
| HD-06 | Cannot be pre-decided; pre-commit the four-condition ratification rule, two conditions non-waivable | Judgment (procedural) |

Five of seven are settled by the repository's own evidence. **Three recommendations changed** from the
versions embedded in the remediation plan (HD-01, HD-03, HD-05) — in each case because verification
produced evidence the plan was written without. The genuinely discretionary calls are the canonical
location in HD-03 and the exclusion of `SHARED_LIBS` in HD-04; both are reversible.

**Plan amendments required if these are ratified:** add option HD-01-D to the plan's decision register and
add a matching task to PHASE-01; downgrade the plan's characterisation of HD-03 as high-effort;
mark HD-05-B as disqualified rather than merely less-preferred.

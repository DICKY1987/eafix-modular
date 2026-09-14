# Governance remediation — decision log

**Date:** 2026-09-09
**Trigger:** an external audit of the 34-module governance architecture (pasted into the task that produced this
branch) scored the repo against its own 8 stated principles and proposed a 6-step "highest-leverage sequence."
**Scope of this pass:** steps 1–4 and 6 of that sequence (all metadata/tooling fixes — no physical file moves).
Step 5 (physically moving source files module-by-module) was deliberately **not** performed; see "Deferred / not
done" at the end of this document, and the reasoning under "Why step 5 was not attempted."

This document exists because several of the fixes below required picking one option among several plausible ones,
with real (if not fully verifiable in advance) consequences for a repository actively used for an algorithmic
trading system. Every such choice is recorded here with the alternatives considered and why the chosen option won,
so a human reviewer can override any single decision without having to re-derive the reasoning from scratch.

---

## 0. A finding that changed the shape of the whole task

The audit's central claim was **"49 paths are claimed by more than one module... this is the boundary violation
the whole architecture exists to prevent."** Before touching anything, this was verified against the live manifests
rather than taken on faith, because "resolve 49 ownership conflicts" and "the schema already has a mechanism for
this and it's just being misread" are very different amounts of work and risk.

**What was actually found:** every one of the 34 manifests already distinguishes `file_ownership.owned_files`
(exclusive-ownership claims) from `file_ownership.shared_files` (an explicit "not yet split out of a shared
service, sharing_policy: needs_refactor" declaration). Checked against `owned_files` alone — the field that
actually means "this module owns this file" — **there are zero collisions.** No file is claimed as owned by more
than one manifest anywhere in the repository. The 49 the audit counted come from also treating a module's
`shared_files` / `source_files` / `file_role_index` entries (which are explicitly *not* ownership claims — the
schema's own `sharing_policy: "needs_refactor"` and `file_assignment_status: "partial"` on those entries say so)
as if they were.

**Decision:** treat this as real information, not a reason to do nothing. The underlying situation the audit was
reacting to is genuine — 7 clusters of services (`calendar-ingestor`, `indicator-engine`, `transport-router`,
`execution-engine`, `reentry-engine`/`reentry-matrix-svc`, `flow-monitor`/`telemetry-daemon`, `signal-generator`)
haven't been physically split yet, so their code is legitimately depended on by 2–6 downstream modules at once.
That's Principle 5 (incremental migration) being incomplete, not Principle 3 (exclusive ownership) being violated
in the manifests themselves. The remediation below fixes the things that *are* actually broken in that data
(module_root, phantom paths, duplicate list entries, one bad entrypoint) rather than manufacturing a "primary
owner" resolution for something that was never actually double-owned.

This does **not** mean the audit was wrong to flag it — a human skimming `owned_files` + `source_files` +
`shared_files` together, or a tool that doesn't distinguish them, would reach exactly the "49 collisions" reading.
That's itself worth fixing loosely (clearer naming / docs), but rewriting the schema was out of scope here.

---

## 1. Phantom paths — purge, don't reassign

**Finding:** 4 distinct paths referenced in manifests do not exist anywhere in the repository:
`services/calendar-ingestor/src/2099900090260118_ff_auto_downloader.py`,
`.../2099900096260118_python_calendar_system.py`, `.../2099900097260118_python_calendar_system_patched.py`
(each referenced by 6 sibling manifests), and `services/desktop-ui/testing/2099900137260118_manual_testing_control_panel.py`
(referenced by 1 manifest). This matches the audit's "26 claimed paths don't exist" once you count per-manifest
reference *instances* rather than distinct paths (4 distinct paths × up to 6 referencing manifests ≈ that count).

**Options considered:**
- (a) Leave them — they're clearly stale, but touching them wasn't strictly required by the audit's numbered list.
- (b) Try to find where these files "really" live (rename-tracking) and repoint the reference.
- (c) Delete the references outright.

**Decision:** (c). A `git log --all --follow` / content-similarity search would be needed to justify (b), and even
if a plausible successor file were found (e.g. `ingestor.py`, `config.py`, `plugin.py` cover similar ground),
asserting "this old reference now means that other file" is a real claim about intent that should be a human call,
not an inferred one. Deleting a reference to something that doesn't exist is reversible and can't corrupt anything;
inventing a new mapping could be wrong in a way that's hard to notice later. All 4 paths were removed from every
list field (`owned_files`, `source_files`, `test_files`, `configuration_files`, `allowed_files`,
`file_role_index`, `shared_files`) of every manifest that referenced them.

---

## 2. Duplicate entries within a single manifest's own lists

**Finding, incidental to the phantom-path check:** several manifests (m0001, m0002, and the calendar-ingestor /
transport-router / execution-engine / reentry-engine / flow-orchestrator "secondary" manifests — see §0) list the
exact same path twice in the same field, e.g. `m0001-f1-config-preferences`'s `source_files` contained every
calendar-ingestor path exactly twice in a row.

**Decision:** de-duplicate (order-preserving) across all `file_ownership` list fields, everywhere. Not an
audit-numbered item, but directly relevant to trusting any file-count statistic derived from these manifests
(including the audit's own — inflated counts from double-listing could have been part of why the multi-claim
number looked as large as it did). Zero judgment call here: identical strings in a list that's supposed to be a
set is unambiguously a bug.

---

## 3. Backfilling `module_root` for 19 modules where it was `null`

**Finding:** `m0001, m0002, m0003, m0004, m0005, m0006, m0008, m0010, m0012, m0014, m0015, m0016, m0017, m0019,
m0020, m0021, m0022, m0024, m0025` all had `file_ownership.module_root: null`. Each of these is the "secondary /
not-yet-split" side of one of the 7 shared-service clusters from §0: it has no `owned_files` of its own yet (or,
for m0016/m0017/m0024, exactly one) because its real implementation still lives inside a sibling module's shared
service directory.

**Options considered:**
1. Point `module_root` at the shared service directory the code currently sits in (e.g. `services/calendar-ingestor`
   for m0001).
2. Point `module_root` at the module's own already-existing scaffold folder (e.g. `m0001-f1-config-preferences`).
3. Leave it null and only fix it once the physical split happens.

**Decision: option 2.** Option 1 was rejected because that directory is explicitly *not* this module's exclusive
territory — 4–6 sibling manifests would end up pointing `module_root` at the same directory, which recreates
exactly the "boundary violation" the audit is worried about, just moved from `owned_files` into `module_root`.
Option 3 was rejected because a null `module_root` is strictly worse for any tool or AI agent trying to find "where
does this module live" — Principle 7 in the audit ("AI-first design") specifically complains about modules that
give an agent nothing to anchor on. Option 2 always resolves to a real, existing, exclusively-owned directory (the
scaffold folder already created for that module's identity), so it's honest — it doesn't claim code is somewhere
it isn't. A note was written into each affected manifest's `reconciliation_status.reconciliation_notes` and a
top-level `notes` entry explaining that the module's canonical implementation has *not* physically moved there yet
and still lives in the shared service directory referenced by that module's own `shared_files`. This keeps the
manifest honest about the gap instead of silently papering over it.

**Modules NOT touched despite having somewhat irregular `module_root` values** (see §5): the 15 "primary" modules
in each cluster (m0003→wait, correction: m0007, m0009, m0011, m0013, m0018, m0023, m0026, m0027, m0028, m0029,
m0030, m0031, m0032, m0034, and m0033 separately) already have `owned_files` and a `module_root` that genuinely
contains at least some of their real code. Those were left as-is even where the root is coarser than ideal (see
§5) — changing a *working, physically-accurate* pointer felt like a materially different (and less justified) kind
of edit than backfilling a `null`.

---

## 4. `m0033-sk1-plugin-interface`: `module_root` was a file, not a directory

**Finding:** `file_ownership.module_root` was literally `"shared/2099900207260118_plugin_interface.py"` — a file
path, violating the schema's own implicit contract that `module_root` is a directory.

**Options considered:**
1. Point it at `shared/` (the parent directory, where 2 of its 3 `owned_files` genuinely live).
2. Point it at the module's own scaffold folder `m0033-sk1-plugin-interface` (where its 3rd owned file — its test —
   lives).

**Decision: option 2**, for the same reason as §3: `shared/` is a cross-cutting directory that other modules also
use for genuinely shared-kernel code (see `module_io_policy.shared_kernel_access_policy` in every manifest);
setting it as m0033's exclusive `module_root` would misrepresent everything else under `shared/` as belonging to
this one module. The gap (2 of 3 owned files still physically sitting in `shared/`, not under the module's own
folder) is recorded in `reconciliation_notes` rather than hidden.

---

## 5. `m0030` and `m0031` both declaring `module_root: services/desktop-ui` — left unchanged

The audit listed this as a "confirmed defect" ("Two modules (m0030, m0031) share `services/desktop-ui`"). On
inspection: their `owned_files` lists are fully disjoint (verified — zero overlapping paths, consistent with the
zero-collision finding in §0). This is the same pattern as `m0026-p1-health-aggregator`, whose own `module_root`
(`services/flow-monitor`) doesn't even contain most of its `owned_files` (10 of 12 are under
`services/telemetry-daemon` instead) — a case the audit didn't flag at all.

**Decision:** leave `m0030` and `m0031` as they were. Two disjoint sets of files sharing a coarse, not-yet-split
parent directory is pre-migration reality (Principle 5 incomplete), not an ownership collision (Principle 3
intact) — reclassifying it as broken and "fixing" it by pointing both at their own empty scaffold folders would
have made the manifests *less* accurate (their real code is genuinely under `services/desktop-ui` today) for the
sake of matching a rule that doesn't actually distinguish this case from m0026's. This is a place where this pass
disagrees with the audit's literal defect list, on the evidence above; a maintainer who disagrees with this call
should say so and it's a one-line revert.

---

## 6. `m0011-s1-signal-engine`: entrypoint fix + orphaned file reclaim

**Finding 1 — semantically wrong binding:** `process_binding.entrypoint_files` was
`["compliance/auto-remediation/2099900012260118_remediation-engine.py"]` — a file belonging to an unrelated
compliance module, not the signal engine.

**Finding 2, discovered while fixing #1:** `services/signal-generator/src/` (m0011's own `module_root`) contains
three real files — `2099900185260118_config.py`, `2099900186260118_processor.py`,
`2099900187260118_plugin.py` — none of which were listed in *any* manifest's `owned_files`. The authoritative
`file_module_mapping.csv` (m0011's declared `ownership_derivation` source) only lists the test file for this
service; these three source files were evidently added to the repo after that CSV/manifest generation pass and
were never backfilled.

**Decision process for the entrypoint:** read all three files. `plugin.py` imports and wires together
`config.py`'s `Settings` and `processor.py`'s `SignalProcessor`, and subclasses `BasePlugin`/`PluginMetadata` from
`shared/plugin_interface.py` — the same "`plugin.py` is the service's entrypoint" shape used consistently by every
other microservice in this repo (`transport-router`, `telemetry-daemon`, `reentry-matrix-svc`,
`execution-engine`, etc., all checked for the pattern). `entrypoint_files` was changed to
`["services/signal-generator/src/2099900187260118_plugin.py"]`.

**Decision for the orphaned files:** added all three to m0011's `owned_files` / `source_files` / `allowed_files`
/ `file_role_index` (with roles `config`, `other`, `plugin` respectively) — they sit directly under this module's
own `module_root`, are unambiguously its code, and fixing the entrypoint required understanding them anyway.
`reconciliation_status.mapped_file_count` was corrected from 1 to 4.

**Explicitly not done:** the same "orphan reclaim" for the other 33 modules. Repo-wide, only ~25% of tracked `.py`
files are claimed by any manifest (the audit's Principle-3 finding); closing that gap requires the same
per-file reading-and-judgment shown here, at a scale (roughly 340 files) that deserves a dedicated pass with its
own review, not a single automated sweep bundled into this one. Doing it uniformly and quickly (e.g. "claim every
file under a module's nominal service directory") would risk exactly the kind of over-claiming (§0) this pass just
finished cleaning up.

---

## 7. Migration map status write-back (`EAFIX_physical_file_migration_map_v1_0_0.json`)

**Finding, verified independently of the audit's number:** of the map's 42 `git_mv` operations, all 42 were still
marked `"status": "approved_not_executed"` — but checking each operation's declared sources/outputs against the
actual filesystem shows **19 have already been executed** (outputs exist, sources are gone) and 23 genuinely
haven't been started. Re-running the map as originally instructed would attempt `git mv` on 19 sources that no
longer exist and fail closed per the map's own `missing_source_policy`.

**Decision:** built `tools/migration/apply_migration_map.py`, a read-verify-writeback tool (see its docstring for
full detail) that: (1) never moves files itself; (2) classifies every operation by comparing declared paths against
disk (`completed` / `not_started` / `partially_executed` / `duplicated_source_still_present` /
`needs_manual_review`); (3) with `--write-back`, corrects `status` in the map JSON to `"completed"` for the 19
verified-done operations (using the vocabulary the map's own `completion_definition` already uses: "completed,
intentionally deferred, or blocked") and stamps `verification_utc` / `verification_method`; (4) always emits a
separate evidence report (`tools/migration/migration_verification_report.generated.json`) in the shape the map's
own `execution_contract.evidence_report_required_fields` describes, so the *reasoning* behind each status is
preserved, not just the new label; and (5) adds a `resume_policy` string directly into the map's
`execution_contract` stating that any future executor must skip operations already marked `"completed"`.

This was run once with `--write-back` as part of this pass — it's a pure correction of the map to match reality
that already exists on disk; it doesn't perform or approve any new move.

**What was deliberately not attempted:** reconstructing `commit_sha` / `references_updated` for the 19
already-executed operations. That would require walking git history per output file with no guarantee of finding
a clean 1:1 commit (some of these may have landed as part of larger, unrelated commits). Evidence records for
these 19 have `commit_sha: null` and an explicit `deviations` note saying the completion was inferred
retroactively from filesystem state, not observed live — a future maintainer with more context can fill this in
better than a guess would.

---

## 8. `pytest.ini` / coverage scope

**Finding:** `testpaths` listed only 2 of 34 module test directories (`m0023`, `m0033`); `addopts` measured
coverage with `--cov=src --cov-fail-under=85`, where `src/` is the *original* CLI-orchestrator codebase this
monorepo also contains (per `CLAUDE.md`) — unrelated to the 34-module trading system, and covering only 34 of the
453 tracked `.py` files server-side.

**Options considered for `testpaths`:**
- Leave as-is (rejected — the point of test dirs existing per module is that they get run).
- Add all 34 `m0*/m0*-tests` directories. Chosen — mechanical, and verified safe (see below).
- Also add every `services/*/tests` directory, since that's where most of the *actual* current test content lives
  today (module test dirs are still mostly `.gitkeep`). Chosen, but only for the 11 that actually exist on disk —
  7 more (`services/common/tests`, `.../compliance-monitor/tests`, etc.) were referenced as a pattern but don't
  exist yet and were left out rather than guessed at, since pytest errors on a nonexistent `testpaths` entry.

**Options considered for `--cov`:**
1. Leave `--cov=src` alone (measures the wrong codebase for this work, but doesn't risk breaking the CLI
   orchestrator's own existing 85% gate).
2. Change it to `--cov=m0*` / add all 34 module `-src` directories individually. Rejected: most of those
   directories are still empty scaffolding (§0), so this wouldn't meaningfully fix "measures almost nothing" — it
   would just be measuring a *different* set of almost-nothing.
3. Add `--cov=services`, where the bulk of the repo's actual current implementation lives (services/ directories
   for the not-yet-split clusters, plus the fully-split single-owner services). Chosen, in addition to keeping
   `--cov=src`.

**Decision:** `addopts` is now `--cov=src --cov=services ...`, and `--cov-fail-under=85` was left unchanged. This
last point is a deliberate non-decision: this session could not install every service's dependencies (confirmed —
`structlog` alone is missing, and collection already errors on 2 pre-existing test files for that reason,
independent of anything changed here) or run the full suite, so there was no way to verify what coverage
percentage `--cov=src --cov=services` would actually produce. Guessing at a new threshold and shipping it as a
hard CI gate risked turning the build permanently red for reasons unrelated to code quality. The safer, verifiable
change (test discovery + coverage *scope*) was made; the threshold is flagged here for a human to revisit once the
suite can actually be run with real dependencies installed.

**Verification actually performed:** `pip install pytest pytest-cov` + `pytest --collect-only
--continue-on-collection-errors` was run against the new config. Collection succeeds for every added test
directory; the only 2 collection errors present are pre-existing (missing `structlog`, affects
`tests/test_websocket_integration.py` and `m0033`'s existing test, both already in the *original* config) — i.e.
the change introduces zero new collection failures.

---

## 9. Structural validator + CI wiring (audit step 4)

Built `tools/validate_module_structure.py` and wired it into a new
`.github/workflows/validate-module-structure.yml`, triggered on changes to any module manifest/README/AGENTS file.
It enforces, exit-code-fail-closed: every module has exactly one parseable `manifest.json`; no path appears in
`owned_files` of more than one module (now that §0–§6 are fixed, this is 0/0, not "0 collisions because we didn't
look hard enough"); every path any manifest lists as owned/source/test/etc. actually exists on disk; `module_root`
is non-null and a real directory; every module has `README.md` and `AGENTS.md`.

**Deliberately not enforced by this validator** (see its own docstring): that `module_root` physically *contains*
every one of a module's `owned_files` (would currently fail for m0026, m0030, m0031, and similar not-yet-split
cases that are legitimate per §5 — turning that into a hard CI failure now would just make the build red for a
known, already-documented, pre-existing condition rather than catching a regression); and full ownership coverage
of the repo's ~453 `.py` files (only ~25% mapped — a real gap, but a metric to track and improve, not a pass/fail
gate at this stage). Running it now: 34/34 manifests checked, 0 errors.

---

## 10. `README.md` + `AGENTS.md` generated for all 34 modules

The audit's "own spec not met" section and Principle 7 ("loading m0011 gives an AI a manifest and 17 `.gitkeep`
files") both point at the same gap: zero of the 34 modules had a `README.md` or `AGENTS.md`, despite
`EAFIX_PROPOSED_34_MODULE_FILE_TREE.md` requiring both. Both were generated per module, templated directly from
that module's own `manifest.json` (purpose, process binding, scope, contracts, dependencies, file ownership,
status) — no invented content, and each file states plainly that it's generated and that the manifest is
authoritative if the two ever disagree. This was judged safe to do outright (unlike §12 below) because a
README/AGENTS file summarizing already-declared manifest data doesn't assert any new decision or approval — it's a
projection, not a governance artifact.

---

## 11. Manifest filename convention (`manifest.json` vs. the spec's `<20-digit>_<SYMBOL>.manifest.json`)

The audit noted the proposed file tree spec wants `<20-digit ID>_<SYMBOL>.manifest.json`, but every module has
plain `manifest.json`. **Decision: not renamed, left as a documented recommendation only.** Unlike the README/CI/
pytest changes above, this file is very likely read by name (`manifest.json`) by tooling this pass didn't
fully enumerate — `tools/registries/*.py`, `tools/manifest_generation` (referenced in each manifest's own
`staleness_policy.staleness_check_command`), and possibly CI workflows not inspected line-by-line. Renaming 34
files that other, unverified tooling may depend on by exact name is a different risk class from every other change
in this log — it's the kind of edit that can silently break something this pass has no way to detect from here.
Recommendation for a human/maintainer: `grep -rn "manifest.json"` across `tools/` and `.github/workflows/` first,
confirm nothing hardcodes the plain name, then rename with `git mv` and update those references in one focused
commit.

---

## 12. `module_container_inventory.json` — not generated, on purpose

The audit noted this file is "referenced as a required precondition" but doesn't exist. It was located: the
migration gap-closure plan (`EAFIX_auth_docs/EAFIX_34_MODULE_REPOSITORY_MIGRATION_GAP_CLOSURE_PLAN_v1_0_0.json`)
lists it alongside `module_identity_ratification.json`, `shared_file_resolution_decisions.json`, and several
others under `artifact_model.authored_artifacts`, each with a `purpose` string like *"Human-approved dispositions
for multi-module and unmapped files"* and *"Governance-approved 34-module identity set."*

**Decision: do not generate it (or its siblings) in this pass.** These are explicitly designed to represent actual
human/governance sign-off on decisions like file disposition and identity ratification — not a data projection
like a README. Fabricating a plausible-looking version of a document whose entire purpose is "this was reviewed
and approved by a human" would be actively misleading to anyone who encounters it later and assumes that approval
happened. This is a different category of risk than every other item in this log, and worth naming explicitly:
**the right way to use this pass's output for that purpose is for a maintainer to treat this decision log —
especially §0, §3, §5, §6 — as candidate input to a real `shared_file_resolution_decisions.json`, and formally
ratify it**, rather than for an agent to auto-generate the "approved" artifact itself.

---

## Why step 5 (physical file moves) was not attempted

The audit's own sequencing puts this last for a reason it states directly: *"Step 5 is the only part that's
actually risky, and it stays risky until 1–4 land."* Steps 1–4 (and 6) landed in this pass. Step 5 means running
`git mv` across roughly 340 currently-unmapped files plus the 23 not-yet-started migration-map operations, deciding
module-by-module where each physically goes — the same category of judgment call as every decision above, but at
10–50x the volume, on a codebase for a live trading system, with no test suite this session could actually execute
to catch a bad move. That combination — high volume of individually-consequential decisions, on financial-system
code, unverifiable by this session — is exactly the case where a single automated pass is the wrong tool. The
validator built in §9 and the corrected migration map in §7 are what make a *future*, deliberately-scoped
physical-migration pass (ideally one file-cluster / one module at a time, each independently reviewable) safe to
attempt, without redoing the governance work first.

---

## Deferred / not done (full list)

- **Step 5**: physical `git mv` of source files into module-owned directories, for both the 7 shared clusters
  (§0) and the 23 not-started migration-map operations (§7). Reasoning above.
- **Full ownership coverage** of the ~340 currently-unmapped `.py` files repo-wide (only m0011's 3 files were
  reclaimed, per §6).
- **Manifest filename rename** to the spec's `<ID>_<SYMBOL>.manifest.json` convention (§11) — flagged as a
  follow-up, not attempted, due to unverified tooling dependencies on the plain name.
- **`module_container_inventory.json`** and its sibling "human-approved" governance artifacts (§12) — not
  fabricated; this log is offered as candidate input for a real ratification pass instead.
- **`--cov-fail-under` threshold** was left unchanged (§8) — flagged for revisit once the suite can actually run
  with full dependencies installed.
- **Renaming/consolidating** the parallel `services/foo_bar` vs `services/foo-bar` directory pairs visible under
  `services/` (e.g. `data-ingestor` / `data_ingestor`, `reentry-engine` / `reentry_engine`) — noticed while
  exploring the tree, not covered by the audit's numbered list, and not investigated deeply enough to know which
  of each pair is live vs. legacy. Flagged here so it isn't lost.

## What this pass did NOT verify

This session could not run the project's full test suite (missing dependencies such as `structlog`; not
installed/verified for every service) or execute a live CI run. Every change above was checked the most rigorous
way available in this environment (filesystem cross-referencing via scripts, `pytest --collect-only`, running the
new validator to green, re-deriving specific facts like the m0011 entrypoint by reading the actual source), but
"the coverage gate still passes at the new scope" and "nothing outside this repo depends on `manifest.json`'s
current name" are explicitly unverified and called out as such above rather than asserted.

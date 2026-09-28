# EAFIX Consolidation - GitHub Projects tracking

Projects the 34-module documentation consolidation plan (v1.0.0) onto GitHub
Issues + a Projects v2 board so phase, wave and module progress is trackable.

Baseline commit: `b2b03563209f3ebbc8951be82f40869e26b7cc3f`

Live project: https://github.com/users/DICKY1987/projects/3

## The governing rule

**The repo is the authority. GitHub Projects is a derived view.**

Section 3 of the plan classifies catalogs, summaries and projections as derived
artifacts that must be "clearly labeled derived, never edited as independent
specifications." A Projects board is exactly that. So the sync is one-way:

```
eafix_consolidation_ssot.json  --project_sync.py-->  Issues + Project board
        (authority)                (one-way)              (derived view)
```

`project_sync.py` never reads board state back into the SSOT. If someone edits a
projected field in the UI, the next run overwrites it and reports it as drift.
To change status, edit the SSOT and re-run.

## What is NOT tracked in GitHub

Deliberately excluded, because putting them on the board would create a second
authority for processing status - the exact failure the plan is built to prevent:

| Not on the board | Owned by |
|---|---|
| 269 source documents | source-processing ledger |
| Extracted claims and dispositions | claim ledger |
| Field-level evidence | the module manifests |
| Gate approval evidence | consolidation policy + ledger |

The board shows rollups of these, never their authoritative state. In particular
the *fully scraped* register and archive index are **generated** from the ledger
(Section 6) - they must not be hand-maintained as project items.

## Item hierarchy

76 items, as GitHub sub-issues (limit: 100 children per parent, 8 levels deep -
this uses 3). Live issue numbers on DICKY1987/eafix-modular: #188-263.

```
Phase P0..P8                         9   (#188-196)
+-- Gate                             9   (#197-205) one per phase
+-- Decision D1..D7                  7   (#206-212) all blocking P1
+-- Deliverable DL1..DL9              9   (#213-221)
+-- Wave W1..W8                       8   (#222-229) (under P4)
    +-- Module m0001..m0034          34   (#230-263)
```

## Fields

14 custom fields (GitHub allows 50 per project; single-selects allow 50 options),
plus GitHub's own built-ins (Status, Parent issue, Sub-issues progress, etc.)

The three readiness dimensions are **separate fields on purpose**. Section 10
requires independent extraction, reconciliation and retention states and forbids
collapsing them into one ambiguous "processed" flag:

- `Schema Valid` - parses and validates against schema v2
- `Spec Ready` - all applicable mandatory fields confirmed
- `Impl Verified` - observed conformance at a recorded commit

Plus: `Item Type`, `Phase`, `Wave`, `Pilot`, `SSOT ID`, `Module Root`,
`Permanent ID`, `Evidence Ref`, `Approver`, `Baseline Commit`, `Blocked Reason`.

## Usage

```bash
# 1. auth with the project scope (skip if gh is already logged in with it)
gh auth login
gh auth refresh -s project -s read:project

# 2. regenerate the SSOT (edit build_ssot.py to change the plan)
python build_ssot.py

# 3. preview - no writes
python project_sync.py --owner DICKY1987 --project 3 \
    --repo DICKY1987/eafix-modular --dry-run

# 4. create the board and its fields (already done for project #3 - safe to
#    re-run, it skips fields/project that already exist)
python project_bootstrap.py DICKY1987

# 5. project it
python project_sync.py --owner DICKY1987 --project 3 --repo DICKY1987/eafix-modular

# re-run any time; it is idempotent and reports drift
# scope a run to one item type:
python project_sync.py --owner DICKY1987 --project 3 \
    --repo DICKY1987/eafix-modular --only Module
```

Idempotency key is an HTML marker `<!-- ssot-id: X -->` in each issue body.
Re-running matches on that, so issues are never duplicated.

Cross-platform: `project_bootstrap.py` is a pure-Python port of the original
bash version, for machines without Git Bash on PATH.

## Suggested board views

| View | Layout | Group by | Filter |
|---|---|---|---|
| Phase gates | Board | Phase | `Item Type: Phase, Gate` |
| Blocking decisions | Table | - | `Item Type: Decision, Status != Done` |
| Module readiness | Table | Wave | `Item Type: Module` - show the 3 readiness fields |
| Pilot | Board | Status | `Pilot: Yes` (m0009, m0016, m0029, m0034) |
| Wave burndown | Board | Wave | `Item Type: Module` |

## Built-in automations worth enabling

- **Item added -> Status: Todo**
- **Item closed -> Status: Done**
- Auto-add is **not** recommended: it would pull unrelated repo issues onto a
  board whose contents are supposed to be a controlled projection.

## Recommended start

Sequence the first run so the board reflects the plan's own gating - the seven
decisions block everything. (Already done for this initial rollout, in this
order: Phase+Gate+Decision, then Deliverable+Wave, then Module.)

Add `Deliverable,Wave,Module` once D1 (manifest location) and D7 (bundle
disposition) are decided, since both change module-level targets.

## Notes on this rollout

- Verified against baseline commit `b2b0356` before generating the SSOT: 269
  source files in `EAFIX_auth_docs`, 0/34 manifests carry v2 fields, 34/34 have
  null contract `schema_ref`, no top-level `archive/` exists yet.
- Decision D7 was added during verification (not in the original plan's
  Section 2): `EAFIX_auth_docs/manifests/eafix_module_manifests_bundle.vNext.schema_valid.json`
  is a competing manifest authority that already disagrees with the module
  roots on 28 of 34 modules.
- Generated text is plain ASCII (no em-dashes). An earlier draft used them and
  they mangled through the Windows console codepage during the first live
  run; stripped before creating any GitHub objects to avoid corrupting issue
  text.

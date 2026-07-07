# GitHub Issue: Glossary Filename Remediation — Promote Canonical File and Remove Stale Working Artifacts

**Label:** `governance` `cleanup` `ai-agent-task`
**Branch to create:** `fix/glossary-filename-remediation`
**Base branch:** `master`
**PR reviewer note:** This PR is intended for AI-program review. The PR description below contains all verification criteria an AI reviewer must check before approving.

---

## Background and Why This Matters

The `EAFIX_auth_docs/` folder currently has **six glossary-related files**. Only one of them is the correct, canonical module governance glossary. The rest are working artifacts, old skeletons, and an unapplied patch — none of which should be present as live files. Any AI agent reading `EAFIX_auth_docs/` today could pick up a stale 4-term v1.0.0 file and treat it as authoritative, or read a bulk-terms working file with zero terms but a partial structure, and produce incorrect governance decisions.

This issue directs a precise remediation: promote the correct file to its canonical name and delete all others.

---

## Exact Current State (Verified by File Inspection)

The following files exist today in `EAFIX_auth_docs/`. Do not infer — verify each file's existence and content before acting.

| Filename | Size | Valid JSON | Schema Version | Terms | Disposition |
|---|---|---|---|---|---|
| `Y_module governance glossary.json` | 72,317 bytes | YES | 1.1.1 | 81 | **RENAME → canonical target name** |
| `U_module governance glossary.txt` | 139,750 bytes | NO | N/A | N/A | **DELETE** — unapplied git format-patch |
| `x_module governance glossary bulk terms.json` | 72,862 bytes | YES | none | 0 | **DELETE** — pre-merge working artifact |
| `module governance glossary bulk terms.json` | 62,595 bytes | YES | none | 0 | **DELETE** — pre-merge working artifact |
| `schema_version_ module_governance_glossary.txt` | 3,128 bytes | YES | 1.0.0 | 4 | **DELETE** — superseded v1.0.0 skeleton |
| `Explanation_ module_governance_glossary.json.txt` | 7,844 bytes | NO | N/A | N/A | **DELETE** — plain-text planning note |

---

## Required Actions — Perform Exactly in This Order

### Action 1 — Create the canonical file

**Create** `EAFIX_auth_docs/module_governance_glossary.json`

Copy the **exact byte-for-byte content** of `EAFIX_auth_docs/Y_module governance glossary.json` into this new file. Do not alter, reformat, regenerate, or summarize the content. Do not parse and re-serialize it. Copy it verbatim.

> **Why a copy, not a rename?** Git treats a rename as delete + add. Using an explicit `git mv` or a copy-then-delete is acceptable — but if your tooling produces a rename, verify that the target file content matches the source before committing. Either approach is correct as long as the content is identical.

**Verification the AI reviewer must confirm:**
- `EAFIX_auth_docs/module_governance_glossary.json` exists in the PR diff as an added file
- Its `schema_version` field equals `"1.1.1"`
- Its `status` field equals `"canonical"`
- Its `document_type` field equals `"module_governance_glossary"`
- It contains exactly **81 terms** in the `terms` array
- It contains exactly **9 entries** in the `ai_usage_rules` array (IDs: GLOSSARY-AI-001 through GLOSSARY-AI-009)
- It contains exactly **8 entries** in the `forbidden_interpretations` array
- It contains exactly **7 entries** in the `relationships` array
- The SHA-256 hash of the file content matches: `084564ad4fed19c50f5f6985a54c52275ad8aa43c8d5eef707a65330535dc712`

---

### Action 2 — Delete `Y_module governance glossary.json`

**Delete** `EAFIX_auth_docs/Y_module governance glossary.json`

Its content has been promoted to `module_governance_glossary.json` in Action 1. The `Y_` prefix was a sort-order workaround used during development, not a governance-approved filename. The file must not remain after the canonical file is created, to prevent agents from reading two copies.

**Verification the AI reviewer must confirm:**
- `EAFIX_auth_docs/Y_module governance glossary.json` is absent from the PR's final file tree
- It appears in the PR diff as a deleted file

---

### Action 3 — Delete `module governance glossary bulk terms.json`

**Delete** `EAFIX_auth_docs/module governance glossary bulk terms.json`

This is a pre-merge working artifact. It has no `schema_version`, no `document_type`, no `status`, and zero entries in its `terms` array. All content that was in this file has already been merged into `Y_module governance glossary.json` (now promoted to `module_governance_glossary.json`). Verified: none of its `additional_ai_usage_rules`, `additional_forbidden_interpretations`, or `relationships` are absent from the canonical v1.1.1 file.

**Verification the AI reviewer must confirm:**
- `EAFIX_auth_docs/module governance glossary bulk terms.json` is absent from the PR's final file tree
- It appears in the PR diff as a deleted file

---

### Action 4 — Delete `x_module governance glossary bulk terms.json`

**Delete** `EAFIX_auth_docs/x_module governance glossary bulk terms.json`

Same category as Action 3. Pre-merge working artifact. Zero terms. The `x_` prefix was used to change sort order during the working session. Its content is a superset of the other bulk file but all material content was already merged into the canonical glossary. It has no independent governance value.

**Verification the AI reviewer must confirm:**
- `EAFIX_auth_docs/x_module governance glossary bulk terms.json` is absent from the PR's final file tree
- It appears in the PR diff as a deleted file

---

### Action 5 — Delete `schema_version_ module_governance_glossary.txt`

**Delete** `EAFIX_auth_docs/schema_version_ module_governance_glossary.txt`

This is the original v1.0.0 skeleton with 4 terms: `module_id`, `canonical_symbol`, `canonical`, and `module_change_request`. It predates the v1.1.1 glossary by multiple sessions. It declares `"status": "canonical"` which is incorrect — it has been superseded. Leaving it in the folder means an AI agent could read two files both claiming `"status": "canonical"` with incompatible content.

**Verification the AI reviewer must confirm:**
- `EAFIX_auth_docs/schema_version_ module_governance_glossary.txt` is absent from the PR's final file tree
- It appears in the PR diff as a deleted file

---

### Action 6 — Delete `U_module governance glossary.txt`

**Delete** `EAFIX_auth_docs/U_module governance glossary.txt`

This is a `git format-patch` file (raw patch format starting with `From <sha> Mon Sep 17 00:00:00 2001`). It was produced in a prior Claude session and was intended to be applied via `git am` to promote the glossary. It was never applied. The operations it described are now being performed manually by this PR, making the patch file obsolete. It is not a governance artifact, not a JSON file, and not a document — it is an operational artifact from a previous session and must not remain in the folder.

**Verification the AI reviewer must confirm:**
- `EAFIX_auth_docs/U_module governance glossary.txt` is absent from the PR's final file tree
- It appears in the PR diff as a deleted file

---

## What This PR Must NOT Do

- **Do not edit the content** of `module_governance_glossary.json`. Copy verbatim from `Y_module governance glossary.json`. Do not reformat, sort keys, add newlines, or regenerate.
- **Do not delete any other files** in `EAFIX_auth_docs/` outside the six listed above.
- **Do not modify** `doc_authority.json` in this PR. A separate remediation for `doc_authority.json` path drift is tracked separately.
- **Do not attempt to apply** `U_module governance glossary.txt` as a git patch. It is being deleted, not applied.
- **Do not create any new files** beyond `module_governance_glossary.json`.
- **Do not rename** any file other than the `Y_module governance glossary.json` → `module_governance_glossary.json` operation.

---

## Expected PR Diff Summary

The PR diff should show exactly:

```
EAFIX_auth_docs/module_governance_glossary.json                   | added   (1,600 lines, canonical glossary v1.1.1)
EAFIX_auth_docs/Y_module governance glossary.json                 | deleted
EAFIX_auth_docs/U_module governance glossary.txt                  | deleted
EAFIX_auth_docs/x_module governance glossary bulk terms.json      | deleted
EAFIX_auth_docs/module governance glossary bulk terms.json        | deleted
EAFIX_auth_docs/schema_version_ module_governance_glossary.txt    | deleted

6 files changed, 1 addition, 5 deletions (net file count)
```

If the diff shows more files changed than this, stop and verify before pushing.

---

## PR Title

```
fix(governance): promote module_governance_glossary.json v1.1.1; remove stale glossary working artifacts
```

---

## PR Description (for AI reviewer)

```
## Summary

Resolves the glossary filename and artifact hygiene issue in EAFIX_auth_docs/.

The canonical module governance glossary (v1.1.1, 81 terms) existed only under
the filename `Y_module governance glossary.json` — a sort-order workaround from
a working session, not the governed filename. This PR:

1. Creates `module_governance_glossary.json` with verbatim content from the Y_ file
2. Deletes the Y_ source file (now redundant)
3. Deletes 4 stale working artifacts that posed an AI-agent confusion risk

## Motivation

Before this PR, an AI agent scanning EAFIX_auth_docs/ would find multiple files
with glossary-like names:
- One claiming `"status": "canonical"` with 4 terms (v1.0.0) ← WRONG
- One with the actual 81 terms but an unofficial filename (Y_)
- Two bulk working files with 0 terms but partial structure
- A raw git patch file (.txt format)

Any agent reading the wrong file would operate on incorrect governance vocabulary.

## Files Changed

### Added
- `EAFIX_auth_docs/module_governance_glossary.json`
  - schema_version: 1.1.1
  - status: canonical
  - document_type: module_governance_glossary
  - 81 terms across 8 categories
  - 9 ai_usage_rules (GLOSSARY-AI-001 through GLOSSARY-AI-009)
  - 8 forbidden_interpretations
  - 7 relationships
  - SHA-256: 084564ad4fed19c50f5f6985a54c52275ad8aa43c8d5eef707a65330535dc712

### Deleted
- `EAFIX_auth_docs/Y_module governance glossary.json`
  Reason: content promoted to canonical filename above. Identical content confirmed
  before deletion (full JSON sort_keys match).

- `EAFIX_auth_docs/module governance glossary bulk terms.json`
  Reason: pre-merge working artifact. No schema_version, no document_type, 0 terms.
  All content_verified as already merged into v1.1.1.

- `EAFIX_auth_docs/x_module governance glossary bulk terms.json`
  Reason: same as above. x_ prefix was sort-order workaround during working session.
  All content verified as already merged into v1.1.1.

- `EAFIX_auth_docs/schema_version_ module_governance_glossary.txt`
  Reason: superseded v1.0.0 skeleton (4 terms only). Incorrectly declared status
  "canonical". Removed to prevent conflict with actual canonical v1.1.1 file.

- `EAFIX_auth_docs/U_module governance glossary.txt`
  Reason: unapplied git format-patch from prior session. Not a document. The
  operations it described are now performed by this PR. No governance value as a
  file in the docs folder.

## AI Reviewer Checklist

An AI program reviewing this PR must verify each item before approving:

### Content integrity
- [ ] `module_governance_glossary.json` is valid JSON
- [ ] `schema_version` == `"1.1.1"`
- [ ] `status` == `"canonical"`
- [ ] `document_type` == `"module_governance_glossary"`
- [ ] `len(terms)` == 81
- [ ] `len(ai_usage_rules)` == 9
- [ ] rule IDs present: GLOSSARY-AI-001 through GLOSSARY-AI-009 (all 9)
- [ ] `len(forbidden_interpretations)` == 8
- [ ] `len(relationships)` == 7
- [ ] SHA-256 of file == `084564ad4fed19c50f5f6985a54c52275ad8aa43c8d5eef707a65330535dc712`

### Deletions confirmed
- [ ] `Y_module governance glossary.json` — absent from final tree
- [ ] `U_module governance glossary.txt` — absent from final tree
- [ ] `x_module governance glossary bulk terms.json` — absent from final tree
- [ ] `module governance glossary bulk terms.json` — absent from final tree
- [ ] `schema_version_ module_governance_glossary.txt` — absent from final tree

### Scope containment
- [ ] No files changed outside `EAFIX_auth_docs/` folder
- [ ] No files changed inside `EAFIX_auth_docs/` other than the 6 listed above
- [ ] `doc_authority.json` is unchanged
- [ ] Total diff: 1 file added, 5 files deleted — nothing else

### No regressions
- [ ] `module_governance_glossary.json` contains term `module_lifecycle_status`
  with governance_rule confirming it is a computed projection (Model C), never stored
- [ ] `module_governance_glossary.json` contains term `identity_status`
  as the sole stored schema field for module identity state
- [ ] AI rule GLOSSARY-AI-009 is present and references `module_lifecycle_status`
  as a derived projection that must never be stored in catalog records

## Testing

No automated tests exist for this change. Correctness is established by:
1. SHA-256 match on the canonical file
2. JSON validity check
3. Term count verification (81)
4. AI rule ID enumeration (GLOSSARY-AI-001 through GLOSSARY-AI-009)

All four checks are listed in the AI Reviewer Checklist above.

## Related

- The repo catalog `Claude_gen_atomic_module_catalog_vNext.json` has an empty
  `modules` array despite declaring `module_count: 34`. This is a separate issue
  tracked for a follow-up PR and is NOT addressed here.
- `doc_authority.json` path drift remediation is also tracked separately.
```

---

## Notes for Copilot

- All filenames above are **exact**, including spaces. File paths in `EAFIX_auth_docs/` are case-sensitive. Do not normalise or escape spaces unless your tooling requires it.
- The file to copy content from (`Y_module governance glossary.json`) has a space between `Y_module` and `governance` — this is intentional and matches the actual filename.
- The target file (`module_governance_glossary.json`) uses underscores throughout — no spaces.
- Do not use the `U_module governance glossary.txt` file as a git patch. It is a file to be deleted, not applied.
- Commit all six changes (1 add, 5 deletes) in a **single commit** on branch `fix/glossary-filename-remediation`.
- The commit message should be:

```
fix(governance): promote module_governance_glossary.json v1.1.1; remove stale working artifacts

Canonical glossary (v1.1.1, 81 terms) was stored under Y_ prefixed filename.
This commit:
- Creates module_governance_glossary.json (verbatim copy of Y_ file)
- Deletes Y_module governance glossary.json (source, now redundant)
- Deletes module governance glossary bulk terms.json (pre-merge working artifact, 0 terms)
- Deletes x_module governance glossary bulk terms.json (pre-merge working artifact, 0 terms)
- Deletes schema_version_ module_governance_glossary.txt (superseded v1.0.0, 4 terms)
- Deletes U_module governance glossary.txt (unapplied git patch, obsolete)

Content verified: all additional_ai_usage_rules, additional_forbidden_interpretations,
and relationships from both bulk files are already present in the v1.1.1 canonical file.
SHA-256 of target: 084564ad4fed19c50f5f6985a54c52275ad8aa43c8d5eef707a65330535dc712
```

# EAFIX_auth_docs Reorganization — Completion Report

**Branch:** `copilot/create-subfolder-structure-eafix-auth-docs`
**Completed:** 2026-06-26
**Report scope:** Path drift correction, routing guardrails, archive manifest completeness, glossary canonicalization, and validation reporting.

---

## 1. Summary

This report covers the finalization pass of the non-destructive reorganization of `EAFIX_auth_docs/` from a flat layout into 15 subject-based subfolders. The first pass (commit: `Restructure EAFIX_auth_docs into subject-based folders`) moved 116 files using `git mv`. This pass corrects path drift discovered after the first move.

---

## 2. Changes Made in This Pass

### 2.1 `doc_authority.json` — 8 entries corrected

| Filename | Was | Now |
|---|---|---|
| `process_step_catalog.json` | `EA-REG/process_step_catalog.json` | `EAFIX_auth_docs/01_canonical_registries/process_step_catalog.json` |
| `module_catalog.json` | `EA-REG/module_catalog.json` | `EAFIX_auth_docs/01_canonical_registries/module_catalog.json` |
| `communication_channels.json` | `EA-REG/communication_channels.json` | `EAFIX_auth_docs/01_canonical_registries/communication_channels.json` |
| `module_catalog.schema.json` | `EA-REG/schemas/module_catalog.schema.json` | `EAFIX_auth_docs/01_canonical_registries/module_catalog.schema.json` |
| `MIGRATION_COMPLETION_SUMMARY.md` | `EA-REG/MIGRATION_COMPLETION_SUMMARY.md` | `EA-REG/superseded/MIGRATION_COMPLETION_SUMMARY.md` |
| `SOLUTION_FILE_MANIFEST.md` | `EA-REG/SOLUTION_FILE_MANIFEST.md` | `EA-REG/superseded/SOLUTION_FILE_MANIFEST.md` |
| `VALIDATION_GATES.md` | `EA-REG/VALIDATION_GATES.md` | `null` (marked `missing_from_disk`) |
| `ALIGNMENT_VALIDATION_REPORT.md` | `EA-REG/ALIGNMENT_VALIDATION_REPORT.md` | `null` (marked `missing_from_disk`) |

After this pass: `14 entries OK / 2 entries marked missing_from_disk / 0 broken`.

### 2.2 Glossary canonicalization — `Y_module governance glossary.json`

- **SHA256 verified identical** to `module_governance_glossary.json`:
  `084564ad4fed19c50f5f6985a54c52275ad8aa43c8d5eef707a65330535dc712`
- Moved from `EAFIX_auth_docs/00_doc_control_and_authority/` → `EAFIX_auth_docs/99_archive_superseded_do_not_route/` using `git mv`.
- `archive_manifest.json` updated with a new entry recording SHA256, replacement file, and reason.
- **`module_governance_glossary.json` is now the only live canonical glossary** in `00_doc_control_and_authority/`.

### 2.3 `archive_manifest.json` — entry added

All 6 files in `99_archive_superseded_do_not_route/` are now covered:

| File | SHA256 | Reason |
|---|---|---|
| `Y_module governance glossary.json` | `084564ad...` | Byte-identical copy; `Y_` was staging name |
| `Explanation_ module_governance_glossary.json.txt` | `efa141bc...` | Working artifact |
| `U_module governance glossary.txt` | `03eab3fa...` | Working artifact |
| `module governance glossary bulk terms.json` | `aa630dc7...` | Superseded bulk terms |
| `schema_version_ module_governance_glossary.txt` | `6c146aa9...` | Superseded artifact |
| `x_module governance glossary bulk terms.json` | `89fa4936...` | Superseded bulk terms |

### 2.4 README guardrails updated

Both cleanup/archive folders now have explicit AI routing exclusion notices:

| Folder | Guardrail updated |
|---|---|
| `90_cleanup_tasks_pr_notes_and_working_artifacts/README.md` | ⛔ "NOT DEFAULT AI ROUTING MATERIAL" header + explicit exclusion rules |
| `99_archive_superseded_do_not_route/README.md` | ⛔ "NOT DEFAULT AI ROUTING MATERIAL — DO NOT ROUTE HERE" header + rules |

### 2.5 Summary router `repo_path_hints` corrected

`EAFIX_auth_docs/12_ai_summary_routers_and_reference_guides/eafix_project_knowledge_summary_router.json` updated:

| Stale hint | Corrected to |
|---|---|
| `EAFIX_auth_docs/identifier_map.json` | `EA-REG/identifier_map.json` |
| `EAFIX_auth_docs/solution_spec.json` | `EA-REG/solution_spec.json` |
| `EAFIX_auth_docs/MIGRATION_COMPLETION_SUMMARY.md` | `EA-REG/superseded/MIGRATION_COMPLETION_SUMMARY.md` |
| `EAFIX_auth_docs/SOLUTION_FILE_MANIFEST.md` | `EA-REG/superseded/SOLUTION_FILE_MANIFEST.md` |
| `EAFIX_auth_docs/VALIDATION_GATES.md` | `repo_path_hint` set to `null`; `stale_path_was: "EA-REG/VALIDATION_GATES.md"`; `path_status: missing_from_disk` |
| `EAFIX_auth_docs/ALIGNMENT_VALIDATION_REPORT.md` | `repo_path_hint` set to `null`; `stale_path_was: "EA-REG/ALIGNMENT_VALIDATION_REPORT.md"`; `path_status: missing_from_disk` |
| `EAFIX_auth_docs/DOC-PAT-EVERY-REUSABLE-PATTERN-PATTERN-304__every_reusable_pattern.pattern.yaml` | `repo_path_hint` set to `null`; `stale_path_was` recorded; `path_status: missing_from_disk` |

---

## 3. Path / Reference Scan Results

### Scan: Flat `EAFIX_auth_docs/<file>` paths (no subfolder) in routing instructions

**Command:** `grep -o 'EAFIX_auth_docs/[^"\\]+' eafix_project_knowledge_reference_routing_instructions.json | grep -v '/0[0-9]_\|/1[0-9]_\|/9[09]_'`

**Result: NONE** — All paths in the root routing instructions correctly reference subject subfolders.

### Scan: Flat paths in `doc_authority.json`

**Result: NONE** — All entries with `relative_path != null` point to subject subfolders or valid EA-REG paths.

### Scan: Stale EA-REG paths in `doc_authority.json` for EAFIX_auth_docs files

**Result: FIXED** — All canonical EAFIX_auth_docs files that were erroneously pointing to `EA-REG/` have been corrected.

### Scan: Flat `EAFIX_auth_docs/<file>` paths (no subfolder) in summary router

**Command:** `grep -o '"repo_path_hint": "EAFIX_auth_docs/[^/"][^"]*"' eafix_project_knowledge_summary_router.json`

**Result: FIXED (post-review pass)** — Stale flat hints (`EAFIX_auth_docs/VALIDATION_GATES.md`, `EAFIX_auth_docs/ALIGNMENT_VALIDATION_REPORT.md`, and `EAFIX_auth_docs/DOC-PAT-EVERY-REUSABLE-PATTERN-PATTERN-304__every_reusable_pattern.pattern.yaml`) are now set to `repo_path_hint: null` with `stale_path_was` recorded. No flat hints remain.

### Scan: Archive manifest vs folder completeness

**Result: COMPLETE** — Manifest covers all 6 files in `99_archive_superseded_do_not_route/`. Zero gaps.

### Scan: Routing exclusion guardrails

**Result: PRESENT** — Both `matching_policy.default_excluded_paths` in the routing instructions and the README files in 90 and 99 folders provide explicit exclusions.

---

## 4. Validation Results

### JSON parse validation

All modified JSON files validated successfully:

| File | Status |
|---|---|
| `EAFIX_auth_docs/00_doc_control_and_authority/doc_authority.json` | ✅ Valid JSON |
| `EAFIX_auth_docs/99_archive_superseded_do_not_route/archive_manifest.json` | ✅ Valid JSON |
| `EAFIX_auth_docs/12_ai_summary_routers_and_reference_guides/eafix_project_knowledge_summary_router.json` | ✅ Valid JSON |
| `eafix_project_knowledge_reference_routing_instructions.json` | ✅ Valid JSON |
| `EAFIX_auth_docs/00_doc_control_and_authority/module_governance_glossary.json` | ✅ Valid JSON |

### Schema validation (`ci/2099900010260118_validate_schemas.py`)

```
=== Validating JSON Contract Schemas ===
Validated 4/4 schemas in JSON Contract Schemas

=== Validating Legacy Event Schemas ===
Validated 7/7 schemas in Legacy Event Schemas

=== Summary ===
Total schemas validated: 11/11
+ All schemas are valid!
```

### Full lint / build / test commands

**Limitation:** `poetry` is not installed in this runner environment. The following commands were not available:

- `poetry run pytest` — not available (`poetry: command not found`)
- `poetry run flake8` — not available
- `poetry run mypy` — not available

These commands do not apply to this task anyway, as this task only modifies documentation/JSON metadata files, not runtime Python code.

---

## 5. Glossary Canonicalization Verification

| Check | Result |
|---|---|
| `module_governance_glossary.json` exists | ✅ Yes |
| Valid JSON | ✅ Yes |
| `document_type == "module_governance_glossary"` | ✅ Yes |
| `status == "canonical"` | ✅ Yes |
| `Y_module governance glossary.json` NOT in `00_doc_control_and_authority/` | ✅ Moved to archive |
| `Y_` file byte-identical to canonical (SHA256) | ✅ Verified |
| Archive manifest entry for `Y_` file | ✅ Present |

---

## 6. Routing Guardrails Verification

| Requirement | Status |
|---|---|
| `EAFIX_auth_docs/90_...` excluded from `default_excluded_paths` in routing instructions | ✅ |
| `EAFIX_auth_docs/99_...` excluded from `default_excluded_paths` in routing instructions | ✅ |
| `default_excluded_paths_override` rule documented | ✅ |
| `90_...` README has explicit exclusion notice | ✅ Updated |
| `99_...` README has explicit exclusion notice | ✅ Updated |

---

## 7. Files Changed in This Pass

- `EAFIX_auth_docs/00_doc_control_and_authority/doc_authority.json` — 8 path corrections
- `EAFIX_auth_docs/00_doc_control_and_authority/Y_module governance glossary.json` → moved to `99_archive_superseded_do_not_route/` (git mv)
- `EAFIX_auth_docs/99_archive_superseded_do_not_route/archive_manifest.json` — 1 new entry for Y_ glossary
- `EAFIX_auth_docs/90_cleanup_tasks_pr_notes_and_working_artifacts/README.md` — routing guardrail updated
- `EAFIX_auth_docs/99_archive_superseded_do_not_route/README.md` — routing guardrail updated
- `EAFIX_auth_docs/12_ai_summary_routers_and_reference_guides/eafix_project_knowledge_summary_router.json` — stale repo_path_hints corrected, including missing-from-disk entries with `repo_path_hint: null` and `stale_path_was` preserved
- `EAFIX_auth_docs/00_doc_control_and_authority/REORGANIZATION_COMPLETION_REPORT.md` — this file (created)

---

## 8. Not Completed / Manual Review Required

| Item | Reason / Action Required |
|---|---|
| `VALIDATION_GATES.md` | File does not exist on disk. Was expected at `EA-REG/VALIDATION_GATES.md`. Was extracted from `MIGRATION_COMPLETION_SUMMARY.md`. Manual regeneration or recovery required. |
| `ALIGNMENT_VALIDATION_REPORT.md` | File does not exist on disk. Was auto-generated by `EA-REG/validate_three_artifact_alignment.py`. Re-run to regenerate. |
| Content consolidation (calendar, reentry, glossary bulk-terms) | Out of scope for this pass per task constraints. Separate consolidation task required. |
| `DOC-PAT-EVERY-REUSABLE-PATTERN-PATTERN-304__every_reusable_pattern.pattern.yaml` | File does not exist on disk. Summary-router entry is now explicitly marked `path: null`, `repo_path_hint: null`, `path_status: missing_from_disk`, and `stale_path_was` preserved. |

---

## 9. Branch Readiness

Post-fix readiness rerun completed on **2026-06-27** after syncing this PR branch with the latest `master` (`git merge origin/master`).

| Check | Status | Notes |
|---|---|---|
| Branch synced with latest `master` | ✅ Yes | Merge commit created on this branch before rerunning validation. |
| Stale-path scans rerun after latest fix | ✅ Yes | No invalid flat-path routing drift found; missing-file router entries remain nulled with `stale_path_was` preserved. |
| JSON parse validation | ✅ Pass | All required JSON files parsed successfully. |
| Schema validation (`ci/2099900010260118_validate_schemas.py`) | ✅ Pass | `11/11` schemas validated successfully. |
| GitHub Actions for latest head commit | ⚠️ Not found | No workflow runs were found for the latest checked head commit. |
| Poetry checks (`pytest`, `flake8`, `mypy`) | ⚠️ Not available | `poetry unavailable in runner: poetry: command not found`. |

No runtime/trading code was modified. This PR remains non-destructive documentation/routing work only.

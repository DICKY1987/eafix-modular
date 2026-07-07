# COPILOT ISSUE — Atomic Module Manifest Population, Pass 2

| Key | Value |
|---|---|
| Task ID | `MANIFEST-POP-PASS2-V1` |
| Repository | `DICKY1987/eafix-modular` |
| Base branch | `master` |
| Work branch | `copilot/manifest-population-pass-2` (create from current `master` HEAD) |
| Target schema | `EAFIX_auth_docs/01_canonical_registries/eafix_unified_atomic_module_schema_v1_0_0.json` |
| Semantic guide | `EAFIX_auth_docs/02_module_architecture_and_atomic_migration/eafix_unified_atomic_module_manifest_ai_fill_instructions_v1_0_0.md` |
| Companion plan | `EAFIX_auth_docs/02_module_architecture_and_atomic_migration/EAFIX_ATOMIC_MANIFEST_POPULATION_FIX_PLAN_V1_0_0".txt` (note: filename contains a literal `"` character — do not rename it) |

## 1. Objective

Populate the currently unfilled and thin sections of all **34** atomic module manifests in `EAFIX_auth_docs/manifests/module_manifests/` using only the authoritative source files named in Section 6, following the exact per-field extraction rules in Section 7. Verified gap state at time of authoring (from `EAFIX_auth_docs/manifests/manifest_fill_coverage_report.vNext.json`):

- `dependencies` missing in 9 manifests
- `service_runtime` missing in 18 manifests
- `file_ownership` partial in 13 manifests; 15 manifests have zero mapped files
- `process_binding.upstream_modules` and `process_binding.downstream_modules` empty in all 34 manifests
- `communication_channels` absent as a top-level section in the sampled manifests
- `migration_traceability` absent in the sampled manifests
- `source_authority.conflict_resolution_order` references stale pre-reorganization flat paths (e.g. `EAFIX_auth_docs/module_catalog.json` instead of `EAFIX_auth_docs/01_canonical_registries/module_catalog.json`)

## 2. Scope containment — NON-NEGOTIABLE

**Write allowlist.** The agent may create or modify ONLY these paths. Any change outside this list is a task failure.

```
EAFIX_auth_docs/manifests/module_manifests/*.manifest.json      (modify only; no create, no delete, no rename)
EAFIX_auth_docs/manifests/manifest_fill_coverage_report.vNext.json   (regenerate)
EAFIX_auth_docs/manifests/manifest_fill_coverage_report.vNext.md     (regenerate)
EAFIX_auth_docs/manifests/manifest_validation_report.json            (regenerate)
EAFIX_auth_docs/manifests/manifest_validation_report.md              (regenerate)
EAFIX_auth_docs/manifests/manifest_population_pass2_report.md        (create — new)
EAFIX_auth_docs/manifests/manifest_population_exceptions.md          (create — new)
```

**Forbidden actions (explicit):**

1. Do NOT delete, rename, or move any file anywhere in the repository.
2. Do NOT modify any file under `EAFIX_auth_docs/00_doc_control_and_authority/`, `EAFIX_auth_docs/01_canonical_registries/`, `EAFIX_auth_docs/02_module_architecture_and_atomic_migration/`, `EAFIX_auth_docs/03_process_lifecycle_and_crosswalks/`, `EAFIX_auth_docs/10_services_source_inventory_and_file_mapping/`, or `EAFIX_auth_docs/99_archive_superseded_do_not_route/`. These are read-only sources for this task.
3. Do NOT modify any file under `services/`, `src/`, `tests/`, `mt4/`, `shared/`, or any other code directory.
4. Do NOT write to `Claude_gen_atomic_module_catalog_vNext.json`. Its `modules[]` array is empty; restoring it is a separate task and is out of scope here.
5. Do NOT create new manifest files. Exactly 34 `*.manifest.json` files exist before this task and exactly the same 34 must exist after.
6. Do NOT overwrite any manifest field listed as `VERIFY_ONLY` in Section 7, even if a source disagrees with it. Record the disagreement in `manifest_population_pass2_report.md` under a "Drift observations" heading instead.
7. Do NOT invent, infer, or approximate any value not directly extractable by a rule in Section 7. When a rule's source yields nothing, apply the rule's stated `MISSING` behavior — never a guessed value. This repeats the governing doctrine of the fill-instructions document: emit a status marker, not fake certainty.
8. Do NOT add any of these fields to any manifest: `work_cells`, `submodules`, `work_cell_context`, `child_modules`, `nested_modules`, `implementation_cells`. The schema's top-level `not` clause rejects them.
9. Do NOT execute any partial run that commits some manifests and skips validation. All 34 manifests are updated and validated in one branch, one PR.
10. If any precondition in Section 4 fails: STOP immediately, make zero writes, and report the failed precondition ID in the PR/issue comment.

## 3. Module universe — the identity anchor

The authoritative module inventory for this task is **the 34 existing manifest files themselves**, identified by filename pattern:

```
{numeric_module_id}_{CANONICAL_SYMBOL}.manifest.json
```

Example: `50000000000000000003_D2_CALENDAR_SOURCE_ADAPTER.manifest.json` → `numeric_module_id = 50000000000000000003`, `canonical_symbol = D2_CALENDAR_SOURCE_ADAPTER`.

Rationale, stated so the agent does not "correct" it: `Claude_gen_atomic_module_catalog_vNext.json` is the locked canonical catalog but its repo copy currently has an empty `modules[]` array, and `module_catalog.json` contains only 27 records under the older symbolic model. Neither may be used to define which modules exist. The 34 manifests were generated from the locked catalog and carry canonical numeric identities. **Do not add modules, remove modules, or change any `module_identity.module_id`, `module_identity.numeric_module_id`, or `module_identity.canonical_symbol` value.**

## 4. Preconditions — verify before any write

Run these checks from repo root. All must pass.

| ID | Check | Exact command / rule | Pass condition |
|---|---|---|---|
| P1 | Manifest count | `ls EAFIX_auth_docs/manifests/module_manifests/*.manifest.json \| wc -l` | Exactly `34` |
| P2 | Schema file present and parses | `python3 -c "import json; json.load(open('EAFIX_auth_docs/01_canonical_registries/eafix_unified_atomic_module_schema_v1_0_0.json'))"` | Exit 0 |
| P3 | All 8 source files in Section 6 exist at their exact paths and parse (JSON parses; CSVs have expected header) | Per-file existence + parse | All pass |
| P4 | Every manifest currently schema-valid | Validation loop from Section 10, run pre-change | 34/34 valid |
| P5 | `file_module_mapping.csv` header row equals `FullName,Service,Role,CanonicalModules,IsTest` (note: the file's first physical line may be blank; the header is the first non-blank line) | Read and compare | Exact match |
| P6 | `updated_trading_process_aligned.json` top-level contains keys `phases` and `steps`, and `steps[0]` contains keys `step_code`, `module_id`, `dependency_step_ids`, `input_contracts`, `output_contracts`, `validation_contract`, `failure_contract`, `entrypoint_files`, `responsible`, `phase_id`, `step_number` | Key inspection | All present |

Record the SHA-256 of every Section 6 source file at read time; these hashes are written into each manifest's `staleness_policy.source_hashes` (Section 7.11) and into `manifest_population_pass2_report.md`.

## 5. Global transformation rules

**R1 — Path normalization.** Every filesystem path written into any manifest MUST be repo-relative with forward slashes. Transform: strip the exact prefix `C:\Users\richg\eafix-modular\` (case-insensitive), then replace every `\` with `/`. Example: `C:\Users\richg\eafix-modular\services\calendar-ingestor\src\2099900093260118_main.py` → `services/calendar-ingestor/src/2099900093260118_main.py`. A path that does not start with that prefix and is not already repo-relative goes to the exceptions file, not into a manifest.

**R2 — Shared files are never owned files.** In `file_module_mapping.csv`, the `CanonicalModules` column is a quoted, comma-separated list. If it contains **more than one** symbol, the file is many-to-many: it MUST be recorded in `file_ownership.shared_files` of **each** listed module and MUST NOT appear in any module's `owned_files`. If it contains **exactly one** symbol, the file goes into that module's `owned_files` (and the role-specific array per R3).

**R3 — Role routing.** The CSV `Role` column value maps a single-owner file into exactly one role-specific array in addition to `owned_files`:

| CSV `Role` value | Also append to | `file_role_index.role` value |
|---|---|---|
| `entrypoint`, `entrypoint_enterprise` | `source_files` | same as CSV value |
| `source`, `processor`, `router`, `validator`, `resolver`, `watcher`, `plugin`, `models`, `service`, `cli` | `source_files` | same as CSV value |
| `test` | `test_files` | `test` |
| `schema` | `schema_files` | `schema` |
| `contract` | `contract_files` | `contract` |
| `config` | `configuration_files` | `config` |
| `documentation` | `documentation_files` | `documentation` |
| `metrics`, `health` | `source_files` | same as CSV value |
| `package_init` | `source_files` | `package_init` |
| `generated` | `generated_files` | `generated` |
| `evidence` | `evidence_files` | `evidence` |
| any other value | `owned_files` only | `other` |

**R4 — No-match handling.** Any CSV row whose single `CanonicalModules` symbol does not match one of the 34 canonical symbols is logged in `manifest_population_exceptions.md` (columns: normalized path, raw symbol token, reason `UNKNOWN_MODULE_SYMBOL`) and written nowhere else. Rows with an **empty** `CanonicalModules` are logged with reason `UNASSIGNED_FILE` and additionally appended to `file_ownership.unassigned_candidate_files` of a module **only** when the file's normalized path starts with `services/{service}/` and that `{service}` equals the module's `service_runtime.service_home` resolved in Section 7.5. Otherwise they appear only in the exceptions file.

**R5 — Timestamp and version.** For every manifest modified: set `last_updated_utc` to the run's single UTC timestamp (ISO 8601, e.g. `2026-07-01T00:00:00Z`; use one identical value across all 34) and set `manifest_version` to `1.1.0`. Do not change `generated_at_utc`.

**R6 — Determinism.** Sort every array of paths and every array of module symbols/IDs lexicographically before writing. Two runs on the same sources must produce byte-identical manifests apart from nothing (the timestamp is fixed per R5 at run start).

**R7 — Hard-fail conditions** (abort entire task, zero commits): invalid JSON produced; any schema-const mismatch (`schema_version`, `document_type`, `packet_type`); any schema-required structural field absent after population; any write outside the Section 2 allowlist.

## 6. Authoritative source files — exact paths

Every extraction in Section 7 names one of these files by ID. No other file in the repository may be read as a data source for manifest values.

| ID | Exact repo path | Provides |
|---|---|---|
| S1 | `EAFIX_auth_docs/01_canonical_registries/updated_trading_process_aligned.json` | Step→module binding, dependency steps, I/O contracts, validation/failure contracts, entrypoints, phase IDs |
| S2 | `EAFIX_auth_docs/01_canonical_registries/process_step_catalog.json` | Step names, `module_symbol`, secondary confirmation of S1 |
| S3 | `EAFIX_auth_docs/01_canonical_registries/module_catalog.json` | Rich per-module scope/responsibilities/key functions (27 symbolic records — data source only, never inventory) |
| S4 | `EAFIX_auth_docs/01_canonical_registries/communication_channels.json` | `channels[]` with `channel_id`, `channel_name`, `channel_number`, `direction`, `protocol`, `port`, `routes`, `data_contracts`, `python_files`, `mt4_files`, `owning_module_id`, `owning_module_symbol`, `status` |
| S5 | `EAFIX_auth_docs/01_canonical_registries/module_registry.json` | `modules[].contract_boundaries.in_types/out_types`, `required_files`, `validation_rules` |
| S6 | `EAFIX_auth_docs/10_services_source_inventory_and_file_mapping/file_module_mapping.csv` | File→module ownership rows (`FullName,Service,Role,CanonicalModules,IsTest`) |
| S7 | `EAFIX_auth_docs/02_module_architecture_and_atomic_migration/EAFIX module reconciliation worksheet.csv` | Columns: `numeric_id, canonical_symbol, catalog_kind, catalog_layer, map_group, map_group_name, map_kind_label, step, phase, responsible_file, service_home_authoritative, candidate_service_INFERRED, owned_channels, mapped_file_count, csv_symbol_tokens, stale_csv_symbol, submodule_doc_status, flags` |
| S8 | `EAFIX_auth_docs/03_process_lifecycle_and_crosswalks/atonic to canonical crosswalk.csv` | Columns: `canonical_step_code, canonical_name, canonical_module_id, canonical_phase, atonic_steps, atonic_phase, relationship, notes` |
| S9 | `EAFIX_auth_docs/00_doc_control_and_authority/active_project_standards_registry.json` | `active_gates[].gate_id`, `active_rules[]` |
| S10 | `EAFIX_auth_docs/10_services_source_inventory_and_file_mapping/eafix_services_ai_reference_20260510.json` | `services_directory.service_inventory[]` with keys `service`, `status`, `purpose` |

**Conflict precedence when two sources give different values for the same field:** S1 > S2 > S5 > S3 for process/contract data; S7 > S10 for service homes; S4 is sole authority for channels; S6 is sole authority for file ownership rows. Any conflict actually encountered is also logged in `manifest_population_pass2_report.md` with both values and the winner.

## 7. Field population map

Every subsection lists: target manifest field(s), `ACTION` (`POPULATE` = write per rule; `VERIFY_ONLY` = compare and report drift, never write), the source ID, the exact lookup, and the `MISSING` behavior. "The module" below means the manifest being processed, joined to sources by, in strict order: (k1) `numeric_module_id`, (k2) `canonical_symbol`, (k3) `process step_code` from the manifest's existing `process_binding.step_code`, (k4) legacy alias listed in `module_identity.legacy_aliases`.

### 7.1 Constants and identity — `VERIFY_ONLY`

`schema_version` (`"1.0.0"`), `document_type` (`"atomic_module_manifest_schema_instance"`), `packet_type` (`"atomic_module_manifest"`), and the entire `module_identity` block. Verify constants match the schema consts and `module_identity.module_id` matches the filename. Mismatch → hard-fail R7 (const) or drift report (identity vs filename).

### 7.2 `module_classification`, `purpose`, `module_scope`, `contracts`, `documentation_set`, `state_and_failure_behavior`, `standards_and_gates` core — `VERIFY_ONLY`

These are reported `filled` in the current coverage report. For each manifest, verify (do not rewrite):

- `purpose` non-empty; if S3 has the module (match k2 on `modules[].canonical_symbol`) and `modules[].purpose` differs materially, log drift.
- `contracts.input_contracts[].name` set equals S1 `steps[].input_contracts` for the step where `steps[].module_id == canonical_symbol` (S1 uses the symbolic ID in `module_id`); same for outputs. Differences → drift report.
- `state_and_failure_behavior.validation_contract.rule` and `.failure_contract.rule` are non-empty; compare against S1 `validation_contract` / `failure_contract` text for the bound step; differences → drift report.
- `standards_and_gates.applicable_gate_ids` ⊆ the S9 gate set `{GATE-PY-QUALITY-001, GATE-PS-QUALITY-001, GATE-MQL4-SAFETY-001, GATE-CPP-DLL-001, GATE-SECURITY-001, GATE-CONTRACTS-001}`; unknown gate IDs → drift report.

### 7.3 `process_binding.upstream_modules` — `POPULATE`

Source S1. Algorithm:
1. Find the step where `steps[].module_id == canonical_symbol` (if multiple steps bind the module, take the one whose `step_code` equals the manifest's existing `process_binding.step_code`).
2. Take its `dependency_step_ids[]`.
3. Resolve each dependency step ID to its step record (match on `step_id`; if not found, match on `step_code`), read that record's `module_id` (a canonical symbol).
4. Map each symbol to its numeric ID via the module universe (Section 3 filename table). Write the resulting **symbols** into `upstream_modules[]`, deduplicated, sorted, self-references removed.

`MISSING` (module has no step in S1, or `dependency_step_ids` empty): write `[]` and add note string `"upstream_modules: no dependency steps in updated_trading_process_aligned.json"` to the manifest's top-level `notes[]`.

### 7.4 `process_binding.downstream_modules` — `POPULATE`

Source S1, derived as the exact inverse of 7.3: after computing 7.3 for all 34 modules, module B appears in module A's `downstream_modules[]` iff A appears in B's `upstream_modules[]`. Deduplicate, sort. `MISSING` (no inbound references): write `[]` with the analogous note.

### 7.5 `service_runtime` — `POPULATE` (18 manifests missing it; for the 16 that have it, `VERIFY_ONLY` on `microservice_port` and `POPULATE` only null/absent subfields)

| Manifest field | Source | Exact lookup | MISSING behavior |
|---|---|---|---|
| `service_home` | S7 | Row where `numeric_id` == module's numeric ID → column `service_home_authoritative` | `null` |
| `candidate_service_home` | S7 | Same row → column `candidate_service_INFERRED` | `null` |
| `runtime_kind` | manifest itself | Map `module_classification.deployable_scope` 1:1 (`python_service`→`python_service`, `mql4_ea`→`mql4_ea`, `mql4_indicator_or_script`→`mql4_indicator_or_script`, `desktop_ui`→`desktop_ui`, `dashboard_backend`→`dashboard_backend`, `gui_gateway`→`gui_gateway`, `shared_kernel`→`shared_kernel`, `external_infrastructure`→`external_infrastructure`, `database`→`database`, `redis_bus`→`redis_bus`, `documentation_only`→`documentation_only`, `mixed`→`mixed`) | `"unknown"` |
| `language` | manifest itself | From `deployable_scope`: `python_service`/`dashboard_backend`/`gui_gateway`→`python`; `mql4_ea`/`mql4_indicator_or_script`→`mql4`; `documentation_only`→`json_yaml_only`; `mixed`→`mixed`; else `"unknown"` | `"unknown"` |
| `microservice_port` | S4 | Any channel where `owning_module_symbol == canonical_symbol` and `port` non-null → that `port`. Multiple distinct non-null ports → exceptions file, reason `PORT_CONFLICT`, write `null` | `null` |
| `runtime_status` | S10 | `service_inventory[]` row where `service == service_home` → map `status` (`Active`→`active`, `Planned`→`planned`, `Deprecated`→`deprecated`; any other literal → `"unknown"`) | `"unknown"` |
| `startup_entrypoints` | S1 | Bound step's `entrypoint_files[]`, each normalized per R1 | `[]` |
| `host`, `deployment_unit`, `health_endpoint`, `metrics_endpoint` | — | Preserve existing value if present | `null` (do not invent) |

### 7.6 `file_ownership` — `POPULATE`

Source S6, applying R1–R4. Per module:

1. Select all CSV rows where the module's `canonical_symbol` appears in `CanonicalModules`.
2. Single-symbol rows → `owned_files` + role array per R3. Multi-symbol rows → one `shared_files` entry: `{"path": <normalized>, "sharing_policy": <"shared_kernel" if path starts with "services/common/" else "needs_refactor">, "allowed_modules": [<all listed symbols, sorted>], "reason": "file_module_mapping.csv lists multiple canonical modules"}`.
3. Build `file_role_index[]`: one entry per row from steps 1–2 with `path` (normalized), `service` (CSV `Service`), `role` (per R3 map), `ownership` (`"owned"` for single-symbol, `"shared"` for multi-symbol), `is_test` (CSV `IsTest` == `1`), `canonical_modules` (all symbols in the row, sorted).
4. `unassigned_candidate_files` per R4.
5. `allowed_files`: preserve existing; if absent write `[]`. `forbidden_files`: preserve existing; if absent write `[]`.
6. `module_root`: `"services/" + service_home` when `service_home` (7.5) is non-null, else `null`. `manifest_path`: `"EAFIX_auth_docs/manifests/module_manifests/" + <this manifest's filename>`.
7. `file_assignment_status`: `"complete"` is forbidden in this pass (the CSV is known-incomplete). Write `"partial"` when steps 1–2 produced ≥1 path; `"unassigned"` when zero paths.
8. `ownership_derivation`: `"file_module_mapping"`.

### 7.7 `dependencies[]` — `POPULATE` (merge; never delete existing entries)

Match the shape already present in the manifests, e.g.: `{"target_type":"module","target_id":"<numeric_id>","target_symbol":"<SYMBOL>","relationship":"consumes_output","consumes_output_contracts":[...],"version_constraint":null,"optional":false,"reason":"<source note>","allowed_access_mode":"declared_output_contract_only"}`.

1. **Module dependencies** — one entry per symbol in `upstream_modules` (7.3): `target_type "module"`, `target_id` = numeric ID, `target_symbol` = symbol, `relationship "consumes_output"`, `consumes_output_contracts` = intersection of (this module's S1 `input_contracts`) with (the upstream module's S1 `output_contracts`); empty intersection → `[]`. `reason`: `"updated_trading_process_aligned.json dependency_step_ids"`.
2. **Channel dependencies** — for each S4 channel where the module's symbol equals `owning_module_symbol`: entry with `target_type "communication_channel"`, `target_id` = `channel_id`, `relationship "publishes_to"` if `direction` starts with the module's side of the arrow, else `"subscribes_to"`; when the direction is ambiguous for the module, use `"requires"`. `consumes_output_contracts` = channel `data_contracts`. `reason`: `"communication_channels.json owning_module_symbol"`.
3. Deduplicate on (`target_type`,`target_id`,`relationship`); an incoming duplicate of an existing entry is skipped, never merged destructively.

`MISSING` (no upstream modules and no channels): write `[]` — the field is schema-required.

### 7.8 `communication_channels` — `POPULATE` (add the top-level section where absent)

Source S4 exclusively. `owned_channels[]`: every channel where `owning_module_symbol == canonical_symbol`, copying these keys verbatim (they are name-identical between S4 and the schema's `channelBinding`): `channel_id, channel_name, channel_number, status, direction, protocol, port, routes, data_contracts, owning_module_id, owning_module_symbol`; normalize `python_files` and `mt4_files` per R1. `consumed_channels[]`: channels whose `routes[]` or `data_contracts[]` intersect this module's S1 `input_contracts` AND whose `owning_module_symbol` differs — copy the same keys. `MISSING` (no matches at all): omit the entire optional `communication_channels` section; do not write empty scaffolding.

### 7.9 `migration_traceability` — `POPULATE` (where absent)

Source S8. Rows where `canonical_module_id == canonical_symbol` (S8 stores the symbolic ID): `source_canonical_steps[]` ← distinct `canonical_step_code`; `source_atonic_steps[]` ← distinct tokens split from `atonic_steps` (delimiter: `;` then `,`, trimmed); `crosswalk_refs[]` ← `["EAFIX_auth_docs/03_process_lifecycle_and_crosswalks/atonic to canonical crosswalk.csv"]`; `migration_status` ← `"not_migrated"` only if zero rows matched, otherwise `"new_atomic_module"` unless the manifest's `module_identity.legacy_aliases` is non-empty, in which case `"renamed_from_legacy_alias"`. `MISSING` row data for a subfield → omit that subfield (all are optional).

### 7.10 `reconciliation_status` — `POPULATE` (refresh derived values)

| Field | Rule |
|---|---|
| `service_binding_status` | `"bound"` if `service_runtime.microservice_port` non-null after 7.5, else `"unbound"` |
| `mapped_file_count` | `len(file_ownership.owned_files) + len(file_ownership.shared_files)` after 7.6 |
| `owned_channel_ids` | `channel_id` list from 7.8 `owned_channels` (or `[]`) |
| `known_flags` | S7 row (match `numeric_id`) → column `flags`, split on `;`/`,`, trimmed, sorted; empty → `[]` |
| `stale_symbol_tokens` | S7 → column `csv_symbol_tokens` split the same way, only when column `stale_csv_symbol` is truthy (`1`/`true`/`yes`); else `[]` |
| `layer_unassigned` | `true` iff manifest `module_classification.layer` equals the string `"unassigned"` |
| `last_reconciled_utc` | The single run timestamp from R5 |

### 7.11 `staleness_policy` and `source_authority` — `POPULATE`

`staleness_policy.regenerate_if_changed` and `.last_generated_from`: the exact ten S-paths of Section 6, sorted. `.source_hashes`: object mapping each S-path to its SHA-256 recorded at P-check time. `.staleness_status`: `"fresh"`. `.staleness_check_command`: preserve existing or `null`.

`source_authority.required_reference_documents` and `.conflict_resolution_order`: replace the stale flat paths with this exact ordered list (current locations, highest authority first):

```
EAFIX_auth_docs/02_module_architecture_and_atomic_migration/Claude_gen_atomic_module_catalog_vNext.json
EAFIX_auth_docs/01_canonical_registries/module_catalog.json
EAFIX_auth_docs/01_canonical_registries/process_step_catalog.json
EAFIX_auth_docs/01_canonical_registries/updated_trading_process_aligned.json
EAFIX_auth_docs/01_canonical_registries/communication_channels.json
EAFIX_auth_docs/01_canonical_registries/module_registry.json
EAFIX_auth_docs/01_canonical_registries/ui_catalog.json
EAFIX_auth_docs/01_canonical_registries/mt4 authoritative reference for ai.json
EAFIX_auth_docs/10_services_source_inventory_and_file_mapping/file_module_mapping.csv
```

`authority_policy`: preserve existing value.

### 7.12 `ai_context` — `POPULATE` only where the section or subfield is absent; never overwrite existing text

`plain_language_summary`: exactly the template `"<module_name> (<canonical_symbol>) <first sentence of purpose, verbatim>"` — no new claims. `context_priority`: `"generated"`. `forbidden_assumptions`: only when absent, seed with the four standard items from fill-instructions §8.23 verbatim: `"Do not assume socket transport is enabled."`, `"Do not assume MT4 can run without the desktop terminal open."`, `"Do not assume risk approval implies order routing."`, `"Do not assume a module can read another module's database table directly."`. All other `ai_context` subfields: leave absent (human-curated).

## 8. Per-module execution loop

For each of the 34 manifests, in filename sort order: **SCAN** (load manifest + join all sources by Section 7 keys) → **DECIDE** (compute every POPULATE value per Section 7; route failures to exceptions per rules) → **ACT/FILL** (apply writes in-memory) → **VALIDATE** (schema-validate the single manifest; on failure, hard-fail R7) → **WRITE** (serialize with 2-space indent, UTF-8, LF line endings, trailing newline) → **VERIFY** (re-read, re-validate). Only after all 34 pass: regenerate the four report files, write the two new reports, commit.

## 9. Exceptions file format

`EAFIX_auth_docs/manifests/manifest_population_exceptions.md` — one markdown table, columns: `module_symbol | field_path | reason_code | detail`. Reason codes used in this task: `UNKNOWN_MODULE_SYMBOL`, `UNASSIGNED_FILE`, `PORT_CONFLICT`, `NO_STEP_BINDING`, `ENUM_UNMAPPABLE`, `SOURCE_CONFLICT`. An exception is a logged fact, not a stop condition, except where Section 5 R7 says otherwise.

## 10. Validation gates — all must pass before commit

```bash
# G1: schema validation, all 34
python3 - << 'EOF'
import json, glob, sys
from jsonschema import Draft202012Validator
schema = json.load(open('EAFIX_auth_docs/01_canonical_registries/eafix_unified_atomic_module_schema_v1_0_0.json'))
v = Draft202012Validator(schema)
bad = 0
for p in sorted(glob.glob('EAFIX_auth_docs/manifests/module_manifests/*.manifest.json')):
    errs = list(v.iter_errors(json.load(open(p))))
    if errs:
        bad += 1
        print('FAIL', p, errs[0].message)
print('valid' if bad == 0 else f'{bad} invalid'); sys.exit(1 if bad else 0)
EOF

# G2: still exactly 34 files, no renames
test "$(ls EAFIX_auth_docs/manifests/module_manifests/*.manifest.json | wc -l)" = "34"

# G3: no forbidden fields anywhere
! grep -lE '"(work_cells|submodules|work_cell_context|child_modules)"' EAFIX_auth_docs/manifests/module_manifests/*.manifest.json

# G4: no Windows paths or backslashes leaked into manifests
! grep -l 'C:\\\\Users' EAFIX_auth_docs/manifests/module_manifests/*.manifest.json

# G5: diff surface is inside the allowlist only
git diff --name-only master | grep -v '^EAFIX_auth_docs/manifests/' | wc -l   # must output 0
```

G6 (manual rule): every manifest's `manifest_version` is `1.1.0` and `last_updated_utc` values are identical across all 34.

## 11. Deliverables, commit, PR

- 34 updated manifests; regenerated coverage + validation reports; new `manifest_population_pass2_report.md` (sections: source hashes, per-field fill counts, drift observations, conflicts encountered with winner) and `manifest_population_exceptions.md`.
- Single commit. Message:

```
manifests: population pass 2 — dependencies, runtime, file ownership, up/downstream, channels, traceability

- Populate service_runtime for 18 manifests; verify ports on 16 bound modules
- Populate file_ownership from file_module_mapping.csv with shared/owned separation (R2)
- Derive upstream_modules/downstream_modules from updated_trading_process_aligned.json
- Merge module + channel dependencies; add communication_channels sections
- Add migration_traceability from atonic-to-canonical crosswalk
- Refresh reconciliation_status, staleness_policy hashes; repoint source_authority to current paths
- No fabricated values: gaps recorded in manifest_population_exceptions.md
Task: MANIFEST-POP-PASS2-V1
```

- PR title: `Manifest population pass 2: fill dependencies, runtime, file ownership, and DAG links across all 34 atomic manifests`
- PR body must include: precondition results (P1–P6), gate results (G1–G6), the exceptions table verbatim, and the drift-observations section verbatim.

## 12. AI-reviewer checklist (paste into PR, check every box)

- [ ] P1–P6 all passed before any write; SHA-256 of all 10 sources recorded
- [ ] Exactly 34 manifest files; zero creations, deletions, renames
- [ ] `git diff --name-only master` shows only allowlisted paths
- [ ] G1 schema validation: 34/34 pass
- [ ] No `work_cells`/`submodules`/`work_cell_context`/`child_modules` anywhere
- [ ] No `C:\Users` or backslash paths in any manifest
- [ ] Every multi-module CSV file appears only in `shared_files`, never in `owned_files`
- [ ] No field contains an invented value; every gap has an exceptions row or a schema-legal status marker (`needs_review`, `unknown`, `null`, `[]`)
- [ ] `module_identity` blocks byte-identical to pre-change state in all 34 manifests
- [ ] `Claude_gen_atomic_module_catalog_vNext.json` untouched
- [ ] `upstream_modules`/`downstream_modules` are exact inverses across the 34-module set
- [ ] All 34 manifests carry `manifest_version: 1.1.0` and one identical `last_updated_utc`

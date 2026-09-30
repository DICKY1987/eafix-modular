# Unified Identity Migration — Completion Summary

**Repository:** `eafix-modular`
**Completion date:** 2026-03-17
**Authoritative spec:** `EA-REG/solution_spec.json`
**Final status:** ALL GATES PASS

---

## Executive Overview

The eafix-modular repository has been migrated from symbolic, text-based identifiers to a two-layer numeric identity system. Every file and directory in the repository now has a unique 20-digit physical ID. Every module, process step, and alias in the trading pipeline now has a unique 20-digit semantic ID. The three canonical artifacts (module catalog, process step catalog, file registry) have been regenerated with numeric-only machine keys.

### Final Pipeline Status

| Metric                 | Value    |
|------------------------|----------|
| physical_status        | **PASS** |
| alignment_status       | **PASS** |
| readiness_status       | **PASS** |
| semantic_coverage_pct  | **100%** |
| physical_warning_count | 1        |
| alignment_warning_count| 0        |

The single physical warning is intentional: `tests/fixtures/test_data/0099900043260118_active_calendar_signals.csv.tmp` is an excluded `.tmp` file that correctly carries no physical ID.

---

## Identity Scheme

### Physical Layer (file/directory identity)

| Prefix | Pattern           | Purpose                | Mechanism              |
|--------|-------------------|------------------------|------------------------|
| `1`    | `^1\d{19}$`       | File IDs               | Registry-assigned (no filename rename) |
| `2`    | `^2\d{19}$`       | Directory IDs          | Sidecar `.dir_id` anchor files |

- **791 file IDs** allocated (range `10000000000000000000`–`10000000000000000790`)
- **250 directory IDs** allocated (range `20000000000000000000`–`20000000000000000249`)
- File IDs are stored in `physical_id_registry.csv` and `migration_manifest.jsonl`, NOT embedded in filenames
- Directory IDs are persisted in `.dir_id` JSON anchor files inside each directory

### Semantic Layer (module/step/component identity)

| Prefix | Pattern           | Purpose              | Count |
|--------|-------------------|----------------------|-------|
| `5`    | `^5\d{19}$`       | Module IDs           | 27 unique (26 pipeline + SHARED_LIBS) |
| `6`    | `^6\d{19}$`       | Process Step IDs     | 26 |
| `7`    | `^7\d{19}$`       | Component IDs        | Future work only |

- **27 canonical modules** with numeric IDs `50000000000000000001` through `50000000000000000026`, plus `SHARED_LIBS` at `50000000000000000099`
- **2 legacy aliases** (resolve to existing modules, stored only in `identifier_map.json`):
  - `O2_OMS` → `O2_OMS_STATE_MACHINE` (ID `50000000000000000019`)
  - `O3_PNL_CLASSIFIER` → `O3_TRADE_CLOSE_CLASSIFIER` (ID `50000000000000000020`)
- **26 process steps** with numeric IDs `60000000000000000001` through `60000000000000000026`
- The `(loop)` control-flow sentinel (step 25) is remapped to `F1_FLOW_ORCHESTRATOR` at generation time

---

## Phase-by-Phase Detail

### PH-00 — Bootstrap

**Purpose:** Create migration configuration, schemas, and scaffolding.

**Deliverables created:**

| File | Role |
|------|------|
| `id_migration/config/physical_id_config.json` | Master config: repo root, exclusions, ID patterns, identity mechanisms |
| `id_migration/config/path_normalization_rules.json` | Path join contract: forward slashes, root stripping, case handling, dot-segment resolution |
| `id_migration/config/file_classification_rules.json` | Scope classification: 7 classes (module_owned, shared, config_data, test, tooling, legacy, out_of_scope) with match rules |
| `id_migration/schemas/dir_id.schema.json` | JSON Schema for `.dir_id` sidecar files (5 required fields: dir_id, allocated_at_utc, allocator_version, project_root_id, relative_path) |
| `id_migration/schemas/physical_id_registry.schema.json` | JSON Schema for the 11-column physical registry (with conditional constraints: files must have file_id, directories must have directory_id) |
| `COUNTER_STORE.json` | Monotonic allocation state (next-to-issue model) |
| `id_migration/scripts/validate_physical_id_config.py` | G-00 gate validator |

**Key decisions:**
- File IDs use `registry_assigned` mechanism with `rename_required: false` — no filenames are changed
- Directory IDs use `sidecar_anchor_file` mechanism with `.dir_id` as the anchor filename
- Repository root does NOT get a directory ID (`assign_root_directory_id: false`)
- 10 directories excluded from scanning (`.git`, `__pycache__`, `node_modules`, `.pytest_cache`, `.mypy_cache`, `htmlcov`, `out`, `.runs`, `.state`, `.coverage`)
- 7 file patterns excluded (`.DS_Store`, `Thumbs.db`, `*.pyc`, `*.pyo`, `*.pyd`, `*.tmp`, `*.bak`)

**Gate G-00:** PASS

---

### PH-01 — Baseline Scan

**Purpose:** Enumerate all repository objects and classify them before any ID assignment.

**Deliverables created:**

| File | Role |
|------|------|
| `id_migration/scripts/01_scan_repo_objects.py` | Repository scanner — walks filesystem, applies exclusions, classifies objects |
| `id_migration/scripts/validate_baseline_csv.py` | G-01 gate validator |
| `id_migration/output/physical_inventory_baseline.csv` | Baseline inventory (12 columns, 1042 rows) |

**Baseline inventory breakdown:**

| Metric | Count |
|--------|-------|
| Total objects | 1,042 |
| Files | 792 |
| Directories | 250 |
| Excluded objects | 1 |

**Scope class distribution:**

| Scope Class    | Count | Description |
|----------------|-------|-------------|
| `module_owned` | 646   | Files belonging to one of the 27 pipeline modules |
| `legacy`       | 220   | Files under `Directory management system/` |
| `test`         | 84    | Files under `tests/` |
| `tooling`      | 58    | Files under `scripts/`, `ci/`, `tools/`, `compliance/` |
| `shared`       | 26    | Files under `shared/` |
| `config_data`  | 8     | Files under `config/`, `schemas/` |

**CSV columns (12):** `object_type`, `relative_path`, `name`, `parent_relative_path`, `extension`, `exists_on_disk`, `is_excluded`, `object_scope_class`, `candidate_semantic_role`, `path_normalized`, `is_semantic_candidate`, `inferred_module_hint`

**Scanner invariants enforced:**
- Read-only: no repository files modified during scan
- All paths normalized per `path_normalization_rules.json` (forward slashes, no leading `./`, collapsed duplicates)
- Excluded directories pruned from traversal entirely (not walked then filtered)

**Gate G-01:** PASS

---

### PH-02 — ID Allocation

**Purpose:** Assign unique 20-digit physical IDs to every non-excluded object and produce the physical registry.

**Deliverables created:**

| File | Role |
|------|------|
| `id_migration/scripts/02_assign_physical_ids.py` | Allocator — supports plan/apply/derive modes |
| `id_migration/scripts/00_run_migration.py` | PH-02 orchestrator (runs plan → apply → derive in sequence) |
| `id_migration/output/migration_manifest.jsonl` | Allocation event ledger (3,123 events) |
| `id_migration/output/physical_id_registry.csv` | 11-column physical registry (1,042 rows) |
| 250 `.dir_id` sidecar files | One per non-excluded directory |

**Allocation summary:**

| Counter | Starting Value | Final Value | Allocated |
|---------|---------------|-------------|-----------|
| file_id | `10000000000000000000` | `10000000000000000791` | 791 |
| directory_id | `20000000000000000000` | `20000000000000000250` | 250 |

**Physical registry columns (11):** `object_type`, `file_id`, `directory_id`, `relative_path`, `name`, `parent_relative_path`, `parent_directory_id`, `extension`, `id_source`, `is_excluded`, `exists_on_disk`

**Allocator design:**
- Plan mode: computes allocations without writing anything, emits manifest events with `plan_` prefix
- Apply mode: writes `.dir_id` anchor files, advances `COUNTER_STORE.json`, emits `apply_` manifest events
- Derive mode: reads `.dir_id` files and manifest to produce `physical_id_registry.csv`
- Idempotent: existing `.dir_id` files and manifest entries are preserved, not re-allocated
- Counter store is written atomically (temp file + rename) before any `.dir_id` files to prevent ID duplication on partial runs
- Parent linkage: every directory row carries `parent_directory_id` pointing to the parent's directory_id

**`.dir_id` sidecar file format:**
```json
{
  "dir_id": "20000000000000000001",
  "allocated_at_utc": "2026-03-16T18:46:29Z",
  "allocator_version": "ph02-allocator/1.0",
  "project_root_id": null,
  "relative_path": "services"
}
```

**Gate:** No dedicated G-02 gate at this phase (PH-03 validates the output).

---

### PH-03 — Physical Validation

**Purpose:** Validate that the physical identity layer is complete and internally consistent.

**Deliverables created:**

| File | Role |
|------|------|
| `id_migration/scripts/03_validate_physical_ids.py` | G-02 gate validator |
| `id_migration/output/physical_validation_report.json` | Structured validation report |

**Validation checks (all passed):**

| Check | Result |
|-------|--------|
| Registry has exactly 11 columns | PASS |
| All non-excluded rows have physical IDs | PASS |
| Parent linkage valid (every `parent_directory_id` exists as a `directory_id`) | PASS |
| No duplicate IDs across entire registry | PASS |
| No orphaned `.dir_id` anchors (every anchor appears in registry) | PASS |
| Registry paths match filesystem positions | PASS |

**Report summary:**
- 1,042 registry rows (792 files + 250 directories)
- 1,041 non-excluded rows with valid physical IDs
- 1 excluded row (the `.tmp` test fixture) — warning only, not an error
- 0 errors, 1 warning

**Gate G-02:** PASS

---

### PH-04 — Semantic Map

**Purpose:** Map all symbolic module identifiers to unique numeric IDs and create the identifier map schema.

**Deliverables created:**

| File | Role |
|------|------|
| `EA-REG/identifier_map.json` | Authoritative symbol-to-numeric mapping |
| `EA-REG/schemas/identifier_map.schema.json` | JSON Schema for identifier_map validation |
| `EA-REG/scripts/validate_identifier_map.py` | G-03 gate validator |

**Identifier map contents:**

- **27 modules** in `modules` section:
  - 26 pipeline modules: `50000000000000000001` (F1_CONFIG_PREFERENCES) through `50000000000000000026` (P1_HEALTH_AGGREGATOR)
  - 1 shared library module: `50000000000000000099` (SHARED_LIBS)
- **2 aliases** in `aliases` section:
  - `O2_OMS` → resolves to `O2_OMS_STATE_MACHINE` (shares ID `50000000000000000019`)
  - `O3_PNL_CLASSIFIER` → resolves to `O3_TRADE_CLOSE_CLASSIFIER` (shares ID `50000000000000000020`)
- **26 process steps** in `process_steps` section:
  - `60000000000000000001` through `60000000000000000026`, each referencing its owning module's numeric ID

**Alias policy:** Aliases exist ONLY in `identifier_map.json`. They are never emitted as rows in `module_catalog.json`. This was a key design decision to prevent the phantom module entries that existed pre-migration (O2_OMS and O3_PNL_CLASSIFIER appeared as separate catalog rows).

**Gate G-03:** PASS

---

### PH-05 — Generator Update

**Purpose:** Modify `generate_three_artifact_catalogs.py` to emit numeric IDs and integrate with the physical registry.

**Files modified:**

| File | Changes |
|------|---------|
| `EA-REG/generate_three_artifact_catalogs.py` | Loads `identifier_map.json` and `physical_id_registry.csv`; resolves aliases; emits numeric `module_id`, `canonical_symbol`, `module_symbol`; adds `file_scope_class` column; stops deriving identity from symbolic parsing |

**Generator modifications implemented (GEN-001 through GEN-006 from absorbed contracts):**

1. **GEN-001:** Load `identifier_map.json` at startup
2. **GEN-002:** Load `physical_id_registry.csv` for file_id/directory_id joins
3. **GEN-003:** Replace symbolic `module_id` with numeric in all output artifacts
4. **GEN-004:** Add `canonical_symbol` as metadata field in module_catalog
5. **GEN-005:** Add `file_scope_class` column to file_registry.csv
6. **GEN-006:** Remap `(loop)` sentinel to `F1_FLOW_ORCHESTRATOR` via `LOOP_SENTINEL_REMAP`

**Regenerated artifacts:**
- `module_catalog.json` — 27 modules, all with `^5\d{19}$` primary keys and `canonical_symbol` metadata
- `process_step_catalog.json` — 26 steps, all with `^6\d{19}$` IDs and numeric `module_id` foreign keys
- `file_registry.csv` — 92 rows, 11 columns including `file_scope_class`

**Gate G-04:** PASS (3 tests in `tests/test_generator_update.py`)

---

### PH-06 — Validator & Schema Update

**Purpose:** Update validation scripts and schemas to enforce numeric patterns and cross-layer linkage.

**Deliverables created/modified:**

| File | Role |
|------|------|
| `EA-REG/schemas/module_catalog.schema.json` | JSON Schema enforcing numeric `module_id` pattern `^5\d{19}$` |
| `EA-REG/validate_three_artifact_alignment.py` | Rewritten to enforce numeric IDs, physical-registry linkage, file_scope_class, and emit three-status output |

**Validator modifications implemented (VAL-001 through VAL-007 from absorbed contracts):**

1. **VAL-001:** Reject symbolic module_id values — enforce `^5\d{19}$` pattern
2. **VAL-002:** Reject symbolic process_step_id values — enforce `^6\d{19}$` pattern
3. **VAL-003:** Emit three separate statuses: `physical_status`, `alignment_status`, `readiness_status`
4. **VAL-004:** Validate `file_scope_class` against 7 allowed values
5. **VAL-005:** Enforce blank-module_id policy (allowed only for test, tooling, legacy, out_of_scope)
6. **VAL-006:** Check cross-layer linkage (file_id/directory_id exist in physical_id_registry)
7. **VAL-007:** Emit `semantic_coverage_pct` in validation output

**Gate G-05:** PASS (1 test in `tests/test_validator_update.py`)

---

### PH-07 — Regenerate & Validate

**Purpose:** Final regeneration of all artifacts and full pipeline validation.

**Deliverables created:**

| File | Role |
|------|------|
| `.state/final_status.json` | Machine-readable pipeline completion record |
| `EA-REG/ALIGNMENT_VALIDATION_REPORT.md` | Human-readable validation report |

**Final validation sequence:**

1. `python EA-REG/generate_three_artifact_catalogs.py` — regenerated all three canonical artifacts
2. `python EA-REG/validate_three_artifact_alignment.py` — all three statuses PASS, 100% semantic coverage
3. `python id_migration/scripts/03_validate_physical_ids.py` — physical layer PASS (0 errors, 1 warning)
4. `pytest tests/test_generator_update.py tests/test_validator_update.py` — 4 tests passed

**Alignment report confirms:**
- 92 file registry rows, 27 modules, 26 process steps
- Module catalog matches schema
- Process catalog matches YAML source
- Physical registry present and linked
- No alignment errors, no readiness errors

**Gate G-06:** PASS

---

## Complete File Inventory

### Migration Infrastructure (`id_migration/`)

```
id_migration/
├── config/
│   ├── file_classification_rules.json      # 7-class scope taxonomy
│   ├── path_normalization_rules.json       # Cross-layer join contract
│   └── physical_id_config.json             # Master migration config
├── output/
│   ├── migration_manifest.jsonl            # 3,123 allocation events
│   ├── physical_id_registry.csv            # 1,042 rows, 11 columns
│   ├── physical_inventory_baseline.csv     # 1,042 rows, 12 columns
│   └── physical_validation_report.json     # G-02 structured report
├── schemas/
│   ├── dir_id.schema.json                  # .dir_id anchor schema
│   └── physical_id_registry.schema.json    # 11-column registry schema
└── scripts/
    ├── 00_run_migration.py                 # PH-02 orchestrator
    ├── 01_scan_repo_objects.py             # PH-01 scanner
    ├── 02_assign_physical_ids.py           # PH-02 allocator
    ├── 03_validate_physical_ids.py         # PH-03 / G-02 validator
    ├── validate_baseline_csv.py            # G-01 validator
    └── validate_physical_id_config.py      # G-00 validator
```

### Semantic Artifacts (`EA-REG/`)

```
EA-REG/
├── identifier_map.json                     # 27 modules + 2 aliases + 26 steps
├── module_catalog.json                     # 27 modules (numeric primary keys)
├── process_step_catalog.json               # 26 steps (numeric IDs + module FKs)
├── file_registry.csv                       # 92 rows, 11 columns (with file_scope_class)
├── generate_three_artifact_catalogs.py     # Updated generator (numeric + physical)
├── validate_three_artifact_alignment.py    # Updated validator (3-status model)
├── ALIGNMENT_VALIDATION_REPORT.md          # Human-readable report
├── schemas/
│   ├── identifier_map.schema.json          # identifier_map validation schema
│   └── module_catalog.schema.json          # Numeric module_id enforcement
└── scripts/
    └── validate_identifier_map.py          # G-03 validator
```

### Other Root-Level Artifacts

```
COUNTER_STORE.json                          # Allocation state (file: ...791, dir: ...250)
.state/final_status.json                    # Pipeline completion record
tests/test_generator_update.py              # 3 regression tests for PH-05
tests/test_validator_update.py              # 1 regression test for PH-06
```

### Distributed `.dir_id` Files

250 sidecar anchor files distributed across the repository, one per non-excluded directory. Each contains the directory's allocated `directory_id`, allocation timestamp, allocator version, and normalized relative path.

---

## Validation Gate Summary

| Gate | Phase | Command | Result |
|------|-------|---------|--------|
| G-00 | PH-00 | `python id_migration/scripts/validate_physical_id_config.py id_migration/config/physical_id_config.json` | PASS |
| G-01 | PH-01 | `python id_migration/scripts/validate_baseline_csv.py id_migration/output/physical_inventory_baseline.csv` | PASS |
| G-02 | PH-03 | `python id_migration/scripts/03_validate_physical_ids.py --config id_migration/config/physical_id_config.json` | PASS |
| G-03 | PH-04 | `python scripts/validate_identifier_map.py identifier_map.json` (from EA-REG/) | PASS |
| G-04 | PH-05 | `pytest -q tests/test_generator_update.py` | PASS (3 tests) |
| G-05 | PH-06 | `pytest -q tests/test_validator_update.py` | PASS (1 test) |
| G-06 | PH-07 | `python validate_three_artifact_alignment.py` (from EA-REG/) | PASS |

---

## Key Design Decisions

1. **Registry-only file IDs.** File identifiers are stored in `physical_id_registry.csv` and the allocation manifest. No filenames were renamed. This avoids breaking existing imports, references, and git history.

2. **Sidecar `.dir_id` anchors.** Directory identifiers are persisted as JSON files inside each directory. This survives directory renames and is visible in git diffs.

3. **Aliases in identifier_map only.** The pre-migration phantom modules `O2_OMS` and `O3_PNL_CLASSIFIER` were removed from `module_catalog.json` and placed solely in `identifier_map.json` as alias records pointing to their canonical targets.

4. **`(loop)` sentinel remapping.** Process step 25 uses `module_id: (loop)` in the YAML source as a control-flow marker. The generator remaps this to `F1_FLOW_ORCHESTRATOR` at generation time via `LOOP_SENTINEL_REMAP`, so no phantom module is created.

5. **Three-status validation model.** The validator emits `physical_status`, `alignment_status`, and `readiness_status` independently, allowing partial-pass states during incremental migration.

6. **Monotonic counter allocation.** `COUNTER_STORE.json` uses a "next ID to issue" model. The allocator writes the counter atomically before creating `.dir_id` files to prevent duplicate IDs on interrupted runs.

7. **Blank module_id policy.** Files classified as `test`, `tooling`, `legacy`, or `out_of_scope` are allowed to have blank `module_id` values. All other scope classes require a valid `^5\d{19}$` module_id.

8. **SHARED_LIBS at ID 99.** The shared library module is assigned `50000000000000000099` (outside the sequential 1–26 range) to leave room for future pipeline module additions without renumbering.

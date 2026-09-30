# EA-REG Directory — AI Operating Instructions

This directory contains the identity migration system for the eafix-modular repository. It implements a two-layer identity scheme: physical IDs for every file/directory, and semantic IDs (numeric-only) for modules, process steps, and components.

## File Roles and How to Use Them

### 1. `solution_spec.json` — THE EXECUTION SPEC (read first)

**Role:** Authoritative execution scaffold for the entire migration. This is the single source of truth for what to build, in what order, and how to validate it.

**How to use:**
- Read `phase_plan.phase_overview` to understand the 8 phases (PH-00 through PH-07) and their dependencies.
- Read `phase_contracts.{PH-XX}` for each phase's inputs, outputs, invariants, pre/postconditions, and failure modes.
- Read `step_contracts.{PH-XX}.{STEP-ID}` for step-level detail including file scopes and evidence requirements.
- Read `validation_gates.{G-XX}` for the executable validation command and expected exit code at each gate.
- Read `absorbed_contracts` for detailed per-artifact field migration rules (from the semantic spec) and per-script normative rules (from the physical spec).
- Read `path_normalization_contract` before writing any code that joins across layers by `relative_path`.
- Read `physical_id_registry_contract` for the 11-column schema that `physical_id_registry.csv` must conform to.
- Read `file_registry_contract` for the 11-column schema (including `file_scope_class`) that `file_registry.csv` must conform to after migration.
- Read `semantic_identity_contract` for the locked module count (28), alias policy, and SHARED_LIBS scope.

**Do not:** Treat any other file as overriding this spec. If a conflict exists, `solution_spec.json` wins.

---

### 2. `unified_identity_migration_plan_v2_DRAFT.md` — DOMAIN REFERENCE

**Role:** Human-readable narrative of the migration design. Provides rationale, examples, pseudocode, and open questions that `solution_spec.json` encodes as machine-checkable contracts.

**How to use:**
- Read when you need to understand *why* a decision was made (e.g., why 11 columns, why SHARED_LIBS exists, why aliases are banned from module_catalog.json).
- Reference the classification logic pseudocode (Python snippet in PH-01 section) when implementing the scanner.
- Reference the registry generation pseudocode (PH-02 section) when implementing the allocator.
- Check the "Open Questions for User" section at the bottom — these are unresolved design decisions that require user input before implementation.

**Do not:** Treat this as the execution spec. Use `solution_spec.json` for phase ordering, gate commands, and file scopes.

---

### 3. `generate_three_artifact_catalogs.py` — GENERATOR SCRIPT

**Role:** Python script that produces the three canonical artifacts: `module_catalog.json`, `process_step_catalog.json`, and `file_registry.csv`.

**How to use:**
- Run from the EA-REG directory: `python generate_three_artifact_catalogs.py`
- It reads up to four inputs:
  - `2026012201113002_updated_trading_process_v2.yaml` (process definition; searched in repo root first, then EA-REG)
  - `file_module_mapping.csv` (legacy file-to-module mapping, in EA-REG)
  - `2026012201111008_FILE_REGISTRY.json` (legacy file registry from `Directory management system/` at repo root; loaded by `load_doc_id_lookup()` for file_id lookups; silently skipped if absent)
  - `module_catalog.json` (existing catalog in EA-REG, used as seed by `load_existing_module_catalog()`; existing modules are preserved rather than regenerated)
- It outputs three files into EA-REG: `module_catalog.json`, `process_step_catalog.json`, `file_registry.csv`

**PH-05 will modify this script** to:
- Load `identifier_map.json` and resolve aliases to numeric module_ids (GEN-001 through GEN-006 in `absorbed_contracts.semantic_migration_contracts.script_changes`)
- Load the 11-column `physical_id_registry.csv` for file_id/directory_id joins
- Add `file_scope_class` column to file_registry.csv output
- Stop deriving identity from symbolic parsing

**Edge case — `(loop)` sentinel:** Process step 25 uses `module_id: (loop)` as a control-flow marker for reentry loop-back, not an independent module. The generator currently remaps it to `F1_FLOW_ORCHESTRATOR` via `LOOP_SENTINEL_REMAP`. PH-05 must remap it to the orchestrator's numeric module_id.

**Current state:** Pre-migration. Still uses symbolic module_ids (e.g., `D2_CALENDAR_SOURCE_ADAPTER`) as primary keys.

---

### 4. `validate_three_artifact_alignment.py` — VALIDATOR SCRIPT

**Role:** Validates cross-artifact alignment: checks that module_catalog, process_step_catalog, and file_registry reference each other correctly.

**How to use:**
- Run from the EA-REG directory: `python validate_three_artifact_alignment.py`
- Produces `ALIGNMENT_VALIDATION_REPORT.md` in EA-REG
- Exit code 0 = pass, 1 = fail

**PH-06 will modify this script** to:
- Enforce numeric-only module_id patterns (`^5\d{19}$`) — reject symbolic keys (VAL-001 through VAL-007 in `absorbed_contracts`)
- Emit three statuses: `physical_status`, `alignment_status`, `readiness_status`
- Validate `file_scope_class` values and blank-module_id policy
- Check cross-layer linkage (file_id/directory_id exist in physical_id_registry)
- Emit `semantic_coverage_pct`

**Current state:** Pre-migration. Validates 10-column schema with symbolic module_ids.

---

### 5. `module_catalog.json` — CANONICAL ARTIFACT (generated output)

**Role:** Machine-readable catalog of all modules in the trading pipeline. One of the three canonical artifacts.

**How to use:**
- Read `.modules[]` for the list of modules with their dependencies, interfaces, and process bindings.
- After migration: primary key will be numeric `module_id` (`^5\d{19}$`), with `canonical_symbol` as metadata.

**Do not:** Edit manually. Regenerate by running `generate_three_artifact_catalogs.py`.

---

### 6. `process_step_catalog.json` — CANONICAL ARTIFACT (generated output)

**Role:** Machine-readable catalog of the 26 process steps in the canonical trading workflow. One of the three canonical artifacts.

**How to use:**
- Read `.steps[]` for step ordering, module bindings, input/output contracts, and entrypoint files.
- After migration: `module_id` foreign keys will be numeric, with `module_symbol` as optional metadata.

**Do not:** Edit manually. Regenerate by running `generate_three_artifact_catalogs.py`.

---

### 7. `file_registry.csv` — CANONICAL ARTIFACT (generated output)

**Role:** CSV registry mapping files to modules and process steps. One of the three canonical artifacts.

**How to use:**
- Currently 10 columns: `file_id, file_name, file_path, directory_id, module_id, process_step_id, purpose, responsibilities, dependencies, key_functions`
- After migration: 11 columns (adds `file_scope_class`), with numeric module_id values and physical IDs from the registry.

**Do not:** Edit manually. Regenerate by running `generate_three_artifact_catalogs.py`.

---

### 8. `baseline_scanner_spec.json` — SCHEMA (PH-01 input)

**Role:** JSON Schema defining the configuration and output format for the baseline repository scanner built in PH-01.

**How to use:**
- Read `scanner_config` for the required configuration fields (repository_root, exclusions, output_format).
- Read `inventory_schema` for the required output columns of `physical_inventory_baseline.csv`.
- When building `id_migration/scripts/01_scan_repo_objects.py`, validate its config against this schema and ensure its output conforms to `inventory_schema`.

---

### 9. `physical_id_config_schema.json` — SCHEMA (PH-00 input)

**Role:** JSON Schema defining the structure of `physical_id_config.json`, created in PH-00.

**How to use:**
- When building PH-00-STEP-002, create `id_migration/config/physical_id_config.json` that validates against this schema.
- Key fields: `repository_root`, `excluded_directories`, `directory_identity_mechanism` (sidecar `.dir_id`), `file_identity_mechanism` (registry_assigned, rename_required=false), `physical_id_patterns` (file_id `^1\d{19}$`, directory_id `^2\d{19}$`).

---

### 10. `file_module_mapping.csv` — LEGACY INPUT (temporary)

**Role:** Legacy CSV that maps repository files to canonical modules using symbolic module_ids. Used as input by `generate_three_artifact_catalogs.py`.

**How to use:**
- Columns: `FullName` (absolute path), `Service`, `Role`, `CanonicalModules` (comma-separated symbolic module_ids), `IsTest`
- The generator reads this via `load_legacy_mapping_rows()` to populate file_registry.csv.
- Contains symbolic module_ids like `D2_CALENDAR_SOURCE_ADAPTER` — these are the values that PH-05 will convert to numeric.

**Lifespan:** This file is needed until PH-05 updates the generator to use `identifier_map.json` instead. After that, it can be retired.

---

### 11. `MODULE CENTRIC REPOSITORY BEST PRACTICES.pdf` — REFERENCE

**Role:** Background reference document on module-centric repository architecture patterns.

**How to use:**
- Consult when making architectural decisions about module boundaries, file ownership, or repository organization.
- Not directly referenced by any script or schema.

---

## Phase Dependency Graph

```
PH-00 --> PH-01 --> PH-02 --> PH-03 (HARD GATE)
  |                              |
  +--> PH-04 (parallel) ---------+
                                 v
                          PH-05 --> PH-06 --> PH-07
```

PH-04 (semantic map) runs in parallel with PH-01 through PH-03 (physical layer). PH-05 cannot start until both PH-03 and PH-04 pass.

## Key Contracts (quick reference)

| Contract | Location in solution_spec.json |
|----------|-------------------------------|
| Path normalization | `path_normalization_contract` |
| Physical registry 11-column schema | `physical_id_registry_contract` |
| File registry + file_scope_class | `file_registry_contract` |
| 28 canonical modules + SHARED_LIBS | `semantic_identity_contract` |
| Generator modifications (GEN-001..006) | `absorbed_contracts.semantic_migration_contracts.script_changes[0]` |
| Validator modifications (VAL-001..007) | `absorbed_contracts.semantic_migration_contracts.script_changes[1]` |
| Physical layer normative rules | `absorbed_contracts.physical_migration_contracts.normative_rules` |
| Script deprecation map | `absorbed_contracts.physical_migration_contracts.deprecation_map` |

## Rules

1. **Never write symbolic module_ids into machine key fields.** After PH-05, all `module_id` values in canonical artifacts must match `^5\d{19}$`.
2. **Registry is always derived, never written directly.** The allocator writes `.dir_id` files and updates `COUNTER_STORE.json`; a separate derive step produces `physical_id_registry.csv`.
3. **Normalize paths before any cross-layer join.** Use forward slashes, strip leading `./`, resolve `.` and `..`, collapse duplicates. See `path_normalization_contract`.
4. **Aliases live only in `identifier_map.json`.** Never add alias entries to `module_catalog.json`.
5. **Blank `module_id` is valid only for** `file_scope_class` values: `test`, `tooling`, `legacy`, `out_of_scope`.

---

## Module Catalog JSON Schema (Target State)

> Source: `EA-REG/superseded/strict target specmodcat.txt` (merged 2026-04-10)

### Required Top-Level Sections per Module Object

```json
{
  "module_id": "string (^5\\d{19}$ after migration)",
  "module_name": "string",
  "module_kind": "string",
  "version": "string (^\\d+\\.\\d+\\.\\d+$)",
  "status": "active | deprecated | experimental | planned",
  "purpose": "...",
  "interfaces": [...],
  "invariants": [...],
  "dependencies": [...]
}
```

**Optional fields:** `responsibilities`, `key_functions`, `process_bindings`, `filesystem_hints`, `quality_gates`, `mvp_classification`, `tags`, `notes`

### Forbidden Shapes

| Field | Rule | Reason |
|-------|------|--------|
| `quality_gates.invariants` | Forbidden as canonical location | Invariants are module contract data, not gate metadata |
| `interface` (singular) | Forbidden field name | Must be plural `interfaces` — catalog supports multiple |

### Key Rule

`invariants` must be promoted to their own top-level field. Do **not** nest them under `quality_gates`.

---

## File Scanner v2.0 — Registry-Ready Fields

> Source: `0199900009260118_FILE_SCANNER_ENHANCEMENTS.md` (merged 2026-04-10)

The Enhanced File Scanner v2.0 extracts three additional fields for database registry integration:

| Field | Description | Pattern |
|-------|-------------|---------|
| `doc_id` | 16-digit prefix extracted from filename | `^\d{16}_.*` → extracts the 16 digits |
| `relative_path` | Path relative to scan root, forward-slash normalized | `os.path.relpath(file_path, scan_root)` |
| `extension` | Lowercase, dot-stripped file extension | `.PDF` → `pdf`, `.py` → `py` |

**CSV schema additions:** `doc_id`, `relative_path`, `extension` columns appended to the standard scan output.

**Markdown output:** Streaming inventory table written per-file during scan (not buffered). Columns: `doc_id | relative_path | size | modified_utc | mime_type | perms`

**Empty `doc_id`:** Files without 16-digit prefix show empty cell — valid and expected for non-registered files.

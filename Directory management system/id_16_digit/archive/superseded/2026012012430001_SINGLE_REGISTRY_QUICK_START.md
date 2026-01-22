# Single Unified SSOT Registry - Quick Start Guide

**Date**: 2026-01-20  
**Status**: READY TO IMPLEMENT

---

## What Changed

**OLD PLAN** (4 separate registries):
```
registry/
├── REGISTRY_A_FILE_ID.json      ❌ Removed
├── REGISTRY_B_ASSET_ID.json     ❌ Removed
├── REGISTRY_C_TRANSIENT_ID.json ❌ Removed
└── REGISTRY_D_EDGE_RELATION.json ❌ Removed
```

**NEW PLAN** (1 unified registry):
```
registry/
└── UNIFIED_SSOT_REGISTRY.json   ✅ ONE FILE FOR EVERYTHING
```

---

## Core Concept

**One registry file with `record_kind` discriminator:**
- `record_kind = "entity"` → Files, assets, transients, externals
- `record_kind = "edge"` → Relationships with evidence
- `record_kind = "generator"` → Derived artifact generators

**Every record has ALL 80 columns** (sparse: unused fields are `null`)

---

## Example Records

### Entity Record (File)
```json
{
  "record_kind": "entity",
  "record_id": "REC-000001",
  "entity_id": "0199900001260118",
  "entity_kind": "file",
  "doc_id": "0199900001260118",
  "filename": ".aider.chat.history.md",
  "extension": ".md",
  "relative_path": "0199900001260118_.aider.chat.history.md",
  "status": "active",
  "created_utc": "2026-01-19T03:54:44Z",
  
  // All other columns are null for file entities
  "asset_id": null,
  "transient_id": null,
  "edge_id": null,
  "generator_id": null
}
```

### Edge Record (Relationship)
```json
{
  "record_kind": "edge",
  "record_id": "REC-000500",
  "edge_id": "EDGE-20260120-000001",
  "source_entity_id_edge": "0199900001260118",
  "target_entity_id_edge": "2099900005260118",
  "rel_type": "DOCUMENTS",
  "confidence": 0.95,
  "evidence_method": "markdown_link_parse",
  "evidence_locator": "line:42",
  "status": "active",
  
  // All entity fields are null for edges
  "entity_id": null,
  "doc_id": null,
  "asset_id": null
}
```

### Generator Record (Derived Artifact)
```json
{
  "record_kind": "generator",
  "record_id": "REC-001000",
  "generator_id": "GEN-000001",
  "generator_name": "module_index_builder",
  "output_path_pattern": "modules/{module_id}/INDEX.md",
  "declared_dependencies": ["entity_kind", "module_id", "status"],
  "status": "active",
  
  // All entity/edge fields are null for generators
  "entity_id": null,
  "edge_id": null
}
```

---

## Migration Steps

### Step 1: Test Migration (Dry Run)

```bash
cd "Directory management system\id_16_digit\core"
python migrate_to_unified_ssot.py --dry-run --validate --sample
```

**Output**:
```
SINGLE UNIFIED SSOT REGISTRY MIGRATION
======================================================================

📂 Loading current registry: registry/ID_REGISTRY.json
   Version: 1.0
   Scope: 260119
   Allocations: 2624

🏗️  Creating unified SSOT structure...
   Columns in superset: 80

🔄 Transforming allocations → entity records...
   Transformed 100/2624 records...
   Transformed 200/2624 records...
   ...
   Transformed 2624/2624 records...

✅ Transformation complete:
   Total: 2624
   Transformed: 2624
   Errors: 0

📋 Sample entity record:
{
  "record_kind": "entity",
  "record_id": "REC-000001",
  "entity_id": "0199900001260118",
  "entity_kind": "file",
  "doc_id": "0199900001260118",
  "filename": ".aider.chat.history.md",
  "extension": ".md",
  "relative_path": "0199900001260118_.aider.chat.history.md",
  "directory_path": ".",
  "status": "active",
  "type_code": "01"
}

VALIDATION: Unified SSOT Registry
======================================================================

1. Checking record_kind field...
   ✅ PASS: All 2624 records have record_kind

2. Record kind distribution:
   entity: 2624

3. Checking entity records...
   ✅ PASS: All entity records valid

4. Checking edge records...
   ℹ️  No edge records (expected after Phase 1)

5. Checking schema compliance (80-column superset)...
   ✅ PASS: All records have all 80 columns

======================================================================
✅ VALIDATION PASSED: Unified SSOT registry is valid

🔍 Dry run complete - no files written
```

### Step 2: Run Actual Migration

```bash
python migrate_to_unified_ssot.py --input ../registry/ID_REGISTRY.json --output ../registry/UNIFIED_SSOT_REGISTRY.json --validate
```

### Step 3: Verify Output

```bash
# Check file size
ls -lh ../registry/UNIFIED_SSOT_REGISTRY.json

# Count records
python -c "import json; r=json.load(open('../registry/UNIFIED_SSOT_REGISTRY.json')); print(f'Records: {len(r[\"records\"])}')"

# Verify all IDs present
python -c "import json; old=json.load(open('../registry/ID_REGISTRY.json')); new=json.load(open('../registry/UNIFIED_SSOT_REGISTRY.json')); old_ids=set(a['id'] for a in old['allocations']); new_ids=set(r['entity_id'] for r in new['records'] if r['record_kind']=='entity'); print('✅ All IDs preserved' if old_ids==new_ids else '❌ Missing IDs')"
```

---

## Query API

### Basic Queries

```python
from unified_registry import UnifiedRegistry

# Load registry
ur = UnifiedRegistry("registry/UNIFIED_SSOT_REGISTRY.json")

# Find entity by ID
entity = ur.find_entity("0199900001260118")
print(entity["filename"])  # .aider.chat.history.md

# Find all files
files = ur.find_entities(entity_kind="file", status="active")
print(f"Found {len(files)} active files")

# Find files in a module
module_files = ur.find_entities(
    entity_kind="file",
    module_id="MODULE-001",
    status="active"
)

# Find files by type
markdown_files = ur.find_entities(
    entity_kind="file",
    extension=".md"
)
```

### Relationship Queries

```python
# Get all relationships for a file
edges = ur.get_relationships("0199900001260118")
for edge in edges:
    print(f"{edge['rel_type']}: {edge['target_entity_id']}")

# Get dependencies
deps = ur.get_dependencies("2099900005260118", recursive=True)
print(f"Total dependencies: {len(deps)}")

# Get what depends on this file
dependents = ur.get_dependents("2099900005260118")
print(f"Files that depend on this: {len(dependents)}")
```

---

## Adding New Records

### Add Asset

```python
ur = UnifiedRegistry("registry/UNIFIED_SSOT_REGISTRY.json")

asset_id = ur.add_entity(
    entity_kind="asset",
    asset_id="SCHEMA-000001",
    asset_family="json_schema",
    asset_version="1.0.0",
    canonical_path="contracts/schemas/registry.schema.json",
    short_description="Unified registry validation schema",
    status="active"
)

ur.save()  # Write back to file
```

### Add Relationship

```python
edge_id = ur.add_edge(
    source_id="0199900001260118",
    target_id="2099900005260118",
    rel_type="DOCUMENTS",
    confidence=0.95,
    evidence={
        "method": "markdown_link_parse",
        "locator": "line:42",
        "snippet": "See [eafix_cli](...)",
        "observed_utc": "2026-01-20T12:00:00Z",
        "tool_version": "scanner_v2.0"
    }
)

ur.save()
```

### Add Transient Run

```python
run_id = ur.add_entity(
    entity_kind="transient",
    transient_id="RUN-20260120-0001",
    transient_type="run_id",
    ttl_seconds=86400,
    expires_utc="2026-01-21T12:00:00Z",
    short_description="File system scan",
    status="closed"
)

ur.save()
```

---

## Column Reference

### Core (9 columns) - ALL records

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `record_kind` | enum | ✅ | entity \| edge \| generator |
| `record_id` | string | ✅ | Unique primary key |
| `status` | enum | ✅ | active \| deprecated \| archived |
| `created_utc` | timestamp | ✅ | Creation time |
| `updated_utc` | timestamp | ✅ | Last update time |
| `created_by` | string | ✅ | Creator (user/tool) |
| `updated_by` | string | ✅ | Last updater |
| `notes` | string | ❌ | Free-form notes |
| `tags` | array | ❌ | Tags for grouping |

### Entity (40 columns) - when record_kind = "entity"

**Identity**:
- `entity_id` (unique across all entities)
- `entity_kind` (file | asset | transient | external)

**File-specific** (11 columns):
- `doc_id`, `filename`, `extension`, `relative_path`, `directory_path`
- `size_bytes`, `mtime_utc`, `sha256`, `content_type`, `absolute_path`

**Asset-specific** (4 columns):
- `asset_id`, `asset_family`, `asset_version`, `canonical_path`

**Transient-specific** (4 columns):
- `transient_id`, `transient_type`, `ttl_seconds`, `expires_utc`

**External-specific** (3 columns):
- `external_ref`, `external_system`, `resolver_hint`

**Module/process** (6 columns):
- `module_id`, `module_id_source`, `module_id_override`
- `process_id`, `process_step_id`, `process_step_role`

**Classification** (8 columns):
- `role_code`, `type_code`, `function_code_1/2/3`
- `entrypoint_flag`, `short_description`

**Provenance** (5 columns):
- `first_seen_utc`, `last_seen_utc`, `scan_id`
- `source_entity_id`, `supersedes_entity_id`

### Edge (12 columns) - when record_kind = "edge"

- `edge_id` (unique)
- `source_entity_id_edge`, `target_entity_id_edge`
- `rel_type`, `directionality`
- `confidence` (0.0-1.0)
- `evidence_method`, `evidence_locator`, `evidence_snippet`
- `observed_utc`, `tool_version`, `edge_flags`

### Generator (17 columns) - when record_kind = "generator"

- `generator_id`, `generator_name`, `generator_version`
- `output_kind`, `output_path`, `output_path_pattern`
- `declared_dependencies`, `input_filters`
- `sort_rule_id`, `sort_keys`
- `template_ref_entity_id`, `validator_id`, `validation_rules`
- `last_build_utc`, `source_registry_hash`, `source_registry_scan_id`
- `output_hash`, `build_report_entity_id`

---

## Benefits

### ✅ Single Source of Truth
- ONE file to back up
- ONE file to version control
- ONE file to query

### ✅ Type Safety
- `record_kind` enforces record type
- All columns present (sparse, but present)
- Schema validation possible

### ✅ Referential Integrity
- Edges reference entities in same file
- Validation checks all references
- No dangling pointers

### ✅ Graph Queries
- Find dependencies/dependents
- Traverse relationship chains
- Detect circular dependencies

### ✅ Atomic Operations
- All changes in one file
- Transaction-safe updates
- No cross-file consistency issues

---

## SQLite Migration (Optional)

For production scale (10,000+ records), migrate to SQLite:

```bash
python migrate_to_unified_ssot.py --format sqlite --output registry/UNIFIED_SSOT_REGISTRY.db
```

**Benefits**:
- ✅ Faster queries (indexes)
- ✅ Built-in referential integrity (foreign keys)
- ✅ ACID transactions
- ✅ Concurrent access
- ✅ Smaller file size (compressed)

---

## Migration Timeline

### Week 1: Single Registry Migration
- Run `migrate_to_unified_ssot.py`
- Validate all IDs preserved
- Test queries with UnifiedRegistry

### Week 2: Add Edge Scanner
- Scan Python imports → edge records
- Scan markdown links → edge records
- Populate `record_kind="edge"` records

### Week 3: Add Asset Registry
- Identify schemas/templates
- Create `entity_kind="asset"` records
- Link files to assets via edges

### Week 4: Add Transient Tracking
- Track scan runs → `entity_kind="transient"`
- Track build events
- Link runs to modified files

### Week 5: Add Generator Registry
- Define generators → `record_kind="generator"`
- Track derived artifacts
- Enforce deterministic rebuilds

---

## Ready to Start?

```bash
# Test migration
cd "Directory management system\id_16_digit\core"
python migrate_to_unified_ssot.py --dry-run --validate --sample

# If dry run passes, run actual migration
python migrate_to_unified_ssot.py --validate
```

**That's it!** One command to migrate to single unified SSOT registry.

---

**END OF QUICK START GUIDE**

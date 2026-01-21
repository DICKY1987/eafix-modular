---
doc_id: 2026012012410001
title: Single Unified SSOT Registry - Complete Specification
date: 2026-01-20T12:41:00Z
status: AUTHORITATIVE
classification: REGISTRY_SPECIFICATION
author: System Architecture - Single SSOT Registry
version: 2.1
supersedes: 2026012012180001 (4-registry plan)
last_updated: 2026-01-20T14:47:00Z
---

# Single Unified SSOT Registry - Complete Specification

## Change Log

### Version 2.1 (2026-01-20T14:47:00Z)
**Alignment with Unified Superset - Resolves 4 Identified Deltas**

1. **`entity_kind` enum expansion** - Added `other` to enum: `file | asset | transient | external | module | directory | process | other`
   - Allows for future entity types not covered by current categories
   - Updated in: YAML schema (line 88), SQLite schema (line 808), column superset (line 11)

2. **`status` enum expansion** - Added transient lifecycle states: `closed | running | pending | failed`
   - Previously: `active | deprecated | quarantined | archived | deleted`
   - Now includes transient-specific states (e.g., transient entity at line 221 uses `status: "closed"`)
   - Updated in: Core schema (line 70), SQLite schema (line 798), column superset (line 3)

3. **`rel_type` normalization rule** - Established uppercase convention
   - All `rel_type` values MUST be uppercase (e.g., `DOCUMENTS`, `IMPORTS`)
   - Added normalization rule: All ingestion processes must call `.upper()` on rel_type
   - Documented in: Relationship Types section (line 347), column superset (line 55)

4. **Column count updated** - 79 → 80 columns
   - `directory_path` was already present in spec (confirmed at lines 113, 193, 434, 576, 811)
   - Count updated due to `module_id_override` being explicitly numbered
   - Total: 9 core + 41 entity + 12 edge + 17 generator + 1 (module_id_override) = 80

**Note**: `directory_path` already existed in the spec; no code changes needed for this field.

## Executive Summary

**One registry. All entity types. All relationships. One source of truth.**

This specification defines a **single physical registry file** using a `record_kind` discriminator to represent all entity types (files, assets, transients, externals) and all relationships (edges, generators) in one authoritative data store.

**Key Principle**: One SSOT artifact with typed records, not four separate registries.

---

## 1. Registry Structure

### Physical Format

**File**: `UNIFIED_SSOT_REGISTRY.json` (or `.db` for SQLite)

```json
{
  "meta": {
    "document_id": "REG-UNIFIED-SSOT-720066-001",
    "registry_name": "UNIFIED_SSOT_REGISTRY",
    "version": "2.0.0",
    "status": "active",
    "last_updated_utc": "2026-01-20T12:41:00Z",
    "authoritative": true,
    "description": "Single source of truth for all entities, relationships, and generators"
  },
  "counters": {
    "record_id": {"current": 0},
    "file_doc_id": {"999_01_260119": {"current": 9}},
    "asset_id": {"SCHEMA": {"current": 0}},
    "transient_id": {"RUN_20260120": {"current": 1}},
    "edge_id": {"20260120": {"current": 0}},
    "generator_id": {"current": 0}
  },
  "records": []
}
```

### Record Discriminator

Every record has `record_kind` as the first field:
- `record_kind = "entity"` → Entity record (file/asset/transient/external)
- `record_kind = "edge"` → Relationship record
- `record_kind = "generator"` → Derived artifact generator

---

## 2. Core Schema (All Records)

### Fields Present in ALL Records

```yaml
# Universal fields (required for all record_kind)
record_kind: enum(entity | edge | generator)
record_id: string (globally unique, primary key)
status: enum(active | deprecated | quarantined | archived | deleted | closed | running | pending | failed)
# Note: 'closed', 'running', 'pending', 'failed' are primarily for transient entities
created_utc: timestamp
updated_utc: timestamp
created_by: string (user/tool)
updated_by: string (user/tool)
notes: string (optional)
tags: array[string] (optional)
```

---

## 3. Entity Records (record_kind = "entity")

### Entity Core Fields

```yaml
# When record_kind = "entity"
entity_id: string (globally unique across all entities)
entity_kind: enum(file | asset | transient | external | module | directory | process | other)
```

### 3.1 File Entity (entity_kind = "file")

**Replaces old Registry A**

```json
{
  "record_kind": "entity",
  "record_id": "REC-000001",
  "entity_id": "0199900001260118",
  "entity_kind": "file",
  "status": "active",
  "created_utc": "2026-01-19T03:54:44.299192Z",
  "updated_utc": "2026-01-19T03:54:44.299192Z",
  "created_by": "import_from_scan",
  "updated_by": "import_from_scan",
  
  // File-specific fields
  "doc_id": "0199900001260118",
  "filename": ".aider.chat.history.md",
  "extension": ".md",
  "relative_path": "0199900001260118_.aider.chat.history.md",
  "absolute_path": null,
  "directory_path": ".",
  "size_bytes": 12345,
  "mtime_utc": "2026-01-19T03:54:44Z",
  "sha256": "abc123...",
  "content_type": "text/markdown",
  
  // Module/process mapping
  "module_id": null,
  "module_id_source": null,
  "process_id": null,
  "process_step_id": null,
  "process_step_role": null,
  
  // Classification
  "role_code": "doc",
  "type_code": "01",
  "function_code_1": null,
  "function_code_2": null,
  "function_code_3": null,
  "entrypoint_flag": false,
  "short_description": "Aider chat history",
  
  // Provenance
  "first_seen_utc": "2026-01-19T03:54:44Z",
  "last_seen_utc": "2026-01-20T12:00:00Z",
  "scan_id": "RUN-20260120-0001",
  "source_entity_id": null,
  "supersedes_entity_id": null,
  
  // Null fields for other entity kinds
  "asset_id": null,
  "asset_family": null,
  "asset_version": null,
  "canonical_path": null,
  "transient_id": null,
  "transient_type": null,
  "ttl_seconds": null,
  "expires_utc": null,
  "external_ref": null,
  "external_system": null,
  "resolver_hint": null
}
```

### 3.2 Asset Entity (entity_kind = "asset")

**Replaces old Registry B**

```json
{
  "record_kind": "entity",
  "record_id": "REC-000002",
  "entity_id": "SCHEMA-000001",
  "entity_kind": "asset",
  "status": "active",
  "created_utc": "2026-01-20T12:00:00Z",
  "updated_utc": "2026-01-20T12:00:00Z",
  "created_by": "asset_allocator",
  "updated_by": "asset_allocator",
  
  // Asset-specific fields
  "asset_id": "SCHEMA-000001",
  "asset_family": "json_schema",
  "asset_version": "1.0.0",
  "canonical_path": "contracts/schemas/json/registry_a.schema.json",
  "short_description": "Registry A validation schema",
  
  // Provenance
  "first_seen_utc": "2026-01-20T12:00:00Z",
  "last_seen_utc": "2026-01-20T12:00:00Z",
  "scan_id": null,
  "source_entity_id": null,
  "supersedes_entity_id": null,
  
  // Null fields for other entity kinds
  "doc_id": null,
  "filename": null,
  "extension": null,
  "relative_path": null,
  "absolute_path": null,
  "directory_path": null,
  "size_bytes": null,
  "mtime_utc": null,
  "sha256": null,
  "content_type": null,
  "module_id": null,
  "role_code": null,
  "type_code": null,
  "transient_id": null,
  "transient_type": null,
  "ttl_seconds": null,
  "expires_utc": null,
  "external_ref": null,
  "external_system": null,
  "resolver_hint": null
}
```

### 3.3 Transient Entity (entity_kind = "transient")

**Replaces old Registry C**

```json
{
  "record_kind": "entity",
  "record_id": "REC-000003",
  "entity_id": "RUN-20260120-0001",
  "entity_kind": "transient",
  "status": "closed",
  "created_utc": "2026-01-20T12:00:00Z",
  "updated_utc": "2026-01-20T12:05:23Z",
  "created_by": "scanner",
  "updated_by": "scanner",
  
  // Transient-specific fields
  "transient_id": "RUN-20260120-0001",
  "transient_type": "run_id",
  "ttl_seconds": 86400,
  "expires_utc": "2026-01-21T12:00:00Z",
  "short_description": "File system scan run",
  
  // Provenance
  "first_seen_utc": "2026-01-20T12:00:00Z",
  "last_seen_utc": "2026-01-20T12:05:23Z",
  "scan_id": "RUN-20260120-0001",
  
  // Null fields for other entity kinds
  "doc_id": null,
  "filename": null,
  "extension": null,
  "relative_path": null,
  "asset_id": null,
  "asset_family": null,
  "asset_version": null,
  "canonical_path": null,
  "external_ref": null,
  "external_system": null,
  "resolver_hint": null
}
```

### 3.4 External Entity (entity_kind = "external")

```json
{
  "record_kind": "entity",
  "record_id": "REC-000004",
  "entity_id": "GITHUB-microsoft/vscode",
  "entity_kind": "external",
  "status": "active",
  "created_utc": "2026-01-20T12:00:00Z",
  "updated_utc": "2026-01-20T12:00:00Z",
  "created_by": "external_ref_scanner",
  "updated_by": "external_ref_scanner",
  
  // External-specific fields
  "external_ref": "microsoft/vscode",
  "external_system": "github",
  "resolver_hint": "https://github.com/microsoft/vscode",
  "short_description": "VS Code repository",
  
  // Null fields for other entity kinds
  "doc_id": null,
  "filename": null,
  "asset_id": null,
  "transient_id": null
}
```

---

## 4. Edge Records (record_kind = "edge")

**Replaces old Registry D**

```json
{
  "record_kind": "edge",
  "record_id": "REC-000005",
  "status": "active",
  "created_utc": "2026-01-20T12:00:00Z",
  "updated_utc": "2026-01-20T12:00:00Z",
  "created_by": "relationship_scanner",
  "updated_by": "relationship_scanner",
  
  // Edge-specific fields
  "edge_id": "EDGE-20260120-000001",
  "source_entity_id": "0199900001260118",
  "target_entity_id": "2099900005260118",
  "rel_type": "DOCUMENTS",
  "directionality": "directed",
  
  // Evidence + confidence
  "confidence": 0.95,
  "evidence_method": "markdown_link_parse",
  "evidence_locator": "line:42",
  "evidence_snippet": "See [eafix_cli](2099900005260118_eafix_cli.py)",
  "observed_utc": "2026-01-20T12:00:00Z",
  "tool_version": "scanner_v2.0",
  "edge_flags": ["verified"],
  
  // Null fields for entity records
  "entity_id": null,
  "entity_kind": null,
  "doc_id": null,
  "filename": null,
  "asset_id": null,
  "transient_id": null,
  "generator_id": null
}
```

### Relationship Types

```yaml
rel_type: enum(
  IMPORTS,
  CALLS,
  TESTS,
  DOCUMENTS,
  USES_SCHEMA,
  USES_TEMPLATE,
  GENERATED_FROM,
  PRODUCES,
  DEPENDS_ON,
  DUPLICATES,
  PARALLEL_IMPL,
  IMPLEMENTS_ASSET,
  REFERENCES_FILE,
  REFERENCES_ASSET,
  CONTAINS,
  CONFLICTS_WITH
)
# Normalization rule: rel_type values MUST be uppercase
# All ingestion processes should normalize to uppercase via: rel_type.upper()
```

---

## 5. Generator Records (record_kind = "generator")

**New capability for derived artifact tracking**

```json
{
  "record_kind": "generator",
  "record_id": "REC-000006",
  "status": "active",
  "created_utc": "2026-01-20T12:00:00Z",
  "updated_utc": "2026-01-20T12:00:00Z",
  "created_by": "generator_registry",
  "updated_by": "generator_registry",
  
  // Generator-specific fields
  "generator_id": "GEN-000001",
  "generator_name": "module_index_builder",
  "generator_version": "1.0.0",
  "output_kind": "module_index",
  "output_path": null,
  "output_path_pattern": "modules/{module_id}/INDEX.md",
  
  // Input specification
  "declared_dependencies": ["entity_kind", "module_id", "status", "role_code", "type_code", "filename"],
  "input_filters": {
    "entity_kind": "file",
    "status": "active",
    "module_id": "{module_id}"
  },
  
  // Ordering specification
  "sort_rule_id": "sort_by_role_type_filename_v1",
  "sort_keys": ["role_code", "type_code", "filename"],
  
  // Template reference
  "template_ref_entity_id": null,
  "validator_id": null,
  "validation_rules": null,
  
  // Build traceability
  "last_build_utc": "2026-01-20T12:00:00Z",
  "source_registry_hash": "sha256:abc123...",
  "source_registry_scan_id": null,
  "output_hash": "sha256:def456...",
  "build_report_entity_id": null,
  
  // Null fields for entity/edge records
  "entity_id": null,
  "entity_kind": null,
  "edge_id": null,
  "source_entity_id": null,
  "target_entity_id": null
}
```

---

## 6. Complete Column Superset (80 columns)

### Core Columns (9) - ALL records

1. `record_kind` *(entity | edge | generator)*
2. `record_id` *(unique primary key)*
3. `status` *(active | deprecated | quarantined | archived | deleted | closed | running | pending | failed)*
4. `notes` *(optional)*
5. `tags` *(array, optional)*
6. `created_utc`
7. `updated_utc`
8. `created_by`
9. `updated_by`

### Entity Columns (41) - when record_kind = "entity"

**Identity**
10. `entity_id`
11. `entity_kind` *(file | asset | transient | external | module | directory | process | other)*

**File-specific** (entity_kind = "file")
12. `doc_id`
13. `filename`
14. `extension`
15. `relative_path`
16. `absolute_path`
17. `directory_path`
18. `size_bytes`
19. `mtime_utc`
20. `sha256`
21. `content_type`

**Asset-specific** (entity_kind = "asset")
22. `asset_id`
23. `asset_family`
24. `asset_version`
25. `canonical_path`

**Transient-specific** (entity_kind = "transient")
26. `transient_id`
27. `transient_type`
28. `ttl_seconds`
29. `expires_utc`

**External-specific** (entity_kind = "external")
30. `external_ref`
31. `external_system`
32. `resolver_hint`

**Module/process mapping**
34. `module_id`
35. `module_id_source`
36. `module_id_override`
37. `process_id`
38. `process_step_id`
39. `process_step_role`

**Classification**
40. `role_code`
41. `type_code`
42. `function_code_1`
43. `function_code_2`
44. `function_code_3`
45. `entrypoint_flag`
46. `short_description`

**Provenance**
47. `first_seen_utc`
48. `last_seen_utc`
49. `scan_id`
50. `source_entity_id`
51. `supersedes_entity_id`

### Edge Columns (12) - when record_kind = "edge"

52. `edge_id`
53. `source_entity_id`
54. `target_entity_id`
55. `rel_type` *(MUST be uppercase)*
56. `directionality`
57. `confidence`
58. `evidence_method`
59. `evidence_locator`
60. `evidence_snippet`
61. `observed_utc`
62. `tool_version`
63. `edge_flags`

### Generator Columns (17) - when record_kind = "generator"

64. `generator_id`
65. `generator_name`
66. `generator_version`
67. `output_kind`
68. `output_path`
69. `output_path_pattern`
70. `declared_dependencies`
71. `input_filters`
72. `sort_rule_id`
73. `sort_keys`
74. `template_ref_entity_id`
75. `validator_id`
76. `validation_rules`
77. `last_build_utc`
78. `source_registry_hash`
79. `source_registry_scan_id`
80. `output_hash`
81. `build_report_entity_id`

---

## 7. Migration from Current System

### Phase 1: Transform ID_REGISTRY.json → Unified Registry

```python
def migrate_to_unified_registry(current_registry_path, output_path):
    """
    Migrate current ID_REGISTRY.json to unified SSOT registry.
    
    Transforms:
    - allocations → entity records (entity_kind=file)
    - Adds record_kind discriminator
    - Adds all superset columns (null where not applicable)
    """
    current = load_json(current_registry_path)
    
    unified = {
        "meta": {
            "document_id": "REG-UNIFIED-SSOT-720066-001",
            "registry_name": "UNIFIED_SSOT_REGISTRY",
            "version": "2.0.0",
            "status": "active",
            "last_updated_utc": datetime.utcnow().isoformat() + "Z",
            "authoritative": True,
            "description": "Single source of truth for all entities, relationships, and generators",
            "migrated_from": "ID_REGISTRY.json v1.0",
            "legacy_scope": current.get("scope")
        },
        "counters": transform_counters(current["counters"]),
        "records": []
    }
    
    # Transform each allocation to entity record
    record_id_counter = 1
    for alloc in current["allocations"]:
        entity_record = {
            # Core fields (all records)
            "record_kind": "entity",
            "record_id": f"REC-{record_id_counter:06d}",
            "status": alloc["status"],
            "created_utc": alloc["allocated_at"],
            "updated_utc": alloc["allocated_at"],
            "created_by": alloc.get("allocated_by", "unknown"),
            "updated_by": alloc.get("allocated_by", "unknown"),
            "notes": None,
            "tags": [],
            
            # Entity fields
            "entity_id": alloc["id"],
            "entity_kind": "file",
            
            # File-specific fields
            "doc_id": alloc["id"],
            "filename": os.path.basename(alloc["file_path"]),
            "extension": os.path.splitext(alloc["file_path"])[1],
            "relative_path": alloc["file_path"],
            "absolute_path": None,
            "directory_path": os.path.dirname(alloc["file_path"]) or ".",
            "size_bytes": None,
            "mtime_utc": None,
            "sha256": None,
            "content_type": None,
            
            # Module/process mapping (null for now)
            "module_id": None,
            "module_id_source": None,
            "module_id_override": None,
            "process_id": None,
            "process_step_id": None,
            "process_step_role": None,
            
            # Classification
            "role_code": None,
            "type_code": alloc.get("metadata", {}).get("type_code"),
            "function_code_1": None,
            "function_code_2": None,
            "function_code_3": None,
            "entrypoint_flag": False,
            "short_description": None,
            
            # Provenance
            "first_seen_utc": alloc["allocated_at"],
            "last_seen_utc": alloc["allocated_at"],
            "scan_id": None,
            "source_entity_id": None,
            "supersedes_entity_id": None,
            
            # Asset-specific (null for file entities)
            "asset_id": None,
            "asset_family": None,
            "asset_version": None,
            "canonical_path": None,
            
            # Transient-specific (null for file entities)
            "transient_id": None,
            "transient_type": None,
            "ttl_seconds": None,
            "expires_utc": None,
            
            # External-specific (null for file entities)
            "external_ref": None,
            "external_system": None,
            "resolver_hint": None,
            
            # Edge-specific (null for entity records)
            "edge_id": None,
            "source_entity_id": None,
            "target_entity_id": None,
            "rel_type": None,
            "directionality": None,
            "confidence": None,
            "evidence_method": None,
            "evidence_locator": None,
            "evidence_snippet": None,
            "observed_utc": None,
            "tool_version": None,
            "edge_flags": None,
            
            # Generator-specific (null for entity records)
            "generator_id": None,
            "generator_name": None,
            "generator_version": None,
            "output_kind": None,
            "output_path": None,
            "output_path_pattern": None,
            "declared_dependencies": None,
            "input_filters": None,
            "sort_rule_id": None,
            "sort_keys": None,
            "template_ref_entity_id": None,
            "validator_id": None,
            "validation_rules": None,
            "last_build_utc": None,
            "source_registry_hash": None,
            "source_registry_scan_id": None,
            "output_hash": None,
            "build_report_entity_id": None
        }
        
        unified["records"].append(entity_record)
        record_id_counter += 1
    
    save_json(output_path, unified)
    return unified
```

---

## 8. Query Interface

### Unified Query API

```python
class UnifiedRegistry:
    """Single interface to query all record types"""
    
    def __init__(self, registry_path):
        self.registry = load_json(registry_path)
        self._build_indexes()
    
    def _build_indexes(self):
        """Build in-memory indexes for fast lookups"""
        self.entities_by_id = {}
        self.edges_by_source = defaultdict(list)
        self.edges_by_target = defaultdict(list)
        self.generators_by_id = {}
        
        for record in self.registry["records"]:
            kind = record["record_kind"]
            
            if kind == "entity":
                self.entities_by_id[record["entity_id"]] = record
            elif kind == "edge":
                self.edges_by_source[record["source_entity_id"]].append(record)
                self.edges_by_target[record["target_entity_id"]].append(record)
            elif kind == "generator":
                self.generators_by_id[record["generator_id"]] = record
    
    def find_entity(self, entity_id):
        """Find entity by ID"""
        return self.entities_by_id.get(entity_id)
    
    def find_entities(self, entity_kind=None, status=None, **filters):
        """Find entities matching filters"""
        results = []
        for record in self.registry["records"]:
            if record["record_kind"] != "entity":
                continue
            if entity_kind and record["entity_kind"] != entity_kind:
                continue
            if status and record["status"] != status:
                continue
            
            # Apply additional filters
            match = True
            for key, value in filters.items():
                if record.get(key) != value:
                    match = False
                    break
            
            if match:
                results.append(record)
        
        return results
    
    def get_relationships(self, entity_id, rel_type=None, direction="both"):
        """Get relationships for entity"""
        edges = []
        
        if direction in ("both", "outbound"):
            edges += self.edges_by_source.get(entity_id, [])
        
        if direction in ("both", "inbound"):
            edges += self.edges_by_target.get(entity_id, [])
        
        if rel_type:
            edges = [e for e in edges if e["rel_type"] == rel_type]
        
        return edges
    
    def get_dependencies(self, entity_id, recursive=False):
        """Get dependency tree"""
        deps = []
        edges = self.get_relationships(entity_id, direction="outbound")
        
        for edge in edges:
            if edge["rel_type"] in ["DEPENDS_ON", "IMPORTS", "USES_SCHEMA", "USES_TEMPLATE"]:
                target_id = edge["target_entity_id"]
                deps.append(target_id)
                
                if recursive:
                    deps += self.get_dependencies(target_id, recursive=True)
        
        return list(set(deps))  # dedupe
    
    def find_files_by_module(self, module_id):
        """Find all files in a module"""
        return self.find_entities(
            entity_kind="file",
            status="active",
            module_id=module_id
        )
    
    def add_entity(self, entity_kind, **fields):
        """Add new entity record"""
        record_id = self._allocate_record_id()
        entity_id = self._allocate_entity_id(entity_kind)
        
        record = self._create_entity_record(record_id, entity_id, entity_kind, fields)
        self.registry["records"].append(record)
        self._update_index("entity", record)
        
        return entity_id
    
    def add_edge(self, source_id, target_id, rel_type, confidence, evidence):
        """Add new edge record"""
        record_id = self._allocate_record_id()
        edge_id = self._allocate_edge_id()
        
        record = self._create_edge_record(record_id, edge_id, source_id, target_id, rel_type, confidence, evidence)
        self.registry["records"].append(record)
        self._update_index("edge", record)
        
        return edge_id
```

---

## 9. SQLite Backend (Optional but Recommended)

### Schema

```sql
CREATE TABLE unified_registry (
    -- Core (all records)
    record_id TEXT PRIMARY KEY,
    record_kind TEXT NOT NULL CHECK(record_kind IN ('entity', 'edge', 'generator')),
    status TEXT NOT NULL CHECK(status IN ('active', 'deprecated', 'quarantined', 'archived', 'deleted', 'closed', 'running', 'pending', 'failed')),
    created_utc TEXT NOT NULL,
    updated_utc TEXT NOT NULL,
    created_by TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    notes TEXT,
    tags TEXT, -- JSON array
    
    -- Entity fields (nullable)
    entity_id TEXT UNIQUE,
    entity_kind TEXT CHECK(entity_kind IN ('file', 'asset', 'transient', 'external', 'module', 'directory', 'process', 'other')),
    doc_id TEXT,
    filename TEXT,
    extension TEXT,
    relative_path TEXT,
    absolute_path TEXT,
    directory_path TEXT,
    size_bytes INTEGER,
    mtime_utc TEXT,
    sha256 TEXT,
    content_type TEXT,
    asset_id TEXT,
    asset_family TEXT,
    asset_version TEXT,
    canonical_path TEXT,
    transient_id TEXT,
    transient_type TEXT,
    ttl_seconds INTEGER,
    expires_utc TEXT,
    external_ref TEXT,
    external_system TEXT,
    resolver_hint TEXT,
    module_id TEXT,
    module_id_source TEXT,
    module_id_override TEXT,
    process_id TEXT,
    process_step_id TEXT,
    process_step_role TEXT,
    role_code TEXT,
    type_code TEXT,
    function_code_1 TEXT,
    function_code_2 TEXT,
    function_code_3 TEXT,
    entrypoint_flag BOOLEAN,
    short_description TEXT,
    first_seen_utc TEXT,
    last_seen_utc TEXT,
    scan_id TEXT,
    source_entity_id TEXT,
    supersedes_entity_id TEXT,
    
    -- Edge fields (nullable)
    edge_id TEXT UNIQUE,
    source_entity_id_edge TEXT, -- separate from entity.source_entity_id
    target_entity_id_edge TEXT,
    rel_type TEXT,
    directionality TEXT CHECK(directionality IN ('directed', 'undirected')),
    confidence REAL CHECK(confidence BETWEEN 0.0 AND 1.0),
    evidence_method TEXT,
    evidence_locator TEXT,
    evidence_snippet TEXT,
    observed_utc TEXT,
    tool_version TEXT,
    edge_flags TEXT, -- JSON array
    
    -- Generator fields (nullable)
    generator_id TEXT UNIQUE,
    generator_name TEXT,
    generator_version TEXT,
    output_kind TEXT,
    output_path TEXT,
    output_path_pattern TEXT,
    declared_dependencies TEXT, -- JSON array
    input_filters TEXT, -- JSON object
    sort_rule_id TEXT,
    sort_keys TEXT, -- JSON array
    template_ref_entity_id TEXT,
    validator_id TEXT,
    validation_rules TEXT, -- JSON object
    last_build_utc TEXT,
    source_registry_hash TEXT,
    source_registry_scan_id TEXT,
    output_hash TEXT,
    build_report_entity_id TEXT,
    
    -- Constraints
    CHECK (
        (record_kind = 'entity' AND entity_id IS NOT NULL) OR
        (record_kind = 'edge' AND edge_id IS NOT NULL) OR
        (record_kind = 'generator' AND generator_id IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_record_kind ON unified_registry(record_kind);
CREATE INDEX idx_entity_id ON unified_registry(entity_id);
CREATE INDEX idx_entity_kind ON unified_registry(entity_kind);
CREATE INDEX idx_edge_source ON unified_registry(source_entity_id_edge);
CREATE INDEX idx_edge_target ON unified_registry(target_entity_id_edge);
CREATE INDEX idx_doc_id ON unified_registry(doc_id);
CREATE INDEX idx_module_id ON unified_registry(module_id);
CREATE INDEX idx_status ON unified_registry(status);

-- Foreign key constraints (enforced at application level for JSON, at DB level for SQLite)
-- source_entity_id_edge REFERENCES unified_registry(entity_id)
-- target_entity_id_edge REFERENCES unified_registry(entity_id)
```

---

## 10. Validation Rules

### Referential Integrity

```python
def validate_unified_registry(registry):
    """Validate single SSOT registry"""
    errors = []
    
    # Build entity ID index
    entity_ids = {
        r["entity_id"] 
        for r in registry["records"] 
        if r["record_kind"] == "entity"
    }
    
    # Validate edges reference valid entities
    for record in registry["records"]:
        if record["record_kind"] == "edge":
            if record["source_entity_id"] not in entity_ids:
                errors.append(f"Edge {record['edge_id']}: source_entity_id {record['source_entity_id']} not found")
            if record["target_entity_id"] not in entity_ids:
                errors.append(f"Edge {record['edge_id']}: target_entity_id {record['target_entity_id']} not found")
            if not (0.0 <= record["confidence"] <= 1.0):
                errors.append(f"Edge {record['edge_id']}: confidence {record['confidence']} out of range")
    
    # Validate generators reference valid entities
    for record in registry["records"]:
        if record["record_kind"] == "generator":
            template_id = record.get("template_ref_entity_id")
            if template_id and template_id not in entity_ids:
                errors.append(f"Generator {record['generator_id']}: template_ref_entity_id {template_id} not found")
    
    return errors
```

---

## 11. Migration Script

**File**: `migrate_to_unified_registry.py`

```python
#!/usr/bin/env python3
"""
Complete migration: ID_REGISTRY.json → UNIFIED_SSOT_REGISTRY.json

Usage:
    python migrate_to_unified_registry.py --input registry/ID_REGISTRY.json --output registry/UNIFIED_SSOT_REGISTRY.json --validate
"""

import json
import os
from datetime import datetime

def migrate_to_unified_registry(input_path, output_path):
    """Full migration to single SSOT registry"""
    
    print(f"Loading current registry: {input_path}")
    current = load_json(input_path)
    
    print(f"Creating unified SSOT registry structure...")
    unified = create_unified_structure(current)
    
    print(f"Transforming {len(current['allocations'])} allocations to entity records...")
    transform_allocations_to_entities(current, unified)
    
    print(f"Saving unified registry: {output_path}")
    save_json(output_path, unified)
    
    print("✅ Migration complete!")
    return unified

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate to single unified SSOT registry")
    parser.add_argument("--input", default="registry/ID_REGISTRY.json")
    parser.add_argument("--output", default="registry/UNIFIED_SSOT_REGISTRY.json")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--format", choices=["json", "sqlite"], default="json")
    
    args = parser.parse_args()
    
    unified = migrate_to_unified_registry(args.input, args.output)
    
    if args.validate:
        errors = validate_unified_registry(unified)
        if errors:
            print(f"❌ Validation failed: {len(errors)} errors")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ Validation passed")
    
    if args.format == "sqlite":
        print("Converting to SQLite...")
        convert_to_sqlite(args.output, args.output.replace(".json", ".db"))
```

---

## 12. Summary

### What This Achieves

✅ **One physical file** (UNIFIED_SSOT_REGISTRY.json or .db)  
✅ **All entity types** in one place (files, assets, transients, externals)  
✅ **All relationships** in one place (edges with evidence)  
✅ **All generators** in one place (derived artifact tracking)  
✅ **Type-safe** via `record_kind` discriminator  
✅ **Referential integrity** enforced by validation  
✅ **Backward compatible** via migration script  
✅ **Graph queries** via unified API  
✅ **SQLite ready** for production scale  

### File Structure

```
registry/
└── UNIFIED_SSOT_REGISTRY.json  # ONE file for everything
    OR
└── UNIFIED_SSOT_REGISTRY.db    # ONE SQLite database
```

### Next Steps

1. Run `migrate_to_unified_registry.py` on test copy
2. Validate output with `--validate` flag
3. Test queries with UnifiedRegistry class
4. Deploy to production
5. Deprecate old 4-file references

---

**END OF SPECIFICATION**

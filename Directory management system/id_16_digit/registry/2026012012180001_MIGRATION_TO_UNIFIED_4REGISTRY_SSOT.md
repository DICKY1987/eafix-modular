---
doc_id: 2026012012180001
title: Migration Plan - Current Registry to Unified 4-Registry SSOT
date: 2026-01-20T12:18:00Z
status: IMPLEMENTATION_READY
classification: MIGRATION_SPECIFICATION
author: System Architecture - Registry Unification
version: 1.0
references:
  - C:\Users\richg\ALL_AI\DOC-GUIDE-REGISTRY-SYSTEM-COMPLETE-001__SYSTEM_REGISTRY_COMPLETE_GUIDE.json
  - C:\Users\richg\ALL_AI\REGISTRY_A_FILE_ID.json
  - C:\Users\richg\ALL_AI\REGISTRY_B_ASSET_ID.json
  - C:\Users\richg\ALL_AI\REGISTRY_C_TRANSIENT_ID.json
  - C:\Users\richg\ALL_AI\REGISTRY_D_EDGE_RELATION.json
---

# Migration Plan: Current Registry → Unified 4-Registry SSOT

## Executive Summary

**Current State**: Single-registry system tracking file identities only (`ID_REGISTRY.json`)  
**Target State**: Unified 4-registry SSOT with type-discriminated records  
**Migration Strategy**: Incremental, non-breaking, phased rollout  
**Timeline**: 8 weeks (4 phases × 2 weeks each)

### Critical Insight

Your current `ID_REGISTRY.json` is **already Registry A** (FILE_ID_REGISTRY) in disguise. This migration will:
1. **Formalize** Registry A with complete schema compliance
2. **Add** Registries B (assets), C (transients), D (edges) as new subsystems
3. **Preserve** all existing allocations and audit logs
4. **Enable** graph relationships, asset management, and runtime tracking

---

## Current vs Target Schema Comparison

### Current ID_REGISTRY.json Structure
```json
{
  "schema_version": "1.0",
  "scope": "260119",
  "counters": {
    "NS_TYPE_SCOPE": {
      "current": N,
      "allocated": N,
      "reserved": []
    }
  },
  "allocations": [
    {
      "id": "16-digit",
      "file_path": "...",
      "allocated_at": "...",
      "allocated_by": "...",
      "status": "active",
      "metadata": {...}
    }
  ]
}
```

### Target REGISTRY_A_FILE_ID.json Structure
```json
{
  "meta": {
    "document_id": "REG-A-FILE-ID-001",
    "registry_name": "FILE_ID_REGISTRY",
    "registry_class": "file_id",
    "version": "2.0.0",
    "status": "active",
    "last_updated_utc": "...",
    "authoritative": true
  },
  "counters": { /* same as current */ },
  "entries": [
    {
      "filename": "extracted",
      "doc_id": "same as current 'id'",
      "id_kind": "doc_id",
      "current_relative_path": "same as current 'file_path'",
      "current_directory_path": "derived",
      "extension": "derived",
      "status": "same as current",
      "registry_created_utc": "same as 'allocated_at'",
      "links": [],  // NEW: relationship hints
      "origin": null,  // NEW: provenance
      "owning_module_id": null,  // NEW: module mapping
      "role": null,  // NEW: classification
      "imports": [],  // NEW: dependency tracking
      "exports": []  // NEW: symbol tracking
    }
  ]
}
```

---

## Phase 1: Registry A Formalization (Weeks 1-2)

### Goal
Transform current `ID_REGISTRY.json` into fully compliant `REGISTRY_A_FILE_ID.json` without breaking existing tools.

### Changes Required

#### 1.1 Add Registry Metadata Block
**Current**: Top-level keys `schema_version`, `scope`, `counters`, `allocations`  
**Target**: Wrapped in proper metadata structure

**Migration Script**: `migrate_phase1_add_metadata.py`
```python
def migrate_to_registry_a(current_registry_path, output_path):
    """Phase 1: Add Registry A metadata wrapper"""
    current = load_json(current_registry_path)
    
    target = {
        "meta": {
            "document_id": "REG-A-FILE-ID-720066-001",
            "registry_name": "FILE_ID_REGISTRY",
            "registry_class": "file_id",
            "version": "2.0.0",
            "status": "active",
            "last_updated_utc": datetime.utcnow().isoformat() + "Z",
            "authoritative": True,
            "description": "Authoritative registry for file-backed identities (16-digit doc_id system)",
            "legacy_scope": current.get("scope"),  # Preserve for audit
            "migrated_from": "ID_REGISTRY.json v1.0",
            "migration_date": datetime.utcnow().isoformat() + "Z"
        },
        "schema": REGISTRY_A_SCHEMA,  # Full schema from spec
        "counters": current["counters"],  # Preserve counters
        "entries": []  # Will populate next
    }
    
    # Transform allocations → entries
    for alloc in current["allocations"]:
        entry = transform_allocation_to_entry(alloc)
        target["entries"].append(entry)
    
    save_json(output_path, target)
    return target
```

#### 1.2 Transform Allocation Records → Entry Records
**Current allocation**:
```json
{
  "id": "0199900001260118",
  "file_path": "0199900001260118_.aider.chat.history.md",
  "allocated_at": "2026-01-19T03:54:44.299192",
  "allocated_by": "import_from_scan",
  "status": "active",
  "metadata": {
    "type_code": "01",
    "ns_code": "999",
    "legacy_id": true
  }
}
```

**Target entry**:
```json
{
  "filename": ".aider.chat.history.md",
  "doc_id": "0199900001260118",
  "id_kind": "doc_id",
  "current_relative_path": "0199900001260118_.aider.chat.history.md",
  "current_directory_path": ".",
  "extension": ".md",
  "status": "active",
  "registry_created_utc": "2026-01-19T03:54:44.299192",
  "registry_updated_utc": "2026-01-19T03:54:44.299192",
  
  // NEW FIELDS (initially null/empty for existing records)
  "links": [],
  "origin": {
    "origin_kind": "imported",
    "origin_ref_id": null,
    "origin_tool_id": "import_from_scan",
    "origin_event_id": null,
    "created_utc": "2026-01-19T03:54:44.299192"
  },
  "owning_module_id": null,
  "owning_subsystem": null,
  "maintainer": null,
  "role": null,
  "imports": [],
  "exports": [],
  "entrypoints": [],
  
  // LEGACY METADATA (preserve for audit)
  "legacy_metadata": {
    "type_code": "01",
    "ns_code": "999",
    "legacy_id": true
  }
}
```

#### 1.3 Field Mapping Table

| Current Field | Target Field | Transformation | Status |
|---------------|--------------|----------------|--------|
| `id` | `doc_id` | Direct copy | ✅ EXACT |
| `file_path` | `current_relative_path` | Direct copy | ✅ EXACT |
| `allocated_at` | `registry_created_utc` | Direct copy | ✅ EXACT |
| `allocated_by` | `origin.origin_tool_id` | Embed in origin object | 🔄 RESTRUCTURE |
| `status` | `status` | Direct copy | ✅ EXACT |
| `metadata.*` | `legacy_metadata` | Move to subobject | 🔄 RESTRUCTURE |
| N/A | `filename` | Extract from `file_path` | 🆕 DERIVE |
| N/A | `id_kind` | Constant: `"doc_id"` | 🆕 CONSTANT |
| N/A | `current_directory_path` | Extract dirname from path | 🆕 DERIVE |
| N/A | `extension` | Extract from filename | 🆕 DERIVE |
| N/A | `links` | Empty array | 🆕 NEW |
| N/A | `origin` | Build from metadata | 🆕 NEW |
| N/A | `imports`, `exports`, `role` | Empty/null (populate later) | 🆕 NEW |

#### 1.4 Validation Rules (Phase 1)

**Must Pass**:
- ✅ All current `id` values preserved as `doc_id`
- ✅ All current `file_path` values preserved in `current_relative_path`
- ✅ Counter state exactly preserved
- ✅ Audit log references still valid
- ✅ New schema validates against `REGISTRY_A_FILE_ID.json` spec

**Migration Validator**: `validate_phase1_migration.py`
```python
def validate_phase1(old_path, new_path):
    old = load_json(old_path)
    new = load_json(new_path)
    
    assert len(old["allocations"]) == len(new["entries"])
    
    for old_alloc in old["allocations"]:
        old_id = old_alloc["id"]
        new_entry = find_entry_by_doc_id(new["entries"], old_id)
        assert new_entry is not None, f"Missing entry for {old_id}"
        assert new_entry["doc_id"] == old_id
        assert new_entry["current_relative_path"] == old_alloc["file_path"]
        assert new_entry["status"] == old_alloc["status"]
    
    print("✅ Phase 1 migration validated")
```

#### 1.5 Backward Compatibility Adapter

**File**: `registry_adapter.py` (temporary, removed after full migration)
```python
class RegistryAdapter:
    """Provides v1.0 API access to v2.0 registry for legacy tools"""
    
    def __init__(self, registry_a_path):
        self.registry_a = load_json(registry_a_path)
    
    def get_allocation_by_id(self, doc_id):
        """Legacy API: return allocation-style record"""
        entry = self.find_entry(doc_id)
        if not entry:
            return None
        
        # Transform back to v1.0 format
        return {
            "id": entry["doc_id"],
            "file_path": entry["current_relative_path"],
            "allocated_at": entry["registry_created_utc"],
            "allocated_by": entry.get("origin", {}).get("origin_tool_id", "unknown"),
            "status": entry["status"],
            "metadata": entry.get("legacy_metadata", {})
        }
```

### Deliverables (Phase 1)

- [ ] `REGISTRY_A_FILE_ID.json` (migrated from ID_REGISTRY.json)
- [ ] `migrate_phase1_add_metadata.py` (migration script)
- [ ] `validate_phase1_migration.py` (validation script)
- [ ] `registry_adapter.py` (backward compat layer)
- [ ] Phase 1 migration report (CSV of transformations)
- [ ] Updated scanner to write to Registry A format

**Success Criteria**:
- All existing IDs preserved
- Existing tools still work via adapter
- New tools can use Registry A directly
- Audit log still references correct IDs

---

## Phase 2: Registry D (Edge Relationships) (Weeks 3-4)

### Goal
Add relationship tracking registry to enable graph queries and evidence-based linking.

### New Registry Structure

**File**: `REGISTRY_D_EDGE_RELATION.json`
```json
{
  "meta": {
    "document_id": "REG-D-EDGE-RELATION-720066-001",
    "registry_name": "EDGE_RELATION_REGISTRY",
    "registry_class": "relationship_graph",
    "version": "1.0.0",
    "status": "active",
    "last_updated_utc": "...",
    "authoritative": true
  },
  "counters": {
    "edge_id_counter": {
      "current": 0,
      "allocated": 0,
      "reserved": []
    }
  },
  "entries": []
}
```

### Edge Record Schema

**Example edge**:
```json
{
  "rel_id": "EDGE-20260120-000001",
  "source_kind": "file",
  "source_id": "0199900001260118",
  "source_path": "0199900001260118_.aider.chat.history.md",
  "target_kind": "file",
  "target_id": "2099900005260118",
  "target_path": "2099900005260118_eafix_cli.py",
  "rel_type": "DOCUMENTS",
  "confidence": 0.95,
  "evidence": {
    "method": "markdown_link_parse",
    "locator": "line:42",
    "snippet": "See [eafix_cli](2099900005260118_eafix_cli.py)",
    "observed_utc": "2026-01-20T12:00:00Z",
    "tool_version": "scanner_v2.0"
  },
  "flags": [],
  "created_utc": "2026-01-20T12:00:00Z",
  "last_verified_utc": "2026-01-20T12:00:00Z"
}
```

### Relationship Types (Initial Set)

| rel_type | Description | Example |
|----------|-------------|---------|
| `IMPORTS` | File imports module | Python import statement |
| `DOCUMENTS` | Docs describe target | README references file |
| `TESTS` | Test file tests target | test_*.py → *.py |
| `USES_SCHEMA` | Uses validation schema | Config uses schema file |
| `GENERATED_FROM` | Generated from source | Derived artifact |
| `DEPENDS_ON` | Dependency relationship | Makefile dependency |
| `DUPLICATES` | Duplicate content | Same functionality |
| `REFERENCES_FILE` | Generic reference | Any file mention |

### Phase 2 Implementation

#### 2.1 Edge Scanner Tool
**File**: `scan_relationships.py`
```python
def scan_file_relationships(registry_a_path, output_path):
    """Scan all files in Registry A for relationships"""
    registry_a = load_json(registry_a_path)
    edges = []
    
    for entry in registry_a["entries"]:
        doc_id = entry["doc_id"]
        file_path = entry["current_relative_path"]
        extension = entry["extension"]
        
        if extension == ".py":
            edges += scan_python_imports(doc_id, file_path)
        elif extension == ".md":
            edges += scan_markdown_links(doc_id, file_path)
        elif extension == ".yaml" or extension == ".yml":
            edges += scan_yaml_references(doc_id, file_path)
    
    registry_d = create_registry_d_structure(edges)
    save_json(output_path, registry_d)
```

#### 2.2 Bidirectional Link Sync
**File**: `sync_registry_links.py`
```python
def sync_links_to_registry_a(registry_a_path, registry_d_path):
    """Copy edges from Registry D to Registry A as link hints"""
    registry_a = load_json(registry_a_path)
    registry_d = load_json(registry_d_path)
    
    # Build index: doc_id → edges
    edges_by_source = defaultdict(list)
    for edge in registry_d["entries"]:
        if edge["source_kind"] == "file":
            edges_by_source[edge["source_id"]].append(edge)
    
    # Update Registry A entries with link hints
    for entry in registry_a["entries"]:
        doc_id = entry["doc_id"]
        edges = edges_by_source.get(doc_id, [])
        
        entry["links"] = [
            {
                "rel_type": e["rel_type"],
                "target_kind": e["target_kind"],
                "target_id": e["target_id"],
                "confidence": e["confidence"],
                "evidence": e["evidence"],
                "last_verified_utc": e["last_verified_utc"]
            }
            for e in edges
        ]
    
    save_json(registry_a_path, registry_a)
```

### Graph Query Examples

**Query 1: Find all files that import target**
```python
def find_importers(registry_d, target_doc_id):
    return [
        e for e in registry_d["entries"]
        if e["rel_type"] == "IMPORTS"
        and e["target_id"] == target_doc_id
    ]
```

**Query 2: Find circular dependencies**
```python
def find_circular_deps(registry_d):
    graph = build_graph(registry_d)
    return detect_cycles(graph)
```

### Deliverables (Phase 2)

- [ ] `REGISTRY_D_EDGE_RELATION.json` (new registry)
- [ ] `scan_relationships.py` (edge detector)
- [ ] `sync_registry_links.py` (bidirectional sync)
- [ ] `query_graph.py` (graph query utilities)
- [ ] Edge coverage report (% of files with edges)
- [ ] Relationship visualization tool

**Success Criteria**:
- Registry D contains edges for all file relationships
- Registry A entries have `links[]` populated
- Graph queries work (imports, tests, docs)
- Circular dependencies detected

---

## Phase 3: Registry B (Asset IDs) + Registry C (Transient IDs) (Weeks 5-6)

### Goal
Add asset and transient ID registries to complete the 4-registry SSOT.

### Registry B: ASSET_ID_REGISTRY

**Purpose**: Track canonical assets (schemas, templates, configs, etc.)

**File**: `REGISTRY_B_ASSET_ID.json`
```json
{
  "meta": {
    "document_id": "REG-B-ASSET-ID-720066-001",
    "registry_name": "ASSET_ID_REGISTRY",
    "registry_class": "asset_id",
    "version": "1.0.0",
    "status": "active"
  },
  "counters": {
    "SCHEMA": {"current": 0},
    "TEMPLATE": {"current": 0},
    "CONFIG": {"current": 0}
  },
  "entries": []
}
```

**Asset Entry Example**:
```json
{
  "asset_id": "SCHEMA-000001",
  "asset_type": "schema",
  "canonical_relative_path": "contracts/schemas/json/registry_a.schema.json",
  "status": "active",
  "registry_created_utc": "2026-01-20T12:00:00Z",
  "version": "1.0.0",
  "description": "Registry A validation schema",
  "implements_doc_ids": [],
  "consumed_by_doc_ids": ["2026011822590001"],  // scanner script
  "depends_on_asset_ids": []
}
```

### Registry C: TRANSIENT_ID_REGISTRY

**Purpose**: Track runtime and logical IDs (runs, events, scans, etc.)

**File**: `REGISTRY_C_TRANSIENT_ID.json`
```json
{
  "meta": {
    "document_id": "REG-C-TRANSIENT-ID-720066-001",
    "registry_name": "TRANSIENT_ID_REGISTRY",
    "registry_class": "non_file_id",
    "version": "1.0.0",
    "status": "active"
  },
  "counters": {
    "RUN": {"current_date": "20260120", "seq": 1},
    "TASK": {"current_date": "20260120", "seq": 1}
  },
  "entries": []
}
```

**Transient Entry Example** (scan run):
```json
{
  "id": "RUN-20260120-0001",
  "id_type": "run_id",
  "backing_kind": "transient",
  "origin_ref": "manual_scan",
  "status": "closed",
  "created_utc": "2026-01-20T12:00:00Z",
  "closed_utc": "2026-01-20T12:05:23Z",
  "linked_doc_ids": ["all files scanned"],
  "evidence_paths": ["scan_output/file_scan_20260120_120000.csv"],
  "result_summary": "Scanned 2625 files, 2624 with doc_ids",
  "touches": {
    "created_doc_ids": [],
    "modified_doc_ids": ["2099900072260118"],  // scanner script
    "deleted_doc_ids": []
  }
}
```

### Phase 3 Implementation

#### 3.1 Asset Allocator
**File**: `allocate_asset_id.py`
```python
def allocate_asset_id(asset_type, canonical_path, description):
    """Allocate new asset_id"""
    registry_b = load_json(REGISTRY_B_PATH)
    
    # Get next counter for asset_type
    counter = registry_b["counters"].get(asset_type, {"current": 0})
    next_seq = counter["current"] + 1
    
    asset_id = f"{asset_type.upper()}-{next_seq:06d}"
    
    entry = {
        "asset_id": asset_id,
        "asset_type": asset_type.lower(),
        "canonical_relative_path": canonical_path,
        "status": "active",
        "registry_created_utc": datetime.utcnow().isoformat() + "Z",
        "description": description,
        "version": "1.0.0",
        "implements_doc_ids": [],
        "consumed_by_doc_ids": [],
        "depends_on_asset_ids": []
    }
    
    registry_b["entries"].append(entry)
    registry_b["counters"][asset_type]["current"] = next_seq
    save_json(REGISTRY_B_PATH, registry_b)
    
    return asset_id
```

#### 3.2 Transient ID Allocator
**File**: `allocate_transient_id.py`
```python
def allocate_transient_id(id_type, origin_ref, linked_doc_ids=None):
    """Allocate runtime/transient ID"""
    registry_c = load_json(REGISTRY_C_PATH)
    
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = id_type.replace("_id", "").upper()
    
    # Get/init counter for today
    counter_key = f"{prefix}_{today}"
    counter = registry_c["counters"].get(counter_key, {"seq": 0})
    next_seq = counter["seq"] + 1
    
    transient_id = f"{prefix}-{today}-{next_seq:04d}"
    
    entry = {
        "id": transient_id,
        "id_type": id_type,
        "backing_kind": "transient",
        "origin_ref": origin_ref,
        "status": "open",
        "created_utc": datetime.utcnow().isoformat() + "Z",
        "linked_doc_ids": linked_doc_ids or [],
        "evidence_paths": [],
        "result_summary": null
    }
    
    registry_c["entries"].append(entry)
    registry_c["counters"][counter_key] = {"seq": next_seq}
    save_json(REGISTRY_C_PATH, registry_c)
    
    return transient_id
```

#### 3.3 Cross-Registry Validation
**File**: `validate_cross_registry.py`
```python
def validate_all_registries():
    """Validate referential integrity across all 4 registries"""
    reg_a = load_json(REGISTRY_A_PATH)
    reg_b = load_json(REGISTRY_B_PATH)
    reg_c = load_json(REGISTRY_C_PATH)
    reg_d = load_json(REGISTRY_D_PATH)
    
    # Build ID indexes
    file_ids = {e["doc_id"] for e in reg_a["entries"]}
    asset_ids = {e["asset_id"] for e in reg_b["entries"]}
    transient_ids = {e["id"] for e in reg_c["entries"]}
    
    errors = []
    
    # Validate Registry D edges reference valid entities
    for edge in reg_d["entries"]:
        if edge["source_kind"] == "file" and edge["source_id"] not in file_ids:
            errors.append(f"Edge {edge['rel_id']}: source_id {edge['source_id']} not in Registry A")
        if edge["target_kind"] == "file" and edge["target_id"] not in file_ids:
            errors.append(f"Edge {edge['rel_id']}: target_id {edge['target_id']} not in Registry A")
        if edge["source_kind"] == "asset" and edge["source_id"] not in asset_ids:
            errors.append(f"Edge {edge['rel_id']}: source_id {edge['source_id']} not in Registry B")
        if edge["target_kind"] == "asset" and edge["target_id"] not in asset_ids:
            errors.append(f"Edge {edge['rel_id']}: target_id {edge['target_id']} not in Registry B")
    
    # Validate Registry A references to Registry B
    for entry in reg_a["entries"]:
        if entry.get("generated_from_asset_id"):
            asset_id = entry["generated_from_asset_id"]
            if asset_id not in asset_ids:
                errors.append(f"File {entry['doc_id']}: generated_from_asset_id {asset_id} not in Registry B")
    
    return errors
```

### Deliverables (Phase 3)

- [ ] `REGISTRY_B_ASSET_ID.json` (new registry)
- [ ] `REGISTRY_C_TRANSIENT_ID.json` (new registry)
- [ ] `allocate_asset_id.py` (asset allocator)
- [ ] `allocate_transient_id.py` (transient allocator)
- [ ] `validate_cross_registry.py` (integrity checker)
- [ ] Asset catalog (list of all schemas/templates/configs)
- [ ] Run history report (all scan runs from Registry C)

**Success Criteria**:
- All schemas/templates registered in Registry B
- All scan runs registered in Registry C
- Cross-registry references validated
- No dangling references

---

## Phase 4: Unified Interface + Generator Registry (Weeks 7-8)

### Goal
Provide unified query interface and add generator metadata for derived artifacts.

### Unified Registry Facade

**File**: `unified_registry.py`
```python
class UnifiedRegistry:
    """Single interface to all 4 registries with graph queries"""
    
    def __init__(self, registry_root_path):
        self.reg_a = load_json(f"{registry_root_path}/REGISTRY_A_FILE_ID.json")
        self.reg_b = load_json(f"{registry_root_path}/REGISTRY_B_ASSET_ID.json")
        self.reg_c = load_json(f"{registry_root_path}/REGISTRY_C_TRANSIENT_ID.json")
        self.reg_d = load_json(f"{registry_root_path}/REGISTRY_D_EDGE_RELATION.json")
    
    def find_entity(self, entity_id):
        """Find entity across all registries"""
        # Try Registry A
        for entry in self.reg_a["entries"]:
            if entry["doc_id"] == entity_id:
                return {"kind": "file", "registry": "A", "entry": entry}
        
        # Try Registry B
        for entry in self.reg_b["entries"]:
            if entry["asset_id"] == entity_id:
                return {"kind": "asset", "registry": "B", "entry": entry}
        
        # Try Registry C
        for entry in self.reg_c["entries"]:
            if entry["id"] == entity_id:
                return {"kind": "transient", "registry": "C", "entry": entry}
        
        return None
    
    def get_relationships(self, entity_id, rel_type=None):
        """Get all relationships for entity"""
        edges = [
            e for e in self.reg_d["entries"]
            if e["source_id"] == entity_id or e["target_id"] == entity_id
        ]
        
        if rel_type:
            edges = [e for e in edges if e["rel_type"] == rel_type]
        
        return edges
    
    def get_dependencies(self, entity_id, recursive=False):
        """Get dependency tree"""
        deps = []
        edges = [
            e for e in self.reg_d["entries"]
            if e["source_id"] == entity_id and e["rel_type"] in ["DEPENDS_ON", "IMPORTS", "USES_SCHEMA"]
        ]
        
        for edge in edges:
            deps.append(edge["target_id"])
            if recursive:
                deps += self.get_dependencies(edge["target_id"], recursive=True)
        
        return list(set(deps))  # dedupe
    
    def get_dependents(self, entity_id):
        """Get reverse dependencies"""
        return [
            e["source_id"] for e in self.reg_d["entries"]
            if e["target_id"] == entity_id and e["rel_type"] in ["DEPENDS_ON", "IMPORTS", "USES_SCHEMA"]
        ]
```

### Generator Registry Addition

**Extension to Registry C**:
```json
{
  "id": "GENERATOR-000001-0000",
  "id_type": "generator_id",
  "backing_kind": "registry_only",
  "origin_ref": "deterministic_build_system",
  "status": "active",
  "created_utc": "2026-01-20T12:00:00Z",
  "generator_name": "module_index_builder",
  "output_path_pattern": "modules/{module_id}/INDEX.md",
  "declared_dependencies": ["entity_kind=file", "module_id", "status=active"],
  "input_filters": {
    "entity_kind": "file",
    "status": "active",
    "owning_module_id": "{module_id}"
  },
  "sort_keys": ["role", "type_code", "filename"],
  "sort_rule_id": "sort_by_role_type_filename_v1",
  "last_build_utc": "2026-01-20T12:00:00Z",
  "source_registry_hash": "sha256_of_input_state",
  "output_hash": "sha256_of_output_file"
}
```

### Deliverables (Phase 4)

- [ ] `unified_registry.py` (single interface)
- [ ] `query_tool.py` (CLI for querying)
- [ ] `generator_registry_extension.json` (spec)
- [ ] `register_generator.py` (generator allocator)
- [ ] Full API documentation
- [ ] Migration completion report

**Success Criteria**:
- Single interface queries all 4 registries
- Graph queries work (dependencies, dependents, etc.)
- Generators registered and traceable
- Full documentation complete

---

## Non-Breaking Migration Strategy

### Compatibility During Migration

**Week 1-2 (Phase 1)**:
- Old tools use `ID_REGISTRY.json` via adapter
- New tools use `REGISTRY_A_FILE_ID.json` directly
- Both files kept in sync

**Week 3-4 (Phase 2)**:
- Registry D added (new functionality, no breakage)
- Old tools unaffected
- New tools can use edge queries

**Week 5-6 (Phase 3)**:
- Registries B/C added (new functionality, no breakage)
- Old tools unaffected
- New tools can use asset/transient IDs

**Week 7-8 (Phase 4)**:
- Unified interface available
- Old tools still work via adapter
- Adapter deprecated (6-month sunset warning)

### Rollback Plan

Each phase is independently rollbackable:
- Phase 1: Restore `ID_REGISTRY.json` from backup
- Phase 2: Delete `REGISTRY_D_EDGE_RELATION.json`, clear `links[]` in Registry A
- Phase 3: Delete Registries B/C
- Phase 4: Remove unified interface (registries still work)

---

## File Structure (Post-Migration)

```
Directory management system/id_16_digit/
├── registry/
│   ├── REGISTRY_A_FILE_ID.json         # File identities (current ID_REGISTRY.json)
│   ├── REGISTRY_B_ASSET_ID.json        # Asset definitions (NEW)
│   ├── REGISTRY_C_TRANSIENT_ID.json    # Runtime/logical IDs (NEW)
│   ├── REGISTRY_D_EDGE_RELATION.json   # Relationship graph (NEW)
│   ├── identity_audit_log.jsonl        # Audit log (preserved)
│   └── IDENTITY_CONFIG.yaml            # Config (preserved)
├── core/
│   ├── unified_registry.py             # Single interface (NEW)
│   ├── registry_adapter.py             # Backward compat (TEMP)
│   ├── allocate_file_id.py             # Phase 1 allocator
│   ├── allocate_asset_id.py            # Phase 3 allocator (NEW)
│   ├── allocate_transient_id.py        # Phase 3 allocator (NEW)
│   └── allocate_edge_id.py             # Phase 2 allocator (NEW)
├── validation/
│   ├── validate_registry_a.py          # Registry A validator
│   ├── validate_registry_d.py          # Registry D validator (NEW)
│   └── validate_cross_registry.py      # Integrity checker (NEW)
├── migration/
│   ├── migrate_phase1_add_metadata.py
│   ├── migrate_phase2_scan_edges.py
│   ├── migrate_phase3_register_assets.py
│   └── migrate_phase4_add_generators.py
└── docs/
    ├── REGISTRY_A_SCHEMA.json
    ├── REGISTRY_B_SCHEMA.json
    ├── REGISTRY_C_SCHEMA.json
    ├── REGISTRY_D_SCHEMA.json
    └── UNIFIED_REGISTRY_API.md
```

---

## Testing Strategy

### Phase 1 Tests
```python
def test_phase1_migration():
    """Test Registry A migration"""
    # Load old registry
    old = load_json("registry/ID_REGISTRY.json")
    
    # Run migration
    migrate_to_registry_a("registry/ID_REGISTRY.json", "registry/REGISTRY_A_FILE_ID.json")
    
    # Validate
    new = load_json("registry/REGISTRY_A_FILE_ID.json")
    assert len(old["allocations"]) == len(new["entries"])
    
    # Test adapter
    adapter = RegistryAdapter("registry/REGISTRY_A_FILE_ID.json")
    first_id = old["allocations"][0]["id"]
    assert adapter.get_allocation_by_id(first_id) is not None
```

### Phase 2 Tests
```python
def test_edge_detection():
    """Test relationship scanning"""
    # Create test file with known imports
    test_file_id = "TEST0000000001"
    create_test_file(test_file_id, "import json\nimport yaml")
    
    # Scan relationships
    edges = scan_python_imports(test_file_id, f"{test_file_id}_test.py")
    
    # Validate
    assert any(e["rel_type"] == "IMPORTS" and "json" in e["evidence"]["snippet"] for e in edges)
```

### Integration Tests
```python
def test_unified_registry():
    """Test unified interface"""
    ur = UnifiedRegistry("registry/")
    
    # Test cross-registry query
    file_entry = ur.find_entity("0199900001260118")
    assert file_entry["kind"] == "file"
    
    # Test relationship query
    deps = ur.get_dependencies("2099900005260118")
    assert len(deps) > 0
```

---

## Monitoring and Metrics

### Phase Completion Metrics

**Phase 1**:
- ✅ 100% of IDs migrated to Registry A
- ✅ All existing tools still functional
- ✅ Zero downtime

**Phase 2**:
- ✅ X% of files have edges detected
- ✅ Y relationship types in use
- ✅ Zero invalid edge references

**Phase 3**:
- ✅ N assets registered
- ✅ M transient runs tracked
- ✅ Zero dangling references

**Phase 4**:
- ✅ Unified interface adopted by N tools
- ✅ Old adapter usage < 10%
- ✅ Full API coverage

### Health Checks

**Daily**:
- Registry file sizes (growth rate)
- Cross-registry integrity (referential checks)
- Edge staleness (last_verified_utc)

**Weekly**:
- Coverage metrics (% files with edges)
- Orphan detection (files with no edges)
- Duplicate detection

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-20 | Use 4-registry pattern | Aligns with ALL_AI spec, clear separation of concerns |
| 2026-01-20 | Keep counters in each registry | Local atomicity, no cross-registry counter dependencies |
| 2026-01-20 | Denormalize links[] in Registry A | Fast single-entity lookups without joining Registry D |
| 2026-01-20 | Use JSON not JSONL for registries | Human-readable, easier to edit, single-file atomic writes |
| 2026-01-20 | Keep audit log as JSONL | Append-only nature suits JSONL format |

---

## Summary

**Current System**: File identity only (ID_REGISTRY.json)  
**Target System**: Unified 4-registry SSOT (A/B/C/D)  
**Migration**: 4 phases, 8 weeks, non-breaking  
**Result**: Complete entity tracking, relationship graph, asset management, runtime observability

**Next Steps**:
1. Review this specification
2. Run Phase 1 migration on test branch
3. Validate backward compatibility
4. Roll out Phase 2-4 incrementally
5. Sunset adapter after 6 months

---

**END OF MIGRATION PLAN**

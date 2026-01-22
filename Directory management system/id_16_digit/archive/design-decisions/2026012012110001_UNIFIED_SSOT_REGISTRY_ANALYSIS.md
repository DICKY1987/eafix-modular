---
doc_id: 2026012012110001
title: Unified SSOT Registry Analysis - Current vs Proposed
date: 2026-01-20T12:11:00Z
status: ANALYSIS_COMPLETE
classification: ARCHITECTURAL_COMPARISON
author: System Architecture Review
version: 1.0
---

# Unified SSOT Registry Analysis: Current vs Proposed

## Executive Summary

This document analyzes the current EAFIX identity system registry structure against the proposed unified SSOT (Single Source of Truth) registry design that consolidates the hypothetical "4-registry" pattern (entity registries A/B/C + relationship registry D) into a single, type-discriminated store.

**Key Finding**: The current system already implements a **simplified, file-focused identity registry** that is closer to a unified SSOT than the 4-registry pattern. However, it lacks:
- Relationship/edge tracking with evidence
- Asset/canonical artifact management
- Transient/runtime ID lifecycle
- Generator/derivation metadata
- Multi-entity-kind support

## Current System Architecture

### Physical Structure

**Primary Registry**: `ID_REGISTRY.json`
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
      "id": "16-digit ID",
      "file_path": "path",
      "allocated_at": "timestamp",
      "allocated_by": "source",
      "status": "active|deprecated|...",
      "metadata": {...}
    }
  ]
}
```

**Audit Log**: `identity_audit_log.jsonl` (append-only)
```jsonl
{"event_id": "uuid", "timestamp": "...", "event_type": "...", "data": {...}}
```

### What It Tracks (Current Scope)

| Capability | Status | Notes |
|------------|--------|-------|
| File entity identity | ✅ COMPLETE | 16-digit ID per file |
| Counter management | ✅ COMPLETE | Per NS/TYPE/SCOPE tuple |
| Allocation history | ✅ COMPLETE | Full audit trail |
| Status lifecycle | ✅ COMPLETE | active, deprecated, etc. |
| Type classification | ✅ COMPLETE | Extension-based, 14+ codes |
| Namespace routing | ✅ COMPLETE | Directory-based, 10+ rules |
| Legacy ID migration | ✅ COMPLETE | Scope mismatch tracking |
| **Asset entities** | ❌ MISSING | No canonical asset registry |
| **Transient IDs** | ❌ MISSING | No runtime/session IDs |
| **Relationships** | ❌ MISSING | No edge/link tracking |
| **Evidence** | ❌ MISSING | No confidence/provenance |
| **Generator metadata** | ❌ MISSING | No derivation rules |
| **Module mapping** | ❌ MISSING | No module_id/process_id |

### Current Entity Model

The current system tracks **one entity kind only**:
- `entity_kind = "file"` (implicit)

Each allocation record represents:
- A physical file on disk
- With a 16-digit unique ID
- Classified by type (extension) and namespace (directory)
- With lifecycle status tracking

## Proposed Unified SSOT Registry

### Design Philosophy (from Jan 18 2026 Document)

The proposed design addresses the "4-registry pattern":
- **Registry A**: Concrete file instances (current system ≈ this)
- **Registry B**: Reusable canonical assets (templates, configs)
- **Registry C**: Logical/transient/runtime IDs (sessions, runs, builds)
- **Registry D**: Relationship edges with evidence and confidence

**Unified Approach**: Single registry with `record_kind` discriminator:
- `record_kind = "entity"` (subsumes A/B/C via `entity_kind`)
- `record_kind = "edge"` (replaces D)
- `record_kind = "generator"` (adds derivation metadata)

### Proposed Schema (79 columns superset)

#### Core (all records): 9 columns
```
record_kind, record_id, status, notes, tags,
created_utc, updated_utc, created_by, updated_by
```

#### Entity records (entity_kind ∈ {file, asset, transient, external, module, directory}): 40 columns
```
entity_id, entity_kind,
# File-specific: doc_id, filename, extension, relative_path, sha256, ...
# Asset-specific: asset_id, asset_family, canonical_path, ...
# Transient-specific: transient_id, transient_type, ttl_seconds, ...
# Module mapping: module_id, process_id, role_code, type_code, ...
```

#### Edge records (relationships): 12 columns
```
edge_id, source_entity_id, target_entity_id, rel_type, confidence,
evidence_method, evidence_locator, evidence_snippet, observed_utc,
tool_version, directionality, edge_flags
```

#### Generator records (derivation metadata): 15 columns
```
generator_id, generator_name, output_path, declared_dependencies,
sort_rule_id, validator_id, last_build_utc, source_registry_hash, ...
```

## Gap Analysis: Current → Proposed

### 1. Entity Expansion Gaps

| Feature | Current | Proposed | Impact |
|---------|---------|----------|--------|
| File entities | ✅ Full | ✅ Full + enhanced | Minor extensions needed |
| Asset entities | ❌ None | ✅ Full registry | NEW: canonical artifacts |
| Transient entities | ❌ None | ✅ Full lifecycle | NEW: runtime IDs |
| External refs | ❌ None | ✅ Full resolver | NEW: cross-system links |
| Module mapping | ❌ None | ✅ Full matrix | NEW: process/role/type |

### 2. Relationship Tracking Gaps

| Feature | Current | Proposed | Impact |
|---------|---------|----------|--------|
| Graph edges | ❌ None | ✅ Full graph | NEW: entire subsystem |
| Evidence tracking | ❌ None | ✅ Required | NEW: confidence + provenance |
| Referential integrity | ❌ None | ✅ Enforced | NEW: validation rules |
| Link types | ❌ None | ✅ 10+ types | NEW: typed relationships |

### 3. Derivation/Generator Gaps

| Feature | Current | Proposed | Impact |
|---------|---------|----------|--------|
| Generator registry | ❌ None | ✅ Full spec | NEW: explicit derivations |
| Dependency tracking | ❌ None | ✅ Declared inputs | NEW: SSOT enforcement |
| Build traceability | ❌ None | ✅ Hash + version | NEW: audit trail |
| Sort rules | ❌ None | ✅ Versioned | NEW: determinism guarantee |

### 4. Column-by-Column Mapping

#### Already Present (Enhanced)
```
Current "id"              → Proposed "entity_id" (when entity_kind=file)
Current "file_path"       → Proposed "relative_path"
Current "allocated_at"    → Proposed "created_utc"
Current "allocated_by"    → Proposed "created_by"
Current "status"          → Proposed "status" (same)
Current "metadata.type_code" → Proposed "type_code"
Current "metadata.ns_code"   → Proposed "namespace_routing" (implicit)
```

#### Missing (Need Addition)
```
NEW: record_kind (discriminator)
NEW: entity_kind (file|asset|transient|...)
NEW: doc_id (16-digit, currently in filename prefix)
NEW: filename (currently embedded in file_path)
NEW: extension (derivable, not stored)
NEW: sha256, mtime_utc, size_bytes (file metadata)
NEW: module_id, process_id, role_code (mapping)
NEW: edge_id, source_entity_id, target_entity_id (relationships)
NEW: confidence, evidence_* (provenance)
NEW: generator_id, declared_dependencies (derivation)
```

## Recommended Migration Path

### Phase 1: Extend Current Registry (Weeks 1-2)

**Goal**: Add `record_kind` and `entity_kind` without breaking existing allocations.

**Changes**:
1. Add `record_kind` field to all existing allocations:
   ```json
   "record_kind": "entity"  // default for all current records
   ```
2. Add `entity_kind` field:
   ```json
   "entity_kind": "file"    // all current records are files
   ```
3. Add minimal file metadata:
   ```json
   "filename": "extracted from file_path",
   "extension": "derived from filename",
   "doc_id": "extracted from ID prefix"
   ```

**Validation**: Ensure existing scanner/allocator still works.

### Phase 2: Add Edge Tracking (Weeks 3-4)

**Goal**: Implement relationship registry alongside entity registry.

**Changes**:
1. Add new edge records:
   ```json
   {
     "record_kind": "edge",
     "edge_id": "unique_id",
     "source_entity_id": "0199900001260118",
     "target_entity_id": "2099900005260118",
     "rel_type": "documents",
     "confidence": 0.95,
     "evidence_method": "static_parse",
     "observed_utc": "2026-01-20T12:00:00Z"
   }
   ```
2. Add relationship scanner/detector tools
3. Implement referential integrity checks

**Validation**: Query entity + edges to prove graph structure.

### Phase 3: Add Asset & Transient Entities (Weeks 5-6)

**Goal**: Expand entity kinds beyond files.

**Changes**:
1. Add asset allocator:
   ```json
   {
     "record_kind": "entity",
     "entity_kind": "asset",
     "entity_id": "asset_001",
     "asset_id": "TEMPLATE_001",
     "canonical_path": "templates/base_config.yaml",
     "asset_family": "config_template",
     "status": "active"
   }
   ```
2. Add transient ID manager:
   ```json
   {
     "record_kind": "entity",
     "entity_kind": "transient",
     "entity_id": "run_20260120_001",
     "transient_id": "run_20260120_001",
     "transient_type": "scan_run",
     "ttl_seconds": 86400,
     "expires_utc": "2026-01-21T12:00:00Z"
   }
   ```

**Validation**: Prove asset reuse + transient lifecycle.

### Phase 4: Add Generator Registry (Weeks 7-8)

**Goal**: Make derived artifacts explicit and traceable.

**Changes**:
1. Add generator records:
   ```json
   {
     "record_kind": "generator",
     "generator_id": "module_index_generator",
     "output_path": "modules/{module_id}/INDEX.md",
     "declared_dependencies": ["entity_kind", "module_id", "status"],
     "sort_rule_id": "sort_by_role_type_filename_v1",
     "last_build_utc": "2026-01-20T12:00:00Z",
     "source_registry_hash": "sha256_of_input_state"
   }
   ```
2. Implement generator framework
3. Add deterministic rebuild logic

**Validation**: Prove same inputs → same outputs.

## Benefits of Unified Registry

### 1. Single Source of Truth
- One authoritative registry file
- No split-brain scenarios (A vs B vs C vs D conflicts)
- Atomic transactions across all record types

### 2. Referential Integrity
- Edges reference entities (enforced)
- Generators declare dependencies (enforced)
- No dangling references possible

### 3. Graph Capabilities
- Query "what documents this file?"
- Query "what does this file depend on?"
- Find circular dependencies
- Trace provenance chains

### 4. Evidence-Based Relationships
- Confidence scores (0.0-1.0)
- Source method tracking (parse vs heuristic)
- Locator/snippet for audit
- Tool version for reproducibility

### 5. Derivation Transparency
- Explicit generator declarations
- Input dependency lists
- Build hash tracking
- Deterministic rebuild guarantee

## Risks and Mitigation

### Risk 1: Registry File Size
**Risk**: Single JSON file grows unbounded with edges/generators.
**Mitigation**: 
- Use JSONL format (append-only, line-oriented)
- Implement compaction (archive old records)
- Consider SQLite for production (same schema, better perf)

### Risk 2: Migration Complexity
**Risk**: Existing tools break during schema changes.
**Mitigation**:
- Phased rollout (phase 1 is backward compatible)
- Schema versioning (`schema_version: "2.0"`)
- Provide adapter layer for old code

### Risk 3: Referential Integrity Overhead
**Risk**: Validation slows down allocation.
**Mitigation**:
- Use in-memory index (entity_id → record)
- Lazy validation (check on commit, not per-record)
- Implement read-through cache

### Risk 4: Over-Engineering
**Risk**: Adding features that aren't needed yet.
**Mitigation**:
- Phase 1-2 add value immediately (edges useful now)
- Phase 3-4 optional (assets/generators only if needed)
- Keep current simple allocator for basic cases

## Decision Matrix

| Scenario | Recommendation |
|----------|----------------|
| **File-only identity** | Current system sufficient |
| **Need cross-file relationships** | Add Phase 2 (edges) |
| **Need asset/template tracking** | Add Phase 3 (assets) |
| **Need runtime/session IDs** | Add Phase 3 (transients) |
| **Need module/process mapping** | Add entity columns (module_id, etc.) |
| **Need derived artifacts SSOT** | Add Phase 4 (generators) |
| **Need full graph queries** | Migrate to SQLite backend |

## Comparison Summary

### Current System Strengths
✅ Production-ready file identity  
✅ Monotonic counter allocation  
✅ Audit logging (JSONL)  
✅ Type/namespace classification  
✅ Legacy migration support  
✅ Validation framework  

### Current System Gaps (vs Unified SSOT)
❌ No relationship tracking (edges)  
❌ No evidence/confidence model  
❌ No asset/canonical entity registry  
❌ No transient ID lifecycle  
❌ No generator metadata  
❌ No module/process mapping  
❌ No referential integrity enforcement  

### Proposed System Additions
🆕 Type-discriminated records (`record_kind`)  
🆕 Multi-entity-kind support (`entity_kind`)  
🆕 Graph edges with evidence  
🆕 Confidence scoring (0.0-1.0)  
🆕 Asset/template registry  
🆕 Transient ID lifecycle  
🆕 Generator declarations  
🆕 Dependency tracking  
🆕 Referential integrity  

## Conclusion

The current EAFIX identity system is **well-architected for its current scope** (file-level identity with type/namespace classification). It already follows SSOT principles:
- Single authoritative registry
- Immutable IDs
- Audit logging
- Deterministic allocation

However, it is **narrowly scoped to files only** and lacks:
- Relationship modeling (edges)
- Multi-entity-kind support (assets, transients, etc.)
- Derivation transparency (generators)

The proposed unified SSOT registry would **extend** the current system to support:
1. **Graph relationships** (what depends on what)
2. **Evidence-based links** (confidence + provenance)
3. **Asset management** (canonical templates/configs)
4. **Transient IDs** (runtime sessions/builds)
5. **Generator metadata** (derived artifact rules)

**Recommendation**: 
- **Keep current system** as-is for file identity (it works)
- **Add Phase 2** (edge tracking) if cross-file relationships are needed
- **Defer Phase 3-4** until assets/generators are actually required
- **Consider SQLite backend** only if graph queries become performance bottleneck

The migration is **incremental and non-breaking**: Phase 1 adds `record_kind`/`entity_kind` without changing existing behavior.

---

## Appendix A: Column Mapping Table

| Proposed Column | Current Equivalent | Status | Notes |
|-----------------|-------------------|--------|-------|
| `record_kind` | N/A | NEW | Discriminator (entity/edge/generator) |
| `record_id` | `id` (for entities) | EXISTS | Rename recommended |
| `entity_id` | `id` | EXISTS | Same value |
| `entity_kind` | N/A (implicit "file") | NEW | Must add |
| `doc_id` | Embedded in `id` | DERIVED | Extract from ID prefix |
| `filename` | Embedded in `file_path` | DERIVED | Extract basename |
| `extension` | Embedded in `filename` | DERIVED | Extract suffix |
| `relative_path` | `file_path` | EXISTS | Rename recommended |
| `status` | `status` | EXISTS | Same |
| `created_utc` | `allocated_at` | EXISTS | Rename recommended |
| `created_by` | `allocated_by` | EXISTS | Rename recommended |
| `updated_utc` | N/A | NEW | Add for mutations |
| `updated_by` | N/A | NEW | Add for audit |
| `type_code` | `metadata.type_code` | EXISTS | Promote to top-level |
| `ns_code` | `metadata.ns_code` | EXISTS | Promote to top-level |
| `module_id` | N/A | NEW | Add for mapping |
| `process_id` | N/A | NEW | Add for mapping |
| `role_code` | N/A | NEW | Add for classification |
| `sha256` | N/A | NEW | Add for content hash |
| `edge_id` | N/A | NEW | For edge records |
| `source_entity_id` | N/A | NEW | For edge records |
| `target_entity_id` | N/A | NEW | For edge records |
| `rel_type` | N/A | NEW | For edge records |
| `confidence` | N/A | NEW | For edge records |
| `evidence_method` | N/A | NEW | For edge records |
| `generator_id` | N/A | NEW | For generator records |
| `declared_dependencies` | N/A | NEW | For generator records |

## Appendix B: Schema Evolution Example

### Current Record (v1.0)
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

### Proposed Record (v2.0 - Phase 1)
```json
{
  "record_kind": "entity",
  "entity_kind": "file",
  "entity_id": "0199900001260118",
  "doc_id": "0199900001260118",
  "filename": ".aider.chat.history.md",
  "extension": ".md",
  "relative_path": "0199900001260118_.aider.chat.history.md",
  "type_code": "01",
  "ns_code": "999",
  "status": "active",
  "created_utc": "2026-01-19T03:54:44.299192",
  "created_by": "import_from_scan",
  "updated_utc": "2026-01-19T03:54:44.299192",
  "updated_by": "import_from_scan",
  "metadata": {
    "legacy_id": true
  }
}
```

### With Edge (v2.0 - Phase 2)
```json
{
  "record_kind": "edge",
  "edge_id": "edge_001",
  "source_entity_id": "0199900001260118",
  "target_entity_id": "2099900005260118",
  "rel_type": "references",
  "confidence": 0.95,
  "evidence_method": "static_parse",
  "evidence_locator": "line 42",
  "observed_utc": "2026-01-20T12:00:00Z",
  "tool_version": "scanner_v2.0",
  "directionality": "directed"
}
```

---

**END OF ANALYSIS**

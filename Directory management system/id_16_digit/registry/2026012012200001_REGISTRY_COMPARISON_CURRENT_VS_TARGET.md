# Registry System Comparison: Current vs Target

**Date**: 2026-01-20  
**Status**: Ready for implementation

---

## Quick Reference

| Aspect | Current System | Target System (4-Registry SSOT) |
|--------|---------------|----------------------------------|
| **Registries** | 1 (ID_REGISTRY.json) | 4 (A/B/C/D) |
| **Entity Types** | Files only | Files, Assets, Transients, Externals |
| **Relationships** | None | Full graph with evidence |
| **Evidence** | None | Confidence + provenance |
| **Asset Management** | None | Canonical templates/schemas |
| **Runtime Tracking** | None | Runs, tasks, events |
| **Cross-References** | Manual | Validated integrity |
| **Graph Queries** | Not supported | Full graph API |

---

## What Each Registry Does

### Registry A: FILE_ID_REGISTRY (Your Current System)
**Purpose**: Track every physical file with a 16-digit doc_id  
**Current**: `ID_REGISTRY.json` ← **You already have this!**  
**Status**: ✅ Production-ready (just needs schema alignment)

**Example Entry**:
```json
{
  "doc_id": "0199900001260118",
  "filename": ".aider.chat.history.md",
  "current_relative_path": "0199900001260118_.aider.chat.history.md",
  "extension": ".md",
  "status": "active",
  "links": [/* relationships */],
  "imports": [/* dependencies */],
  "role": "doc"
}
```

### Registry B: ASSET_ID_REGISTRY (NEW)
**Purpose**: Track reusable canonical assets (schemas, templates, configs)  
**Current**: ❌ Does not exist  
**Status**: 🔨 Need to build

**Example Entry**:
```json
{
  "asset_id": "SCHEMA-000001",
  "asset_type": "schema",
  "canonical_relative_path": "contracts/schemas/registry_a.schema.json",
  "status": "active",
  "consumed_by_doc_ids": ["2026011822590001"]  // which files use this
}
```

**Use Case**: Track that `IDENTITY_CONFIG.yaml` is a canonical config template used by the scanner.

### Registry C: TRANSIENT_ID_REGISTRY (NEW)
**Purpose**: Track runtime identifiers (runs, tasks, events, scans)  
**Current**: ❌ Does not exist (runs stored in ad-hoc files)  
**Status**: 🔨 Need to build

**Example Entry**:
```json
{
  "id": "RUN-20260120-0001",
  "id_type": "run_id",
  "backing_kind": "transient",
  "status": "closed",
  "linked_doc_ids": ["all scanned files"],
  "evidence_paths": ["scan_output/file_scan_20260120_120000.csv"],
  "result_summary": "Scanned 2625 files"
}
```

**Use Case**: Track that scanner run `RUN-20260120-0001` scanned all files and produced CSV output.

### Registry D: EDGE_RELATION_REGISTRY (NEW)
**Purpose**: Graph of relationships between all entities (A/B/C)  
**Current**: ❌ Does not exist (relationships stored informally)  
**Status**: 🔨 Need to build

**Example Entry**:
```json
{
  "rel_id": "EDGE-20260120-000001",
  "source_kind": "file",
  "source_id": "0199900001260118",
  "target_kind": "file",
  "target_id": "2099900005260118",
  "rel_type": "DOCUMENTS",
  "confidence": 0.95,
  "evidence": {
    "method": "markdown_link_parse",
    "locator": "line:42",
    "snippet": "See [eafix_cli](2099900005260118_eafix_cli.py)"
  }
}
```

**Use Case**: Track that README documents scanner script with 95% confidence (found markdown link).

---

## Migration Impact Assessment

### What Stays the Same ✅
- Your 16-digit IDs (`0199900001260118`)
- Your filename pattern (`{doc_id}_basename`)
- Your counter system (monotonic sequences)
- Your audit log (JSONL format)
- Your IDENTITY_CONFIG.yaml
- Your existing tools (via adapter layer)

### What Changes 🔄
- `ID_REGISTRY.json` → `REGISTRY_A_FILE_ID.json` (schema alignment)
- Allocations array → Entries array (field renaming)
- `id` field → `doc_id` field (clearer semantics)
- `file_path` → `current_relative_path` (explicit naming)
- Add new fields: `links`, `origin`, `role`, `imports`, `exports`

### What's New 🆕
- Registry B (assets) - track schemas/templates
- Registry C (transients) - track runs/events
- Registry D (edges) - track relationships
- Graph query API - find dependencies, dependents, etc.
- Evidence model - confidence scores + provenance
- Cross-registry validation - enforce referential integrity

---

## Real-World Examples

### Example 1: "What files import this module?"

**Current System**:
```bash
# Manual grep
grep -r "import scanner" --include="*.py"
```

**Target System**:
```python
# Structured query with confidence
ur = UnifiedRegistry()
importers = ur.get_relationships("2026011822590001", rel_type="IMPORTS")
for edge in importers:
    print(f"{edge['source_id']} imports this (confidence: {edge['confidence']})")
```

### Example 2: "Which files were modified in last scan?"

**Current System**:
```bash
# Parse CSV manually or check git log
```

**Target System**:
```python
# Query Registry C
ur = UnifiedRegistry()
last_run = ur.find_latest_transient("run_id")
modified_files = last_run["entry"]["touches"]["modified_doc_ids"]
```

### Example 3: "What files use this schema?"

**Current System**:
```bash
# No structured way to track this
```

**Target System**:
```python
# Query Registry D
ur = UnifiedRegistry()
consumers = ur.get_relationships("SCHEMA-000001", rel_type="USES_SCHEMA")
for edge in consumers:
    print(f"{edge['source_id']} uses this schema")
```

---

## File Layout Comparison

### Current Structure
```
registry/
├── ID_REGISTRY.json           # Single registry (file IDs only)
├── identity_audit_log.jsonl   # Audit log
└── IDENTITY_CONFIG.yaml       # Configuration
```

### Target Structure (Post-Migration)
```
registry/
├── REGISTRY_A_FILE_ID.json         # File identities (enhanced)
├── REGISTRY_B_ASSET_ID.json        # Asset definitions (NEW)
├── REGISTRY_C_TRANSIENT_ID.json    # Runtime IDs (NEW)
├── REGISTRY_D_EDGE_RELATION.json   # Relationship graph (NEW)
├── identity_audit_log.jsonl        # Audit log (same)
└── IDENTITY_CONFIG.yaml            # Configuration (same)
```

---

## Migration Phases Summary

### Phase 1 (Weeks 1-2): Registry A Formalization
**Goal**: Transform ID_REGISTRY.json → REGISTRY_A_FILE_ID.json  
**Impact**: No breaking changes (adapter provides backward compatibility)  
**Deliverable**: Compliant Registry A with all existing IDs preserved

**What You Get**:
- ✅ Schema-compliant file registry
- ✅ New fields: `links`, `origin`, `role`, `imports`, `exports`
- ✅ Backward compatibility via adapter
- ✅ Foundation for graph relationships

### Phase 2 (Weeks 3-4): Registry D (Edges)
**Goal**: Add relationship tracking with evidence  
**Impact**: New functionality, no changes to existing tools  
**Deliverable**: Full relationship graph

**What You Get**:
- ✅ Relationship detection (imports, docs, tests, etc.)
- ✅ Evidence tracking (method, locator, snippet, confidence)
- ✅ Graph queries (dependencies, dependents, cycles)
- ✅ Bidirectional link sync (Registry A ↔ Registry D)

### Phase 3 (Weeks 5-6): Registries B + C
**Goal**: Add asset and transient tracking  
**Impact**: New functionality, no changes to existing tools  
**Deliverable**: Complete 4-registry SSOT

**What You Get**:
- ✅ Asset management (schemas, templates, configs)
- ✅ Runtime tracking (runs, tasks, events)
- ✅ Provenance chains (file → generated from → asset)
- ✅ Run history (all scans tracked)

### Phase 4 (Weeks 7-8): Unified Interface
**Goal**: Single API for all registries + generator metadata  
**Impact**: Simplified usage, deprecate adapter  
**Deliverable**: Production-ready unified system

**What You Get**:
- ✅ Unified query interface (single entry point)
- ✅ Cross-registry queries (one API call)
- ✅ Generator registry (derived artifact tracking)
- ✅ Full documentation + examples

---

## Key Decisions

| Question | Answer | Rationale |
|----------|--------|-----------|
| **Break existing tools?** | No | Adapter layer provides v1.0 API |
| **Change 16-digit IDs?** | No | Preserve exactly as-is |
| **Rewrite scanner?** | No | Small updates to write Registry A format |
| **Manual graph entry?** | No | Auto-detect via scanners |
| **JSON or JSONL?** | JSON for registries, JSONL for audit log | Human-readable registries, append-only log |
| **One big registry or 4 small?** | 4 separate files | Clear separation, independent schema evolution |

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All IDs from ID_REGISTRY.json present in REGISTRY_A_FILE_ID.json
- [ ] Existing scanner works via adapter
- [ ] Validation passes (100% data preservation)
- [ ] Documentation updated

### Phase 2 Complete When:
- [ ] Registry D populated with all detectable relationships
- [ ] Registry A entries have `links[]` synced from Registry D
- [ ] Graph queries work (find importers, dependents, etc.)
- [ ] Edge coverage > 80% for Python files

### Phase 3 Complete When:
- [ ] All schemas/templates registered in Registry B
- [ ] All scan runs registered in Registry C
- [ ] Cross-registry validation passes (no dangling refs)
- [ ] Asset/transient allocators working

### Phase 4 Complete When:
- [ ] UnifiedRegistry class provides single query interface
- [ ] CLI tool can query all registries
- [ ] Generator registry tracks derived artifacts
- [ ] Old adapter usage < 10% (sunset plan in place)

---

## Questions to Answer Before Starting

1. **Scope ID**: Current is `260119`. Target should be `720066` (from spec). Migrate or keep?
   - Recommendation: **Keep `260119`** as legacy_scope, use `720066` in new meta.document_id

2. **Counter Format**: Current is `"NS_TYPE_SCOPE": {...}`. Keep or change to spec format?
   - Recommendation: **Keep as-is** for Phase 1 (works fine, no need to change)

3. **Audit Log**: Keep separate or integrate into registries?
   - Recommendation: **Keep separate** (JSONL format is perfect for append-only)

4. **Backward Compat Duration**: How long to support old API?
   - Recommendation: **6 months** after Phase 4 completion

5. **Registry Location**: Current is `registry/`. Keep or move?
   - Recommendation: **Keep `registry/`** as root for all 4 registries

---

## Next Steps (Immediate)

1. **Review** this comparison and migration plan
2. **Test** migrate_phase1.py on a copy of ID_REGISTRY.json
3. **Validate** that existing scanner still works with adapter
4. **Decide** on migration timeline (can do phases in parallel if desired)
5. **Create** GitHub issue/project board for tracking progress

---

**READY TO START?**

Run this to test Phase 1 migration (dry run, no files written):
```bash
cd "Directory management system/id_16_digit/core"
python migrate_phase1.py --input ../registry/ID_REGISTRY.json --output ../registry/REGISTRY_A_FILE_ID.json --validate --dry-run
```

Then review the output and decide to proceed with actual migration.

---

**END OF COMPARISON**

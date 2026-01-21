---
doc_id: DECISION-2026-01-21-001
title: SCOPE Value and Counter Key Format - Authoritative Decision
date: 2026-01-21T18:59:32Z
status: REQUIRES_DECISION
classification: CRITICAL_SYSTEM_DECISION
---

# SCOPE Value and Counter Key Format - Decision Document

## Executive Summary

**Critical Issue**: The identity system has **two different SCOPE values** and **two different counter key formats** in active use, creating inconsistency across specifications and implementations.

**This document requires immediate decision** to establish the authoritative standard.

---

## Issue 1: SCOPE Value Inconsistency

### Current State Analysis

#### SCOPE: **260118** (Original)
- **Actual File Usage**: 15 files use this scope
- **Found in**:
  - `registry/1199900028260118_ID_REGISTRY.json` (scope: "260118")
  - Most legacy files: `0199900091260118_AGENTS.md`, `0199900095260118_README.md`
  - `SEQ_ALLOCATOR_SPEC.md` examples
  
#### SCOPE: **260119** (Transition)
- **Actual File Usage**: 5 files use this scope
- **Found in**:
  - `registry/ID_REGISTRY.json` (scope: "260119")
  - Newer files: `0199900006260119_CLAUDE.md`, `0199900008260119_MIGRATION_SUMMARY.md`
  - `2099900001260119_apply_ids_to_filenames.py`

#### SCOPE: **720066** (Latest Config)
- **Actual File Usage**: 0 files use this scope in filenames
- **Found in**:
  - `IDENTITY_CONFIG.yaml` (scope: "720066") ✅ **CURRENT CONFIG**
  - `docs/id_16_digit_SYSTEM_DOCUMENTATION.md` (all examples use 720066)
  - Recent documentation

#### SCOPE: **Other values** (33 files)
- Various files with date-based scopes (020001, 600002, etc.)
- Appears to be YYYYMM date format mixed into sequence position

### Evidence Summary

| SCOPE   | Config Files | Registry Files | Actual Filenames | Documentation |
|---------|--------------|----------------|------------------|---------------|
| 260118  | 0            | 1 (legacy)     | 15               | SEQ_ALLOCATOR_SPEC |
| 260119  | 0            | 1 (current)    | 5                | 0 |
| 720066  | 1 ✅         | 0              | 0                | SYSTEM_DOCS |
| Other   | 0            | 0              | 33               | 0 |

### Interpretation

**260118** appears to be:
- Original implementation scope
- Still embedded in 15 legacy filenames
- Used in old registry format

**260119** appears to be:
- Attempted migration (day incremented from 260118 to 260119)
- Used in 5 files
- Current active registry

**720066** appears to be:
- Recent reconfiguration in `IDENTITY_CONFIG.yaml`
- Not yet applied to any actual files
- Documented as current standard

**"Other" values** suggest:
- Possible confusion between SEQ and SCOPE segments
- Files created with incorrect ID format
- Date values (YYYYMM) mistakenly used as SCOPE

---

## Issue 2: Counter Key Format Inconsistency

### Format A: `{SCOPE}:{NS}:{TYPE}` (Spec)

**Defined in**: `SEQ_ALLOCATOR_SPEC.md` line 58

```yaml
counter_key_string = "{SCOPE}:{NS}:{TYPE}"
Example: "260118:200:20"
```

**Documentation Support**:
- `SEQ_ALLOCATOR_SPEC.md` (authoritative contract)
- Examples: `"260118:200:20"` means SCOPE=260118, NS=200, TYPE=20

### Format B: `{NS}_{TYPE}_{SCOPE}` (Implementation)

**Defined in**: `core/2099900074260118_registry_store.py` line 194

```python
def _get_counter_key(self, ns_code: str, type_code: str, scope: str) -> str:
    return f"{ns_code}_{type_code}_{scope}"
```

**Found in**:
- `registry/ID_REGISTRY.json` (actual keys: `"999_01_260119"`, `"999_20_260119"`)
- `2026011822020001_3_PHASE_MODERNIZATION_ROADMAP.md` line 149: "Key format: NS_TYPE_SCOPE"
- `registry/2026012012110001_UNIFIED_SSOT_REGISTRY_ANALYSIS.md`: `"NS_TYPE_SCOPE"`

### Comparison

| Aspect | Format A (Spec) | Format B (Implementation) |
|--------|-----------------|---------------------------|
| **Separator** | Colon `:` | Underscore `_` |
| **Order** | SCOPE:NS:TYPE | NS_TYPE_SCOPE |
| **Used in** | SEQ_ALLOCATOR_SPEC.md | Actual code & registry |
| **Sort Behavior** | Groups by SCOPE first | Groups by NS first |
| **Matches ID Structure** | Yes (TTNNNSSSSSSSSSSS) | No (reverses order) |

### IDENTITY_CONFIG.yaml Specification

Both config files specify:
```yaml
counter_key: [NS, TYPE, SCOPE]
```

**This means**: Counter streams are keyed by the tuple `(NS, TYPE, SCOPE)`.

**It does NOT specify**:
- String separator character
- String representation order

---

## Recommended Decisions

### Decision 1: Authoritative SCOPE Value

**RECOMMENDED**: **720066** (current IDENTITY_CONFIG.yaml value)

**Rationale**:
1. ✅ Currently configured in `IDENTITY_CONFIG.yaml` (authoritative source)
2. ✅ Documented in latest `SYSTEM_DOCUMENTATION.md`
3. ✅ Fresh start - no legacy files to conflict with
4. ❌ Not yet used in any actual filenames (migration needed)

**Alternative**: Revert to **260118** or **260119**
- Maintains compatibility with existing filenames
- But perpetuates legacy configuration

**Migration Impact**:
- If choosing 720066: Need to migrate 20 existing files (260118 + 260119)
- If choosing 260118/260119: Need to update `IDENTITY_CONFIG.yaml` and all docs

### Decision 2: Authoritative Counter Key Format

**RECOMMENDED**: **`{SCOPE}:{NS}:{TYPE}`** (colon separator, SCOPE-first)

**Rationale**:
1. ✅ Matches the ID segment order: TT-NNN-SSSSS-SSSSSS
2. ✅ Defined in authoritative `SEQ_ALLOCATOR_SPEC.md` contract
3. ✅ SCOPE-first grouping supports multi-project scenarios
4. ✅ Colon is standard delimiter for hierarchical keys (e.g., Redis, cache keys)
5. ❌ Requires code change in `registry_store.py` line 194

**Alternative**: Keep **`{NS}_{TYPE}_{SCOPE}`** (underscore, NS-first)
- Maintains compatibility with current `ID_REGISTRY.json`
- But violates the authoritative spec
- NS-first grouping less useful (NS is project-specific anyway)

**Migration Impact**:
- If choosing `SCOPE:NS:TYPE`: Update `registry_store.py`, migrate existing registry keys
- If choosing `NS_TYPE_SCOPE`: Update `SEQ_ALLOCATOR_SPEC.md`, accept spec violation

---

## Decision Matrix

### Option A: SCOPE=720066, Format=`SCOPE:NS:TYPE` ✅ RECOMMENDED
- **Pros**: Clean slate, spec-compliant, future-proof
- **Cons**: Requires migration of 20 files + registry rewrite
- **Effort**: Medium (1-2 days)

### Option B: SCOPE=260118, Format=`NS_TYPE_SCOPE`
- **Pros**: No file migration needed
- **Cons**: Perpetuates legacy, violates spec, maintains inconsistency
- **Effort**: Low (update docs only)

### Option C: SCOPE=260119, Format=`SCOPE:NS:TYPE`
- **Pros**: Minimal file migration (5 files already use 260119)
- **Cons**: 260119 has no documented rationale, still legacy
- **Effort**: Medium

---

## Implementation Checklist

### If Choosing SCOPE=720066 + Format=`SCOPE:NS:TYPE`:

1. **Update Code**:
   - [ ] `core/2099900074260118_registry_store.py` line 194: Change to `f"{scope}:{ns_code}:{type_code}"`
   - [ ] Search all Python files for `f"{ns_code}_{type_code}_{scope}"` pattern

2. **Update Registry**:
   - [ ] Backup `registry/ID_REGISTRY.json`
   - [ ] Convert counter keys: `"999_01_260119"` → `"720066:999:01"`
   - [ ] Update scope field: `"scope": "260119"` → `"scope": "720066"`

3. **Update Documentation**:
   - [ ] `SEQ_ALLOCATOR_SPEC.md`: Update examples to use 720066
   - [ ] `0199900095260118_README.md`: Update scope references
   - [ ] `2026011820600002_QUICK_START_GUIDE.md`: Update scope examples

4. **Migrate Files** (Optional - Phase 3):
   - [ ] 15 files with scope=260118
   - [ ] 5 files with scope=260119
   - [ ] Document migration in audit log

5. **Validation**:
   - [ ] Run scanner with new config
   - [ ] Verify counter key format in output
   - [ ] Test allocation with new format
   - [ ] Run validation suite

---

## Questions Requiring Answer

### Question 1: SCOPE Selection
**What does the 6-digit SCOPE represent?**

Possibilities:
- `260118` = Date 2026-01-18 (project start date)
- `260119` = Date 2026-01-19 (migration date)
- `720066` = Derived value (7+2+0+0+6+6=21, or other encoding)

**Decision Needed**: Choose SCOPE value and document its meaning.

### Question 2: File Migration
**Should existing files be migrated to new SCOPE?**

Options:
- **Yes**: Consistency, all files use same SCOPE
- **No**: Preserve history, SCOPE captures allocation date
- **Partial**: Only migrate files without IDs yet

**Decision Needed**: Migration policy for existing files.

### Question 3: Backward Compatibility
**Should system support reading multiple SCOPE values?**

Options:
- **Yes**: Registry can hold mixed SCOPE values (260118, 260119, 720066)
- **No**: Enforce single SCOPE, reject files with wrong SCOPE

**Decision Needed**: Strict vs. lenient SCOPE validation.

---

## Next Steps

1. **Make Decisions**: Answer the three questions above
2. **Document Authority**: Update this document with final decisions
3. **Execute Migration**: Follow implementation checklist
4. **Update Specs**: Ensure all documentation matches decisions
5. **Create Unified Docs**: Proceed with documentation consolidation framework

---

## Appendix: Counter Key Format Analysis

### Why SCOPE-first matters

**Multi-project scenario**:
```
SCOPE:NS:TYPE ordering:
  720066:100:01  # Project A, docs, markdown
  720066:100:20  # Project A, docs, python
  720066:200:20  # Project A, scripts, python
  880055:100:01  # Project B, docs, markdown
  880055:200:20  # Project B, scripts, python

NS:TYPE:SCOPE ordering:
  100:01:720066  # Docs markdown, Project A
  100:01:880055  # Docs markdown, Project B  ← separated
  100:20:720066  # Docs python, Project A
  200:20:720066  # Scripts python, Project A
  200:20:880055  # Scripts python, Project B
```

SCOPE-first keeps all counters for one project together, which is semantically correct since NS codes are project-specific.

---

**Status**: AWAITING DECISION  
**Decision Maker**: Project Lead / Technical Architect  
**Deadline**: Before documentation consolidation begins  
**Document Version**: 1.0  
**Last Updated**: 2026-01-21T18:59:32Z

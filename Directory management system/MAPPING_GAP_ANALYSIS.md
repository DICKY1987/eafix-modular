# Mapping Architecture Gap - Comprehensive Analysis

**Date:** 2026-01-22  
**Status:** CRITICAL_GAP_IDENTIFIED  
**Priority:** HIGH  

---

## Executive Summary

Your system has a **critical 3-way mapping gap** preventing deterministic traceability between:
- **Files** (implementation code)
- **Process Steps** (trading workflow stages)
- **Modules** (logical boundaries with contracts)

**Current State:** You have the **architecture specification** but lack the **implementation**.

---

## 1. What You Have (Infrastructure)

### ✅ Process Document
**Location:** `Directory management system\DOD_modules_contracts\updated_trading_process_aligned.yaml`

**Contents:**
- 24+ process steps defined
- Each step has `module_id` (owner)
- Input/output contracts declared
- Validation and failure policies

**Example Step:**
```yaml
- number: 16
  name: "Serialize and send to MT4 adapter"
  module_id: B1_MT4_ADAPTER_TRANSPORT
  responsible: "transport_service.py"
  input: "RoutedOrderIntent + ResolvedConfig"
  output: "BrokerOrderEnvelope + AdapterAck"
```

**What's Missing:** No `entrypoint_files` field linking steps to actual code files.

---

### ✅ Mapping Reference Specification
**Location:** `Directory management system\DOD_modules_contracts\# Process↔Module and File↔Step Mapp.txt`

**Defines:**
- Canonical sources of truth (Module Registry, Process Doc, File Registry)
- Contract boundaries and ownership rules
- File roles (entrypoint/library/schema/config/test)
- Derivation algorithms for step→entrypoint mapping
- Validation rules to prevent drift

**Critical Rule:**
> "Files map to steps only if: `file.module_id == step.module_id` AND `file.role == entrypoint`"

**This is the SPECIFICATION but not the IMPLEMENTATION.**

---

### ✅ ID Registry System
**Location:** `Directory management system\id_16_digit\registry\ID_REGISTRY.json`

**Contains:**
- File identity allocation (16-digit IDs)
- File paths and timestamps
- Type codes (01=markdown, 20=python, etc.)
- Namespace codes (999=uncategorized, 100=docs, etc.)

**Current Schema:**
```json
{
  "id": "0199900001260118",
  "file_path": "path/to/file.py",
  "allocated_at": "2026-01-19T03:54:44Z",
  "metadata": {
    "type_code": "20",
    "ns_code": "999"
  }
}
```

**What's Missing:**
- ❌ No `module_id` field
- ❌ No `role` field (entrypoint/library/schema/config)
- ❌ No `step_refs` field
- ❌ No `contracts_produced` or `contracts_consumed`

---

### ✅ Unified SSOT Registry Spec (v2.1)
**Location:** `Directory management system\id_16_digit\registry\2026012012410001_SINGLE_UNIFIED_SSOT_REGISTRY_SPEC.md`

**Defines 80 columns including:**
- Entity fields (doc_id, relative_path, module_id, role)
- Edge fields (relationships between entities)
- Generator fields (derivation metadata)

**Status:** Specification exists but **not implemented** in actual registry files.

---

## 2. The Critical Gaps

### Gap 1: File Registry Missing Module Ownership
**Impact:** Cannot answer "Which module owns file X?"

**Current State:**
```json
// ID_REGISTRY.json (actual)
{
  "id": "2099900001260119",
  "file_path": "src/transport_service.py",
  "metadata": {"type_code": "20", "ns_code": "999"}
}
```

**Required State:**
```json
// FILE_REGISTRY.json (needed)
{
  "doc_id": "2099900001260119",
  "relative_path": "src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py",
  "module_id": "B1_MT4_ADAPTER_TRANSPORT",
  "role": "entrypoint",
  "step_refs": [16]
}
```

---

### Gap 2: Process Document Missing Entrypoint Files
**Impact:** Cannot answer "Which file executes Step 16?"

**Current State:**
```yaml
- number: 16
  module_id: B1_MT4_ADAPTER_TRANSPORT
  responsible: "transport_service.py"  # Just a label, not a link
```

**Required State:**
```yaml
- number: 16
  module_id: B1_MT4_ADAPTER_TRANSPORT
  entrypoint_files:
    - src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py
  responsible: "transport_service.py"
```

---

### Gap 3: Module Registry Missing
**Impact:** Cannot derive file ownership from path patterns.

**Per mapping spec, should contain:**
```yaml
module_id: B1_MT4_ADAPTER_TRANSPORT
out_types:
  - BrokerOrderEnvelope
  - AdapterAck
required_files:
  - pattern: "src/B1_MT4_ADAPTER_TRANSPORT/**/*.py"
    role: entrypoint
  - pattern: "tests/B1_MT4_ADAPTER_TRANSPORT/**/*.py"
    role: test
```

**Status:** Referenced in process YAML (`MODULE_REGISTRY_version 1.0.0.txt`) but location unknown.

---

## 3. Consequences of the Gap

### 🚫 Cannot Trace Execution Flow
- Question: "Step 16 failed. Which file do I debug?"
- Current: Manual search through `responsible` labels
- Needed: Direct link to entrypoint file(s)

### 🚫 Cannot Validate Module Boundaries
- Question: "Does file X violate module ownership?"
- Current: No enforcement possible
- Needed: File registry with `module_id` validated against module boundaries

### 🚫 Cannot Generate Dependency Graphs
- Question: "What does Step 16 depend on?"
- Current: Only contract names (strings)
- Needed: File→Step→Module→Contract chain

### 🚫 Cannot Enforce Contract Compliance
- Question: "Does transport_service.py actually produce BrokerOrderEnvelope?"
- Current: Trust documentation
- Needed: `contracts_produced` field validated against module registry

### 🚫 AI Navigation Broken
- AI agents cannot deterministically navigate from:
  - Process step → Implementation file
  - Implementation file → Process steps it implements
  - Module → All files owned

---

## 4. The Solution (Phased Implementation)

### Phase 1: Extend File Registry Schema ⚡ PRIORITY
**Action:** Migrate `ID_REGISTRY.json` → `FILE_REGISTRY.json`

**Add Fields:**
```yaml
# Required (deterministic)
module_id: string          # From module ownership rules
role: enum                 # entrypoint|library|schema|config|test|doc|data
relative_path: string      # Normalized path from repo root

# Optional (high-value)
step_refs: [int]          # Only for role=entrypoint
contracts_produced: [str] # For discovery/validation
contracts_consumed: [str] # For dependency analysis
```

**Migration Script Required:**
1. Read current `ID_REGISTRY.json`
2. For each file:
   - Apply module ownership rules (from MODULE_REGISTRY patterns)
   - Infer `role` from path and extension
   - Leave `step_refs` blank initially
3. Write to new `FILE_REGISTRY.json`
4. Validate against UNIFIED_SSOT_REGISTRY_SPEC v2.1

---

### Phase 2: Add Entrypoint Files to Process Doc
**Action:** Update `updated_trading_process_aligned.yaml`

**For Each Step:**
1. Identify step's `module_id`
2. Query FILE_REGISTRY for files where:
   - `module_id` matches step
   - `role == entrypoint`
   - File name matches `responsible` label
3. Add `entrypoint_files: [...]` to step

**Example Transformation:**
```yaml
# Before
- number: 16
  module_id: B1_MT4_ADAPTER_TRANSPORT
  responsible: "transport_service.py"

# After
- number: 16
  module_id: B1_MT4_ADAPTER_TRANSPORT
  responsible: "transport_service.py"
  entrypoint_files:
    - src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py
```

---

### Phase 3: Populate step_refs in File Registry (Bidirectional Link)
**Action:** Derive from process document

**Algorithm:**
```python
for step in process_steps:
    for entrypoint_file in step.entrypoint_files:
        file_record = file_registry.get(entrypoint_file)
        file_record.step_refs.append(step.number)
```

**Validation Rule:**
```python
# Bidirectional consistency check
for file in file_registry where role == 'entrypoint':
    for step_num in file.step_refs:
        step = process_doc.steps[step_num]
        assert file.path in step.entrypoint_files
        assert file.module_id == step.module_id
```

---

### Phase 4: Locate/Create Module Registry
**Action:** Find or create `MODULE_REGISTRY_version 1.0.0.txt`

**Minimum Required Per Module:**
```yaml
module_id: B1_MT4_ADAPTER_TRANSPORT
module_type: adapter
status: active
owner: richg

contract_boundaries:
  in_types:
    - RoutedOrderIntent
    - ResolvedConfig
  out_types:
    - BrokerOrderEnvelope
    - AdapterAck

required_files:
  - role: entrypoint
    pattern: "src/B1_MT4_ADAPTER_TRANSPORT/**/*.py"
    description: "Adapter service implementations"
  - role: test
    pattern: "tests/B1_MT4_ADAPTER_TRANSPORT/**/*.py"
    description: "Module test suite"
  - role: schema
    pattern: "schemas/B1_MT4_ADAPTER_TRANSPORT/**/*.json"
```

**Usage:** Validate that FILE_REGISTRY assignments match module boundaries.

---

## 5. Validation Rules to Implement

### Rule 1: Module Ownership Completeness
```python
def validate_module_ownership():
    for file in file_registry:
        assert file.module_id is not None, f"File {file.path} has no module"
        assert file.module_id in module_registry, f"Unknown module {file.module_id}"
```

### Rule 2: Entrypoint-Step Alignment
```python
def validate_entrypoint_step_mapping():
    for file in file_registry where role == 'entrypoint':
        if file.step_refs:
            for step_num in file.step_refs:
                step = process_doc.get_step(step_num)
                assert file.module_id == step.module_id, \
                    f"File {file.path} module mismatch with step {step_num}"
```

### Rule 3: Role Restrictions
```python
def validate_role_restrictions():
    for file in file_registry:
        if file.step_refs:
            assert file.role == 'entrypoint', \
                f"Non-entrypoint file {file.path} has step_refs"
```

### Rule 4: Contract Boundary Compliance
```python
def validate_contract_boundaries():
    for step in process_doc.steps:
        module = module_registry.get(step.module_id)
        assert step.output in module.out_types, \
            f"Step {step.number} output {step.output} not in module contract"
```

---

## 6. Benefits After Implementation

### ✅ Deterministic Traceability
```
Query: "What implements Step 16?"
Answer: src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py

Query: "What steps does transport_service.py implement?"
Answer: Step 16 (Serialize and send to MT4 adapter)

Query: "What module owns transport_service.py?"
Answer: B1_MT4_ADAPTER_TRANSPORT

Query: "What contracts does B1_MT4_ADAPTER_TRANSPORT produce?"
Answer: BrokerOrderEnvelope, AdapterAck
```

### ✅ Automated Dependency Analysis
- Generate complete dependency graphs
- Detect circular dependencies
- Identify orphaned files (no module ownership)

### ✅ AI-Assisted Navigation
- AI can deterministically navigate codebase
- Generate accurate refactoring suggestions
- Understand blast radius of changes

### ✅ Governance Enforcement
- Pre-commit hooks validate file→module ownership
- CI checks contract boundary compliance
- Prevent drift between docs and implementation

---

## 7. Migration Risks and Mitigations

### Risk 1: Incorrect Module Assignments
**Mitigation:** 
- Start with conservative fallback (module_id: UNCATEGORIZED)
- Manual review of critical entrypoint assignments
- Gradual refinement based on path patterns

### Risk 2: Breaking Existing Tools
**Mitigation:**
- Keep ID_REGISTRY.json for backward compatibility
- Introduce FILE_REGISTRY.json as additive
- Deprecation period with dual-read support

### Risk 3: Incomplete Module Registry
**Mitigation:**
- Allow module_id: PENDING for new files
- Periodic audit reports of unmapped files
- Incremental module definition (start with critical path)

---

## 8. Implementation Checklist

### Week 1: Schema Extension
- [ ] Define FILE_REGISTRY.json schema (extend SSOT v2.1)
- [ ] Create migration script: ID_REGISTRY → FILE_REGISTRY
- [ ] Add module_id, role, step_refs fields
- [ ] Validate against JSON schema

### Week 2: Process Document Enhancement
- [ ] Locate MODULE_REGISTRY_version 1.0.0.txt
- [ ] Parse module boundaries and required_files patterns
- [ ] Derive entrypoint_files for all 24 steps
- [ ] Update updated_trading_process_aligned.yaml

### Week 3: Bidirectional Linking
- [ ] Populate step_refs in FILE_REGISTRY
- [ ] Implement validation rules (4 rules above)
- [ ] Generate validation report
- [ ] Fix any inconsistencies

### Week 4: Automation & Tooling
- [ ] Create file scanner with module assignment
- [ ] Pre-commit hook: validate file→module ownership
- [ ] CI job: validate step→entrypoint consistency
- [ ] Generate traceability matrix report

---

## 9. Success Metrics

### Quantitative
- 100% of Python files have module_id assigned
- 100% of entrypoint files have step_refs populated
- 100% of process steps have entrypoint_files
- 0 validation errors in CI

### Qualitative
- AI can answer "what implements step X?" in <1s
- Developers can trace execution path deterministically
- Module boundary violations caught pre-commit
- Refactoring blast radius calculable

---

## 10. Related Documents

### Architecture Specs
- `Directory management system\DOD_modules_contracts\# Process↔Module and File↔Step Mapp.txt`
- `Directory management system\id_16_digit\registry\2026012012410001_SINGLE_UNIFIED_SSOT_REGISTRY_SPEC.md`
- `Directory management system\id_16_digit\registry\2026012014470004_REGISTRY_V2.1_QUICK_REFERENCE.md`

### Current State
- `Directory management system\DOD_modules_contracts\updated_trading_process_aligned.yaml`
- `Directory management system\id_16_digit\registry\ID_REGISTRY.json`

### Gap Analysis
- `C:\Users\richg\Downloads\ChatGPT-File Process Mapping Analysis.md` (original discovery)
- This document (comprehensive solution)

---

## 11. Conclusion

You have a **well-architected specification** but a **critical implementation gap**:

**Gap:** The 3-way mapping (Files ↔ Steps ↔ Modules) is **documented but not implemented**.

**Impact:** 
- Cannot trace execution deterministically
- Cannot enforce module boundaries
- Cannot generate dependency graphs
- AI navigation broken

**Solution:** 4-phase migration:
1. Extend FILE_REGISTRY with module_id + role + step_refs
2. Add entrypoint_files to process document
3. Populate bidirectional links
4. Implement validation automation

**Timeline:** 4 weeks with proper planning and testing.

**Priority:** HIGH - This is foundational infrastructure for governance, traceability, and AI-assisted development.

---

**Next Step:** Locate MODULE_REGISTRY_version 1.0.0.txt and validate it contains the required fields for module boundary enforcement.

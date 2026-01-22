# Mapping Gap - Complete Implementation Plan

**Created:** 2026-01-22  
**Status:** READY_FOR_EXECUTION  
**Priority:** CRITICAL  
**Owner:** System Architecture Team  
**Estimated Duration:** 6 weeks (with parallel workstreams)

---

## Executive Summary

This plan addresses the critical 3-way mapping gap (Files ↔ Steps ↔ Modules) through a structured 6-week implementation with 3 parallel workstreams and comprehensive validation.

**Success Criteria:**
- 100% files have module ownership
- 100% process steps linked to entrypoint files
- Zero mapping validation errors
- Complete traceability chain operational

---

## Pre-Flight Checklist (Week 0 - Before Starting)

### Preparation Tasks
- [ ] **Backup all registries:** ID_REGISTRY.json, process YAML, all docs
- [ ] **Set up version control branch:** `feature/mapping-gap-fix`
- [ ] **Create test environment:** Copy of production data for safe testing
- [ ] **Document current state:** Snapshot of all 24 process steps and file counts
- [ ] **Identify stakeholders:** Get signoff on schema changes

### Prerequisites Validation
- [ ] Verify `updated_trading_process_aligned.yaml` is accessible
- [ ] Confirm `ID_REGISTRY.json` schema version and record count
- [ ] Locate or confirm missing `MODULE_REGISTRY_version 1.0.0.txt`
- [ ] Review mapping reference: `# Process↔Module and File↔Step Mapp.txt`
- [ ] Check SSOT Registry Spec v2.1 for schema compliance

### Tooling Setup
- [ ] Install JSON Schema validator
- [ ] Set up Python environment with required libraries
- [ ] Configure pre-commit hooks framework
- [ ] Prepare CI/CD pipeline for validation jobs

**Duration:** 3-5 days  
**Blockers:** None (can proceed immediately after backups)

---

## Phase 1: Module Registry Creation (Week 1-2)

### Objective
Create the missing `MODULE_REGISTRY_version 1.0.0.txt` with all 24+ modules defined.

### Tasks

#### 1.1 Extract Module List from Process Document
**Script:** `extract_modules_from_process.py`

```python
# Input: updated_trading_process_aligned.yaml
# Output: module_list.json

modules = {
    "F1_CONFIG_PREFERENCES",
    "F3_CLOCK_SCHEDULER",
    "D2_CALENDAR_SOURCE_ADAPTER",
    "D3_CALENDAR_NORMALIZER",
    "F2_EVENT_LOG",
    "D4_CALENDAR_TRIGGER_BUILDER",
    "D1_MARKET_FEED_ADAPTER",
    "C1_BAR_BUILDER",
    "C2_INDICATOR_ENGINE",
    "C3_FEATURE_PACKAGER",
    "S1_SIGNAL_ENGINE",
    "S2_INTENT_BUILDER",
    "R1_RISK_EVALUATOR",
    "R2_ORDER_INTENT_COMPILER",
    "O1_ORDER_ROUTER",
    "B1_MT4_ADAPTER_TRANSPORT",
    "B2_MT4_EA_EXECUTOR",
    "B3_EXEC_EVENT_NORMALIZER",
    "O2_OMS_STATE_MACHINE",
    "O3_TRADE_CLOSE_CLASSIFIER",
    "E1_OUTCOME_BUCKETIZER",
    "E2_PROXIMITY_EVALUATOR",
    "E3_MATRIX_LOOKUP",
    "E4_REENTRY_DECISION_BUILDER",
    # ... etc
}
```

**Deliverable:** `modules_extracted.json`  
**Validation:** Count must match unique module_id values in process YAML  
**Time:** 2 hours

---

#### 1.2 Define Module Contracts from Process Steps
**Script:** `derive_module_contracts.py`

For each module, extract contracts from all steps where `step.module_id == module_id`:

```python
# Example for B1_MT4_ADAPTER_TRANSPORT
{
  "module_id": "B1_MT4_ADAPTER_TRANSPORT",
  "in_types": ["RoutedOrderIntent", "ResolvedConfig"],
  "out_types": ["BrokerOrderEnvelope", "AdapterAck"],
  "steps_owned": [16]
}
```

**Algorithm:**
1. Group steps by module_id
2. Collect all `input` contracts → in_types
3. Collect all `output` contracts → out_types
4. Deduplicate and sort

**Deliverable:** `module_contracts_derived.json`  
**Validation:** Every step's output must be in its module's out_types  
**Time:** 4 hours

---

#### 1.3 Map Modules to File Patterns
**Script:** `infer_module_file_patterns.py`

**Strategy:**
1. Scan filesystem for existing patterns
2. Map to module structure (if exists)
3. Define default patterns if structure missing

```python
# Pattern inference rules
patterns = {
    "entrypoint": f"src/{module_id}/**/*.py",
    "library": f"src/{module_id}/lib/**/*.py",
    "test": f"tests/{module_id}/**/*.py",
    "schema": f"schemas/{module_id}/**/*.json",
    "config": f"config/{module_id}/**/*.yaml",
    "doc": f"docs/{module_id}/**/*.md"
}
```

**Deliverable:** `module_file_patterns.json`  
**Validation:** At least one pattern per module  
**Time:** 6 hours

---

#### 1.4 Generate MODULE_REGISTRY File
**Script:** `generate_module_registry.py`

Combine outputs from 1.2 and 1.3:

```yaml
# MODULE_REGISTRY_version 1.0.0.txt
registry_version: "1.0.0"
generated_at: "2026-01-22T12:00:00Z"
source: "Derived from updated_trading_process_aligned.yaml"

modules:
  - module_id: B1_MT4_ADAPTER_TRANSPORT
    module_type: adapter
    status: active
    owner: system
    purpose: "Serialize orders and transport to MT4 EA"
    
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
        description: "Transport service implementations"
      - role: test
        pattern: "tests/B1_MT4_ADAPTER_TRANSPORT/**/*.py"
        description: "Module test suite"
      - role: schema
        pattern: "schemas/B1_MT4_ADAPTER_TRANSPORT/**/*.json"
        description: "Contract schemas"
    
    validation_rules:
      - check: "entrypoint_exists"
        pattern: "src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py"
      - check: "output_contracts_implemented"
        contracts: ["BrokerOrderEnvelope", "AdapterAck"]
  
  # ... repeat for all 24+ modules
```

**Deliverable:** `MODULE_REGISTRY_version 1.0.0.txt`  
**Validation:** YAML parses correctly, all modules from step 1.1 present  
**Time:** 8 hours

---

#### 1.5 Validate Module Registry
**Script:** `validate_module_registry.py`

**Checks:**
- [ ] All modules from process doc are present
- [ ] No duplicate module_ids
- [ ] All contract types are valid strings
- [ ] All file patterns are valid glob syntax
- [ ] Each module has at least one required_files entry

**Deliverable:** `module_registry_validation_report.json`  
**Time:** 2 hours

**Phase 1 Total Time:** 22 hours (~3 days)  
**Phase 1 Deliverables:** MODULE_REGISTRY_version 1.0.0.txt + validation report

---

## Phase 2: File Registry Extension (Week 2-3)

### Objective
Transform ID_REGISTRY.json → FILE_REGISTRY.json with module ownership and roles.

### Tasks

#### 2.1 Design FILE_REGISTRY Schema
**Document:** `FILE_REGISTRY_SCHEMA_v2.1.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "File Registry v2.1",
  "type": "object",
  "properties": {
    "schema_version": {"const": "2.1"},
    "scope": {"type": "string", "pattern": "^\\d{6}$"},
    "generated_at": {"type": "string", "format": "date-time"},
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["doc_id", "relative_path", "module_id", "role"],
        "properties": {
          "doc_id": {"type": "string", "pattern": "^\\d{16}$"},
          "relative_path": {"type": "string"},
          "absolute_path": {"type": "string"},
          "filename": {"type": "string"},
          "extension": {"type": "string"},
          "module_id": {"type": "string"},
          "role": {
            "enum": ["entrypoint", "library", "schema", "config", 
                     "test", "doc", "data", "tooling", "fixture"]
          },
          "step_refs": {
            "type": "array",
            "items": {"type": "integer"}
          },
          "contracts_produced": {
            "type": "array",
            "items": {"type": "string"}
          },
          "contracts_consumed": {
            "type": "array",
            "items": {"type": "string"}
          },
          "type_code": {"type": "string"},
          "ns_code": {"type": "string"},
          "size_bytes": {"type": "integer"},
          "mtime_utc": {"type": "string", "format": "date-time"},
          "sha256": {"type": "string"},
          "status": {"enum": ["active", "deprecated", "archived"]},
          "metadata": {"type": "object"}
        }
      }
    }
  }
}
```

**Deliverable:** `FILE_REGISTRY_SCHEMA_v2.1.json`  
**Time:** 4 hours

---

#### 2.2 Infer Module Ownership for Existing Files
**Script:** `assign_module_ownership.py`

**Algorithm:**
```python
def assign_module_id(file_path, module_registry):
    for module in module_registry.modules:
        for pattern in module.required_files:
            if glob_match(file_path, pattern.pattern):
                return module.module_id, pattern.role
    
    # Fallback: infer from path
    if "src/" in file_path:
        # Extract module from path: src/B1_MT4_ADAPTER_TRANSPORT/file.py
        parts = file_path.split("/")
        if len(parts) >= 2:
            return parts[1], "library"
    
    # Ultimate fallback
    return "UNCATEGORIZED", "library"
```

**Deliverable:** `file_module_assignments.json`  
**Validation:** No files left with null module_id  
**Time:** 6 hours

---

#### 2.3 Infer File Roles
**Script:** `assign_file_roles.py`

**Rules:**
```python
def infer_role(file_path, filename):
    # Explicit paths
    if file_path.startswith("tests/"):
        return "test"
    if file_path.startswith("docs/"):
        return "doc"
    if file_path.startswith("schemas/"):
        return "schema"
    if file_path.startswith("config/"):
        return "config"
    if file_path.startswith("data/"):
        return "data"
    
    # Naming conventions
    if "test_" in filename or "_test" in filename:
        return "test"
    if filename.endswith(".schema.json"):
        return "schema"
    if "config" in filename.lower():
        return "config"
    if filename in ["__init__.py", "setup.py", "main.py", "app.py"]:
        return "entrypoint"
    
    # Extension-based
    if file_path.endswith((".md", ".txt", ".rst")):
        return "doc"
    if file_path.endswith((".json", ".yaml", ".toml")) and "schema" in file_path:
        return "schema"
    
    # Default
    return "library"
```

**Manual Review Required:** Entrypoint files (critical for mapping)  
**Deliverable:** `file_roles_assigned.json`  
**Time:** 8 hours (including manual review)

---

#### 2.4 Migrate ID_REGISTRY → FILE_REGISTRY
**Script:** `migrate_registry.py`

```python
def migrate_record(old_record, module_assignments, role_assignments):
    doc_id = old_record["id"]
    file_path = old_record["file_path"]
    
    module_id, suggested_role = module_assignments.get(file_path)
    final_role = role_assignments.get(file_path, suggested_role)
    
    new_record = {
        "doc_id": doc_id,
        "relative_path": normalize_path(file_path),
        "filename": os.path.basename(file_path),
        "extension": get_extension(file_path),
        "module_id": module_id,
        "role": final_role,
        "step_refs": [],  # Populated in Phase 3
        "contracts_produced": [],  # Populated in Phase 4
        "contracts_consumed": [],  # Populated in Phase 4
        "type_code": old_record["metadata"]["type_code"],
        "ns_code": old_record["metadata"]["ns_code"],
        "status": old_record["status"],
        "allocated_at": old_record["allocated_at"],
        "metadata": old_record["metadata"]
    }
    
    return new_record
```

**Deliverable:** `FILE_REGISTRY.json`  
**Validation:** Record count matches ID_REGISTRY.json  
**Time:** 4 hours

---

#### 2.5 Validate FILE_REGISTRY
**Script:** `validate_file_registry.py`

**Checks:**
- [ ] Schema compliance (JSON Schema validation)
- [ ] All doc_ids are unique
- [ ] All module_ids exist in MODULE_REGISTRY
- [ ] All roles are in allowed enum
- [ ] No null/missing required fields
- [ ] File paths are normalized and valid

**Deliverable:** `file_registry_validation_report.json`  
**Time:** 3 hours

**Phase 2 Total Time:** 25 hours (~3 days)  
**Phase 2 Deliverables:** FILE_REGISTRY.json + schema + validation report

---

## Phase 3: Process Document Enhancement (Week 3-4)

### Objective
Add `entrypoint_files` to all 24 process steps.

### Tasks

#### 3.1 Map Steps to Candidate Entrypoints
**Script:** `derive_step_entrypoints.py`

**Algorithm:**
```python
def find_entrypoints_for_step(step, file_registry, module_registry):
    module_id = step["module_id"]
    responsible = step.get("responsible", "")
    
    # Filter files by module and role
    candidates = [
        f for f in file_registry.files
        if f["module_id"] == module_id and f["role"] == "entrypoint"
    ]
    
    # Rank by filename match with responsible label
    ranked = []
    for candidate in candidates:
        score = 0
        if responsible in candidate["filename"]:
            score += 10
        if candidate["filename"].endswith(".py"):
            score += 5
        if "main" in candidate["filename"] or "service" in candidate["filename"]:
            score += 3
        ranked.append((score, candidate))
    
    ranked.sort(reverse=True)
    
    # Return top candidates
    return [c["relative_path"] for score, c in ranked[:3]]
```

**Deliverable:** `step_entrypoint_candidates.json`  
**Manual Review Required:** Verify top candidate for each step  
**Time:** 6 hours

---

#### 3.2 Manual Review and Correction
**Document:** `step_entrypoint_review.xlsx`

For each step:
- [ ] Review suggested entrypoint
- [ ] Verify file actually implements step logic
- [ ] Add additional entrypoints if needed (max 3 per step)
- [ ] Flag steps with no clear entrypoint for investigation

**Deliverable:** `step_entrypoint_approved.json`  
**Time:** 8 hours (critical manual work)

---

#### 3.3 Update Process YAML
**Script:** `update_process_with_entrypoints.py`

```python
def update_step(step, approved_entrypoints):
    step_num = step["number"]
    entrypoints = approved_entrypoints.get(step_num, [])
    
    if entrypoints:
        step["entrypoint_files"] = entrypoints
    else:
        step["entrypoint_files"] = []
        step["_warning"] = "NO_ENTRYPOINT_FOUND"
    
    return step
```

**Before:**
```yaml
- number: 16
  module_id: B1_MT4_ADAPTER_TRANSPORT
  responsible: "transport_service.py"
  input: "RoutedOrderIntent + ResolvedConfig"
  output: "BrokerOrderEnvelope + AdapterAck"
```

**After:**
```yaml
- number: 16
  module_id: B1_MT4_ADAPTER_TRANSPORT
  responsible: "transport_service.py"
  entrypoint_files:
    - src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py
  input: "RoutedOrderIntent + ResolvedConfig"
  output: "BrokerOrderEnvelope + AdapterAck"
```

**Deliverable:** `updated_trading_process_aligned_v2.yaml`  
**Time:** 3 hours

---

#### 3.4 Validate Process→Entrypoint Mapping
**Script:** `validate_process_entrypoints.py`

**Checks:**
- [ ] All steps have entrypoint_files (or explicit waiver)
- [ ] All entrypoint files exist in FILE_REGISTRY
- [ ] All entrypoint files have role='entrypoint'
- [ ] All entrypoint files belong to step's module
- [ ] File paths are correct and normalized

**Deliverable:** `process_entrypoint_validation_report.json`  
**Time:** 3 hours

**Phase 3 Total Time:** 20 hours (~2.5 days)  
**Phase 3 Deliverables:** Updated process YAML + validation report

---

## Phase 4: Bidirectional Linking (Week 4)

### Objective
Populate `step_refs` in FILE_REGISTRY to create bidirectional links.

### Tasks

#### 4.1 Generate step_refs from Process Document
**Script:** `populate_step_refs.py`

```python
def populate_step_refs(file_registry, process_doc):
    # Clear existing step_refs
    for file in file_registry.files:
        file["step_refs"] = []
    
    # Populate from process
    for step in process_doc.steps:
        step_num = step["number"]
        for entrypoint_path in step.get("entrypoint_files", []):
            file_record = find_file_by_path(file_registry, entrypoint_path)
            if file_record:
                if step_num not in file_record["step_refs"]:
                    file_record["step_refs"].append(step_num)
            else:
                log_error(f"Step {step_num} references missing file: {entrypoint_path}")
    
    # Sort step_refs for determinism
    for file in file_registry.files:
        file["step_refs"].sort()
    
    return file_registry
```

**Deliverable:** `FILE_REGISTRY_v2.json` (with step_refs populated)  
**Time:** 3 hours

---

#### 4.2 Validate Bidirectional Consistency
**Script:** `validate_bidirectional_mapping.py`

**Checks:**
```python
def validate_bidirectional(file_registry, process_doc):
    errors = []
    
    # Forward check: Process → Files
    for step in process_doc.steps:
        step_num = step["number"]
        for entrypoint_path in step.get("entrypoint_files", []):
            file_record = find_file_by_path(file_registry, entrypoint_path)
            if not file_record:
                errors.append(f"Step {step_num} references non-existent file: {entrypoint_path}")
            elif step_num not in file_record.get("step_refs", []):
                errors.append(f"Step {step_num} → {entrypoint_path} missing reverse link")
    
    # Reverse check: Files → Process
    for file in file_registry.files:
        if file["role"] == "entrypoint" and file.get("step_refs"):
            for step_num in file["step_refs"]:
                step = find_step_by_number(process_doc, step_num)
                if not step:
                    errors.append(f"File {file['relative_path']} references non-existent step {step_num}")
                elif file["relative_path"] not in step.get("entrypoint_files", []):
                    errors.append(f"File {file['relative_path']} → Step {step_num} missing forward link")
                elif file["module_id"] != step["module_id"]:
                    errors.append(f"Module mismatch: {file['relative_path']} ({file['module_id']}) vs Step {step_num} ({step['module_id']})")
    
    return errors
```

**Deliverable:** `bidirectional_validation_report.json`  
**Acceptance Criteria:** Zero errors  
**Time:** 4 hours

---

#### 4.3 Generate Traceability Matrix
**Script:** `generate_traceability_matrix.py`

**Output Formats:**
1. **CSV Report:** `traceability_matrix.csv`
   ```csv
   Step,Module,Entrypoint_File,Contracts_In,Contracts_Out
   16,B1_MT4_ADAPTER_TRANSPORT,src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py,RoutedOrderIntent,BrokerOrderEnvelope
   ```

2. **Markdown Report:** `TRACEABILITY_REPORT.md`
   ```markdown
   ## Step 16: Serialize and send to MT4 adapter
   - **Module:** B1_MT4_ADAPTER_TRANSPORT
   - **Entrypoint:** src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py
   - **Inputs:** RoutedOrderIntent, ResolvedConfig
   - **Outputs:** BrokerOrderEnvelope, AdapterAck
   ```

3. **JSON Report:** `traceability_matrix.json`

**Deliverable:** 3 traceability reports  
**Time:** 3 hours

**Phase 4 Total Time:** 10 hours (~1.5 days)  
**Phase 4 Deliverables:** FILE_REGISTRY with step_refs + traceability matrix

---

## Phase 5: Validation Automation (Week 5)

### Objective
Build automated validation tools and integrate into CI/CD.

### Tasks

#### 5.1 Implement Core Validators

**Validator 1: Module Ownership Completeness**
```python
# validators/module_ownership_validator.py

def validate_module_ownership(file_registry, module_registry):
    errors = []
    warnings = []
    
    for file in file_registry.files:
        # Check module_id exists
        if not file.get("module_id"):
            errors.append(f"File {file['relative_path']} has no module_id")
            continue
        
        # Check module_id is valid
        if file["module_id"] not in module_registry.module_ids:
            if file["module_id"] == "UNCATEGORIZED":
                warnings.append(f"File {file['relative_path']} is uncategorized")
            else:
                errors.append(f"File {file['relative_path']} has unknown module {file['module_id']}")
    
    return {
        "check": "module_ownership_completeness",
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "total_files": len(file_registry.files),
            "uncategorized": len([f for f in file_registry.files if f["module_id"] == "UNCATEGORIZED"]),
            "categorized": len([f for f in file_registry.files if f["module_id"] != "UNCATEGORIZED"])
        }
    }
```

**Validator 2: Entrypoint-Step Alignment**
```python
# validators/entrypoint_step_validator.py

def validate_entrypoint_step_mapping(file_registry, process_doc):
    errors = []
    
    for file in file_registry.files:
        if file["role"] != "entrypoint":
            continue
        
        if not file.get("step_refs"):
            # Entrypoint with no steps - might be unused
            continue
        
        for step_num in file["step_refs"]:
            step = find_step_by_number(process_doc, step_num)
            
            if not step:
                errors.append(f"File {file['relative_path']} references non-existent step {step_num}")
                continue
            
            # Check module alignment
            if file["module_id"] != step["module_id"]:
                errors.append(
                    f"Module mismatch: File {file['relative_path']} "
                    f"(module={file['module_id']}) vs Step {step_num} "
                    f"(module={step['module_id']})"
                )
    
    return {
        "check": "entrypoint_step_alignment",
        "passed": len(errors) == 0,
        "errors": errors
    }
```

**Validator 3: Role Restrictions**
```python
# validators/role_validator.py

def validate_role_restrictions(file_registry):
    errors = []
    
    for file in file_registry.files:
        # Only entrypoints should have step_refs
        if file.get("step_refs") and file["role"] != "entrypoint":
            errors.append(
                f"Non-entrypoint file {file['relative_path']} "
                f"(role={file['role']}) has step_refs: {file['step_refs']}"
            )
    
    return {
        "check": "role_restrictions",
        "passed": len(errors) == 0,
        "errors": errors
    }
```

**Validator 4: Contract Boundary Compliance**
```python
# validators/contract_validator.py

def validate_contract_boundaries(process_doc, module_registry):
    errors = []
    warnings = []
    
    for step in process_doc.steps:
        module = module_registry.get_module(step["module_id"])
        
        if not module:
            errors.append(f"Step {step['number']} references unknown module {step['module_id']}")
            continue
        
        # Check outputs
        step_outputs = parse_contracts(step.get("output", ""))
        for output in step_outputs:
            if output not in module["out_types"]:
                errors.append(
                    f"Step {step['number']} output '{output}' not in "
                    f"module {module['module_id']} out_types: {module['out_types']}"
                )
        
        # Check inputs (warning only, as cross-cutting inputs are allowed)
        step_inputs = parse_contracts(step.get("input", ""))
        for input_contract in step_inputs:
            if input_contract not in module["in_types"]:
                warnings.append(
                    f"Step {step['number']} input '{input_contract}' not in "
                    f"module {module['module_id']} in_types: {module['in_types']}"
                )
    
    return {
        "check": "contract_boundary_compliance",
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
```

**Deliverable:** 4 validator modules  
**Time:** 12 hours

---

#### 5.2 Create Master Validation Runner
**Script:** `run_all_validators.py`

```python
#!/usr/bin/env python3
"""
Master validation runner - executes all validators and generates report.
Usage: python run_all_validators.py
"""

import json
from validators import (
    module_ownership_validator,
    entrypoint_step_validator,
    role_validator,
    contract_validator
)

def run_all_validations():
    # Load data
    file_registry = load_json("FILE_REGISTRY.json")
    module_registry = load_yaml("MODULE_REGISTRY_version 1.0.0.txt")
    process_doc = load_yaml("updated_trading_process_aligned.yaml")
    
    # Run validators
    results = []
    
    print("Running Module Ownership Validator...")
    results.append(module_ownership_validator.validate_module_ownership(
        file_registry, module_registry
    ))
    
    print("Running Entrypoint-Step Alignment Validator...")
    results.append(entrypoint_step_validator.validate_entrypoint_step_mapping(
        file_registry, process_doc
    ))
    
    print("Running Role Restrictions Validator...")
    results.append(role_validator.validate_role_restrictions(
        file_registry
    ))
    
    print("Running Contract Boundary Validator...")
    results.append(contract_validator.validate_contract_boundaries(
        process_doc, module_registry
    ))
    
    # Generate summary
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_checks": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "total_errors": sum(len(r.get("errors", [])) for r in results),
        "total_warnings": sum(len(r.get("warnings", [])) for r in results),
        "results": results
    }
    
    # Write report
    with open("validation_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Total Checks: {summary['total_checks']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Total Warnings: {summary['total_warnings']}")
    
    # Exit with error if any checks failed
    if summary['failed'] > 0:
        print("\n❌ VALIDATION FAILED")
        return 1
    else:
        print("\n✅ ALL VALIDATIONS PASSED")
        return 0

if __name__ == "__main__":
    exit(run_all_validations())
```

**Deliverable:** `run_all_validators.py`  
**Time:** 4 hours

---

#### 5.3 Create Pre-Commit Hook
**File:** `.pre-commit-hooks/validate-mapping.sh`

```bash
#!/bin/bash
# Pre-commit hook for mapping validation

echo "🔍 Validating file-step-module mapping..."

python3 run_all_validators.py

if [ $? -ne 0 ]; then
    echo "❌ Mapping validation failed!"
    echo "Please fix errors before committing."
    exit 1
fi

echo "✅ Mapping validation passed"
exit 0
```

**Integration:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-mapping
        name: Validate File-Step-Module Mapping
        entry: .pre-commit-hooks/validate-mapping.sh
        language: system
        pass_filenames: false
        always_run: true
```

**Deliverable:** Pre-commit hook + config  
**Time:** 3 hours

---

#### 5.4 Create CI/CD Validation Job
**File:** `.github/workflows/validate-mapping.yml`

```yaml
name: Validate Mapping

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate-mapping:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install pyyaml jsonschema
      
      - name: Run mapping validators
        run: |
          python run_all_validators.py
      
      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: validation_report.json
      
      - name: Comment PR with results
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('validation_report.json'));
            
            let comment = '## ❌ Mapping Validation Failed\n\n';
            comment += `- **Total Errors:** ${report.total_errors}\n`;
            comment += `- **Total Warnings:** ${report.total_warnings}\n\n`;
            
            if (report.total_errors > 0) {
              comment += '### Errors:\n';
              for (const result of report.results) {
                if (result.errors.length > 0) {
                  comment += `\n**${result.check}:**\n`;
                  for (const error of result.errors) {
                    comment += `- ${error}\n`;
                  }
                }
              }
            }
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

**Deliverable:** CI/CD workflow  
**Time:** 4 hours

**Phase 5 Total Time:** 23 hours (~3 days)  
**Phase 5 Deliverables:** 4 validators + runner + hooks + CI/CD

---

## Phase 6: Documentation & Rollout (Week 6)

### Objective
Document the new system and roll out to production.

### Tasks

#### 6.1 Create User Documentation

**Document 1: Mapping System Overview**
```markdown
# File-Step-Module Mapping System

## Purpose
This system provides deterministic traceability between:
- Implementation files (Python, YAML, JSON, etc.)
- Process steps (trading workflow stages)
- Modules (logical boundaries with contracts)

## Key Concepts

### Module Ownership
Every file belongs to exactly one module. Modules define:
- Contract boundaries (inputs/outputs)
- File ownership patterns (required_files)
- Acceptance tests

### File Roles
- **entrypoint**: Executes a process step
- **library**: Shared code, imported by entrypoints
- **schema**: Contract definitions
- **config**: Configuration files
- **test**: Unit/integration tests
- **doc**: Documentation

### Step-Entrypoint Linking
Only `entrypoint` files can be linked to process steps.
Links are bidirectional and validated automatically.

## Usage

### Query: Which file implements Step X?
```bash
grep -A 3 "^  - number: 16" updated_trading_process_aligned.yaml | grep entrypoint_files
```

### Query: Which steps does file Y implement?
```bash
jq '.files[] | select(.relative_path == "src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py") | .step_refs' FILE_REGISTRY.json
```

### Query: Which module owns file Z?
```bash
jq '.files[] | select(.relative_path == "src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py") | .module_id' FILE_REGISTRY.json
```

## Validation
Run all validators:
```bash
python run_all_validators.py
```
```

**Deliverable:** `MAPPING_SYSTEM_USER_GUIDE.md`  
**Time:** 6 hours

---

**Document 2: Developer Guide**
```markdown
# Developer Guide: Working with the Mapping System

## Adding a New File

1. **Determine Module Ownership**
   - Place file in module-specific directory: `src/{module_id}/`
   - Or manually assign in FILE_REGISTRY.json

2. **Assign Role**
   - If file executes a process step: `role: entrypoint`
   - If imported by other files: `role: library`
   - If defines contracts: `role: schema`

3. **Link to Process Steps (if entrypoint)**
   - Update process YAML: add file to `entrypoint_files`
   - Run validators: `python run_all_validators.py`

## Adding a New Module

1. **Update MODULE_REGISTRY**
   ```yaml
   - module_id: NEW_MODULE_ID
     contract_boundaries:
       in_types: [...]
       out_types: [...]
     required_files:
       - role: entrypoint
         pattern: "src/NEW_MODULE_ID/**/*.py"
   ```

2. **Create Module Structure**
   ```
   src/NEW_MODULE_ID/
   ├── main.py          (entrypoint)
   ├── lib/             (libraries)
   └── README.md
   ```

3. **Run Validators**

## Adding a New Process Step

1. **Update Process YAML**
   ```yaml
   - number: 25
     module_id: NEW_MODULE_ID
     entrypoint_files:
       - src/NEW_MODULE_ID/main.py
     input: "InputContract"
     output: "OutputContract"
   ```

2. **Verify Entrypoint Exists**
   - Check FILE_REGISTRY for entrypoint file
   - Verify `role: entrypoint`

3. **Run Validators**
```

**Deliverable:** `MAPPING_SYSTEM_DEVELOPER_GUIDE.md`  
**Time:** 6 hours

---

#### 6.2 Create Migration Notes
**Document:** `MIGRATION_NOTES.md`

```markdown
# Migration Notes: ID_REGISTRY → FILE_REGISTRY

## Breaking Changes
- Schema version updated: 1.0 → 2.1
- New required fields: `module_id`, `role`
- File renamed: ID_REGISTRY.json → FILE_REGISTRY.json

## Backward Compatibility
- Old ID_REGISTRY.json preserved for 30 days
- Legacy tools can continue reading old format
- New tools read FILE_REGISTRY.json exclusively

## Migration Path
1. All existing files assigned module_id
2. All files assigned role based on path/name inference
3. Manual review of entrypoint assignments completed
4. Bidirectional links validated

## Known Issues
- 47 files in UNCATEGORIZED module (to be reassigned)
- 3 steps have no clear entrypoint (under investigation)

## Rollback Procedure
If critical issues arise:
1. Restore ID_REGISTRY.json from backup
2. Revert process YAML to v1 (no entrypoint_files)
3. Disable pre-commit hooks
4. File incident report
```

**Deliverable:** `MIGRATION_NOTES.md`  
**Time:** 3 hours

---

#### 6.3 Conduct Training Session
**Session:** 2-hour training for team

**Agenda:**
1. Overview of mapping system (15 min)
2. Demo: Querying traceability (20 min)
3. Demo: Adding new files (20 min)
4. Demo: Running validators (15 min)
5. Q&A (30 min)
6. Hands-on exercises (20 min)

**Materials:**
- Slide deck
- Hands-on lab exercises
- Cheat sheet (1-page reference)

**Deliverable:** Training session + materials  
**Time:** 12 hours (prep + delivery)

---

#### 6.4 Production Rollout
**Checklist:**

**Pre-Deployment:**
- [ ] All validators pass with zero errors
- [ ] Backup all registries and process docs
- [ ] Tag release: `v2.1-mapping-system`
- [ ] Update CHANGELOG.md

**Deployment:**
- [ ] Deploy FILE_REGISTRY.json to production
- [ ] Deploy updated process YAML
- [ ] Deploy MODULE_REGISTRY
- [ ] Enable pre-commit hooks
- [ ] Enable CI/CD validation

**Post-Deployment:**
- [ ] Run full validation suite
- [ ] Generate traceability matrix
- [ ] Verify AI navigation works
- [ ] Monitor for 48 hours
- [ ] Collect team feedback

**Rollback Triggers:**
- Critical bug preventing development
- More than 50 validation errors
- Team consensus to rollback

**Deliverable:** Production deployment completed  
**Time:** 8 hours

---

#### 6.5 Post-Deployment Monitoring
**Week 6+ ongoing**

**Metrics to Track:**
- Validation pass rate (target: 100%)
- Number of UNCATEGORIZED files (target: <5%)
- Pre-commit hook failures (target: <10%)
- Developer questions/issues (track in wiki)

**Weekly Reports:**
- Validation status
- New files added and their module assignments
- Mapping violations caught by CI
- Improvement recommendations

**Deliverable:** Weekly status reports for 4 weeks  
**Time:** 2 hours/week

**Phase 6 Total Time:** 35 hours (~1 week)  
**Phase 6 Deliverables:** Documentation + training + production deployment

---

## Success Criteria & Acceptance Tests

### Primary Success Criteria
- [ ] **100% File Ownership:** All files have valid module_id
- [ ] **100% Step Linking:** All 24 process steps have entrypoint_files
- [ ] **Zero Validation Errors:** All 4 validators pass
- [ ] **Bidirectional Consistency:** File→Step and Step→File links verified

### Secondary Success Criteria
- [ ] **<5% Uncategorized:** Less than 5% of files in UNCATEGORIZED module
- [ ] **<3 Entrypoints/Step:** Average entrypoints per step ≤ 3
- [ ] **<10 Steps/Entrypoint:** No entrypoint file implements >10 steps
- [ ] **AI Navigation:** AI can answer traceability queries in <2 seconds

### Acceptance Tests

**Test 1: Traceability Query**
```bash
# Given: Step 16 exists
# When: Query which file implements it
# Then: Returns exactly 1 file: src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py
```

**Test 2: Reverse Traceability**
```bash
# Given: File src/B1_MT4_ADAPTER_TRANSPORT/transport_service.py exists
# When: Query which steps it implements
# Then: Returns exactly 1 step: Step 16
```

**Test 3: Module Boundary Enforcement**
```bash
# Given: File assigned to module A
# When: Linked to step in module B
# Then: Validator raises error
```

**Test 4: Role Restriction**
```bash
# Given: File with role='library'
# When: step_refs is populated
# Then: Validator raises error
```

**Test 5: Contract Compliance**
```bash
# Given: Step outputs ContractX
# When: ContractX not in module's out_types
# Then: Validator raises error
```

---

## Risk Management

### High-Risk Areas

**Risk 1: Incorrect Module Assignments**
- **Probability:** Medium
- **Impact:** High (breaks traceability)
- **Mitigation:**
  - Manual review of all entrypoint assignments
  - Conservative fallback to UNCATEGORIZED
  - Incremental refinement over 4 weeks
  - Weekly audits and corrections

**Risk 2: Process YAML Corruption**
- **Probability:** Low
- **Impact:** Critical (breaks entire workflow)
- **Mitigation:**
  - Automated backups before each change
  - Schema validation before commit
  - Staged rollout (dev → staging → prod)
  - Rollback procedure documented

**Risk 3: Breaking Existing Tools**
- **Probability:** Medium
- **Impact:** Medium (disrupts development)
- **Mitigation:**
  - Preserve ID_REGISTRY.json for 30 days
  - Dual-read support in transition period
  - Comprehensive testing in dev environment
  - Communication plan for deprecation

**Risk 4: Incomplete MODULE_REGISTRY**
- **Probability:** High
- **Impact:** Medium (manual workarounds needed)
- **Mitigation:**
  - Generate initial version from process doc
  - Allow PENDING/UNCATEGORIZED modules
  - Incremental definition over 6 weeks
  - Document gaps and workarounds

---

## Resource Requirements

### Personnel
- **Lead Developer:** 40 hours (Phases 1-4 implementation)
- **DevOps Engineer:** 20 hours (Phase 5 CI/CD)
- **Technical Writer:** 20 hours (Phase 6 documentation)
- **QA Engineer:** 16 hours (validation testing)
- **Project Manager:** 12 hours (coordination)

**Total:** 108 person-hours (~2.7 person-weeks)

### Tools & Infrastructure
- Python 3.10+ with libraries (PyYAML, jsonschema, pytest)
- JSON Schema validator
- Pre-commit framework
- CI/CD pipeline (GitHub Actions or equivalent)
- Documentation platform (Markdown viewer)

### Budget Estimate
- Personnel: $10,800 (108 hours × $100/hour average)
- Tools/licenses: $500
- Training materials: $200
- **Total:** ~$11,500

---

## Timeline Summary

| Phase | Duration | Deliverables | Dependencies |
|-------|----------|--------------|--------------|
| **Pre-Flight** | 3-5 days | Backups, branch, environment | None |
| **Phase 1** | 3 days | MODULE_REGISTRY | Pre-flight |
| **Phase 2** | 3 days | FILE_REGISTRY | Phase 1 |
| **Phase 3** | 2.5 days | Process YAML v2 | Phase 2 |
| **Phase 4** | 1.5 days | Bidirectional links | Phase 3 |
| **Phase 5** | 3 days | Validators + CI | Phase 4 |
| **Phase 6** | 5 days | Docs + deployment | Phase 5 |
| **Total** | **~6 weeks** | Complete mapping system | - |

**Critical Path:** Phase 1 → Phase 2 → Phase 3 → Phase 4  
**Parallel Work:** Phase 5 can start after Phase 3 complete

---

## Next Steps (Immediate Actions)

### Week 0 - Before Starting
1. [ ] **Get Approval:** Present plan to stakeholders
2. [ ] **Create Branch:** `feature/mapping-gap-fix`
3. [ ] **Backup Everything:** All registries + process docs
4. [ ] **Set Up Environment:** Python, tools, CI access
5. [ ] **Assign Roles:** Lead dev, DevOps, QA, PM

### Week 1 - Start Phase 1
1. [ ] **Day 1:** Extract modules from process YAML
2. [ ] **Day 2:** Derive module contracts
3. [ ] **Day 3:** Map modules to file patterns
4. [ ] **Day 4:** Generate MODULE_REGISTRY
5. [ ] **Day 5:** Validate and review

### Communication Plan
- **Daily:** Standup for implementation team
- **Weekly:** Status update to stakeholders
- **Bi-weekly:** Demo progress to broader team
- **End of project:** Training session for all developers

---

## Appendix: Scripts Inventory

### Phase 1 Scripts
- `extract_modules_from_process.py`
- `derive_module_contracts.py`
- `infer_module_file_patterns.py`
- `generate_module_registry.py`
- `validate_module_registry.py`

### Phase 2 Scripts
- `assign_module_ownership.py`
- `assign_file_roles.py`
- `migrate_registry.py`
- `validate_file_registry.py`

### Phase 3 Scripts
- `derive_step_entrypoints.py`
- `update_process_with_entrypoints.py`
- `validate_process_entrypoints.py`

### Phase 4 Scripts
- `populate_step_refs.py`
- `validate_bidirectional_mapping.py`
- `generate_traceability_matrix.py`

### Phase 5 Scripts
- `validators/module_ownership_validator.py`
- `validators/entrypoint_step_validator.py`
- `validators/role_validator.py`
- `validators/contract_validator.py`
- `run_all_validators.py`

### Utility Scripts
- `backup_registries.sh`
- `rollback_to_backup.sh`
- `query_traceability.py`
- `generate_reports.py`

**Total Scripts:** 23

---

## Conclusion

This implementation plan addresses the critical mapping gap through a systematic 6-week effort:

1. **Create** the missing MODULE_REGISTRY
2. **Extend** FILE_REGISTRY with module/role/step fields
3. **Enhance** process document with entrypoint_files
4. **Establish** bidirectional links with validation
5. **Automate** validation in pre-commit and CI/CD
6. **Document** and deploy to production

**Expected Outcome:**
- ✅ Complete traceability: Files ↔ Steps ↔ Modules
- ✅ Automated governance enforcement
- ✅ AI-navigable codebase
- ✅ Zero mapping drift

**Timeline:** 6 weeks  
**Budget:** ~$11,500  
**Risk Level:** Medium (well-mitigated)

---

**Ready to begin implementation on approval.**

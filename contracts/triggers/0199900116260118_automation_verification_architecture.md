# ALVT Architecture - Automation Verification Architecture

**doc_id:** `0199900116260118`  
**Created:** 2026-01-23T18:56:00Z  
**Version:** 1.0  
**Status:** Phase 1 - Architecture Defined

## Overview

ALVT (Automation Lifecycle Verification Tooling) provides objective, repeatable verification that automation triggers are correctly wired and complete before runtime execution.

## Core Principle

**Automation completeness must be provable through static analysis and graph connectivity verification before any runtime execution.**

## Architecture Layers

### Layer 0: Static Integrity
Verifies fundamental requirements without execution:
- Referenced files exist at specified paths
- Referenced config keys exist and are accessible
- No stub/TODO markers in required-path code
- All dependencies are resolvable

### Layer 1: Graph Connectivity
Verifies automation wiring through graph analysis:
- Required nodes exist (entrypoint, dispatcher, handler, gates, evidence)
- Required edges exist (trigger→entrypoint→dispatcher→handler→gates/evidence)
- No orphaned steps (all steps reachable from entrypoint)
- No missing transitions (all required paths complete)

### Layer 2+: Deferred (See Backlog)
- Layer 2: Plan determinism (hash stability, reproducible plans)
- Layer 3: Sandbox execution (isolated workspace testing)
- Layer 4: Negative path validation (error handling)
- Layer 5: Idempotency verification (safe re-execution)

## Artifact Flow

```
Trigger Lifecycle Contract (YAML)
         ↓
   ALVT Layer 0 Tool
         ↓
   reports/alvt/static.<trigger>.json (PASS/FAIL)
         ↓
   ALVT Layer 1 Tool
         ↓
   reports/alvt/graph.<trigger>.json (PASS/FAIL)
         ↓
   ACC Table Reconciliation
         ↓
   Contract-ACC Consistency Check
         ↓
   Validation Gates (pytest)
         ↓
   Baseline Freeze (when all PASS)
```

## Canonical Artifacts

### 1. Trigger Lifecycle Contract (Source of Truth)
**Location:** `contracts/triggers/trigger.<TRIGGER_ID>.yaml`  
**Purpose:** Machine-readable specification of:
- Trigger identity and metadata
- Required files and their roles
- Required config keys
- Expected nodes (entrypoint, dispatcher, handler, gates, evidence)
- Expected edges (wiring paths)
- Completion criteria

### 2. ALVT Tools
**Location:** `tools/alvt/`  
**Components:**
- `validate_contract.py` - Contract schema validation
- `layer0_static.py` - Static integrity verification
- `layer1_graph.py` - Graph connectivity verification
- `alvt_cli.py` - Unified CLI wrapper (Phase 5)

### 3. Verification Reports
**Location:** `reports/alvt/`  
**Format:** JSON with deterministic structure
- `static.<trigger>.json` - Layer 0 results
- `graph.<trigger>.json` - Layer 1 results

**Report Schema:**
```json
{
  "trigger_id": "string",
  "verification_layer": "layer0|layer1",
  "status": "PASS|FAIL",
  "timestamp_utc": "ISO8601",
  "checks": [
    {
      "check_id": "string",
      "passed": "boolean",
      "reason": "string (if failed)",
      "evidence": {}
    }
  ],
  "summary": {
    "total_checks": "int",
    "passed": "int",
    "failed": "int"
  }
}
```

### 4. Test Suite
**Location:** `tests/`  
**Coverage:**
- `test_alvt_layer0.py` - Layer 0 verification tests
- `test_alvt_layer1.py` - Layer 1 verification tests
- Must be runnable via `pytest -q`
- Must produce deterministic pass/fail

### 5. ACC Table (Automation Chain of Custody)
**Purpose:** Human/AI-readable cross-reference showing complete automation chain
**Generated from:** Contract + actual implementation scan
**Used for:** Gap detection and contract reconciliation

## Workspace-Safe Testing Rules (NON-NEGOTIABLE)

### Rule 1: No Global State Modification
Tests must NOT:
- Write to registry files outside test workspace
- Modify config files in production locations
- Create files in non-test directories
- Mutate shared state

### Rule 2: Workspace Isolation
All test execution must:
- Use `tmp_path` fixture for file operations
- Use workspace-relative paths for registry operations
- Clean up all artifacts after test completion
- Be repeatable without manual cleanup

### Rule 3: Registry Path Policy
- **Production:** Absolute paths to `data/registries/`
- **Testing:** Workspace-relative paths (e.g., `workspace_dir/test_registry.json`)
- **Validation:** Path must be configurable via Ops interface injection

### Rule 4: Deterministic Evidence
- All evidence artifacts must have deterministic names
- Timestamps must use fixed test values or be normalized
- File hashes must be reproducible
- Reports must sort collections consistently

## Contract-to-Implementation Binding

### Required Contract Sections
1. **metadata:** trigger_id, version, description
2. **required_files:** List of paths + roles (entrypoint, dispatcher, handler, etc.)
3. **required_config:** Config keys that must exist
4. **required_nodes:** Graph nodes (with node_id and node_type)
5. **required_edges:** Graph edges (from_node → to_node)
6. **forbidden_patterns:** Stub markers, TODO comments in required paths
7. **completion_gates:** What must be true for contract satisfaction

### ALVT Tool Responsibilities

**validate_contract.py:**
- Schema validation against contract template
- Path resolvability check (files referenced exist or are valid patterns)
- Internal consistency (edges reference declared nodes)

**layer0_static.py:**
- File existence verification (all `required_files` present)
- Config key verification (all `required_config` accessible)
- Forbidden pattern detection (search for stubs/TODOs in required paths)
- Output: JSON report with per-check status

**layer1_graph.py:**
- Node existence verification (all `required_nodes` found in code)
- Edge verification (all `required_edges` present in call graph)
- Orphan detection (no unreachable nodes)
- Output: JSON report with graph analysis

## Validation Gates

### Phase-Specific Gates

**Phase 1 (Architecture):**
```bash
python -m compileall src tools
# Exit 0 = PASS
```

**Phase 2 (Contracts):**
```bash
python tools/alvt/validate_contract.py --trigger FILE_IDENTITY_CREATE
# Exit 0 = PASS, prints "VALID"
```

**Phase 3 (Implementation):**
```bash
pytest -q tests/test_alvt_layer0.py
pytest -q tests/test_alvt_layer1.py
# Both exit 0 = PASS
```

**Phase 4 (Fix-Validate Loop):**
```bash
python tools/alvt/layer0_static.py --trigger FILE_IDENTITY_CREATE
python tools/alvt/layer1_graph.py --trigger FILE_IDENTITY_CREATE
# Both produce reports with status=PASS
# Run twice consecutively - both must PASS
```

## Fix-Validate-Repeat Discipline

When any gate FAILS:
1. **Capture failure evidence** → Issue log entry
2. **Identify root cause** → Missing file, config, node, or edge
3. **Apply minimal fix** → Add missing artifact or update contract
4. **Re-run gate** → Confirm fix resolved issue
5. **Repeat until PASS** → No manual "it looks good" allowed

## Integration with Existing Systems

### Registry Integration
- ALVT verification gates can be added to registry write policy
- "Automation complete" flag in registry requires ALVT PASS
- Registry-as-SSOT remains authoritative

### Evidence System Integration
- ALVT reports are themselves evidence artifacts
- Can be stored in evidence registry with metadata
- Queryable via EvidenceOps helpers

### Module/Contract System Integration
- Trigger contracts extend module contract pattern
- ALVT tools follow same ops injection pattern
- Workspace-safe rules align with existing test patterns

## Success Metrics

### Phase Completion Metrics
- **Phase 1:** Architecture doc exists + compiles
- **Phase 2:** Contract validates + paths resolve
- **Phase 3:** Tests exist + are runnable
- **Phase 4:** Tools produce PASS reports (2 consecutive runs)
- **Phase 5:** CLI works + runbook sufficient for non-author
- **Phase 6:** Baseline frozen + backlog documented

### Quality Gates (All Must Pass)
1. Contract schema validation: 100% PASS
2. Layer 0 static checks: 100% PASS
3. Layer 1 graph checks: 100% PASS
4. Pytest test suite: 100% PASS
5. Repeat execution: 2 consecutive runs PASS
6. No manual intervention required

## Decision Log

### Decision 1: Python Implementation Language
**Rationale:** Existing tooling in Python; pytest ecosystem; AST parsing available

### Decision 2: YAML Contract Format
**Rationale:** Human-readable; schema-validatable; version-controllable; comment-friendly

### Decision 3: JSON Report Format
**Rationale:** Machine-parseable; deterministic serialization; tooling support

### Decision 4: Ops Injection Pattern
**Rationale:** Aligns with automation minimal production pattern; testability; workspace isolation

### Decision 5: Layer 0+1 First, Layer 2+ Deferred
**Rationale:** Cheapest verification with highest ROI; establishes baseline before runtime work

## Phase 1 Exit Criteria
- [x] Architecture document created and committed
- [x] Workspace-safe rules documented
- [x] Artifact relationships defined
- [x] Validation gates specified
- [x] Compile check ready to execute

**Phase 1 Status:** ✅ COMPLETE

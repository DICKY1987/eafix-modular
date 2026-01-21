---
doc_id: 2026012120420018
title: Registry Operations Runbook
version: 1.0
date: 2026-01-21
status: AUTHORITATIVE
classification: OPERATIONS_GUIDE
author: System Architecture
---

# Registry Operations Runbook

**Document ID**: 2026012120420018  
**Version**: 1.0  
**Last Updated**: 2026-01-21T20:42:00Z

## Table of Contents

1. [Overview](#overview)
2. [Setup](#setup)
3. [Daily Operations](#daily-operations)
4. [Validation Gates](#validation-gates)
5. [Troubleshooting](#troubleshooting)
6. [Emergency Procedures](#emergency-procedures)
7. [CLI Reference](#cli-reference)

---

## 1. Overview

### Purpose

This runbook provides operational procedures for the Unified SSOT Registry validation system. It covers:
- Environment setup
- Running validators
- Interpreting results
- Troubleshooting common issues
- Emergency recovery procedures

### Components

- **Policy Artifacts** (6 files):
  - `2026012120420001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`
  - `2026012120420002_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`
  - `2026012120420003_EDGE_EVIDENCE_POLICY.yaml`
  - `2026012120420004_MODULE_ASSIGNMENT_POLICY.yaml`
  - `2026012120420005_PROCESS_REGISTRY.yaml`
  - `2026012120420017_SCHEMA_AUTHORITY_POLICY.md`

- **Validators** (5 modules):
  - `2026012120420006_validate_write_policy.py`
  - `2026012120420007_validate_derivations.py`
  - `2026012120420008_validate_conditional_enums.py`
  - `2026012120420009_validate_edge_evidence.py`
  - `2026012120420010_normalize_registry.py`

- **CLI**: `2026012120420011_registry_cli.py`

---

## 2. Setup

### 2.1 Prerequisites

**Required**:
- Python 3.8+
- PyYAML 6.0+
- jsonschema 4.0+
- pytest 7.0+ (for running tests)

**Check Installation**:
```bash
python --version
pip list | grep -E "(PyYAML|jsonschema|pytest)"
```

### 2.2 Directory Structure

```
id_16_digit/
├── contracts/           # Policy files (YAML)
├── validation/          # Validator modules (Python)
├── automation/          # CLI tools
├── tests/              # Test suites
├── docs/               # Documentation
└── ID_REGISTRY.json    # Canonical registry (if exists)
```

### 2.3 Environment Variables (Optional)

```bash
# Override registry location
export REGISTRY_PATH="/path/to/ID_REGISTRY.json"

# Verbose mode by default
export REGISTRY_VERBOSE=1
```

---

## 3. Daily Operations

### 3.1 Running Full Validation

**Command**:
```bash
cd "Directory management system/id_16_digit"
python automation/2026012120420011_registry_cli.py validate --strict
```

**Expected Output**:
```
Running registry validation...

✅ Write policy validation PASSED
✅ Derivations validation PASSED
✅ Conditional enum validation PASSED
✅ Edge evidence validation PASSED

🎉 All validation checks PASSED
```

**If Failures Occur**:
1. Review error messages
2. Run validators individually (see Section 5)
3. Apply fixes
4. Re-run validation

### 3.2 Normalizing Registry

**Dry-Run First** (recommended):
```bash
python automation/2026012120420011_registry_cli.py normalize --dry-run --verbose
```

**Apply Changes**:
```bash
python automation/2026012120420011_registry_cli.py normalize
```

**What It Does**:
- Converts paths to forward slashes
- Uppercases `rel_type` fields
- Lowercases `extension` fields
- Normalizes timestamps to ISO 8601 with Z suffix

### 3.3 Checking Policy Compliance

**Command**:
```bash
python automation/2026012120420011_registry_cli.py check-policy --write-policy --derivations
```

**Use Case**: Pre-commit check to ensure no policy violations before pushing changes.

---

## 4. Validation Gates

### 4.1 Gate 1: Write Policy Enforcement

**Purpose**: Ensure column ownership rules respected.

**Command**:
```bash
python validation/2026012120420006_validate_write_policy.py --registry ID_REGISTRY.json --verbose
```

**Pass Criteria**:
- No user writes to tool-only fields
- No immutable field changes
- Valid status transitions

**Common Failures**:
- "Column 'record_id' is tool_only, user writes not allowed"
- "Column 'created_utc' is immutable, cannot change"

**Fix**: Revert manual edits to protected fields, use scanner/CLI instead.

### 4.2 Gate 2: Derivations Consistency

**Purpose**: Ensure computed fields match formulas.

**Command**:
```bash
python validation/2026012120420007_validate_derivations.py --registry ID_REGISTRY.json --verbose
```

**Pass Criteria**:
- All derived fields match recomputed values
- No formula drift

**Common Failures**:
- "Column 'filename': stored='old.py' != computed='new.py'"
- "Column 'directory_path': stored='src\\module' != computed='src/module'"

**Fix**: Run normalizer, or rescan files to refresh derived fields.

### 4.3 Gate 3: Conditional Enum Validation

**Purpose**: Validate context-aware enum constraints.

**Command**:
```bash
python validation/2026012120420008_validate_conditional_enums.py --registry ID_REGISTRY.json --verbose
```

**Pass Criteria**:
- Transient statuses only for transient entities
- TTL and expires_utc consistency
- Edge evidence_method present

**Common Failures**:
- "Status 'running' not allowed for entity_kind='file'"
- "ttl_seconds set but expires_utc missing"

**Fix**: Correct status field, or add missing required fields.

### 4.4 Gate 4: Edge Evidence Quality

**Purpose**: Ensure edges have sufficient auditability.

**Command**:
```bash
python validation/2026012120420009_validate_edge_evidence.py --registry ID_REGISTRY.json --verbose
```

**Pass Criteria**:
- All edges have evidence_method
- Required fields present per method
- Confidence in allowed range
- Heuristic edges quarantined

**Common Failures**:
- "Missing evidence_method (required for all edges)"
- "Missing required field 'evidence_locator' for evidence_method='static_parse'"

**Fix**: Add missing evidence fields, or quarantine incomplete edges.

### 4.5 Gate 5: Normalization Check

**Purpose**: Ensure consistent field formats.

**Command**:
```bash
python validation/2026012120420010_normalize_registry.py --registry ID_REGISTRY.json --dry-run --verbose
```

**Pass Criteria**:
- 0 records need normalization
- Paths use forward slashes
- rel_type uppercase
- Timestamps have Z suffix

**Common Failures**:
- "relative_path: src\\file.py → src/file.py"
- "rel_type: imports → IMPORTS"

**Fix**: Run `normalize --apply`.

---

## 5. Troubleshooting

### 5.1 Validation Failures

**Problem**: Validator reports errors but cause unclear.

**Debug Steps**:
1. Run validator with `--verbose` flag
2. Check first error message for specific field/record
3. Inspect that record in `ID_REGISTRY.json`
4. Cross-reference with policy file

**Example**:
```bash
# Find the failing record
grep -A 10 "REC-000123" ID_REGISTRY.json

# Check policy for that field
grep -A 5 "module_id:" contracts/2026012120420001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml
```

### 5.2 Import Errors

**Problem**: `ModuleNotFoundError` or `ImportError`.

**Solutions**:
1. Ensure you're in the correct directory:
   ```bash
   cd "Directory management system/id_16_digit"
   pwd
   ```

2. Check Python path:
   ```bash
   python -c "import sys; print('\\n'.join(sys.path))"
   ```

3. Run from project root:
   ```bash
   PYTHONPATH=. python validation/2026012120420006_validate_write_policy.py
   ```

### 5.3 YAML Parse Errors

**Problem**: `yaml.scanner.ScannerError` when loading policies.

**Causes**:
- Tab characters (YAML requires spaces)
- Unquoted special characters
- Incorrect indentation

**Fix**:
```bash
# Check for tabs
grep -P '\t' contracts/*.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('contracts/FILE.yaml'))"
```

### 5.4 Performance Issues

**Problem**: Validation takes too long (>30 seconds for <10k records).

**Causes**:
- Large registry file (>100MB)
- Derivations recomputing expensive functions
- No caching of policy files

**Solutions**:
1. Profile validators:
   ```bash
   python -m cProfile -s time validation/2026012120420007_validate_derivations.py
   ```

2. Use dry-run for quick checks:
   ```bash
   python automation/2026012120420011_registry_cli.py normalize --dry-run
   ```

3. Query subsets:
   ```bash
   python automation/2026012120420011_registry_cli.py query --entity-kind file --output subset.json
   # Then validate subset
   ```

### 5.5 Cross-Platform Path Issues

**Problem**: Validation fails on Windows but passes on Linux.

**Cause**: Path separator differences (`\` vs `/`).

**Fix**: Run normalizer first:
```bash
python automation/2026012120420011_registry_cli.py normalize --apply
```

All validators now normalize paths internally, but registry should still use forward slashes.

---

## 6. Emergency Procedures

### 6.1 Registry Corruption

**Symptoms**:
- JSON parse error
- Missing required fields
- Duplicate IDs

**Recovery**:
1. **Stop all writes immediately**
2. Restore from backup:
   ```bash
   cp ID_REGISTRY.json.backup ID_REGISTRY.json
   ```

3. If no backup, attempt repair:
   ```bash
   # Check JSON validity
   python -m json.tool ID_REGISTRY.json > /dev/null
   
   # If invalid, find last valid state in git history
   git log --all --full-history -- ID_REGISTRY.json
   git checkout <commit-hash> -- ID_REGISTRY.json
   ```

4. Run full validation after restoration:
   ```bash
   python automation/2026012120420011_registry_cli.py validate --strict --report recovery_report.json
   ```

### 6.2 Policy File Corruption

**Symptoms**:
- YAML parse errors
- Missing policy sections
- Validators crash on load

**Recovery**:
1. Identify corrupted policy:
   ```bash
   for f in contracts/*.yaml; do
     echo "Checking $f"
     python -c "import yaml; yaml.safe_load(open('$f'))" || echo "FAILED: $f"
   done
   ```

2. Restore from git:
   ```bash
   git checkout HEAD -- contracts/2026012120420001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml
   ```

3. Verify restoration:
   ```bash
   python -c "import yaml; print('✓ Valid YAML'); yaml.safe_load(open('contracts/FILE.yaml'))"
   ```

### 6.3 Validator Crashes

**Symptoms**:
- Python exceptions during validation
- Exit code 2 (unexpected error)
- Traceback in output

**Debug**:
1. Capture full traceback:
   ```bash
   python validation/VALIDATOR.py 2>&1 | tee error.log
   ```

2. Check for known issues:
   - FileNotFoundError: Policy file missing
   - KeyError: Registry missing expected field
   - TypeError: Field type mismatch

3. Test with minimal registry:
   ```python
   # Create minimal test case
   echo '{"meta": {}, "records": [{"record_kind": "entity", "record_id": "REC-000001"}]}' > test.json
   python validation/VALIDATOR.py --registry test.json
   ```

4. If bug confirmed, quarantine problematic records and file issue.

---

## 7. CLI Reference

### 7.1 Main Commands

#### validate
```bash
python automation/2026012120420011_registry_cli.py validate [--strict] [--report FILE] [-v]
```
- `--strict`: Exit on first error
- `--report FILE`: Save detailed JSON report
- `-v, --verbose`: Verbose output

#### derive
```bash
python automation/2026012120420011_registry_cli.py derive [--dry-run] [--apply] [-v]
```
- `--dry-run`: Show changes without applying
- `--apply`: Apply changes to registry (NOT IMPLEMENTED YET)

#### normalize
```bash
python automation/2026012120420011_registry_cli.py normalize [--dry-run] [-v]
```
- `--dry-run`: Show changes without applying
- `-v, --verbose`: Show per-record changes

#### check-policy
```bash
python automation/2026012120420011_registry_cli.py check-policy [--write-policy] [--derivations] [-v]
```
- `--write-policy`: Check write policy only
- `--derivations`: Check derivations only
- (no flags: check both)

#### query
```bash
python automation/2026012120420011_registry_cli.py query [--record-kind KIND] [--entity-kind KIND] [--min-confidence N] [--output FILE]
```
- `--record-kind`: entity | edge | generator
- `--entity-kind`: file | asset | transient | etc.
- `--min-confidence`: Minimum confidence (0.0-1.0) for edges
- `--output FILE`: Save results to JSON

#### export
```bash
python automation/2026012120420011_registry_cli.py export --format [csv|sqlite] --output FILE [--entity-kind KIND]
```
- `--format`: csv | sqlite
- `--output FILE`: Output file path
- `--entity-kind`: Filter by kind (NOT IMPLEMENTED YET)

### 7.2 Individual Validator Commands

#### Write Policy
```bash
python validation/2026012120420006_validate_write_policy.py \
  --registry ID_REGISTRY.json \
  --actor [user|tool] \
  --verbose
```

#### Derivations
```bash
python validation/2026012120420007_validate_derivations.py \
  --registry ID_REGISTRY.json \
  --config CONFIG.yaml \
  --verbose
```

#### Conditional Enums
```bash
python validation/2026012120420008_validate_conditional_enums.py \
  --registry ID_REGISTRY.json \
  --verbose
```

#### Edge Evidence
```bash
python validation/2026012120420009_validate_edge_evidence.py \
  --registry ID_REGISTRY.json \
  --auto-correct \
  --verbose \
  --list-methods
```
- `--auto-correct`: Apply auto-quarantine
- `--list-methods`: Show known evidence methods

#### Normalize
```bash
python validation/2026012120420010_normalize_registry.py \
  --registry ID_REGISTRY.json \
  --output NORMALIZED.json \
  --dry-run \
  --verbose
```
- `--output FILE`: Save to different file
- `--dry-run`: Don't save changes

---

## 8. Operational Checklist

### 8.1 Daily Health Check
- [ ] Run `validate --strict`
- [ ] Check for new quarantined edges
- [ ] Review normalization report
- [ ] Verify backup exists and is recent

### 8.2 Pre-Deployment
- [ ] Run all validators
- [ ] Run integration tests: `python tests/2026012120420016_test_integration.py`
- [ ] Run unit tests: `python tests/2026012120420012_test_write_policy.py`
- [ ] Backup current registry
- [ ] Test on staging copy first

### 8.3 Post-Deployment
- [ ] Re-run validators
- [ ] Check for new errors
- [ ] Monitor validation performance
- [ ] Update runbook if issues discovered

---

## 9. Support and Escalation

### 9.1 Self-Service
- Review this runbook
- Check error messages in validator output
- Search Git history for similar issues

### 9.2 Getting Help
- Check `docs/2026012102510001_UNIFIED_SSOT_REGISTRY_IMPLEMENTATION_PLAN.md`
- Review policy contracts in `contracts/`
- Run integration tests to isolate issue

### 9.3 Reporting Issues
Include:
- Command run
- Full error output
- Registry snippet (sanitized)
- Policy file version
- Python version and OS

---

## 10. Hardening Features (v1.1)

### 10.1 Derive --Apply (Atomic Registry Updates)

**Purpose**: Apply derivation formulas to registry with atomic write + backup.

**Safety Guarantees**:
- Backup created before any modification
- Atomic write via temp file + os.replace()
- fsync ensures data persistence
- Idempotent (running twice = no changes second time)
- Respects write policy (only updates tool-owned fields)

**Basic Usage**:
```bash
# Dry-run: check what would change
python automation/2026012120420011_registry_cli.py derive --dry-run

# Apply changes with backup
python automation/2026012120420011_registry_cli.py derive --apply

# Timestamped backup (keeps history)
python automation/2026012120420011_registry_cli.py derive --apply --timestamped-backup

# Save detailed change report
python automation/2026012120420011_registry_cli.py derive --apply --report changes.json
```

**Output**:
```
Applying derivations to registry...
→ ENT-001: 2 field(s) updated
    extension: PY → py
    type_code: None → 00

✓ Backup created: ID_REGISTRY.json.backup
✓ Registry updated atomically: ID_REGISTRY.json

Results:
  Total records: 150
  Records updated: 12
  
  Fields updated:
    extension: 12
    type_code: 8
```

**Implementation Notes**:
1. **Backup Strategy**: Creates `.backup` file (or timestamped) before ANY writes
2. **Atomic Write**: Writes to `.tmp_registry_*.json`, fsyncs, then `os.replace()`
3. **Determinism**: Same inputs → same outputs (no timestamp fields recomputed)
4. **Idempotency**: Second run finds 0 changes if first succeeded

**Error Handling**:
- Backup failure → abort, exit code 2
- Write failure → temp file cleaned up, original untouched
- Validation failure → continue (but log warnings)

**When to Use**:
- After scan updates scanner-provided fields
- To fix inconsistent derived fields
- Before critical operations (atomic = safe)

**When NOT to Use**:
- Don't use to fix user-only fields (use manual edit)
- Don't use if registry format changed (migrate first)

---

### 10.2 Export to CSV/SQLite

**Purpose**: Export registry to CSV or SQLite for analysis/reporting.

#### CSV Export

**Deterministic Output**:
- Column order: priority columns first (record_id, doc_id, entity_kind...), then alphabetical
- Row order: sorted by (record_kind, record_id)
- Complex fields: serialized as JSON strings
- All columns present in every row (blank for null)

**Usage**:
```bash
# Export all records
python automation/2026012120420011_registry_cli.py export --format csv --output registry.csv

# Filter by entity kind
python automation/2026012120420011_registry_cli.py export --format csv --output files.csv --entity-kind file

# Filter by record kind
python automation/2026012120420011_registry_cli.py export --format csv --output edges.csv --record-kind edge
```

**Example CSV**:
```csv
record_id,record_kind,doc_id,entity_kind,filename,extension,semantic_tags
ENT-001,entity,1234567890123456,file,test.py,py,"[""policy"", ""validator""]"
EDGE-001,edge,,,,,
```

#### SQLite Export

**Schema**:
- `meta` table: key-value pairs from registry metadata
- `entity_records` table: all entity fields + indexes on (doc_id, entity_kind, module_id, status)
- `edge_records` table: all edge fields + indexes on (source_doc_id, target_doc_id, rel_type)
- `generator_records` table: all generator fields + indexes on (output_doc_id)

**Usage**:
```bash
# Export to SQLite
python automation/2026012120420011_registry_cli.py export --format sqlite --output registry.sqlite

# Query with SQL
sqlite3 registry.sqlite "SELECT filename, extension FROM entity_records WHERE module_id='MOD-CORE'"

# Check table structure
sqlite3 registry.sqlite ".schema entity_records"
```

**Queryable Examples**:
```sql
-- Find all Python files
SELECT doc_id, filename FROM entity_records WHERE extension='py';

-- Find high-confidence edges
SELECT * FROM edge_records WHERE confidence_score > 0.9;

-- Count by module
SELECT module_id, COUNT(*) FROM entity_records GROUP BY module_id;
```

**Implementation Notes**:
1. **Full Rebuild**: Drops existing DB, recreates tables (deterministic)
2. **Indexes**: Created for common query patterns
3. **Serialization**: Lists/dicts stored as JSON text
4. **Determinism**: Same registry → identical DB (row order stable)

---

### 10.3 Module Assignment Validator

**Purpose**: Enforce MODULE_ASSIGNMENT_POLICY precedence chain.

**Precedence Chain** (highest to lowest):
1. **Override** (`module_id_override` field) - manual override
2. **Manifest** (`.module.yaml` file in directory tree) - explicit declaration
3. **Path Rule** (regex match on `relative_path`) - automatic inference
4. **Default** (null) - unassigned

**Validation Rules**:
- Actual `module_id` must match expected from precedence
- Conflicts detected if multiple path rules match with different modules
- Override always wins (no validation against other rules)

**Usage**:
```bash
# Standalone validator
python validation/2026012120460001_validate_module_assignment.py --registry ID_REGISTRY.json --verbose

# Integrated in CLI
python automation/2026012120420011_registry_cli.py validate --include-module
```

**Example Output**:
```
Results:
  Total records: 150
  Entity records: 120
  Valid: 115
  Invalid: 5
  
  Module source distribution:
    override: 3
    manifest: 12
    path_rule: 95
    unassigned: 10

❌ Module assignment validation FAILED
  ENT-042: Module mismatch: actual='MOD-TESTS' != expected='MOD-CORE' (source: path_rule, reason: Matched pattern: ^core/.*)
```

**Path Rules** (from policy):
- `^core/.*` → MOD-CORE
- `^validation/.*` → MOD-VALIDATION
- `^registry/.*` → MOD-REGISTRY
- `^automation/.*` → MOD-AUTOMATION
- `^tests/.*` → MOD-TESTS
- `^docs/.*` → MOD-DOCS
- `^contracts/.*` → MOD-CONTRACTS
- `^hooks/.*` → MOD-HOOKS
- `^monitoring/.*` → MOD-MONITORING

**When to Enable**:
- When module features are used (module-based reports, etc.)
- To enforce architectural boundaries
- For modular codebases with clear ownership

**Gating**: Use `--include-module` flag (opt-in)

---

### 10.4 Process Validation Validator

**Purpose**: Enforce PROCESS_REGISTRY rules for workflow mapping.

**Validation Rules**:
1. `process_step_id` requires `process_id` (can't have step without process)
2. `process_step_role` requires both `process_id` and `process_step_id`
3. `process_id` must exist in registry (PROC-BUILD, PROC-TEST, PROC-DEPLOY, PROC-SCAN, PROC-VALIDATE)
4. `process_step_id` must belong to its `process_id`
5. `process_step_role` must be allowed for that step

**Usage**:
```bash
# Standalone validator
python validation/2026012120460002_validate_process.py --registry ID_REGISTRY.json --verbose

# Integrated in CLI
python automation/2026012120420011_registry_cli.py validate --include-process
```

**Example Output**:
```
Results:
  Total records: 150
  Records with process fields: 25
  Valid: 23
  Invalid: 2
  
  Records by process:
    PROC-BUILD: 12
    PROC-TEST: 10
    PROC-SCAN: 3

❌ Process validation FAILED
  ENT-099: process_step_id 'STEP-COMPILE' present but process_id is missing
  ENT-100: process_step_role 'fixture' not allowed for process 'PROC-BUILD' step 'STEP-COMPILE'. Allowed roles: ['input', 'output', 'tool', 'config']
```

**Valid Processes**:
- `PROC-BUILD` (steps: STEP-COMPILE, STEP-BUNDLE, STEP-LINT)
- `PROC-TEST` (steps: STEP-UNIT-TEST, STEP-INTEGRATION-TEST, STEP-E2E-TEST)
- `PROC-DEPLOY` (steps: STEP-PACKAGE, STEP-PUBLISH, STEP-PROVISION, STEP-RELEASE)
- `PROC-SCAN` (steps: STEP-DISCOVERY, STEP-ANALYSIS, STEP-SYNC)
- `PROC-VALIDATE` (steps: STEP-POLICY-CHECK, STEP-DERIVATION-CHECK, STEP-QUALITY-CHECK)

**When to Enable**:
- When process mapping features are used
- To ensure workflow integrity
- For process-aware tooling

**Gating**: Use `--include-process` flag (opt-in)

---

## 11. Implementation Notes

### 11.1 Atomic Write + Backup Strategy

**Flow**:
1. Read `ID_REGISTRY.json`
2. Compute changes (in memory)
3. If changes > 0:
   - `shutil.copy2(registry_file, backup_path)`  # Preserve metadata
   - `tempfile.mkstemp()` in same directory  # Atomic on same filesystem
   - `json.dump()` to temp file
   - `f.flush()` + `os.fsync()`  # Force write to disk
   - `os.replace(temp, registry)`  # Atomic on POSIX/Windows
4. If changes == 0: exit (no backup needed)

**Why Atomic**:
- `os.replace()` is atomic on both Windows and POSIX
- Prevents partial writes visible to readers
- Power loss during write → either old or new, never corrupt
- Same-filesystem requirement ensures atomicity

### 11.2 Export Determinism Rules

**CSV**:
- Column order from `priority_columns` list + sorted remainder
- Row order: `sorted(records, key=lambda r: (r.get("record_kind"), r.get("record_id")))`
- Complex field serialization: `json.dumps(value, ensure_ascii=False)`

**SQLite**:
- Full rebuild (drop + recreate) for determinism
- Indexes created in fixed order
- No timestamps in schema (would break reproducibility)
- INSERT order: records sorted before insertion

### 11.3 Validator Gating (Opt-In)

**Why Opt-In**:
- Module/process validators depend on features that may not be used
- Avoids false positives in projects not using those features
- Explicit intent (user knows what's being validated)

**How to Enable**:
```bash
# Enable module validator
registry_cli.py validate --include-module

# Enable process validator
registry_cli.py validate --include-process

# Enable both
registry_cli.py validate --include-module --include-process
```

**Default Behavior** (no flags):
- Runs: write_policy, derivations, conditional_enums, edge_evidence
- Skips: module_assignment, process_validation

---

## 12. Changelog

### v1.1 (2026-01-21) - Hardening Release
- **NEW**: derive --apply with atomic writes and backup
- **NEW**: CSV export with deterministic column/row ordering
- **NEW**: SQLite export with queryable schema + indexes
- **NEW**: Module assignment validator with precedence chain
- **NEW**: Process validation validator with workflow rules
- **IMPROVED**: Derivation engine skips timestamp fields (idempotency fix)
- **DOCS**: Implementation notes section added
- **TESTS**: 100% pass rate (5 derive, 5 export, 10 validator tests)

### v1.0 (2026-01-21)
- Initial runbook
- Covers all 5 validators + CLI
- Emergency procedures documented
- Cross-platform notes added

---

**Last Updated**: 2026-01-21T22:45:00Z  
**Next Review**: 2026-04-21 (Quarterly)

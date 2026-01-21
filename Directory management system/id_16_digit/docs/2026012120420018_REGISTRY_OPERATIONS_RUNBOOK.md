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

## 10. Changelog

### v1.0 (2026-01-21)
- Initial runbook
- Covers all 5 validators + CLI
- Emergency procedures documented
- Cross-platform notes added

---

**Last Updated**: 2026-01-21T20:42:00Z  
**Next Review**: 2026-04-21 (Quarterly)

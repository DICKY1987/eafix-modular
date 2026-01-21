# Registry Hardening - Quick Reference

**Version**: 1.1  
**Date**: 2026-01-21

---

## derive --apply (Atomic Updates)

```bash
# Check what would change (safe)
python automation/2026012120420011_registry_cli.py derive --dry-run

# Apply changes with backup
python automation/2026012120420011_registry_cli.py derive --apply

# With timestamped backup
python automation/2026012120420011_registry_cli.py derive --apply --timestamped-backup

# Generate detailed report
python automation/2026012120420011_registry_cli.py derive --apply --report changes.json --verbose
```

**When to use**: After scanner updates, to fix inconsistent derived fields  
**Safety**: Creates backup, atomic write, idempotent

---

## export to CSV/SQLite

```bash
# Export to CSV (all records)
python automation/2026012120420011_registry_cli.py export --format csv --output registry.csv

# Filter by entity kind
python automation/2026012120420011_registry_cli.py export --format csv --output files.csv --entity-kind file

# Export to SQLite
python automation/2026012120420011_registry_cli.py export --format sqlite --output registry.sqlite

# Query SQLite
sqlite3 registry.sqlite "SELECT filename FROM entity_records WHERE extension='py'"
```

**CSV**: Deterministic columns/rows, JSON serialization for complex fields  
**SQLite**: Indexed, queryable, perfect for analysis

---

## Module Assignment Validator

```bash
# Validate module assignments
python automation/2026012120420011_registry_cli.py validate --include-module

# Standalone
python validation/2026012120460001_validate_module_assignment.py --registry ID_REGISTRY.json --verbose
```

**Precedence**: override > manifest > path_rule > default  
**Path Rules**: `core/` → MOD-CORE, `tests/` → MOD-TESTS, etc.

---

## Process Validation Validator

```bash
# Validate process mappings
python automation/2026012120420011_registry_cli.py validate --include-process

# Standalone
python validation/2026012120460002_validate_process.py --registry ID_REGISTRY.json --verbose
```

**Rules**: Step requires process, role requires step+process, all must exist in registry

---

## Common Workflows

### Fix Inconsistent Derived Fields
```bash
# 1. Check what needs fixing
registry_cli.py derive --dry-run

# 2. Apply fixes
registry_cli.py derive --apply

# 3. Verify
registry_cli.py validate --strict
```

### Export for Analysis
```bash
# 1. Export to SQLite
registry_cli.py export --format sqlite --output analysis.sqlite

# 2. Query
sqlite3 analysis.sqlite "SELECT module_id, COUNT(*) FROM entity_records GROUP BY module_id"

# 3. Export subset to CSV
registry_cli.py export --format csv --output core_files.csv --entity-kind file
```

### Full Validation (All Gates)
```bash
registry_cli.py validate --strict --include-module --include-process --report full_report.json
```

---

## Troubleshooting

### derive --apply Reports Changes on Second Run
**Cause**: User-only fields being modified, or timestamp fields  
**Fix**: Timestamp fields now skipped (v1.1+). Check for user field violations.

### CSV Export Has Wrong Column Order
**Cause**: Expecting specific order  
**Fix**: CSV order is deterministic but may differ from expectations. Priority columns first, rest alphabetical.

### Module Validator Reports Mismatches
**Cause**: Actual module_id doesn't match path rules  
**Fix**: Either fix module_id or add override with `module_id_override` field

### Process Validator Fails
**Cause**: process_step_id without process_id, or invalid combination  
**Fix**: Ensure process_id present when step_id used, and combinations are valid per PROCESS_REGISTRY.yaml

---

## File Locations

| Component | Location |
|-----------|----------|
| CLI | `automation/2026012120420011_registry_cli.py` |
| Derivations Engine | `validation/2026012120420007_validate_derivations.py` |
| Module Validator | `validation/2026012120460001_validate_module_assignment.py` |
| Process Validator | `validation/2026012120460002_validate_process.py` |
| Tests (derive) | `tests/2026012120460003_test_derive_apply.py` |
| Tests (export) | `tests/2026012120460004_test_export.py` |
| Tests (validators) | `tests/2026012120460005_test_validators.py` |
| Runbook | `docs/2026012120420018_REGISTRY_OPERATIONS_RUNBOOK.md` |

---

## Test Suite

```bash
# Run all new tests
python tests/2026012120460003_test_derive_apply.py
python tests/2026012120460004_test_export.py
python tests/2026012120460005_test_validators.py

# Run all tests (new + existing)
python tests/2026012120420012_test_write_policy.py
python tests/2026012120420016_test_integration.py
```

**Expected**: 34/34 tests passing (100%)

---

## Safety Checklist

Before running derive --apply in production:
- [ ] Backup registry manually first
- [ ] Run with `--dry-run` to preview changes
- [ ] Check that `records_updated` count is reasonable
- [ ] Run on staging/test copy first
- [ ] Verify backup was created (`.backup` file)
- [ ] Test with `--timestamped-backup` to keep history

Before using validators in CI/CD:
- [ ] Understand which validators to run (core vs opt-in)
- [ ] Set up proper error handling (exit codes)
- [ ] Configure notifications for failures
- [ ] Document expected baseline (e.g., module validator may fail initially if modules not assigned)

---

**Quick Help**: `registry_cli.py --help` or `registry_cli.py [command] --help`  
**Full Documentation**: `docs/2026012120420018_REGISTRY_OPERATIONS_RUNBOOK.md`

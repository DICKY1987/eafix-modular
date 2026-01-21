<!-- doc_id: DOC-AUTOOPS-071 -->

# RepoAutoOps Runbook

**Version:** 0.1.0  
**Last Updated:** 2026-01-21  
**Doc ID:** DOC-AUTOOPS-071

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Components](#components)
6. [Troubleshooting](#troubleshooting)
7. [Operations](#operations)

---

## Overview

RepoAutoOps is an automated Git operations system that watches your filesystem for changes, classifies files according to module contracts, assigns identity prefixes and doc_ids, validates files, and automatically stages them for Git commits.

### Key Features

- **Async File Watching**: Monitor directories for changes with stability checking
- **Policy Enforcement**: Classify files using module contracts
- **Identity Assignment**: Auto-assign 16-digit prefixes and doc_ids
- **Validation**: Plugin-based validation system (doc_id, secrets)
- **Safe Git Operations**: Dry-run by default, explicit execution required
- **Loop Prevention**: Avoid processing self-induced changes

### Architecture

```
FileWatcher → EventQueue → Orchestrator → PolicyGate → Validators → Identity → GitAdapter
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Git installed and configured
- Write access to repository

### Install Package

```bash
cd /path/to/eafix-modular
pip install -e ".[dev]"
```

### Verify Installation

```bash
repo-autoops --version
# Output: repo-autoops, version 0.1.0

repo-autoops --help
```

---

## Configuration

### Create Configuration File

Copy the example configuration:

```bash
cp config/repo_autoops.yaml my_config.yaml
```

### Configuration Structure

```yaml
repository_root: "."

watch:
  enabled: true
  roots: ["."]
  ignore_patterns:
    - ".git/"
    - "__pycache__/"
    - "*.pyc"
  file_patterns:
    - "*.py"
    - "*.md"

identity:
  numeric_prefix_enabled: true
  doc_id_enabled: true

policy:
  contracts_dir: "config/module_contracts"

safety:
  dry_run_default: true  # IMPORTANT: Always dry-run first
```

### Module Contracts

Create contracts for each module:

```yaml
# config/module_contracts/my_module.yaml
module_id: "my_module"
root: "path/to/module"
canonical_allowlist:
  - "*.py"
  - "*.md"
forbidden_patterns:
  - "*.exe"
  - "secrets.*"
```

---

## Usage

### CLI Commands

#### Check Status

```bash
repo-autoops status
```

**Output:**
```
Pending work items: 0
Dry run: enabled
Repository: /path/to/repo
```

#### Watch Mode (Dry Run)

```bash
repo-autoops watch --dry-run --config my_config.yaml
```

This will:
1. Start file watcher
2. Process changes as they occur
3. Log what WOULD happen (no actual changes)
4. Press Ctrl+C to stop

#### Manual Enqueue

```bash
repo-autoops enqueue path/to/file.py
```

#### Process Queue

```bash
repo-autoops reconcile --dry-run
```

#### Validate Files

```bash
repo-autoops validate path/to/file.py
```

#### Execute Mode (CAUTION)

Only after verifying dry-run output:

```bash
repo-autoops watch --execute --config my_config.yaml
```

---

## Components

### FileWatcher

Monitors filesystem for changes using `watchfiles`.

**Features:**
- Async file watching
- Stability checking (waits for file to stop changing)
- Content hashing to detect actual changes
- Pattern matching (include/exclude)

**Doc ID:** DOC-AUTOOPS-004

### EventQueue

SQLite-backed persistent queue.

**Features:**
- Survives restarts
- Deduplication by path
- Status tracking (pending, processing, done, failed)
- Batch processing

**Doc ID:** DOC-AUTOOPS-005

### PolicyGate

Classifies files according to module contracts.

**Classifications:**
- `canonical`: Should be committed
- `generated`: Auto-generated, ignore
- `run_artifact`: Runtime files, ignore
- `quarantine`: Unknown/forbidden files

**Doc ID:** DOC-AUTOOPS-007

### IdentityPipeline

Assigns identifiers to files.

**16-Digit Prefix Format:** `YYYYMMDDHHmmssff`

**Doc ID Format:** `DOC-MODULE-NNN`

**Doc ID:** DOC-AUTOOPS-009

### Validators

Plugin-based validation system.

**Built-in Validators:**
- `DocIdValidator`: Checks for doc_id presence
- `SecretScanner`: Detects hardcoded secrets

**Doc ID:** DOC-AUTOOPS-010

### GitAdapter

Safe Git operations.

**Operations:**
- `stage_files`: Add files to staging
- `commit`: Create commit
- `pull_rebase`: Pull with rebase
- `push`: Push to remote

**Doc ID:** DOC-AUTOOPS-008

### LoopPrevention

Prevents infinite loops from self-induced changes.

**Mechanism:**
- Tracks operations in progress
- Suppresses events within time window (5 seconds default)
- Cleans up stale operations

**Doc ID:** DOC-AUTOOPS-006

---

## Troubleshooting

### Issue: No files being processed

**Check:**
1. Verify watch patterns match your files
2. Check ignore patterns aren't excluding files
3. Ensure files exist under watch roots
4. Run `repo-autoops status` to see queue

**Solution:**
```bash
repo-autoops enqueue path/to/file.py --dry-run
repo-autoops status
```

### Issue: File quarantined

**Check:**
```bash
repo-autoops validate path/to/file.py
```

**Causes:**
- No module contract found
- File matches forbidden pattern
- File not in any allowlist

**Solution:**
1. Create/update module contract
2. Add file pattern to canonical_allowlist
3. Check file isn't in forbidden_patterns

### Issue: Validation failed

**Check logs:**
```
validator_failed validator=doc_id message="No doc_id found (required)"
```

**Solution:**
```bash
# Add doc_id manually or use identity pipeline
repo-autoops assign-id path/to/file.py --dry-run
```

### Issue: Git operations failing

**Check:**
1. Git credentials configured
2. Remote repository accessible
3. Branch not protected
4. No merge conflicts

**Solution:**
```bash
git status
git pull --rebase
repo-autoops reconcile --dry-run
```

### Issue: Loop detected

**Symptoms:**
- Same file processed repeatedly
- Logs show "self_induced_in_progress"

**This is normal:** Loop prevention is working!

**If persistent:**
```bash
# Check suppression window in config
# Increase if needed (default 5 seconds)
```

### Issue: SQLite database locked

**Cause:** Multiple instances running

**Solution:**
```bash
# Stop all instances
pkill -f repo-autoops

# Or on Windows:
taskkill /F /IM python.exe /FI "WINDOWTITLE eq repo-autoops*"

# Remove lock
rm .repo_autoops_queue.db-journal
```

---

## Operations

### Daily Operations

#### Morning Startup

```bash
# 1. Check status
repo-autoops status

# 2. Process any pending items
repo-autoops reconcile --dry-run

# 3. Start watcher
repo-autoops watch --dry-run
```

#### Pre-Commit Check

```bash
# Validate all staged files
git diff --cached --name-only | xargs -I {} repo-autoops validate {}
```

#### End of Day

```bash
# Stop watcher (Ctrl+C)

# Check final queue status
repo-autoops status

# Review audit logs
cat _evidence/audit/*.jsonl | tail -50
```

### Maintenance

#### Clean Queue

```bash
# Remove completed items older than 24 hours
repo-autoops cleanup --days 1
```

#### Update Contracts

```bash
# After updating module contracts
repo-autoops validate-contracts

# Reconcile against new contracts
repo-autoops reconcile --dry-run
```

#### Backup

```bash
# Backup queue database
cp .repo_autoops_queue.db .repo_autoops_queue.db.backup

# Backup audit logs
tar -czf audit_backup_$(date +%Y%m%d).tar.gz _evidence/audit/
```

### Monitoring

#### View Logs

```bash
# Tail audit logs
tail -f _evidence/audit/$(date +%Y%m%d).jsonl

# Filter by event type
grep "file_classified" _evidence/audit/*.jsonl

# Count events
grep -c "file_event" _evidence/audit/*.jsonl
```

#### Queue Metrics

```bash
# Check queue depth
repo-autoops status | grep "Pending"

# List quarantined files
sqlite3 .repo_autoops_queue.db "SELECT path FROM work_items WHERE status='quarantined'"
```

---

## Safety Guidelines

### Always Dry-Run First

```bash
# CORRECT: Test first
repo-autoops watch --dry-run
# Review output...
# If satisfied, run with --execute

# WRONG: Don't run directly with --execute
```

### Gradual Rollout

1. **Phase 1:** Single directory, dry-run only
2. **Phase 2:** Monitor logs, validate behavior
3. **Phase 3:** Enable execution for one module
4. **Phase 4:** Expand to full repository

### Backup Before Automation

```bash
# Create safety branch
git checkout -b safety/before-autoops
git push origin safety/before-autoops

# Now safe to test automation
git checkout master
repo-autoops watch --execute
```

### Emergency Stop

```bash
# Kill watcher immediately
pkill -9 -f repo-autoops

# Revert recent commits if needed
git log -5
git reset --hard <safe-commit-hash>
```

---

## Advanced Usage

### Custom Validators

Create `plugins/validators/my_validator.py`:

```python
from repo_autoops.validators import Validator
from repo_autoops.models.results import ValidationResult

class MyValidator:
    def validate(self, path):
        # Your validation logic
        return ValidationResult(
            passed=True,
            validator_name="my_validator",
            message="Validation passed"
        )
```

Register in config:

```yaml
validation:
  custom_validators:
    - my_validator
```

### Integration with CI/CD

```yaml
# .github/workflows/autoops.yml
name: RepoAutoOps
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pip install -e .
      - run: repo-autoops validate-all
```

### Scheduled Reconciliation

Windows Task Scheduler:

```xml
<Task>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-01T09:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>repo-autoops</Command>
      <Arguments>reconcile --dry-run</Arguments>
    </Exec>
  </Actions>
</Task>
```

---

## Reference

### File Locations

- **Config:** `config/repo_autoops.yaml`
- **Contracts:** `config/module_contracts/*.yaml`
- **Queue DB:** `.repo_autoops_queue.db`
- **Audit Logs:** `_evidence/audit/*.jsonl`
- **Quarantine:** `_quarantine/`

### Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Validation failed
- `4`: Git operation failed

### Environment Variables

- `REPO_AUTOOPS_CONFIG`: Path to config file
- `REPO_AUTOOPS_DRY_RUN`: Force dry-run mode (`1`/`0`)
- `REPO_AUTOOPS_LOG_LEVEL`: Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

---

## Support

### Documentation

- Architecture: `GIT_AUTOMATION_ARCHITECTURE_COMPLETE.txt`
- Gap Analysis: `GIT_AUTOMATION_GAP_ANALYSIS.txt`
- Phase 1 Summary: `PHASE_1_DELIVERY_SUMMARY.md`

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_watcher.py -v

# Run with coverage
pytest --cov=repo_autoops --cov-report=html
```

### Getting Help

```bash
repo-autoops --help
repo-autoops watch --help
repo-autoops validate --help
```

---

**End of Runbook**

For updates and issues, see: https://github.com/DICKY1987/eafix-modular

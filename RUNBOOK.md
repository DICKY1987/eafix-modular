# UNIFIED REGISTRY AUTOMATION SYSTEM - RUNBOOK

**Document ID:** 2026012322470013  
**Version:** 1.0  
**Date:** 2026-01-23  
**Status:** OPERATIONAL GUIDE

---

## TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Commands](#commands)
5. [Troubleshooting](#troubleshooting)
6. [Monitoring](#monitoring)

---

## PREREQUISITES

- Python 3.8 or higher
- SQLite 3
- File permissions to watch target directories
- ~100MB disk space for registry + queue + backups

---

## INSTALLATION

```bash
cd eafix-modular

# Install dependencies
pip install watchdog

# Verify installation
python -m repo_autoops.automation_descriptor.cli --help
```

---

## QUICK START

### 1. Validate Registry

```bash
python -m repo_autoops.automation_descriptor.cli validate-registry
```

Expected output:
```
Registry hash: 8f3e4b2a1c9d...
Validation: PASSED
```

### 2. Check Work Queue Status

```bash
python -m repo_autoops.automation_descriptor.cli queue-status
```

Expected output:
```
Queue Status:
  queued: 0
  running: 0
  completed: 12
```

### 3. Start Filesystem Watcher

```bash
python -m repo_autoops.automation_descriptor.cli start-watcher --paths repo_autoops scripts
```

Expected output:
```
Starting watcher...
Press Ctrl+C to stop
```

---

## COMMANDS

### `validate-registry`

Validates the registry structure and computes current hash.

**Usage:**
```bash
python -m repo_autoops.automation_descriptor.cli validate-registry
```

**Output:**
- Registry hash (first 16 characters)
- Validation status

---

### `queue-status`

Shows work queue statistics by status.

**Usage:**
```bash
python -m repo_autoops.automation_descriptor.cli queue-status
```

**Output:**
- Count of items by status (queued/running/completed/failed/dead_letter)

---

### `start-watcher`

Starts filesystem watcher daemon to monitor changes.

**Usage:**
```bash
python -m repo_autoops.automation_descriptor.cli start-watcher [--paths PATH...]
```

**Options:**
- `--paths`: Directories to watch (default: repo_autoops)

**Example:**
```bash
python -m repo_autoops.automation_descriptor.cli start-watcher --paths repo_autoops scripts services
```

**To Stop:**
- Press `Ctrl+C` in terminal

---

## TROUBLESHOOTING

### Issue: "watchdog not installed"

**Diagnosis:**
```bash
python -c "import watchdog"
```

**Fix:**
```bash
pip install watchdog
```

---

### Issue: Registry write failed

**Diagnosis:**
Check backup directory:
```bash
ls -la "Directory management system/02_DOCUMENTATION/id_16_digit/registry/backups/"
```

**Fix:**
Rollback to latest backup:
```bash
cd "Directory management system/02_DOCUMENTATION/id_16_digit/registry"
cp backups/UNIFIED_SSOT_REGISTRY_YYYYMMDD_HHMMSS.json UNIFIED_SSOT_REGISTRY.json
```

---

### Issue: Work queue stuck

**Diagnosis:**
```bash
python -m repo_autoops.automation_descriptor.cli queue-status
```

**Fix:**
Reset stale items (via Python):
```python
from repo_autoops.automation_descriptor.work_queue import WorkQueue
queue = WorkQueue()
queue.reset_stale_running(older_than_minutes=5)
```

---

## MONITORING

### Key Metrics

1. **Queue Depth:**
```bash
python -m repo_autoops.automation_descriptor.cli queue-status
```
Healthy: queued < 100

2. **Registry Size:**
```bash
du -h "Directory management system/02_DOCUMENTATION/id_16_digit/registry/UNIFIED_SSOT_REGISTRY.json"
```
Healthy: Growing linearly with file count

3. **Backup Count:**
```bash
ls -1 "Directory management system/02_DOCUMENTATION/id_16_digit/registry/backups/" | wc -l
```
Healthy: Backups created regularly

---

## PRODUCTION DEPLOYMENT

### Phase 1: Dry Run (24 hours)
Monitor without writes to validate detection

### Phase 2: Validation (Every hour)
Run `validate-registry` via cron

### Phase 3: Gradual Rollout
Start with subset of paths, expand after 48 hours

### Phase 4: Full Production
Enable all watch paths, monitor for 1 week

---

## SUPPORT

**Logs:** `~/.dms/logs/`  
**Queue:** `~/.dms/queue/work_queue.db`  
**Registry:** `Directory management system/02_DOCUMENTATION/id_16_digit/registry/UNIFIED_SSOT_REGISTRY.json`  
**Backups:** `Directory management system/02_DOCUMENTATION/id_16_digit/registry/backups/`

---

## VALIDATION GATES

All commands should execute without errors:

```bash
# Gate 1: Validate registry
python -m repo_autoops.automation_descriptor.cli validate-registry

# Gate 2: Check queue
python -m repo_autoops.automation_descriptor.cli queue-status

# Gate 3: Help text
python -m repo_autoops.automation_descriptor.cli --help
```

**Expected:** All commands succeed with exit code 0

---

**END OF RUNBOOK**

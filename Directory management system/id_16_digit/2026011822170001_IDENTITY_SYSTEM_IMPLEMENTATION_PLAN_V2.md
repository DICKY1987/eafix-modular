---
doc_id: 2026011822170001
title: EAFIX Identity System - Complete Implementation Plan v2.0
date: 2026-01-18T22:17:38Z
status: APPROVED_FOR_IMPLEMENTATION
classification: TECHNICAL_SPECIFICATION
version: 2.0
author: Senior Identity Systems Architect
supersedes: 2026011822020001
---

# EAFIX Identity System - Complete Implementation Plan v2.0

## Document Control

**Version:** 2.0  
**Status:** Approved for Implementation  
**Supersedes:** 2026011822020001 (3-Phase Roadmap)  
**Includes:** All gap analysis recommendations from 2026011822150001

---

## Executive Summary

This implementation plan delivers a **production-grade identity management system** for EAFIX with:
- **Central registry** for collision prevention
- **Automated lifecycle management** for moves/renames/deprecations
- **Full observability** with audit logs and metrics
- **CI/CD integration** with enforcement gates
- **Complete tooling** for allocation, validation, and maintenance

**Timeline:** 8 weeks  
**Effort:** 200 hours (1 FTE)  
**Risk:** Low (incremental, tested approach)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EAFIX Identity System                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐    │
│  │   Scanner    │─────▶│   Registry   │◀─────│  Allocator   │    │
│  │  (Discovers) │      │  (Authority) │      │  (Assigns)   │    │
│  └──────────────┘      └──────────────┘      └──────────────┘    │
│         │                      │                      │            │
│         ▼                      ▼                      ▼            │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐    │
│  │  Validators  │      │   Lifecycle  │      │   Renamer    │    │
│  │  (Checks)    │      │  (Manages)   │      │  (Updates)   │    │
│  └──────────────┘      └──────────────┘      └──────────────┘    │
│         │                      │                      │            │
│         └──────────────────────┴──────────────────────┘            │
│                                │                                    │
│                                ▼                                    │
│                       ┌──────────────┐                             │
│                       │  Audit Log   │                             │
│                       │  (JSONL)     │                             │
│                       └──────────────┘                             │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                         Automation Layer                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │  Git Hooks   │   │File Watcher  │   │   Scheduler  │          │
│  │  (Pre-commit)│   │ (Real-time)  │   │  (Nightly)   │          │
│  └──────────────┘   └──────────────┘   └──────────────┘          │
│         │                   │                   │                   │
│         └───────────────────┴───────────────────┘                   │
│                             │                                        │
│                             ▼                                        │
│                    ┌──────────────┐                                 │
│                    │   CI/CD      │                                 │
│                    │   Pipeline   │                                 │
│                    └──────────────┘                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
1. SCAN PHASE
   Scanner → Filesystem → CSV (26 columns)
   
2. ALLOCATION PHASE
   CSV → Allocator → Registry → Assigned IDs
   
3. VALIDATION PHASE
   Registry → Validators → Pass/Fail
   
4. LIFECYCLE PHASE
   Git Changes → Lifecycle Manager → Registry Updates
   
5. OBSERVABILITY PHASE
   All Events → Audit Log → Metrics → Dashboard
```

---

## Phase 1: Core System (Weeks 1-2)

### Objective

**Build the foundational registry and validation infrastructure to prevent ID collisions immediately.**

### Deliverables

#### 1.1 Central Registry Store

**File:** `id_16_digit/core/registry_store.py`

**Features:**
- JSON-based counter management
- File-based locking (fcntl)
- Atomic read-modify-write operations
- Allocation history tracking
- Counter per NS/TYPE/SCOPE tuple

**Schema:** `contracts/schemas/json/2026011822170002_registry_store.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Central ID Registry",
  "type": "object",
  "required": ["schema_version", "scope", "counters", "allocations", "metadata"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "scope": {"pattern": "^\\d{6}$"},
    "counters": {
      "type": "object",
      "propertyNames": {"pattern": "^\\d{3}_\\d{2}_\\d{6}$"},
      "additionalProperties": {
        "type": "object",
        "properties": {
          "current": {"type": "integer", "minimum": 0, "maximum": 99999},
          "allocated": {"type": "integer", "minimum": 0},
          "reserved": {"type": "array", "items": {"type": "integer"}}
        }
      }
    },
    "allocations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "file_path", "allocated_at", "status"],
        "properties": {
          "id": {"pattern": "^\\d{16}$"},
          "file_path": {"type": "string"},
          "allocated_at": {"format": "date-time"},
          "status": {"enum": ["active", "deprecated", "superseded"]},
          "metadata": {"type": "object"}
        }
      }
    }
  }
}
```

**API:**
```python
class RegistryStore:
    def allocate_id(ns_code: str, type_code: str, file_path: str) -> str
    def check_uniqueness() -> Tuple[bool, List[str]]
    def get_allocation(id_or_path: str) -> Optional[AllocationRecord]
    def mark_deprecated(id: str, superseded_by: Optional[str])
    def get_stats() -> Dict
```

**Implementation:**
- 500 lines of Python
- Comprehensive error handling
- Thread-safe operations
- Unit tests with concurrent access

#### 1.2 Uniqueness Validator

**File:** `id_16_digit/validation/validate_uniqueness.py`

**Checks:**
1. No duplicate IDs in filesystem
2. No duplicate IDs in registry
3. Filesystem ↔ Registry sync

**Output:**
```
✅ PASS: All IDs unique and synced
❌ FAIL: 3 errors found:
  - DUPLICATE_IN_FS: ID 2010000100260118 in 2 files
  - SYNC_ERROR: ID 2010000200260118 in registry but not filesystem
  - UNREGISTERED: ID 2010000300260118 in filesystem but not registry
```

**Integration:**
- Runs on every scan
- CLI tool for manual checks
- Exit code 0 (pass) or 1 (fail)

#### 1.3 Registry Sync Validator

**File:** `id_16_digit/validation/validate_identity_sync.py`

**Checks:**
1. IDs in filesystem but not registered (unregistered files)
2. IDs in registry but files missing/moved (stale paths)
3. Path mismatches (moved files without registry update)

**Usage:**
```bash
python validate_identity_sync.py \
  scan_output/file_scan_latest.csv \
  registry/ID_REGISTRY.json
```

#### 1.4 Duplicate Fixer

**File:** `id_16_digit/validation/fix_duplicates.py`

**Strategy:**
- Keep most recently modified file
- Reassign IDs to older duplicates
- Dry-run mode by default
- `--execute` flag for actual changes

**Usage:**
```bash
# Preview fixes
python fix_duplicates.py scan.csv registry.json

# Apply fixes
python fix_duplicates.py scan.csv registry.json --execute
```

#### 1.5 Audit Logger

**File:** `id_16_digit/monitoring/audit_logger.py`

**Format:** Append-only JSONL

**Events Logged:**
```json
{"event_id": "uuid", "run_id": "scan_123", "timestamp": "2026-01-18T22:00:00Z", "event_type": "allocation", "data": {"doc_id": "2010000100260118", "file_path": "services/api.py"}}
{"event_id": "uuid", "run_id": "scan_123", "timestamp": "2026-01-18T22:00:01Z", "event_type": "move", "data": {"doc_id": "2010000100260118", "old_path": "api.py", "new_path": "services/api.py"}}
{"event_id": "uuid", "run_id": "scan_123", "timestamp": "2026-01-18T22:00:02Z", "event_type": "validation_error", "data": {"error_type": "duplicate", "details": {...}}}
```

**Integration:** All registry operations automatically logged

### Implementation Steps - Week 1

**Day 1-2: Registry Store**
- [ ] Implement `RegistryStore` class
- [ ] Add file locking mechanism
- [ ] Write JSON schema
- [ ] Unit tests (10 tests minimum)

**Day 3: Uniqueness Validator**
- [ ] Implement 3-way validation
- [ ] CLI interface
- [ ] Integration tests

**Day 4: Sync Validator**
- [ ] Implement sync checks
- [ ] Move detection logic
- [ ] CLI interface

**Day 5: Duplicate Fixer + Audit Logger**
- [ ] Fixer with dry-run mode
- [ ] Audit logger JSONL
- [ ] Integration tests

### Implementation Steps - Week 2

**Day 6-7: Integration Testing**
- [ ] Load testing (1000+ allocations)
- [ ] Concurrent access tests
- [ ] Failure recovery tests
- [ ] Performance benchmarking

**Day 8-9: Documentation**
- [ ] Registry API documentation
- [ ] Operational runbook
- [ ] Backup/restore procedures
- [ ] Troubleshooting guide

**Day 10: Phase 1 Handoff**
- [ ] Full system demo
- [ ] Code review
- [ ] Deploy to test environment
- [ ] Stakeholder approval

### Success Criteria - Phase 1

- ✅ Registry tracks 100+ allocations successfully
- ✅ Zero ID collisions in testing
- ✅ Lock mechanism prevents corruption
- ✅ Uniqueness validator catches all duplicates
- ✅ Sync validator detects all mismatches
- ✅ Audit log captures all events
- ✅ Performance: <1s for allocation, <100ms for lock

---

## Phase 2: Lifecycle & Automation (Weeks 3-5)

### Objective

**Implement automated ID allocation, file lifecycle management, and enforcement hooks.**

### Deliverables

#### 2.1 ID Allocator

**File:** `id_16_digit/core/id_allocator.py`

**Features:**
- Batch allocation mode
- Preview mode (dry-run)
- Integration with registry
- Metadata preservation

**API:**
```python
class IDAllocator:
    def allocate_single(file_path: str, type_code: str, ns_code: str) -> str
    def allocate_batch(files: List[Dict]) -> List[Tuple[str, str]]
    def preview_allocation(file_path: str) -> Dict
    def reserve_id(ns_code: str, type_code: str) -> str
```

**Usage:**
```bash
# Allocate single file
python id_allocator.py --file services/api.py --type 20 --ns 999

# Batch mode from CSV
python id_allocator.py --batch scan_output/file_scan_latest.csv --limit 100

# Preview mode
python id_allocator.py --batch scan.csv --dry-run
```

#### 2.2 File Renamer

**File:** `id_16_digit/core/file_renamer.py`

**Features:**
- Rename files with ID prefix
- Git-aware (uses git mv)
- Update imports/references
- Atomic operations
- Rollback capability

**Safety:**
- Backup before rename
- Verify no conflicts
- Update registry atomically
- Handle import updates

**Usage:**
```bash
# Rename single file
python file_renamer.py --file api.py --id 2010000100260118

# Batch rename
python file_renamer.py --batch allocations.json

# Dry-run
python file_renamer.py --batch allocations.json --dry-run
```

#### 2.3 Lifecycle Manager

**File:** `id_16_digit/core/lifecycle_manager.py`

**Workflows:**

**1. File Move:**
```python
def handle_move(old_path: str, new_path: str):
    # Update registry path
    # Preserve allocation timestamp
    # Log move event
```

**2. File Rename with ID Change:**
```python
def handle_rename_with_id_change(old_id: str, new_id: str, path: str):
    # Mark old ID as superseded
    # Create new allocation
    # Link supersession
```

**3. Deprecation:**
```python
def handle_deprecation(id: str, reason: str):
    # Mark as deprecated
    # Log reason
    # Notify if referenced elsewhere
```

**Git Integration:**
- Detect moves via `git diff --cached --name-status`
- Auto-update registry on detected moves
- Fail commit if registry update fails

#### 2.4 Frontmatter Injector

**File:** `id_16_digit/core/frontmatter_injector.py`

**Supported Formats:**

**Python:**
```python
# doc_id: 2010000100260118
```

**Markdown:**
```markdown
---
doc_id: 2010000100260118
---
```

**YAML/JSON:**
```yaml
doc_id: 2010000100260118
```

**PowerShell:**
```powershell
# DOC_ID: 2010000100260118
```

#### 2.5 Git Pre-Commit Hook

**File:** `id_16_digit/hooks/pre-commit.py`

**Checks:**
1. New files have IDs (or exempt)
2. ID format valid (16 digits)
3. No duplicates introduced
4. Registry in sync
5. Detect moves and update registry

**Behavior:**
- Exit 0: All checks pass, commit proceeds
- Exit 1: Validation failed, commit blocked
- `--no-verify`: Emergency override

**Installation:**
```bash
python id_16_digit/hooks/install_hook.py
```

#### 2.6 File Watcher

**File:** `id_16_digit/automation/file_watcher.py`

**Features:**
- Monitor file changes (create/modify/move/delete)
- Debounce mechanism (30s default)
- Exclude .git, venv, scan_output
- Auto-trigger validation on changes
- Background daemon mode

**Tech:** `watchdog` library

**Usage:**
```bash
# Start watcher
python file_watcher.py --watch-dir . --debounce 30

# Background mode
python file_watcher.py --daemon
```

#### 2.7 Scheduled Tasks

**File:** `id_16_digit/automation/scheduled_tasks.py`

**Tasks:**

**Nightly (2 AM):**
- Full repository scan
- Uniqueness validation
- Sync validation
- Coverage report

**Weekly (Monday 6 AM):**
- Coverage trend analysis
- Deprecation report
- Allocation velocity metrics

**Monthly (1st, 3 AM):**
- Registry audit
- Cleanup deprecated IDs >90 days
- Capacity planning (sequence limits)

**Implementation:**
```python
# Using schedule library
schedule.every().day.at("02:00").do(nightly_scan)
schedule.every().monday.at("06:00").do(weekly_report)
schedule.every().month.at("03:00").do(monthly_audit)
```

**Platform:**
- GitHub Actions (cron)
- Windows Task Scheduler
- systemd timers (Linux)

### Implementation Steps - Week 3

**Day 1-2: ID Allocator**
- [ ] Implement allocator with registry integration
- [ ] Batch mode
- [ ] Preview mode
- [ ] Unit tests

**Day 3: File Renamer**
- [ ] Rename logic with git integration
- [ ] Import update detection
- [ ] Rollback mechanism
- [ ] Tests

**Day 4-5: Lifecycle Manager**
- [ ] Move handler
- [ ] Rename handler
- [ ] Deprecation handler
- [ ] Git hook integration

### Implementation Steps - Week 4

**Day 6: Frontmatter Injector**
- [ ] Multi-format support
- [ ] Validation
- [ ] Tests for all formats

**Day 7-8: Git Hook + File Watcher**
- [ ] Pre-commit hook with all checks
- [ ] Move detection
- [ ] File watcher with debounce
- [ ] Installation scripts

**Day 9-10: Scheduled Tasks**
- [ ] Scheduler implementation
- [ ] Task definitions
- [ ] GitHub Actions workflows
- [ ] Logging and alerting

### Implementation Steps - Week 5

**Day 11-12: Integration Testing**
- [ ] End-to-end allocation workflow
- [ ] Move/rename lifecycle tests
- [ ] Hook testing with mock git repo
- [ ] Watcher stress testing

**Day 13-14: Documentation & Handoff**
- [ ] Lifecycle documentation
- [ ] Automation setup guide
- [ ] Troubleshooting guide
- [ ] Phase 2 demo

### Success Criteria - Phase 2

- ✅ Successfully allocate and rename 500+ files
- ✅ Zero data loss during operations
- ✅ Moves detected and registry updated automatically
- ✅ Git hooks prevent invalid commits
- ✅ File watcher detects changes within 10s
- ✅ Scheduled tasks run reliably
- ✅ Rollback mechanism tested and verified

---

## Phase 3: Observability & Hardening (Weeks 6-8)

### Objective

**Add comprehensive monitoring, metrics, and operational tooling for production readiness.**

### Deliverables

#### 3.1 Metrics Exporter

**File:** `id_16_digit/monitoring/metrics_exporter.py`

**Metrics:**

**Coverage Metrics:**
- `identity_coverage_percentage` - % of files with IDs
- `identity_total_files` - Total trackable files
- `identity_files_with_ids` - Files with assigned IDs

**Allocation Metrics:**
- `identity_total_allocations` - Total IDs ever allocated
- `identity_active_allocations` - Currently active IDs
- `identity_deprecated_allocations` - Deprecated IDs
- `identity_allocation_rate_per_day` - Daily allocation velocity

**Operation Metrics:**
- `identity_validation_errors_total` - Total validation failures
- `identity_duplicate_detections` - Duplicates caught
- `identity_registry_version` - Registry version number
- `identity_lock_acquisition_time_ms` - Lock performance

**Export Formats:**
- Prometheus (`.prom`)
- JSON
- CSV

**Usage:**
```bash
# Export Prometheus metrics
python metrics_exporter.py --format prometheus --output metrics.prom

# JSON format
python metrics_exporter.py --format json --output metrics.json
```

#### 3.2 Coverage Trend Tracker

**File:** `id_16_digit/monitoring/coverage_tracker.py`

**Features:**
- Track coverage % over time
- Detect regressions
- Generate trend reports
- Alert on drops >5%

**Storage:** `coverage_history.jsonl`

```json
{"date": "2026-01-18", "coverage": 0.95, "total_files": 571, "with_ids": 543}
{"date": "2026-01-19", "coverage": 0.96, "total_files": 580, "with_ids": 557}
```

**Report Generation:**
```bash
# Weekly trend report
python coverage_tracker.py --period week --output report.md

# Alert on regression
python coverage_tracker.py --check-regression --threshold 0.05
```

#### 3.3 CI/CD Pipeline

**File:** `.github/workflows/identity-validation.yml`

**Jobs:**

**1. Validate Uniqueness:**
```yaml
- name: Check Uniqueness
  run: |
    python id_16_digit/validation/validate_uniqueness.py \
      scan_output/scan.csv \
      registry/ID_REGISTRY.json
```

**2. Check Coverage:**
```yaml
- name: Validate Coverage
  run: |
    python id_16_digit/validation/validate_coverage.py \
      --baseline 0.95
```

**3. Verify Sync:**
```yaml
- name: Registry Sync
  run: |
    python id_16_digit/validation/validate_identity_sync.py \
      scan_output/scan.csv \
      registry/ID_REGISTRY.json
```

**4. Format Validation:**
```yaml
- name: Check ID Formats
  run: |
    python id_16_digit/validation/validate_formats.py
```

**Enforcement:**
- Block PR merge on failure
- Required status check
- Auto-comment with error details
- Suggest fixes

#### 3.4 Dashboard

**File:** `id_16_digit/monitoring/dashboard.py`

**Metrics Displayed:**
- Current coverage %
- Total allocations
- Allocation rate (7-day average)
- Last validation status
- Duplicate count
- Registry health
- Sequence utilization by namespace

**Implementation:**
- Simple web dashboard (Flask)
- Refresh every 60s
- Mobile-responsive
- Export to PNG

**Access:**
```bash
python dashboard.py --port 8080
# Open http://localhost:8080
```

#### 3.5 Drift Detector

**File:** `id_16_digit/monitoring/drift_detector.py`

**Detects:**
1. Files missing IDs that should have them
2. IDs not in registry (unregistered)
3. Registry entries for non-existent files (stale)
4. Deprecated IDs still in active use
5. Sequence numbers approaching limits

**Output:**
```
DRIFT REPORT - 2026-01-18T22:00:00Z
===========================================
Missing IDs: 5 files
  - services/new_api.py (no ID)
  - docs/README.md (no ID)

Unregistered IDs: 2 files
  - 2010000100260118 (services/legacy.py)

Stale Paths: 1 entry
  - 2010000200260118 (registered at old/path.py, not found)

Deprecation Violations: 0

Capacity Warnings: 1
  - Namespace 999_20_260118: 98,500/99,999 (98.5% used)
```

#### 3.6 Operational Runbook

**File:** `id_16_digit/docs/OPERATIONAL_RUNBOOK.md`

**Sections:**
1. Daily operations
2. Weekly maintenance
3. Monthly audits
4. Incident response
5. Backup/restore procedures
6. Capacity planning
7. Troubleshooting guide

### Implementation Steps - Week 6

**Day 1-2: Metrics Exporter**
- [ ] Implement metrics calculation
- [ ] Prometheus export
- [ ] JSON/CSV export
- [ ] Tests

**Day 3: Coverage Tracker**
- [ ] Time-series storage
- [ ] Trend analysis
- [ ] Regression detection
- [ ] Report generation

**Day 4-5: CI/CD Pipeline**
- [ ] GitHub Actions workflows
- [ ] Status checks
- [ ] PR comments
- [ ] Integration tests

### Implementation Steps - Week 7

**Day 6: Dashboard**
- [ ] Flask web interface
- [ ] Real-time metrics
- [ ] Charts/graphs
- [ ] Mobile responsive

**Day 7: Drift Detector**
- [ ] Drift detection algorithms
- [ ] Report generation
- [ ] Alert triggers
- [ ] CLI interface

**Day 8-9: Documentation**
- [ ] Operational runbook
- [ ] Troubleshooting guide
- [ ] Best practices
- [ ] Training materials

**Day 10: Integration Testing**
- [ ] End-to-end observability tests
- [ ] Dashboard testing
- [ ] Alert testing
- [ ] Performance validation

### Implementation Steps - Week 8

**Day 11-12: Production Hardening**
- [ ] Error handling review
- [ ] Edge case testing
- [ ] Performance optimization
- [ ] Security review

**Day 13: Deployment Preparation**
- [ ] Production checklist
- [ ] Rollback plan
- [ ] Monitoring setup
- [ ] On-call runbook

**Day 14: Final Handoff**
- [ ] Full system demo
- [ ] Training session
- [ ] Production deployment
- [ ] Post-deployment monitoring

### Success Criteria - Phase 3

- ✅ Metrics exported to Prometheus
- ✅ Dashboard accessible and accurate
- ✅ CI pipeline blocks invalid PRs
- ✅ Drift detection finds <5 issues/week
- ✅ Coverage tracker shows trends
- ✅ Operational runbook complete
- ✅ System production-ready

---

## File Structure

```
id_16_digit/
├── core/
│   ├── registry_store.py              # Phase 1
│   ├── id_allocator.py                # Phase 2
│   ├── file_renamer.py                # Phase 2
│   ├── lifecycle_manager.py           # Phase 2
│   ├── frontmatter_injector.py        # Phase 2
│   └── __init__.py
│
├── validation/
│   ├── validate_uniqueness.py         # Phase 1
│   ├── validate_identity_sync.py      # Phase 1
│   ├── validate_coverage.py           # Enhanced
│   ├── validate_formats.py            # Phase 3
│   ├── fix_duplicates.py              # Phase 1
│   └── __init__.py
│
├── monitoring/
│   ├── audit_logger.py                # Phase 1
│   ├── metrics_exporter.py            # Phase 3
│   ├── coverage_tracker.py            # Phase 3
│   ├── drift_detector.py              # Phase 3
│   ├── dashboard.py                   # Phase 3
│   └── __init__.py
│
├── automation/
│   ├── file_watcher.py                # Phase 2
│   ├── scheduled_tasks.py             # Phase 2
│   └── __init__.py
│
├── hooks/
│   ├── pre-commit.py                  # Phase 2
│   ├── install_hook.py                # Phase 2
│   └── README.md
│
├── contracts/
│   └── schemas/
│       └── json/
│           ├── 2026011820599999_counter_store.schema.json
│           └── 2026011822170002_registry_store.schema.json
│
├── registry/
│   ├── ID_REGISTRY.json               # Created by system
│   ├── .ID_REGISTRY.lock              # Lock file
│   └── identity_audit_log.jsonl       # Audit log
│
├── docs/
│   ├── OPERATIONAL_RUNBOOK.md         # Phase 3
│   ├── TROUBLESHOOTING_GUIDE.md       # Phase 3
│   ├── API_REFERENCE.md               # Phase 2
│   └── MIGRATION_GUIDE.md             # Phase 2
│
└── tests/
    ├── test_registry_store.py
    ├── test_allocator.py
    ├── test_lifecycle.py
    ├── test_validators.py
    └── test_integration.py
```

---

## Integration Points

### Enhanced File Scanner v2.py

**Add Allocation Mode:**

```python
# New CLI argument
parser.add_argument('--allocate-ids', action='store_true',
                   help='Allocate IDs during scan')

# Integration in _process_file
if config.allocate_ids and metadata.needs_id:
    from core.id_allocator import IDAllocator
    allocator = IDAllocator(config.registry_path)
    
    allocated_id = allocator.allocate_single(
        file_path=metadata.relative_path,
        type_code=metadata.type_code,
        ns_code=metadata.ns_code
    )
    
    metadata.planned_id = allocated_id
    metadata.needs_id = False
```

### IDENTITY_CONFIG.yaml

**No changes required** - existing config compatible.

### doc_id_subsystem

**Coexistence Strategy:**
- id_16_digit: File naming (16-digit numeric IDs)
- doc_id_subsystem: Documentation cross-reference (DOC-* IDs)
- Optional dual-ID mapping in registry

---

## Testing Strategy

### Unit Tests (100+ tests)

**Core Components:**
- `test_registry_store.py` - 30 tests
- `test_allocator.py` - 20 tests
- `test_lifecycle.py` - 15 tests
- `test_validators.py` - 25 tests
- `test_monitoring.py` - 10 tests

**Coverage Target:** ≥90%

### Integration Tests (30+ tests)

**Workflows:**
- End-to-end allocation
- Move/rename lifecycle
- Duplicate detection and fixing
- Git hook integration
- CI/CD pipeline

### Load Tests

**Scenarios:**
- 1,000 concurrent allocations
- 10,000 file scan
- 100 GB registry size
- 10 simultaneous lock acquisitions

**Performance Targets:**
- Allocation: <1s per ID
- Lock acquisition: <100ms
- Uniqueness check: <5s for 10k files
- Sync validation: <10s for 10k files

### Security Tests

**Checks:**
- Lock file permissions
- Registry file permissions
- Injection attacks (file paths)
- Race conditions
- Directory traversal

---

## Deployment Strategy

### Phase 1 Rollout (Week 2)

1. **Deploy registry to test environment**
2. **Run validation tools on test data**
3. **Generate test allocations (100 files)**
4. **Verify no collisions**
5. **Deploy to staging**

### Phase 2 Rollout (Week 5)

1. **Install git hooks on dev machines**
2. **Start file watcher in test mode**
3. **Enable scheduled tasks**
4. **Monitor for 1 week**
5. **Deploy to staging**
6. **Enable in production (opt-in)**

### Phase 3 Rollout (Week 8)

1. **Deploy metrics exporter**
2. **Configure CI/CD pipeline**
3. **Launch dashboard**
4. **Enable drift detection**
5. **Full production deployment**

### Rollback Plan

**Per Phase:**
- Phase 1: Delete registry, restore from backup
- Phase 2: Disable hooks/watcher, manual mode
- Phase 3: Disable CI gates, manual validation

---

## Operational Procedures

### Daily Operations (Automated)

- ✅ File watcher monitors changes
- ✅ Git hooks validate commits
- ✅ Nightly scan runs at 2 AM
- ✅ Metrics exported every 5 min

**Manual (5 min):**
- Review drift report
- Check dashboard
- Respond to alerts

### Weekly Maintenance (30 min)

**Tasks:**
- Review coverage trend
- Audit deprecation queue
- Check capacity warnings
- Backup registry to git

### Monthly Audit (2 hours)

**Tasks:**
- Full repository scan
- Registry integrity check
- Performance analysis
- Capacity planning
- Security review

### Backup Strategy

**Frequency:**
- On every registry update (automatic)
- Daily snapshots (kept 30 days)
- Weekly snapshots (kept 1 year)

**Storage:**
- Git repository (version control)
- S3/Cloud storage (offsite)
- Local copies (quick restore)

**Restore Procedure:**
1. Identify backup timestamp
2. Restore registry JSON
3. Run sync validator
4. Reconcile differences
5. Resume operations

---

## Monitoring & Alerts

### Health Checks

**Registry Health:**
- File accessible
- Lock file functioning
- No corruption
- Version incrementing

**Operational Health:**
- Hooks enabled
- Watcher running
- Scheduler active
- CI pipeline passing

### Alert Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Duplicate ID detected | 🔴 CRITICAL | Block commits, notify team |
| Coverage drop >5% | 🟡 WARNING | Investigate, notify lead |
| Registry corruption | 🔴 CRITICAL | Restore from backup |
| Lock timeout | 🟡 WARNING | Check for deadlocks |
| Sequence >95% used | 🟠 HIGH | Plan namespace expansion |
| Sync errors >10 | 🟡 WARNING | Run reconciliation |

### Metrics Dashboard

**Layout:**
```
┌─────────────────────────────────────────┐
│  EAFIX Identity System Dashboard       │
├─────────────────────────────────────────┤
│  Coverage: 96.2% ↑                      │
│  Total IDs: 1,234                       │
│  Allocation Rate: 45/day                │
│  Last Scan: 2 hours ago                 │
├─────────────────────────────────────────┤
│  [Coverage Trend Chart]                 │
│  [Allocation Rate Chart]                │
├─────────────────────────────────────────┤
│  Validation Status: ✅ PASS             │
│  Duplicates: 0                          │
│  Sync Errors: 0                         │
│  Drift Issues: 2                        │
└─────────────────────────────────────────┘
```

---

## Risk Analysis

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Registry corruption | LOW | CRITICAL | Atomic writes, backups, validation |
| Performance degradation | MEDIUM | MEDIUM | Caching, optimization, monitoring |
| Lock contention | LOW | MEDIUM | Timeout, retry, alerting |
| Sequence exhaustion | LOW | HIGH | Monitoring, capacity planning |
| Integration bugs | MEDIUM | MEDIUM | Comprehensive testing, staged rollout |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Team adoption | MEDIUM | HIGH | Training, documentation, support |
| False positives | MEDIUM | LOW | Threshold tuning, exemptions |
| Workflow disruption | LOW | MEDIUM | Gradual rollout, opt-in period |
| Maintenance overhead | LOW | MEDIUM | Automation, monitoring |

### Mitigation Summary

**Technical:**
- Extensive testing (100+ unit tests)
- Staged deployment (test → staging → prod)
- Rollback procedures documented
- Monitoring and alerting

**Operational:**
- 2-hour training session
- Comprehensive documentation
- Opt-in period (2 weeks)
- Dedicated support channel

---

## Success Metrics

### Phase 1 KPIs (Week 2)

| Metric | Target | Actual |
|--------|--------|--------|
| Registry latency | <1s | TBD |
| Lock acquisition | <100ms p99 | TBD |
| ID collisions | 0 | TBD |
| Uniqueness coverage | 100% | TBD |
| Test coverage | ≥90% | TBD |

### Phase 2 KPIs (Week 5)

| Metric | Target | Actual |
|--------|--------|--------|
| Files allocated | ≥500 | TBD |
| Data loss incidents | 0 | TBD |
| Hook installation | 100% | TBD |
| Watcher uptime | ≥99% | TBD |
| Rollback success | 100% | TBD |

### Phase 3 KPIs (Week 8)

| Metric | Target | Actual |
|--------|--------|--------|
| CI blocks invalid PRs | 100% | TBD |
| Dashboard uptime | ≥99% | TBD |
| Drift issues/week | <5 | TBD |
| Coverage | ≥95% | TBD |
| Alert false positive | <10% | TBD |

### Overall System Health (Month 1)

| Metric | Target | Current |
|--------|--------|---------|
| ID coverage | ≥95% | TBD |
| Duplicate rate | 0% | TBD |
| Allocation success | ≥99.9% | TBD |
| MTTD (Mean Time To Detect) | <1 hour | TBD |
| MTTR (Mean Time To Resolve) | <4 hours | TBD |

---

## Training Plan

### Developer Training (2 hours)

**Module 1: System Overview (30 min)**
- ID structure (TYPE-NS-SEQ-SCOPE)
- Registry architecture
- Workflow overview

**Module 2: Daily Operations (45 min)**
- Running scanner with allocation
- Handling validation errors
- Using lifecycle manager
- Interpreting dashboard

**Module 3: Troubleshooting (45 min)**
- Common errors and fixes
- Registry recovery
- Emergency procedures
- Support escalation

### Materials

- Training slide deck
- Video walkthrough
- Quick reference card
- FAQ document

---

## Documentation Deliverables

### Phase 1 Docs

- ✅ Registry API Reference
- ✅ Validation Guide
- ✅ Backup/Restore Procedures

### Phase 2 Docs

- ✅ Lifecycle Workflows Guide
- ✅ Git Hook Setup Guide
- ✅ Automation Configuration

### Phase 3 Docs

- ✅ Operational Runbook
- ✅ Troubleshooting Guide
- ✅ Monitoring & Alerts Guide
- ✅ Migration Guide

---

## Timeline Summary

### 8-Week Schedule

| Week | Phase | Focus | Hours | Deliverables |
|------|-------|-------|-------|--------------|
| 1 | Phase 1 | Registry + Validators | 40 | 5 components |
| 2 | Phase 1 | Testing + Docs | 20 | Production-ready Phase 1 |
| 3 | Phase 2 | Allocator + Renamer | 30 | Allocation tooling |
| 4 | Phase 2 | Lifecycle + Hooks | 30 | Automation |
| 5 | Phase 2 | Integration + Docs | 20 | Production-ready Phase 2 |
| 6 | Phase 3 | Metrics + CI/CD | 30 | Observability |
| 7 | Phase 3 | Dashboard + Drift | 20 | Monitoring |
| 8 | Phase 3 | Hardening + Deploy | 10 | Production deployment |

**Total:** 200 hours over 8 weeks (1 FTE)

---

## Cost-Benefit Analysis

### Development Costs

- **Engineering:** 200 hours @ $150/hr = $30,000
- **Testing/QA:** 40 hours @ $100/hr = $4,000
- **DevOps:** 20 hours @ $150/hr = $3,000
- **Total:** $37,000

### Operational Costs (Annual)

- **Maintenance:** 2 hours/week @ $150/hr = $15,600
- **Monitoring:** $100/month = $1,200
- **Total:** $16,800/year

### Benefits (Annual)

**Time Savings:**
- Manual ID assignment: 10 min/file × 1000 files = 167 hours saved
- Duplicate resolution: 1 hour/incident × 50 incidents = 50 hours saved
- Manual validation: 30 min/week × 52 weeks = 26 hours saved
- **Total:** 243 hours × $150/hr = **$36,450/year**

**Risk Reduction:**
- ID collision incidents avoided: 20/year × $2,000/incident = $40,000
- Data loss incidents avoided: 5/year × $10,000/incident = $50,000
- **Total:** **$90,000/year**

**ROI:** ($36,450 + $90,000 - $16,800) / $37,000 = **296% first year**

---

## Next Steps

### Immediate (Week 0)

1. **Approve implementation plan**
2. **Allocate resources** (1 FTE for 8 weeks)
3. **Set up development environment**
4. **Create project board/tracking**
5. **Kick-off meeting**

### Week 1 Start

1. **Begin Phase 1 implementation**
2. **Daily standups**
3. **Weekly progress reviews**
4. **Stakeholder updates**

### Post-Implementation

1. **Production deployment**
2. **Monitoring and support**
3. **Gather feedback**
4. **Plan enhancements**

---

## Approval

**Plan Status:** ✅ Ready for Implementation  
**Reviewed By:** [Stakeholder Name]  
**Approved By:** [Management]  
**Date:** 2026-01-18  
**Version:** 2.0

---

**Document Owner:** Senior Identity Systems Architect  
**Last Updated:** 2026-01-18T22:17:38Z  
**Version:** 2.0  
**Status:** APPROVED FOR IMPLEMENTATION  
**Supersedes:** 2026011822020001, Incorporates: 2026011822150001

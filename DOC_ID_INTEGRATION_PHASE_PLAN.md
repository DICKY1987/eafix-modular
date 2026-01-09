# Doc ID Subsystem Integration - Phase Plan
<!-- DOC_ID: DOC-DOC-0021 -->

**Project:** eafix-modular  
**Target System:** Doc ID Subsystem v3.0  
**Created:** 2026-01-09
**Status:** Ready for Execution

---

## Executive Summary

This plan outlines the complete integration of the Doc ID Subsystem into the eafix-modular repository. The system will assign unique, trackable IDs to all files for traceability, governance, and automated workflows.

### Integration Goals
- ✅ 100% coverage of Python files
- ✅ 100% coverage of YAML/JSON configuration files
- ✅ Automated validation in CI/CD
- ✅ Git pre-commit hooks for enforcement
- ✅ Full traceability for all repository artifacts

---

## Phase 0: Pre-Integration Assessment

**Duration:** 1-2 hours  
**Owner:** Technical Lead  
**Status:** NOT STARTED

### Tasks

#### 0.1 Repository Analysis
```bash
# Count files by type
cd C:\Users\richg\eafix-modular
Get-ChildItem -Recurse -File | Group-Object Extension | Sort-Object Count -Descending
```

**Expected Output:**
- Total Python files count
- Total YAML/YML files count
- Total JSON files count
- Total Markdown files count
- Total shell/PowerShell scripts count

#### 0.2 Directory Structure Review
- [ ] Review `services/` directory structure (11 services identified)
- [ ] Review `shared/` modules (reentry, idempotency, positioning)
- [ ] Review `tests/` organization (unit, integration, e2e, contracts)
- [ ] Review `contracts/` and `compliance/` directories
- [ ] Review `P_*` legacy directories

#### 0.3 Identify Exclusions
**Files/Directories to EXCLUDE from Doc ID assignment:**
- `.git/`
- `__pycache__/`
- `.venv/`, `venv/`, `node_modules/`
- `*.pyc`, `*.pyo`
- `.aider*`, `.claude`
- `signals.db` (SQLite database)
- Binary files (images, compiled assets)

#### 0.4 Baseline Metrics
- [ ] Total eligible files for doc ID assignment
- [ ] Estimated assignment time (50-100 files/batch)
- [ ] Identify critical paths (services, shared modules)

**Deliverables:**
- ✅ Repository assessment report
- ✅ Exclusion list documented
- ✅ Baseline metrics captured

---

## Phase 1: System Setup & Configuration

**Duration:** 2-3 hours  
**Owner:** DevOps/Platform Team  
**Status:** NOT STARTED

### Tasks

#### 1.1 Initialize Registry
```bash
cd doc_id_subsystem/registry
cp DOC_ID_REGISTRY.yaml.template DOC_ID_REGISTRY.yaml
```

#### 1.2 Define Categories for eafix-modular
Edit `DOC_ID_REGISTRY.yaml`:

```yaml
doc_id: DOC-CONFIG-REGISTRY-001
version: 1.0
categories:
  SERVICE:
    prefix: DOC-SERVICE
    description: Microservice implementations (data-ingestor, calendar-ingestor, etc.)
    next_id: 1
    count: 0
  
  API:
    prefix: DOC-API
    description: API endpoints and handlers (main.py, routers)
    next_id: 1
    count: 0
  
  MODEL:
    prefix: DOC-MODEL
    description: Data models and schemas (models.py, schemas)
    next_id: 1
    count: 0
  
  SHARED:
    prefix: DOC-SHARED
    description: Shared libraries (reentry, idempotency, positioning)
    next_id: 1
    count: 0
  
  TEST:
    prefix: DOC-TEST
    description: Test files (unit, integration, e2e, contract tests)
    next_id: 1
    count: 0
  
  CONFIG:
    prefix: DOC-CONFIG
    description: Configuration files (YAML, JSON, environment configs)
    next_id: 1
    count: 0
  
  SCRIPT:
    prefix: DOC-SCRIPT
    description: Automation scripts (CI, deployment, validation)
    next_id: 1
    count: 0
  
  CONTRACT:
    prefix: DOC-CONTRACT
    description: Service contracts and interfaces
    next_id: 1
    count: 0
  
  INFRA:
    prefix: DOC-INFRA
    description: Infrastructure as code (Docker, Kubernetes, Terraform)
    next_id: 1
    count: 0
  
  DOC:
    prefix: DOC-DOC
    description: Documentation files (README, guides, runbooks)
    next_id: 1
    count: 0
  
  LEGACY:
    prefix: DOC-LEGACY
    description: Legacy code in P_* directories (Friday updates, etc.)
    next_id: 1
    count: 0

docs: []
```

#### 1.3 Configure Classification Rules
Edit `doc_id_subsystem/core/classify_scope.py`:

```python
def classify_file(file_path: str) -> str:
    """Classify files into categories based on eafix-modular structure."""
    path_lower = file_path.lower().replace('\\', '/')
    
    # Services
    if '/services/' in path_lower and '/src/' in path_lower:
        if 'main.py' in path_lower or 'router' in path_lower:
            return 'API'
        elif 'models.py' in path_lower or 'schemas' in path_lower:
            return 'MODEL'
        else:
            return 'SERVICE'
    
    # Shared modules
    if '/shared/' in path_lower:
        return 'SHARED'
    
    # Tests
    if '/tests/' in path_lower or '/test_' in path_lower or path_lower.endswith('_test.py'):
        return 'TEST'
    
    # Contracts
    if '/contracts/' in path_lower or 'contract' in path_lower:
        return 'CONTRACT'
    
    # Scripts
    if '/scripts/' in path_lower or '/ci/' in path_lower:
        return 'SCRIPT'
    
    # Infrastructure
    if any(x in path_lower for x in ['/deploy/', '/dag/', 'docker', 'compose', '.yml']):
        return 'INFRA'
    
    # Documentation
    if path_lower.endswith(('.md', '.rst', '.txt')) and 'readme' in path_lower:
        return 'DOC'
    
    # Configuration
    if path_lower.endswith(('.yaml', '.yml', '.json', '.toml', '.ini', '.env')):
        return 'CONFIG'
    
    # Legacy P_ directories
    if '/p_' in path_lower or path_lower.startswith('p_'):
        return 'LEGACY'
    
    # Default
    return 'CONFIG'
```

#### 1.4 Update Scanner Configuration
Edit `doc_id_subsystem/core/doc_id_scanner.py`:

```python
ELIGIBLE_PATTERNS = [
    "**/*.py",
    "**/*.yaml",
    "**/*.yml", 
    "**/*.json",
    "**/*.md",
    "**/*.sh",
    "**/*.ps1",
    "**/*.bat",
    "**/Dockerfile*",
    "**/*.toml",
]

EXCLUDE_PATTERNS = [
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "*.pyc",
    ".aider*",
    ".claude",
    "*.db",
    "*.sqlite",
]
```

#### 1.5 Create Integration Scripts
Create helper scripts in `doc_id_subsystem/`:

**`run_initial_scan.ps1`:**
```powershell
# Initial repository scan
Write-Host "Starting Doc ID initial scan..." -ForegroundColor Cyan
cd core
python doc_id_scanner.py --repo-root "C:\Users\richg\eafix-modular"
Write-Host "Scan complete. Check docs_inventory.jsonl" -ForegroundColor Green
```

**`assign_batch.ps1`:**
```powershell
param(
    [int]$BatchSize = 50,
    [string]$Category = "AUTO"
)
cd core
python batch_assign_docids.py --batch-size $BatchSize --category $Category
```

**Deliverables:**
- ✅ Registry configured with 11 categories
- ✅ Classification rules customized
- ✅ Scanner configured
- ✅ Helper scripts created

---

## Phase 2: Initial File Discovery & ID Assignment

**Duration:** 4-6 hours  
**Owner:** Development Team  
**Status:** NOT STARTED

### Tasks

#### 2.1 Initial Scan (Discovery)
```bash
cd doc_id_subsystem
.\run_initial_scan.ps1
```

**Expected Output:**
- `registry/docs_inventory.jsonl` with all discovered files
- Summary statistics by file type
- List of files missing doc IDs

#### 2.2 Batch Assignment - Critical Services
**Priority 1: Core Services (services/)**

```bash
# Assign IDs to service implementations
cd core
python batch_assign_docids.py --path "../services/" --batch-size 50 --category SERVICE
```

**Services to process:**
- data-ingestor
- calendar-ingestor
- calendar-downloader
- transport-router
- flow-orchestrator
- reentry-engine
- reentry-matrix-svc
- indicator-engine
- event-gateway
- telemetry-daemon
- data-validator

#### 2.3 Batch Assignment - Shared Modules
**Priority 2: Shared Libraries (shared/)**

```bash
python batch_assign_docids.py --path "../shared/" --batch-size 50 --category SHARED
```

Modules:
- shared/reentry/
- shared/idempotency/
- shared/positioning/

#### 2.4 Batch Assignment - Tests
**Priority 3: Test Suite (tests/)**

```bash
python batch_assign_docids.py --path "../tests/" --batch-size 100 --category TEST
```

Test directories:
- tests/unit/
- tests/integration/
- tests/e2e/
- tests/contracts/
- tests/fixtures/

#### 2.5 Batch Assignment - Configuration
**Priority 4: Configuration Files**

```bash
# YAML/JSON configs
python batch_assign_docids.py --pattern "**/*.yaml" --batch-size 50 --category CONFIG
python batch_assign_docids.py --pattern "**/*.yml" --batch-size 50 --category CONFIG
python batch_assign_docids.py --pattern "**/*.json" --batch-size 50 --category CONFIG
```

#### 2.6 Batch Assignment - Infrastructure
**Priority 5: Infrastructure Code**

```bash
python batch_assign_docids.py --path "../deploy/" --batch-size 50 --category INFRA
python batch_assign_docids.py --path "../dag/" --batch-size 50 --category INFRA
python batch_assign_docids.py --path "../observability/" --batch-size 50 --category INFRA
```

#### 2.7 Batch Assignment - Scripts & CI
**Priority 6: Automation Scripts**

```bash
python batch_assign_docids.py --path "../scripts/" --batch-size 50 --category SCRIPT
python batch_assign_docids.py --path "../ci/" --batch-size 50 --category SCRIPT
```

#### 2.8 Batch Assignment - Documentation
**Priority 7: Documentation Files**

```bash
python batch_assign_docids.py --pattern "**/*.md" --batch-size 50 --category DOC
```

#### 2.9 Batch Assignment - Legacy Code
**Priority 8: P_* Directories (Optional)**

```bash
python batch_assign_docids.py --pattern "P_*/**/*.py" --batch-size 50 --category LEGACY
```

**Deliverables:**
- ✅ All eligible files have doc IDs assigned
- ✅ Registry updated with all assignments
- ✅ Inventory file synchronized

---

## Phase 3: Validation & Quality Assurance

**Duration:** 2-3 hours  
**Owner:** QA Team  
**Status:** NOT STARTED

### Tasks

#### 3.1 Validate Coverage
```bash
cd ../validation
python validate_doc_id_coverage.py --baseline 0.95
```

**Target Coverage:**
- Python files: 100%
- YAML/YML files: 100%
- JSON files: 100%
- Markdown files: ≥95%
- Shell scripts: ≥90%

#### 3.2 Validate Uniqueness
```bash
python validate_doc_id_uniqueness.py --strict
```

**Checks:**
- No duplicate doc IDs across repository
- No conflicting IDs in registry
- All IDs follow format: `DOC-{CATEGORY}-{NUMBER}`

#### 3.3 Validate Format
```bash
cd ../core
python fix_docid_format.py --check --no-fix
```

**Format Rules:**
- Prefix matches category (e.g., `DOC-SERVICE-*` for services)
- Numbering is sequential within category
- No gaps in numbering (acceptable but flagged)

#### 3.4 Fix Any Issues
If validation errors found:

```bash
# Fix duplicate IDs
cd ../validation
python fix_duplicate_doc_ids.py --auto-resolve

# Fix invalid formats
python fix_invalid_doc_ids.py --auto-fix

# Re-validate
python validate_doc_id_coverage.py --baseline 0.95
python validate_doc_id_uniqueness.py --strict
```

#### 3.5 Generate Coverage Report
```bash
cd ../core
python doc_id_scanner.py --stats --report coverage_report.json
```

**Report Contents:**
- Total files scanned
- Files with doc IDs
- Files missing doc IDs
- Coverage by file type
- Coverage by directory

**Deliverables:**
- ✅ Coverage ≥95% achieved
- ✅ All IDs unique and valid
- ✅ Coverage report generated
- ✅ Issues fixed and documented

---

## Phase 4: Automation & CI/CD Integration

**Duration:** 3-4 hours  
**Owner:** DevOps Team  
**Status:** NOT STARTED

### Tasks

#### 4.1 Install Pre-Commit Hook
```bash
cd doc_id_subsystem/automation
python -c "import shutil; shutil.copy('pre_commit_hook.py', '../../.git/hooks/pre-commit')"

# Make executable (Unix/Linux)
chmod +x ../../.git/hooks/pre-commit
```

**Hook Functionality:**
- Validates doc IDs before commit
- Blocks commits with invalid IDs
- Auto-assigns IDs to new files (optional)

#### 4.2 Add GitHub Actions Workflow
Create `.github/workflows/doc_id_validation.yml`:

```yaml
name: Doc ID Validation

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  validate-doc-ids:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pyyaml
      
      - name: Validate Doc ID Coverage
        run: |
          cd doc_id_subsystem/validation
          python validate_doc_id_coverage.py --baseline 0.95 --ci
      
      - name: Validate Doc ID Uniqueness
        run: |
          cd doc_id_subsystem/validation
          python validate_doc_id_uniqueness.py --strict --ci
      
      - name: Check Format
        run: |
          cd doc_id_subsystem/core
          python fix_docid_format.py --check --no-fix --ci
      
      - name: Upload Coverage Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: doc-id-coverage-report
          path: doc_id_subsystem/reports/coverage_*.json
```

#### 4.3 Add Makefile Targets
Edit `Makefile`:

```makefile
# Doc ID Management
.PHONY: docid-scan docid-validate docid-fix

docid-scan:
	@echo "Scanning repository for doc IDs..."
	cd doc_id_subsystem/core && python doc_id_scanner.py --repo-root ../..

docid-validate:
	@echo "Validating doc ID coverage and uniqueness..."
	cd doc_id_subsystem/validation && \
		python validate_doc_id_coverage.py --baseline 0.95 && \
		python validate_doc_id_uniqueness.py --strict

docid-fix:
	@echo "Fixing doc ID issues..."
	cd doc_id_subsystem/validation && \
		python fix_duplicate_doc_ids.py --auto-resolve && \
		python fix_invalid_doc_ids.py --auto-fix

docid-report:
	@echo "Generating doc ID coverage report..."
	cd doc_id_subsystem/core && python doc_id_scanner.py --stats --report ../../reports/doc_id_coverage.json
```

#### 4.4 Add Taskfile.yml Tasks
Edit `Taskfile.yml`:

```yaml
tasks:
  docid:scan:
    desc: Scan repository for doc IDs
    cmds:
      - cd doc_id_subsystem/core && python doc_id_scanner.py --repo-root ../..

  docid:validate:
    desc: Validate doc ID coverage and uniqueness
    cmds:
      - cd doc_id_subsystem/validation && python validate_doc_id_coverage.py --baseline 0.95
      - cd doc_id_subsystem/validation && python validate_doc_id_uniqueness.py --strict

  docid:assign:
    desc: Batch assign doc IDs (use --batch-size flag)
    cmds:
      - cd doc_id_subsystem/core && python batch_assign_docids.py --batch-size {{.BATCH_SIZE | default 50}}

  docid:fix:
    desc: Fix doc ID issues
    cmds:
      - cd doc_id_subsystem/validation && python fix_duplicate_doc_ids.py --auto-resolve
      - cd doc_id_subsystem/validation && python fix_invalid_doc_ids.py --auto-fix
```

#### 4.5 Update AGENTS.md
Add to `AGENTS.md`:

```markdown
## Doc ID System

All files in the repository must have a unique doc ID for traceability.

### Commands
- `make docid-scan`: Scan for missing doc IDs
- `make docid-validate`: Validate coverage and uniqueness
- `make docid-fix`: Auto-fix issues
- `task docid:assign`: Assign IDs to new files

### Doc ID Format
```
DOC-{CATEGORY}-{NUMBER}
```

### Categories
- SERVICE: Microservices
- API: API endpoints
- MODEL: Data models
- SHARED: Shared libraries
- TEST: Test files
- CONFIG: Configuration
- SCRIPT: Automation scripts
- CONTRACT: Service contracts
- INFRA: Infrastructure code
- DOC: Documentation
- LEGACY: Legacy P_* code

### Adding Doc IDs to New Files
New files should automatically get doc IDs via pre-commit hook. Manual assignment:
```bash
task docid:assign BATCH_SIZE=10
```
```

**Deliverables:**
- ✅ Pre-commit hook installed
- ✅ CI/CD workflow configured
- ✅ Makefile targets added
- ✅ Taskfile tasks added
- ✅ Documentation updated

---

## Phase 5: Documentation & Training

**Duration:** 2 hours  
**Owner:** Tech Lead  
**Status:** NOT STARTED

### Tasks

#### 5.1 Create Integration Documentation
Create `docs/doc_id_system.md`:

```markdown
# Doc ID System Documentation

## Overview
The doc ID system provides unique, trackable identifiers for all files in the repository.

## Usage

### For Developers
- All new files automatically get doc IDs via pre-commit hook
- Check coverage: `make docid-validate`
- Fix issues: `make docid-fix`

### For CI/CD
- Doc ID validation runs on all PRs
- PRs fail if coverage < 95% or duplicates found

### Doc ID Format
```
DOC-{CATEGORY}-{NUMBER}
```

Example: `DOC-SERVICE-001` (first service file)

## Maintenance
- Weekly: Review coverage reports
- Monthly: Audit and clean registry
- As needed: Fix validation errors

## Troubleshooting
See `doc_id_subsystem/INTEGRATION_GUIDE.md`
```

#### 5.2 Update README.md
Add section to main `README.md`:

```markdown
## Document Traceability

This repository uses a doc ID system for file traceability. Each file has a unique identifier.

**Quick Commands:**
```bash
make docid-scan      # Scan for doc IDs
make docid-validate  # Validate coverage
task docid:assign    # Assign to new files
```

For details, see `docs/doc_id_system.md`
```

#### 5.3 Create Runbook
Create `docs/runbooks/doc_id_maintenance.md`:

```markdown
# Doc ID System Maintenance Runbook

## Daily Operations
- Automated via pre-commit hook
- CI/CD validates on PRs

## Weekly Tasks
1. Review coverage: `make docid-report`
2. Check for drift: Look for files added without IDs
3. Fix any validation errors: `make docid-fix`

## Monthly Tasks
1. Full audit: `make docid-scan && make docid-validate`
2. Review category assignments
3. Update registry if needed
4. Backup registry: `git add doc_id_subsystem/registry/DOC_ID_REGISTRY.yaml`

## Incident Response
### Issue: Duplicate doc IDs
```bash
cd doc_id_subsystem/validation
python fix_duplicate_doc_ids.py --auto-resolve
```

### Issue: Coverage dropped below 95%
```bash
make docid-scan
cd doc_id_subsystem/core
python batch_assign_docids.py --category AUTO --batch-size 100
make docid-validate
```

### Issue: Pre-commit hook failing
1. Check `.git/hooks/pre-commit` exists
2. Verify it's executable
3. Test manually: `python .git/hooks/pre-commit`
```

#### 5.4 Team Training Materials
Create `docs/doc_id_quick_start.md`:

```markdown
# Doc ID System - Quick Start for Developers

## What is it?
Every file gets a unique ID like `DOC-SERVICE-042` for traceability.

## Do I need to do anything?
**No!** The pre-commit hook handles it automatically.

## What if I see an error?
Run: `make docid-fix`

## What if I want to check coverage?
Run: `make docid-validate`

## What categories exist?
- SERVICE, API, MODEL, SHARED, TEST, CONFIG, SCRIPT, CONTRACT, INFRA, DOC, LEGACY

## More info?
See `doc_id_subsystem/INTEGRATION_GUIDE.md`
```

**Deliverables:**
- ✅ Integration documentation created
- ✅ README updated
- ✅ Maintenance runbook created
- ✅ Quick start guide created

---

## Phase 6: Monitoring & Reporting

**Duration:** 2 hours  
**Owner:** Platform Team  
**Status:** NOT STARTED

### Tasks

#### 6.1 Setup Coverage Tracking
Create `scripts/doc_id_metrics.py`:

```python
#!/usr/bin/env python3
"""Generate doc ID metrics for monitoring."""

import json
import subprocess
from pathlib import Path

def get_coverage_metrics():
    """Run scanner and extract metrics."""
    result = subprocess.run(
        ["python", "doc_id_subsystem/core/doc_id_scanner.py", "--stats"],
        capture_output=True,
        text=True
    )
    # Parse output and extract metrics
    # Return as dict for Prometheus/monitoring
    return {
        "total_files": 0,
        "files_with_ids": 0,
        "coverage_percent": 0.0,
    }

if __name__ == "__main__":
    metrics = get_coverage_metrics()
    print(json.dumps(metrics, indent=2))
```

#### 6.2 Add Prometheus Metrics (Optional)
If using Prometheus, expose metrics:

```python
# In observability/metrics_exporter.py
from prometheus_client import Gauge

doc_id_coverage = Gauge('doc_id_coverage_percent', 'Doc ID coverage percentage')
doc_id_total_files = Gauge('doc_id_total_files', 'Total files tracked')

# Update periodically
def update_doc_id_metrics():
    metrics = get_coverage_metrics()
    doc_id_coverage.set(metrics['coverage_percent'])
    doc_id_total_files.set(metrics['total_files'])
```

#### 6.3 Create Dashboard (Optional)
Add to Grafana or monitoring dashboard:
- Doc ID coverage percentage (target: ≥95%)
- Total files tracked
- Files missing IDs
- Validation errors over time

#### 6.4 Setup Alerting (Optional)
Add Alertmanager rules:

```yaml
# observability/alerting/doc_id_alerts.yml
groups:
  - name: doc_id_alerts
    interval: 1h
    rules:
      - alert: DocIDCoverageLow
        expr: doc_id_coverage_percent < 95
        for: 1h
        annotations:
          summary: "Doc ID coverage below 95%"
          description: "Current coverage: {{ $value }}%"
      
      - alert: DocIDValidationErrors
        expr: doc_id_validation_errors > 0
        for: 15m
        annotations:
          summary: "Doc ID validation errors detected"
          description: "{{ $value }} errors found"
```

**Deliverables:**
- ✅ Metrics script created
- ✅ Prometheus metrics added (optional)
- ✅ Dashboard created (optional)
- ✅ Alerts configured (optional)

---

## Phase 7: Rollout & Stabilization

**Duration:** 1-2 weeks  
**Owner:** Tech Lead + Team  
**Status:** NOT STARTED

### Tasks

#### 7.1 Soft Launch (Week 1)
- [ ] Enable pre-commit hook for volunteers
- [ ] Monitor for issues
- [ ] Collect feedback
- [ ] Fix any edge cases

#### 7.2 Team Rollout (Week 2)
- [ ] Announce to team
- [ ] Share quick start guide
- [ ] Enable pre-commit hook for all devs
- [ ] Monitor CI/CD pipeline

#### 7.3 Mandatory Enforcement (Week 2+)
- [ ] Make doc ID validation required for PR merge
- [ ] Update PR template to mention doc IDs
- [ ] Add to code review checklist

#### 7.4 Post-Launch Review
- [ ] Review coverage metrics (target: ≥95%)
- [ ] Review validation errors (target: 0)
- [ ] Collect team feedback
- [ ] Document lessons learned

**Deliverables:**
- ✅ System rolled out to entire team
- ✅ Coverage target achieved
- ✅ Team trained and comfortable
- ✅ Post-launch review completed

---

## Success Criteria

### Phase Completion Checklist
- [ ] Phase 0: Repository assessment complete
- [ ] Phase 1: System configured and ready
- [ ] Phase 2: All files assigned doc IDs
- [ ] Phase 3: Validation passing (≥95% coverage)
- [ ] Phase 4: Automation and CI/CD integrated
- [ ] Phase 5: Documentation complete
- [ ] Phase 6: Monitoring in place
- [ ] Phase 7: System rolled out and stable

### Key Metrics
- **Coverage Target:** ≥95% of eligible files
- **Validation Errors:** 0 duplicates, 0 format errors
- **CI/CD Integration:** All PRs validated
- **Team Adoption:** 100% using pre-commit hook

### Risk Mitigation
- **Risk:** Large backlog of files to process
  - **Mitigation:** Batch processing by priority
- **Risk:** Merge conflicts during rollout
  - **Mitigation:** Coordinate with team, use feature branch
- **Risk:** Performance impact of pre-commit hook
  - **Mitigation:** Optimize hook, make it fast (<2s)
- **Risk:** Legacy P_* directories complex
  - **Mitigation:** Process last, mark as LEGACY category

---

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0 | 1-2 hours | None |
| Phase 1 | 2-3 hours | Phase 0 complete |
| Phase 2 | 4-6 hours | Phase 1 complete |
| Phase 3 | 2-3 hours | Phase 2 complete |
| Phase 4 | 3-4 hours | Phase 3 complete |
| Phase 5 | 2 hours | Phase 4 complete |
| Phase 6 | 2 hours | Phase 4 complete |
| Phase 7 | 1-2 weeks | All phases complete |

**Total Estimated Time:** 16-21 hours + 1-2 weeks stabilization

---

## Next Steps

1. **Review this plan** with team leads
2. **Schedule Phase 0** (assessment)
3. **Allocate resources** for Phases 1-6
4. **Set rollout date** for Phase 7
5. **Assign owners** for each phase
6. **Create tracking ticket** or project board

---

## References

- **Doc ID System Spec:** `doc_id_subsystem/docs/DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md`
- **Integration Guide:** `doc_id_subsystem/INTEGRATION_GUIDE.md`
- **Quick Reference:** `doc_id_subsystem/docs/QUICK_REFERENCE.md`
- **Batch Assignment Guide:** `doc_id_subsystem/docs/BATCH_DOC_ID_ASSIGNMENT_GUIDE.md`

---

## Contact

**Questions?** See the integration guide or contact the platform team.

**Doc ID System Version:** 3.0  
**Source:** ALL_AI Repository  
**Integration Date:** 2026-01-09

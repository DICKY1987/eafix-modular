---
doc_id: DOC-GUIDE-BATCH-DOC-ID-ASSIGNMENT-GUIDE-271
---

# Batch Doc ID Assignment Guide

**Purpose:** Assign doc IDs to all files in the specified directories  
**Created:** 2025-12-28  
**System:** SUB_DOC_ID v2.0

---

## Quick Start - 3 Steps

### Step 1: Scan Repository
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS
python doc_id_scanner.py scan
python doc_id_scanner.py stats
```

This will:
- Scan all eligible files in the repository
- Identify files missing doc_ids
- Create `docs_inventory.jsonl` in `5_REGISTRY_DATA/`

### Step 2: Assign Doc IDs (Batch)
```powershell
# Preview first (dry-run)
python doc_id_assigner.py auto-assign --dry-run

# Assign to first 100 files (recommended for testing)
python doc_id_assigner.py auto-assign --limit 100

# Assign to ALL files missing doc_ids
python doc_id_assigner.py auto-assign
```

### Step 3: Sync Registry
```powershell
cd ..\5_REGISTRY_DATA
python sync_registries.py sync
```

---

## Target Directories

You specified these 62 directories for doc ID creation:

```
PHASE5_ENTRY_GATE_DELIVERABLES
.pytest_cache
.benchmarks
PROCESS_STEP_LIB
UTI_TOOLS
test_aider_ollama
.claude
envs
runbooks
.runs
tests
SUB_DOC_ID
.governance
htmlcov
reports
scripts
docs
PHASE_0_BOOTSTRAP
PHASE_1_PLANNING
PHASE_2_REQUEST_BUILDING
PHASE_3_SCHEDULING
PHASE_4_ROUTING
PHASE_5_EXECUTION
PHASE_6_ERROR_RECOVERY
PHASE_7_MONITORING
SUB_AIM
SUB_CLP
SUB_DECISION_ELIMINATION
SUB_ENVIRONMENT
SUB_GITHUB
SUB_GLOSSARY
SUB_GUI
SUB_IO_CONTRACT_PIPELINE
SUB_LOG_REVIEW
SUB_LOGS
SUB_PATH_REGISTRY
SUB_PATTERNS
SUB_TEMPLATES
templates
.state
observability
DOCSYS
data
automation
IO_CONTRACT_FOR_START_PHASE_5
LIFECYCLE_V2.5.3_CONSOLIDATED
SSOT_System
LIFECYCLE
.ai
.workstreams
instances
Backups
specs
Proposed 25-File Foundational Context Set
patches
benchmarks
NEW DEVDirectory Evaluation Framework - Complete Package
out
UTI_VISUAL_DIAGRAMS
logs
modules
.github
AI_CONCEPTS_&_REFERENCE
```

**Note:** The scanner automatically processes ALL directories in the repo. You don't need to specify them individually.

---

## Detailed Instructions

### Option A: Batch Process Everything (Recommended)

```powershell
# Navigate to doc_id tools
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS

# 1. Scan entire repository
python doc_id_scanner.py scan

# 2. Check statistics
python doc_id_scanner.py stats

# 3. Preview assignments (see what will happen)
python doc_id_assigner.py auto-assign --dry-run | Out-File "..\.cache\assignment_preview.txt"

# 4. Review preview
notepad "..\.cache\assignment_preview.txt"

# 5. Execute assignment (all files)
python doc_id_assigner.py auto-assign

# 6. Sync registry
cd ..\5_REGISTRY_DATA
python sync_registries.py sync

# 7. Verify coverage
cd ..\2_VALIDATION_FIXING
python validate_doc_id_coverage.py --baseline 0.55
```

### Option B: Incremental Assignment (Safer)

Process files in batches to monitor progress:

```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS

# Batch 1: First 100 files
python doc_id_assigner.py auto-assign --limit 100
python ..\5_REGISTRY_DATA\sync_registries.py sync

# Batch 2: Next 100 files
python doc_id_assigner.py auto-assign --limit 100
python ..\5_REGISTRY_DATA\sync_registries.py sync

# Batch 3: Next 100 files
python doc_id_assigner.py auto-assign --limit 100
python ..\5_REGISTRY_DATA\sync_registries.py sync

# Continue until all files are processed...

# Final: Assign remaining files
python doc_id_assigner.py auto-assign
```

### Option C: Directory-Specific (Manual Control)

If you want to process specific directories only:

```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS

# Assign to a single file
python doc_id_assigner.py single --path "C:\Users\richg\ALL_AI\scripts\some_script.py" --category SCRIPT --name "some-script"
```

---

## Configuration

### File Types Eligible for Doc IDs

The scanner looks for these file extensions:
- `.py` - Python files
- `.md` - Markdown documentation
- `.yaml`, `.yml` - YAML config files
- `.ps1` - PowerShell scripts
- `.sh` - Shell scripts
- `.txt` - Text files
- `.json` - JSON files (selected)

### Excluded Directories

These directories are automatically skipped:
- `.venv`, `venv`, `__pycache__`
- `.git`, `.pytest_cache`
- `node_modules`
- Hidden directories (starting with `.`)

### Doc ID Format

Doc IDs are assigned in this format:
```
DOC-[CATEGORY]-[NAME]-[NUMBER]
```

**Examples:**
- `DOC-SCRIPT-VALIDATE-PHASE-001`
- `DOC-CORE-ORCHESTRATOR-042`
- `DOC-TEST-INTEGRATION-137`

---

## Categories Used

| Category | Prefix | Use For |
|----------|--------|---------|
| CORE | CORE | Core system components |
| SCRIPT | SCRIPT | Scripts and utilities |
| TEST | TEST | Test files |
| GUIDE | GUIDE | Documentation files |
| CONFIG | CONFIG | Configuration files |
| PAT | PAT | Pattern definitions |
| ERROR | ERROR | Error handling |
| AIM | AIM | AIM subsystem |
| GUI | GUI | GUI components |
| GLOSSARY | GLOSSARY | Glossary terms |
| PM | PM | Project management |
| SPEC | SPEC | Specifications |

---

## Monitoring Progress

### Check Coverage Statistics
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS
python doc_id_scanner.py stats
```

**Output Example:**
```
=== Doc ID Coverage Statistics ===
Total Files: 2,847
With Doc IDs: 1,423 (50.0%)
Missing Doc IDs: 1,424 (50.0%)
```

### Generate Coverage Report
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\4_REPORTING_MONITORING
python doc_id_coverage_trend.py --report
```

### Check for Issues
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\2_VALIDATION_FIXING

# Check for duplicates
python fix_duplicate_doc_ids.py --check

# Check for invalid formats
python fix_invalid_doc_ids.py --check

# Check coverage vs baseline
python validate_doc_id_coverage.py --baseline 0.55
```

---

## Automation Setup (Optional)

### Install Git Pre-Commit Hook
Automatically validate doc_ids before commits:
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\3_AUTOMATION_HOOKS
python install_pre_commit_hook.py
```

### Setup File Watcher
Monitor file changes and auto-scan:
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\3_AUTOMATION_HOOKS
python file_watcher.py --debounce 600
```

### Schedule Daily Scans
Setup Windows Task Scheduler to run daily:
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\3_AUTOMATION_HOOKS
python setup_scheduled_tasks.py --interval daily
```

---

## Troubleshooting

### Issue: Scanner Fails
**Symptom:** Scanner crashes or hangs  
**Solution:**
```powershell
# Check Python version (needs 3.8+)
python --version

# Install dependencies
pip install pyyaml

# Run with error logging
python doc_id_scanner.py scan 2>&1 | Out-File scan_errors.txt
```

### Issue: Assigner Can't Find Files
**Symptom:** "No files found to assign"  
**Solution:**
```powershell
# Ensure scan was run first
python doc_id_scanner.py scan

# Check inventory file exists
Test-Path ..\5_REGISTRY_DATA\docs_inventory.jsonl

# View inventory
Get-Content ..\5_REGISTRY_DATA\docs_inventory.jsonl | Select-Object -First 10
```

### Issue: Duplicate Doc IDs
**Symptom:** Validation fails with duplicates  
**Solution:**
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\2_VALIDATION_FIXING
python fix_duplicate_doc_ids.py --auto-resolve
```

### Issue: Registry Out of Sync
**Symptom:** Registry doesn't reflect recent assignments  
**Solution:**
```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\5_REGISTRY_DATA
python sync_registries.py sync --force
```

---

## Verification Commands

After assignment, verify everything worked:

```powershell
# 1. Check coverage improved
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS
python doc_id_scanner.py stats

# 2. Validate no duplicates
cd ..\2_VALIDATION_FIXING
python fix_duplicate_doc_ids.py --check

# 3. Validate no invalid formats
python fix_invalid_doc_ids.py --check

# 4. Check registry integrity
cd ..\5_REGISTRY_DATA
python sync_registries.py validate

# 5. Generate report
cd ..\4_REPORTING_MONITORING
python doc_id_coverage_trend.py --report
```

---

## Expected Results

After running the batch assignment:

1. **Coverage:** Should reach 90%+ (from ~50% baseline)
2. **Registry:** `DOC_ID_REGISTRY.yaml` should have all assignments
3. **Inventory:** `docs_inventory.jsonl` should show updated status
4. **Files:** Each file should have doc_id in frontmatter/header

---

## Performance Expectations

For a repository with ~3,000 files:

| Operation | Time | Notes |
|-----------|------|-------|
| Scan | 15-30 seconds | Checks all files |
| Assign (100 files) | 5-10 seconds | Incremental batch |
| Assign (all files) | 1-3 minutes | Full assignment |
| Sync Registry | 2-5 seconds | Updates YAML |
| Validation | 10-20 seconds | Checks integrity |

---

## Best Practices

1. **Always Preview First:** Use `--dry-run` before actual assignment
2. **Incremental Assignment:** Use `--limit` for large batches
3. **Frequent Syncing:** Sync registry after each batch
4. **Validate Often:** Run validators to catch issues early
5. **Backup Registry:** Copy `DOC_ID_REGISTRY.yaml` before major operations
6. **Monitor Coverage:** Track progress with statistics commands

---

## Alternative: Using Unified CLI

If you prefer a single command interface:

```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\7_CLI_INTERFACE

# Scan
python cli_wrapper.py scan

# Assign
python cli_wrapper.py assign

# Sync
python cli_wrapper.py sync

# Report
python cli_wrapper.py report daily
```

---

## Next Steps After Assignment

1. **Enable Git Hook:** Auto-validate on commits
2. **Setup Monitoring:** Daily reports and alerts
3. **Configure Baseline:** Set coverage target (e.g., 90%)
4. **Document Categories:** Update category definitions
5. **Train Team:** Share this guide with collaborators

---

## Support

For detailed documentation:
- **Process Map:** `SUB_DOC_ID/DOC_ID_PROCESS_MAP.md`
- **System README:** `SUB_DOC_ID/README.md`
- **Migration Guide:** `SUB_DOC_ID/MIGRATION_COMPLETE.md`

For command help:
```powershell
python doc_id_scanner.py --help
python doc_id_assigner.py --help
python sync_registries.py --help
```

---

## Summary - One-Command Solution

If you just want to process everything quickly:

```powershell
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS
python doc_id_scanner.py scan && `
python doc_id_assigner.py auto-assign && `
cd ..\5_REGISTRY_DATA && `
python sync_registries.py sync && `
cd ..\2_VALIDATION_FIXING && `
python validate_doc_id_coverage.py --baseline 0.55
```

This single pipeline will:
1. ✅ Scan the entire repository
2. ✅ Assign doc IDs to all eligible files
3. ✅ Sync the registry
4. ✅ Validate coverage

**Estimated time:** 2-5 minutes for ~3,000 files

---

**END OF GUIDE**

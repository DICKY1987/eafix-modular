---
doc_id: DOC-GUIDE-QUICK-REFERENCE-275
---

# SUB_DOC_ID Quick Reference Card

**Version:** 1.0.0  
**Date:** 2025-12-28  
**Purpose:** Quick command reference for common operations

---

## 📋 Essential Commands

### Scan Repository
```bash
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS
python doc_id_scanner.py scan                    # Scan and update inventory
python doc_id_scanner.py stats                   # Show statistics
python doc_id_scanner.py report                  # Generate report
```

### Assign Doc IDs
```bash
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\1_CORE_OPERATIONS
python doc_id_assigner.py auto-assign --dry-run  # Preview assignments
python doc_id_assigner.py auto-assign --limit 50 # Assign to first 50 files
python doc_id_assigner.py auto-assign            # Assign to all files
```

### Validate System
```bash
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\2_VALIDATION_FIXING
python validate_doc_id_coverage.py --baseline 0.55   # Check coverage
python validate_doc_id_uniqueness.py                  # Check uniqueness
python validate_doc_id_sync.py                        # Check file-registry sync
```

### Sync Registry
```bash
cd C:\Users\richg\ALL_AI\SUB_DOC_ID\5_REGISTRY_DATA
python sync_registries.py sync                   # Bidirectional sync
python sync_registries.py validate               # Validate sync
```

---

## 📁 Key File Locations

| What | Where |
|------|-------|
| **Master Spec** | `DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md` (root) |
| **Quick Start** | `BATCH_DOC_ID_ASSIGNMENT_GUIDE.md` (root) |
| **Directory Index** | `DIRECTORY_INDEX.md` (root) |
| **Scanner** | `1_CORE_OPERATIONS/doc_id_scanner.py` |
| **Assigner** | `1_CORE_OPERATIONS/doc_id_assigner.py` |
| **Registry** | `5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml` |
| **Validators** | `2_VALIDATION_FIXING/validate_*.py` |
| **Tests** | `6_TESTS/test_*.py` |

---

## 🔑 Important Files

### DO NOT EDIT DIRECTLY
- `5_REGISTRY_DATA/DOC_ID_REGISTRY.yaml` (use sync_registries.py)
- `.dir_id` (governance)
- `DIR_CONTRACT.yaml` (governance)
- `DIR_MANIFEST.yaml` (governance)

### PRIMARY OPERATIONS
- `doc_id_scanner.py` - Scan repository
- `doc_id_assigner.py` - Assign doc_ids (replaces all old writers)
- `sync_registries.py` - Registry synchronization
- `pre_commit_hook.py` - Git pre-commit validation

---

## 📖 Documentation Quick Access

### For AI Agents
1. `DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md` - Complete 47KB specification
2. `DIRECTORY_INDEX.md` - Navigation guide (this directory)
3. `BATCH_DOC_ID_ASSIGNMENT_GUIDE.md` - Quick start guide

### For Humans
1. `README.md` - Main entry point
2. `BATCH_DOC_ID_ASSIGNMENT_GUIDE.md` - Quick start
3. Directory-specific READMEs in each numbered directory

---

## 🚀 Common Workflows

### New File Added
```bash
# 1. Scan to detect new file
cd 1_CORE_OPERATIONS
python doc_id_scanner.py scan

# 2. Assign doc_id
python doc_id_assigner.py auto-assign --limit 1

# 3. Sync registry
cd ../5_REGISTRY_DATA
python sync_registries.py sync
```

### Bulk Assignment
```bash
# 1. Scan repository
cd 1_CORE_OPERATIONS
python doc_id_scanner.py scan --emit missing.json

# 2. Preview assignments
python doc_id_assigner.py auto-assign --dry-run

# 3. Assign in batches
python doc_id_assigner.py auto-assign --limit 100

# 4. Sync registry
cd ../5_REGISTRY_DATA
python sync_registries.py sync
```

### Validation Check
```bash
cd 2_VALIDATION_FIXING
python validate_doc_id_coverage.py --baseline 0.55
python validate_doc_id_uniqueness.py
python validate_doc_id_sync.py
```

---

## ⚡ Quick Tips

1. **Always scan first** before assigning
2. **Use --dry-run** to preview changes
3. **Sync registry** after bulk operations
4. **Check coverage** regularly
5. **Use directory READMEs** for detailed help

---

## 🔧 Troubleshooting

### Issue: File not getting doc_id
**Solution:** Check if file type is eligible in `common/rules.py`

### Issue: Duplicate doc_id
**Solution:** Run `2_VALIDATION_FIXING/fix_duplicate_doc_ids.py`

### Issue: Registry out of sync
**Solution:** Run `5_REGISTRY_DATA/sync_registries.py sync`

### Issue: Coverage too low
**Solution:** Run bulk assignment with `doc_id_assigner.py auto-assign`

---

## 📞 Getting Help

```bash
# Command-level help
python doc_id_scanner.py --help
python doc_id_assigner.py --help
python sync_registries.py --help

# Read documentation
# - DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md (complete info)
# - DIRECTORY_INDEX.md (navigation)
# - Directory READMEs (operation-specific)
```

---

**Quick Reference Card v1.0.0**  
**Last Updated:** 2025-12-28  
**For:** SUB_DOC_ID Document ID Management System

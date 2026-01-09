# Doc ID Subsystem Integration Guide
<!-- DOC_ID: DOC-DOC-0022 -->

**Version:** 1.0
**Target Project:** eafix-modular  
**Source System:** ALL_AI Doc ID System v3.0  
**Date:** 2026-01-09

---

## Overview

This package contains the **Doc ID Subsystem** - a production-ready document identification and tracking system exported from the ALL_AI repository. It provides automated assignment, validation, and tracking of unique document IDs across your entire codebase.

### What's Included

```
doc_id_subsystem/
├── core/                    # Core scanning and assignment tools
│   ├── doc_id_scanner.py   # File discovery and ID extraction
│   ├── doc_id_assigner.py  # ID injection into files
│   ├── batch_assign_docids.py
│   ├── classify_scope.py
│   ├── fix_docid_format.py
│   └── [common utilities]
├── validation/              # Validation and fixing tools
│   ├── validate_doc_id_coverage.py
│   ├── validate_doc_id_uniqueness.py
│   ├── fix_invalid_doc_ids.py
│   └── fix_duplicate_doc_ids.py
├── automation/              # Git hooks and file watchers
│   ├── file_watcher.py
│   └── pre_commit_hook.py
├── registry/                # Doc ID registry template
│   └── DOC_ID_REGISTRY.yaml.template
├── docs/                    # Complete documentation
│   ├── DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md
│   ├── BATCH_DOC_ID_ASSIGNMENT_GUIDE.md
│   ├── QUICK_REFERENCE.md
│   └── GUIDE_ADDING_NEW_ID_TYPES.md
├── README.md               # System overview
└── INTEGRATION_GUIDE.md    # This file
```

---

## Quick Start

### Step 1: Setup Registry

```bash
cd doc_id_subsystem/registry
cp DOC_ID_REGISTRY.yaml.template DOC_ID_REGISTRY.yaml
```

Edit `DOC_ID_REGISTRY.yaml` to customize categories for your project.

### Step 2: Initial Scan

```bash
cd ../core
python doc_id_scanner.py --repo-root /path/to/eafix-modular
```

This creates `docs_inventory.jsonl` with all discovered files.

### Step 3: Batch Assignment

```bash
python batch_assign_docids.py --batch-size 50 --category CONFIG
```

This assigns doc IDs to eligible files in batches.

### Step 4: Validation

```bash
cd ../validation
python validate_doc_id_coverage.py
python validate_doc_id_uniqueness.py
```

---

## Integration Steps

### 1. Customize for Your Project

#### Update Categories

Edit `registry/DOC_ID_REGISTRY.yaml` and define categories relevant to eafix-modular:

```yaml
categories:
  API:
    prefix: DOC-API
    description: API endpoints and handlers
    next_id: 1
  MODEL:
    prefix: DOC-MODEL
    description: Data models and schemas
    next_id: 1
  SERVICE:
    prefix: DOC-SERVICE
    description: Business logic services
    next_id: 1
  TEST:
    prefix: DOC-TEST
    description: Test files
    next_id: 1
  CONFIG:
    prefix: DOC-CONFIG
    description: Configuration files
    next_id: 1
```

#### Configure Scope Rules

Edit `core/classify_scope.py` to match your project structure:

```python
def classify_file(file_path: str) -> str:
    """Classify files into categories based on path patterns."""
    if '/api/' in file_path or 'api_' in file_path:
        return 'API'
    elif '/models/' in file_path:
        return 'MODEL'
    elif '/services/' in file_path:
        return 'SERVICE'
    elif '/tests/' in file_path or 'test_' in file_path:
        return 'TEST'
    else:
        return 'CONFIG'
```

### 2. Set Up Automation (Optional)

#### Pre-commit Hook

```bash
cp automation/pre_commit_hook.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

#### File Watcher (Optional)

```bash
# Run in background to auto-detect changes
python automation/file_watcher.py --watch-dir /path/to/eafix-modular
```

### 3. Batch Process Existing Files

```bash
# Scan repository
python core/doc_id_scanner.py --repo-root /path/to/eafix-modular

# Assign IDs in batches
python core/batch_assign_docids.py --batch-size 100
```

### 4. Add to Your CI/CD

Add validation to your CI pipeline:

```yaml
# .github/workflows/doc_id_validation.yml
name: Doc ID Validation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate Doc IDs
        run: |
          python doc_id_subsystem/validation/validate_doc_id_uniqueness.py
          python doc_id_subsystem/validation/validate_doc_id_coverage.py
```

---

## Configuration

### Environment Variables

```bash
# Registry location
export DOC_ID_REGISTRY_PATH="/path/to/DOC_ID_REGISTRY.yaml"

# Repository root
export REPO_ROOT="/path/to/eafix-modular"

# Scan inventory location
export DOCS_INVENTORY_PATH="./docs_inventory.jsonl"
```

### Python Dependencies

```bash
pip install pyyaml  # For registry parsing
```

No other dependencies required - the system uses Python standard library only.

---

## Doc ID Format

### Standard Format

```
DOC-{CATEGORY}-{NUMBER}
```

Examples:
- `DOC-API-001` - First API document
- `DOC-MODEL-042` - 42nd model document
- `DOC-CONFIG-123` - 123rd configuration document

### Injection Methods

#### Python Files
```python
# DOC_ID: DOC-API-001
# API endpoint handler
```

#### YAML/JSON Files
```yaml
doc_id: DOC-CONFIG-001
```

#### Markdown Files
```markdown
---
doc_id: DOC-GUIDE-001
---
```

---

## Common Workflows

### Add IDs to New Files

```bash
# Scan for new files
python core/doc_id_scanner.py --repo-root .

# Assign IDs to files missing them
python core/batch_assign_docids.py --category AUTO
```

### Fix Invalid IDs

```bash
# Detect and fix formatting issues
python validation/fix_invalid_doc_ids.py

# Fix duplicate IDs
python validation/fix_duplicate_doc_ids.py
```

### Generate Reports

```bash
# Coverage report
python validation/validate_doc_id_coverage.py --report

# Uniqueness check
python validation/validate_doc_id_uniqueness.py --verbose
```

---

## Maintenance

### Daily Operations

1. **Automated scanning** via file watcher or pre-commit hook
2. **Manual validation** before releases
3. **Registry backup** (commit `DOC_ID_REGISTRY.yaml` to git)

### Weekly Review

1. Check coverage metrics
2. Review and categorize new files
3. Fix any validation errors

### Monthly Audit

1. Full repository scan
2. Validate all IDs
3. Update documentation

---

## Troubleshooting

### Common Issues

#### "Registry not found"
- Ensure `DOC_ID_REGISTRY.yaml` exists in `registry/`
- Set `DOC_ID_REGISTRY_PATH` environment variable

#### "Duplicate doc_id detected"
- Run `validation/fix_duplicate_doc_ids.py`
- Manually resolve conflicts if needed

#### "Invalid format"
- Run `validation/fix_invalid_doc_ids.py`
- Check category prefixes in registry

### Getting Help

Refer to complete documentation:
- `docs/DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md` - Full technical spec
- `docs/QUICK_REFERENCE.md` - Command cheat sheet
- `docs/BATCH_DOC_ID_ASSIGNMENT_GUIDE.md` - Batch processing guide

---

## Migration from Source System

This subsystem was exported from the ALL_AI repository where it manages:
- **2,636 documents** across 8 categories
- **100% coverage** on Python, YAML, JSON files
- **Production stability** with comprehensive validation

### Key Differences

The export includes:
- ✅ Core scanning and assignment logic
- ✅ Validation and fixing tools
- ✅ Registry system with YAML format
- ✅ Automation hooks
- ✅ Complete documentation

Not included (source system specific):
- ❌ SSOT integration (patch-based updates)
- ❌ Lifecycle system integration
- ❌ Event emission system
- ❌ Original test suite (create your own)

---

## Next Steps

1. **Review** the complete specification: `docs/DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md`
2. **Customize** categories in `registry/DOC_ID_REGISTRY.yaml`
3. **Run** initial scan: `python core/doc_id_scanner.py`
4. **Start** batch assignment: `python core/batch_assign_docids.py`
5. **Validate** results: `python validation/validate_doc_id_coverage.py`

---

## License & Credits

**Source:** ALL_AI Repository Doc ID System v3.0  
**Exported:** 2026-01-09  
**License:** Same as eafix-modular project

---

## Contact & Support

For questions about this subsystem integration, refer to:
- Complete specification in `docs/`
- Source system documentation at `C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\`

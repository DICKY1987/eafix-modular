---
doc_id: DOC-DOC-0003
---

# Doc ID Subsystem for eafix-modular

**Version:** 1.0  
**Source:** ALL_AI Doc ID System v3.0  
**Status:** Production-Ready  
**Last Updated:** 2026-01-09

---

## What Is This?

A **document identification and tracking subsystem** that assigns unique, stable IDs to every file in your repository. Enables traceability, automated workflows, and governance enforcement.

### Key Features

- 🔍 **Auto-scanning** - Discover all files and detect missing IDs
- 🎯 **Auto-assignment** - Inject doc IDs into eligible files
- ✅ **Validation** - Ensure uniqueness, format consistency
- 📊 **Reporting** - Coverage metrics and trends
- 🔄 **Automation** - Git hooks, file watchers
- 📝 **Registry** - Central YAML-based ID allocation

---

## Quick Start (3 Steps)

### 1. Run Setup

```bash
cd doc_id_subsystem
python setup.py
```

This will:
- Create your doc ID registry
- Run initial repository scan
- Show next steps

### 2. Assign IDs

```bash
cd core
python batch_assign_docids.py --batch-size 50 --category AUTO
```

### 3. Validate

```bash
cd ../validation
python validate_doc_id_coverage.py
python validate_doc_id_uniqueness.py
```

---

## Directory Structure

```
doc_id_subsystem/
├── core/                    # Scanner, assigner, utilities
├── validation/              # Validators and fixers
├── automation/              # Git hooks, file watchers
├── registry/                # Doc ID registry (YAML)
├── docs/                    # Complete documentation
├── setup.py                 # Quick setup script
├── INTEGRATION_GUIDE.md     # Detailed integration guide
└── README.md               # This file
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** | Complete integration guide with examples |
| **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** | Command cheat sheet |
| **[DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md](docs/DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md)** | Full technical specification |
| **[BATCH_DOC_ID_ASSIGNMENT_GUIDE.md](docs/BATCH_DOC_ID_ASSIGNMENT_GUIDE.md)** | Batch processing guide |

---

## Doc ID Format

```
DOC-{CATEGORY}-{NUMBER}
```

**Examples:**
- `DOC-API-001` - API endpoint
- `DOC-MODEL-042` - Data model
- `DOC-TEST-123` - Test file
- `DOC-CONFIG-099` - Configuration

---

## Common Commands

### Scan Repository
```bash
python core/doc_id_scanner.py --repo-root /path/to/repo
```

### Assign IDs
```bash
python core/batch_assign_docids.py --batch-size 100
```

### Validate Coverage
```bash
python validation/validate_doc_id_coverage.py
```

### Fix Issues
```bash
python validation/fix_invalid_doc_ids.py
python validation/fix_duplicate_doc_ids.py
```

---

## Integration with eafix-modular

### Recommended Categories

Edit `registry/DOC_ID_REGISTRY.yaml`:

```yaml
categories:
  API:
    prefix: DOC-API
    description: API endpoints and handlers
  MODEL:
    prefix: DOC-MODEL
    description: Data models and schemas
  SERVICE:
    prefix: DOC-SERVICE
    description: Business logic services
  TEST:
    prefix: DOC-TEST
    description: Test files
  CONFIG:
    prefix: DOC-CONFIG
    description: Configuration files
  MIGRATION:
    prefix: DOC-MIGRATION
    description: Database migrations
```

### File Classification

Customize `core/classify_scope.py` for your structure:

```python
def classify_file(file_path: str) -> str:
    if '/api/' in file_path:
        return 'API'
    elif '/models/' in file_path:
        return 'MODEL'
    elif '/tests/' in file_path:
        return 'TEST'
    # ... add more rules
```

---

## Automation Setup

### Pre-commit Hook (Recommended)

```bash
cp automation/pre_commit_hook.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Validates doc IDs before each commit.

### File Watcher (Optional)

```bash
# Run in background
python automation/file_watcher.py --watch-dir . &
```

Auto-scans when files change.

### CI/CD Integration

Add to `.github/workflows/doc_id_check.yml`:

```yaml
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

## System Requirements

- **Python:** 3.7+
- **Dependencies:** `pyyaml` (optional, for registry parsing)
- **OS:** Windows, Linux, macOS

No other dependencies - uses Python standard library.

---

## Maintenance

### Daily
- Automated validation via pre-commit hook
- File watcher for real-time scanning

### Weekly
- Review coverage metrics
- Fix validation errors
- Categorize new files

### Monthly
- Full repository audit
- Update documentation
- Backup registry to git

---

## Production Status

This subsystem is **production-ready** and manages:

- **Source system:** 2,636 documents
- **Coverage:** 100% on Python, YAML, JSON
- **Uptime:** Active since 2025-12
- **Validation:** Comprehensive test suite

---

## Troubleshooting

### Registry not found
```bash
cd registry
cp DOC_ID_REGISTRY.yaml.template DOC_ID_REGISTRY.yaml
```

### Duplicate IDs detected
```bash
python validation/fix_duplicate_doc_ids.py
```

### Invalid format
```bash
python validation/fix_invalid_doc_ids.py
```

### Need help?
See `INTEGRATION_GUIDE.md` for detailed troubleshooting.

---

## License

Same license as eafix-modular project.

## Credits

**Source System:** ALL_AI Repository  
**Export Date:** 2026-01-09  
**Original System:** Doc ID System v3.0

---

## Next Steps

1. ✅ **Run setup:** `python setup.py`
2. 📖 **Read guide:** `INTEGRATION_GUIDE.md`
3. 🔍 **Initial scan:** See Quick Start above
4. 🎯 **Batch assign:** Process your files
5. ✅ **Validate:** Ensure quality

**Questions?** Check `docs/DOC_ID_SYSTEM_COMPLETE_SPECIFICATION.md` for complete technical details.

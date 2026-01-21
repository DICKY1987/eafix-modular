# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-Project Glossary is a comprehensive glossary governance framework for managing 83+ terms across 9 categories. The system provides:
- Term lifecycle management (proposed → draft → active → deprecated → archived)
- Single Source of Truth (SSOT) enforcement across documentation
- Automated validation and quality tracking (current score: 92%)
- Patch-based update workflows

## Commands

### Validation
```bash
# Full validation
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py

# Quick validation (structure only)
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py --quick

# Check orphaned terms
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py --check-orphans

# Verify implementation paths
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py --check-paths
```

### Term Updates
```bash
# Dry run (preview changes)
python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py --spec updates/add-schemas.yaml --dry-run

# Apply patch
python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py --spec updates/add-schemas.yaml --apply

# Single term update
python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py --term TERM-ENGINE-001 --field implementation.files --value "core/engine/orchestrator.py"

# Apply and validate
python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py --spec updates/add-schemas.yaml --apply --validate
```

## Architecture

### Key Files

| File | Purpose |
|------|---------|
| `DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml` | Machine-readable term registry (83+ terms, YAML) |
| `docs/DOC-GUIDE-GLOSSARY-SYSTEM-PLAN-910__GLOSSARY_SYSTEM_PLAN.md` | SSOT and generated artifact plan |
| `docs/DOC-GUIDE-GLOSSARY-665__glossary.md` | Generated human-readable glossary |
| `DOC-REGISTRY-TERM-ID-001__GLOSSARY_REGISTRY.yaml` | Generated term ID registry |
| `docs/DOC-GUIDE-DOC-GLOSSARY-GOVERNANCE-872__DOC_GLOSSARY_GOVERNANCE.md` | Governance framework and lifecycle policies |
| `docs/DOC-GUIDE-DOC-GLOSSARY-SCHEMA-873__DOC_GLOSSARY_SCHEMA.md` | JSON Schema for term structure |
| `docs/DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md` | Version history and change tracking |
| `schemas/DOC-CONFIG-GLOSSARY-PROCESS-STEPS-SCHEMA-302__GLOSSARY_PROCESS_STEPS_SCHEMA.yaml` | Process automation schema |

### Term Identification System

**Format**: `TERM-<CATEGORY>-<SEQUENCE>` (e.g., `TERM-ENGINE-001`)

**Categories**:
- `ENGINE` - Core Engine (23 terms)
- `PATCH` - Patch Management (8 terms)
- `ERROR` - Error Detection (10 terms)
- `SPEC` - Specifications (10 terms)
- `STATE` - State Management (8 terms)
- `INTEG` - Integrations (10 terms)
- `FRAME` - Framework (3 terms)
- `PM` - Project Management (4 terms)
- `ARCH` - Architecture (8 terms)

### Term Lifecycle

```
proposed → draft → active → deprecated → archived
    ↓         ↓       ↓
  rejected  rejected (updated)
```

### File Naming Convention

Files use DOC_ID prefixes: `DOC-<TYPE>-<CONTEXT>-<SEQ>__<name>.<ext>`

## Data Structures

### Term Schema (required fields)
- `term_id`: Unique identifier (pattern: `^TERM-[A-Z]+-[0-9]{3}$`)
- `name`: Display name (2-100 chars)
- `category`: One of 9 categories
- `definition`: 20-1000 characters, must start with type (Component/Process/Pattern)
- `status`: proposed | draft | active | deprecated | archived

### Validation Rules
- Definition length: 20-1000 characters
- Related terms: minimum 1 recommended
- Implementation paths must exist (verified by `--check-paths`)
- Cross-references must point to existing terms
- No orphaned terms (not linked by any other term)

## Dependencies

- Python 3.x
- PyYAML (`yaml` module)

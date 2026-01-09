# Adding New ID Types - Quick Start Guide

**Doc ID**: DOC-GUIDE-NEW-ID-TYPES-001  
**Status**: Complete  
**Last Updated**: 2026-01-03

---

## Overview

This guide shows you how to add a new stable ID type to the system in 1-4 weeks, leveraging the unified framework.

## Prerequisites

- Python 3.8+
- Access to repository
- Familiarity with existing ID types (doc_id, trigger_id, pattern_id)

---

## Step-by-Step Process

### Phase 1: Registration (1 hour)

#### 1.1 Register in Meta-Registry

```bash
python id_type_manager.py register \
  --type schema_id \
  --name "Schema Identifier" \
  --classification minted \
  --tier 2 \
  --format "SCHEMA-{TYPE}-{NAME}-{SEQ}" \
  --regex "^SCHEMA-([A-Z0-9]+)-([A-Z0-9-]+)-([0-9]{3,})$" \
  --priority high \
  --owner "Schema Governance" \
  --registry-file "data/schemas/SCHEMA_REGISTRY.yaml" \
  --description "Stable identifier for data schema definitions" \
  --categories "JSON,YAML,SQL,PROTO"
```

#### 1.2 Verify Registration

```bash
python id_type_manager.py info --type schema_id
```

---

### Phase 2: Scaffolding (30 minutes)

#### 2.1 Create Directory Structure

```bash
python id_type_manager.py scaffold --type schema_id
```

This creates:
```
schema_id/
├── 1_CORE_OPERATIONS/
├── 2_VALIDATION_FIXING/
├── 3_AUTOMATION_HOOKS/
├── 4_REPORTING_MONITORING/
├── 5_REGISTRY_DATA/
├── 6_TESTS/
├── 7_CLI_INTERFACE/
├── common/
├── docs/
├── README.md
└── DIR_MANIFEST.yaml
```

---

### Phase 3: Core Implementation (1-2 weeks)

#### 3.1 Create Validation Rules (`common/rules.py`)

```python
"""
doc_id: DOC-RULES-SCHEMA-ID-001
Schema ID validation rules
"""

import re

SCHEMA_ID_FORMAT = r'^SCHEMA-([A-Z0-9]+)-([A-Z0-9-]+)-([0-9]{3,})$'
SCHEMA_ID_PATTERN = re.compile(SCHEMA_ID_FORMAT)
VALID_CATEGORIES = ['JSON', 'YAML', 'SQL', 'PROTO']

def validate_schema_id_format(schema_id: str) -> tuple[bool, str]:
    """Validate schema_id format"""
    if not schema_id:
        return False, "schema_id cannot be empty"
    
    match = SCHEMA_ID_PATTERN.match(schema_id)
    if not match:
        return False, f"Invalid format. Expected: SCHEMA-{{TYPE}}-{{NAME}}-{{SEQ}}"
    
    type_cat, name, seq = match.groups()
    
    if type_cat not in VALID_CATEGORIES:
        return False, f"Invalid type '{type_cat}'. Must be one of: {', '.join(VALID_CATEGORIES)}"
    
    if len(seq) < 3:
        return False, f"Sequence number must be at least 3 digits"
    
    return True, ""

def format_schema_id(type_cat: str, name: str, sequence: int) -> str:
    """Format a schema_id"""
    seq_str = str(sequence).zfill(3)
    return f"SCHEMA-{type_cat.upper()}-{name.upper()}-{seq_str}"
```

#### 3.2 Implement Scanner (`1_CORE_OPERATIONS/schema_id_scanner.py`)

Use doc_id scanner as template - adapt for schema files.

#### 3.3 Implement Registry (`5_REGISTRY_DATA/SCHEMA_ID_REGISTRY.yaml`)

```yaml
---
doc_id: DOC-REGISTRY-SCHEMA-001
meta:
  version: 1.0.0
  created_utc: '2026-01-03T15:00:00Z'
  updated_utc: '2026-01-03T15:00:00Z'
  schema_version: 1.0.0
  total_schemas: 0
  description: Central registry for schema identities

categories:
  JSON:
    prefix: JSON
    description: JSON schemas
    next_id: 1
  YAML:
    prefix: YAML
    description: YAML schemas
    next_id: 1
  SQL:
    prefix: SQL
    description: SQL schemas
    next_id: 1
  PROTO:
    prefix: PROTO
    description: Protocol buffer schemas
    next_id: 1

schemas: []
```

---

### Phase 4: Validators (2-3 days)

Create 4-5 validators in `2_VALIDATION_FIXING/`:

1. **validate_schema_id_format.py** - Format compliance
2. **validate_schema_id_uniqueness.py** - No duplicates
3. **validate_schema_id_sync.py** - Registry ↔ filesystem sync
4. **validate_schema_id_references.py** - No broken references
5. **validate_schema_id_coverage.py** - Coverage metrics (optional)

**Copy templates from trigger_id or pattern_id validators.**

---

### Phase 5: Testing (2-3 days)

#### 5.1 Create Tests (`6_TESTS/test_schema_id.py`)

```python
"""
doc_id: DOC-TEST-SCHEMA-ID-001
Tests for schema_id system
"""

import pytest
from common.rules import validate_schema_id_format, format_schema_id

def test_valid_format():
    valid, msg = validate_schema_id_format("SCHEMA-JSON-USER-PROFILE-001")
    assert valid
    
def test_invalid_format():
    valid, msg = validate_schema_id_format("SCHEMA-INVALID")
    assert not valid
    
def test_format_schema_id():
    result = format_schema_id("JSON", "USER-PROFILE", 1)
    assert result == "SCHEMA-JSON-USER-PROFILE-001"
```

#### 5.2 Run Tests

```bash
pytest 6_TESTS/ -v
```

---

### Phase 6: Automation (2-3 days)

#### 6.1 Add to Unified Sync

Edit `sync_all_registries.py`:

```python
REGISTRY_CONFIGS = {
    # ... existing configs ...
    'schema_id': {
        'registry_file': 'data/schemas/SCHEMA_ID_REGISTRY.yaml',
        'inventory_file': 'data/schemas/schemas_inventory.jsonl',
        'scanner': 'schema_id/1_CORE_OPERATIONS/schema_id_scanner.py',
        'enabled': True
    }
}
```

#### 6.2 Add to Pre-Commit Hook

Edit `unified_pre_commit_hook.py` - add schema_id validators to list.

---

### Phase 7: Activation (1 day)

#### 7.1 Update Status

```bash
python id_type_manager.py update-status \
  --type schema_id \
  --status active \
  --notes "Scanner and validators implemented and tested"
```

#### 7.2 Run Full Validation

```bash
# Test all validators
python schema_id/2_VALIDATION_FIXING/validate_schema_id_format.py
python schema_id/2_VALIDATION_FIXING/validate_schema_id_uniqueness.py
python schema_id/2_VALIDATION_FIXING/validate_schema_id_sync.py
python schema_id/2_VALIDATION_FIXING/validate_schema_id_references.py

# Test unified sync
python sync_all_registries.py --type schema_id
```

#### 7.3 Promote to Production

```bash
python id_type_manager.py update-status \
  --type schema_id \
  --status production \
  --notes "All validators passing, ready for production use"
```

---

## Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **1. Registration** | 1 hour | Meta-registry entry |
| **2. Scaffolding** | 30 min | Directory structure |
| **3. Core Implementation** | 1-2 weeks | Scanner, registry, rules |
| **4. Validators** | 2-3 days | 4-5 validator scripts |
| **5. Testing** | 2-3 days | Test suite, coverage |
| **6. Automation** | 2-3 days | Sync, hooks, dashboard |
| **7. Activation** | 1 day | Status updates, validation |
| **TOTAL** | **1-3 weeks** | Fully operational ID type |

**Simple types**: 1-2 weeks  
**Complex types** (with special logic): 3-4 weeks

---

## Checklist

Use this checklist to track implementation:

- [ ] Registered in ID_TYPE_REGISTRY.yaml
- [ ] Directory structure scaffolded
- [ ] `common/rules.py` created with validation functions
- [ ] Scanner implemented in `1_CORE_OPERATIONS/`
- [ ] Registry YAML created in `5_REGISTRY_DATA/`
- [ ] Format validator implemented
- [ ] Uniqueness validator implemented
- [ ] Sync validator implemented
- [ ] Reference validator implemented
- [ ] Coverage validator implemented (if applicable)
- [ ] Tests created in `6_TESTS/`
- [ ] All tests passing
- [ ] Added to `sync_all_registries.py`
- [ ] Added to `unified_pre_commit_hook.py`
- [ ] README.md updated
- [ ] Documentation complete
- [ ] Status updated to "production"
- [ ] All validators passing 100%

---

## Quick Reference Commands

```bash
# Register new type
python id_type_manager.py register --type <TYPE> ...

# Scaffold structure
python id_type_manager.py scaffold --type <TYPE>

# Check status
python id_type_manager.py info --type <TYPE>

# List all types
python id_type_manager.py list

# Update status
python id_type_manager.py update-status --type <TYPE> --status <STATUS>

# Test sync
python sync_all_registries.py --type <TYPE>

# Run all validators
python unified_pre_commit_hook.py

# Validate meta-registry
python validate_id_type_registry.py
```

---

## Getting Help

- **Documentation**: See `STABLE_ID_UNIFIED_PROCESS.md`
- **Examples**: Study `doc_id`, `trigger_id`, or `pattern_id` implementations
- **Meta-Registry**: See `ID_TYPE_REGISTRY.yaml` for all registered types
- **Templates**: Use existing validators as templates

---

## Tips for Success

1. **Start simple** - Copy from existing ID type
2. **Test early** - Write tests before implementation
3. **Follow patterns** - Reuse existing validator structure
4. **Document as you go** - Update README.md continuously
5. **Validate often** - Run validators after each change
6. **Use the tools** - Leverage id_type_manager.py

---

**Remember**: The framework does most of the work. Focus on your unique business logic and validation rules.

---

**Status**: ✅ Complete  
**Last Review**: 2026-01-03  
**Next Review**: As needed

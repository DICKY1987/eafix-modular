# DOC_ID: DOC-SCRIPT-1083
# Glossary Term Identifier Usage Guide

**Type ID:** `term_id`  
**Classification:** natural

---

## Quick Start

### Generating Runtime IDs

```python
from scripts.automation.term_id_assigner import generate_term_id

new_id = generate_term_id()
print(new_id)  # TERM-XXX-NNN
```

---

## Validation

Validate the registry:

```bash
python scripts/validators/validate_term_id.py
```

---

## Registry Lookup

View all assigned IDs:

```bash
cat DOC-REGISTRY-TERM-ID-001__GLOSSARY_REGISTRY.yaml
```

---

## Integration

### Pre-commit Hook

Automatically validates on commit (if enabled in automation).

### CI/CD Pipeline

Add to `.github/workflows/`:

```yaml
- name: Validate Glossary Term Identifier
  run: python scripts/validators/validate_term_id.py
```

---

**Last Updated:** 2026-01-04

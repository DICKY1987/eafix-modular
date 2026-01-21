# DOC_ID: DOC-SCRIPT-1081
# Glossary Term Identifier Registry

**Type ID:** `term_id`  
**Classification:** natural  
**Owner:** Glossary Team  
**Status:** Active

---

## Overview

Stable identifier for glossary terms (TERM-<CATEGORY>-<SEQUENCE> format)

**Format:** `TERM-<CATEGORY>-<SEQUENCE>`

This registry is generated from `DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml` and should not be edited manually.

## Categories

*No categories defined*

---

## Registry Structure

```yaml
term_ids:
  - id: <TERM-XXX-NNN>
    name: <human_readable_name>
    status: active
    created_utc: <ISO8601_timestamp>
    categories: [<category_list>]
```

---

## Usage

### Minting a New Glossary Term Identifier


---

## Validation

This registry is validated by:
- Format validator (regex: `^TERM-[A-Z]+-[0-9]{3}$`)
- Uniqueness validator
- Sync validator (registry ↔ filesystem)

---

## Automation

*No automation configured*

---

## References

- **ID Type Registry:** `RUNTIME/doc_id/SUB_DOC_ID/ID_TYPE_REGISTRY.yaml`
- **Governance:** `.ai/governance.md`
- **Universal Registry Schema:** `CONTEXT/docs/reference/UNIVERSAL_REGISTRY_SCHEMA_REFERENCE.md`

---

**Last Updated:** 2026-01-04

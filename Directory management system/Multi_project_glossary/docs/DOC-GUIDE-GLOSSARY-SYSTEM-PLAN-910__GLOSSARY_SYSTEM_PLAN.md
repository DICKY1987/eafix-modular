<!-- DOC_LINK: DOC-GUIDE-GLOSSARY-SYSTEM-PLAN-910 -->
---
doc_id: DOC-GUIDE-GLOSSARY-SYSTEM-PLAN-910
status: draft
doc_type: guide
---

# Glossary System Plan

## Purpose

Define the target glossary structure and artifacts to eliminate drift. The SSOT is YAML, and all other glossary artifacts are generated from it.

## Source of Truth (SSOT)

Path:
- `Directory management system\Multi_project_glossary\DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml`

Rules:
- SSOT is the only file edited by humans.
- Term IDs must follow `TERM-<CATEGORY>-<SEQUENCE>` (example: `TERM-ENGINE-001`).
- Remove `statistics` and `quality` blocks entirely to avoid churn.

### Term Record Shape (SSOT)

Required fields:
- `term_id` (key in `terms`)
- `name`
- `category`
- `status`
- `definition`
- `added_date`
- `added_by`
- `last_modified`

Optional fields:
- `modified_by`
- `aliases`
- `types`
- `implementation`
- `schema_refs`
- `config_refs`
- `usage_examples`
- `related_terms`
- `patch_history`
- `deprecation`

Example:
```yaml
schema_version: "1.0.0"
last_updated: "2026-01-20T00:00:00Z"
total_terms: 83
terms:
  TERM-ENGINE-001:
    name: "Orchestrator"
    category: "Core Engine"
    status: "active"
    definition: |
      Component that coordinates workstream execution, dependency resolution,
      and worker assignment across the pipeline.
    added_date: "2025-11-20"
    added_by: "architecture-team"
    last_modified: "2025-11-23T14:30:00Z"
    modified_by: "automation"
    aliases:
      - "Workstream Orchestrator"
    implementation:
      files:
        - "core/engine/orchestrator.py"
    related_terms:
      - term_id: "TERM-ENGINE-002"
        relationship: "uses"
```

## Generated Artifacts

### 1) Human Glossary (Markdown)

Path:
- `Directory management system\Multi_project_glossary\docs\DOC-GUIDE-GLOSSARY-665__glossary.md`

Rules:
- Generated from SSOT, never edited manually.
- Terms ordered alphabetically by name and grouped by A-Z headings.
- Required sections:
  - `# Glossary`
  - `## A` (and other letters as needed)
  - `## Index by Category`
  - `## Quick Reference`
  - `## See Also`

Term entry template:
```
### Term Name
**Term ID**: TERM-XXX-NNN
**Category**: Category Name
**Definition**: ...
```

Include optional sections only when data exists in SSOT (Implementation, Examples, Related Terms).

### 2) Term ID Registry (YAML)

Path:
- `Directory management system\Multi_project_glossary\DOC-REGISTRY-TERM-ID-001__GLOSSARY_REGISTRY.yaml`

Rules:
- Generated from SSOT, never edited manually.
- `term_ids` list is derived from SSOT terms.
- `created_utc` is derived from `added_date` (if date-only, set time to `T00:00:00Z`).

Registry template:
```yaml
meta:
  version: 1.0.0
  created_utc: "<generation time>"
  updated_utc: "<generation time>"
  total_entries: <count>
  owner: Glossary Team
  description: Stable identifier for glossary terms (TERM-<CATEGORY>-<SEQUENCE> format)
term_ids:
  - id: TERM-ENGINE-001
    name: Orchestrator
    status: active
    created_utc: "2025-11-20T00:00:00Z"
    categories:
      - Core Engine
```

## Editing Workflow

1. Edit SSOT YAML only.
2. Run generator to update glossary markdown and term_id registry.
3. Validate output (glossary structure + term_id format).
4. Commit SSOT and generated artifacts together.

## Non-Goals

- No metrics or reports are generated as standalone artifacts.
- No manual edits to generated files.

<!-- DOC_LINK: DOC-GUIDE-DOC-GLOSSARY-SCHEMA-873 -->
---
status: draft
doc_type: guide
module_refs: []
script_refs: []
doc_id: DOC-GUIDE-DOC-GLOSSARY-SCHEMA-873
---

# Glossary Term Schema

**Doc ID**: `DOC-GLOSSARY-SCHEMA-001`
**Version**: 1.0.0
**Last Updated**: 2025-11-25
**Status**: ACTIVE
**Owner**: Architecture Team

---

## Purpose

Defines the canonical schema for glossary terms, including:
- Term structure and required fields
- Metadata format
- Validation rules
- Templates for common term types

---

## Term Schema (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://schema.pipeline.dev/glossary/term.v1.json",
  "title": "Glossary Term",
  "description": "Schema for a glossary term entry",
  "type": "object",
  "required": ["term_id", "name", "category", "definition", "status"],
  "properties": {
    "term_id": {
      "type": "string",
      "pattern": "^TERM-[A-Z]+-[0-9]{3}$",
      "description": "Unique term identifier",
      "examples": ["TERM-ENGINE-001", "TERM-PATCH-005"]
    },
    "name": {
      "type": "string",
      "minLength": 2,
      "maxLength": 100,
      "description": "Display name of the term"
    },
    "category": {
      "type": "string",
      "enum": [
        "Core Engine",
        "Patch Management",
        "Error Detection",
        "Specifications",
        "State Management",
        "Integrations",
        "Framework",
        "Project Management"
      ],
      "description": "Primary category for term organization"
    },
    "definition": {
      "type": "string",
      "minLength": 20,
      "maxLength": 1000,
      "description": "Clear, concise definition of the term"
    },
    "status": {
      "type": "string",
      "enum": ["proposed", "draft", "active", "deprecated", "archived"],
      "description": "Current lifecycle status"
    },
    "aliases": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Alternative names or synonyms"
    },
    "types": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "description"],
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"}
        }
      },
      "description": "Variants or subtypes of this term"
    },
    "implementation": {
      "type": "object",
      "properties": {
        "files": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Source files implementing this concept"
        },
        "line_ranges": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "file": {"type": "string"},
              "start_line": {"type": "integer"},
              "end_line": {"type": "integer"}
            }
          }
        },
        "entry_points": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Main functions or classes"
        }
      }
    },
    "schema_refs": {
      "type": "array",
      "items": {"type": "string"},
      "description": "JSON Schema files defining this concept"
    },
    "config_refs": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Configuration files for this concept"
    },
    "usage_examples": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["language", "code"],
        "properties": {
          "language": {"type": "string"},
          "code": {"type": "string"},
          "description": {"type": "string"}
        }
      }
    },
    "related_terms": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["term_id", "relationship"],
        "properties": {
          "term_id": {"type": "string"},
          "relationship": {
            "type": "string",
            "enum": [
              "uses",
              "used_by",
              "depends_on",
              "required_by",
              "implements",
              "implemented_by",
              "extends",
              "extended_by",
              "related"
            ]
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["added_date", "added_by", "last_modified"],
      "properties": {
        "added_date": {
          "type": "string",
          "format": "date"
        },
        "added_by": {
          "type": "string"
        },
        "last_modified": {
          "type": "string",
          "format": "date-time"
        },
        "modified_by": {
          "type": "string"
        },
        "review_date": {
          "type": "string",
          "format": "date"
        },
        "reviewers": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "patch_history": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["patch_id", "action", "date"],
        "properties": {
          "patch_id": {"type": "string"},
          "action": {
            "type": "string",
            "enum": [
              "added",
              "updated_definition",
              "updated_implementation",
              "updated_examples",
              "deprecated",
              "archived"
            ]
          },
          "date": {"type": "string", "format": "date-time"},
          "description": {"type": "string"}
        }
      }
    },
    "deprecation": {
      "type": "object",
      "properties": {
        "date": {"type": "string", "format": "date"},
        "reason": {"type": "string"},
        "replacement_term_id": {"type": "string"},
        "migration_guide": {"type": "string"}
      }
    }
  }
}
```

---

## Metadata Schema

**File**: `DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml`

```yaml
# Glossary Metadata
# This file tracks term lifecycle and machine-readable data
# DO NOT EDIT MANUALLY - Use scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py

schema_version: "1.0.0"
last_updated: "2025-11-25T00:00:00Z"
total_terms: 75

terms:
  TERM-ENGINE-001:
    name: "Orchestrator"
    category: "Core Engine"
    status: "active"
    added_date: "2025-11-20"
    added_by: "architecture-team"
    last_modified: "2025-11-23T14:30:00Z"
    modified_by: "automation"

    aliases:
      - "Workstream Orchestrator"
      - "Job Orchestrator"

    implementation:
      files:
        - "core/engine/orchestrator.py"
        - "engine/orchestrator/orchestrator.py"
      entry_points:
        - "Orchestrator.run_workstream()"
        - "Orchestrator.execute_bundle()"

    schema_refs:
      - "schema/workstream.schema.json"
      - "schema/uet/execution_request.v1.json"

    config_refs:
      - "config/orchestrator.yaml"

    related_terms:
      - term_id: "TERM-ENGINE-002"
        relationship: "uses"
      - term_id: "TERM-ENGINE-015"
        relationship: "uses"
      - term_id: "TERM-STATE-003"
        relationship: "depends_on"

    patch_history:
      - patch_id: "01J2ZB1B3Y5D0C8QK7F3HA2XYZ"
        action: "added"
        date: "2025-11-20T10:00:00Z"
        description: "Initial term creation"
      - patch_id: "01J3AC9F2X4E1D9RL8G4JB3CDE"
        action: "updated_implementation"
        date: "2025-11-23T14:30:00Z"
        description: "Added entry point references"

  TERM-PATCH-001:
    name: "Patch Artifact"
    category: "Patch Management"
    status: "active"
    # ... (similar structure)

categories:
  "Core Engine":
    code: "ENGINE"
    description: "Execution orchestration components"
    term_count: 23
  "Patch Management":
    code: "PATCH"
    description: "Patch lifecycle and validation"
    term_count: 8
  # ...

statistics:
  by_status:
    active: 72
    deprecated: 3
    draft: 2
    proposed: 1
    archived: 0
  by_category:
    "Core Engine": 23
    "Patch Management": 8
    "Error Detection": 10
    # ...
  orphaned_terms: []
  avg_related_terms: 3.2
```

---

## Validation Rules

### Required Fields

**All Terms MUST Have**:
1. `term_id` - Unique identifier
2. `name` - Display name
3. `category` - Category assignment
4. `definition` - Clear definition (20-1000 chars)
5. `status` - Lifecycle status
6. `metadata.added_date` - Creation date
7. `metadata.added_by` - Creator

### Optional But Recommended

**Terms SHOULD Have**:
- At least 2 `related_terms`
- At least 1 `implementation.files` (if code-based)
- At least 1 `usage_examples` (for complex concepts)
- `schema_refs` (if schema-driven)

### Quality Constraints

```yaml
# config/DOC-CONFIG-GLOSSARY-POLICY-055__glossary_policy.yaml

validation:
  definition:
    min_length: 20
    max_length: 1000
    required_patterns:
      - "\\b(Component|Process|Pattern|System|Tool|Mechanism)\\b"  # Starts with type
    forbidden_patterns:
      - "^It is"  # Avoid weak starts
      - "^This is"
      - "\\bTODO\\b"  # No incomplete definitions

  related_terms:
    min_count: 1
    max_count: 10
    require_bidirectional: true  # If A links to B, B should link to A

  implementation:
    verify_files_exist: true
    verify_entry_points_exist: true

  cross_references:
    max_orphaned_terms: 0
    max_dead_links: 0

  naming:
    max_length: 100
    forbidden_chars: ["#", "$", "%"]
    case_style: "title"  # Title Case
```

---

## Term Templates

### Core Engine Component

```yaml
term_id: "TERM-ENGINE-XXX"
name: "Component Name"
category: "Core Engine"
status: "active"

definition: |
  Component that [primary responsibility]. [Key behavior or pattern].

types:
  - name: "Variant A"
    description: "Specific implementation for X"
  - name: "Variant B"
    description: "Specific implementation for Y"

implementation:
  files:
    - "core/engine/component.py"
  entry_points:
    - "ComponentClass.__init__()"
    - "ComponentClass.execute()"

schema_refs:
  - "schema/component.schema.json"

config_refs:
  - "config/component.yaml"

usage_examples:
  - language: "python"
    code: |
      from core.engine.component import Component
      comp = Component(config)
      result = comp.execute(task)
    description: "Basic usage pattern"

related_terms:
  - term_id: "TERM-ENGINE-001"
    relationship: "uses"
  - term_id: "TERM-STATE-003"
    relationship: "depends_on"

metadata:
  added_date: "2025-11-25"
  added_by: "developer-name"
  last_modified: "2025-11-25T00:00:00Z"
```

### Error Detection Concept

```yaml
term_id: "TERM-ERROR-XXX"
name: "Error Concept"
category: "Error Detection"
status: "active"

definition: |
  Process of [error handling behavior]. [Key mechanism].

implementation:
  files:
    - "error/engine/concept.py"
    - "error/plugins/*/plugin.py"
  entry_points:
    - "ErrorEngine.detect()"
    - "Plugin.parse()"

usage_examples:
  - language: "python"
    code: |
      from error.engine.error_engine import ErrorEngine
      engine = ErrorEngine()
      errors = engine.detect(file_path)
    description: "Detect errors in a file"

related_terms:
  - term_id: "TERM-ERROR-001"
    relationship: "implements"
  - term_id: "TERM-ERROR-005"
    relationship: "uses"

metadata:
  added_date: "2025-11-25"
  added_by: "developer-name"
  last_modified: "2025-11-25T00:00:00Z"
```

### Framework/Pattern Concept

```yaml
term_id: "TERM-FRAME-XXX"
name: "Pattern Name"
category: "Framework"
status: "active"

definition: |
  [Design pattern/architectural concept] that [purpose and benefit].

types:
  - name: "Implementation A"
    description: "Used in [context]"
  - name: "Implementation B"
    description: "Used in [context]"

implementation:
  files:
    - "core/patterns/pattern.py"
  entry_points:
    - "pattern_function()"

schema_refs:
  - "schema/uet/pattern.v1.json"

usage_examples:
  - language: "python"
    code: |
      # Example implementation
      pattern = Pattern()
      result = pattern.apply(data)
    description: "Applying the pattern"

related_terms:
  - term_id: "TERM-FRAME-001"
    relationship: "extends"
  - term_id: "TERM-ENGINE-010"
    relationship: "implemented_by"

metadata:
  added_date: "2025-11-25"
  added_by: "architecture-team"
  last_modified: "2025-11-25T00:00:00Z"
```

### Deprecated Term

```yaml
term_id: "TERM-OLD-XXX"
name: "Legacy Concept"
category: "Core Engine"
status: "deprecated"

definition: |
  ⚠️ **DEPRECATED**: [Original definition]. Use [new term] instead.

deprecation:
  date: "2025-11-01"
  reason: "Replaced by improved implementation"
  replacement_term_id: "TERM-NEW-XXX"
  migration_guide: |
    Replace all instances of:
    ```python
    from old.module import OldClass
    ```
    With:
    ```python
    from new.module import NewClass
    ```

implementation:
  files:
    - "legacy/old_module.py"  # Still exists for compatibility

related_terms:
  - term_id: "TERM-NEW-XXX"
    relationship: "replaced_by"

metadata:
  added_date: "2025-09-01"
  added_by: "original-dev"
  last_modified: "2025-11-01T00:00:00Z"
  modified_by: "architecture-team"

patch_history:
  - patch_id: "01J2..."
    action: "added"
    date: "2025-09-01T00:00:00Z"
  - patch_id: "01J5..."
    action: "deprecated"
    date: "2025-11-01T00:00:00Z"
    description: "Marked as deprecated, migration path added"
```

---

## Field Definitions

### term_id
**Type**: String
**Pattern**: `TERM-<CATEGORY>-<SEQUENCE>`
**Required**: Yes
**Purpose**: Unique, stable identifier for tracking and automation

### name
**Type**: String (2-100 chars)
**Required**: Yes
**Purpose**: Human-readable display name
**Style**: Title Case

### category
**Type**: Enum
**Required**: Yes
**Values**: Core Engine, Patch Management, Error Detection, Specifications, State Management, Integrations, Framework, Project Management
**Purpose**: Primary organization and indexing

### definition
**Type**: String (20-1000 chars)
**Required**: Yes
**Purpose**: Clear, concise explanation
**Style**: Start with type (Component/Process/Pattern), present tense, technical precision

### status
**Type**: Enum
**Required**: Yes
**Values**: proposed, draft, active, deprecated, archived
**Purpose**: Lifecycle tracking

### aliases
**Type**: Array of strings
**Required**: No
**Purpose**: Alternative names, synonyms, common misspellings

### types
**Type**: Array of {name, description}
**Required**: No
**Purpose**: Document variants or subtypes

### implementation
**Type**: Object {files, line_ranges, entry_points}
**Required**: No (but recommended for code concepts)
**Purpose**: Link to actual code

### schema_refs
**Type**: Array of file paths
**Required**: No
**Purpose**: Link to JSON Schema definitions

### usage_examples
**Type**: Array of {language, code, description}
**Required**: No (but recommended for complex concepts)
**Purpose**: Show practical usage

### related_terms
**Type**: Array of {term_id, relationship}
**Required**: At least 1 recommended
**Purpose**: Cross-referencing and navigation

### metadata
**Type**: Object {added_date, added_by, last_modified, ...}
**Required**: Yes
**Purpose**: Tracking provenance and history

### patch_history
**Type**: Array of {patch_id, action, date, description}
**Required**: No
**Purpose**: Audit trail of changes

---

## Relationship Types

| Relationship | Meaning | Example |
|-------------|---------|---------|
| `uses` | A uses/invokes B | Orchestrator uses Executor |
| `used_by` | A is used by B | Executor used_by Orchestrator |
| `depends_on` | A requires B to function | Orchestrator depends_on Database |
| `required_by` | A is required by B | Database required_by Orchestrator |
| `implements` | A implements pattern/interface B | AiderAdapter implements Adapter |
| `implemented_by` | A is implemented by B | Adapter implemented_by AiderAdapter |
| `extends` | A extends/inherits from B | Worker extends BaseWorker |
| `extended_by` | A is extended by B | BaseWorker extended_by Worker |
| `related` | General association | Circuit Breaker related Retry Logic |

---

## Validation Examples

### Valid Term

```yaml
term_id: "TERM-ENGINE-001"
name: "Orchestrator"
category: "Core Engine"
status: "active"
definition: "Component that coordinates workstream execution, dependency resolution, and worker assignment across the pipeline."

implementation:
  files: ["core/engine/orchestrator.py"]
  entry_points: ["Orchestrator.run_workstream()"]

related_terms:
  - term_id: "TERM-ENGINE-002"
    relationship: "uses"

metadata:
  added_date: "2025-11-20"
  added_by: "arch-team"
  last_modified: "2025-11-20T00:00:00Z"
```

✅ **Passes Validation**

### Invalid Term - Missing Required Fields

```yaml
term_id: "TERM-ENGINE-002"
name: "Executor"
# ❌ Missing: category, definition, status, metadata
```

❌ **Validation Error**: Missing required fields

### Invalid Term - Poor Definition

```yaml
term_id: "TERM-ENGINE-003"
name: "Scheduler"
category: "Core Engine"
status: "active"
definition: "It schedules stuff."  # ❌ Too short, unclear, poor style

metadata:
  added_date: "2025-11-20"
  added_by: "developer"
  last_modified: "2025-11-20T00:00:00Z"
```

❌ **Validation Error**: Definition too short (< 20 chars), lacks technical precision

---

## Related Documents

- **[DOC-GUIDE-DOC-GLOSSARY-GOVERNANCE-872__DOC_GLOSSARY_GOVERNANCE.md](DOC-GUIDE-DOC-GLOSSARY-GOVERNANCE-872__DOC_GLOSSARY_GOVERNANCE.md)** - Governance and processes
- **[DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md](DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md)** - Update history
- **[DOC-GUIDE-GLOSSARY-665__glossary.md](DOC-GUIDE-GLOSSARY-665__glossary.md)** - Main glossary

---

**Document Status**: ACTIVE
**Next Review**: 2025-12-25
**Maintained By**: Architecture Team
**Version**: 1.0.0

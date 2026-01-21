<!-- DOC_LINK: DOC-GUIDE-DOC-GLOSSARY-GOVERNANCE-872 -->
---
status: draft
doc_type: guide
module_refs: []
script_refs: []
doc_id: DOC-GUIDE-DOC-GLOSSARY-GOVERNANCE-872
---

# Glossary Governance Framework

**Doc ID**: `DOC-GLOSSARY-GOV-001`
**Version**: 1.0.0
**Last Updated**: 2025-11-25
**Status**: ACTIVE
**Owner**: Architecture Team

---

## Purpose

This document defines the governance framework for maintaining the repository glossary, including:
- Glossary structure and schema
- Term identification and lifecycle
- Update mechanisms (manual and patch-based)
- Quality standards and refinement processes
- Automation and tooling

---

## Table of Contents

1. [Glossary Structure](#glossary-structure)
2. [Term Identification System](#term-identification-system)
3. [Term Lifecycle](#term-lifecycle)
4. [Update Mechanisms](#update-mechanisms)
5. [Quality Standards](#quality-standards)
6. [Refinement Process](#refinement-process)
7. [Automation](#automation)
8. [Related Documents](#related-documents)

---

## Glossary Structure

### File Organization

```
DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml  # SSOT term registry
DOC-REGISTRY-TERM-ID-001__GLOSSARY_REGISTRY.yaml           # Generated term ID registry
docs/
  DOC-GUIDE-GLOSSARY-665__glossary.md                      # Generated glossary
  DOC-GUIDE-DOC-GLOSSARY-GOVERNANCE-872__DOC_GLOSSARY_GOVERNANCE.md  # This document (governance)
  DOC-GUIDE-DOC-GLOSSARY-SCHEMA-873__DOC_GLOSSARY_SCHEMA.md          # Term schema definition
  DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md    # Update history
  DOC-GUIDE-GLOSSARY-SYSTEM-PLAN-910__GLOSSARY_SYSTEM_PLAN.md        # SSOT plan
scripts/
  DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py     # Validation tool
  DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py                 # Patch-based term updates
  generate_glossary.py                                               # Glossary generator (planned)
  generate_glossary_index.py                                         # Generate term index
config/
  DOC-CONFIG-GLOSSARY-POLICY-055__glossary_policy.yaml               # Validation rules
```

### Glossary Document Structure

The main `docs/DOC-GUIDE-GLOSSARY-665__glossary.md` follows this canonical structure:

```markdown
# Glossary – AI Development Pipeline

**Metadata Section**
- Last Updated
- Purpose
- Audience
- Navigation links
- Related Documents

**Alphabetical Term Sections** (A-Z)
## A
### Term Name
- Category
- Definition
- [Optional] Types/Variants
- [Optional] Implementation
- [Optional] Schema
- [Optional] Usage/Examples
- Related Terms

**Category Index**
Groups terms by functional category

**Quick Reference**
Common commands and lookups

**See Also**
Cross-references to other docs
```

---

## Term Identification System

### Term ID Format

Every glossary term has a unique identifier for tracking and automation:

**Format**: `TERM-<CATEGORY>-<SEQUENCE>`

**Examples**:
- `TERM-ENGINE-001` → Orchestrator
- `TERM-PATCH-005` → Patch Artifact
- `TERM-ERROR-010` → Error Plugin
- `TERM-STATE-003` → Pipeline Database

### Category Codes

| Code | Category | Description |
|------|----------|-------------|
| `ENGINE` | Core Engine | Execution orchestration components |
| `PATCH` | Patch Management | Patch lifecycle and validation |
| `ERROR` | Error Detection | Error detection and recovery |
| `SPEC` | Specifications | Spec management and tooling |
| `STATE` | State Management | Database and state tracking |
| `INTEG` | Integrations | External tool integrations |
| `FRAME` | Framework | UET and foundational concepts |
| `PM` | Project Management | CCPM and planning |

### Term Metadata

Each term maintains hidden metadata (not visible in user-facing glossary):

```yaml
# DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml
terms:
  TERM-ENGINE-001:
    name: "Orchestrator"
    category: "Core Engine"
    added_date: "2025-11-20"
    added_by: "architecture-team"
    last_modified: "2025-11-23"
    status: "active"
    aliases: ["Workstream Orchestrator", "Job Orchestrator"]
    implementation_files:
      - "core/engine/orchestrator.py"
      - "engine/orchestrator/orchestrator.py"
    schema_refs:
      - "schema/workstream.schema.json"
    related_term_ids:
      - TERM-ENGINE-002  # Executor
      - TERM-ENGINE-015  # Scheduler
    patch_history:
      - patch_id: "01J2ZB..."
        action: "added"
        date: "2025-11-20"
      - patch_id: "01J3AC..."
        action: "updated_definition"
        date: "2025-11-23"
```

### Term Status Values

- **`active`** - Current, in-use term
- **`deprecated`** - Still documented but discouraged
- **`archived`** - Historical, no longer relevant
- **`proposed`** - Under review, not yet official
- **`draft`** - Being developed

---

## Term Lifecycle

### Lifecycle States

```
proposed → draft → active → deprecated → archived
    ↓         ↓       ↓
  rejected  rejected (updated)
```

### State Transitions

#### 1. Proposal
**Trigger**: New concept introduced in code or docs

**Actions**:
- Create term proposal in `DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml`
- Assign term ID
- Set status = `proposed`
- Draft initial definition

**Approval**: Architecture team review

#### 2. Drafting
**Trigger**: Proposal approved

**Actions**:
- Write full definition
- Add implementation references
- Create examples
- Link related terms
- Set status = `draft`

**Review**: Peer review for clarity and accuracy

#### 3. Activation
**Trigger**: Draft reviewed and approved

**Actions**:
- Generate `docs/DOC-GUIDE-GLOSSARY-665__glossary.md` from SSOT
- Update category index
- Update cross-references
- Set status = `active`
- Announce in changelog

#### 4. Deprecation
**Trigger**: Concept being phased out

**Actions**:
- Mark with ⚠️ DEPRECATED notice
- Add migration guidance
- Set status = `deprecated`
- Keep in glossary for 2+ releases

#### 5. Archival
**Trigger**: Concept fully removed from codebase

**Actions**:
- Move to `docs/glossary_archive.md`
- Add archive notice with removal date
- Set status = `archived`
- Remove from main glossary

---

## Update Mechanisms

### Manual Updates

**When**: Small edits, clarifications, typo fixes

**Process**:
1. Edit `DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml` directly
2. Update `last_modified` in SSOT
3. Add entry to `docs/DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md`
4. Generate `docs/DOC-GUIDE-GLOSSARY-665__glossary.md` and `DOC-REGISTRY-TERM-ID-001__GLOSSARY_REGISTRY.yaml` (see plan doc)
5. Run `python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py`
6. Commit with message: `docs(glossary): <description>`

### Patch-Based Updates

**When**: Systematic updates across multiple terms, automated changes

**Process**:
1. Create patch specification:
   ```yaml
   # updates/update-001.yaml
   patch_id: "01J4XY..."
   description: "Add implementation paths to all Core Engine terms"
   terms:
     - term_id: TERM-ENGINE-001
       action: update
       field: implementation
       value: "core/engine/orchestrator.py"
     - term_id: TERM-ENGINE-002
       action: update
       field: implementation
       value: "core/engine/executor.py"
   ```

2. Generate patch:
   ```bash
   python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py --spec updates/update-001.yaml
   ```

3. Review generated diff

4. Apply patch:
   ```bash
   git apply updates/update-001.patch
   ```

5. Validate:
   ```bash
   python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py
   ```

6. Update metadata and changelog

### Automated Extraction

**When**: Syncing glossary with code changes

**Process**:
1. Scan code for new terms:
   ```bash
   python scripts/generate_glossary.py --ssot DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml
   ```

2. Tool outputs proposed terms:
   ```yaml
   proposed_terms:
     - name: "Circuit Breaker"
       category: "Core Engine"
       source_file: "core/engine/circuit_breakers.py"
       definition_hint: "Resilience pattern that prevents cascading failures"
       confidence: 0.85
   ```

3. Review and approve proposals

4. Automated tool adds to metadata as `proposed`

5. Architecture team reviews and promotes to `draft`

---

## Quality Standards

### Definition Quality

**Required Elements**:
- ✅ Clear, concise definition (1-3 sentences)
- ✅ Category assignment
- ✅ At least one related term
- ✅ Implementation location (if applicable)

**Optional but Recommended**:
- Examples (code or usage)
- Schema references
- Type variants
- Common patterns

### Definition Style

**✅ Good Definitions**:
- Start with "Component that...", "Process of...", "Pattern for..."
- Use present tense
- Avoid circular definitions
- Define acronyms on first use
- Use technical precision

**❌ Poor Definitions**:
- Vague: "Thing that helps with orchestration"
- Circular: "Orchestrator is what orchestrates"
- Too verbose: Multi-paragraph definitions
- Missing context: Assumes too much prior knowledge

### Cross-Reference Quality

**Every term should**:
- Link to 2-5 related terms
- Be linked FROM at least 1 other term
- Have bidirectional relationships
- Avoid orphaned terms

**Validation**:
```bash
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py --check-orphans
```

---

## Refinement Process

### Continuous Improvement

**Monthly Review** (Architecture Team):
1. Review terms added/updated in past month
2. Check for inconsistencies
3. Update obsolete definitions
4. Improve clarity based on feedback

**Quarterly Audit**:
1. Validate all implementation paths still exist
2. Check for missing new concepts
3. Remove truly obsolete archived terms
4. Update category organization

### Community Refinement

**Feedback Mechanisms**:
- GitHub issues with label `glossary-feedback`
- Inline comments in PRs
- Architecture team discussions

**Feedback Template**:
```markdown
### Glossary Feedback: [Term Name]

**Term ID**: TERM-XXX-NNN
**Issue Type**: [unclear | incorrect | missing | improvement]

**Current Definition**:
[Quote current definition]

**Proposed Change**:
[Your suggested improvement]

**Rationale**:
[Why this change improves clarity/accuracy]
```

### Metrics

Track glossary health:
```yaml
metrics:
  total_terms: 75
  active_terms: 72
  deprecated_terms: 3
  orphaned_terms: 0  # Target: 0
  terms_without_implementation: 5
  avg_related_terms_per_term: 3.2
  terms_added_this_month: 4
  terms_updated_this_month: 12
```

---

## Automation

### Validation Tool

**Location**: `scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py`

**Checks**:
```python
def validate_glossary():
    """Validate glossary structure and content."""
    errors = []

    # Structure checks
    errors += check_alphabetical_order()
    errors += check_heading_levels()
    errors += check_required_sections()

    # Content checks
    errors += check_term_definitions()
    errors += check_category_assignments()
    errors += check_implementation_paths()

    # Cross-reference checks
    errors += check_related_terms_exist()
    errors += check_orphaned_terms()
    errors += check_broken_links()

    # Metadata checks
    errors += validate_term_ids()
    errors += check_metadata_sync()

    return errors
```

**Usage**:
```bash
# Validate all
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py

# Check specific aspect
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py --check-orphans
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py --check-paths
```

### Index Generation

**Location**: `scripts/generate_glossary_index.py`

**Outputs**:
- `docs/glossary_index.json` - Machine-readable term index
- `docs/glossary_graph.dot` - Term relationship graph

**Usage**:
```bash
python scripts/generate_glossary_index.py
```

### Patch Generation

**Location**: `scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py`

**Capabilities**:
- Bulk term updates
- Schema-driven changes
- Atomic multi-term patches
- Rollback support

**Example**:
```bash
# Update single term
python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py \
  --term TERM-ENGINE-001 \
  --field implementation \
  --value "core/engine/orchestrator.py"

# Bulk update from spec
python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py \
  --spec updates/add-schemas.yaml \
  --dry-run  # Preview changes
```

---

## Schema Definition

See **[DOC-GUIDE-DOC-GLOSSARY-SCHEMA-873__DOC_GLOSSARY_SCHEMA.md](DOC-GUIDE-DOC-GLOSSARY-SCHEMA-873__DOC_GLOSSARY_SCHEMA.md)** for:
- Term schema (JSON Schema)
- Metadata schema
- Validation rules
- Example templates

---

## Changelog

See **[DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md](DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md)** for:
- Term addition history
- Update log
- Deprecation notices
- Archive events

---

## Related Documents

### Core References
- **[DOC-GUIDE-GLOSSARY-665__glossary.md](DOC-GUIDE-GLOSSARY-665__glossary.md)** - Main glossary (user-facing)
- **[DOC-GUIDE-GLOSSARY-SYSTEM-PLAN-910__GLOSSARY_SYSTEM_PLAN.md](DOC-GUIDE-GLOSSARY-SYSTEM-PLAN-910__GLOSSARY_SYSTEM_PLAN.md)** - SSOT and generation plan
- **[DOC-GUIDE-DOC-GLOSSARY-SCHEMA-873__DOC_GLOSSARY_SCHEMA.md](DOC-GUIDE-DOC-GLOSSARY-SCHEMA-873__DOC_GLOSSARY_SCHEMA.md)** - Term schema definition
- **[DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md](DOC-GUIDE-DOC-GLOSSARY-CHANGELOG-871__DOC_GLOSSARY_CHANGELOG.md)** - Update history

### Related Documentation
- **[DOC_DOCUMENTATION_INDEX.md](DOC_DOCUMENTATION_INDEX.md)** - All documentation
- **[DOC_IMPLEMENTATION_LOCATIONS.md](DOC_IMPLEMENTATION_LOCATIONS.md)** - Code locations
- **[DOC_ARCHITECTURE.md](DOC_ARCHITECTURE.md)** - System architecture

### Tool Documentation
- **Validation Tool**: `docs/DOC-GUIDE-GLOSSARY-PROCESS-DOCS-README-292__GLOSSARY_PROCESS_DOCS_README.md`
- **Patch Tool**: `scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py --help`
- **Generate Tool**: `scripts/generate_glossary.py --help`

---

## Quick Reference

### Common Commands

```bash
# Validate glossary
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py

# Add new term (interactive)
python scripts/add_term.py

# Update term
python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py --term TERM-ENGINE-001

# Extract new terms from code
python scripts/generate_glossary.py --ssot DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml

# Generate index
python scripts/generate_glossary_index.py

# Check for orphaned terms
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py --check-orphans
```

### File Locations

```
DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml  # SSOT term registry
DOC-REGISTRY-TERM-ID-001__GLOSSARY_REGISTRY.yaml           # Generated term ID registry
docs/DOC-GUIDE-GLOSSARY-665__glossary.md                   # Generated glossary
docs/DOC-GUIDE-DOC-GLOSSARY-*.md                           # Governance docs
scripts/                                                   # Tooling
config/DOC-CONFIG-GLOSSARY-POLICY-055__glossary_policy.yaml        # Validation rules
```

---

## Governance

**Review Cadence**:
- **Daily**: Automated validation in CI
- **Weekly**: Architecture team reviews new proposals
- **Monthly**: Quality review and refinement
- **Quarterly**: Comprehensive audit

**Approval Authority**:
- **New Terms**: Architecture team (2+ approvals)
- **Updates**: Any contributor (peer review)
- **Deprecation**: Architecture team decision
- **Schema Changes**: Architecture team + governance

**Quality Gates**:
- All PRs touching glossary must pass validation
- New terms require metadata entry
- Updates require changelog entry
- Schema changes require version bump

---

**Document Status**: ACTIVE
**Next Review**: 2025-12-25
**Maintained By**: Architecture Team
**Version**: 1.0.0

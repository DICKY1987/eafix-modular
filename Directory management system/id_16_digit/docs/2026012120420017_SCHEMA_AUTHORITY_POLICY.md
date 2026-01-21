---
doc_id: 2026012120420017
title: Schema Authority Policy
version: 1.0
effective_date: 2026-01-21
status: AUTHORITATIVE
classification: GOVERNANCE_POLICY
author: System Architecture
---

# Schema Authority Policy

**Document ID**: 2026012120420017  
**Policy Version**: 1.0  
**Effective Date**: 2026-01-21T20:42:00Z  
**Status**: AUTHORITATIVE

## 1. Governance Principles

### 1.1 Single Source of Truth

**JSON Schema is authoritative**:
- Location: `registry/2026012014470001_unified_ssot_registry.schema.json`
- Version tracked in `meta.version` field (semantic versioning)
- Documentation must match schema; documentation does NOT override schema
- **Conflict Resolution**: Schema wins in all disputes

### 1.2 Schema Versioning

**Semantic Versioning** (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes (requires migration, old tools incompatible)
- **MINOR**: Backward-compatible additions (new optional fields, enum values)
- **PATCH**: Non-functional changes (documentation, descriptions, examples)

**Current Version**: 2.1.0 (as of 2026-01-20)

---

## 2. Enum Management

### 2.1 Allowed Without Schema Bump (Backward-Compatible)

✅ **Adding new values to open enums**:
- `entity_kind`: file | asset | transient | external | module | directory | process | **[new_kind]**
- `rel_type`: IMPORTS | DEPENDS_ON | CALLS | **[NEW_REL]** (open enum, no exhaustive list)

✅ **Expanding documentation of existing values**:
- Adding usage notes, examples, clarifications

✅ **Adding optional fields**:
- New columns with `required: false` in schema

### 2.2 Requires Schema Bump (Breaking Changes)

❌ **Removing enum values**:
- Breaking: Existing registries may contain removed value
- Requires: Major version bump + migration plan

❌ **Renaming enum values**:
- Breaking: Queries and filters break
- Requires: Major version bump + search-replace migration

❌ **Changing enum constraints**:
- Example: Making `status` conditional on `entity_kind`
- Requires: Minor bump (if validation added) or major (if makes existing data invalid)

---

## 3. Conditional Enums

### 3.1 Status Field Rules

**Core Lifecycle** (all entity kinds):
- `active` — Operational, current
- `deprecated` — Marked for removal, still usable
- `quarantined` — Flagged for review, use with caution
- `archived` — Retired, read-only
- `deleted` — Logically deleted, may be purged

**Transient-Specific** (only when `entity_kind=transient`):
- `closed` — Completed execution
- `running` — Currently active
- `pending` — Queued, not started
- `failed` — Execution failed

**Validation Rule**:
```python
if record_kind == "entity" and entity_kind == "transient":
    allowed_status = core_lifecycle + transient_specific
else:
    allowed_status = core_lifecycle_only

if status not in allowed_status:
    raise ValidationError(f"Status '{status}' not allowed for entity_kind '{entity_kind}'")
```

**Enforcement**: Validator MUST check conditional logic before accepting writes.

### 3.2 Entity Kind: "other" Governance

**Allowed but requires documentation**:
- `entity_kind=other` is permitted for unknown/emerging types
- **Requirement**: `notes` field MUST document reason for "other" classification
- **Review Process**: Annual audit of "other" entities
- **Promotion Threshold**: If `count(other) > 10%` of total entities → schema bump to add new explicit kind

**Example Workflow**:
1. New entity type discovered (e.g., "container image")
2. Initially classify as `entity_kind=other`, add note: "Container image, awaiting schema addition"
3. If count grows, propose schema bump to add `entity_kind=container`
4. Update schema, migrate "other" → "container"

---

## 4. Adding New Record Kinds

**Current Record Kinds**: `entity | edge | generator`

**To Add New Record Kind** (e.g., `annotation`):

### 4.1 Requirements
1. **Design Document**: Justify need, define use cases
2. **Column Set**: Define complete column set for new kind (core + kind-specific)
3. **Schema Update**: Add discriminated union branch in JSON Schema
4. **Major Version Bump**: Increment schema version (e.g., 2.1 → 3.0)
5. **Validator Updates**: Update all validators to handle new kind
6. **Migration Plan**: Document how to handle existing registries (may be no-op if additive)
7. **Tool Updates**: Update scanner, CLI, generators to support new kind

### 4.2 Approval Process
- Design doc reviewed by System Architect
- Schema change approved by governance committee (if applicable)
- Testing in non-production environment required
- Migration tested on copy of production registry

---

## 5. Schema Change Workflow

### 5.1 Standard Process

**1. Propose Change**
- Create design document with rationale
- Identify breaking vs non-breaking
- Estimate migration effort

**2. Update JSON Schema**
- Edit `2026012014470001_unified_ssot_registry.schema.json`
- Update `meta.version` field
- Add `meta.changelog` entry

**3. Bump Schema Version**
- Patch: Documentation only
- Minor: New optional fields, enum values (backward-compatible)
- Major: Breaking changes (requires migration)

**4. Update Validators**
- Modify all validators to enforce new rules
- Add tests for new validation logic

**5. Update Documentation**
- Update column dictionary
- Update quick reference guide
- Update implementation plan

**6. Migrate Existing Registries** (if breaking)
- Write migration script
- Test on copy of production data
- Document rollback procedure

**7. Update Registry Metadata**
- Set `meta.version` in `ID_REGISTRY.json` to new schema version
- Log change in `identity_audit_log.jsonl`

### 5.2 Version Compatibility Check

**At Load Time**:
```python
registry_version = registry["meta"]["version"]
schema_version = schema["meta"]["version"]

if registry_version.major > schema_version.major:
    raise IncompatibleVersionError("Registry too new for this tool")

if registry_version.major < schema_version.major:
    warn("Registry version older than schema, migration recommended")
```

**Tool Behavior**:
- Tools MUST gracefully handle unknown fields (forward compatibility)
- Tools MUST NOT write records requiring newer schema to older registries
- Tools SHOULD validate `meta.version` before writes

---

## 6. Backward Compatibility

### 6.1 Forward Compatibility (Reading Newer Registries)
- Tools MUST ignore unknown fields (don't error on extra columns)
- Tools MUST ignore unknown enum values in non-critical fields (log warning)
- Tools MUST error on unknown `record_kind` (critical discriminator)

### 6.2 Backward Compatibility (Writing to Older Registries)
- Tools MUST NOT write new record kinds to older registries
- Tools MUST NOT write new required fields to older registries
- Tools SHOULD check `meta.version` before writes

### 6.3 Migration Strategy
- **Opt-in**: Migrations are manual, not automatic
- **Non-destructive**: Original registry backed up before migration
- **Reversible**: Rollback script provided with migration
- **Testable**: Migration dry-run mode available

---

## 7. Emergency Hotfix Process

**For Critical Bugs** (data loss, corruption risk, security vulnerability):

### 7.1 Fast-Track Approval
1. **Immediate Action**: Fix applied without full workflow
2. **Documentation**: Update `CHANGELOG.md` immediately
3. **Retrospective Design Doc**: Create within 48 hours
4. **Version Bump**: Patch version bump (e.g., 2.1.0 → 2.1.1)

### 7.2 Communication
- Notify all users via commit message, release notes
- Document exact issue, impact, and fix
- Provide upgrade instructions

### 7.3 Post-Hotfix Review
- Weekly review of hotfix (was it necessary?)
- Extract lessons learned
- Update processes to prevent similar issues

---

## 8. Enum Addition Examples

### 8.1 Adding New entity_kind (Minor Bump)

**Before** (v2.1.0):
```json
"entity_kind": {
  "enum": ["file", "asset", "transient", "external", "module", "directory", "process", "other"]
}
```

**After** (v2.2.0):
```json
"entity_kind": {
  "enum": ["file", "asset", "transient", "external", "module", "directory", "process", "container", "other"]
}
```

**Migration**: None required (backward-compatible addition)

### 8.2 Adding New Conditional Status (Minor Bump + Validator Update)

**Before** (v2.1.0):
- Transient statuses: closed | running | pending | failed

**After** (v2.2.0):
- Transient statuses: closed | running | pending | failed | **suspended**

**Migration**: None required (new state additive)

**Validator Update**: Add "suspended" to allowed transient states

---

## 9. Validation and Enforcement

### 9.1 Pre-Commit Validation
- Schema version check
- Required field validation
- Conditional enum validation
- Derivation consistency check

### 9.2 Runtime Validation
- Load-time version compatibility check
- Write-time policy enforcement
- Query-time graceful degradation (unknown fields ignored)

### 9.3 Audit Trail
- All schema changes logged in `identity_audit_log.jsonl`
- Version history tracked in Git
- Breaking changes documented in `CHANGELOG.md`

---

## 10. Governance and Ownership

### 10.1 Policy Owner
- **Role**: System Architect
- **Responsibilities**: 
  - Approve schema changes
  - Maintain schema authority policy
  - Resolve schema conflicts

### 10.2 Review Cycle
- **Frequency**: Quarterly
- **Scope**: Review "other" entity_kind usage, enum growth, breaking change requests
- **Output**: Recommendations for schema evolution

### 10.3 Change Approval Authority
- **Patch changes**: System Architect (documentation only)
- **Minor changes**: System Architect + Tech Lead review
- **Major changes**: Full governance committee approval + migration plan

---

## 11. References

- JSON Schema: `registry/2026012014470001_unified_ssot_registry.schema.json`
- Write Policy: `contracts/2026012120420001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml`
- Derivations: `contracts/2026012120420002_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml`
- Implementation Plan: `docs/2026012102510001_UNIFIED_SSOT_REGISTRY_IMPLEMENTATION_PLAN.md`

---

## 12. Changelog

### v1.0 (2026-01-21)
- Initial policy document
- Defined governance principles
- Documented enum management rules
- Established schema change workflow
- Created emergency hotfix process

---

**Effective Immediately**: 2026-01-21T20:42:00Z  
**Next Review**: 2026-04-21 (Quarterly)

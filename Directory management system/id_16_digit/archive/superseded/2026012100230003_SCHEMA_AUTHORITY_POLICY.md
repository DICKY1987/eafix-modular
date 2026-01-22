---
doc_id: 2026012100230003
title: Schema Authority Policy
version: 1.0
date: 2026-01-21T00:23:14Z
status: AUTHORITATIVE
classification: GOVERNANCE_POLICY
purpose: Define governance for schema changes and enum additions
---

# Schema Authority Policy

## Version
- **Policy Version**: 1.0
- **Effective Date**: 2026-01-21
- **Document ID**: 2026012100230003
- **Last Updated**: 2026-01-21T00:23:14Z

---

## 0) Executive Summary

This policy establishes **one authoritative source of truth** for the Unified SSOT Registry schema and defines strict governance rules for schema evolution to prevent drift, conflicts, and breaking changes.

**Key Principles**:
1. JSON Schema is authoritative (documentation follows schema)
2. Semantic versioning for all schema changes
3. Conditional enums require validator enforcement
4. Breaking changes require migration plans
5. Emergency hotfixes have retroactive documentation requirements

---

## 1) Governance Principles

### 1.1 Single Source of Truth

**Authoritative Schema**: `registry/2026012014470001_unified_ssot_registry.schema.json`

**Authority Hierarchy**:
1. **JSON Schema file** - Ultimate authority
2. **DERIVATIONS.yaml** - Authoritative for computed fields
3. **WRITE_POLICY.yaml** - Authoritative for ownership
4. **Documentation** - Describes schema, does NOT override it

**Resolution Rule**: In any conflict, JSON Schema wins. Documentation must be updated to match schema.

### 1.2 Schema Versioning

**Location**: `meta.version` field in registry metadata

**Semantic Versioning** (MAJOR.MINOR.PATCH):
- **MAJOR** (x.0.0) - Breaking changes
  - Removing fields
  - Renaming fields
  - Changing field types
  - Removing enum values
  - Adding required fields to existing record kinds
  - Changing discriminator logic

- **MINOR** (0.x.0) - Backward-compatible additions
  - Adding optional fields
  - Adding new enum values (non-conditional)
  - Adding new record_kind (if opt-in)
  - Expanding validation rules (non-breaking)

- **PATCH** (0.0.x) - Documentation/description changes
  - Clarifying field descriptions
  - Adding examples
  - Fixing typos
  - Updating documentation

**Version Bump Trigger**: Any schema file modification MUST bump version.

---

## 2) Enum Management

### 2.1 Enum Categories

**Closed Enums** (require schema bump to add values):
- `record_kind`: entity | edge | generator
- `writable_by`: tool_only | user_only | both | never
- `update_policy`: immutable | recompute_on_scan | ...

**Open Enums** (can add values without schema bump):
- `entity_kind`: file | asset | transient | external | module | directory | process | other
- `rel_type`: IMPORTS | CALLS | DOCUMENTS | ...
- `evidence_method`: static_parse | dynamic_trace | user_asserted | heuristic | config_declared

**Conditional Enums** (values allowed only under certain conditions):
- `status`: Core lifecycle + transient-specific states

### 2.2 Adding Enum Values

**Closed Enums**:
1. Propose change in design document
2. Update JSON Schema
3. Bump MAJOR or MINOR version
4. Update all validators
5. Update documentation
6. Test all tools

**Open Enums**:
1. Add value to schema (MINOR version bump)
2. Document in column dictionary
3. Update validators if needed
4. No migration required

**Conditional Enums**:
1. Requires validator update (MINOR version bump)
2. Add conditional logic to validator
3. Document condition in schema
4. Test validation

### 2.3 Removing Enum Values

**Always Breaking** - Requires MAJOR version bump:
1. Create deprecation notice (one version ahead)
2. Mark enum value as deprecated in schema
3. Scanner warns on deprecated value usage
4. Next MAJOR version: remove value
5. Migration guide required

---

## 3) Conditional Enums (Special Rules)

### 3.1 Status Field

**Core Lifecycle States** (all entities):
- `active` - Currently in use
- `deprecated` - Marked for future removal
- `quarantined` - Isolated due to issues
- `archived` - Moved to long-term storage
- `deleted` - Soft-deleted

**Transient-Specific States** (entity_kind=transient only):
- `closed` - Completed/finished
- `running` - Currently executing
- `pending` - Queued/waiting
- `failed` - Execution failed

**Validation Rule**: Validator MUST reject transient states for non-transient entities.

**Implementation**:
```python
if record['status'] in ['closed', 'running', 'pending', 'failed']:
    if record.get('entity_kind') != 'transient':
        raise ValidationError(f"Status '{record['status']}' only allowed for transient entities")
```

### 3.2 Entity Kind "other"

**Governance Workflow**:
1. `other` is allowed but requires documentation in `notes` field
2. Quarterly review: analyze all `entity_kind=other` entities
3. If pattern emerges, promote to explicit kind (MINOR version bump)
4. **Threshold**: If count(other) > 10% of total entities → REQUIRED schema bump

**Usage Policy**:
- Must document reason in `notes`: "Temporary: [description]"
- Annual review to reduce `other` usage
- Goal: <5% of entities use `other`

---

## 4) Adding New Record Kinds

**Current**: `entity | edge | generator`

**To Add New record_kind**:
1. **Requires MAJOR version bump** (breaking change)
2. Design document with:
   - Complete column set for new kind
   - Discriminator logic
   - Use cases
   - Migration plan
3. Update JSON Schema discriminator
4. Update all validators
5. Update all tools (scanner, generator runner, query API)
6. Create migration script
7. Test with production registry

**Timeline**: Minimum 2 weeks for review and testing

---

## 5) Schema Change Workflow

### 5.1 Standard Workflow

1. **Propose** - Create design document
   - Describe change
   - Rationale
   - Impact analysis
   - Migration plan (if breaking)

2. **Review** - Team review
   - Assess backward compatibility
   - Identify affected tools
   - Estimate migration effort

3. **Implement** - Update artifacts
   - Update JSON Schema file
   - Bump `meta.version` field
   - Update validators
   - Update documentation
   - Create migration script (if needed)

4. **Test** - Validation
   - Test with production registry
   - Validate all tools
   - Test migration (if breaking)

5. **Deploy** - Rollout
   - Merge schema changes
   - Run migration (if breaking)
   - Update registry version
   - Notify stakeholders

### 5.2 Change Request Template

```markdown
## Schema Change Request

**Change Type**: [MAJOR | MINOR | PATCH]
**Proposed Version**: [x.y.z]
**Date**: [YYYY-MM-DD]
**Author**: [name]

### Summary
[One-paragraph description]

### Changes
- [ ] Add field: [field_name, type, optional/required]
- [ ] Remove field: [field_name]
- [ ] Modify enum: [enum_name, added/removed values]
- [ ] Other: [description]

### Backward Compatibility
[Breaking | Compatible | N/A]

### Migration Required
[Yes | No]
[If yes, describe migration steps]

### Affected Tools
- [ ] Scanner
- [ ] Validator
- [ ] Generator runner
- [ ] Query API
- [ ] Documentation

### Testing Plan
[How will this be tested?]

### Timeline
- Review: [date]
- Implement: [date]
- Deploy: [date]
```

---

## 6) Backward Compatibility

### 6.1 Forward Compatibility

**Tools MUST**:
- Gracefully handle unknown fields (ignore, don't error)
- Handle unknown enum values (treat as valid unless validation required)
- Version-check registry at load time

**Implementation**:
```python
registry = load_registry(path)
registry_version = registry['meta']['version']
tool_max_version = "2.1.0"

if parse_version(registry_version) > parse_version(tool_max_version):
    print(f"Warning: Registry version {registry_version} newer than tool supports {tool_max_version}")
    print("Tool may not understand all fields. Consider upgrading.")
```

### 6.2 Breaking Change Migration

**Required Artifacts**:
1. Migration script (automated)
2. Migration guide (manual steps)
3. Rollback procedure
4. Test suite for migration

**Migration Script Requirements**:
- Idempotent (safe to run multiple times)
- Validates before/after
- Creates backup
- Logs all changes
- Dry-run mode

---

## 7) Emergency Hotfix Process

**For Critical Bugs** (data loss, corruption risk, security):

1. **Immediate Action** (within 1 hour)
   - Fix implemented
   - Hotfix merged
   - Registry patched

2. **Documentation** (within 24 hours)
   - Update `CHANGELOG.md`
   - Document hotfix in schema file
   - Notify stakeholders

3. **Retroactive Governance** (within 48 hours)
   - Create design document
   - Follow-up review
   - Assess process improvements

**Example Scenarios**:
- Data corruption due to schema bug
- Security vulnerability in validator
- Critical ID collision issue

---

## 8) Validator Requirements

### 8.1 Conditional Validation

Validators MUST enforce:
1. Conditional enum rules (e.g., transient-only status values)
2. Field co-requirements (e.g., expires_utc + ttl_seconds)
3. Required fields per record_kind
4. Type constraints per discriminator value

### 8.2 Version Compatibility

Validators MUST:
1. Check schema version compatibility at startup
2. Reject writes to registries with incompatible schema version
3. Warn on deprecated field usage
4. Log validation rule version

---

## 9) Documentation Requirements

### 9.1 Schema Documentation

**Must Include**:
- Field descriptions for all columns
- Enum value meanings
- Conditional rules
- Examples
- Version history

**Synchronized Documents**:
- `COLUMN_DICTIONARY.md` - Field reference
- `QUICK_REFERENCE.md` - Schema summary
- `IMPLEMENTATION_PLAN.md` - Roadmap

### 9.2 Changelog

**`CHANGELOG.md` Format**:
```markdown
## [2.1.0] - 2026-01-21

### Added
- Added `directory_path` derivation policy
- Added conditional status validation

### Changed
- Expanded `status` enum with transient states

### Deprecated
- None

### Removed
- None

### Fixed
- None
```

---

## 10) Governance Roles

### 10.1 Schema Steward

**Responsibilities**:
- Review schema change requests
- Maintain schema documentation
- Coordinate migrations
- Version management

**Authority**:
- Approve/reject schema changes
- Emergency hotfix decisions

### 10.2 Tool Owners

**Responsibilities**:
- Implement schema changes in tools
- Report compatibility issues
- Test migrations

---

## 11) Compliance

### 11.1 Schema Change Checklist

Before merging any schema change:
- [ ] Design document created
- [ ] Version bumped appropriately
- [ ] JSON Schema file updated
- [ ] Validators updated
- [ ] Documentation updated
- [ ] Migration script created (if breaking)
- [ ] Tests pass
- [ ] Changelog updated
- [ ] Stakeholders notified

### 11.2 Audit

**Quarterly Review**:
- Assess schema stability
- Review `entity_kind=other` usage
- Check deprecated field usage
- Evaluate validator performance

---

## 12) References

- JSON Schema: `registry/2026012014470001_unified_ssot_registry.schema.json`
- Registry Spec: `registry/2026012012410001_SINGLE_UNIFIED_SSOT_REGISTRY_SPEC.md`
- Column Dictionary: `registry/2026012015460001_COLUMN_DICTIONARY.md`
- Implementation Plan: `registry/2026012102510001_UNIFIED_SSOT_REGISTRY_IMPLEMENTATION_PLAN.md`

---

**Policy Status**: AUTHORITATIVE  
**Review Cycle**: Quarterly  
**Next Review**: 2026-04-21

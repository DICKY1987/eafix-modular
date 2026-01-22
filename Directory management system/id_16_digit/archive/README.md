# Archived Documentation

This directory contains historical and superseded documentation that is no longer
part of the active documentation set but is preserved for reference.

**Archive Date**: 2026-01-22  
**Reason**: Documentation consolidation to reduce redundancy and improve clarity

---

## Directory Structure

### superseded/
Documents that have been replaced by newer versions:
- **2026012100230003_SCHEMA_AUTHORITY_POLICY.md**  
  Replaced by: `docs/2026012120420017_SCHEMA_AUTHORITY_POLICY.md`  
  Date: 2026-01-21 (same day, improved version created 20 hours later)
  
- **2026012012430001_SINGLE_REGISTRY_QUICK_START.md**  
  Superseded by: `registry/2026012014470004_REGISTRY_V2.1_QUICK_REFERENCE.md` + `docs/2026012120420018_REGISTRY_OPERATIONS_RUNBOOK.md`  
  Date: 2026-01-20 (initial quick start, replaced by more comprehensive docs 3 days later)

### design-decisions/
Historical documents from the design and decision-making phase:
- **2026012012110001_UNIFIED_SSOT_REGISTRY_ANALYSIS.md**  
  Purpose: Analysis that led to single unified registry design (vs 4 separate registries)  
  Date: 2026-01-20  
  Status: Decision made, implementation complete
  
- **2026012012200001_REGISTRY_COMPARISON_CURRENT_VS_TARGET.md**  
  Purpose: Migration planning document comparing old design to new  
  Date: 2026-01-20  
  Status: Target state achieved

---

## When to Consult Archived Docs

**Understanding Design Rationale**:
- Why did we choose a single unified registry?
- What alternatives were considered?
- What were the tradeoffs?

**Historical Context**:
- How did the registry evolve?
- What problems were we solving?
- What was the migration path?

**Onboarding**:
- "Why is the system designed this way?"
- "What design decisions were made and why?"

**Troubleshooting**:
- Comparing old vs new approaches
- Understanding legacy references

---

## Current Documentation

See parent directory for active documentation:

### Entry Points
- `/0199900095260118_README.md` - Main project README
- `/2026011820600002_QUICK_START_GUIDE.md` - Quick start for users
- `/HARDENING_QUICK_REFERENCE.md` - Quick CLI commands

### Policies & Operations
- `/docs/2026012120420017_SCHEMA_AUTHORITY_POLICY.md` - Governance
- `/docs/2026012120420018_REGISTRY_OPERATIONS_RUNBOOK.md` - Operations guide
- `/docs/id_16_digit_SYSTEM_DOCUMENTATION.md` - Comprehensive system doc

### Registry Specifications
- `/registry/2026012012410001_SINGLE_UNIFIED_SSOT_REGISTRY_SPEC.md` - Registry spec v2.1
- `/registry/2026012014470004_REGISTRY_V2.1_QUICK_REFERENCE.md` - Schema quick reference
- `/registry/2026012015460001_COLUMN_DICTIONARY.md` - Column definitions
- `/registry/2026012102510001_UNIFIED_SSOT_REGISTRY_IMPLEMENTATION_PLAN.md` - Implementation plan
- `/registry/2026012100230013_IMPLEMENTATION_COMPLETE.md` - Completion status

### Completion Tracking
- `/PROJECT_COMPLETION_SUMMARY.md` - Phases 0-9 (initial implementation)
- `/HARDENING_COMPLETION_SUMMARY.md` - Phase 10 (hardening features)

---

## Git History

All archived files remain available in Git history:
```bash
# View file history
git log --follow -- archive/superseded/2026012100230003_SCHEMA_AUTHORITY_POLICY.md

# Restore archived file (if needed)
git show master:archive/superseded/2026012100230003_SCHEMA_AUTHORITY_POLICY.md > restored_file.md
```

---

## Archive Maintenance

**Policy**: Archive files are **read-only historical references**. They should not be:
- Updated or modified (except for critical corrections)
- Used as authoritative sources for current operations
- Linked from active documentation (except historical context notes)

**When to Archive New Files**:
- File is superseded by a newer version
- Design document is no longer relevant after implementation
- Migration document is obsolete after migration complete
- Quick start is replaced by more comprehensive guide

**When NOT to Archive**:
- File is still referenced in current operations
- Historical context is needed frequently
- Alternative documentation doesn't fully replace content

---

**Last Updated**: 2026-01-22T00:23:00Z  
**Archived By**: Documentation consolidation (see DOCUMENTATION_CONSOLIDATION_REVIEW.md)  
**Active Documentation Count**: 20 files (reduced from 24)

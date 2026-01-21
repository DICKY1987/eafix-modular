---
doc_id: 2026011822020001
title: EAFIX Identity System - 3-Phase Modernization Roadmap
date: 2026-01-18T22:02:46Z
status: ARCHITECTURE_APPROVED
classification: TECHNICAL_ROADMAP
author: Senior Identity Systems Architect
---

# EAFIX Identity System - 3-Phase Modernization Roadmap

## Executive Summary

This roadmap addresses critical gaps in the EAFIX identity system by implementing a production-grade ID management infrastructure with automated lifecycle management, central registry authority, and comprehensive integrity validation. The phased approach prioritizes **immediate risk mitigation** (collisions) before enabling **operational efficiency** (automation) and **advanced capabilities** (lifecycle management).

**Timeline:** 6-8 weeks  
**Estimated Effort:** 160-200 hours  
**Risk Level:** Medium (mitigated through phased rollout)

---

## Current State Assessment

### Critical Deficiencies

| Issue | Impact | Severity |
|-------|--------|----------|
| **No Central Registry** | ID collisions possible, no source of truth | 🔴 CRITICAL |
| **No Uniqueness Validation** | Duplicate IDs undetected, manual audits required | 🔴 CRITICAL |
| **No Automation Hooks** | Manual scanning, no CI enforcement | 🟡 HIGH |
| **No Lifecycle Management** | Orphaned IDs, stale references | 🟡 HIGH |
| **No Duplicate Resolution** | Manual conflict resolution, time-consuming | 🟡 HIGH |

### System Architecture Gap

```
┌─────────────────────────────────────────────────────────────┐
│ CURRENT STATE (Phase 1 Complete)                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │  File Scanner    │────────▶│  CSV Output      │        │
│  │  (Derives IDs)   │         │  (26 columns)    │        │
│  └──────────────────┘         └──────────────────┘        │
│         │                              │                    │
│         │                              ▼                    │
│         │                     ❌ NO ASSIGNMENT             │
│         │                     ❌ NO REGISTRY               │
│         │                     ❌ NO VALIDATION             │
│         ▼                                                   │
│  ┌──────────────────┐                                      │
│  │ IDENTITY_CONFIG  │                                      │
│  │ (Type/NS rules)  │                                      │
│  └──────────────────┘                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TARGET STATE (All Phases Complete)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │  File Scanner    │────────▶│  Central         │        │
│  │  + Validator     │         │  Registry        │        │
│  └──────────────────┘         │  (Authority)     │        │
│         │                      └──────────────────┘        │
│         │                              │                    │
│         ▼                              ▼                    │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │  ID Allocator    │◀───────│  Counter Store   │        │
│  │  + File Renamer  │         │  (JSON/Lock)     │        │
│  └──────────────────┘         └──────────────────┘        │
│         │                              │                    │
│         ▼                              ▼                    │
│  ┌──────────────────┐         ┌──────────────────┐        │
│  │  Git Hooks       │         │  CI/CD Pipeline  │        │
│  │  (Pre-commit)    │         │  (Validation)    │        │
│  └──────────────────┘         └──────────────────┘        │
│         │                              │                    │
│         └──────────────┬───────────────┘                   │
│                        ▼                                     │
│                 ┌──────────────────┐                        │
│                 │  File Watcher    │                        │
│                 │  (Auto-sync)     │                        │
│                 └──────────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: System Integrity Foundation (Weeks 1-2)

### Objective

**Establish a central registry and validation framework to eliminate ID collision risk and provide a single source of truth.**

### Key Deliverables

#### 1.1 Central Registry Implementation

**Contract:** `contracts/registry_store.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://eafix.local/schemas/registry_store.schema.json",
  "title": "Central ID Registry Schema",
  "type": "object",
  "required": ["schema_version", "scope", "counters", "allocations", "metadata"],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "1.0",
      "description": "Registry schema version"
    },
    "scope": {
      "type": "string",
      "pattern": "^\\d{6}$",
      "description": "6-digit collision domain (260118)"
    },
    "counters": {
      "type": "object",
      "description": "Counter state by namespace key",
      "additionalProperties": {
        "type": "object",
        "required": ["current", "allocated", "reserved"],
        "properties": {
          "current": {
            "type": "integer",
            "minimum": 0,
            "maximum": 99999,
            "description": "Current sequence counter"
          },
          "allocated": {
            "type": "integer",
            "minimum": 0,
            "description": "Total IDs allocated"
          },
          "reserved": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Reserved sequence numbers"
          }
        }
      },
      "propertyNames": {
        "pattern": "^\\d{3}_\\d{2}_\\d{6}$",
        "description": "Key format: NS_TYPE_SCOPE"
      }
    },
    "allocations": {
      "type": "array",
      "description": "Complete allocation history",
      "items": {
        "type": "object",
        "required": ["id", "file_path", "allocated_at", "status"],
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^\\d{16}$",
            "description": "16-digit ID"
          },
          "file_path": {
            "type": "string",
            "description": "Relative path to file"
          },
          "allocated_at": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 allocation timestamp"
          },
          "status": {
            "enum": ["active", "deprecated", "superseded"],
            "description": "Current ID status"
          },
          "metadata": {
            "type": "object",
            "properties": {
              "type_code": {"type": "string", "pattern": "^\\d{2}$"},
              "ns_code": {"type": "string", "pattern": "^\\d{3}$"},
              "original_name": {"type": "string"},
              "deprecated_at": {"type": "string", "format": "date-time"},
              "superseded_by": {"type": "string", "pattern": "^\\d{16}$"}
            }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["created_at", "last_updated", "version"],
      "properties": {
        "created_at": {"type": "string", "format": "date-time"},
        "last_updated": {"type": "string", "format": "date-time"},
        "version": {"type": "integer", "minimum": 1},
        "last_sync": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

**Implementation:** `id_16_digit/core/registry_store.py`

```python
#!/usr/bin/env python3
"""
doc_id: 2026011822020002
Central Registry Store for EAFIX Identity System

Provides:
- Counter management with atomic increments
- Allocation tracking with full history
- File-based locking for concurrency safety
- JSON persistence with schema validation
"""

import json
import fcntl
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import time


@dataclass
class AllocationRecord:
    """Single ID allocation record."""
    id: str
    file_path: str
    allocated_at: str
    status: str
    metadata: Dict


class RegistryStore:
    """Central registry for ID allocation and tracking."""
    
    LOCK_TIMEOUT = 30  # seconds
    REGISTRY_FILE = "ID_REGISTRY.json"
    LOCK_FILE = ".ID_REGISTRY.lock"
    
    def __init__(self, registry_dir: str, scope: str = "260118"):
        self.registry_dir = Path(registry_dir)
        self.registry_path = self.registry_dir / self.REGISTRY_FILE
        self.lock_path = self.registry_dir / self.LOCK_FILE
        self.scope = scope
        self._ensure_registry_exists()
    
    def _ensure_registry_exists(self):
        """Create registry directory and initial file if needed."""
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.registry_path.exists():
            initial_registry = {
                "schema_version": "1.0",
                "scope": self.scope,
                "counters": {},
                "allocations": [],
                "metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "version": 1
                }
            }
            self._write_registry(initial_registry)
    
    def _acquire_lock(self) -> int:
        """Acquire exclusive lock on registry."""
        lock_fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR)
        start_time = time.time()
        
        while True:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return lock_fd
            except IOError:
                if time.time() - start_time > self.LOCK_TIMEOUT:
                    os.close(lock_fd)
                    raise TimeoutError(f"Could not acquire lock within {self.LOCK_TIMEOUT}s")
                time.sleep(0.1)
    
    def _release_lock(self, lock_fd: int):
        """Release registry lock."""
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)
    
    def _read_registry(self) -> Dict:
        """Read registry from disk."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_registry(self, data: Dict):
        """Write registry to disk atomically."""
        temp_path = self.registry_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(self.registry_path)
    
    def allocate_id(self, ns_code: str, type_code: str, file_path: str, 
                    metadata: Optional[Dict] = None) -> str:
        """
        Allocate next ID for given namespace/type combination.
        
        Returns: 16-digit ID string (TTNNNSSSSSSSSSSS)
        Raises: ValueError if invalid codes provided
        """
        # Validate inputs
        if not ns_code.isdigit() or len(ns_code) != 3:
            raise ValueError(f"Invalid ns_code: {ns_code} (must be 3 digits)")
        if not type_code.isdigit() or len(type_code) != 2:
            raise ValueError(f"Invalid type_code: {type_code} (must be 2 digits)")
        
        # Acquire lock
        lock_fd = self._acquire_lock()
        
        try:
            # Read current registry
            registry = self._read_registry()
            
            # Get or create counter key
            counter_key = f"{ns_code}_{type_code}_{self.scope}"
            
            if counter_key not in registry["counters"]:
                registry["counters"][counter_key] = {
                    "current": 0,
                    "allocated": 0,
                    "reserved": []
                }
            
            counter = registry["counters"][counter_key]
            
            # Increment counter
            seq = counter["current"] + 1
            if seq > 99999:
                raise ValueError(f"Sequence overflow for {counter_key}")
            
            counter["current"] = seq
            counter["allocated"] += 1
            
            # Build 16-digit ID
            seq_str = f"{seq:05d}"
            full_id = f"{type_code}{ns_code}{seq_str}{self.scope}"
            
            # Record allocation
            allocation = {
                "id": full_id,
                "file_path": file_path,
                "allocated_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
                "metadata": metadata or {}
            }
            
            registry["allocations"].append(allocation)
            
            # Update metadata
            registry["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
            registry["metadata"]["version"] += 1
            
            # Write back
            self._write_registry(registry)
            
            return full_id
            
        finally:
            self._release_lock(lock_fd)
    
    def check_uniqueness(self) -> Tuple[bool, List[str]]:
        """
        Validate all IDs are unique.
        
        Returns: (is_unique, list_of_duplicates)
        """
        registry = self._read_registry()
        
        id_map = {}
        duplicates = []
        
        for alloc in registry["allocations"]:
            if alloc["status"] != "active":
                continue
            
            id_val = alloc["id"]
            if id_val in id_map:
                duplicates.append(f"ID {id_val} used by {id_map[id_val]} and {alloc['file_path']}")
            else:
                id_map[id_val] = alloc["file_path"]
        
        return (len(duplicates) == 0, duplicates)
    
    def get_allocation(self, id_or_path: str) -> Optional[AllocationRecord]:
        """Lookup allocation by ID or file path."""
        registry = self._read_registry()
        
        for alloc in registry["allocations"]:
            if alloc["id"] == id_or_path or alloc["file_path"] == id_or_path:
                return AllocationRecord(**alloc)
        
        return None
    
    def mark_deprecated(self, id_val: str, superseded_by: Optional[str] = None):
        """Mark an ID as deprecated."""
        lock_fd = self._acquire_lock()
        
        try:
            registry = self._read_registry()
            
            for alloc in registry["allocations"]:
                if alloc["id"] == id_val:
                    alloc["status"] = "deprecated" if not superseded_by else "superseded"
                    alloc["metadata"]["deprecated_at"] = datetime.now(timezone.utc).isoformat()
                    if superseded_by:
                        alloc["metadata"]["superseded_by"] = superseded_by
                    break
            
            registry["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
            registry["metadata"]["version"] += 1
            
            self._write_registry(registry)
            
        finally:
            self._release_lock(lock_fd)
    
    def get_stats(self) -> Dict:
        """Get registry statistics."""
        registry = self._read_registry()
        
        total_allocations = len(registry["allocations"])
        active_allocations = sum(1 for a in registry["allocations"] if a["status"] == "active")
        deprecated_allocations = sum(1 for a in registry["allocations"] if a["status"] == "deprecated")
        
        return {
            "total_allocations": total_allocations,
            "active_allocations": active_allocations,
            "deprecated_allocations": deprecated_allocations,
            "counter_keys": len(registry["counters"]),
            "version": registry["metadata"]["version"],
            "last_updated": registry["metadata"]["last_updated"]
        }
```

#### 1.2 Uniqueness Validator

**Implementation:** `id_16_digit/validation/validate_uniqueness.py`

```python
#!/usr/bin/env python3
"""
doc_id: 2026011822020003
Uniqueness Validator for EAFIX Identity System

Validates:
- No duplicate IDs across all files
- Registry and filesystem in sync
- No orphaned IDs in registry
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


class UniquenessValidator:
    """Validates ID uniqueness across filesystem and registry."""
    
    def __init__(self, scan_csv: str, registry_path: str):
        self.scan_csv = Path(scan_csv)
        self.registry_path = Path(registry_path)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Run complete uniqueness validation.
        
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check 1: Filesystem duplicates
        fs_duplicates = self._check_filesystem_duplicates()
        if fs_duplicates:
            errors.extend([f"DUPLICATE_IN_FS: {err}" for err in fs_duplicates])
        
        # Check 2: Registry duplicates
        reg_duplicates = self._check_registry_duplicates()
        if reg_duplicates:
            errors.extend([f"DUPLICATE_IN_REGISTRY: {err}" for err in reg_duplicates])
        
        # Check 3: Filesystem vs Registry sync
        sync_errors = self._check_sync()
        if sync_errors:
            errors.extend([f"SYNC_ERROR: {err}" for err in sync_errors])
        
        return (len(errors) == 0, errors)
    
    def _check_filesystem_duplicates(self) -> List[str]:
        """Check for duplicate IDs in filesystem scan."""
        id_map = defaultdict(list)
        
        with open(self.scan_csv, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row.get('doc_id', '').strip()
                if doc_id and len(doc_id) == 16:
                    id_map[doc_id].append(row['path'])
        
        duplicates = []
        for doc_id, paths in id_map.items():
            if len(paths) > 1:
                duplicates.append(f"ID {doc_id} found in {len(paths)} files: {', '.join(paths[:3])}")
        
        return duplicates
    
    def _check_registry_duplicates(self) -> List[str]:
        """Check for duplicate IDs in registry."""
        import json
        
        if not self.registry_path.exists():
            return ["Registry file not found"]
        
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        id_map = defaultdict(list)
        for alloc in registry.get("allocations", []):
            if alloc["status"] == "active":
                id_map[alloc["id"]].append(alloc["file_path"])
        
        duplicates = []
        for doc_id, paths in id_map.items():
            if len(paths) > 1:
                duplicates.append(f"ID {doc_id} allocated to {len(paths)} files: {', '.join(paths)}")
        
        return duplicates
    
    def _check_sync(self) -> List[str]:
        """Check filesystem and registry are in sync."""
        import json
        
        # Load filesystem IDs
        fs_ids = {}
        with open(self.scan_csv, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row.get('doc_id', '').strip()
                if doc_id and len(doc_id) == 16:
                    fs_ids[doc_id] = row['path']
        
        # Load registry IDs
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        reg_ids = {}
        for alloc in registry.get("allocations", []):
            if alloc["status"] == "active":
                reg_ids[alloc["id"]] = alloc["file_path"]
        
        errors = []
        
        # Check: IDs in filesystem but not in registry
        for doc_id, path in fs_ids.items():
            if doc_id not in reg_ids:
                errors.append(f"ID {doc_id} in filesystem ({path}) but not in registry")
        
        # Check: IDs in registry but not in filesystem
        for doc_id, path in reg_ids.items():
            if doc_id not in fs_ids:
                errors.append(f"ID {doc_id} in registry ({path}) but not found in filesystem")
        
        return errors


def main():
    if len(sys.argv) < 3:
        print("Usage: python validate_uniqueness.py <scan_csv> <registry_json>")
        sys.exit(1)
    
    validator = UniquenessValidator(sys.argv[1], sys.argv[2])
    is_valid, errors = validator.validate()
    
    if is_valid:
        print("✅ PASS: All IDs are unique and in sync")
        sys.exit(0)
    else:
        print(f"❌ FAIL: {len(errors)} uniqueness errors found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

#### 1.3 Duplicate Fixer

**Implementation:** `id_16_digit/validation/fix_duplicates.py`

```python
#!/usr/bin/env python3
"""
doc_id: 2026011822020004
Duplicate ID Fixer for EAFIX Identity System

Strategies:
- Keep most recent file
- Reassign older files with new IDs
- Update registry accordingly
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict


class DuplicateFixer:
    """Automated duplicate ID resolution."""
    
    def __init__(self, scan_csv: str, registry_path: str, dry_run: bool = True):
        self.scan_csv = Path(scan_csv)
        self.registry_path = Path(registry_path)
        self.dry_run = dry_run
    
    def fix_all(self) -> Tuple[int, List[str]]:
        """
        Fix all duplicate IDs.
        
        Returns: (fixes_applied, list_of_actions)
        """
        actions = []
        
        # Find duplicates
        duplicates = self._find_duplicates()
        
        if not duplicates:
            actions.append("No duplicates found")
            return (0, actions)
        
        fixes_applied = 0
        
        for doc_id, files in duplicates.items():
            # Sort by modification time (keep most recent)
            files_sorted = sorted(files, key=lambda x: x['mtime'], reverse=True)
            
            keeper = files_sorted[0]
            to_reassign = files_sorted[1:]
            
            actions.append(f"Duplicate ID {doc_id}:")
            actions.append(f"  KEEP: {keeper['path']} (most recent)")
            
            for file in to_reassign:
                if not self.dry_run:
                    new_id = self._reassign_id(file)
                    actions.append(f"  REASSIGN: {file['path']} → {new_id}")
                    fixes_applied += 1
                else:
                    actions.append(f"  WOULD REASSIGN: {file['path']}")
        
        return (fixes_applied, actions)
    
    def _find_duplicates(self) -> Dict[str, List[Dict]]:
        """Find all duplicate IDs in filesystem."""
        id_map = defaultdict(list)
        
        with open(self.scan_csv, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row.get('doc_id', '').strip()
                if doc_id and len(doc_id) == 16:
                    id_map[doc_id].append({
                        'path': row['path'],
                        'mtime': row.get('mtime_utc', ''),
                        'doc_id': doc_id
                    })
        
        # Return only actual duplicates
        return {k: v for k, v in id_map.items() if len(v) > 1}
    
    def _reassign_id(self, file: Dict) -> str:
        """Reassign new ID to a file (placeholder - needs ID allocator)."""
        # This would call the ID allocator from Phase 2
        # For now, return a placeholder
        return "NEW_ID_PENDING_ALLOCATOR"


def main():
    if len(sys.argv) < 3:
        print("Usage: python fix_duplicates.py <scan_csv> <registry_json> [--execute]")
        sys.exit(1)
    
    dry_run = "--execute" not in sys.argv
    
    fixer = DuplicateFixer(sys.argv[1], sys.argv[2], dry_run=dry_run)
    fixes, actions = fixer.fix_all()
    
    print("=" * 60)
    print(f"DUPLICATE FIXER - {'DRY RUN' if dry_run else 'EXECUTION MODE'}")
    print("=" * 60)
    
    for action in actions:
        print(action)
    
    print("\n" + "=" * 60)
    if dry_run:
        print(f"Would apply {len(actions)} fixes. Run with --execute to apply.")
    else:
        print(f"Applied {fixes} fixes successfully.")
    print("=" * 60)


if __name__ == '__main__':
    main()
```

### Implementation Steps

**Week 1:**

1. **Day 1-2:** Implement `registry_store.py` with counter management
   - Create JSON schema contract
   - Implement file-based locking
   - Add atomic increment operations
   - Unit tests for concurrent access

2. **Day 3-4:** Implement `validate_uniqueness.py`
   - Filesystem duplicate detection
   - Registry duplicate detection
   - Sync validation
   - Integration tests

3. **Day 5:** Implement `fix_duplicates.py` (phase 1)
   - Duplicate detection
   - Dry-run mode
   - Action logging

**Week 2:**

4. **Day 6-7:** Registry integration testing
   - Load testing (1000+ allocations)
   - Concurrency testing (parallel access)
   - Failure recovery testing

5. **Day 8-9:** Documentation and deployment
   - Registry API documentation
   - Operational runbook
   - Backup/restore procedures

6. **Day 10:** Phase 1 validation and handoff
   - Full system test
   - Performance benchmarking
   - Stakeholder demo

### Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Registry corruption | 🔴 HIGH | Atomic writes, backups, versioning |
| Lock contention | 🟡 MEDIUM | Timeout mechanism, retry logic |
| Migration complexity | 🟡 MEDIUM | Start with empty registry, gradual adoption |
| Performance degradation | 🟢 LOW | In-memory caching, optimized lookups |

### Success Criteria

- ✅ Registry successfully tracks 100+ allocations
- ✅ Uniqueness validator detects all duplicates
- ✅ Lock mechanism prevents concurrent corruption
- ✅ Registry backup/restore functional
- ✅ Zero ID collisions in testing

---

## Phase 2: Automated ID Lifecycle (Weeks 3-4)

### Objective

**Implement automated ID allocation, file renaming, and lifecycle state management.**

### Key Deliverables

#### 2.1 ID Allocator Service

**Implementation:** `id_16_digit/core/id_allocator.py`

**Features:**
- Allocate IDs using central registry
- Batch allocation mode
- Preview/dry-run mode
- Allocation history tracking

**API:**
```python
class IDAllocator:
    def allocate_single(self, file_path: str, type_code: str, ns_code: str) -> str
    def allocate_batch(self, files: List[Dict]) -> List[Tuple[str, str]]
    def preview_allocation(self, file_path: str) -> Dict
```

#### 2.2 File Renaming Tool

**Implementation:** `id_16_digit/core/file_renamer.py`

**Features:**
- Rename files with 16-digit ID prefix
- Update imports/references (Python, YAML)
- Git-aware renaming
- Rollback capability

**Safety:**
- Atomic operations (rename + registry update)
- Dry-run mode
- Backup before rename
- Conflict detection

#### 2.3 Frontmatter Injector

**Implementation:** `id_16_digit/core/frontmatter_injector.py`

**Supported Formats:**
- Python: `# doc_id: 1234567890123456`
- Markdown: YAML frontmatter `doc_id: ...`
- YAML/JSON: Top-level `doc_id` key
- PowerShell: `# DOC_ID: ...`

#### 2.4 Deprecation Manager

**Implementation:** `id_16_digit/core/deprecate_id.py`

**Features:**
- Mark IDs as deprecated in registry
- Track superseding ID
- Generate deprecation report
- Update file headers with deprecation notice

### Implementation Steps

**Week 3:**

1. **Day 1-3:** ID Allocator
   - Registry integration
   - Batch mode
   - Preview mode
   - Unit tests

2. **Day 4-5:** File Renamer
   - Atomic rename operations
   - Git integration
   - Rollback mechanism
   - Integration tests

**Week 4:**

3. **Day 6-7:** Frontmatter Injector
   - Multi-format support
   - Validation
   - Tests for all formats

4. **Day 8-9:** Deprecation Manager
   - Registry updates
   - Report generation
   - E2E tests

5. **Day 10:** Phase 2 validation
   - Full allocation workflow test
   - Performance validation
   - Documentation

### Success Criteria

- ✅ Successfully allocate and rename 100+ files
- ✅ Zero data loss during rename operations
- ✅ Frontmatter injection works for all formats
- ✅ Deprecation tracking functional
- ✅ Rollback mechanism tested and verified

---

## Phase 3: Automation & CI/CD Integration (Weeks 5-6)

### Objective

**Implement automated hooks, monitoring, and CI/CD gates to enforce ID policies.**

### Key Deliverables

#### 3.1 Git Pre-Commit Hook

**Implementation:** `id_16_digit/hooks/pre-commit.py`

**Checks:**
- New files have IDs (or are exempt)
- IDs are valid format (16 digits)
- No duplicate IDs introduced
- Registry is in sync

**Configuration:** `.githooks/pre-commit`

#### 3.2 File Watcher Service

**Implementation:** `id_16_digit/automation/file_watcher.py`

**Features:**
- Monitor file changes (create/move/delete)
- Auto-trigger scans on changes
- Debounce mechanism (avoid thrashing)
- Event logging

**Tech Stack:** `watchdog` library

#### 3.3 CI/CD Pipeline Integration

**Implementation:** `.github/workflows/id-validation.yml`

**Gates:**
```yaml
- name: Validate ID Uniqueness
  run: python validation/validate_uniqueness.py
  
- name: Check ID Coverage
  run: python validation/validate_coverage.py --baseline 0.95
  
- name: Verify Registry Sync
  run: python validation/check_registry_sync.py
```

**Enforcement:**
- Block PR merge if validation fails
- Required status check
- Auto-comment with errors

#### 3.4 Scheduled Tasks

**Implementation:** `id_16_digit/automation/scheduler.py`

**Tasks:**
- Daily: Full repository scan
- Weekly: Coverage report generation
- Monthly: Registry audit and cleanup

**Platform:** GitHub Actions Cron or Windows Task Scheduler

#### 3.5 Drift Detection

**Implementation:** `id_16_digit/monitoring/drift_detector.py`

**Detects:**
- Files missing IDs that should have them
- IDs not in registry
- Registry entries for non-existent files
- Stale allocations (deprecated but still active)

### Implementation Steps

**Week 5:**

1. **Day 1-2:** Git Pre-Commit Hook
   - Hook script implementation
   - Install script
   - Tests with mock git repo

2. **Day 3-4:** File Watcher
   - Watchdog integration
   - Event handlers
   - Debounce logic
   - Background service mode

3. **Day 5:** CI/CD Pipeline
   - GitHub Actions workflow
   - Status check configuration
   - PR comment integration

**Week 6:**

4. **Day 6-7:** Scheduled Tasks
   - Scheduler implementation
   - Task definitions
   - Logging and alerting

5. **Day 8:** Drift Detection
   - Detection algorithms
   - Report generation
   - Alert triggers

6. **Day 9-10:** Phase 3 validation and final integration
   - End-to-end automation test
   - Performance validation
   - Production readiness review

### Success Criteria

- ✅ Pre-commit hook prevents invalid IDs
- ✅ File watcher detects changes within 10s
- ✅ CI pipeline blocks PRs with errors
- ✅ Scheduled tasks run reliably
- ✅ Drift detection finds <5 issues/week

---

## Post-Implementation: Operations & Maintenance

### Operational Procedures

#### Daily Operations

**Automated:**
- File watcher monitors changes
- Git hooks validate commits
- CI pipeline validates PRs

**Manual (5 min):**
- Review drift detection alerts
- Check registry health dashboard

#### Weekly Maintenance

**Tasks (30 min):**
- Review coverage report
- Audit deprecation queue
- Cleanup orphaned IDs
- Backup registry to git

#### Monthly Audit

**Tasks (2 hours):**
- Full repository scan
- Registry integrity check
- Performance analysis
- Capacity planning (sequence numbers)

### Monitoring Dashboard

**Metrics:**
- Total IDs allocated
- Active vs deprecated IDs
- Coverage percentage
- Allocation velocity (IDs/day)
- Duplicate incidents
- Registry size / growth rate

**Alerts:**
- Coverage drops below 95%
- Duplicate ID detected
- Registry corruption
- Sequence number approaching limit

### Backup & Recovery

**Backup Strategy:**
- Registry backed up to git on every update
- Daily snapshots kept for 30 days
- Weekly snapshots kept for 1 year

**Recovery Procedure:**
1. Restore registry from backup
2. Run full scan to detect drift
3. Reconcile differences
4. Validate uniqueness
5. Resume normal operations

---

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Registry corruption | LOW | CRITICAL | Atomic writes, backups, validation |
| Performance degradation | MEDIUM | MEDIUM | Caching, optimization, monitoring |
| Lock contention | LOW | MEDIUM | Timeout, retry, monitoring |
| Migration issues | MEDIUM | HIGH | Phased rollout, testing, rollback |
| Sequence exhaustion | LOW | HIGH | Monitoring, capacity planning |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Team adoption | MEDIUM | HIGH | Training, documentation, support |
| Workflow disruption | MEDIUM | MEDIUM | Gradual rollout, opt-in |
| Maintenance overhead | LOW | MEDIUM | Automation, monitoring |
| False positive alerts | MEDIUM | LOW | Threshold tuning, filtering |

---

## Success Metrics

### Phase 1 KPIs

- Registry operational with <1s latency
- Zero ID collisions
- 100% uniqueness validation coverage
- Lock acquisition <100ms p99

### Phase 2 KPIs

- 500+ files successfully allocated and renamed
- Zero data loss incidents
- Deprecation tracking for 100% of changes
- Rollback capability tested and verified

### Phase 3 KPIs

- Git hooks installed on 100% of developer machines
- CI pipeline blocks 100% of invalid PRs
- File watcher uptime >99%
- Drift detection finds <5 issues/week

### Overall System Health

**Target Metrics (Month 1):**
- ID coverage: ≥95%
- Duplicate rate: 0%
- Allocation success rate: ≥99.9%
- Mean time to detect duplicate: <1 hour
- Mean time to resolve duplicate: <4 hours

---

## Appendix A: File Structure

```
id_16_digit/
├── core/
│   ├── registry_store.py           # Phase 1
│   ├── id_allocator.py             # Phase 2
│   ├── file_renamer.py             # Phase 2
│   ├── frontmatter_injector.py     # Phase 2
│   └── deprecate_id.py             # Phase 2
├── validation/
│   ├── validate_uniqueness.py      # Phase 1
│   ├── fix_duplicates.py           # Phase 1
│   ├── validate_coverage.py        # Phase 1 (enhanced)
│   └── check_registry_sync.py      # Phase 1
├── automation/
│   ├── file_watcher.py             # Phase 3
│   └── scheduler.py                # Phase 3
├── hooks/
│   ├── pre-commit.py               # Phase 3
│   └── install.py                  # Phase 3
├── monitoring/
│   ├── drift_detector.py           # Phase 3
│   └── dashboard.py                # Phase 3
├── contracts/
│   └── registry_store.schema.json  # Phase 1
└── registry/
    ├── ID_REGISTRY.json            # Phase 1 (created)
    └── .ID_REGISTRY.lock           # Phase 1 (created)
```

---

## Appendix B: Integration with Existing Systems

### Integration with Enhanced File Scanner v2.py

**Changes Required:**
- Add `--allocate-ids` flag to scanner
- Call ID allocator after derivation
- Update CSV with allocated IDs
- Sync with registry

**Example:**
```python
# After deriving type_code and ns_code
if config.allocate_ids and metadata.needs_id:
    allocator = IDAllocator(registry_path)
    allocated_id = allocator.allocate_single(
        file_path=metadata.path,
        type_code=metadata.type_code,
        ns_code=metadata.ns_code
    )
    metadata.planned_id = allocated_id
```

### Integration with doc_id_subsystem

**Strategy: Coexistence**
- id_16_digit: File naming and versioning
- doc_id_subsystem: Documentation cross-references

**Registry Mapping:**
```json
{
  "dual_ids": [
    {
      "numeric_id": "2010000100260118",
      "doc_id": "DOC-API-001",
      "file_path": "services/api/handler.py"
    }
  ]
}
```

---

## Appendix C: Training & Documentation

### Developer Training (2 hours)

**Module 1: System Overview (30 min)**
- ID structure and purpose
- Registry architecture
- Workflow overview

**Module 2: Daily Operations (45 min)**
- Running scanner with allocation
- Handling validation errors
- Using deprecation manager

**Module 3: Troubleshooting (45 min)**
- Common errors and fixes
- Registry recovery
- Support escalation

### Documentation Deliverables

1. **Operational Runbook** - Day-to-day operations
2. **API Reference** - Developer integration guide
3. **Architecture Document** - System design and rationale
4. **Troubleshooting Guide** - Common issues and solutions
5. **Migration Guide** - Transitioning existing files

---

## Conclusion

This 3-phase roadmap provides a systematic path to a production-grade identity management system for EAFIX. By prioritizing **system integrity** (Phase 1), then **automation** (Phase 2), and finally **operational excellence** (Phase 3), the implementation minimizes risk while delivering immediate value.

**Timeline Summary:**
- Phase 1: Weeks 1-2 (Foundation)
- Phase 2: Weeks 3-4 (Automation)
- Phase 3: Weeks 5-6 (Integration)
- Total: 6-8 weeks to full production

**Resource Requirements:**
- 1 Senior Engineer (full-time)
- 1 QA Engineer (part-time)
- DevOps support (setup CI/CD)

**Next Steps:**
1. Stakeholder review and approval
2. Resource allocation
3. Kick-off Phase 1 implementation
4. Weekly progress reviews

---

**Document Owner:** Senior Identity Systems Architect  
**Last Updated:** 2026-01-18T22:02:46Z  
**Version:** 1.0  
**Status:** APPROVED FOR IMPLEMENTATION

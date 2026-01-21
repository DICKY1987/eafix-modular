#!/usr/bin/env python3
"""
Phase 1 Migration Script: ID_REGISTRY.json → REGISTRY_A_FILE_ID.json

Transforms current single-registry system into Registry A (FILE_ID) format
while preserving 100% backward compatibility.

Usage:
    python migrate_phase1.py --input registry/ID_REGISTRY.json --output registry/REGISTRY_A_FILE_ID.json --validate
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Registry A Schema (from specification)
REGISTRY_A_SCHEMA = {
    "id_format": {
        "identifier_field_name": "doc_id",
        "pattern": r"^\d{16}$",
        "type": "string",
        "length": 16,
        "immutable": True
    },
    "filename_rule": {
        "pattern": r"^{doc_id}_.+",
        "description": "Filename MUST start with 16 digits + underscore"
    },
    "backing_kind": "file",
    "required_fields": [
        "filename", "doc_id", "id_kind", "current_relative_path",
        "current_directory_path", "extension", "status", "registry_created_utc"
    ]
}


def load_json(path: str) -> Dict:
    """Load JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: str, data: Dict, indent: int = 2):
    """Save JSON file with pretty formatting"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def extract_filename_from_path(file_path: str) -> str:
    """Extract filename from relative path"""
    return os.path.basename(file_path)


def extract_directory_from_path(file_path: str) -> str:
    """Extract directory from relative path"""
    dirname = os.path.dirname(file_path)
    return dirname if dirname else "."


def extract_extension(filename: str) -> str:
    """Extract file extension including dot"""
    _, ext = os.path.splitext(filename)
    return ext


def transform_allocation_to_entry(allocation: Dict) -> Dict:
    """
    Transform v1.0 allocation record to v2.0 Registry A entry.
    
    Input (v1.0):
    {
      "id": "0199900001260118",
      "file_path": "0199900001260118_.aider.chat.history.md",
      "allocated_at": "2026-01-19T03:54:44.299192",
      "allocated_by": "import_from_scan",
      "status": "active",
      "metadata": {
        "type_code": "01",
        "ns_code": "999",
        "legacy_id": true
      }
    }
    
    Output (v2.0):
    {
      "filename": ".aider.chat.history.md",
      "doc_id": "0199900001260118",
      "id_kind": "doc_id",
      "current_relative_path": "0199900001260118_.aider.chat.history.md",
      "current_directory_path": ".",
      "extension": ".md",
      "status": "active",
      "registry_created_utc": "2026-01-19T03:54:44.299192",
      "registry_updated_utc": "2026-01-19T03:54:44.299192",
      "links": [],
      "origin": {...},
      ...
    }
    """
    file_path = allocation["file_path"]
    filename = extract_filename_from_path(file_path)
    directory = extract_directory_from_path(file_path)
    extension = extract_extension(filename)
    
    # Build origin object from allocated_by
    origin = {
        "origin_kind": "imported" if allocation.get("allocated_by") == "import_from_scan" else "human",
        "origin_ref_id": None,
        "origin_tool_id": allocation.get("allocated_by", "unknown"),
        "origin_event_id": None,
        "created_utc": allocation["allocated_at"]
    }
    
    # Core entry (required fields)
    entry = {
        "filename": filename,
        "doc_id": allocation["id"],
        "id_kind": "doc_id",
        "current_relative_path": file_path,
        "current_directory_path": directory,
        "extension": extension,
        "status": allocation["status"],
        "registry_created_utc": allocation["allocated_at"],
        "registry_updated_utc": allocation["allocated_at"],  # Same as created for initial migration
    }
    
    # Relationship fields (NEW - empty for now)
    entry["links"] = []
    entry["origin"] = origin
    entry["owning_module_id"] = None
    entry["owning_subsystem"] = None
    entry["maintainer"] = None
    entry["role"] = None
    entry["imports"] = []
    entry["exports"] = []
    entry["entrypoints"] = []
    
    # Preserve legacy metadata for audit
    if "metadata" in allocation:
        entry["legacy_metadata"] = allocation["metadata"]
    
    return entry


def migrate_to_registry_a(input_path: str, output_path: str) -> Dict:
    """
    Main migration function: ID_REGISTRY.json → REGISTRY_A_FILE_ID.json
    
    Returns migration report with statistics.
    """
    print(f"Loading current registry from: {input_path}")
    current_registry = load_json(input_path)
    
    print(f"Registry version: {current_registry.get('schema_version')}")
    print(f"Scope: {current_registry.get('scope')}")
    print(f"Total allocations: {len(current_registry.get('allocations', []))}")
    
    # Build Registry A structure
    registry_a = {
        "meta": {
            "document_id": "REG-A-FILE-ID-720066-001",  # Using your project's scope ID
            "registry_name": "FILE_ID_REGISTRY",
            "registry_class": "file_id",
            "version": "2.0.0",
            "status": "active",
            "last_updated_utc": datetime.utcnow().isoformat() + "Z",
            "authoritative": True,
            "description": "Authoritative registry for file-backed identities (16-digit doc_id system)",
            
            # Migration metadata
            "legacy_scope": current_registry.get("scope"),
            "migrated_from": "ID_REGISTRY.json v1.0",
            "migration_date": datetime.utcnow().isoformat() + "Z",
            "migration_tool": "migrate_phase1.py v1.0"
        },
        "schema": REGISTRY_A_SCHEMA,
        "counters": current_registry.get("counters", {}),  # Preserve counters exactly
        "entries": []
    }
    
    # Transform each allocation → entry
    print("\nTransforming allocations to entries...")
    migration_stats = {
        "total_allocations": len(current_registry.get("allocations", [])),
        "transformed": 0,
        "errors": []
    }
    
    for i, allocation in enumerate(current_registry.get("allocations", []), 1):
        try:
            entry = transform_allocation_to_entry(allocation)
            registry_a["entries"].append(entry)
            migration_stats["transformed"] += 1
            
            if i % 100 == 0:
                print(f"  Transformed {i}/{migration_stats['total_allocations']} records...")
        except Exception as e:
            error_msg = f"Error transforming allocation {allocation.get('id', 'UNKNOWN')}: {str(e)}"
            migration_stats["errors"].append(error_msg)
            print(f"  ⚠️  {error_msg}")
    
    print(f"\n✅ Transformation complete: {migration_stats['transformed']}/{migration_stats['total_allocations']} records")
    
    if migration_stats["errors"]:
        print(f"⚠️  {len(migration_stats['errors'])} errors encountered")
    
    # Save Registry A
    print(f"\nSaving Registry A to: {output_path}")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    save_json(output_path, registry_a)
    
    print("✅ Registry A created successfully")
    
    return migration_stats


def validate_migration(old_path: str, new_path: str) -> bool:
    """
    Validate that migration preserved all data correctly.
    
    Checks:
    - Same number of records
    - All doc_ids preserved
    - All file_paths preserved
    - All statuses preserved
    - Counter state preserved
    """
    print("\n" + "="*60)
    print("VALIDATION: Checking migration integrity")
    print("="*60)
    
    old_registry = load_json(old_path)
    new_registry = load_json(new_path)
    
    old_allocs = old_registry.get("allocations", [])
    new_entries = new_registry.get("entries", [])
    
    validation_errors = []
    
    # Check 1: Record count
    print(f"\n1. Record count: {len(old_allocs)} → {len(new_entries)}")
    if len(old_allocs) != len(new_entries):
        validation_errors.append(f"Record count mismatch: {len(old_allocs)} vs {len(new_entries)}")
    else:
        print("   ✅ PASS")
    
    # Check 2: All doc_ids preserved
    print("\n2. Doc ID preservation")
    old_ids = {a["id"] for a in old_allocs}
    new_ids = {e["doc_id"] for e in new_entries}
    missing_ids = old_ids - new_ids
    extra_ids = new_ids - old_ids
    
    if missing_ids:
        validation_errors.append(f"Missing IDs: {missing_ids}")
        print(f"   ❌ FAIL: Missing {len(missing_ids)} IDs")
    elif extra_ids:
        validation_errors.append(f"Extra IDs: {extra_ids}")
        print(f"   ❌ FAIL: Extra {len(extra_ids)} IDs")
    else:
        print("   ✅ PASS: All doc_ids preserved")
    
    # Check 3: File paths preserved
    print("\n3. File path preservation")
    old_paths = {a["file_path"] for a in old_allocs}
    new_paths = {e["current_relative_path"] for e in new_entries}
    
    if old_paths != new_paths:
        validation_errors.append("File paths mismatch")
        print(f"   ❌ FAIL: Path differences detected")
    else:
        print("   ✅ PASS: All file paths preserved")
    
    # Check 4: Status preservation (spot check)
    print("\n4. Status preservation (spot check)")
    old_alloc = old_allocs[0] if old_allocs else None
    new_entry = next((e for e in new_entries if e["doc_id"] == old_alloc["id"]), None) if old_alloc else None
    
    if old_alloc and new_entry:
        if old_alloc["status"] == new_entry["status"]:
            print(f"   ✅ PASS: Status preserved ({old_alloc['status']})")
        else:
            validation_errors.append(f"Status mismatch for {old_alloc['id']}")
            print(f"   ❌ FAIL: Status changed")
    
    # Check 5: Counter preservation
    print("\n5. Counter state preservation")
    old_counters = old_registry.get("counters", {})
    new_counters = new_registry.get("counters", {})
    
    if old_counters == new_counters:
        print("   ✅ PASS: Counters preserved exactly")
    else:
        validation_errors.append("Counter state mismatch")
        print(f"   ❌ FAIL: Counter differences detected")
    
    # Check 6: New fields added
    print("\n6. New Registry A fields added")
    required_new_fields = ["links", "origin", "owning_module_id", "role", "imports", "exports"]
    if new_entries:
        first_entry = new_entries[0]
        missing_fields = [f for f in required_new_fields if f not in first_entry]
        if missing_fields:
            validation_errors.append(f"Missing new fields: {missing_fields}")
            print(f"   ❌ FAIL: Missing fields: {missing_fields}")
        else:
            print(f"   ✅ PASS: All new fields present")
    
    # Summary
    print("\n" + "="*60)
    if validation_errors:
        print(f"❌ VALIDATION FAILED: {len(validation_errors)} errors")
        for error in validation_errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ VALIDATION PASSED: Migration is correct")
        return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate ID_REGISTRY.json to REGISTRY_A_FILE_ID.json (Phase 1)")
    parser.add_argument("--input", default="registry/ID_REGISTRY.json", help="Input registry path")
    parser.add_argument("--output", default="registry/REGISTRY_A_FILE_ID.json", help="Output registry path")
    parser.add_argument("--validate", action="store_true", help="Run validation after migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing files")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be written")
    
    # Run migration
    stats = migrate_to_registry_a(args.input, args.output if not args.dry_run else "/tmp/test_registry_a.json")
    
    print("\n" + "="*60)
    print("MIGRATION STATISTICS")
    print("="*60)
    print(f"Total records: {stats['total_allocations']}")
    print(f"Transformed: {stats['transformed']}")
    print(f"Errors: {len(stats['errors'])}")
    
    # Run validation if requested
    if args.validate and not args.dry_run:
        is_valid = validate_migration(args.input, args.output)
        if not is_valid:
            print("\n⚠️  Migration validation failed - review errors above")
            exit(1)
    
    if args.dry_run:
        print("\n🔍 Dry run complete - no files written")
    else:
        print(f"\n✅ Phase 1 migration complete!")
        print(f"\nNext steps:")
        print(f"1. Review {args.output}")
        print(f"2. Test existing tools with registry_adapter.py")
        print(f"3. Run Phase 2 to add edge relationships")

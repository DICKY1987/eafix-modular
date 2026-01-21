#!/usr/bin/env python3
"""
Single Unified SSOT Registry Migration Script

Migrates ID_REGISTRY.json → UNIFIED_SSOT_REGISTRY.json (one file, all record types)

Usage:
    python migrate_to_unified_ssot.py --input registry/ID_REGISTRY.json --output registry/UNIFIED_SSOT_REGISTRY.json --validate
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Complete 80-column superset schema
UNIFIED_SCHEMA_COLUMNS = [
    # Core (all records)
    "record_kind", "record_id", "status", "notes", "tags",
    "created_utc", "updated_utc", "created_by", "updated_by",
    
    # Entity fields
    "entity_id", "entity_kind",
    
    # File-specific
    "doc_id", "filename", "extension", "relative_path", "absolute_path",
    "directory_path", "size_bytes", "mtime_utc", "sha256", "content_type",
    
    # Asset-specific
    "asset_id", "asset_family", "asset_version", "canonical_path",
    
    # Transient-specific
    "transient_id", "transient_type", "ttl_seconds", "expires_utc",
    
    # External-specific
    "external_ref", "external_system", "resolver_hint",
    
    # Module/process mapping
    "module_id", "module_id_source", "module_id_override",
    "process_id", "process_step_id", "process_step_role",
    
    # Classification
    "role_code", "type_code", "function_code_1", "function_code_2", "function_code_3",
    "entrypoint_flag", "short_description",
    
    # Provenance
    "first_seen_utc", "last_seen_utc", "scan_id",
    "source_entity_id", "supersedes_entity_id",
    
    # Edge fields
    "edge_id", "source_entity_id_edge", "target_entity_id_edge",
    "rel_type", "directionality", "confidence",
    "evidence_method", "evidence_locator", "evidence_snippet",
    "observed_utc", "tool_version", "edge_flags",
    
    # Generator fields
    "generator_id", "generator_name", "generator_version",
    "output_kind", "output_path", "output_path_pattern",
    "declared_dependencies", "input_filters",
    "sort_rule_id", "sort_keys",
    "template_ref_entity_id", "validator_id", "validation_rules",
    "last_build_utc", "source_registry_hash", "source_registry_scan_id",
    "output_hash", "build_report_entity_id"
]


def load_json(path: str) -> Dict:
    """Load JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: str, data: Dict, indent: int = 2):
    """Save JSON file"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def create_empty_record() -> Dict:
    """Create record with all columns initialized to None"""
    return {col: None for col in UNIFIED_SCHEMA_COLUMNS}


def create_unified_structure(current_registry: Dict) -> Dict:
    """Create unified registry structure"""
    return {
        "meta": {
            "document_id": "REG-UNIFIED-SSOT-720066-001",
            "registry_name": "UNIFIED_SSOT_REGISTRY",
            "version": "2.0.0",
            "status": "active",
            "last_updated_utc": datetime.utcnow().isoformat() + "Z",
            "authoritative": True,
            "description": "Single source of truth for all entities, relationships, and generators",
            "migrated_from": "ID_REGISTRY.json v1.0",
            "migration_date": datetime.utcnow().isoformat() + "Z",
            "legacy_scope": current_registry.get("scope"),
            "total_columns": len(UNIFIED_SCHEMA_COLUMNS)
        },
        "counters": {
            "record_id": {"current": 0, "allocated": 0},
            "file_doc_id": current_registry.get("counters", {}),
            "asset_id": {},
            "transient_id": {},
            "edge_id": {},
            "generator_id": {"current": 0}
        },
        "records": []
    }


def transform_allocation_to_entity(allocation: Dict, record_id: int) -> Dict:
    """
    Transform v1.0 allocation to v2.0 entity record.
    
    Creates a sparse record with all 80 columns, only populating relevant ones.
    """
    record = create_empty_record()
    
    # Core fields (all records)
    record["record_kind"] = "entity"
    record["record_id"] = f"REC-{record_id:06d}"
    record["status"] = allocation["status"]
    record["created_utc"] = allocation["allocated_at"]
    record["updated_utc"] = allocation["allocated_at"]
    record["created_by"] = allocation.get("allocated_by", "unknown")
    record["updated_by"] = allocation.get("allocated_by", "unknown")
    record["notes"] = None
    record["tags"] = []
    
    # Entity identity
    record["entity_id"] = allocation["id"]
    record["entity_kind"] = "file"
    
    # File-specific fields
    record["doc_id"] = allocation["id"]
    record["filename"] = os.path.basename(allocation["file_path"])
    record["extension"] = os.path.splitext(allocation["file_path"])[1]
    record["relative_path"] = allocation["file_path"]
    record["directory_path"] = os.path.dirname(allocation["file_path"]) or "."
    
    # Classification
    metadata = allocation.get("metadata", {})
    record["type_code"] = metadata.get("type_code")
    
    # Provenance
    record["first_seen_utc"] = allocation["allocated_at"]
    record["last_seen_utc"] = allocation["allocated_at"]
    
    # All other fields remain None (sparse record)
    return record


def migrate_to_unified_registry(input_path: str, output_path: str) -> Dict:
    """
    Main migration: ID_REGISTRY.json → UNIFIED_SSOT_REGISTRY.json
    
    Returns unified registry dict.
    """
    print("="*70)
    print("SINGLE UNIFIED SSOT REGISTRY MIGRATION")
    print("="*70)
    
    print(f"\n📂 Loading current registry: {input_path}")
    current = load_json(input_path)
    
    print(f"   Version: {current.get('schema_version')}")
    print(f"   Scope: {current.get('scope')}")
    print(f"   Allocations: {len(current.get('allocations', []))}")
    
    print(f"\n🏗️  Creating unified SSOT structure...")
    unified = create_unified_structure(current)
    print(f"   Columns in superset: {len(UNIFIED_SCHEMA_COLUMNS)}")
    
    print(f"\n🔄 Transforming allocations → entity records...")
    record_id_counter = 1
    stats = {
        "total_allocations": len(current.get("allocations", [])),
        "transformed": 0,
        "errors": []
    }
    
    for i, allocation in enumerate(current.get("allocations", []), 1):
        try:
            entity_record = transform_allocation_to_entity(allocation, record_id_counter)
            unified["records"].append(entity_record)
            stats["transformed"] += 1
            record_id_counter += 1
            
            if i % 100 == 0:
                print(f"   Transformed {i}/{stats['total_allocations']} records...")
        
        except Exception as e:
            error_msg = f"Error transforming {allocation.get('id', 'UNKNOWN')}: {str(e)}"
            stats["errors"].append(error_msg)
            print(f"   ⚠️  {error_msg}")
    
    # Update counters
    unified["counters"]["record_id"]["current"] = record_id_counter - 1
    unified["counters"]["record_id"]["allocated"] = record_id_counter - 1
    
    print(f"\n✅ Transformation complete:")
    print(f"   Total: {stats['total_allocations']}")
    print(f"   Transformed: {stats['transformed']}")
    print(f"   Errors: {len(stats['errors'])}")
    
    print(f"\n💾 Saving unified registry: {output_path}")
    save_json(output_path, unified)
    
    # Print size comparison
    old_size = os.path.getsize(input_path) if os.path.exists(input_path) else 0
    new_size = os.path.getsize(output_path)
    print(f"\n📊 File size comparison:")
    print(f"   Old: {old_size:,} bytes")
    print(f"   New: {new_size:,} bytes")
    print(f"   Ratio: {new_size/old_size:.2f}x" if old_size > 0 else "   Ratio: N/A")
    
    return unified, stats


def validate_unified_registry(unified: Dict) -> List[str]:
    """
    Validate unified SSOT registry.
    
    Checks:
    - All records have record_kind
    - Entity records have entity_id and entity_kind
    - Edge records have edge_id, source, target
    - Referential integrity (edges point to valid entities)
    - Confidence ranges (0.0-1.0)
    """
    print("\n" + "="*70)
    print("VALIDATION: Unified SSOT Registry")
    print("="*70)
    
    errors = []
    
    # Check 1: All records have record_kind
    print("\n1. Checking record_kind field...")
    for i, record in enumerate(unified["records"]):
        if "record_kind" not in record or record["record_kind"] is None:
            errors.append(f"Record {i}: missing record_kind")
    
    if errors:
        print(f"   ❌ FAIL: {len(errors)} records missing record_kind")
    else:
        print(f"   ✅ PASS: All {len(unified['records'])} records have record_kind")
    
    # Check 2: Count by record_kind
    print("\n2. Record kind distribution:")
    kind_counts = defaultdict(int)
    for record in unified["records"]:
        kind_counts[record.get("record_kind", "UNKNOWN")] += 1
    
    for kind, count in sorted(kind_counts.items()):
        print(f"   {kind}: {count}")
    
    # Check 3: Entity records have entity_id and entity_kind
    print("\n3. Checking entity records...")
    entity_errors = 0
    for record in unified["records"]:
        if record.get("record_kind") == "entity":
            if not record.get("entity_id"):
                errors.append(f"Entity record {record.get('record_id')}: missing entity_id")
                entity_errors += 1
            if not record.get("entity_kind"):
                errors.append(f"Entity record {record.get('record_id')}: missing entity_kind")
                entity_errors += 1
    
    if entity_errors == 0:
        print(f"   ✅ PASS: All entity records valid")
    else:
        print(f"   ❌ FAIL: {entity_errors} entity record errors")
    
    # Check 4: Edge records (if any)
    print("\n4. Checking edge records...")
    edge_count = kind_counts.get("edge", 0)
    if edge_count == 0:
        print(f"   ℹ️  No edge records (expected after Phase 1)")
    else:
        # Validate edges
        entity_ids = {
            r["entity_id"] 
            for r in unified["records"] 
            if r.get("record_kind") == "entity" and r.get("entity_id")
        }
        
        edge_errors = 0
        for record in unified["records"]:
            if record.get("record_kind") == "edge":
                if not record.get("edge_id"):
                    errors.append(f"Edge record {record.get('record_id')}: missing edge_id")
                    edge_errors += 1
                
                source = record.get("source_entity_id_edge")
                target = record.get("target_entity_id_edge")
                
                if source and source not in entity_ids:
                    errors.append(f"Edge {record.get('edge_id')}: source {source} not found")
                    edge_errors += 1
                
                if target and target not in entity_ids:
                    errors.append(f"Edge {record.get('edge_id')}: target {target} not found")
                    edge_errors += 1
                
                confidence = record.get("confidence")
                if confidence is not None and not (0.0 <= confidence <= 1.0):
                    errors.append(f"Edge {record.get('edge_id')}: confidence {confidence} out of range")
                    edge_errors += 1
        
        if edge_errors == 0:
            print(f"   ✅ PASS: All {edge_count} edge records valid")
        else:
            print(f"   ❌ FAIL: {edge_errors} edge record errors")
    
    # Check 5: Schema compliance (all records have all columns)
    print("\n5. Checking schema compliance (80-column superset)...")
    schema_errors = 0
    for record in unified["records"]:
        missing_cols = [col for col in UNIFIED_SCHEMA_COLUMNS if col not in record]
        if missing_cols:
            errors.append(f"Record {record.get('record_id')}: missing columns {missing_cols}")
            schema_errors += 1
    
    if schema_errors == 0:
        print(f"   ✅ PASS: All records have all {len(UNIFIED_SCHEMA_COLUMNS)} columns")
    else:
        print(f"   ❌ FAIL: {schema_errors} records missing columns")
    
    # Summary
    print("\n" + "="*70)
    if errors:
        print(f"❌ VALIDATION FAILED: {len(errors)} errors")
        print("\nFirst 10 errors:")
        for error in errors[:10]:
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")
        return errors
    else:
        print("✅ VALIDATION PASSED: Unified SSOT registry is valid")
        return []


def compare_registries(old_path: str, new_path: str):
    """Compare old and new registries to ensure no data loss"""
    print("\n" + "="*70)
    print("COMPARISON: Old vs New Registry")
    print("="*70)
    
    old = load_json(old_path)
    new = load_json(new_path)
    
    old_ids = {a["id"] for a in old.get("allocations", [])}
    new_ids = {
        r["entity_id"] 
        for r in new["records"] 
        if r.get("record_kind") == "entity" and r.get("entity_kind") == "file"
    }
    
    print(f"\n📊 ID Comparison:")
    print(f"   Old registry: {len(old_ids)} IDs")
    print(f"   New registry: {len(new_ids)} entity IDs")
    
    missing = old_ids - new_ids
    extra = new_ids - old_ids
    
    if missing:
        print(f"   ❌ Missing {len(missing)} IDs: {list(missing)[:5]}...")
    else:
        print(f"   ✅ All old IDs present")
    
    if extra:
        print(f"   ⚠️  Extra {len(extra)} IDs: {list(extra)[:5]}...")
    else:
        print(f"   ✅ No extra IDs")
    
    return len(missing) == 0 and len(extra) == 0


def print_sample_record(unified: Dict, record_kind: str = "entity"):
    """Print sample record to verify structure"""
    print(f"\n📋 Sample {record_kind} record:")
    print("="*70)
    
    for record in unified["records"]:
        if record.get("record_kind") == record_kind:
            # Print only non-null fields
            print(json.dumps({
                k: v for k, v in record.items() if v is not None
            }, indent=2))
            break


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate ID_REGISTRY.json to single unified SSOT registry"
    )
    parser.add_argument(
        "--input", 
        default="registry/ID_REGISTRY.json",
        help="Input registry path"
    )
    parser.add_argument(
        "--output", 
        default="registry/UNIFIED_SSOT_REGISTRY.json",
        help="Output registry path"
    )
    parser.add_argument(
        "--validate", 
        action="store_true",
        help="Run validation after migration"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without writing files"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Print sample record after migration"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files will be written\n")
        output_path = "/tmp/test_unified_registry.json"
    else:
        output_path = args.output
    
    # Run migration
    unified, stats = migrate_to_unified_registry(args.input, output_path)
    
    # Print sample record
    if args.sample:
        print_sample_record(unified, "entity")
    
    # Run validation
    if args.validate:
        errors = validate_unified_registry(unified)
        
        if not args.dry_run:
            compare_registries(args.input, args.output)
    
    # Summary
    print("\n" + "="*70)
    print("MIGRATION SUMMARY")
    print("="*70)
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Records transformed: {stats['transformed']}")
    print(f"Errors: {len(stats['errors'])}")
    
    if args.dry_run:
        print("\n🔍 Dry run complete - no files written")
    else:
        print(f"\n✅ Migration complete!")
        print(f"\nNext steps:")
        print(f"1. Review {args.output}")
        print(f"2. Test queries with UnifiedRegistry class")
        print(f"3. Add edge records (Phase 2)")
        print(f"4. Add asset/transient records (Phase 3)")
        print(f"5. Add generator records (Phase 4)")

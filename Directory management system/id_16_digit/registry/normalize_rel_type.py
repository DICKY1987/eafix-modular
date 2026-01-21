#!/usr/bin/env python3
"""
doc_id: 2026012014470003
Migration script: Normalize rel_type to uppercase (Schema v2.1 alignment)

Usage:
    python normalize_rel_type.py --input UNIFIED_SSOT_REGISTRY.json --output UNIFIED_SSOT_REGISTRY_v2.1.json --validate

Purpose:
    Aligns existing unified registry with v2.1 schema requirement:
    - All rel_type values MUST be uppercase
    - Validates after normalization
    - Creates backup before modification
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


def load_registry(path: Path) -> Dict:
    """Load registry JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_registry(path: Path, registry: Dict):
    """Save registry JSON file with pretty printing."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def normalize_rel_type(registry: Dict) -> Tuple[Dict, List[Dict]]:
    """
    Normalize all rel_type values to uppercase.
    
    Returns:
        (updated_registry, change_log)
    """
    change_log = []
    
    for record in registry.get("records", []):
        if record.get("record_kind") == "edge":
            rel_type = record.get("rel_type")
            if rel_type and rel_type != rel_type.upper():
                old_value = rel_type
                new_value = rel_type.upper()
                record["rel_type"] = new_value
                
                change_log.append({
                    "edge_id": record.get("edge_id"),
                    "record_id": record.get("record_id"),
                    "old_rel_type": old_value,
                    "new_rel_type": new_value,
                    "source_entity_id": record.get("source_entity_id"),
                    "target_entity_id": record.get("target_entity_id")
                })
    
    # Update registry metadata
    if "meta" in registry:
        registry["meta"]["last_updated_utc"] = datetime.utcnow().isoformat() + "Z"
        registry["meta"]["version"] = "2.1.0"  # Bump to v2.1
        
        if "migration_history" not in registry["meta"]:
            registry["meta"]["migration_history"] = []
        
        registry["meta"]["migration_history"].append({
            "migration_id": "normalize_rel_type_v2.1",
            "applied_at": datetime.utcnow().isoformat() + "Z",
            "changes_count": len(change_log),
            "description": "Normalized all rel_type values to uppercase for v2.1 schema compliance"
        })
    
    return registry, change_log


def validate_rel_types(registry: Dict) -> List[str]:
    """
    Validate that all rel_type values are uppercase.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    valid_rel_types = {
        "IMPORTS", "CALLS", "TESTS", "DOCUMENTS", "USES_SCHEMA", "USES_TEMPLATE",
        "GENERATED_FROM", "PRODUCES", "DEPENDS_ON", "DUPLICATES", "PARALLEL_IMPL",
        "IMPLEMENTS_ASSET", "REFERENCES_FILE", "REFERENCES_ASSET", "CONTAINS",
        "CONFLICTS_WITH"
    }
    
    for record in registry.get("records", []):
        if record.get("record_kind") == "edge":
            rel_type = record.get("rel_type")
            if not rel_type:
                errors.append(f"Edge {record.get('edge_id')}: rel_type is missing or null")
            elif rel_type != rel_type.upper():
                errors.append(f"Edge {record.get('edge_id')}: rel_type '{rel_type}' is not uppercase")
            elif rel_type not in valid_rel_types:
                errors.append(f"Edge {record.get('edge_id')}: rel_type '{rel_type}' is not a valid enum value")
    
    return errors


def create_backup(input_path: Path) -> Path:
    """Create timestamped backup of input file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = input_path.parent / f"{input_path.stem}_backup_{timestamp}{input_path.suffix}"
    
    with open(input_path, 'r', encoding='utf-8') as src:
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    
    return backup_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Normalize rel_type values to uppercase (v2.1 schema alignment)"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input unified registry JSON file"
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to overwriting input with backup)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate after normalization"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup before modifying (default: True)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying files"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)
    
    print(f"📂 Loading registry: {input_path}")
    registry = load_registry(input_path)
    
    print(f"🔍 Analyzing edge records...")
    original_errors = validate_rel_types(registry)
    if original_errors:
        print(f"⚠️  Found {len(original_errors)} validation errors:")
        for error in original_errors[:10]:  # Show first 10
            print(f"   - {error}")
        if len(original_errors) > 10:
            print(f"   ... and {len(original_errors) - 10} more")
    else:
        print("✅ All rel_type values are already uppercase")
        return
    
    print(f"\n🔄 Normalizing rel_type values...")
    updated_registry, change_log = normalize_rel_type(registry)
    
    print(f"📊 Normalization complete:")
    print(f"   - Total edge records updated: {len(change_log)}")
    
    if change_log:
        print(f"\n📝 Changes:")
        for i, change in enumerate(change_log[:5], 1):
            print(f"   {i}. Edge {change['edge_id']}: '{change['old_rel_type']}' → '{change['new_rel_type']}'")
        if len(change_log) > 5:
            print(f"   ... and {len(change_log) - 5} more")
    
    if args.dry_run:
        print("\n🧪 DRY RUN: No files modified")
        return
    
    # Determine output path
    output_path = Path(args.output) if args.output else input_path
    
    # Create backup if modifying in place
    if args.backup and output_path == input_path:
        backup_path = create_backup(input_path)
        print(f"\n💾 Backup created: {backup_path}")
    
    # Save updated registry
    print(f"\n💾 Saving updated registry: {output_path}")
    save_registry(output_path, updated_registry)
    
    # Validate if requested
    if args.validate:
        print(f"\n✓ Validating updated registry...")
        errors = validate_rel_types(updated_registry)
        if errors:
            print(f"❌ Validation failed with {len(errors)} errors:")
            for error in errors[:10]:
                print(f"   - {error}")
            sys.exit(1)
        else:
            print("✅ Validation passed: All rel_type values are uppercase")
    
    # Save change log
    if change_log:
        log_path = output_path.parent / f"{output_path.stem}_rel_type_changes.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(change_log, f, indent=2, ensure_ascii=False)
        print(f"\n📋 Change log saved: {log_path}")
    
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()

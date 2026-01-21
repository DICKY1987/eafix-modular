"""
doc_id: 2026012100230007
title: Registry Normalizer
version: 1.0
date: 2026-01-21T00:23:14Z
purpose: Apply normalization rules to registry (paths, casing, IDs)
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple


class RegistryNormalizer:
    """Normalizes registry fields according to locked rules."""
    
    def __init__(self):
        """Initialize normalizer."""
        self.changes_made = []
    
    def normalize_path(self, path: str) -> str:
        """
        Normalize relative_path or directory_path.
        
        Rules:
        - Forward slashes /
        - No leading slash
        - No ./ prefix
        - Collapse repeated slashes
        - Root directory = "."
        """
        if not path:
            return ""
        
        # Replace backslashes
        path = path.replace("\\", "/")
        
        # Remove leading ./
        while path.startswith("./"):
            path = path[2:]
        
        # Remove leading slash
        path = path.lstrip("/")
        
        # Collapse repeated slashes
        while "//" in path:
            path = path.replace("//", "/")
        
        # Remove trailing slash
        path = path.rstrip("/")
        
        # Empty means root
        if not path:
            return "."
        
        return path
    
    def normalize_rel_type(self, rel_type: str) -> str:
        """
        Normalize rel_type to uppercase.
        
        Rules:
        - Always uppercase
        """
        if not rel_type:
            return ""
        return rel_type.upper()
    
    def normalize_doc_id(self, doc_id: str) -> str:
        """
        Normalize doc_id to exactly 16 digits.
        
        Rules:
        - Must be exactly 16 digits
        - No prefix, no separators
        """
        if not doc_id:
            return ""
        
        # Remove any non-digit characters
        digits_only = re.sub(r'\D', '', doc_id)
        
        # Must be exactly 16 digits
        if len(digits_only) == 16:
            return digits_only
        else:
            # Invalid, return original
            return doc_id
    
    def normalize_record_id(self, record_id: str) -> str:
        """
        Normalize record_id format.
        
        Rules:
        - Format: REC-000001 (6-digit zero-padded)
        """
        if not record_id:
            return ""
        
        # Extract number
        match = re.match(r'REC-(\d+)', record_id, re.IGNORECASE)
        if match:
            number = int(match.group(1))
            return f"REC-{number:06d}"
        
        # Try without prefix
        if record_id.isdigit():
            number = int(record_id)
            return f"REC-{number:06d}"
        
        # Invalid, return original
        return record_id
    
    def normalize_edge_id(self, edge_id: str) -> str:
        """
        Normalize edge_id format.
        
        Rules:
        - Format: EDGE-YYYYMMDD-000001 (date + 6-digit counter)
        """
        if not edge_id:
            return ""
        
        # Extract parts
        match = re.match(r'EDGE-(\d{8})-(\d+)', edge_id, re.IGNORECASE)
        if match:
            date_part = match.group(1)
            number = int(match.group(2))
            return f"EDGE-{date_part}-{number:06d}"
        
        # Invalid, return original
        return edge_id
    
    def normalize_generator_id(self, generator_id: str) -> str:
        """
        Normalize generator_id format.
        
        Rules:
        - Format: GEN-000001 (6-digit zero-padded)
        """
        if not generator_id:
            return ""
        
        # Extract number
        match = re.match(r'GEN-(\d+)', generator_id, re.IGNORECASE)
        if match:
            number = int(match.group(1))
            return f"GEN-{number:06d}"
        
        # Invalid, return original
        return generator_id
    
    def normalize_timestamp(self, timestamp: str) -> str:
        """
        Normalize timestamp to ISO 8601 with Z suffix.
        
        Rules:
        - Format: YYYY-MM-DDTHH:MM:SS.ffffffZ
        - Trailing Z required (not +00:00)
        """
        if not timestamp:
            return ""
        
        # Replace +00:00 with Z
        if timestamp.endswith('+00:00'):
            timestamp = timestamp[:-6] + 'Z'
        
        # Ensure trailing Z
        if not timestamp.endswith('Z'):
            timestamp += 'Z'
        
        return timestamp
    
    def normalize_field(
        self,
        field_name: str,
        value: Any,
        record: Dict[str, Any]
    ) -> Tuple[Any, bool]:
        """
        Normalize single field value.
        
        Args:
            field_name: Field name
            value: Current value
            record: Full record for context
            
        Returns:
            (normalized_value, was_changed)
        """
        if value is None:
            return value, False
        
        original = value
        
        # Path fields
        if field_name in ['relative_path', 'directory_path', 'canonical_path']:
            value = self.normalize_path(value)
        
        # Relationship type
        elif field_name == 'rel_type':
            value = self.normalize_rel_type(value)
        
        # ID fields
        elif field_name == 'doc_id':
            value = self.normalize_doc_id(value)
        elif field_name == 'record_id':
            value = self.normalize_record_id(value)
        elif field_name == 'edge_id':
            value = self.normalize_edge_id(value)
        elif field_name == 'generator_id':
            value = self.normalize_generator_id(value)
        
        # Timestamp fields
        elif field_name.endswith('_utc'):
            value = self.normalize_timestamp(value)
        
        # Field names (should be snake_case, but we don't change them)
        # This would be schema-level, not data-level
        
        changed = (original != value)
        return value, changed
    
    def normalize_record(
        self,
        record: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Normalize all fields in record.
        
        Args:
            record: Record to normalize
            
        Returns:
            (normalized_record, list_of_changes)
        """
        changes = []
        record_id = record.get('record_id', 'UNKNOWN')
        
        for field_name, value in list(record.items()):
            normalized_value, was_changed = self.normalize_field(field_name, value, record)
            
            if was_changed:
                record[field_name] = normalized_value
                changes.append(f"{field_name}: '{value}' -> '{normalized_value}'")
        
        return record, changes
    
    def normalize_registry(
        self,
        registry: Dict[str, Any],
        dry_run: bool = False
    ) -> Tuple[Dict[str, Any], int, List[str]]:
        """
        Normalize entire registry.
        
        Args:
            registry: Registry to normalize
            dry_run: If True, don't modify registry (just report changes)
            
        Returns:
            (normalized_registry, total_changes, change_summary)
        """
        all_changes = []
        records_changed = 0
        
        records = registry.get('records', [])
        print(f"\n✓ Normalizing {len(records)} records...")
        
        if dry_run:
            print("  (DRY RUN: no changes will be saved)")
        
        for idx, record in enumerate(records):
            normalized_record, changes = self.normalize_record(record)
            
            if changes:
                records_changed += 1
                record_id = record.get('record_id', f'record_{idx}')
                all_changes.append(f"[{record_id}] {len(changes)} changes")
                
                for change in changes:
                    all_changes.append(f"  - {change}")
                
                if not dry_run:
                    records[idx] = normalized_record
        
        print(f"✓ Normalization complete:")
        print(f"  Records changed: {records_changed}/{len(records)}")
        print(f"  Total field changes: {len([c for c in all_changes if c.startswith('  -')])}")
        
        return registry, records_changed, all_changes


def main():
    """CLI entry point for registry normalization."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python normalize_registry.py <registry.json> [--apply]")
        print()
        print("Options:")
        print("  --apply    Apply normalization (default: dry-run)")
        sys.exit(1)
    
    registry_path = sys.argv[1]
    apply_changes = '--apply' in sys.argv
    
    print(f"Normalizing registry: {registry_path}")
    print("=" * 60)
    
    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # Normalize
    normalizer = RegistryNormalizer()
    normalized_registry, records_changed, changes = normalizer.normalize_registry(
        registry,
        dry_run=not apply_changes
    )
    
    # Show changes
    if changes:
        print("\nChanges:")
        for change in changes[:50]:  # Show first 50
            print(change)
        if len(changes) > 50:
            print(f"... and {len(changes) - 50} more")
    
    print("\n" + "=" * 60)
    
    if apply_changes:
        if records_changed > 0:
            # Save normalized registry
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(normalized_registry, f, indent=2, ensure_ascii=False)
            
            print(f"✓ APPLIED: Registry normalized and saved to {registry_path}")
            print(f"  {records_changed} records updated")
            sys.exit(0)
        else:
            print("✓ No changes needed - registry already normalized")
            sys.exit(0)
    else:
        if records_changed > 0:
            print(f"✓ DRY RUN COMPLETE: {records_changed} records would be changed")
            print("  Run with --apply to save changes")
            sys.exit(0)
        else:
            print("✓ No changes needed - registry already normalized")
            sys.exit(0)


if __name__ == '__main__':
    main()

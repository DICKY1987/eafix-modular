#!/usr/bin/env python3
"""
doc_id: 2026012120420010
Unified SSOT Registry - Registry Normalizer

Applies normalization rules: paths (forward slash), rel_type (uppercase), etc.
Ensures consistent representation across tools and platforms.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class RegistryNormalizer:
    """Normalizes registry fields to canonical format."""
    
    def __init__(self):
        """Initialize normalizer with rules."""
        self.rules = self._init_rules()
        self.stats = {
            "total_records": 0,
            "normalized": 0,
            "unchanged": 0,
            "fields_changed": {}
        }
    
    def _init_rules(self) -> List[Dict[str, Any]]:
        """Initialize normalization rules."""
        return [
            {
                "name": "relative_path_forward_slash",
                "field": "relative_path",
                "applies_when": {"record_kind": "entity"},
                "normalizer": self._normalize_path
            },
            {
                "name": "directory_path_forward_slash",
                "field": "directory_path",
                "applies_when": {"record_kind": "entity"},
                "normalizer": self._normalize_path
            },
            {
                "name": "rel_type_uppercase",
                "field": "rel_type",
                "applies_when": {"record_kind": "edge"},
                "normalizer": self._normalize_rel_type
            },
            {
                "name": "extension_lowercase",
                "field": "extension",
                "applies_when": {"record_kind": "entity"},
                "normalizer": self._normalize_extension
            },
            {
                "name": "timestamps_iso8601",
                "field": "created_utc",
                "applies_when": {},
                "normalizer": self._normalize_timestamp
            },
            {
                "name": "timestamps_iso8601",
                "field": "updated_utc",
                "applies_when": {},
                "normalizer": self._normalize_timestamp
            }
        ]
    
    def _applies_to_record(self, rule: Dict[str, Any], record: Dict[str, Any]) -> bool:
        """Check if rule applies to record."""
        applies_when = rule.get("applies_when", {})
        
        for field, expected in applies_when.items():
            actual = record.get(field)
            if actual != expected:
                return False
        
        return True
    
    def _normalize_path(self, value: Any) -> Any:
        """
        Normalize path: forward slashes, no leading ./, no trailing /.
        Root directory represented as '.'.
        """
        if not value or not isinstance(value, str):
            return value
        
        # Convert backslashes to forward slashes
        normalized = value.replace('\\', '/')
        
        # Remove leading ./
        normalized = normalized.lstrip('./')
        
        # Remove trailing slash (unless it's just '.')
        if normalized != '.':
            normalized = normalized.rstrip('/')
        
        # Empty path becomes '.'
        if not normalized:
            normalized = '.'
        
        return normalized
    
    def _normalize_rel_type(self, value: Any) -> Any:
        """Normalize rel_type to UPPERCASE."""
        if not value or not isinstance(value, str):
            return value
        
        return value.upper()
    
    def _normalize_extension(self, value: Any) -> Any:
        """Normalize extension to lowercase, no leading dot."""
        if not value or not isinstance(value, str):
            return value
        
        # Remove leading dot if present
        normalized = value.lstrip('.')
        
        # Lowercase
        normalized = normalized.lower()
        
        return normalized
    
    def _normalize_timestamp(self, value: Any) -> Any:
        """
        Normalize timestamp to ISO 8601 with trailing Z.
        Format: YYYY-MM-DDTHH:MM:SS.ffffffZ
        """
        if not value or not isinstance(value, str):
            return value
        
        # Already has Z suffix
        if value.endswith('Z'):
            return value
        
        # Has +00:00 suffix (convert to Z)
        if value.endswith('+00:00'):
            return value.replace('+00:00', 'Z')
        
        # No timezone indicator (assume UTC, add Z)
        if 'T' in value and not any(tz in value for tz in ['Z', '+', '-']):
            return value + 'Z'
        
        return value
    
    def normalize_record(
        self, 
        record: Dict[str, Any],
        in_place: bool = False
    ) -> Dict[str, Any]:
        """
        Normalize a single record.
        
        Args:
            record: Record to normalize
            in_place: If True, modify record directly; else return copy
        
        Returns:
            Normalized record (same object if in_place=True, copy otherwise)
        """
        if not in_place:
            record = dict(record)
        
        changed_fields = []
        
        for rule in self.rules:
            if not self._applies_to_record(rule, record):
                continue
            
            field = rule.get("field")
            if field not in record:
                continue
            
            old_value = record[field]
            normalizer = rule.get("normalizer")
            
            if not normalizer:
                continue
            
            new_value = normalizer(old_value)
            
            if old_value != new_value:
                record[field] = new_value
                changed_fields.append(field)
                
                # Track stats
                if field not in self.stats["fields_changed"]:
                    self.stats["fields_changed"][field] = 0
                self.stats["fields_changed"][field] += 1
        
        if changed_fields:
            self.stats["normalized"] += 1
            # Update updated_utc timestamp
            record["updated_utc"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        else:
            self.stats["unchanged"] += 1
        
        return record
    
    def normalize_registry_file(
        self,
        registry_path: str,
        output_path: Optional[str] = None,
        dry_run: bool = False,
        verbose: bool = False
    ) -> Dict[str, int]:
        """
        Normalize all records in registry file.
        
        Args:
            registry_path: Path to ID_REGISTRY.json
            output_path: Output path (default: overwrite input)
            dry_run: If True, don't save, just report
            verbose: Print detailed results
        
        Returns:
            Statistics dict
        """
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        records = registry.get("records", [])
        self.stats["total_records"] = len(records)
        
        for idx, record in enumerate(records):
            record_id = record.get("record_id", f"record_{idx}")
            
            old_record = dict(record)
            self.normalize_record(record, in_place=True)
            
            if verbose:
                # Check what changed
                changed = []
                for key in record.keys():
                    if old_record.get(key) != record.get(key):
                        changed.append(key)
                
                if changed:
                    print(f"→ {record_id}: normalized {', '.join(changed)}")
                else:
                    print(f"  {record_id}: unchanged")
        
        # Save if not dry-run
        if not dry_run:
            output_path = output_path or registry_path
            
            # Update registry metadata
            if "meta" in registry:
                registry["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            
            if verbose:
                print(f"\n✓ Saved normalized registry to: {output_path}")
        
        return self.stats


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Normalize registry fields to canonical format"
    )
    parser.add_argument(
        "--registry",
        default="ID_REGISTRY.json",
        help="Path to registry file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path (default: overwrite input)"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Dry run: report changes without saving"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        normalizer = RegistryNormalizer()
        
        if args.verbose:
            print("Normalization rules:")
            for rule in normalizer.rules:
                print(f"  - {rule['name']}: {rule['field']}")
            print()
        
        stats = normalizer.normalize_registry_file(
            registry_path=args.registry,
            output_path=args.output,
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        
        print(f"\nResults:")
        print(f"  Total records: {stats['total_records']}")
        print(f"  Normalized: {stats['normalized']}")
        print(f"  Unchanged: {stats['unchanged']}")
        
        if stats['fields_changed']:
            print(f"\n  Fields changed:")
            for field, count in sorted(stats['fields_changed'].items()):
                print(f"    {field}: {count}")
        
        if args.dry_run:
            print("\n⚠ Dry run: no changes saved")
        else:
            print(f"\n✅ Registry normalized successfully")
        
        return 0
    
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())

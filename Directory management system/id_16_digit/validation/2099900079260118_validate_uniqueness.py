"""
doc_id: 2026011822400003
Uniqueness Validator - Ensure all IDs are unique across filesystem and registry.

Checks:
1. No duplicate IDs in filesystem
2. No duplicate IDs in registry
3. Filesystem ↔ Registry synchronization
"""

import sys
import csv
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry_store import RegistryStore


class UniquenessValidator:
    """Validates ID uniqueness across filesystem and registry."""

    def __init__(self, scan_csv_path: str, registry_path: str):
        """
        Initialize validator.
        
        Args:
            scan_csv_path: Path to file scan CSV
            registry_path: Path to ID_REGISTRY.json
        """
        self.scan_csv_path = Path(scan_csv_path)
        self.registry_path = Path(registry_path)
        self.registry = RegistryStore(str(registry_path))
        self.errors: List[Dict] = []

    def _read_scan_csv(self) -> Dict[str, str]:
        """
        Read scan CSV and extract ID to path mapping.
        
        Returns:
            Dictionary of {id: file_path}
        """
        id_to_path = {}
        
        if not self.scan_csv_path.exists():
            return id_to_path
        
        try:
            f = open(self.scan_csv_path, 'r', encoding='utf-8', errors='replace')
        except:
            f = open(self.scan_csv_path, 'r', encoding='latin-1')
        
        try:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row.get('doc_id', '').strip()
                file_path = row.get('relative_path', '').strip()
                
                if doc_id and doc_id != 'UNASSIGNED' and len(doc_id) == 16:
                    id_to_path[doc_id] = self.registry.canonicalize_path(file_path)
        finally:
            f.close()
        
        return id_to_path

    def check_filesystem_duplicates(self, fs_ids: Dict[str, str]) -> List[str]:
        """
        Check for duplicate IDs in filesystem.
        
        Args:
            fs_ids: Dictionary of {id: file_path}
            
        Returns:
            List of duplicate IDs
        """
        id_counts = Counter(fs_ids.keys())
        duplicates = [id_val for id_val, count in id_counts.items() if count > 1]
        
        for dup_id in duplicates:
            # Find all files with this ID
            files = [path for id_val, path in fs_ids.items() if id_val == dup_id]
            self.errors.append({
                'type': 'DUPLICATE_IN_FS',
                'id': dup_id,
                'message': f'ID {dup_id} appears in {len(files)} files',
                'files': files
            })
        
        return duplicates

    def check_registry_duplicates(self) -> List[str]:
        """
        Check for duplicate IDs in registry.
        
        Returns:
            List of duplicate IDs
        """
        is_unique, duplicates = self.registry.check_uniqueness()
        
        for dup_id in duplicates:
            self.errors.append({
                'type': 'DUPLICATE_IN_REGISTRY',
                'id': dup_id,
                'message': f'ID {dup_id} appears multiple times in registry'
            })
        
        return duplicates

    def check_sync_errors(self, fs_ids: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """
        Check for sync errors between filesystem and registry.
        
        Args:
            fs_ids: Dictionary of {id: file_path} from filesystem
            
        Returns:
            Tuple of (unregistered_ids, orphaned_ids)
        """
        registry_ids = {
            id_val: self.registry.canonicalize_path(path)
            for id_val, path in self.registry.get_all_active_ids()
        }
        
        fs_id_set = set(fs_ids.keys())
        registry_id_set = set(registry_ids.keys())
        
        # IDs in filesystem but not registry
        unregistered = fs_id_set - registry_id_set
        for id_val in unregistered:
            self.errors.append({
                'type': 'UNREGISTERED',
                'id': id_val,
                'message': f'ID {id_val} in filesystem but not in registry',
                'file': fs_ids[id_val]
            })
        
        # IDs in registry but not filesystem
        orphaned = registry_id_set - fs_id_set
        for id_val in orphaned:
            self.errors.append({
                'type': 'ORPHANED',
                'id': id_val,
                'message': f'ID {id_val} in registry but file not found',
                'registered_path': registry_ids[id_val]
            })
        
        # Check for path mismatches (ID exists in both but path differs)
        common_ids = fs_id_set & registry_id_set
        for id_val in common_ids:
            fs_path = fs_ids[id_val]
            reg_path = registry_ids[id_val]
            
            if fs_path != reg_path:
                self.errors.append({
                    'type': 'PATH_MISMATCH',
                    'id': id_val,
                    'message': f'Path mismatch for ID {id_val}',
                    'filesystem_path': fs_path,
                    'registry_path': reg_path
                })
        
        return list(unregistered), list(orphaned)

    def validate(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            True if all checks pass, False otherwise
        """
        self.errors = []
        
        # Read filesystem state
        fs_ids = self._read_scan_csv()
        
        # Run checks
        fs_duplicates = self.check_filesystem_duplicates(fs_ids)
        registry_duplicates = self.check_registry_duplicates()
        unregistered, orphaned = self.check_sync_errors(fs_ids)
        
        return len(self.errors) == 0

    def print_report(self):
        """Print validation report to stdout."""
        if len(self.errors) == 0:
            print("✅ PASS: All IDs unique and synced")
            print(f"\nSummary:")
            stats = self.registry.get_stats()
            print(f"  - Active IDs: {stats['active_allocations']}")
            print(f"  - Registry version: {stats['registry_version']}")
            return
        
        print(f"❌ FAIL: {len(self.errors)} errors found")
        print()
        
        # Group errors by type
        errors_by_type = {}
        for error in self.errors:
            error_type = error['type']
            if error_type not in errors_by_type:
                errors_by_type[error_type] = []
            errors_by_type[error_type].append(error)
        
        # Print errors by type
        for error_type, type_errors in errors_by_type.items():
            print(f"{error_type}: {len(type_errors)} errors")
            for error in type_errors[:10]:  # Limit to 10 per type
                print(f"  - {error['message']}")
                if 'files' in error:
                    for file in error['files'][:5]:
                        print(f"    • {file}")
                elif 'file' in error:
                    print(f"    • {error['file']}")
                elif 'filesystem_path' in error:
                    print(f"    • FS: {error['filesystem_path']}")
                    print(f"    • REG: {error['registry_path']}")
            
            if len(type_errors) > 10:
                print(f"  ... and {len(type_errors) - 10} more")
            print()


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate ID uniqueness across filesystem and registry'
    )
    parser.add_argument(
        'scan_csv',
        help='Path to file scan CSV'
    )
    parser.add_argument(
        'registry',
        help='Path to ID_REGISTRY.json'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output errors as JSON'
    )
    
    args = parser.parse_args()
    
    validator = UniquenessValidator(args.scan_csv, args.registry)
    is_valid = validator.validate()
    
    if args.json:
        import json
        print(json.dumps({
            'valid': is_valid,
            'error_count': len(validator.errors),
            'errors': validator.errors
        }, indent=2))
    else:
        validator.print_report()
    
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()

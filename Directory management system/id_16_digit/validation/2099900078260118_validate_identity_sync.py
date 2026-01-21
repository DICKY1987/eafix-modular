"""
doc_id: 2026011822400004
Identity Sync Validator - Ensure registry and filesystem are synchronized.

Checks:
1. IDs in filesystem but not registered (unregistered files)
2. IDs in registry but files missing/moved (stale paths)
3. Path mismatches (moved files without registry update)
"""

import sys
import csv
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.registry_store import RegistryStore


class SyncValidator:
    """Validates synchronization between filesystem and registry."""

    def __init__(self, scan_csv_path: str, registry_path: str):
        """
        Initialize sync validator.
        
        Args:
            scan_csv_path: Path to file scan CSV
            registry_path: Path to ID_REGISTRY.json
        """
        self.scan_csv_path = Path(scan_csv_path)
        self.registry_path = Path(registry_path)
        self.registry = RegistryStore(str(registry_path))
        self.issues: List[Dict] = []

    def _read_scan_csv(self) -> Dict[str, str]:
        """Read scan CSV and extract ID to path mapping."""
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

    def validate_sync(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Validate sync between filesystem and registry.
        
        Returns:
            Tuple of (unregistered, stale_paths, mismatches)
        """
        self.issues = []
        
        fs_ids = self._read_scan_csv()
        registry_ids = {
            id_val: self.registry.canonicalize_path(path)
            for id_val, path in self.registry.get_all_active_ids()
        }
        
        fs_id_set = set(fs_ids.keys())
        registry_id_set = set(registry_ids.keys())
        
        # Unregistered: in filesystem but not registry
        unregistered = []
        for id_val in fs_id_set - registry_id_set:
            issue = {
                'type': 'unregistered',
                'id': id_val,
                'file_path': fs_ids[id_val],
                'message': f'File has ID but not registered: {fs_ids[id_val]}'
            }
            unregistered.append(issue)
            self.issues.append(issue)
        
        # Stale paths: in registry but not filesystem
        stale_paths = []
        for id_val in registry_id_set - fs_id_set:
            issue = {
                'type': 'stale_path',
                'id': id_val,
                'registered_path': registry_ids[id_val],
                'message': f'Registry entry for missing file: {registry_ids[id_val]}'
            }
            stale_paths.append(issue)
            self.issues.append(issue)
        
        # Path mismatches: ID exists in both but paths differ
        mismatches = []
        for id_val in fs_id_set & registry_id_set:
            fs_path = fs_ids[id_val]
            reg_path = registry_ids[id_val]
            
            if fs_path != reg_path:
                issue = {
                    'type': 'path_mismatch',
                    'id': id_val,
                    'filesystem_path': fs_path,
                    'registry_path': reg_path,
                    'message': f'Path mismatch for ID {id_val}'
                }
                mismatches.append(issue)
                self.issues.append(issue)
        
        return unregistered, stale_paths, mismatches

    def print_report(self):
        """Print sync validation report."""
        unregistered, stale_paths, mismatches = self.validate_sync()
        
        if not self.issues:
            print("✅ SYNC PASS: Filesystem and registry are synchronized")
            stats = self.registry.get_stats()
            print(f"\nSummary:")
            print(f"  - Active IDs: {stats['active_allocations']}")
            print(f"  - Registry version: {stats['registry_version']}")
            return
        
        print(f"❌ SYNC FAIL: {len(self.issues)} sync issues found")
        print()
        
        if unregistered:
            print(f"UNREGISTERED FILES: {len(unregistered)}")
            print("  Files with IDs not in registry:")
            for issue in unregistered[:10]:
                print(f"  - {issue['id']}: {issue['file_path']}")
            if len(unregistered) > 10:
                print(f"  ... and {len(unregistered) - 10} more")
            print()
        
        if stale_paths:
            print(f"STALE REGISTRY PATHS: {len(stale_paths)}")
            print("  Registry entries for missing/moved files:")
            for issue in stale_paths[:10]:
                print(f"  - {issue['id']}: {issue['registered_path']}")
            if len(stale_paths) > 10:
                print(f"  ... and {len(stale_paths) - 10} more")
            print()
        
        if mismatches:
            print(f"PATH MISMATCHES: {len(mismatches)}")
            print("  Files moved without registry update:")
            for issue in mismatches[:10]:
                print(f"  - {issue['id']}:")
                print(f"    FS:  {issue['filesystem_path']}")
                print(f"    REG: {issue['registry_path']}")
            if len(mismatches) > 10:
                print(f"  ... and {len(mismatches) - 10} more")
            print()


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate sync between filesystem and registry'
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
        help='Output issues as JSON'
    )
    
    args = parser.parse_args()
    
    validator = SyncValidator(args.scan_csv, args.registry)
    validator.validate_sync()
    
    if args.json:
        import json
        print(json.dumps({
            'synced': len(validator.issues) == 0,
            'issue_count': len(validator.issues),
            'issues': validator.issues
        }, indent=2))
    else:
        validator.print_report()
    
    sys.exit(0 if len(validator.issues) == 0 else 1)


if __name__ == '__main__':
    main()

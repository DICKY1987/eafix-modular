#!/usr/bin/env python3
# doc_id: 2026011823400001
"""
Apply IDs to Filenames - Rename files with their allocated IDs from registry.

Usage:
    python apply_ids_to_filenames.py --dry-run
    python apply_ids_to_filenames.py --apply
    python apply_ids_to_filenames.py --apply --limit 10
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Tuple, Dict
import json

sys.path.insert(0, str(Path(__file__).parent))

from core.registry_store import RegistryStore


def rename_file_with_id(registry: RegistryStore, dry_run: bool = True, limit: int = None) -> Tuple[int, int, int]:
    """
    Rename files to include their allocated IDs.
    
    Args:
        registry: Registry store instance
        dry_run: If True, only show what would be renamed
        limit: Maximum number of files to rename (None for all)
    
    Returns:
        Tuple of (renamed_count, skipped_count, error_count)
    """
    renamed = 0
    skipped = 0
    errors = 0
    
    # Read registry
    with registry._lock():
        data = registry._read_registry()
    
    allocations = data.get('allocations', [])
    
    print(f"\n{'=' * 70}")
    print(f"{'DRY RUN - ' if dry_run else ''}RENAMING FILES WITH ALLOCATED IDs")
    print(f"{'=' * 70}\n")
    print(f"Total allocations to process: {len(allocations)}")
    if limit:
        print(f"Limiting to: {limit} files")
    print()
    
    repo_root = Path(__file__).parent.parent
    
    for i, alloc in enumerate(allocations):
        if limit and renamed >= limit:
            print(f"\n✓ Reached limit of {limit} renames")
            break
        
        doc_id = alloc.get('id', '')
        file_path = alloc.get('file_path', '')
        status = alloc.get('status', '')
        
        # Skip non-active allocations
        if status != 'active':
            skipped += 1
            continue
        
        # Skip if no file path
        if not file_path:
            skipped += 1
            continue
        
        # Get full path
        full_path = repo_root / file_path
        
        # Check if file exists
        if not full_path.exists():
            skipped += 1
            continue
        
        # Get filename components
        filename = full_path.name
        
        # Check if filename already has an ID prefix (16 digits + underscore)
        if len(filename) > 17 and filename[16] == '_' and filename[:16].isdigit():
            skipped += 1
            continue
        
        # Create new filename with ID prefix
        new_filename = f"{doc_id}_{filename}"
        new_path = full_path.parent / new_filename
        
        # Check if new path already exists
        if new_path.exists() and new_path != full_path:
            print(f"  ✗ Target exists: {new_filename}")
            errors += 1
            continue
        
        # Display what will be done
        if renamed < 10 or not dry_run:
            print(f"  {'[DRY RUN] ' if dry_run else '✓ '}{filename}")
            print(f"    → {new_filename}")
        
        # Perform rename if not dry run
        if not dry_run:
            try:
                full_path.rename(new_path)
                renamed += 1
                
                # Try to update registry with new path (non-critical)
                try:
                    new_relative_path = str(new_path.relative_to(repo_root)).replace('\\', '/')
                    registry.update_file_path(doc_id, new_relative_path)
                except Exception as reg_err:
                    pass  # Registry update is non-critical, file was renamed successfully
                
            except Exception as e:
                print(f"  ✗ Error renaming {filename}: {e}")
                errors += 1
        else:
            renamed += 1
    
    if renamed > 10 and dry_run:
        print(f"  ... and {renamed - 10} more files")
    
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"{'Would rename' if dry_run else 'Renamed'}:  {renamed}")
    print(f"Skipped:   {skipped} (already have ID, not found, or deprecated)")
    print(f"Errors:    {errors}")
    print(f"{'=' * 70}\n")
    
    return renamed, skipped, errors


def main():
    parser = argparse.ArgumentParser(
        description="Apply allocated IDs to filenames"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be renamed without actually renaming'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually rename the files'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of files to rename'
    )
    parser.add_argument(
        '--registry',
        default='registry/ID_REGISTRY.json',
        help='Path to registry file (default: registry/ID_REGISTRY.json)'
    )
    
    args = parser.parse_args()
    
    # Default to dry-run if neither specified
    dry_run = not args.apply
    
    if args.apply:
        response = input("\n⚠️  This will rename files in the repository. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    # Initialize registry
    registry = RegistryStore(args.registry)
    
    # Perform rename
    renamed, skipped, errors = rename_file_with_id(
        registry,
        dry_run=dry_run,
        limit=args.limit
    )
    
    if dry_run:
        print("ℹ️  This was a dry run. Use --apply to actually rename files.")
    else:
        print("✅ File renaming complete!")
        if errors > 0:
            print(f"⚠️  {errors} errors occurred during renaming.")


if __name__ == '__main__':
    main()

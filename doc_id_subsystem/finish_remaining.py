#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0001
"""
Finish tagging remaining eligible files with doc IDs.
"""
import json
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from batch_assign_docids import (
    load_inventory,
    load_registry,
    determine_category,
    inject_doc_id,
    save_registry
)

def finish_remaining_files():
    """Tag all remaining eligible files (exclude unsupported types)."""
    
    print("\n" + "="*60)
    print("FINISHING REMAINING DOC ID ASSIGNMENTS")
    print("="*60)
    
    # Load current state
    inventory = load_inventory()
    registry = load_registry()
    
    # Get files needing doc IDs (exclude unsupported types)
    unsupported_types = {'sh', 'ps1', 'bat', 'toml', 'unknown'}
    missing_files = [
        item for item in inventory
        if item.get('status') != 'registered' and item.get('file_type') not in unsupported_types
    ]
    
    print(f"\nFound {len(missing_files)} eligible files needing doc IDs")
    
    if not missing_files:
        print("✅ All eligible files already have doc IDs!")
        return
    
    # Process each file
    success_count = 0
    fail_count = 0
    
    for idx, item in enumerate(missing_files, 1):
        path = item['path']
        file_type = item['file_type']
        
        # Classify and assign
        category = determine_category(path)
        next_id = registry['categories'][category]['next_id']
        prefix = registry['categories'][category]['prefix']
        doc_id = f"DOC-{prefix}-{next_id:04d}"
        
        print(f"\n{idx}. {path}")
        print(f"   Category: {category}, Doc ID: {doc_id}")
        
        # Inject doc ID
        full_path = Path.cwd().parent / path  # Go up one level from doc_id_subsystem
        try:
            if inject_doc_id(full_path, doc_id, dry_run=False):
                print(f"    ✅ Injected {doc_id}")
                
                # Update registry
                registry['categories'][category]['next_id'] += 1
                registry['categories'][category]['count'] += 1
                
                # Add to docs list
                registry['docs'].append({
                    'doc_id': doc_id,
                    'path': path,
                    'category': category,
                    'file_type': file_type,
                    'assigned_date': '2026-01-09'
                })
                
                success_count += 1
            else:
                print(f"    ⚠️  Failed to inject")
                fail_count += 1
        except Exception as e:
            print(f"    ❌ Error: {e}")
            fail_count += 1
    
    # Update metadata
    registry['metadata']['last_updated'] = '2026-01-09'
    registry['metadata']['total_docs'] = len(registry['docs'])
    
    # Save registry
    print("\nUpdating registry...")
    save_registry(registry)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Processed: {len(missing_files)} files")
    print(f"Success:   {success_count} files")
    print(f"Failed:    {fail_count} files")
    print("\nCategory ID allocations:")
    for cat_name, cat_data in registry['categories'].items():
        if cat_data['count'] > 0:
            print(f"  {cat_name:12s}: {cat_data['count']} IDs")
    print("="*60)
    print("\n✅ Registry updated!")
    print("   Next steps:")
    print("   1. Re-scan: python core/doc_id_scanner.py")
    print("   2. Validate coverage")
    print("   3. Commit changes")

if __name__ == "__main__":
    finish_remaining_files()

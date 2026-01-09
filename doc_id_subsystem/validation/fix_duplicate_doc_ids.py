#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-FIX-DUPLICATE-DOC-IDS-003
"""
Fix Duplicate DOC_IDs

PURPOSE: Find and fix duplicate doc_ids in the inventory
PATTERN: PATTERN-DOC-ID-FIX-DUPLICATES-001

USAGE:
    python doc_id/fix_duplicate_doc_ids.py analyze
    python doc_id/fix_duplicate_doc_ids.py fix --dry-run
    python doc_id/fix_duplicate_doc_ids.py fix
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, INVENTORY_PATH
from common.utils import load_jsonl, save_jsonl


def analyze_duplicates() -> Dict[str, List[dict]]:
    """Find all duplicate doc_ids in inventory."""
    doc_id_map = defaultdict(list)
    
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry.get('doc_id') and entry.get('status') == 'registered':
                file_path = REPO_ROOT / entry['path']
                if file_path.is_symlink():
                    continue
                doc_id_map[entry['doc_id']].append(entry)
    
    # Filter to only duplicates
    duplicates = {doc_id: entries for doc_id, entries in doc_id_map.items() if len(entries) > 1}
    
    return duplicates


def print_duplicate_analysis(duplicates: Dict[str, List[dict]]):
    """Print analysis of duplicate doc_ids."""
    print("=" * 70)
    print(f"DUPLICATE DOC_ID ANALYSIS")
    print("=" * 70)
    print(f"\nFound {len(duplicates)} unique doc_ids with duplicates")
    print(f"Total duplicate entries: {sum(len(entries) for entries in duplicates.values())}\n")
    
    # Group by count
    by_count = defaultdict(list)
    for doc_id, entries in duplicates.items():
        by_count[len(entries)].append(doc_id)
    
    print("By occurrence count:")
    for count in sorted(by_count.keys(), reverse=True):
        doc_ids = by_count[count]
        print(f"  {count} occurrences: {len(doc_ids)} doc_ids")
        for doc_id in sorted(doc_ids)[:3]:  # Show first 3
            print(f"    - {doc_id}")
        if len(doc_ids) > 3:
            print(f"    ... and {len(doc_ids) - 3} more")
    
    print("\nMost duplicated (top 10):")
    sorted_dupes = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
    for doc_id, entries in sorted_dupes[:10]:
        print(f"\n  {doc_id} ({len(entries)} occurrences):")
        for entry in entries[:5]:  # Show first 5 paths
            print(f"    - {entry['path']}")
        if len(entries) > 5:
            print(f"    ... and {len(entries) - 5} more")


def generate_unique_doc_id(base_doc_id: str, file_path: str, seen_ids: set) -> str:
    """Generate unique doc_id based on file type and path."""
    # Extract base pattern: DOC-PATTERN-ATOMIC-CREATE-TEMPLATE-001 -> DOC-PATTERN-ATOMIC-CREATE-TEMPLATE
    match = re.match(r'^(DOC-[A-Z]+-[A-Z-]+?)-\d{3}$', base_doc_id)
    if not match:
        # Try without trailing number
        match = re.match(r'^(DOC-[A-Z]+-[A-Z-]+)$', base_doc_id)
    
    if match:
        base = match.group(1)
    else:
        # Fallback: extract prefix only
        prefix_match = re.match(r'^(DOC-[A-Z]+)-', base_doc_id)
        if prefix_match:
            base = prefix_match.group(1)
            stem = Path(file_path).stem.upper().replace('_', '-')
            base = f"{base}-{stem}"
        else:
            base = base_doc_id.rsplit('-', 1)[0] if '-' in base_doc_id else base_doc_id
    
    # Determine file type suffix (keep it SHORT and descriptive)
    path_obj = Path(file_path)
    filename = path_obj.name.lower()
    stem = path_obj.stem.lower()
    
    # Special handling for __init__.py files
    if filename == '__init__.py':
        suffix = 'INIT'
    elif 'pattern.yaml' in filename or 'pattern.yml' in filename:
        suffix = 'SPEC'
    elif 'schema.json' in filename:
        suffix = 'SCHEMA'
    elif 'schema.id.yaml' in filename or 'schema.id.yml' in filename:
        suffix = 'SCHEMA-ID'
    elif 'instance_full' in stem:
        suffix = 'FULL'
    elif 'instance_minimal' in stem:
        suffix = 'MIN'
    elif 'instance_test' in stem:
        suffix = 'TEST'
    elif 'executor' in stem and path_obj.suffix == '.ps1':
        suffix = 'EXEC'
    elif 'conftest' in stem:
        suffix = 'CONF'
    elif 'mock_' in stem:
        suffix = 'MOCK'
    elif stem.startswith('test_') and path_obj.suffix == '.py':
        suffix = 'TEST'
    elif 'readme' in stem.lower():
        suffix = 'README'
    elif path_obj.suffix == '.json':
        suffix = 'JSON'
    elif path_obj.suffix in ['.yaml', '.yml']:
        suffix = 'YAML'
    elif path_obj.suffix == '.md':
        suffix = 'MD'
    elif path_obj.suffix == '.py':
        suffix = 'PY'
    elif path_obj.suffix == '.ps1':
        suffix = 'PS1'
    elif path_obj.suffix == '.txt':
        suffix = 'TXT'
    else:
        suffix = 'FILE'
    
    # Generate unique ID with counter
    counter = 1
    if base.endswith(f"-{suffix}"):
        new_doc_id = f"{base}-{counter:03d}"
    else:
        new_doc_id = f"{base}-{suffix}-{counter:03d}"
    
    while new_doc_id in seen_ids:
        counter += 1
        if base.endswith(f"-{suffix}"):
            new_doc_id = f"{base}-{counter:03d}"
        else:
            new_doc_id = f"{base}-{suffix}-{counter:03d}"
    
    return new_doc_id


def fix_duplicates(dry_run: bool = True):
    """Fix duplicate doc_ids by assigning unique IDs (Option A: unique per file)."""
    duplicates = analyze_duplicates()
    
    if not duplicates:
        print("✅ No duplicate doc_ids found!")
        return
    
    print(f"{'=' * 70}")
    print(f"FIXING {len(duplicates)} DUPLICATE DOC_IDS (Option A: Unique per file)")
    print(f"{'=' * 70}\n")
    
    # Load all entries
    all_entries = []
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            all_entries.append(json.loads(line.strip()))
    
    # Track changes
    changes = []
    seen_doc_ids = set()
    
    # First pass: collect all existing doc_ids
    for entry in all_entries:
        doc_id = entry.get('doc_id')
        if doc_id and entry.get('status') == 'registered' and doc_id not in duplicates:
            seen_doc_ids.add(doc_id)
    
    # Second pass: fix duplicates
    for entry in all_entries:
        doc_id = entry.get('doc_id')
        
        if not doc_id or entry.get('status') != 'registered':
            continue
        
        # If this is a duplicate
        if doc_id in duplicates:
            if doc_id in seen_doc_ids:
                # This is a duplicate occurrence - needs new ID
                new_doc_id = generate_unique_doc_id(doc_id, entry['path'], seen_doc_ids)
                
                changes.append({
                    'path': entry['path'],
                    'old_id': doc_id,
                    'new_id': new_doc_id
                })
                
                entry['doc_id'] = new_doc_id
                seen_doc_ids.add(new_doc_id)
            else:
                # First occurrence - keep it
                seen_doc_ids.add(doc_id)
    
    # Report changes
    print(f"{'DRY RUN: Would change' if dry_run else 'Changing'} {len(changes)} entries:\n")
    
    # Group by pattern for better readability
    by_pattern = {}
    for change in changes:
        pattern_name = Path(change['path']).parts[1] if len(Path(change['path']).parts) > 1 else 'other'
        if pattern_name not in by_pattern:
            by_pattern[pattern_name] = []
        by_pattern[pattern_name].append(change)
    
    # Show grouped changes
    shown = 0
    for pattern_name, pattern_changes in sorted(by_pattern.items()):
        if shown >= 15:  # Limit output
            break
        print(f"\n  Pattern: {pattern_name}")
        for change in pattern_changes[:5]:  # Show first 5 per pattern
            print(f"    {Path(change['path']).name}")
            print(f"      {change['old_id']}")
            print(f"      → {change['new_id']}")
            shown += 1
        if len(pattern_changes) > 5:
            print(f"    ... and {len(pattern_changes) - 5} more in this pattern")
    
    if len(by_pattern) > 15:
        remaining_patterns = len(by_pattern) - 15
        remaining_changes = sum(len(changes) for pattern, changes in list(by_pattern.items())[15:])
        print(f"\n  ... and {remaining_changes} changes across {remaining_patterns} more patterns")
    
    # Save if not dry run
    if not dry_run:
        with open(INVENTORY_PATH, 'w', encoding='utf-8') as f:
            for entry in all_entries:
                f.write(json.dumps(entry) + '\n')
        
        print(f"\n✅ Updated {INVENTORY_PATH}")
        print(f"\n⚠️  Next steps:")
        print(f"   1. Run: python doc_id/apply_doc_id_changes_to_files.py")
        print(f"      (Updates actual files with new doc_ids)")
        print(f"   2. Run: python doc_id/doc_id_scanner.py scan")
        print(f"   3. Run: python doc_id/sync_registries.py sync")
    else:
        print(f"\n💡 Run without --dry-run to apply changes to inventory")


def main():
    parser = argparse.ArgumentParser(description="Fix Duplicate DOC_IDs")
    parser.add_argument('action', choices=['analyze', 'fix'], help='Action to perform')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes')
    
    args = parser.parse_args()
    
    if args.action == 'analyze':
        duplicates = analyze_duplicates()
        print_duplicate_analysis(duplicates)
    elif args.action == 'fix':
        fix_duplicates(dry_run=args.dry_run)


if __name__ == '__main__':
    main()

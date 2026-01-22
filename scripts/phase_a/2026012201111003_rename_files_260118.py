#!/usr/bin/env python3
# doc_id: 2026012201111003
# Phase A3: Rename Files with 260119 → 260118
# Created: 2026-01-22T01:11:41Z

import os
import sys
import json
from pathlib import Path
from typing import List, Tuple

def find_files_with_scope(root_dir: Path, scope: str) -> List[Path]:
    """Find all files containing the scope in filename."""
    matches = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if scope in file:
                file_path = Path(root) / file
                matches.append(file_path)
    
    return matches

def rename_file(file_path: Path, old_scope: str, new_scope: str, dry_run: bool = False) -> Tuple[Path, bool]:
    """Rename a single file, replacing scope in filename."""
    old_name = file_path.name
    new_name = old_name.replace(old_scope, new_scope)
    
    if old_name == new_name:
        return file_path, False
    
    new_path = file_path.parent / new_name
    
    # Check if target already exists
    if new_path.exists():
        print(f"  ⚠️  Target already exists: {new_path.name}")
        return file_path, False
    
    if dry_run:
        print(f"  [DRY RUN] Would rename: {old_name} → {new_name}")
        return new_path, True
    
    # Rename
    try:
        file_path.rename(new_path)
        return new_path, True
    except Exception as e:
        print(f"  ❌ Failed to rename {file_path.name}: {e}")
        return file_path, False

def main():
    repo_root = Path(__file__).parent.parent.parent
    
    old_scope = "260119"
    new_scope = "260118"
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    auto_yes = '--yes' in sys.argv or '-y' in sys.argv
    
    print(f"🔍 Finding files with scope {old_scope}...")
    files_to_rename = find_files_with_scope(repo_root, old_scope)
    
    if not files_to_rename:
        print(f"✅ No files found with scope {old_scope}")
        return 0
    
    print(f"📝 Found {len(files_to_rename)} files to rename:")
    for file in files_to_rename:
        try:
            rel_path = file.relative_to(repo_root)
        except ValueError:
            rel_path = file
        print(f"  • {rel_path}")
    
    print()
    
    # Confirm (unless auto-yes or dry-run)
    if not auto_yes and not dry_run:
        response = input(f"Rename {len(files_to_rename)} files? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Aborted by user")
            return 1
    
    print()
    if dry_run:
        print(f"🔄 DRY RUN: Simulating renames...")
    else:
        print(f"🔄 Renaming files...")
    
    rename_log = []
    success_count = 0
    fail_count = 0
    
    for file in files_to_rename:
        try:
            rel_path = file.relative_to(repo_root)
        except ValueError:
            rel_path = file
        
        new_path, success = rename_file(file, old_scope, new_scope, dry_run=dry_run)
        
        if success:
            try:
                new_rel_path = new_path.relative_to(repo_root)
            except ValueError:
                new_rel_path = new_path
            
            print(f"  ✅ {rel_path} → {new_rel_path.name}")
            rename_log.append({
                'old': str(rel_path),
                'new': str(new_rel_path),
                'success': True,
                'dry_run': dry_run
            })
            success_count += 1
        else:
            print(f"  ❌ Failed: {rel_path}")
            rename_log.append({
                'old': str(rel_path),
                'new': None,
                'success': False,
                'dry_run': dry_run
            })
            fail_count += 1
    
    # Write log
    log_path = repo_root / "backups" / "file_rename_log.json"
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(rename_log, f, indent=2)
    
    print()
    print(f"📊 Summary:")
    print(f"  Renamed: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Log saved to: {log_path}")
    
    if dry_run:
        print("\n💡 This was a dry run. Re-run without --dry-run to apply changes.")
        return 0
    
    if fail_count > 0:
        print("\n⚠️  Some renames failed. Review log before proceeding.")
        return 1
    else:
        print("\n✅ All files renamed successfully!")
        return 0

if __name__ == '__main__':
    sys.exit(main())

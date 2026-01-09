#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_LINK: DOC-SCRIPT-FIX-INVALID-DOC-IDS-002
"""
Fix Invalid DOC_IDs

PURPOSE: Fix doc_ids missing the required -XXX numeric suffix
PATTERN: PATTERN-DOC-ID-FIX-INVALID-001

USAGE:
    python doc_id/fix_invalid_doc_ids.py --dry-run
    python doc_id/fix_invalid_doc_ids.py
"""

import argparse
import json
import re
import sys
import yaml
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT, INVENTORY_PATH, REGISTRY_PATH
from common.rules import DOC_ID_REGEX, validate_doc_id  # Phase 1: Use centralized rules
from common.utils import load_yaml, save_yaml, load_jsonl

# Valid doc_id pattern from common.rules (centralized)
VALID_DOC_ID_REGEX = DOC_ID_REGEX
# Invalid pattern: Missing -### suffix
INVALID_DOC_ID_REGEX = re.compile(r"^(DOC-[A-Z0-9]+-[A-Z0-9-]+)$")


def load_invalid_entries() -> List[dict]:
    """Load entries with invalid doc_ids from inventory."""
    if not INVENTORY_PATH.exists():
        print(f"❌ Inventory not found: {INVENTORY_PATH}")
        sys.exit(1)
    
    invalid = []
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line.strip())
            if entry.get('status') == 'invalid':
                invalid.append(entry)
    
    return invalid


def get_next_id_for_category(category: str) -> int:
    """Get next available ID number for a category from registry."""
    if not REGISTRY_PATH.exists():
        print(f"⚠️  Registry not found: {REGISTRY_PATH}")
        return 1
    
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding='utf-8'))
    
    category_info = registry.get('categories', {}).get(category, {})
    if isinstance(category_info, dict):
        return category_info.get('next_id', 1)
    
    return 1


def extract_category_from_doc_id(doc_id: str) -> str:
    """Extract category from doc_id prefix."""
    match = re.match(r'^DOC-([A-Z]+)-', doc_id)
    if match:
        prefix = match.group(1)
        
        # Map prefix to category
        category_map = {
            'CORE': 'core', 'ERROR': 'error', 'PAT': 'patterns',
            'GUIDE': 'guide', 'SPEC': 'spec', 'TEST': 'test',
            'SCRIPT': 'script', 'CONFIG': 'config', 'AIM': 'aim',
            'PM': 'pm', 'ENGINE': 'engine', 'GUI': 'gui',
        }
        
        return category_map.get(prefix, 'unknown')
    
    return 'unknown'


def normalize_doc_id(doc_id: str) -> str:
    """Normalize doc_id to allowed characters and structure."""
    normalized = doc_id.strip().upper()
    normalized = normalized.replace("_", "-").replace(".", "-")
    normalized = re.sub(r"[^A-Z0-9-]", "", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if re.search(r"-X+$", normalized):
        normalized = re.sub(r"-X+$", "", normalized).strip("-")
    return normalized


def generate_fixed_doc_id(invalid_doc_id: str) -> Tuple[str, str]:
    """Generate a valid doc_id by normalizing and adding numeric suffix if needed."""
    normalized = normalize_doc_id(invalid_doc_id)
    category = extract_category_from_doc_id(normalized)
    next_id = get_next_id_for_category(category)
    
    if VALID_DOC_ID_REGEX.match(normalized):
        return normalized, category
    
    if re.search(r"-\d{3}$", normalized):
        normalized = re.sub(r"-\d{3}$", "", normalized).strip("-")
    
    fixed_doc_id = f"{normalized}-{next_id:03d}"
    
    return fixed_doc_id, category


def fix_doc_id_in_file(file_path: Path, old_doc_id: str, new_doc_id: str, dry_run: bool = True) -> bool:
    """Replace invalid doc_id in file with valid one."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"⚠️  Could not read {file_path}: {e}")
        return False
    
    # Try different patterns
    patterns = [
        (r'# DOC_ID:\s*' + re.escape(old_doc_id), f'# DOC_ID: {new_doc_id}'),
        (r'DOC_ID:\s*' + re.escape(old_doc_id), f'DOC_ID: {new_doc_id}'),
        (r'# DOC_LINK:\s*' + re.escape(old_doc_id), f'# DOC_LINK: {new_doc_id}'),
        (r'DOC_LINK:\s*' + re.escape(old_doc_id), f'DOC_LINK: {new_doc_id}'),
        (r'^doc_id:\s*' + re.escape(old_doc_id), f'doc_id: {new_doc_id}'),
        (r'^doc_id:\s*[\'"]?' + re.escape(old_doc_id) + r'[\'"]?', f'doc_id: {new_doc_id}'),
        (r'"doc_id"\s*:\s*"' + re.escape(old_doc_id) + r'"', f'"doc_id": "{new_doc_id}"'),
    ]
    
    new_content = content
    replaced = False
    
    for pattern, replacement in patterns:
        if re.search(pattern, new_content, flags=re.MULTILINE):
            new_content = re.sub(pattern, replacement, new_content, flags=re.MULTILINE)
            replaced = True
            break
    
    if not replaced:
        print(f"⚠️  Could not find doc_id pattern in {file_path}")
        return False
    
    if not dry_run:
        file_path.write_text(new_content, encoding='utf-8')
        print(f"✓ Fixed {file_path}")
    else:
        print(f"Would fix {file_path}: {old_doc_id} -> {new_doc_id}")
    
    return True


def update_registry_next_id(category: str, new_next_id: int, dry_run: bool = True):
    """Update next_id in registry for a category."""
    if not REGISTRY_PATH.exists():
        return
    
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding='utf-8'))
    
    if 'categories' in registry and category in registry['categories']:
        if isinstance(registry['categories'][category], dict):
            old_next_id = registry['categories'][category].get('next_id', 1)
            if new_next_id > old_next_id:
                registry['categories'][category]['next_id'] = new_next_id
                
                if not dry_run:
                    REGISTRY_PATH.write_text(
                        yaml.dump(registry, sort_keys=False, allow_unicode=True),
                        encoding='utf-8'
                    )


def main():
    parser = argparse.ArgumentParser(description="Fix Invalid DOC_IDs")
    parser.add_argument('--dry-run', action='store_true', help='Preview changes')
    
    args = parser.parse_args()
    
    print("=== Fixing Invalid DOC_IDs ===\n")
    
    invalid_entries = load_invalid_entries()
    
    if not invalid_entries:
        print("✅ No invalid doc_ids found!")
        return
    
    print(f"Found {len(invalid_entries)} invalid doc_ids\n")
    
    fixed_count = 0
    category_updates = {}
    
    for entry in invalid_entries:
        old_doc_id = entry['doc_id']
        file_path = REPO_ROOT / entry['path']
        
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
        
        new_doc_id, category = generate_fixed_doc_id(old_doc_id)
        
        print(f"\nFile: {entry['path']}")
        print(f"  Old: {old_doc_id}")
        print(f"  New: {new_doc_id}")
        print(f"  Category: {category}")
        
        if fix_doc_id_in_file(file_path, old_doc_id, new_doc_id, dry_run=args.dry_run):
            fixed_count += 1
            
            # Track next_id updates
            match = re.search(r'-(\d{3})$', new_doc_id)
            if match:
                id_num = int(match.group(1))
                if category not in category_updates:
                    category_updates[category] = id_num + 1
                else:
                    category_updates[category] = max(category_updates[category], id_num + 1)
    
    print(f"\n{'=' * 50}")
    print(f"{'Would fix' if args.dry_run else 'Fixed'} {fixed_count}/{len(invalid_entries)} files")
    
    # Update registry next_id values
    if category_updates:
        print(f"\nRegistry updates needed:")
        for category, next_id in category_updates.items():
            print(f"  {category}: next_id = {next_id}")
            update_registry_next_id(category, next_id, dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"\n💡 Run without --dry-run to apply changes")
    else:
        print(f"\n✅ All fixes applied!")
        print(f"\n⚠️  Remember to:")
        print(f"   1. Run: python doc_id/doc_id_scanner.py scan")
        print(f"   2. Run: python doc_id/sync_registries.py sync")


if __name__ == '__main__':
    main()

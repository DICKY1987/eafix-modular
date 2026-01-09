#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-1013
"""
Batch Doc ID Assignment Script

PURPOSE: Assign doc_ids to files missing them in batches
STATUS: active
"""

import json
import re
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Paths - adjusted for eafix-modular structure
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent
INVENTORY_PATH = BASE_DIR / "registry" / "docs_inventory.jsonl"
REGISTRY_PATH = BASE_DIR / "registry" / "DOC_ID_REGISTRY.yaml"

def load_inventory():
    """Load the docs inventory"""
    entries = []
    with open(INVENTORY_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries

def load_registry():
    """Load the YAML registry"""
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_registry(registry):
    """Save the updated registry"""
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False)

def determine_category(path: str) -> str:
    """Determine doc_id category based on file path for eafix-modular"""
    path_lower = path.lower().replace('\\', '/')
    
    # Services
    if '/services/' in path_lower:
        if '/src/' in path_lower:
            if 'main.py' in path_lower or 'router' in path_lower:
                return 'api'
            elif 'models.py' in path_lower or 'schema' in path_lower:
                return 'model'
            else:
                return 'service'
        elif '/tests/' in path_lower:
            return 'test'
        else:
            return 'service'
    
    # Shared modules
    if '/shared/' in path_lower:
        return 'shared'
    
    # Tests
    if '/tests/' in path_lower or 'test_' in path_lower or path_lower.endswith('_test.py'):
        return 'test'
    
    # Contracts
    if '/contracts/' in path_lower or 'contract' in path_lower:
        return 'contract'
    
    # Scripts
    if '/scripts/' in path_lower or '/ci/' in path_lower or path_lower.endswith('.sh'):
        return 'script'
    
    # Infrastructure
    if any(x in path_lower for x in ['/deploy/', '/dag/', 'docker', 'compose']):
        return 'infra'
    
    # Documentation
    if path_lower.endswith(('.md', '.rst', '.txt')):
        if 'readme' in path_lower or '/docs/' in path_lower:
            return 'doc'
    
    # Configuration
    if path_lower.endswith(('.yaml', '.yml', '.json', '.toml', '.ini', '.env')):
        return 'config'
    
    # Legacy P_ directories
    if '/p_' in path_lower or path_lower.startswith('p_'):
        return 'legacy'
    
    # Default based on extension
    if path_lower.endswith('.py'):
        return 'service'
    
    return 'config'

def generate_doc_id(category: str, next_id: int) -> str:
    """Generate a doc_id for the given category"""
    category_prefix_map = {
        'service': 'SERVICE',
        'api': 'API',
        'model': 'MODEL',
        'shared': 'SHARED',
        'test': 'TEST',
        'config': 'CONFIG',
        'script': 'SCRIPT',
        'contract': 'CONTRACT',
        'infra': 'INFRA',
        'doc': 'DOC',
        'legacy': 'LEGACY',
        'spec': 'SPEC',
        'test': 'TEST',
        'script': 'SCRIPT',
        'config': 'CONFIG',
    }
    
    prefix = category_prefix_map.get(category, 'SCRIPT')
    return f"DOC-{prefix}-{next_id:04d}"

def inject_doc_id_python(file_path: Path, doc_id: str) -> bool:
    """Inject doc_id into Python file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if already has doc_id
        if re.search(r'DOC[-_]ID:', content, re.IGNORECASE):
            return False
        
        lines = content.splitlines(keepends=True)
        insert_idx = 0
        
        # Skip shebang
        if lines and lines[0].startswith('#!'):
            insert_idx = 1
        
        # Skip encoding declaration
        if insert_idx < len(lines) and 'coding' in lines[insert_idx]:
            insert_idx += 1
        
        # Insert doc_id comment
        doc_id_line = f"# DOC_ID: {doc_id}\n"
        lines.insert(insert_idx, doc_id_line)
        
        file_path.write_text(''.join(lines), encoding='utf-8')
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

def inject_doc_id_markdown(file_path: Path, doc_id: str) -> bool:
    """Inject doc_id into Markdown file with YAML frontmatter"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if already has doc_id
        if re.search(r'doc_id:', content, re.IGNORECASE):
            return False
        
        # Check if has frontmatter
        if content.startswith('---\n'):
            # Insert into existing frontmatter
            lines = content.splitlines(keepends=True)
            # Find end of frontmatter
            end_idx = None
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    end_idx = i
                    break
            
            if end_idx:
                # Insert before closing ---
                lines.insert(end_idx, f"doc_id: {doc_id}\n")
                file_path.write_text(''.join(lines), encoding='utf-8')
                return True
        
        # Add new frontmatter
        new_content = f"---\ndoc_id: {doc_id}\n---\n\n{content}"
        file_path.write_text(new_content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

def inject_doc_id_yaml(file_path: Path, doc_id: str) -> bool:
    """Inject doc_id into YAML file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if already has doc_id
        if re.search(r'doc_id:', content, re.IGNORECASE):
            return False
        
        # Add at beginning
        new_content = f"doc_id: {doc_id}\n{content}"
        file_path.write_text(new_content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

def inject_doc_id_json(file_path: Path, doc_id: str) -> bool:
    """Inject doc_id into JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if already has doc_id
        if 'doc_id' in data:
            return False
        
        # Add doc_id at beginning
        data = {'doc_id': doc_id, **data}
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"    Error: {e}")
        return False

def inject_doc_id(file_path: Path, doc_id: str, dry_run=True):
    """Inject doc_id into file based on type"""
    if dry_run:
        print(f"    [DRY-RUN] Would inject {doc_id}")
        return True
    
    suffix = file_path.suffix.lower()
    
    if suffix == '.py':
        result = inject_doc_id_python(file_path, doc_id)
    elif suffix == '.md':
        result = inject_doc_id_markdown(file_path, doc_id)
    elif suffix in ['.yaml', '.yml']:
        result = inject_doc_id_yaml(file_path, doc_id)
    elif suffix == '.json':
        result = inject_doc_id_json(file_path, doc_id)
    else:
        print(f"    Unsupported file type: {suffix}")
        return False
    
    if result:
        print(f"    ✅ Injected {doc_id}")
    else:
        print(f"    ⚠️  Already has doc_id or failed")
    
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Batch assign doc_ids to Python files')
    parser.add_argument('--limit', type=int, default=50, help='Max files to process')
    parser.add_argument('--execute', action='store_true', help='Actually modify files (default is dry-run)')
    parser.add_argument('--filter', choices=['py', 'all'], default='py', help='File type filter')
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    print(f"\n{'='*60}")
    print(f"Batch Doc ID Assignment")
    print(f"{'='*60}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print(f"Limit: {args.limit} files")
    print(f"Filter: {args.filter}")
    print(f"{'='*60}\n")
    
    # Load data
    print("Loading inventory...")
    inventory = load_inventory()
    
    print("Loading registry...")
    registry = load_registry()
    
    # Filter for missing doc_ids
    missing = [
        e for e in inventory 
        if e.get('status') == 'missing' and 
           (args.filter == 'all' or e.get('file_type') == args.filter)
    ]
    
    print(f"\nFound {len(missing)} files needing doc_ids")
    print(f"Processing first {min(args.limit, len(missing))} files...\n")
    
    # Track category counters
    category_counts = {}
    for cat_name, cat_data in registry['categories'].items():
        category_counts[cat_name] = cat_data.get('next_id', 1)
    
    processed = 0
    success = 0
    
    for entry in missing[:args.limit]:
        path_str = entry['path']
        file_path = REPO_ROOT / path_str
        
        # Determine category
        category = determine_category(path_str)
        
        # Generate doc_id
        next_id = category_counts.get(category, 1)
        doc_id = generate_doc_id(category, next_id)
        
        print(f"{processed+1}. {path_str}")
        print(f"   Category: {category}, Doc ID: {doc_id}")
        
        # Inject doc_id
        if inject_doc_id(file_path, doc_id, dry_run):
            category_counts[category] = next_id + 1
            success += 1
        
        processed += 1
        print()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Processed: {processed} files")
    print(f"Success:   {success} files")
    print(f"Failed:    {processed - success} files")
    print(f"\nCategory ID allocations:")
    for cat, next_id in category_counts.items():
        original = registry['categories'][cat].get('next_id', 1)
        used = next_id - original
        if used > 0:
            print(f"  {cat:12s}: {original:4d} -> {next_id:4d} ({used} used)")
    print(f"{'='*60}\n")
    
    # Update registry if not dry run and success > 0
    if not dry_run and success > 0:
        print("Updating registry...")
        for cat_name in category_counts:
            registry['categories'][cat_name]['next_id'] = category_counts[cat_name]
            registry['categories'][cat_name]['count'] = registry['categories'][cat_name].get('count', 0) + (category_counts[cat_name] - registry['categories'][cat_name].get('next_id', 1))
        
        registry['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        registry['metadata']['total_docs'] = registry['metadata'].get('total_docs', 0) + success
        
        save_registry(registry)
        print("✅ Registry updated!")
    
    if dry_run:
        print("⚠️  This was a DRY-RUN. No files were modified.")
        print("   Run with --execute to actually modify files.\n")
    else:
        print("✅ Files modified successfully!")
        print("   Next steps:")
        print("   1. Review changes: git diff")
        print("   2. Update registry: already done!")
        print("   3. Re-scan: cd .. && python core/doc_id_scanner.py")
        print("   4. Validate: cd ../validation && python validate_doc_id_coverage.py\n")

if __name__ == '__main__':
    main()

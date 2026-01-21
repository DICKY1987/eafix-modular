#!/usr/bin/env python3
# doc_id: DOC-DOC-0032
"""
Batch Doc ID Assignment for EAFIX Source Code
Assigns doc_ids to Python files in services/ directory
"""
import re
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "doc_id_subsystem" / "registry" / "DOC_ID_REGISTRY.yaml"

def read_registry():
    """Read current registry to get next IDs"""
    if not REGISTRY_PATH.exists():
        return {"service": 128, "api": 1, "shared": 1, "test": 32, "model": 1}
    
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse next_id values
    next_ids = {}
    for line in content.split('\n'):
        if 'next_id:' in line:
            # Get category from previous lines
            pass
    
    return {"service": 128, "api": 1, "shared": 1, "test": 32, "model": 1}

def categorize_file(path: Path) -> str:
    """Determine doc_id category for a file"""
    path_str = str(path).lower()
    
    if 'test' in path_str:
        return 'test'
    elif 'services/common' in path_str or 'shared/' in path_str:
        return 'shared'
    elif '/src/main.py' in path_str or '/src/plugin.py' in path_str:
        return 'service'
    elif 'models' in path_str or 'schemas' in path_str:
        return 'model'
    elif '/src/' in path_str:
        return 'api'
    else:
        return 'service'

def has_doc_id(file_path: Path) -> bool:
    """Check if file already has a doc_id"""
    try:
        content = file_path.read_text(encoding='utf-8')
        return bool(re.search(r'doc_id:\s*DOC-[A-Z]+-\d+', content))
    except:
        return False

def add_doc_id(file_path: Path, doc_id: str, dry_run: bool = False):
    """Add doc_id to a Python file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Determine insertion point
        if content.startswith('#!'):
            # After shebang
            lines = content.split('\n')
            lines.insert(1, f'# doc_id: {doc_id}')
            new_content = '\n'.join(lines)
        elif content.startswith('"""') or content.startswith("'''"):
            # After docstring
            if '"""' in content[3:]:
                idx = content.index('"""', 3) + 3
            elif "'''" in content[3:]:
                idx = content.index("'''", 3) + 3
            else:
                idx = 0
            new_content = content[:idx] + f'\n# doc_id: {doc_id}\n' + content[idx:]
        else:
            # At the top
            new_content = f'# doc_id: {doc_id}\n' + content
        
        if not dry_run:
            file_path.write_text(new_content, encoding='utf-8')
        
        return True
    except Exception as e:
        print(f"Error adding doc_id to {file_path}: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Batch assign doc_ids to source files')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--category', choices=['service', 'api', 'shared', 'test', 'all'], 
                       default='all', help='Filter by category')
    args = parser.parse_args()
    
    # Get next IDs
    next_ids = read_registry()
    
    # Find Python files in services/
    service_files = list(REPO_ROOT.glob('services/**/*.py'))
    shared_files = list(REPO_ROOT.glob('shared/**/*.py'))
    
    all_files = service_files + shared_files
    print(f"Found {len(all_files)} Python files")
    
    # Filter files without doc_id
    files_to_process = []
    for f in all_files:
        if '__pycache__' in str(f):
            continue
        if not has_doc_id(f):
            category = categorize_file(f)
            if args.category == 'all' or args.category == category:
                files_to_process.append((f, category))
    
    print(f"{len(files_to_process)} files need doc_ids")
    
    if args.limit:
        files_to_process = files_to_process[:args.limit]
        print(f"Processing first {args.limit} files")
    
    # Assign doc_ids
    success_count = 0
    for file_path, category in files_to_process:
        doc_id = f"DOC-{category.upper()}-{next_ids[category]:04d}"
        next_ids[category] += 1
        
        rel_path = file_path.relative_to(REPO_ROOT)
        print(f"{'[DRY-RUN] ' if args.dry_run else ''}Assigning {doc_id} to {rel_path}")
        
        if add_doc_id(file_path, doc_id, args.dry_run):
            success_count += 1
    
    print(f"\n{'Would assign' if args.dry_run else 'Assigned'} doc_ids to {success_count}/{len(files_to_process)} files")
    
    if not args.dry_run:
        print(f"\nNext IDs: {next_ids}")
        print("Remember to update registry: doc_id_subsystem/registry/DOC_ID_REGISTRY.yaml")

if __name__ == '__main__':
    main()

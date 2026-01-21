#!/usr/bin/env python3
# doc_id: DOC-DOC-0033
"""
Complete Doc ID Assignment - Close all gaps
Handles Python, JSON, YAML, Markdown, Shell, and other file types
"""
import re
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "doc_id_subsystem" / "registry" / "DOC_ID_REGISTRY.yaml"

# Starting IDs (from previous assignments)
NEXT_IDS = {
    "service": 204,
    "api": 1,
    "shared": 1,
    "test": 40,
    "model": 4,
    "config": 106,
    "script": 1,
    "contract": 40,
    "infra": 6,
    "doc": 20,
    "legacy": 65
}

def categorize_file(path: Path) -> str:
    """Determine doc_id category for a file"""
    path_str = str(path).lower()
    
    if 'test' in path_str or path_str.endswith('test.py'):
        return 'test'
    elif '.github/workflows' in path_str or 'ci/' in path_str or 'scripts/' in path_str:
        return 'script'
    elif 'contracts/' in path_str or 'schemas/' in path_str:
        return 'contract'
    elif 'deploy/' in path_str or 'docker' in path_str or 'kubernetes' in path_str:
        return 'infra'
    elif 'docs/' in path_str or path_str.endswith('.md') or path_str.endswith('readme'):
        return 'doc'
    elif 'config/' in path_str or path_str.endswith(('.yaml', '.yml', '.toml', '.json')):
        return 'config'
    elif 'p_' in path_str or 'legacy' in path_str or 'friday' in path_str:
        return 'legacy'
    elif 'services/common' in path_str or 'shared/' in path_str:
        return 'shared'
    elif 'models' in path_str:
        return 'model'
    elif 'services/' in path_str:
        return 'service'
    else:
        return 'doc'

def has_doc_id(file_path: Path) -> bool:
    """Check if file already has a doc_id"""
    try:
        content = file_path.read_text(encoding='utf-8')
        return bool(re.search(r'doc_id:\s*DOC-[A-Z]+-\d+', content))
    except:
        return False

def add_doc_id_py(content: str, doc_id: str) -> str:
    """Add doc_id to Python file"""
    if content.startswith('#!'):
        lines = content.split('\n', 1)
        return lines[0] + f'\n# doc_id: {doc_id}\n' + (lines[1] if len(lines) > 1 else '')
    else:
        return f'# doc_id: {doc_id}\n' + content

def add_doc_id_yaml(content: str, doc_id: str) -> str:
    """Add doc_id to YAML file"""
    if content.startswith('---'):
        lines = content.split('\n', 1)
        return f'---\ndoc_id: {doc_id}\n' + (lines[1] if len(lines) > 1 else '')
    else:
        return f'---\ndoc_id: {doc_id}\n---\n' + content

def add_doc_id_json(content: str, doc_id: str) -> str:
    """Add doc_id to JSON file"""
    # Insert at top as comment
    return f'{{\n  "_doc_id": "{doc_id}",\n' + content[1:]

def add_doc_id_md(content: str, doc_id: str) -> str:
    """Add doc_id to Markdown file"""
    return f'---\ndoc_id: {doc_id}\n---\n\n' + content

def add_doc_id_sh(content: str, doc_id: str) -> str:
    """Add doc_id to shell script"""
    if content.startswith('#!'):
        lines = content.split('\n', 1)
        return lines[0] + f'\n# doc_id: {doc_id}\n' + (lines[1] if len(lines) > 1 else '')
    else:
        return f'# doc_id: {doc_id}\n' + content

def add_doc_id_generic(content: str, doc_id: str, ext: str) -> str:
    """Add doc_id to other file types"""
    if ext in ['.mq4', '.txt', '.bat', '.ps1']:
        return f'// doc_id: {doc_id}\n' + content
    else:
        return f'# doc_id: {doc_id}\n' + content

def add_doc_id_to_file(file_path: Path, doc_id: str, dry_run: bool = False) -> bool:
    """Add doc_id to a file based on its type"""
    try:
        content = file_path.read_text(encoding='utf-8')
        ext = file_path.suffix.lower()
        
        if ext == '.py':
            new_content = add_doc_id_py(content, doc_id)
        elif ext in ['.yaml', '.yml']:
            new_content = add_doc_id_yaml(content, doc_id)
        elif ext == '.json':
            new_content = add_doc_id_json(content, doc_id)
        elif ext == '.md':
            new_content = add_doc_id_md(content, doc_id)
        elif ext == '.sh':
            new_content = add_doc_id_sh(content, doc_id)
        else:
            new_content = add_doc_id_generic(content, doc_id, ext)
        
        if not dry_run:
            file_path.write_text(new_content, encoding='utf-8')
        
        return True
    except Exception as e:
        print(f"Error adding doc_id to {file_path}: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Complete doc_id gap closure')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    args = args = parser.parse_args()
    
    next_ids = NEXT_IDS.copy()
    
    # Find all trackable files
    extensions = ["*.py", "*.md", "*.yaml", "*.yml", "*.json", "*.txt", "*.sh", "*.bat", "*.ps1", "*.mq4", "*.toml"]
    exclude_patterns = ["__pycache__", ".git", "node_modules", ".pytest_cache", ".coverage", "reports"]
    
    all_files = []
    for ext in extensions:
        all_files.extend(REPO_ROOT.rglob(ext))
    
    # Filter out excluded directories
    filtered_files = []
    for f in all_files:
        excluded = False
        for pattern in exclude_patterns:
            if pattern in str(f):
                excluded = True
                break
        if not excluded:
            filtered_files.append(f)
    
    print(f"Found {len(filtered_files)} total files")
    
    # Find files without doc_id
    files_to_process = []
    for f in filtered_files:
        if not has_doc_id(f):
            category = categorize_file(f)
            files_to_process.append((f, category))
    
    print(f"{len(files_to_process)} files need doc_ids")
    
    if args.limit:
        files_to_process = files_to_process[:args.limit]
        print(f"Processing first {args.limit} files")
    
    # Assign doc_ids
    success_count = 0
    by_category = {}
    
    for file_path, category in files_to_process:
        doc_id = f"DOC-{category.upper()}-{next_ids[category]:04d}"
        next_ids[category] += 1
        
        rel_path = file_path.relative_to(REPO_ROOT)
        print(f"{'[DRY-RUN] ' if args.dry_run else ''}Assigning {doc_id} to {rel_path}")
        
        if add_doc_id_to_file(file_path, doc_id, args.dry_run):
            success_count += 1
            by_category[category] = by_category.get(category, 0) + 1
    
    print(f"\n{'Would assign' if args.dry_run else 'Assigned'} doc_ids to {success_count}/{len(files_to_process)} files")
    print(f"\nBy category:")
    for cat, count in sorted(by_category.items()):
        print(f"  {cat.upper()}: {count} files")
    
    if not args.dry_run:
        print(f"\nNext IDs: {next_ids}")
        print("Remember to update registry: doc_id_subsystem/registry/DOC_ID_REGISTRY.yaml")

if __name__ == '__main__':
    main()

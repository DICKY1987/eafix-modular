#!/usr/bin/env python3
# doc_id: 2026012201111007
# Phase B.2: Create FILE_REGISTRY with module_id and role assignments
# Created: 2026-01-22T01:11:41Z

import json
import os
import sys
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

def load_module_registry(registry_path: Path) -> Dict:
    """Load MODULE_REGISTRY."""
    with open(registry_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_id_registry(registry_path: Path) -> Dict:
    """Load existing ID_REGISTRY."""
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def infer_role_from_path(file_path: str, filename: str) -> str:
    """Infer file role from path and filename."""
    file_path_lower = file_path.lower()
    filename_lower = filename.lower()
    
    # Explicit path-based roles
    if 'test' in file_path_lower:
        return 'test'
    if file_path_lower.startswith('docs/') or file_path_lower.startswith('documentation/'):
        return 'doc'
    if file_path_lower.startswith('schemas/') or file_path_lower.startswith('contracts/schemas/'):
        return 'schema'
    if file_path_lower.startswith('config/'):
        return 'config'
    if file_path_lower.startswith('data/'):
        return 'data'
    if file_path_lower.startswith('scripts/'):
        return 'tooling'
    
    # Filename-based inference
    if 'test_' in filename_lower or '_test' in filename_lower:
        return 'test'
    if filename_lower.endswith('.schema.json'):
        return 'schema'
    if 'config' in filename_lower and filename_lower.endswith(('.yaml', '.json', '.toml')):
        return 'config'
    if filename_lower in ['readme.md', 'changelog.md', 'license', 'license.txt']:
        return 'doc'
    
    # Extension-based
    if filename_lower.endswith(('.md', '.txt', '.rst', '.adoc')):
        return 'doc'
    
    # Python entrypoint heuristics
    if filename_lower.endswith('.py'):
        if any(word in filename_lower for word in ['main', 'app', 'service', 'adapter', 'engine', 'builder']):
            return 'entrypoint'
        return 'library'
    
    # Default
    if filename_lower.endswith(('.py', '.js', '.ts')):
        return 'library'
    
    return 'doc'

def match_module_pattern(file_path: str, pattern: str) -> bool:
    """Check if file path matches a module's file pattern."""
    # Convert glob pattern to regex
    # Simple implementation: ** -> .*, * -> [^/]*
    regex_pattern = pattern.replace('**/', '.*').replace('*', '[^/]*')
    regex_pattern = '^' + regex_pattern + '$'
    
    try:
        return bool(re.match(regex_pattern, file_path))
    except:
        return False

def assign_module_id(file_path: str, module_registry: Dict) -> str:
    """Assign module_id based on file path and module patterns."""
    # Check each module's required_files patterns
    for module in module_registry.get('modules', []):
        module_id = module.get('module_id')
        required_files = module.get('required_files', [])
        
        for file_spec in required_files:
            pattern = file_spec.get('pattern', '')
            if match_module_pattern(file_path, pattern):
                return module_id
    
    # Path-based inference (fallback)
    if '/' in file_path:
        parts = file_path.split('/')
        if len(parts) >= 2:
            # Check if second part looks like a module ID
            potential_module = parts[1]
            if any(potential_module == m['module_id'] for m in module_registry.get('modules', [])):
                return potential_module
    
    # Check if file path contains any module ID
    for module in module_registry.get('modules', []):
        module_id = module.get('module_id')
        if module_id in file_path:
            return module_id
    
    return 'UNCATEGORIZED'

def create_file_registry(id_registry: Dict, module_registry: Dict) -> Dict:
    """Transform ID_REGISTRY into FILE_REGISTRY with module_id and roles."""
    file_registry = {
        'schema_version': '2.1',
        'scope': id_registry.get('scope', '260118'),
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'doc_id': '2026012201111008',
        'files': []
    }
    
    allocations = id_registry.get('allocations', [])
    print(f"Processing {len(allocations)} file records...")
    
    for allocation in allocations:
        doc_id = allocation.get('id', '')
        file_path = allocation.get('file_path', '')
        
        # Normalize path to forward slashes
        file_path_normalized = file_path.replace('\\', '/')
        
        filename = os.path.basename(file_path)
        extension = os.path.splitext(filename)[1].lstrip('.')
        
        # Assign module_id
        module_id = assign_module_id(file_path_normalized, module_registry)
        
        # Infer role
        role = infer_role_from_path(file_path_normalized, filename)
        
        file_record = {
            'doc_id': doc_id,
            'relative_path': file_path_normalized,
            'filename': filename,
            'extension': extension,
            'module_id': module_id,
            'role': role,
            'step_refs': [],  # Will be populated in Phase B.4
            'contracts_produced': [],  # Future enhancement
            'contracts_consumed': [],  # Future enhancement
            'type_code': allocation.get('metadata', {}).get('type_code', '00'),
            'ns_code': allocation.get('metadata', {}).get('ns_code', '999'),
            'status': allocation.get('status', 'active'),
            'allocated_at': allocation.get('allocated_at'),
            'metadata': allocation.get('metadata', {})
        }
        
        file_registry['files'].append(file_record)
    
    return file_registry

def main():
    repo_root = Path(__file__).parent.parent.parent
    
    id_registry_path = repo_root / "Directory management system" / "id_16_digit" / "registry" / "ID_REGISTRY.json"
    module_registry_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "2026012201111006_MODULE_REGISTRY_v1.0.0.yaml"
    output_path = repo_root / "Directory management system" / "id_16_digit" / "registry" / "2026012201111008_FILE_REGISTRY.json"
    
    if not id_registry_path.exists():
        print(f"❌ ID_REGISTRY not found: {id_registry_path}")
        return 1
    
    if not module_registry_path.exists():
        print(f"❌ MODULE_REGISTRY not found: {module_registry_path}")
        return 1
    
    print("🔨 Creating FILE_REGISTRY with module_id and role assignments...")
    
    try:
        # Load inputs
        print("📖 Loading ID_REGISTRY...")
        id_registry = load_id_registry(id_registry_path)
        
        print("📖 Loading MODULE_REGISTRY...")
        module_registry = load_module_registry(module_registry_path)
        
        # Create FILE_REGISTRY
        file_registry = create_file_registry(id_registry, module_registry)
        
        # Statistics
        total_files = len(file_registry['files'])
        uncategorized = sum(1 for f in file_registry['files'] if f['module_id'] == 'UNCATEGORIZED')
        categorized = total_files - uncategorized
        
        role_counts = {}
        for f in file_registry['files']:
            role = f['role']
            role_counts[role] = role_counts.get(role, 0) + 1
        
        print(f"\n✅ FILE_REGISTRY created:")
        print(f"  Total files: {total_files}")
        print(f"  Categorized: {categorized} ({100*categorized/total_files:.1f}%)")
        print(f"  Uncategorized: {uncategorized} ({100*uncategorized/total_files:.1f}%)")
        print(f"\n  Role distribution:")
        for role, count in sorted(role_counts.items()):
            print(f"    {role}: {count}")
        
        # Write output
        print(f"\n💾 Writing FILE_REGISTRY...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(file_registry, f, indent=2)
        
        print(f"💾 FILE_REGISTRY written to: {output_path}")
        
        # Also write summary
        summary_path = repo_root / "backups" / "file_registry_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_files': total_files,
                'categorized': categorized,
                'uncategorized': uncategorized,
                'role_counts': role_counts,
                'generated_at': file_registry['generated_at']
            }, f, indent=2)
        
        print(f"💾 Summary written to: {summary_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Creation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

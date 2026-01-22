#!/usr/bin/env python3
# doc_id: 2026012201113003
# Phase B.4.3: Populate step_refs in FILE_REGISTRY
# Created: 2026-01-22T01:36:17Z

import json
import sys
import yaml
from pathlib import Path
from typing import Dict

def load_file_registry(path: Path) -> Dict:
    """Load FILE_REGISTRY."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_process_doc(path: Path) -> Dict:
    """Load process document."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def populate_step_refs(file_registry: Dict, process_doc: Dict) -> Dict:
    """Populate step_refs in FILE_REGISTRY from process document."""
    
    # Clear existing step_refs
    for file in file_registry['files']:
        file['step_refs'] = []
    
    # Build path lookup for files
    file_lookup = {f['relative_path']: f for f in file_registry['files']}
    
    # Populate from process document
    steps = process_doc.get('steps', [])
    updates_count = 0
    
    for step in steps:
        step_num = step.get('number')
        entrypoint_files = step.get('entrypoint_files', [])
        
        for entrypoint_path in entrypoint_files:
            if not entrypoint_path:
                continue
            
            file_record = file_lookup.get(entrypoint_path)
            if file_record:
                if step_num not in file_record['step_refs']:
                    file_record['step_refs'].append(step_num)
                    updates_count += 1
            else:
                print(f"⚠️  Warning: Step {step_num} references unknown file: {entrypoint_path}")
    
    # Sort step_refs for determinism
    for file in file_registry['files']:
        if file['step_refs']:
            file['step_refs'].sort()
    
    print(f"✅ Updated {updates_count} file records with step_refs")
    
    return file_registry

def main():
    repo_root = Path(__file__).parent.parent.parent
    
    file_registry_path = repo_root / "Directory management system" / "id_16_digit" / "registry" / "2026012201111008_FILE_REGISTRY.json"
    process_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "2026012201113002_updated_trading_process_v2.yaml"
    output_path = repo_root / "Directory management system" / "id_16_digit" / "registry" / "2026012201113004_FILE_REGISTRY_v2.json"
    
    if not file_registry_path.exists():
        print(f"❌ FILE_REGISTRY not found: {file_registry_path}")
        return 1
    
    if not process_path.exists():
        print(f"❌ Updated process document not found: {process_path}")
        return 1
    
    print("🔨 Populating step_refs in FILE_REGISTRY...")
    
    try:
        # Load data
        file_registry = load_file_registry(file_registry_path)
        process_doc = load_process_doc(process_path)
        
        # Populate step_refs
        updated_registry = populate_step_refs(file_registry, process_doc)
        
        # Statistics
        files_with_refs = sum(1 for f in updated_registry['files'] if f['step_refs'])
        total_refs = sum(len(f['step_refs']) for f in updated_registry['files'])
        
        print(f"\n📊 Statistics:")
        print(f"  Files with step_refs: {files_with_refs}")
        print(f"  Total step references: {total_refs}")
        
        # Write updated registry
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_registry, f, indent=2)
        
        print(f"\n✅ Updated FILE_REGISTRY written to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Population failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

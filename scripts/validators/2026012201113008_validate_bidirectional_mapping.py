#!/usr/bin/env python3
# doc_id: 2026012201113008
# Phase B.5: Bidirectional Mapping Validator
# Created: 2026-01-22T01:36:17Z

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List

def load_file_registry(path: Path) -> Dict:
    """Load FILE_REGISTRY."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_process_doc(path: Path) -> Dict:
    """Load process document."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_bidirectional_mapping(file_registry: Dict, process_doc: Dict) -> Dict:
    """Validate bidirectional consistency between FILE_REGISTRY and process document."""
    errors = []
    warnings = []
    
    # Build lookups
    file_lookup = {f['relative_path']: f for f in file_registry['files']}
    steps_by_number = {s['number']: s for s in process_doc.get('steps', [])}
    
    # Forward check: Process → Files
    for step in process_doc.get('steps', []):
        step_num = step.get('number')
        entrypoint_files = step.get('entrypoint_files', [])
        
        for entrypoint_path in entrypoint_files:
            if not entrypoint_path:
                continue
            
            file_record = file_lookup.get(entrypoint_path)
            
            if not file_record:
                errors.append(f"Step {step_num} references non-existent file: {entrypoint_path}")
            elif step_num not in file_record.get('step_refs', []):
                errors.append(f"Step {step_num} → {entrypoint_path} missing reverse link in step_refs")
            elif file_record.get('role') != 'entrypoint':
                errors.append(f"Step {step_num} references non-entrypoint file: {entrypoint_path} (role={file_record.get('role')})")
    
    # Reverse check: Files → Process
    for file in file_registry['files']:
        step_refs = file.get('step_refs', [])
        
        if not step_refs:
            continue
        
        # Only entrypoints should have step_refs
        if file.get('role') != 'entrypoint':
            errors.append(f"Non-entrypoint file {file['relative_path']} (role={file['role']}) has step_refs: {step_refs}")
            continue
        
        for step_num in step_refs:
            step = steps_by_number.get(step_num)
            
            if not step:
                errors.append(f"File {file['relative_path']} references non-existent step {step_num}")
            elif file['relative_path'] not in step.get('entrypoint_files', []):
                errors.append(f"File {file['relative_path']} → Step {step_num} missing forward link in entrypoint_files")
    
    # Statistics
    files_with_refs = sum(1 for f in file_registry['files'] if f.get('step_refs'))
    steps_with_entrypoints = sum(1 for s in process_doc.get('steps', []) if s.get('entrypoint_files'))
    
    return {
        'check': 'bidirectional_mapping_consistency',
        'passed': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'stats': {
            'files_with_step_refs': files_with_refs,
            'steps_with_entrypoints': steps_with_entrypoints,
            'total_files': len(file_registry['files']),
            'total_steps': len(process_doc.get('steps', []))
        }
    }

def main():
    repo_root = Path(__file__).parent.parent.parent
    
    file_registry_path = repo_root / "Directory management system" / "id_16_digit" / "registry" / "2026012201113004_FILE_REGISTRY_v2.json"
    process_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "2026012201113002_updated_trading_process_v2.yaml"
    
    if not file_registry_path.exists():
        print(f"❌ FILE_REGISTRY_v2 not found: {file_registry_path}")
        return 1
    
    if not process_path.exists():
        print(f"❌ Updated process document not found: {process_path}")
        return 1
    
    print("🔍 Validating bidirectional mapping consistency...")
    
    try:
        file_registry = load_file_registry(file_registry_path)
        process_doc = load_process_doc(process_path)
        
        result = validate_bidirectional_mapping(file_registry, process_doc)
        
        print(f"\n{'✅ PASSED' if result['passed'] else '❌ FAILED'}: {result['check']}")
        
        if result.get('errors'):
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  • {error}")
        
        if result.get('warnings'):
            print(f"\nWarnings ({len(result['warnings'])}):")
            for warning in result['warnings']:
                print(f"  • {warning}")
        
        print(f"\n📊 Statistics:")
        for key, value in result.get('stats', {}).items():
            print(f"  {key}: {value}")
        
        # Write report
        report_path = repo_root / "backups" / "bidirectional_validation_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Report written to: {report_path}")
        
        return 0 if result['passed'] else 1
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# doc_id: 2026012201113005
# Phase B.4.4: Generate Traceability Matrix
# Created: 2026-01-22T01:36:17Z

import json
import sys
import yaml
import csv
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

def load_module_registry(path: Path) -> Dict:
    """Load MODULE_REGISTRY."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_traceability_matrix(process_doc: Dict, file_registry: Dict, module_registry: Dict) -> List[Dict]:
    """Generate comprehensive traceability matrix."""
    
    matrix = []
    
    # Build lookups
    file_lookup = {f['relative_path']: f for f in file_registry['files']}
    module_lookup = {m['module_id']: m for m in module_registry['modules']}
    
    steps = process_doc.get('steps', [])
    
    for step in steps:
        step_num = step.get('number')
        step_name = step.get('name', '')
        module_id = step.get('module_id', '')
        input_contracts = step.get('input', '')
        output_contracts = step.get('output', '')
        entrypoint_files = step.get('entrypoint_files', [])
        
        # Get module info
        module = module_lookup.get(module_id, {})
        module_type = module.get('module_type', 'unknown')
        
        # Get entrypoint file info
        entrypoint_info = []
        for ep_path in entrypoint_files:
            file_rec = file_lookup.get(ep_path)
            if file_rec:
                entrypoint_info.append({
                    'file': ep_path,
                    'doc_id': file_rec.get('doc_id', ''),
                    'role': file_rec.get('role', ''),
                    'filename': file_rec.get('filename', '')
                })
        
        matrix_row = {
            'step_number': step_num,
            'step_name': step_name,
            'module_id': module_id,
            'module_type': module_type,
            'input_contracts': input_contracts,
            'output_contracts': output_contracts,
            'entrypoint_count': len(entrypoint_files),
            'entrypoints': entrypoint_info,
            'has_implementation': len(entrypoint_files) > 0
        }
        
        matrix.append(matrix_row)
    
    return matrix

def write_csv_matrix(matrix: List[Dict], output_path: Path):
    """Write matrix as CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Step', 'Step Name', 'Module', 'Module Type',
            'Inputs', 'Outputs', 'Entrypoint File', 'Has Implementation'
        ])
        
        # Data
        for row in matrix:
            entrypoint_str = row['entrypoints'][0]['file'] if row['entrypoints'] else ''
            writer.writerow([
                row['step_number'],
                row['step_name'],
                row['module_id'],
                row['module_type'],
                row['input_contracts'],
                row['output_contracts'],
                entrypoint_str,
                'Yes' if row['has_implementation'] else 'No'
            ])

def write_markdown_matrix(matrix: List[Dict], output_path: Path):
    """Write matrix as Markdown."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Traceability Matrix: Process Steps ↔ Implementation Files\n\n")
        f.write(f"**Generated:** 2026-01-22T01:36:17Z  \n")
        f.write(f"**Total Steps:** {len(matrix)}  \n")
        
        implemented = sum(1 for r in matrix if r['has_implementation'])
        f.write(f"**Implemented:** {implemented}/{len(matrix)} ({100*implemented/len(matrix):.1f}%)  \n\n")
        
        f.write("---\n\n")
        
        for row in matrix:
            f.write(f"## Step {row['step_number']}: {row['step_name']}\n\n")
            f.write(f"- **Module:** `{row['module_id']}` ({row['module_type']})\n")
            f.write(f"- **Inputs:** {row['input_contracts'] or 'None'}\n")
            f.write(f"- **Outputs:** {row['output_contracts'] or 'None'}\n")
            
            if row['entrypoints']:
                f.write(f"- **Implementation:**\n")
                for ep in row['entrypoints']:
                    f.write(f"  - `{ep['file']}`\n")
                    f.write(f"    - doc_id: `{ep['doc_id']}`\n")
            else:
                f.write(f"- **Implementation:** ⚠️ Not mapped\n")
            
            f.write("\n")

def main():
    repo_root = Path(__file__).parent.parent.parent
    
    file_registry_path = repo_root / "Directory management system" / "id_16_digit" / "registry" / "2026012201113004_FILE_REGISTRY_v2.json"
    process_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "2026012201113002_updated_trading_process_v2.yaml"
    module_registry_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "2026012201111006_MODULE_REGISTRY_v1.0.0.yaml"
    
    csv_output = repo_root / "docs" / "mapping_system" / "2026012201113006_traceability_matrix.csv"
    md_output = repo_root / "docs" / "mapping_system" / "2026012201113007_traceability_matrix.md"
    json_output = repo_root / "backups" / "traceability_matrix.json"
    
    if not all([file_registry_path.exists(), process_path.exists(), module_registry_path.exists()]):
        print("❌ Required files not found")
        return 1
    
    print("🔨 Generating traceability matrix...")
    
    try:
        # Load data
        file_registry = load_file_registry(file_registry_path)
        process_doc = load_process_doc(process_path)
        module_registry = load_module_registry(module_registry_path)
        
        # Generate matrix
        matrix = generate_traceability_matrix(process_doc, file_registry, module_registry)
        
        # Statistics
        total_steps = len(matrix)
        implemented = sum(1 for r in matrix if r['has_implementation'])
        
        print(f"\n✅ Generated traceability matrix:")
        print(f"  Total steps: {total_steps}")
        print(f"  Implemented: {implemented} ({100*implemented/total_steps:.1f}%)")
        print(f"  Not mapped: {total_steps - implemented}")
        
        # Write outputs
        write_csv_matrix(matrix, csv_output)
        print(f"\n💾 CSV written to: {csv_output}")
        
        write_markdown_matrix(matrix, md_output)
        print(f"💾 Markdown written to: {md_output}")
        
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(matrix, f, indent=2)
        print(f"💾 JSON written to: {json_output}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

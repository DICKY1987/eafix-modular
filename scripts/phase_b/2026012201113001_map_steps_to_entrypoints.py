#!/usr/bin/env python3
# doc_id: 2026012201113001
# Phase B.4.2: Intelligent Step-to-Entrypoint Mapper
# Created: 2026-01-22T01:36:17Z

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional

def load_file_registry(path: Path) -> Dict:
    """Load FILE_REGISTRY."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_process_doc(path: Path) -> Dict:
    """Load process document."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_entrypoint_files(file_registry: Dict) -> List[Dict]:
    """Get all files with role=entrypoint."""
    return [f for f in file_registry['files'] if f['role'] == 'entrypoint']

def calculate_match_score(step: Dict, entrypoint: Dict) -> int:
    """Calculate match score between step and entrypoint file."""
    score = 0
    
    step_name = step.get('name', '').lower()
    step_module = step.get('module_id', '').lower()
    responsible = step.get('responsible', '').lower()
    
    filename = entrypoint['filename'].lower()
    filepath = entrypoint['relative_path'].lower()
    
    # Keyword matching from step name
    keywords = {
        'calendar': ['calendar', 'ingestor'],
        'market': ['market', 'feed', 'data'],
        'bar': ['bar'],
        'indicator': ['indicator'],
        'signal': ['signal'],
        'intent': ['intent'],
        'risk': ['risk'],
        'order': ['order', 'router'],
        'transport': ['transport', 'router'],
        'adapter': ['adapter'],
        'reentry': ['reentry', 're-entry'],
        'matrix': ['matrix'],
        'oms': ['oms'],
        'health': ['health', 'telemetry'],
        'event': ['event', 'gateway'],
        'orchestrat': ['orchestrat'],
        'flow': ['flow']
    }
    
    for keyword, variants in keywords.items():
        if keyword in step_name:
            for variant in variants:
                if variant in filename or variant in filepath:
                    score += 10
    
    # Module ID matching
    if step_module:
        # Check for module name fragments in path
        module_parts = step_module.split('_')
        for part in module_parts:
            if len(part) > 2 and part.lower() in filepath:
                score += 5
    
    # Responsible field matching
    if responsible and responsible in filename:
        score += 15
    
    # Service path matching (services/* structure)
    if 'services/' in filepath:
        service_name = filepath.split('/')[1] if '/' in filepath else ''
        if service_name:
            # Check if service name relates to step name
            for word in step_name.split():
                if len(word) > 3 and word in service_name:
                    score += 8
    
    return score

def map_steps_to_entrypoints(process_doc: Dict, file_registry: Dict) -> Dict:
    """Map each process step to candidate entrypoint files."""
    entrypoints = get_entrypoint_files(file_registry)
    steps = process_doc.get('steps', [])
    
    mappings = {}
    
    for step in steps:
        step_num = step.get('number')
        if not step_num:
            continue
        
        # Calculate scores for all entrypoints
        candidates = []
        for entrypoint in entrypoints:
            score = calculate_match_score(step, entrypoint)
            if score > 0:
                candidates.append({
                    'file': entrypoint['relative_path'],
                    'filename': entrypoint['filename'],
                    'score': score
                })
        
        # Sort by score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top 3 candidates
        top_candidates = candidates[:3] if candidates else []
        
        mappings[step_num] = {
            'step_name': step.get('name'),
            'module_id': step.get('module_id'),
            'responsible': step.get('responsible'),
            'candidates': top_candidates,
            'recommended': top_candidates[0]['file'] if top_candidates else None
        }
    
    return mappings

def generate_process_yaml_with_entrypoints(process_doc: Dict, mappings: Dict, output_path: Path):
    """Generate updated process YAML with entrypoint_files field."""
    
    steps = process_doc.get('steps', [])
    
    for step in steps:
        step_num = step.get('number')
        mapping = mappings.get(step_num)
        
        if mapping and mapping.get('recommended'):
            # Add entrypoint_files field
            step['entrypoint_files'] = [mapping['recommended']]
        else:
            # No clear match - add empty list with comment
            step['entrypoint_files'] = []
    
    # Write updated YAML
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(process_doc, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main():
    repo_root = Path(__file__).parent.parent.parent
    
    file_registry_path = repo_root / "Directory management system" / "id_16_digit" / "registry" / "2026012201111008_FILE_REGISTRY.json"
    process_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "updated_trading_process_aligned.yaml"
    output_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "2026012201113002_updated_trading_process_v2.yaml"
    mappings_output = repo_root / "backups" / "step_entrypoint_mappings.json"
    
    if not file_registry_path.exists():
        print(f"❌ FILE_REGISTRY not found: {file_registry_path}")
        return 1
    
    if not process_path.exists():
        print(f"❌ Process document not found: {process_path}")
        return 1
    
    print("🔨 Mapping process steps to entrypoint files...")
    
    try:
        # Load data
        file_registry = load_file_registry(file_registry_path)
        process_doc = load_process_doc(process_path)
        
        # Generate mappings
        mappings = map_steps_to_entrypoints(process_doc, file_registry)
        
        # Show mappings
        print(f"\n✅ Generated mappings for {len(mappings)} steps:\n")
        
        mapped_count = 0
        unmapped_count = 0
        
        for step_num in sorted(mappings.keys()):
            mapping = mappings[step_num]
            step_name = mapping['step_name']
            recommended = mapping['recommended']
            
            if recommended:
                mapped_count += 1
                print(f"Step {step_num}: {step_name}")
                print(f"  → {recommended}")
                if mapping['candidates']:
                    top_score = mapping['candidates'][0]['score']
                    print(f"  (confidence: {top_score})")
            else:
                unmapped_count += 1
                print(f"Step {step_num}: {step_name}")
                print(f"  → ⚠️  No clear entrypoint match")
        
        print(f"\n📊 Summary:")
        print(f"  Mapped: {mapped_count}")
        print(f"  Unmapped: {unmapped_count}")
        
        # Save mappings
        with open(mappings_output, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, indent=2)
        
        print(f"\n💾 Mappings saved to: {mappings_output}")
        
        # Generate updated process YAML
        print(f"\n🔨 Generating updated process YAML...")
        generate_process_yaml_with_entrypoints(process_doc, mappings, output_path)
        
        print(f"✅ Updated process YAML written to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Mapping failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

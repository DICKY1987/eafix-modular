#!/usr/bin/env python3
# doc_id: 2026012201111005
# Phase B1: Generate MODULE_REGISTRY from Process Document
# Created: 2026-01-22T01:11:41Z

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime

def parse_contracts(contract_str: str) -> List[str]:
    """Parse contract string like 'ContractA + ContractB' into list."""
    if not contract_str:
        return []
    contracts = [c.strip() for c in contract_str.split('+') if c.strip()]
    # Filter out non-contract words like "ResolvedConfig" being everywhere
    return contracts

def derive_module_contracts(process_doc: Dict) -> Dict[str, Dict]:
    """Derive contract boundaries for each module from process steps."""
    modules = {}
    
    steps = process_doc.get('steps', [])
    for step in steps:
        module_id = step.get('module_id')
        if not module_id or module_id == '(loop)':
            continue
        
        if module_id not in modules:
            modules[module_id] = {
                'module_id': module_id,
                'in_types': set(),
                'out_types': set(),
                'steps_owned': []
            }
        
        # Add step number
        modules[module_id]['steps_owned'].append(step.get('number'))
        
        # Parse inputs
        input_str = step.get('input', '')
        inputs = parse_contracts(input_str)
        modules[module_id]['in_types'].update(inputs)
        
        # Parse outputs
        output_str = step.get('output', '')
        outputs = parse_contracts(output_str)
        modules[module_id]['out_types'].update(outputs)
    
    # Convert sets to sorted lists
    for module in modules.values():
        module['in_types'] = sorted(module['in_types'])
        module['out_types'] = sorted(module['out_types'])
    
    return modules

def infer_module_type(module_id: str) -> str:
    """Infer module type from module_id prefix."""
    prefix = module_id.split('_')[0] if '_' in module_id else module_id
    
    type_map = {
        'F': 'foundation',
        'D': 'data_adapter',
        'C': 'computation',
        'S': 'strategy',
        'R': 'risk',
        'O': 'order_management',
        'B': 'broker_adapter',
        'E': 'event_processing',
        'P': 'health'
    }
    
    return type_map.get(prefix, 'other')

def generate_file_patterns(module_id: str) -> List[Dict]:
    """Generate default file patterns for module."""
    return [
        {
            'role': 'entrypoint',
            'pattern': f"src/{module_id}/**/*.py",
            'description': f"{module_id} implementation files"
        },
        {
            'role': 'test',
            'pattern': f"tests/{module_id}/**/*.py",
            'description': f"{module_id} test suite"
        },
        {
            'role': 'schema',
            'pattern': f"schemas/{module_id}/**/*.json",
            'description': f"{module_id} contract schemas"
        }
    ]

def generate_module_registry(process_doc: Dict) -> Dict:
    """Generate complete MODULE_REGISTRY structure."""
    # Derive contracts
    module_contracts = derive_module_contracts(process_doc)
    
    # Build registry
    registry = {
        'registry_version': '1.0.0',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'source': 'Derived from updated_trading_process_aligned.yaml',
        'doc_id': '2026012201111006',
        'modules': []
    }
    
    for module_id in sorted(module_contracts.keys()):
        contracts = module_contracts[module_id]
        
        module_def = {
            'module_id': module_id,
            'module_type': infer_module_type(module_id),
            'status': 'active',
            'owner': 'system',
            'purpose': f"Implements steps {', '.join(map(str, contracts['steps_owned']))}",
            'contract_boundaries': {
                'in_types': contracts['in_types'],
                'out_types': contracts['out_types']
            },
            'required_files': generate_file_patterns(module_id),
            'validation_rules': [
                {
                    'check': 'output_contracts_implemented',
                    'contracts': contracts['out_types']
                }
            ]
        }
        
        registry['modules'].append(module_def)
    
    return registry

def write_yaml_registry(registry: Dict, output_path: Path):
    """Write registry as YAML file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main():
    repo_root = Path(__file__).parent.parent.parent
    process_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "updated_trading_process_aligned.yaml"
    output_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "2026012201111006_MODULE_REGISTRY_v1.0.0.yaml"
    
    if not process_path.exists():
        print(f"❌ Process document not found: {process_path}")
        return 1
    
    print("🔨 Generating MODULE_REGISTRY from process document...")
    
    try:
        # Load process document
        with open(process_path, 'r', encoding='utf-8') as f:
            process_doc = yaml.safe_load(f)
        
        # Generate registry
        registry = generate_module_registry(process_doc)
        
        print(f"✅ Generated registry with {len(registry['modules'])} modules")
        
        # Write to file
        write_yaml_registry(registry, output_path)
        
        print(f"💾 MODULE_REGISTRY written to: {output_path}")
        
        # Also write JSON version for easier processing
        json_path = repo_root / "backups" / "module_registry.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
        
        print(f"💾 JSON copy written to: {json_path}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

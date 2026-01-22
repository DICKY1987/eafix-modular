#!/usr/bin/env python3
# doc_id: 2026012201111004
# Phase B1.1: Extract Module List from Process Document
# Created: 2026-01-22T01:11:41Z

import json
import sys
import yaml
from pathlib import Path
from typing import Set

def extract_modules(process_path: Path) -> Set[str]:
    """Extract unique module_ids from process document."""
    with open(process_path, 'r', encoding='utf-8') as f:
        process_doc = yaml.safe_load(f)
    
    modules = set()
    
    steps = process_doc.get('steps', [])
    for step in steps:
        module_id = step.get('module_id')
        if module_id:
            modules.add(module_id)
    
    return modules

def main():
    repo_root = Path(__file__).parent.parent.parent
    process_path = repo_root / "Directory management system" / "DOD_modules_contracts" / "updated_trading_process_aligned.yaml"
    
    if not process_path.exists():
        print(f"❌ Process document not found: {process_path}")
        sys.exit(1)
    
    print(f"📖 Reading process document: {process_path.name}")
    
    try:
        modules = extract_modules(process_path)
        modules_sorted = sorted(modules)
        
        print(f"✅ Extracted {len(modules_sorted)} unique modules:")
        for module in modules_sorted:
            print(f"  • {module}")
        
        # Write to JSON
        output_path = repo_root / "backups" / "modules_extracted.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'module_count': len(modules_sorted),
                'modules': modules_sorted,
                'source': str(process_path.name),
                'extracted_at': '2026-01-22T01:11:41Z'
            }, f, indent=2)
        
        print(f"\n💾 Output written to: {output_path}")
        return 0
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

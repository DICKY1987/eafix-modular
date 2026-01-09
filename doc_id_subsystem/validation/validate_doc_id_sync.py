#!/usr/bin/env python3
"""
DOC_ID: DOC-CORE-2-VALIDATION-FIXING-VALIDATE-DOC-ID-SYNC-1163
Registry-Inventory Sync Validator
Validates doc_ids between DOC_ID_REGISTRY.yaml and docs_inventory.jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import yaml

def main(output: str = None):
    """Validate sync between registry and inventory"""
    base = Path(__file__).parent.parent
    registry_path = base / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"
    inventory_path = base / "5_REGISTRY_DATA" / "docs_inventory.jsonl"
    
    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)
    
    registry_ids = {d.get('doc_id') for d in registry.get('documents', []) if d.get('doc_id')}
    
    # Load inventory
    inventory_ids = set()
    if inventory_path.exists():
        with open(inventory_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    if item.get('doc_id'):
                        inventory_ids.add(item['doc_id'])
    
    # Compare
    drift = registry_ids - inventory_ids  # In registry but not inventory
    missing = inventory_ids - registry_ids  # In inventory but not registry
    
    passed = len(drift) == 0 and len(missing) == 0
    
    results = {
        "task_id": "AUTO-007",
        "timestamp": datetime.now().isoformat(),
        "status": "PASSED" if passed else "FAILED",
        "registry_count": len(registry_ids),
        "inventory_count": len(inventory_ids),
        "drift_count": len(drift),
        "missing_count": len(missing)
    }
    
    # Output results
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
    
    # Console output
    print(f"\n=== DOC_ID Sync Validation ===")
    print(f"Registry: {len(registry_ids)} IDs")
    print(f"Inventory: {len(inventory_ids)} IDs")
    print(f"Drift: {len(drift)} IDs")
    print(f"Missing: {len(missing)} IDs")
    
    if passed:
        print("\n✅ PASSED: Registry and inventory are in sync")
        return 0
    else:
        print("\n❌ FAILED: Sync issues detected")
        if drift:
            print(f"   {len(drift)} IDs in registry but not inventory")
        if missing:
            print(f"   {len(missing)} IDs in inventory but not registry")
        return 1
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Registry-File Sync Validator")
    parser.add_argument("--output", help="Output JSON file path (optional)")
    args = parser.parse_args()
    sys.exit(main(args.output))
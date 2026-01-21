#!/usr/bin/env python3
"""
doc_id: 2026012120460002
Unified SSOT Registry - Process Validation Validator

Validates process mappings against PROCESS_REGISTRY.yaml.
Ensures process_id, process_step_id, and process_step_role combinations are valid.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ProcessValidator:
    """Validates process mappings against registry."""
    
    def __init__(self, policy_path: Optional[str] = None):
        """
        Initialize validator.
        
        Args:
            policy_path: Path to PROCESS_REGISTRY.yaml
        """
        if policy_path is None:
            base_dir = Path(__file__).parent.parent
            policy_path = base_dir / "contracts" / "2026012120420005_PROCESS_REGISTRY.yaml"
        
        self.policy_path = Path(policy_path)
        self.registry = self._load_registry()
        self.processes = self.registry.get("processes", [])
        self._build_lookup_tables()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load and parse process registry."""
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Process registry not found: {self.policy_path}")
        
        with open(self.policy_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _build_lookup_tables(self):
        """Build lookup tables for fast validation."""
        self.valid_process_ids: Set[str] = set()
        self.process_steps: Dict[str, Dict[str, Set[str]]] = {}
        self.all_valid_roles: Set[str] = set()
        
        for process in self.processes:
            process_id = process.get("process_id")
            if not process_id:
                continue
            
            self.valid_process_ids.add(process_id)
            self.process_steps[process_id] = {}
            
            for step in process.get("steps", []):
                step_id = step.get("process_step_id")
                allowed_roles = step.get("allowed_roles", [])
                
                if step_id:
                    self.process_steps[process_id][step_id] = set(allowed_roles)
                    self.all_valid_roles.update(allowed_roles)
    
    def validate_record(
        self, 
        record: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate process mapping for a record.
        
        Args:
            record: Entity record with process fields
        
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        
        process_id = record.get("process_id")
        process_step_id = record.get("process_step_id")
        process_step_role = record.get("process_step_role")
        
        # If no process fields, skip validation
        if not any([process_id, process_step_id, process_step_role]):
            return True, []
        
        # Rule 1: If process_step_id is present, process_id must be present
        if process_step_id and not process_id:
            errors.append(
                f"process_step_id '{process_step_id}' present but process_id is missing"
            )
            return False, errors
        
        # Rule 2: If process_step_role is present, both process_id and process_step_id must be present
        if process_step_role:
            if not process_id:
                errors.append(
                    f"process_step_role '{process_step_role}' present but process_id is missing"
                )
            if not process_step_id:
                errors.append(
                    f"process_step_role '{process_step_role}' present but process_step_id is missing"
                )
            
            if not process_id or not process_step_id:
                return False, errors
        
        # Rule 3: Validate process_id exists in registry
        if process_id and process_id not in self.valid_process_ids:
            errors.append(
                f"process_id '{process_id}' not found in process registry. "
                f"Valid: {sorted(self.valid_process_ids)}"
            )
        
        # Rule 4: Validate process_step_id belongs to process_id
        if process_id and process_step_id:
            if process_id not in self.process_steps:
                errors.append(
                    f"process_id '{process_id}' has no steps defined"
                )
            elif process_step_id not in self.process_steps[process_id]:
                valid_steps = sorted(self.process_steps[process_id].keys())
                errors.append(
                    f"process_step_id '{process_step_id}' not valid for process '{process_id}'. "
                    f"Valid steps: {valid_steps}"
                )
        
        # Rule 5: Validate process_step_role is allowed for the step
        if process_id and process_step_id and process_step_role:
            if process_id in self.process_steps and process_step_id in self.process_steps[process_id]:
                allowed_roles = self.process_steps[process_id][process_step_id]
                if process_step_role not in allowed_roles:
                    errors.append(
                        f"process_step_role '{process_step_role}' not allowed for "
                        f"process '{process_id}' step '{process_step_id}'. "
                        f"Allowed roles: {sorted(allowed_roles)}"
                    )
        
        return len(errors) == 0, errors
    
    def validate_registry_file(
        self,
        registry_path: str,
        verbose: bool = False
    ) -> Tuple[bool, List[str], Dict[str, int]]:
        """
        Validate all records with process fields in registry.
        
        Args:
            registry_path: Path to ID_REGISTRY.json
            verbose: Print detailed results
        
        Returns:
            (is_valid, error_messages, stats) tuple
        """
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        records = registry.get("records", [])
        all_errors = []
        stats = {
            "total": len(records),
            "with_process_fields": 0,
            "valid": 0,
            "invalid": 0,
            "by_process": {}
        }
        
        for idx, record in enumerate(records):
            record_id = record.get("record_id", f"record_{idx}")
            
            # Check if record has process fields
            has_process = any([
                record.get("process_id"),
                record.get("process_step_id"),
                record.get("process_step_role")
            ])
            
            if not has_process:
                continue
            
            stats["with_process_fields"] += 1
            
            is_valid, errors = self.validate_record(record)
            
            # Track by process
            process_id = record.get("process_id")
            if process_id:
                stats["by_process"][process_id] = stats["by_process"].get(process_id, 0) + 1
            
            if is_valid:
                stats["valid"] += 1
                if verbose:
                    print(f"✓ {record_id}")
            else:
                stats["invalid"] += 1
                if verbose:
                    print(f"✗ {record_id}")
                for error in errors:
                    all_errors.append(f"  {record_id}: {error}")
                    if verbose:
                        print(f"    {error}")
        
        return len(all_errors) == 0, all_errors, stats


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate process mappings against registry"
    )
    parser.add_argument(
        "--registry",
        default="ID_REGISTRY.json",
        help="Path to registry file"
    )
    parser.add_argument(
        "--policy",
        help="Path to PROCESS_REGISTRY.yaml (default: auto-detect)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        validator = ProcessValidator(policy_path=args.policy)
        
        if args.verbose:
            print(f"Loaded process registry: {validator.policy_path}")
            print(f"Valid processes: {len(validator.valid_process_ids)}")
            print(f"Valid roles: {sorted(validator.all_valid_roles)}")
            print()
        
        is_valid, errors, stats = validator.validate_registry_file(
            registry_path=args.registry,
            verbose=args.verbose
        )
        
        print(f"\nResults:")
        print(f"  Total records: {stats['total']}")
        print(f"  Records with process fields: {stats['with_process_fields']}")
        print(f"  Valid: {stats['valid']}")
        print(f"  Invalid: {stats['invalid']}")
        
        if stats['by_process']:
            print(f"\n  Records by process:")
            for process_id, count in sorted(stats['by_process'].items()):
                print(f"    {process_id}: {count}")
        
        if is_valid:
            print("\n✅ Process validation PASSED")
            return 0
        else:
            print("\n❌ Process validation FAILED")
            for error in errors[:20]:
                print(error)
            if len(errors) > 20:
                print(f"  ... and {len(errors) - 20} more errors")
            return 1
    
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())

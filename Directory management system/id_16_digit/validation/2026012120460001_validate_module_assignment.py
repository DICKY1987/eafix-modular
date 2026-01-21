#!/usr/bin/env python3
"""
doc_id: 2026012120460001
Unified SSOT Registry - Module Assignment Validator

Validates module assignments against MODULE_ASSIGNMENT_POLICY.yaml.
Enforces precedence: override > manifest > path_rule > default.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ModuleAssignmentValidator:
    """Validates module assignments against policy."""
    
    def __init__(self, policy_path: Optional[str] = None):
        """
        Initialize validator.
        
        Args:
            policy_path: Path to MODULE_ASSIGNMENT_POLICY.yaml
        """
        if policy_path is None:
            base_dir = Path(__file__).parent.parent
            policy_path = base_dir / "contracts" / "2026012120420004_MODULE_ASSIGNMENT_POLICY.yaml"
        
        self.policy_path = Path(policy_path)
        self.policy = self._load_policy()
        self.precedence_chain = self.policy.get("precedence_chain", [])
        self._extract_path_rules()
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load and parse module assignment policy."""
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Module assignment policy not found: {self.policy_path}")
        
        with open(self.policy_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _extract_path_rules(self):
        """Extract path rules from precedence chain."""
        self.path_rules = []
        for level in self.precedence_chain:
            if level.get("source") == "path_rule":
                self.path_rules = level.get("rules", [])
                break
    
    def compute_expected_module_id(
        self, 
        record: Dict[str, Any],
        base_dir: Optional[Path] = None
    ) -> Tuple[Optional[str], str, str]:
        """
        Compute expected module_id using precedence chain.
        
        Args:
            record: Entity record
            base_dir: Base directory for manifest lookup
        
        Returns:
            (expected_module_id, source, reason) tuple
        """
        # Level 1: Override
        override = record.get("module_id_override")
        if override:
            return override, "override", "module_id_override field present"
        
        # Level 2: Manifest
        if base_dir:
            rel_path = record.get("relative_path", "")
            if rel_path:
                manifest_module = self._lookup_manifest_module(rel_path, base_dir)
                if manifest_module:
                    return manifest_module, "manifest", f"Found in .module.yaml manifest"
        
        # Level 3: Path rules
        rel_path = record.get("relative_path", "")
        if rel_path:
            for rule in self.path_rules:
                pattern = rule.get("pattern")
                module_id = rule.get("module_id")
                
                if not pattern or not module_id:
                    continue
                
                # Match pattern
                if re.match(pattern, rel_path):
                    return module_id, "path_rule", f"Matched pattern: {pattern}"
        
        # Level 4: Default (unassigned)
        return None, "unassigned", "No rules matched"
    
    def _lookup_manifest_module(
        self, 
        relative_path: str, 
        base_dir: Path
    ) -> Optional[str]:
        """
        Look up module_id from .module.yaml manifest.
        
        Searches parent directories for .module.yaml or module.yaml files.
        
        Args:
            relative_path: Relative path of entity
            base_dir: Base directory to search from
        
        Returns:
            module_id from manifest or None
        """
        # Get directory of the entity
        entity_path = base_dir / relative_path
        search_dir = entity_path.parent if entity_path.is_file() else entity_path
        
        # Search up the directory tree
        for _ in range(5):  # Limit search depth
            for manifest_name in [".module.yaml", "module.yaml"]:
                manifest_path = search_dir / manifest_name
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = yaml.safe_load(f)
                        
                        if isinstance(manifest, dict):
                            module_id = manifest.get("module_id")
                            if module_id:
                                return module_id
                    except Exception:
                        pass  # Ignore malformed manifests
            
            # Move to parent directory
            parent = search_dir.parent
            if parent == search_dir:
                break  # Reached root
            search_dir = parent
        
        return None
    
    def validate_record(
        self, 
        record: Dict[str, Any],
        base_dir: Optional[Path] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate module assignment for a record.
        
        Args:
            record: Entity record
            base_dir: Base directory for manifest lookup
        
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        
        # Only validate entity records
        if record.get("record_kind") != "entity":
            return True, []
        
        # Compute expected module_id
        expected_module_id, source, reason = self.compute_expected_module_id(record, base_dir)
        actual_module_id = record.get("module_id")
        
        # Check for mismatch
        if actual_module_id != expected_module_id:
            errors.append(
                f"Module mismatch: actual='{actual_module_id}' != expected='{expected_module_id}' "
                f"(source: {source}, reason: {reason})"
            )
        
        # Check for conflicts (multiple rules could apply)
        rel_path = record.get("relative_path", "")
        if rel_path:
            matched_rules = []
            for rule in self.path_rules:
                pattern = rule.get("pattern")
                if pattern and re.match(pattern, rel_path):
                    matched_rules.append((pattern, rule.get("module_id")))
            
            if len(matched_rules) > 1:
                # Multiple rules matched - potential ambiguity
                # Check if they all assign the same module_id
                module_ids = set(m[1] for m in matched_rules)
                if len(module_ids) > 1:
                    errors.append(
                        f"Multiple conflicting path rules matched for '{rel_path}': " +
                        ", ".join(f"{p} → {m}" for p, m in matched_rules)
                    )
        
        return len(errors) == 0, errors
    
    def validate_registry_file(
        self,
        registry_path: str,
        base_dir: Optional[str] = None,
        verbose: bool = False
    ) -> Tuple[bool, List[str], Dict[str, int]]:
        """
        Validate all entity records in registry.
        
        Args:
            registry_path: Path to ID_REGISTRY.json
            base_dir: Base directory for manifest lookup
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
            "entities": 0,
            "valid": 0,
            "invalid": 0,
            "by_source": {}
        }
        
        # Convert base_dir to Path
        base_path = Path(base_dir) if base_dir else Path(registry_path).parent
        
        for idx, record in enumerate(records):
            record_id = record.get("record_id", f"record_{idx}")
            
            if record.get("record_kind") != "entity":
                continue
            
            stats["entities"] += 1
            
            is_valid, errors = self.validate_record(record, base_path)
            
            # Track module source distribution
            _, source, _ = self.compute_expected_module_id(record, base_path)
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
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
        description="Validate module assignments against policy"
    )
    parser.add_argument(
        "--registry",
        default="ID_REGISTRY.json",
        help="Path to registry file"
    )
    parser.add_argument(
        "--policy",
        help="Path to MODULE_ASSIGNMENT_POLICY.yaml (default: auto-detect)"
    )
    parser.add_argument(
        "--base-dir",
        help="Base directory for manifest lookup (default: registry directory)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        validator = ModuleAssignmentValidator(policy_path=args.policy)
        
        if args.verbose:
            print(f"Loaded policy: {validator.policy_path}")
            print(f"Path rules: {len(validator.path_rules)}")
            print()
        
        is_valid, errors, stats = validator.validate_registry_file(
            registry_path=args.registry,
            base_dir=args.base_dir,
            verbose=args.verbose
        )
        
        print(f"\nResults:")
        print(f"  Total records: {stats['total']}")
        print(f"  Entity records: {stats['entities']}")
        print(f"  Valid: {stats['valid']}")
        print(f"  Invalid: {stats['invalid']}")
        
        if stats['by_source']:
            print(f"\n  Module source distribution:")
            for source, count in sorted(stats['by_source'].items()):
                print(f"    {source}: {count}")
        
        if is_valid:
            print("\n✅ Module assignment validation PASSED")
            return 0
        else:
            print("\n❌ Module assignment validation FAILED")
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

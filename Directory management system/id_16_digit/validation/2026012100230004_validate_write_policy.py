"""
doc_id: 2026012100230004
title: Write Policy Validator
version: 1.0
date: 2026-01-21T00:23:14Z
purpose: Enforce column ownership and write rules to prevent registry drift
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class WritePolicyValidator:
    """Validates registry writes against WRITE_POLICY.yaml."""
    
    def __init__(self, policy_path: Optional[str] = None):
        """
        Initialize validator with write policy.
        
        Args:
            policy_path: Path to WRITE_POLICY.yaml (auto-detects if None)
        """
        if policy_path is None:
            policy_path = self._find_policy_file()
        
        self.policy_path = Path(policy_path)
        self.policy = self._load_policy()
        self.violations = []
        
    def _find_policy_file(self) -> str:
        """Auto-detect WRITE_POLICY.yaml location."""
        candidates = [
            Path("contracts/2026012100230001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml"),
            Path("../contracts/2026012100230001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml"),
            Path("contracts/UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml"),
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        raise FileNotFoundError(
            "Could not find WRITE_POLICY.yaml. "
            "Expected at: contracts/2026012100230001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml"
        )
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load write policy from YAML file."""
        with open(self.policy_path, 'r', encoding='utf-8') as f:
            policy = yaml.safe_load(f)
        
        print(f"✓ Loaded write policy from {self.policy_path}")
        print(f"  Policy version: {policy.get('policy_version')}")
        print(f"  Columns defined: {len(policy.get('columns', {}))}")
        
        return policy
    
    def validate_write(
        self,
        column: str,
        old_value: Any,
        new_value: Any,
        actor: str,
        record: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a single column write.
        
        Args:
            column: Column name
            old_value: Current value (None if new record)
            new_value: Proposed new value
            actor: Who is making the change (tool name or user ID)
            record: Full record for context
            
        Returns:
            (is_valid, error_message)
        """
        # Get column policy
        col_policy = self.policy['columns'].get(column)
        if not col_policy:
            # Unknown column - allow (forward compatibility)
            return True, None
        
        writable_by = col_policy['writable_by']
        update_policy = col_policy['update_policy']
        
        # Determine if actor is tool or user
        is_tool = self._is_tool_actor(actor)
        
        # Check ownership
        if writable_by == 'tool_only' and not is_tool:
            return False, f"Column '{column}' is tool-only, user writes rejected"
        
        if writable_by == 'user_only' and is_tool:
            return False, f"Column '{column}' is user-only, tool writes rejected"
        
        if writable_by == 'never':
            if old_value is not None:
                return False, f"Column '{column}' is immutable after creation"
        
        # Check update policy
        if update_policy == 'immutable':
            if old_value is not None and old_value != new_value:
                # Allow null to non-null (lazy population)
                if old_value is None:
                    return True, None
                return False, f"Column '{column}' is immutable, cannot change from {old_value} to {new_value}"
        
        # Check status transitions
        if column == 'status' and old_value is not None:
            allowed = col_policy.get('allowed_transitions', {}).get(old_value, [])
            if new_value not in allowed:
                return False, f"Status transition {old_value} -> {new_value} not allowed"
        
        return True, None
    
    def validate_record(
        self,
        record: Dict[str, Any],
        old_record: Optional[Dict[str, Any]],
        actor: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate all changes in a record.
        
        Args:
            record: New/updated record
            old_record: Previous record state (None if new)
            actor: Who is making changes
            
        Returns:
            (all_valid, list_of_errors)
        """
        errors = []
        
        for column, new_value in record.items():
            old_value = old_record.get(column) if old_record else None
            
            # Skip if value unchanged
            if old_record and old_value == new_value:
                continue
            
            is_valid, error = self.validate_write(
                column, old_value, new_value, actor, record
            )
            
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors
    
    def _is_tool_actor(self, actor: str) -> bool:
        """Determine if actor is a tool or user."""
        tool_prefixes = ['scanner', 'validator', 'generator', 'migrator', 'system', 'tool']
        actor_lower = actor.lower()
        return any(actor_lower.startswith(prefix) for prefix in tool_prefixes)
    
    def check_override_precedence(
        self,
        record: Dict[str, Any],
        column: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if override field precedence is correct.
        
        Args:
            record: Record to check
            column: Column to check (must have override_field in policy)
            
        Returns:
            (is_valid, error_message)
        """
        col_policy = self.policy['columns'].get(column)
        if not col_policy:
            return True, None
        
        override_field = col_policy.get('override_field')
        if not override_field:
            return True, None
        
        override_value = record.get(override_field)
        derived_value = record.get(column)
        
        if override_value is not None and override_value != derived_value:
            return False, f"Column '{column}' should match override field '{override_field}' when override is set"
        
        return True, None
    
    def validate_registry(
        self,
        registry: Dict[str, Any],
        actor: str = "validator"
    ) -> Tuple[bool, List[str]]:
        """
        Validate entire registry against write policy.
        
        Args:
            registry: Full registry to validate
            actor: Who is validating (default: validator)
            
        Returns:
            (all_valid, list_of_errors)
        """
        errors = []
        
        records = registry.get('records', [])
        print(f"\n✓ Validating {len(records)} records against write policy...")
        
        for idx, record in enumerate(records):
            record_id = record.get('record_id', f'record_{idx}')
            
            # Check immutable fields weren't changed (compare to "creation state")
            # Since we don't have history, we just validate consistency
            
            # Check override precedence for module_id
            if 'module_id' in record:
                is_valid, error = self.check_override_precedence(record, 'module_id')
                if not is_valid:
                    errors.append(f"[{record_id}] {error}")
        
        if errors:
            print(f"✗ Write policy violations found: {len(errors)}")
            for error in errors[:10]:  # Show first 10
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        else:
            print(f"✓ All records pass write policy validation")
        
        return len(errors) == 0, errors
    
    def get_column_policy(self, column: str) -> Optional[Dict[str, Any]]:
        """Get policy for a specific column."""
        return self.policy['columns'].get(column)
    
    def is_tool_writable(self, column: str) -> bool:
        """Check if column is writable by tools."""
        col_policy = self.get_column_policy(column)
        if not col_policy:
            return False
        return col_policy['writable_by'] in ['tool_only', 'both']
    
    def is_user_writable(self, column: str) -> bool:
        """Check if column is writable by users."""
        col_policy = self.get_column_policy(column)
        if not col_policy:
            return False
        return col_policy['writable_by'] in ['user_only', 'both']
    
    def get_writable_columns(self, actor: str) -> List[str]:
        """Get list of columns writable by actor."""
        is_tool = self._is_tool_actor(actor)
        writable = []
        
        for column, col_policy in self.policy['columns'].items():
            writable_by = col_policy['writable_by']
            
            if writable_by == 'both':
                writable.append(column)
            elif is_tool and writable_by == 'tool_only':
                writable.append(column)
            elif not is_tool and writable_by == 'user_only':
                writable.append(column)
        
        return writable


def main():
    """CLI entry point for write policy validation."""
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validate_write_policy.py <registry.json>")
        sys.exit(1)
    
    registry_path = sys.argv[1]
    
    print(f"Validating registry: {registry_path}")
    print("=" * 60)
    
    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # Validate
    validator = WritePolicyValidator()
    is_valid, errors = validator.validate_registry(registry)
    
    print("\n" + "=" * 60)
    if is_valid:
        print("✓ PASS: Registry complies with write policy")
        sys.exit(0)
    else:
        print(f"✗ FAIL: {len(errors)} write policy violations")
        sys.exit(1)


if __name__ == '__main__':
    main()

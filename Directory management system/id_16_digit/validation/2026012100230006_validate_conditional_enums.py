"""
doc_id: 2026012100230006
title: Conditional Enum Validator
version: 1.0
date: 2026-01-21T00:23:14Z
purpose: Validate conditional enum constraints (e.g., transient-only status values)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


class ConditionalEnumValidator:
    """Validates conditional enum constraints."""
    
    # Enum definitions with conditional rules
    STATUS_CORE = ['active', 'deprecated', 'quarantined', 'archived', 'deleted']
    STATUS_TRANSIENT = ['closed', 'running', 'pending', 'failed']
    STATUS_ALL = STATUS_CORE + STATUS_TRANSIENT
    
    ENTITY_KIND_EXPLICIT = ['file', 'asset', 'transient', 'external', 'module', 'directory', 'process']
    ENTITY_KIND_ALL = ENTITY_KIND_EXPLICIT + ['other']
    
    RECORD_KIND_ALL = ['entity', 'edge', 'generator']
    
    def __init__(self):
        """Initialize validator."""
        self.violations = []
    
    def validate_status_conditional(
        self,
        record: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate status field conditional constraints.
        
        Rule: Transient-specific states only allowed when entity_kind=transient
        
        Args:
            record: Record to validate
            
        Returns:
            (is_valid, error_message)
        """
        status = record.get('status')
        entity_kind = record.get('entity_kind')
        record_kind = record.get('record_kind')
        record_id = record.get('record_id', 'UNKNOWN')
        
        if not status:
            return True, None
        
        # Only apply to entity records
        if record_kind != 'entity':
            return True, None
        
        # Check if status is transient-specific
        if status in self.STATUS_TRANSIENT:
            if entity_kind != 'transient':
                return False, (
                    f"Status '{status}' only allowed for transient entities, "
                    f"but entity_kind='{entity_kind}'"
                )
        
        # Check if status is valid at all
        if status not in self.STATUS_ALL:
            return False, f"Invalid status value: '{status}'"
        
        return True, None
    
    def validate_entity_kind_other(
        self,
        record: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate entity_kind='other' has required documentation.
        
        Rule: entity_kind='other' must have reason in notes field
        
        Args:
            record: Record to validate
            
        Returns:
            (is_valid, error_message)
        """
        entity_kind = record.get('entity_kind')
        record_kind = record.get('record_kind')
        notes = record.get('notes', '')
        record_id = record.get('record_id', 'UNKNOWN')
        
        if record_kind != 'entity':
            return True, None
        
        if entity_kind == 'other':
            if not notes or 'Temporary:' not in notes:
                return False, (
                    "entity_kind='other' requires documentation in notes field "
                    "(must contain 'Temporary: [reason]')"
                )
        
        # Check if entity_kind is valid
        if entity_kind not in self.ENTITY_KIND_ALL:
            return False, f"Invalid entity_kind value: '{entity_kind}'"
        
        return True, None
    
    def validate_expires_utc_coexistence(
        self,
        record: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate expires_utc and ttl_seconds coexistence.
        
        Rule: If expires_utc is set, ttl_seconds should also be set
        
        Args:
            record: Record to validate
            
        Returns:
            (is_valid, error_message)
        """
        expires_utc = record.get('expires_utc')
        ttl_seconds = record.get('ttl_seconds')
        entity_kind = record.get('entity_kind')
        record_kind = record.get('record_kind')
        record_id = record.get('record_id', 'UNKNOWN')
        
        if record_kind != 'entity' or entity_kind != 'transient':
            return True, None
        
        if expires_utc and not ttl_seconds:
            # Warning, not error (expires_utc could be manually set)
            return True, None
        
        if ttl_seconds and not expires_utc:
            return False, (
                "ttl_seconds is set but expires_utc is not computed "
                "(should be ADD_SECONDS(created_utc, ttl_seconds))"
            )
        
        return True, None
    
    def validate_record_kind(
        self,
        record: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate record_kind is valid.
        
        Args:
            record: Record to validate
            
        Returns:
            (is_valid, error_message)
        """
        record_kind = record.get('record_kind')
        record_id = record.get('record_id', 'UNKNOWN')
        
        if not record_kind:
            return False, "Missing required field: record_kind"
        
        if record_kind not in self.RECORD_KIND_ALL:
            return False, f"Invalid record_kind value: '{record_kind}'"
        
        return True, None
    
    def validate_edge_required_fields(
        self,
        record: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate edge records have required fields.
        
        Args:
            record: Record to validate
            
        Returns:
            (is_valid, error_message)
        """
        record_kind = record.get('record_kind')
        
        if record_kind != 'edge':
            return True, None
        
        required = ['edge_id', 'source_entity_id', 'target_entity_id', 'rel_type']
        missing = [f for f in required if not record.get(f)]
        
        if missing:
            return False, f"Edge missing required fields: {', '.join(missing)}"
        
        return True, None
    
    def validate_generator_required_fields(
        self,
        record: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate generator records have required fields.
        
        Args:
            record: Record to validate
            
        Returns:
            (is_valid, error_message)
        """
        record_kind = record.get('record_kind')
        
        if record_kind != 'generator':
            return True, None
        
        # Must have output_path OR output_path_pattern
        output_path = record.get('output_path')
        output_path_pattern = record.get('output_path_pattern')
        
        if not output_path and not output_path_pattern:
            return False, "Generator must have output_path OR output_path_pattern"
        
        # Must have sort_keys OR sort_rule_id
        sort_keys = record.get('sort_keys')
        sort_rule_id = record.get('sort_rule_id')
        
        if not sort_keys and not sort_rule_id:
            return False, "Generator must have sort_keys OR sort_rule_id"
        
        # Must have declared_dependencies
        declared_dependencies = record.get('declared_dependencies')
        if not declared_dependencies:
            return False, "Generator must have declared_dependencies (non-empty list)"
        
        return True, None
    
    def validate_record(
        self,
        record: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate all conditional constraints for record.
        
        Args:
            record: Record to validate
            
        Returns:
            (all_valid, list_of_errors)
        """
        errors = []
        record_id = record.get('record_id', 'UNKNOWN')
        
        # Run all validators
        validators = [
            self.validate_record_kind,
            self.validate_status_conditional,
            self.validate_entity_kind_other,
            self.validate_expires_utc_coexistence,
            self.validate_edge_required_fields,
            self.validate_generator_required_fields,
        ]
        
        for validator in validators:
            is_valid, error = validator(record)
            if not is_valid:
                errors.append(f"[{record_id}] {error}")
        
        return len(errors) == 0, errors
    
    def validate_registry(
        self,
        registry: Dict[str, Any]
    ) -> Tuple[bool, List[str], Dict[str, int]]:
        """
        Validate entire registry.
        
        Args:
            registry: Full registry to validate
            
        Returns:
            (all_valid, list_of_errors, statistics)
        """
        errors = []
        stats = {
            'total_records': 0,
            'entity_kind_other_count': 0,
            'transient_status_count': 0,
        }
        
        records = registry.get('records', [])
        stats['total_records'] = len(records)
        
        print(f"\n✓ Validating {len(records)} records for conditional enum constraints...")
        
        for record in records:
            # Collect statistics
            if record.get('entity_kind') == 'other':
                stats['entity_kind_other_count'] += 1
            
            if record.get('status') in self.STATUS_TRANSIENT:
                stats['transient_status_count'] += 1
            
            # Validate
            is_valid, record_errors = self.validate_record(record)
            if not is_valid:
                errors.extend(record_errors)
        
        # Check entity_kind='other' threshold (>10% triggers warning)
        if stats['total_records'] > 0:
            other_percent = (stats['entity_kind_other_count'] / stats['total_records']) * 100
            if other_percent > 10:
                print(f"\n⚠ WARNING: {other_percent:.1f}% of entities use entity_kind='other'")
                print("  Consider promoting common 'other' patterns to explicit entity kinds")
        
        if errors:
            print(f"✗ Conditional enum violations found: {len(errors)}")
            for error in errors[:10]:  # Show first 10
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        else:
            print(f"✓ All records pass conditional enum validation")
        
        return len(errors) == 0, errors, stats


def main():
    """CLI entry point for conditional enum validation."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validate_conditional_enums.py <registry.json>")
        sys.exit(1)
    
    registry_path = sys.argv[1]
    
    print(f"Validating registry: {registry_path}")
    print("=" * 60)
    
    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # Validate
    validator = ConditionalEnumValidator()
    is_valid, errors, stats = validator.validate_registry(registry)
    
    print("\n" + "=" * 60)
    print(f"Statistics:")
    print(f"  Total records: {stats['total_records']}")
    print(f"  entity_kind='other': {stats['entity_kind_other_count']}")
    print(f"  Transient status values: {stats['transient_status_count']}")
    
    print("\n" + "=" * 60)
    if is_valid:
        print("✓ PASS: All conditional enum constraints satisfied")
        sys.exit(0)
    else:
        print(f"✗ FAIL: {len(errors)} conditional enum violations")
        sys.exit(1)


if __name__ == '__main__':
    main()

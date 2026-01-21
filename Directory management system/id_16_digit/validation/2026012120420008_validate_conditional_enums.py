#!/usr/bin/env python3
"""
doc_id: 2026012120420008
Unified SSOT Registry - Conditional Enum Validator

Validates context-aware enum constraints (e.g., status field depends on entity_kind).
Ensures transient-specific statuses only used for transient entities.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ConditionalEnumValidator:
    """Validates conditional enum constraints."""
    
    # Core lifecycle statuses (all entity kinds)
    CORE_LIFECYCLE = {"active", "deprecated", "quarantined", "archived", "deleted"}
    
    # Transient-specific statuses
    TRANSIENT_SPECIFIC = {"closed", "running", "pending", "failed"}
    
    def __init__(self):
        """Initialize validator with enum rules."""
        self.rules = self._init_rules()
    
    def _init_rules(self) -> List[Dict[str, Any]]:
        """Initialize validation rules."""
        return [
            {
                "name": "status_by_entity_kind",
                "field": "status",
                "applies_when": {"record_kind": "entity"},
                "validator": self._validate_status_by_entity_kind
            },
            {
                "name": "ttl_with_expires",
                "field": "ttl_seconds",
                "applies_when": {"record_kind": "entity", "entity_kind": "transient"},
                "validator": self._validate_ttl_with_expires
            },
            {
                "name": "edge_evidence_required",
                "field": "evidence_method",
                "applies_when": {"record_kind": "edge"},
                "validator": self._validate_edge_evidence
            }
        ]
    
    def _applies_to_record(self, rule: Dict[str, Any], record: Dict[str, Any]) -> bool:
        """Check if rule applies to record."""
        applies_when = rule.get("applies_when", {})
        
        for field, expected in applies_when.items():
            actual = record.get(field)
            if actual != expected:
                return False
        
        return True
    
    def _validate_status_by_entity_kind(
        self, 
        record: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate status field based on entity_kind.
        
        Rule: Transient statuses only allowed for entity_kind=transient
        """
        status = record.get("status")
        entity_kind = record.get("entity_kind")
        
        if not status:
            return True, None  # No status set (allowed)
        
        # Determine allowed statuses
        if entity_kind == "transient":
            allowed = self.CORE_LIFECYCLE | self.TRANSIENT_SPECIFIC
        else:
            allowed = self.CORE_LIFECYCLE
        
        if status not in allowed:
            return False, (
                f"Status '{status}' not allowed for entity_kind='{entity_kind}'. "
                f"Allowed: {sorted(allowed)}"
            )
        
        return True, None
    
    def _validate_ttl_with_expires(
        self, 
        record: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate TTL and expiration consistency.
        
        Rule: If ttl_seconds set, expires_utc should be present (and vice versa)
        """
        ttl_seconds = record.get("ttl_seconds")
        expires_utc = record.get("expires_utc")
        
        if ttl_seconds is not None and expires_utc is None:
            return False, "ttl_seconds set but expires_utc missing (should be derived)"
        
        if expires_utc is not None and ttl_seconds is None:
            return False, "expires_utc set but ttl_seconds missing (required for expiration)"
        
        return True, None
    
    def _validate_edge_evidence(
        self, 
        record: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate edge evidence fields.
        
        Rule: Edges must have evidence_method set
        """
        evidence_method = record.get("evidence_method")
        
        if not evidence_method:
            return False, "Edge missing evidence_method (required for auditability)"
        
        # Known evidence methods
        known_methods = {
            "static_parse", "dynamic_trace", "user_asserted", 
            "heuristic", "config_declared"
        }
        
        if evidence_method not in known_methods:
            # Warning, not error (open enum)
            pass
        
        return True, None
    
    def validate_record(
        self, 
        record: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate all conditional enums in a record.
        
        Args:
            record: Record to validate
        
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        
        for rule in self.rules:
            if not self._applies_to_record(rule, record):
                continue
            
            validator = rule.get("validator")
            if not validator:
                continue
            
            is_valid, error = validator(record)
            
            if not is_valid and error:
                errors.append(f"[{rule['name']}] {error}")
        
        return len(errors) == 0, errors
    
    def validate_registry_file(
        self,
        registry_path: str,
        verbose: bool = False
    ) -> tuple[bool, List[str], Dict[str, int]]:
        """
        Validate all records in registry.
        
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
        stats = {"total": len(records), "valid": 0, "invalid": 0}
        
        for idx, record in enumerate(records):
            record_id = record.get("record_id", f"record_{idx}")
            
            is_valid, errors = self.validate_record(record)
            
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
        description="Validate conditional enum constraints"
    )
    parser.add_argument(
        "--registry",
        default="ID_REGISTRY.json",
        help="Path to registry file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        validator = ConditionalEnumValidator()
        
        if args.verbose:
            print("Conditional enum rules:")
            for rule in validator.rules:
                print(f"  - {rule['name']}: {rule['field']}")
            print()
        
        is_valid, errors, stats = validator.validate_registry_file(
            registry_path=args.registry,
            verbose=args.verbose
        )
        
        print(f"\nResults: {stats['valid']}/{stats['total']} valid, {stats['invalid']} invalid")
        
        if is_valid:
            print("✅ Conditional enum validation PASSED")
            return 0
        else:
            print("❌ Conditional enum validation FAILED")
            for error in errors:
                print(error)
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

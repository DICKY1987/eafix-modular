#!/usr/bin/env python3
"""
doc_id: 2026012120420009
Unified SSOT Registry - Edge Evidence Validator

Validates edge evidence completeness and auto-quarantines low-quality edges.
Enforces evidence requirements per method (static_parse, heuristic, etc).
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class EdgeEvidenceValidator:
    """Validates edge evidence against EDGE_EVIDENCE_POLICY."""
    
    def __init__(self, policy_path: Optional[str] = None):
        """
        Initialize validator with evidence policy.
        
        Args:
            policy_path: Path to EDGE_EVIDENCE_POLICY.yaml (default: auto-detect)
        """
        if policy_path is None:
            base_dir = Path(__file__).parent.parent
            policy_path = base_dir / "contracts" / "2026012120420003_EDGE_EVIDENCE_POLICY.yaml"
        
        self.policy_path = Path(policy_path)
        self.policy = self._load_policy()
        self.evidence_methods = self.policy.get("evidence_methods", {})
        self.validation_rules = self.policy.get("validation_rules", {})
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load and parse evidence policy YAML."""
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Evidence policy not found: {self.policy_path}")
        
        with open(self.policy_path, 'r', encoding='utf-8') as f:
            policy = yaml.safe_load(f)
        
        if not policy or "evidence_methods" not in policy:
            raise ValueError(f"Invalid policy file: missing 'evidence_methods' key")
        
        return policy
    
    def validate_edge(
        self, 
        edge: Dict[str, Any],
        auto_correct: bool = False
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate edge evidence.
        
        Args:
            edge: Edge record to validate
            auto_correct: If True, apply auto-corrections (e.g., quarantine)
        
        Returns:
            (is_valid, error_messages, corrections) tuple
        """
        errors = []
        corrections = {}
        
        # Rule 1: evidence_method must be set
        evidence_method = edge.get("evidence_method")
        if not evidence_method:
            errors.append("Missing evidence_method (required for all edges)")
            return False, errors, corrections
        
        # Check if method is known
        if evidence_method not in self.evidence_methods:
            errors.append(f"Unknown evidence_method: '{evidence_method}'")
            # Don't fail entirely, just warn
        
        method_spec = self.evidence_methods.get(evidence_method, {})
        
        # Rule 2: Required fields must be present
        required_fields = method_spec.get("required_fields", [])
        for field in required_fields:
            if not edge.get(field):
                errors.append(f"Missing required field '{field}' for evidence_method='{evidence_method}'")
        
        # Rule 3: Confidence must be in allowed range
        confidence = edge.get("confidence")
        if confidence is not None:
            conf_range = method_spec.get("confidence_range", [0.0, 1.0])
            if not (conf_range[0] <= confidence <= conf_range[1]):
                errors.append(
                    f"Confidence {confidence} out of range {conf_range} "
                    f"for evidence_method='{evidence_method}'"
                )
        
        # Rule 4: Heuristic edges must have notes with "heuristic:" prefix
        if evidence_method == "heuristic":
            notes = edge.get("notes", "")
            if not notes or "heuristic:" not in notes.lower():
                errors.append("Heuristic edges must have notes with 'heuristic:' prefix documenting the rule")
        
        # Rule 5: User-asserted edges must have non-empty notes
        if evidence_method == "user_asserted":
            notes = edge.get("notes", "")
            if not notes:
                errors.append("User-asserted edges must have notes explaining the rationale")
        
        # Rule 6: evidence_locator format validation
        evidence_locator = edge.get("evidence_locator", "")
        validation_rules = method_spec.get("validation_rules", [])
        for rule in validation_rules:
            if isinstance(rule, str) and "evidence_locator matches pattern" in rule:
                # Extract pattern
                match = re.search(r'pattern "(.*?)"', rule)
                if match:
                    pattern = match.group(1)
                    if not re.match(pattern, evidence_locator):
                        errors.append(f"evidence_locator '{evidence_locator}' doesn't match expected pattern: {pattern}")
        
        # Auto-quarantine checks
        status = edge.get("status", "active")
        should_quarantine = False
        quarantine_reason = None
        
        # Check auto-quarantine triggers
        triggers = self.policy.get("quarantine_policy", {}).get("auto_quarantine_triggers", [])
        for trigger in triggers:
            if "evidence_method" in trigger:
                if evidence_method == trigger["evidence_method"]:
                    should_quarantine = True
                    quarantine_reason = trigger["reason"]
                    break
            
            if "confidence" in trigger:
                trigger_conf = trigger["confidence"]
                if "< " in trigger_conf:
                    threshold = float(trigger_conf.split("< ")[1])
                    if confidence and confidence < threshold:
                        should_quarantine = True
                        quarantine_reason = trigger["reason"]
                        break
            
            if "evidence_locator" in trigger and trigger["evidence_locator"] is None:
                if not evidence_locator:
                    should_quarantine = True
                    quarantine_reason = trigger["reason"]
                    break
        
        # Apply auto-correction if enabled
        if should_quarantine and auto_correct:
            if status != "quarantined":
                corrections["status"] = "quarantined"
                corrections["_reason"] = quarantine_reason
        elif should_quarantine and status != "quarantined":
            errors.append(f"Edge should be quarantined: {quarantine_reason}")
        
        return len(errors) == 0, errors, corrections
    
    def validate_registry_file(
        self,
        registry_path: str,
        auto_correct: bool = False,
        verbose: bool = False
    ) -> Tuple[bool, List[str], Dict[str, int]]:
        """
        Validate all edges in registry.
        
        Args:
            registry_path: Path to ID_REGISTRY.json
            auto_correct: Apply auto-corrections (quarantine)
            verbose: Print detailed results
        
        Returns:
            (is_valid, error_messages, stats) tuple
        """
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        records = registry.get("records", [])
        all_errors = []
        stats = {
            "total_edges": 0, 
            "valid": 0, 
            "invalid": 0,
            "quarantined": 0,
            "auto_corrected": 0
        }
        
        for idx, record in enumerate(records):
            # Only validate edges
            if record.get("record_kind") != "edge":
                continue
            
            stats["total_edges"] += 1
            edge_id = record.get("edge_id", f"edge_{idx}")
            
            is_valid, errors, corrections = self.validate_edge(
                edge=record,
                auto_correct=auto_correct
            )
            
            if record.get("status") == "quarantined":
                stats["quarantined"] += 1
            
            if corrections:
                stats["auto_corrected"] += 1
                if verbose:
                    print(f"→ {edge_id}: Auto-corrected {list(corrections.keys())}")
            
            if is_valid:
                stats["valid"] += 1
                if verbose:
                    print(f"✓ {edge_id}")
            else:
                stats["invalid"] += 1
                if verbose:
                    print(f"✗ {edge_id}")
                for error in errors:
                    all_errors.append(f"  {edge_id}: {error}")
                    if verbose:
                        print(f"    {error}")
        
        return len(all_errors) == 0, all_errors, stats
    
    def get_evidence_methods(self) -> List[str]:
        """Get list of known evidence methods."""
        return list(self.evidence_methods.keys())
    
    def get_method_requirements(self, method: str) -> Dict[str, Any]:
        """Get requirements for a specific evidence method."""
        return self.evidence_methods.get(method, {})


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate edge evidence requirements"
    )
    parser.add_argument(
        "--registry",
        default="ID_REGISTRY.json",
        help="Path to registry file"
    )
    parser.add_argument(
        "--policy",
        help="Path to evidence policy YAML (default: auto-detect)"
    )
    parser.add_argument(
        "--auto-correct",
        action="store_true",
        help="Apply auto-corrections (e.g., quarantine low-quality edges)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--list-methods",
        action="store_true",
        help="List known evidence methods and exit"
    )
    
    args = parser.parse_args()
    
    try:
        validator = EdgeEvidenceValidator(policy_path=args.policy)
        
        if args.list_methods:
            print("Known evidence methods:")
            for method in validator.get_evidence_methods():
                spec = validator.get_method_requirements(method)
                print(f"\n  {method}:")
                print(f"    Description: {spec.get('description')}")
                print(f"    Confidence range: {spec.get('confidence_range')}")
                print(f"    Required fields: {spec.get('required_fields')}")
            return 0
        
        if args.verbose:
            print(f"Loaded evidence policy: {validator.policy_path}")
            print(f"Known evidence methods: {len(validator.evidence_methods)}")
            print()
        
        is_valid, errors, stats = validator.validate_registry_file(
            registry_path=args.registry,
            auto_correct=args.auto_correct,
            verbose=args.verbose
        )
        
        print(f"\nResults:")
        print(f"  Total edges: {stats['total_edges']}")
        print(f"  Valid: {stats['valid']}")
        print(f"  Invalid: {stats['invalid']}")
        print(f"  Quarantined: {stats['quarantined']}")
        if args.auto_correct:
            print(f"  Auto-corrected: {stats['auto_corrected']}")
        
        if is_valid:
            print("\n✅ Edge evidence validation PASSED")
            return 0
        else:
            print("\n❌ Edge evidence validation FAILED")
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

"""
doc_id: 2026012100230009
title: Edge Evidence Validator
version: 1.0
date: 2026-01-21T00:23:14Z
purpose: Validate edge evidence requirements per EDGE_EVIDENCE_POLICY.yaml
"""

import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta, timezone


class EdgeEvidenceValidator:
    """Validates edge evidence against policy requirements."""
    
    def __init__(self, policy_path: Optional[str] = None):
        """
        Initialize validator with edge evidence policy.
        
        Args:
            policy_path: Path to EDGE_EVIDENCE_POLICY.yaml (auto-detects if None)
        """
        if policy_path is None:
            policy_path = self._find_policy_file()
        
        self.policy_path = Path(policy_path)
        self.policy = self._load_policy()
        self.violations = []
        
    def _find_policy_file(self) -> str:
        """Auto-detect EDGE_EVIDENCE_POLICY.yaml location."""
        candidates = [
            Path("contracts/2026012100230008_EDGE_EVIDENCE_POLICY.yaml"),
            Path("../contracts/2026012100230008_EDGE_EVIDENCE_POLICY.yaml"),
            Path("contracts/EDGE_EVIDENCE_POLICY.yaml"),
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        raise FileNotFoundError(
            "Could not find EDGE_EVIDENCE_POLICY.yaml. "
            "Expected at: contracts/2026012100230008_EDGE_EVIDENCE_POLICY.yaml"
        )
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load edge evidence policy from YAML file."""
        with open(self.policy_path, 'r', encoding='utf-8') as f:
            policy = yaml.safe_load(f)
        
        print(f"✓ Loaded edge evidence policy from {self.policy_path}")
        print(f"  Policy version: {policy.get('policy_version')}")
        print(f"  Evidence methods: {len(policy.get('evidence_methods', {}))}")
        
        return policy
    
    def validate_evidence_method(
        self,
        edge: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate evidence fields for an edge.
        
        Args:
            edge: Edge record to validate
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        edge_id = edge.get('edge_id', 'UNKNOWN')
        
        # Check evidence_method exists
        evidence_method = edge.get('evidence_method')
        if not evidence_method:
            return False, [f"Missing required field: evidence_method"]
        
        # Get method definition
        methods = self.policy.get('evidence_methods', {})
        method_def = methods.get(evidence_method)
        
        if not method_def:
            return False, [f"Unknown evidence_method: '{evidence_method}'"]
        
        # Check required fields
        required_fields = method_def.get('required_fields', [])
        for field in required_fields:
            if not edge.get(field):
                errors.append(f"Missing required field for {evidence_method}: {field}")
        
        # Validate confidence range
        confidence = edge.get('confidence')
        if confidence is not None:
            conf_range = method_def.get('confidence_range', [0.0, 1.0])
            if not (conf_range[0] <= confidence <= conf_range[1]):
                errors.append(
                    f"Confidence {confidence} outside allowed range {conf_range} "
                    f"for {evidence_method}"
                )
        
        # Validate evidence_locator pattern
        evidence_locator = edge.get('evidence_locator')
        if evidence_locator:
            patterns = self.policy.get('evidence_locator_patterns', {}).get(evidence_method, [])
            if patterns:
                matches_pattern = any(re.match(pattern, evidence_locator) for pattern in patterns)
                if not matches_pattern:
                    errors.append(
                        f"evidence_locator '{evidence_locator}' does not match "
                        f"expected patterns for {evidence_method}"
                    )
        
        # Check notes requirement
        if evidence_method in ['user_asserted', 'heuristic']:
            notes = edge.get('notes', '')
            if not notes:
                errors.append(f"{evidence_method} requires notes field")
            elif evidence_method == 'heuristic' and not notes.startswith('heuristic:'):
                errors.append("heuristic method requires notes with 'heuristic:' prefix")
        
        # Check observed_utc age for user_asserted
        if evidence_method == 'user_asserted':
            observed_utc = edge.get('observed_utc')
            if observed_utc:
                try:
                    obs_date = datetime.fromisoformat(observed_utc.replace('Z', '+00:00'))
                    age_days = (datetime.now(timezone.utc) - obs_date).days
                    if age_days > 90:
                        # Warning, not error
                        print(f"⚠ [{edge_id}] User assertion is {age_days} days old (>90 days)")
                except Exception as e:
                    errors.append(f"Invalid observed_utc format: {e}")
        
        return len(errors) == 0, errors
    
    def check_auto_quarantine(
        self,
        edge: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if edge should be auto-quarantined.
        
        Args:
            edge: Edge record
            
        Returns:
            (should_quarantine, reason)
        """
        edge_id = edge.get('edge_id', 'UNKNOWN')
        
        # Check auto-quarantine conditions
        evidence_method = edge.get('evidence_method')
        confidence = edge.get('confidence', 1.0)
        evidence_locator = edge.get('evidence_locator')
        
        # Heuristic method
        if evidence_method == 'heuristic':
            return True, "Heuristic edges must be quarantined until confirmed"
        
        # Low confidence
        if confidence < 0.5:
            return True, f"Confidence {confidence} < 0.5 threshold"
        
        # Missing evidence_locator
        if not evidence_locator:
            return True, "Missing evidence_locator"
        
        return False, None
    
    def validate_edge_flags(
        self,
        edge: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate edge_flags are consistent with evidence_method.
        
        Args:
            edge: Edge record
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        edge_id = edge.get('edge_id', 'UNKNOWN')
        
        evidence_method = edge.get('evidence_method')
        edge_flags = edge.get('edge_flags', [])
        
        # Get expected auto_flags from policy
        methods = self.policy.get('evidence_methods', {})
        method_def = methods.get(evidence_method, {})
        expected_auto_flags = method_def.get('auto_flags', [])
        
        # Check if auto_flags are present
        for flag in expected_auto_flags:
            if flag not in edge_flags:
                # Warning, not error (flags might be added manually later)
                print(f"⚠ [{edge_id}] Missing expected flag '{flag}' for {evidence_method}")
        
        # Validate known flags
        known_flags = self.policy.get('edge_flags', {}).keys()
        for flag in edge_flags:
            if flag not in known_flags:
                errors.append(f"Unknown edge flag: '{flag}'")
        
        return len(errors) == 0, errors
    
    def validate_edge(
        self,
        edge: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate single edge record.
        
        Args:
            edge: Edge record to validate
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        edge_id = edge.get('edge_id', 'UNKNOWN')
        
        # Only validate edge records
        record_kind = edge.get('record_kind')
        if record_kind != 'edge':
            return True, []
        
        # Validate evidence method and fields
        is_valid, method_errors = self.validate_evidence_method(edge)
        if not is_valid:
            errors.extend([f"[{edge_id}] {e}" for e in method_errors])
        
        # Validate edge flags
        is_valid, flag_errors = self.validate_edge_flags(edge)
        if not is_valid:
            errors.extend([f"[{edge_id}] {e}" for e in flag_errors])
        
        # Check auto-quarantine
        should_quarantine, reason = self.check_auto_quarantine(edge)
        if should_quarantine:
            current_status = edge.get('status')
            if current_status != 'quarantined':
                print(f"⚠ [{edge_id}] Should be quarantined: {reason}")
                # Don't add to errors - just warning
        
        return len(errors) == 0, errors
    
    def validate_registry(
        self,
        registry: Dict[str, Any]
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate all edges in registry.
        
        Args:
            registry: Full registry to validate
            
        Returns:
            (all_valid, list_of_errors, statistics)
        """
        errors = []
        stats = {
            'total_edges': 0,
            'by_method': {},
            'by_confidence': {'high': 0, 'medium': 0, 'low': 0},
            'quarantined': 0,
            'missing_evidence': 0,
        }
        
        records = registry.get('records', [])
        edges = [r for r in records if r.get('record_kind') == 'edge']
        stats['total_edges'] = len(edges)
        
        print(f"\n✓ Validating {len(edges)} edges against evidence policy...")
        
        for edge in edges:
            # Collect statistics
            evidence_method = edge.get('evidence_method', 'unknown')
            stats['by_method'][evidence_method] = stats['by_method'].get(evidence_method, 0) + 1
            
            confidence = edge.get('confidence', 0.0)
            if confidence >= 0.8:
                stats['by_confidence']['high'] += 1
            elif confidence >= 0.5:
                stats['by_confidence']['medium'] += 1
            else:
                stats['by_confidence']['low'] += 1
            
            if edge.get('status') == 'quarantined':
                stats['quarantined'] += 1
            
            if not edge.get('evidence_locator'):
                stats['missing_evidence'] += 1
            
            # Validate
            is_valid, edge_errors = self.validate_edge(edge)
            if not is_valid:
                errors.extend(edge_errors)
        
        if errors:
            print(f"✗ Edge evidence violations found: {len(errors)}")
            for error in errors[:10]:  # Show first 10
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        else:
            print(f"✓ All edges meet evidence requirements")
        
        return len(errors) == 0, errors, stats


def main():
    """CLI entry point for edge evidence validation."""
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validate_edge_evidence.py <registry.json>")
        sys.exit(1)
    
    registry_path = sys.argv[1]
    
    print(f"Validating registry: {registry_path}")
    print("=" * 60)
    
    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # Validate
    validator = EdgeEvidenceValidator()
    is_valid, errors, stats = validator.validate_registry(registry)
    
    print("\n" + "=" * 60)
    print(f"Edge Statistics:")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  By method:")
    for method, count in stats['by_method'].items():
        print(f"    {method}: {count}")
    print(f"  By confidence:")
    print(f"    High (≥0.8): {stats['by_confidence']['high']}")
    print(f"    Medium (0.5-0.79): {stats['by_confidence']['medium']}")
    print(f"    Low (<0.5): {stats['by_confidence']['low']}")
    print(f"  Quarantined: {stats['quarantined']}")
    print(f"  Missing evidence: {stats['missing_evidence']}")
    
    print("\n" + "=" * 60)
    if is_valid:
        print("✓ PASS: All edges meet evidence requirements")
        sys.exit(0)
    else:
        print(f"✗ FAIL: {len(errors)} edge evidence violations")
        sys.exit(1)


if __name__ == '__main__':
    main()

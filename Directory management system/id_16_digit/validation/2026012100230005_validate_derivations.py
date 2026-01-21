"""
doc_id: 2026012100230005
title: Derivation Validator
version: 1.0
date: 2026-01-21T00:23:14Z
purpose: Validate computed fields match their formulas
"""

import yaml
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone


class DerivationValidator:
    """Validates computed fields against DERIVATIONS.yaml formulas."""
    
    def __init__(self, derivations_path: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize validator with derivations.
        
        Args:
            derivations_path: Path to DERIVATIONS.yaml (auto-detects if None)
            config_path: Path to IDENTITY_CONFIG.yaml for lookups
        """
        if derivations_path is None:
            derivations_path = self._find_derivations_file()
        
        self.derivations_path = Path(derivations_path)
        self.derivations = self._load_derivations()
        
        # Load config for lookups
        self.config = self._load_config(config_path) if config_path else {}
        
        self.mismatches = []
        
    def _find_derivations_file(self) -> str:
        """Auto-detect DERIVATIONS.yaml location."""
        candidates = [
            Path("contracts/2026012100230002_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml"),
            Path("../contracts/2026012100230002_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml"),
            Path("contracts/UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml"),
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        
        raise FileNotFoundError(
            "Could not find DERIVATIONS.yaml. "
            "Expected at: contracts/2026012100230002_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml"
        )
    
    def _load_derivations(self) -> Dict[str, Any]:
        """Load derivations from YAML file."""
        with open(self.derivations_path, 'r', encoding='utf-8') as f:
            derivations = yaml.safe_load(f)
        
        print(f"✓ Loaded derivations from {self.derivations_path}")
        print(f"  Derivations version: {derivations.get('derivations_version')}")
        print(f"  Derivations defined: {len(derivations.get('derivations', []))}")
        
        return derivations
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load IDENTITY_CONFIG.yaml for lookups."""
        if not Path(config_path).exists():
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    # =============================================================================
    # FORMULA DSL IMPLEMENTATION
    # =============================================================================
    
    def BASENAME(self, path: str) -> str:
        """Extract filename from path."""
        if not path:
            return ""
        return os.path.basename(path)
    
    def DIRNAME(self, path: str) -> str:
        """Extract directory from path, root = '.'"""
        if not path:
            return "."
        dirname = os.path.dirname(path)
        if not dirname or dirname == "/":
            return "."
        return dirname.replace("\\", "/")
    
    def EXTENSION(self, filename: str) -> str:
        """Extract lowercase extension without dot."""
        if not filename:
            return ""
        ext = Path(filename).suffix
        if not ext:
            return ""
        return ext[1:].lower()  # Remove leading dot and lowercase
    
    def UPPER(self, text: str) -> str:
        """Convert to uppercase."""
        return text.upper() if text else ""
    
    def LOWER(self, text: str) -> str:
        """Convert to lowercase."""
        return text.lower() if text else ""
    
    def ADD_SECONDS(self, utc_ts: str, seconds: int) -> str:
        """Add seconds to ISO 8601 timestamp."""
        if not utc_ts:
            return ""
        try:
            dt = datetime.fromisoformat(utc_ts.replace('Z', '+00:00'))
            from datetime import timedelta
            new_dt = dt + timedelta(seconds=seconds)
            return new_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception as e:
            return f"ERROR: {e}"
    
    def EXTRACT_16_DIGIT_PREFIX(self, filename: str) -> str:
        """Extract 16-digit prefix from filename."""
        if not filename:
            return ""
        match = re.match(r'^(\d{16})_', filename)
        if match:
            return match.group(1)
        return ""
    
    def LOOKUP_CONFIG(self, map_name: str, key: str, default: str) -> str:
        """Lookup value in config map."""
        config_map = self.config.get(map_name, {})
        return config_map.get(key, default)
    
    def NOW_UTC(self) -> str:
        """Current UTC timestamp (tool-only)."""
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # =============================================================================
    # DERIVATION EVALUATION
    # =============================================================================
    
    def compute_field(self, derivation: Dict[str, Any], record: Dict[str, Any]) -> Any:
        """
        Compute field value using formula.
        
        Args:
            derivation: Derivation definition
            record: Record with input values
            
        Returns:
            Computed value
        """
        formula = derivation['formula']
        column_name = derivation['column_name']
        
        try:
            # Simple formula parser (safe, no eval)
            if formula.startswith('BASENAME('):
                input_field = formula[9:-1]  # Extract field name
                return self.BASENAME(record.get(input_field, ""))
            
            elif formula.startswith('DIRNAME('):
                input_field = formula[8:-1]
                return self.DIRNAME(record.get(input_field, ""))
            
            elif formula == "DIRNAME(relative_path) OR '.'":
                result = self.DIRNAME(record.get('relative_path', ""))
                return result if result else "."
            
            elif formula.startswith('EXTENSION('):
                input_field = formula[10:-1]
                return self.EXTENSION(record.get(input_field, ""))
            
            elif formula.startswith('UPPER('):
                input_field = formula[6:-1]
                return self.UPPER(record.get(input_field, ""))
            
            elif formula.startswith('EXTRACT_16_DIGIT_PREFIX('):
                input_field = formula[24:-1]
                return self.EXTRACT_16_DIGIT_PREFIX(record.get(input_field, ""))
            
            elif formula.startswith('LOOKUP_CONFIG('):
                # Parse LOOKUP_CONFIG('map_name', key_field, 'default')
                parts = formula[14:-1].split(',')
                map_name = parts[0].strip().strip("'\"")
                key_field = parts[1].strip()
                default = parts[2].strip().strip("'\"")
                key_value = record.get(key_field, "")
                return self.LOOKUP_CONFIG(map_name, key_value, default)
            
            elif formula.startswith('ADD_SECONDS('):
                # Parse ADD_SECONDS(created_utc, ttl_seconds)
                parts = formula[12:-1].split(',')
                ts_field = parts[0].strip()
                seconds_field = parts[1].strip()
                ts_value = record.get(ts_field, "")
                seconds_value = record.get(seconds_field, 0)
                return self.ADD_SECONDS(ts_value, int(seconds_value))
            
            elif formula == "NOW_UTC()":
                return self.NOW_UTC()
            
            else:
                return f"UNKNOWN_FORMULA: {formula}"
        
        except Exception as e:
            return f"ERROR: {e}"
    
    def applies_to_record(self, derivation: Dict[str, Any], record: Dict[str, Any]) -> bool:
        """Check if derivation applies to this record."""
        applies_when = derivation.get('applies_when', {})
        
        for field, expected in applies_when.items():
            if field == 'ttl_seconds' and expected == 'present':
                if 'ttl_seconds' not in record or record['ttl_seconds'] is None:
                    return False
            elif isinstance(expected, list):
                if record.get(field) not in expected:
                    return False
            else:
                if record.get(field) != expected:
                    return False
        
        return True
    
    def validate_field(
        self,
        record: Dict[str, Any],
        column: str
    ) -> Tuple[bool, Optional[str], Any, Any]:
        """
        Validate single computed field.
        
        Args:
            record: Record to validate
            column: Column name
            
        Returns:
            (is_valid, error_message, actual_value, expected_value)
        """
        # Find derivation for this column
        derivation = None
        for deriv in self.derivations['derivations']:
            if deriv['column_name'] == column:
                if self.applies_to_record(deriv, record):
                    derivation = deriv
                    break
        
        if not derivation:
            # No derivation found (not a computed field or doesn't apply)
            return True, None, None, None
        
        # Compute expected value
        expected = self.compute_field(derivation, record)
        actual = record.get(column)
        
        # Compare
        if actual != expected:
            record_id = record.get('record_id', 'UNKNOWN')
            return False, f"Mismatch in {column}: actual='{actual}', expected='{expected}'", actual, expected
        
        return True, None, actual, expected
    
    def validate_record(
        self,
        record: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate all computed fields in record.
        
        Args:
            record: Record to validate
            
        Returns:
            (all_valid, list_of_errors)
        """
        errors = []
        
        # Check each derivation
        for derivation in self.derivations['derivations']:
            column = derivation['column_name']
            
            if not self.applies_to_record(derivation, record):
                continue
            
            is_valid, error, actual, expected = self.validate_field(record, column)
            if not is_valid:
                record_id = record.get('record_id', 'UNKNOWN')
                errors.append(f"[{record_id}] {error}")
        
        return len(errors) == 0, errors
    
    def validate_registry(
        self,
        registry: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate entire registry against derivations.
        
        Args:
            registry: Full registry to validate
            
        Returns:
            (all_valid, list_of_errors)
        """
        errors = []
        
        records = registry.get('records', [])
        print(f"\n✓ Validating {len(records)} records against derivations...")
        
        for record in records:
            is_valid, record_errors = self.validate_record(record)
            if not is_valid:
                errors.extend(record_errors)
        
        if errors:
            print(f"✗ Derivation mismatches found: {len(errors)}")
            for error in errors[:10]:  # Show first 10
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more")
        else:
            print(f"✓ All computed fields match their formulas")
        
        return len(errors) == 0, errors
    
    def recompute_field(self, record: Dict[str, Any], column: str) -> Any:
        """Recompute single field value."""
        for derivation in self.derivations['derivations']:
            if derivation['column_name'] == column:
                if self.applies_to_record(derivation, record):
                    return self.compute_field(derivation, record)
        return None
    
    def recompute_all_fields(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Recompute all computed fields in record."""
        for derivation in self.derivations['derivations']:
            if self.applies_to_record(derivation, record):
                column = derivation['column_name']
                record[column] = self.compute_field(derivation, record)
        return record


def main():
    """CLI entry point for derivation validation."""
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validate_derivations.py <registry.json> [--config identity_config.yaml]")
        sys.exit(1)
    
    registry_path = sys.argv[1]
    config_path = None
    
    if len(sys.argv) > 3 and sys.argv[2] == '--config':
        config_path = sys.argv[3]
    
    print(f"Validating registry: {registry_path}")
    print("=" * 60)
    
    # Load registry
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # Validate
    validator = DerivationValidator(config_path=config_path)
    is_valid, errors = validator.validate_registry(registry)
    
    print("\n" + "=" * 60)
    if is_valid:
        print("✓ PASS: All computed fields match formulas")
        sys.exit(0)
    else:
        print(f"✗ FAIL: {len(errors)} derivation mismatches")
        sys.exit(1)


if __name__ == '__main__':
    main()

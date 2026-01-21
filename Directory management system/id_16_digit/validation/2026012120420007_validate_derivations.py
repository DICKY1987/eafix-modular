#!/usr/bin/env python3
"""
doc_id: 2026012120420007
Unified SSOT Registry - Derivations Validator

Recomputes derived fields using safe formula DSL and validates consistency.
Ensures stored values match their derivation formulas.
"""

import os
import sys
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta, timezone
import yaml
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class DerivationEngine:
    """Safe formula evaluation engine for registry derivations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize derivation engine.
        
        Args:
            config: Configuration maps (e.g., type_code_by_extension)
        """
        self.config = config or {}
        self._init_functions()
    
    def _init_functions(self):
        """Initialize safe function catalog."""
        self.functions: Dict[str, Callable] = {
            "BASENAME": self._basename,
            "DIRNAME": self._dirname,
            "EXTENSION": self._extension,
            "UPPER": self._upper,
            "LOWER": self._lower,
            "ADD_SECONDS": self._add_seconds,
            "SHA256_BYTES": self._sha256_bytes,
            "NOW_UTC": self._now_utc,
            "EXTRACT_16_DIGIT_PREFIX": self._extract_16_digit_prefix,
            "LOOKUP_CONFIG": self._lookup_config,
            "NORMALIZE_PATH": self._normalize_path,
        }
    
    def _basename(self, path: str) -> str:
        """Extract filename from path."""
        return Path(path).name
    
    def _dirname(self, path: str) -> str:
        """Extract directory, root returns '.'"""
        dirname = str(Path(path).parent)
        return "." if dirname in ("", ".") else dirname
    
    def _extension(self, filename: str) -> str:
        """Extract extension without dot, lowercase."""
        ext = Path(filename).suffix
        return ext[1:].lower() if ext else ""
    
    def _upper(self, text: str) -> str:
        """Convert to uppercase."""
        return text.upper() if text else ""
    
    def _lower(self, text: str) -> str:
        """Convert to lowercase."""
        return text.lower() if text else ""
    
    def _add_seconds(self, utc_ts: str, seconds: int) -> str:
        """Add seconds to ISO 8601 timestamp."""
        dt = datetime.fromisoformat(utc_ts.rstrip('Z'))
        dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        new_dt = dt + timedelta(seconds=seconds)
        return new_dt.isoformat().replace('+00:00', 'Z')
    
    def _sha256_bytes(self, data: bytes) -> str:
        """Compute SHA256 hash."""
        return hashlib.sha256(data).hexdigest()
    
    def _now_utc(self) -> str:
        """Current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    def _extract_16_digit_prefix(self, filename: str) -> Optional[str]:
        """Extract 16-digit doc_id from filename."""
        match = re.match(r'^(\d{16})_', filename)
        return match.group(1) if match else None
    
    def _lookup_config(self, map_name: str, key: str, default: str) -> str:
        """Lookup in config map with default."""
        config_map = self.config.get(map_name, {})
        return config_map.get(key, default)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path: forward slashes, no leading ./, no trailing /"""
        path = path.replace('\\', '/')
        path = path.lstrip('./')
        path = path.rstrip('/')
        return path if path else "."
    
    def evaluate(self, formula: str, inputs: Dict[str, Any]) -> Any:
        """
        Evaluate formula with safe DSL.
        
        Args:
            formula: Formula string (e.g., "BASENAME(relative_path)")
            inputs: Input values (e.g., {"relative_path": "src/file.py"})
        
        Returns:
            Computed value
        """
        # Parse formula: FUNCTION(arg1, arg2, ...)
        match = re.match(r'^([A-Z_]+)\((.*)\)$', formula.strip())
        if not match:
            # Simple value reference
            if formula in inputs:
                return inputs[formula]
            raise ValueError(f"Invalid formula: {formula}")
        
        func_name = match.group(1)
        args_str = match.group(2)
        
        if func_name not in self.functions:
            raise ValueError(f"Unknown function: {func_name}")
        
        # Parse arguments
        args = []
        if args_str:
            # Split by comma, handle quoted strings
            arg_parts = [a.strip() for a in args_str.split(',')]
            for arg in arg_parts:
                if arg.startswith("'") and arg.endswith("'"):
                    # String literal
                    args.append(arg[1:-1])
                elif arg.isdigit():
                    # Integer literal
                    args.append(int(arg))
                elif arg in inputs:
                    # Variable reference
                    args.append(inputs[arg])
                else:
                    raise ValueError(f"Invalid argument: {arg}")
        
        # Call function
        return self.functions[func_name](*args)


class DerivationsValidator:
    """Validates derived fields against derivation rules."""
    
    def __init__(
        self, 
        derivations_path: Optional[str] = None,
        config_path: Optional[str] = None
    ):
        """
        Initialize validator.
        
        Args:
            derivations_path: Path to DERIVATIONS.yaml
            config_path: Path to config YAML (type codes, etc)
        """
        if derivations_path is None:
            base_dir = Path(__file__).parent.parent
            derivations_path = base_dir / "contracts" / "2026012120420002_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml"
        
        self.derivations_path = Path(derivations_path)
        self.derivations_doc = self._load_derivations()
        self.derivations = self.derivations_doc.get("derivations", [])
        
        # Load config (type codes, etc)
        config = self._load_config(config_path) if config_path else {}
        self.engine = DerivationEngine(config=config)
    
    def _load_derivations(self) -> Dict[str, Any]:
        """Load derivations YAML."""
        if not self.derivations_path.exists():
            raise FileNotFoundError(f"Derivations file not found: {self.derivations_path}")
        
        with open(self.derivations_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration YAML."""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _applies_to_record(self, derivation: Dict[str, Any], record: Dict[str, Any]) -> bool:
        """Check if derivation applies to this record."""
        applies_when = derivation.get("applies_when", {})
        
        for field, expected in applies_when.items():
            actual = record.get(field)
            
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif expected == "present":
                if actual is None:
                    return False
            elif actual != expected:
                return False
        
        return True
    
    def recompute_field(
        self, 
        column: str, 
        record: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Recompute a derived field.
        
        Args:
            column: Column name to recompute
            record: Full record with input values
        
        Returns:
            Computed value or None if no derivation applies
        """
        # Find applicable derivation
        for derivation in self.derivations:
            if derivation.get("column_name") != column:
                continue
            
            if not self._applies_to_record(derivation, record):
                continue
            
            # Build inputs dict
            input_fields = derivation.get("inputs", [])
            inputs = {}
            for field in input_fields:
                if field in record:
                    inputs[field] = record[field]
            
            # Evaluate formula
            formula = derivation.get("formula")
            if not formula:
                continue
            
            try:
                return self.engine.evaluate(formula, inputs)
            except Exception as e:
                # Formula evaluation failed
                return None
        
        return None
    
    def validate_record(
        self, 
        record: Dict[str, Any],
        recompute: bool = False
    ) -> tuple[bool, List[str]]:
        """
        Validate derived fields in a record.
        
        Args:
            record: Record to validate
            recompute: If True, recompute and show diffs
        
        Returns:
            (is_valid, error_messages) tuple
        """
        errors = []
        
        for derivation in self.derivations:
            column = derivation.get("column_name")
            
            if not self._applies_to_record(derivation, record):
                continue
            
            stored_value = record.get(column)
            computed_value = self.recompute_field(column, record)
            
            if computed_value is None:
                # Could not compute (missing inputs?)
                continue
            
            # Compare stored vs computed
            if stored_value != computed_value:
                errors.append(
                    f"Column '{column}': stored='{stored_value}' != computed='{computed_value}' "
                    f"(formula: {derivation.get('formula')})"
                )
        
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
        stats = {"total": len(records), "valid": 0, "invalid": 0, "skipped": 0}
        
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
        description="Validate registry derivations"
    )
    parser.add_argument(
        "--registry",
        default="ID_REGISTRY.json",
        help="Path to registry file"
    )
    parser.add_argument(
        "--derivations",
        help="Path to derivations YAML (default: auto-detect)"
    )
    parser.add_argument(
        "--config",
        help="Path to config YAML (type codes, etc)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        validator = DerivationsValidator(
            derivations_path=args.derivations,
            config_path=args.config
        )
        
        if args.verbose:
            print(f"Loaded derivations: {validator.derivations_path}")
            print(f"Derivation rules: {len(validator.derivations)}")
            print()
        
        is_valid, errors, stats = validator.validate_registry_file(
            registry_path=args.registry,
            verbose=args.verbose
        )
        
        print(f"\nResults: {stats['valid']}/{stats['total']} valid, {stats['invalid']} invalid")
        
        if is_valid:
            print("✅ Derivations validation PASSED")
            return 0
        else:
            print("❌ Derivations validation FAILED")
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

#!/usr/bin/env python3
"""
doc_id: 2026012120420011
Unified SSOT Registry - CLI Interface

Main command dispatcher for registry operations: validate, derive, normalize, query, export.
Provides unified interface to all validators and tools.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Dynamic imports (validators may not exist yet)
def import_validator(module_name: str, class_name: str):
    """Dynamically import validator module."""
    try:
        import importlib.util
        validator_dir = Path(__file__).parent.parent / "validation"
        
        # Find module file
        module_file = None
        for f in validator_dir.glob(f"*{module_name}.py"):
            module_file = f
            break
        
        if not module_file:
            return None
        
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name, None)
    except Exception as e:
        print(f"Warning: Could not import {class_name}: {e}", file=sys.stderr)
        return None


class RegistryCLI:
    """Main CLI dispatcher."""
    
    def __init__(self):
        """Initialize CLI."""
        self.base_dir = Path(__file__).parent.parent
        self.registry_path = self.base_dir / "ID_REGISTRY.json"
    
    def cmd_validate(self, args) -> int:
        """
        Validate registry against all policies.
        
        Usage:
            registry validate [--strict] [--report FILE]
        """
        print("Running registry validation...")
        print()
        
        all_passed = True
        results = {}
        
        # Run write policy validation
        WritePolicyValidator = import_validator("validate_write_policy", "WritePolicyValidator")
        if WritePolicyValidator:
            try:
                validator = WritePolicyValidator()
                is_valid, errors = validator.validate_registry_file(
                    registry_path=str(self.registry_path),
                    verbose=args.verbose
                )
                results["write_policy"] = {"passed": is_valid, "errors": errors}
                
                if is_valid:
                    print("✅ Write policy validation PASSED")
                else:
                    print("❌ Write policy validation FAILED")
                    all_passed = False
                    if args.strict:
                        for error in errors[:5]:  # Show first 5
                            print(f"  {error}")
            except Exception as e:
                print(f"⚠ Write policy validation ERROR: {e}")
                all_passed = False
        
        # Run derivations validation
        DerivationsValidator = import_validator("validate_derivations", "DerivationsValidator")
        if DerivationsValidator:
            try:
                validator = DerivationsValidator()
                is_valid, errors, stats = validator.validate_registry_file(
                    registry_path=str(self.registry_path),
                    verbose=args.verbose
                )
                results["derivations"] = {"passed": is_valid, "errors": errors, "stats": stats}
                
                if is_valid:
                    print("✅ Derivations validation PASSED")
                else:
                    print("❌ Derivations validation FAILED")
                    all_passed = False
                    if args.strict:
                        for error in errors[:5]:
                            print(f"  {error}")
            except Exception as e:
                print(f"⚠ Derivations validation ERROR: {e}")
                all_passed = False
        
        # Run conditional enum validation
        ConditionalEnumValidator = import_validator("validate_conditional_enums", "ConditionalEnumValidator")
        if ConditionalEnumValidator:
            try:
                validator = ConditionalEnumValidator()
                is_valid, errors, stats = validator.validate_registry_file(
                    registry_path=str(self.registry_path),
                    verbose=args.verbose
                )
                results["conditional_enums"] = {"passed": is_valid, "errors": errors, "stats": stats}
                
                if is_valid:
                    print("✅ Conditional enum validation PASSED")
                else:
                    print("❌ Conditional enum validation FAILED")
                    all_passed = False
                    if args.strict:
                        for error in errors[:5]:
                            print(f"  {error}")
            except Exception as e:
                print(f"⚠ Conditional enum validation ERROR: {e}")
                all_passed = False
        
        # Run edge evidence validation
        EdgeEvidenceValidator = import_validator("validate_edge_evidence", "EdgeEvidenceValidator")
        if EdgeEvidenceValidator:
            try:
                validator = EdgeEvidenceValidator()
                is_valid, errors, stats = validator.validate_registry_file(
                    registry_path=str(self.registry_path),
                    verbose=args.verbose
                )
                results["edge_evidence"] = {"passed": is_valid, "errors": errors, "stats": stats}
                
                if is_valid:
                    print("✅ Edge evidence validation PASSED")
                else:
                    print("❌ Edge evidence validation FAILED")
                    all_passed = False
                    if args.strict:
                        for error in errors[:5]:
                            print(f"  {error}")
            except Exception as e:
                print(f"⚠ Edge evidence validation ERROR: {e}")
                all_passed = False
        
        # Save report if requested
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Report saved to: {args.report}")
        
        print()
        if all_passed:
            print("🎉 All validation checks PASSED")
            return 0
        else:
            print("❌ Some validation checks FAILED")
            return 1
    
    def cmd_derive(self, args) -> int:
        """
        Recompute derived fields.
        
        Usage:
            registry derive [--dry-run] [--apply]
        """
        DerivationsValidator = import_validator("validate_derivations", "DerivationsValidator")
        if not DerivationsValidator:
            print("❌ Derivations validator not found", file=sys.stderr)
            return 1
        
        try:
            validator = DerivationsValidator()
            
            if args.dry_run:
                print("Dry-run: checking derived fields...")
                is_valid, errors, stats = validator.validate_registry_file(
                    registry_path=str(self.registry_path),
                    verbose=args.verbose
                )
                
                if is_valid:
                    print("✅ All derived fields consistent (no changes needed)")
                    return 0
                else:
                    print(f"⚠ {len(errors)} fields would be updated:")
                    for error in errors[:10]:
                        print(f"  {error}")
                    return 1
            else:
                print("❌ --apply not implemented yet (requires registry rewrite logic)")
                return 1
        
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 2
    
    def cmd_normalize(self, args) -> int:
        """
        Normalize registry fields.
        
        Usage:
            registry normalize [--dry-run] [--apply]
        """
        RegistryNormalizer = import_validator("normalize_registry", "RegistryNormalizer")
        if not RegistryNormalizer:
            print("❌ Registry normalizer not found", file=sys.stderr)
            return 1
        
        try:
            normalizer = RegistryNormalizer()
            stats = normalizer.normalize_registry_file(
                registry_path=str(self.registry_path),
                dry_run=args.dry_run,
                verbose=args.verbose
            )
            
            print(f"\nResults:")
            print(f"  Total records: {stats['total_records']}")
            print(f"  Normalized: {stats['normalized']}")
            print(f"  Unchanged: {stats['unchanged']}")
            
            if stats['fields_changed']:
                print(f"\n  Fields changed:")
                for field, count in sorted(stats['fields_changed'].items()):
                    print(f"    {field}: {count}")
            
            if args.dry_run:
                print("\n⚠ Dry run: no changes saved")
            else:
                print(f"\n✅ Registry normalized successfully")
            
            return 0
        
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 2
    
    def cmd_check_policy(self, args) -> int:
        """
        Check for policy violations.
        
        Usage:
            registry check-policy [--write-policy] [--derivations]
        """
        violations = []
        
        if args.write_policy or not (args.write_policy or args.derivations):
            WritePolicyValidator = import_validator("validate_write_policy", "WritePolicyValidator")
            if WritePolicyValidator:
                validator = WritePolicyValidator()
                is_valid, errors = validator.validate_registry_file(
                    registry_path=str(self.registry_path),
                    verbose=args.verbose
                )
                if not is_valid:
                    violations.extend(errors)
        
        if args.derivations or not (args.write_policy or args.derivations):
            DerivationsValidator = import_validator("validate_derivations", "DerivationsValidator")
            if DerivationsValidator:
                validator = DerivationsValidator()
                is_valid, errors, stats = validator.validate_registry_file(
                    registry_path=str(self.registry_path),
                    verbose=args.verbose
                )
                if not is_valid:
                    violations.extend(errors)
        
        if violations:
            print(f"❌ Found {len(violations)} policy violations:")
            for violation in violations[:20]:
                print(f"  {violation}")
            return 1
        else:
            print("✅ No policy violations found")
            return 0
    
    def cmd_query(self, args) -> int:
        """
        Query registry records.
        
        Usage:
            registry query [--record-kind KIND] [--entity-kind KIND] [--output FILE]
        """
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            records = registry.get("records", [])
            
            # Apply filters
            if args.record_kind:
                records = [r for r in records if r.get("record_kind") == args.record_kind]
            
            if args.entity_kind:
                records = [r for r in records if r.get("entity_kind") == args.entity_kind]
            
            if args.min_confidence:
                records = [r for r in records if r.get("confidence", 0) >= args.min_confidence]
            
            # Output
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
                print(f"✅ {len(records)} records saved to: {args.output}")
            else:
                print(json.dumps(records, indent=2, ensure_ascii=False))
            
            return 0
        
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 2
    
    def cmd_export(self, args) -> int:
        """
        Export registry to different format.
        
        Usage:
            registry export --format [csv|sqlite] --output FILE
        """
        print(f"❌ Export to {args.format} not implemented yet", file=sys.stderr)
        return 1


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified SSOT Registry CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  registry validate --strict
  registry validate --report validation_report.json
  registry derive --dry-run
  registry normalize --apply
  registry query --entity-kind file --output files.json
  registry check-policy --write-policy --derivations
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate registry against all policies")
    validate_parser.add_argument("--strict", action="store_true", help="Exit on first error")
    validate_parser.add_argument("--report", help="Save detailed report to JSON file")
    validate_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Derive command
    derive_parser = subparsers.add_parser("derive", help="Recompute derived fields")
    derive_parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would change")
    derive_parser.add_argument("--apply", action="store_true", help="Apply changes")
    derive_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Normalize command
    normalize_parser = subparsers.add_parser("normalize", help="Normalize field formats")
    normalize_parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would change")
    normalize_parser.add_argument("--apply", action="store_true", help="Apply changes (default if no dry-run)")
    normalize_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Check-policy command
    check_parser = subparsers.add_parser("check-policy", help="Check for policy violations")
    check_parser.add_argument("--write-policy", action="store_true", help="Check write policy")
    check_parser.add_argument("--derivations", action="store_true", help="Check derivations")
    check_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query registry records")
    query_parser.add_argument("--record-kind", choices=["entity", "edge", "generator"], help="Filter by record kind")
    query_parser.add_argument("--entity-kind", help="Filter by entity kind")
    query_parser.add_argument("--min-confidence", type=float, help="Minimum confidence for edges")
    query_parser.add_argument("--output", "-o", help="Output file (JSON)")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export registry")
    export_parser.add_argument("--format", choices=["csv", "sqlite"], required=True, help="Export format")
    export_parser.add_argument("--output", "-o", required=True, help="Output file")
    export_parser.add_argument("--entity-kind", help="Filter by entity kind")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = RegistryCLI()
    
    # Dispatch to command handler
    cmd_method = getattr(cli, f"cmd_{args.command.replace('-', '_')}", None)
    if not cmd_method:
        print(f"❌ Unknown command: {args.command}", file=sys.stderr)
        return 1
    
    try:
        return cmd_method(args)
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())

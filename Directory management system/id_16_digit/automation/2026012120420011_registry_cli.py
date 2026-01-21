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
            registry validate [--strict] [--report FILE] [--include-module] [--include-process]
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
        
        # Run module assignment validation (if enabled)
        if args.include_module:
            ModuleAssignmentValidator = import_validator("validate_module_assignment", "ModuleAssignmentValidator")
            if ModuleAssignmentValidator:
                try:
                    validator = ModuleAssignmentValidator()
                    base_dir = str(self.registry_path.parent)
                    is_valid, errors, stats = validator.validate_registry_file(
                        registry_path=str(self.registry_path),
                        base_dir=base_dir,
                        verbose=args.verbose
                    )
                    results["module_assignment"] = {"passed": is_valid, "errors": errors, "stats": stats}
                    
                    if is_valid:
                        print("✅ Module assignment validation PASSED")
                    else:
                        print("❌ Module assignment validation FAILED")
                        all_passed = False
                        if args.strict:
                            for error in errors[:5]:
                                print(f"  {error}")
                except Exception as e:
                    print(f"⚠ Module assignment validation ERROR: {e}")
                    all_passed = False
        
        # Run process validation (if enabled)
        if args.include_process:
            ProcessValidator = import_validator("validate_process", "ProcessValidator")
            if ProcessValidator:
                try:
                    validator = ProcessValidator()
                    is_valid, errors, stats = validator.validate_registry_file(
                        registry_path=str(self.registry_path),
                        verbose=args.verbose
                    )
                    results["process_validation"] = {"passed": is_valid, "errors": errors, "stats": stats}
                    
                    if is_valid:
                        print("✅ Process validation PASSED")
                    else:
                        print("❌ Process validation FAILED")
                        all_passed = False
                        if args.strict:
                            for error in errors[:5]:
                                print(f"  {error}")
                except Exception as e:
                    print(f"⚠ Process validation ERROR: {e}")
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
            registry derive [--dry-run] [--apply] [--timestamped-backup] [--report FILE]
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
                    print(f"⚠ {len(errors)} field(s) would be updated:")
                    for error in errors[:10]:
                        print(f"  {error}")
                    if len(errors) > 10:
                        print(f"  ... and {len(errors) - 10} more")
                    return 0
            
            elif args.apply:
                print("Applying derivations to registry...")
                apply_stats = validator.apply_derivations(
                    registry_path=str(self.registry_path),
                    backup_suffix=".backup",
                    create_timestamped_backup=args.timestamped_backup,
                    verbose=args.verbose
                )
                
                print(f"\nResults:")
                print(f"  Total records: {apply_stats['total_records']}")
                print(f"  Records updated: {apply_stats['records_updated']}")
                
                if apply_stats['fields_updated']:
                    print(f"\n  Fields updated:")
                    for field, count in sorted(apply_stats['fields_updated'].items()):
                        print(f"    {field}: {count}")
                
                # Save report if requested
                if args.report:
                    with open(args.report, 'w', encoding='utf-8') as f:
                        json.dump(apply_stats, f, indent=2, ensure_ascii=False)
                    print(f"\n📄 Report saved to: {args.report}")
                
                if apply_stats['records_updated'] > 0:
                    print(f"\n✅ Registry updated successfully")
                else:
                    print(f"\n✅ No changes needed (already consistent)")
                
                return 0
            else:
                print("❌ Error: must specify --dry-run or --apply", file=sys.stderr)
                return 1
        
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            import traceback
            if args.verbose:
                traceback.print_exc()
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
            registry export --format [csv|sqlite] --output FILE [--entity-kind KIND]
        """
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            records = registry.get("records", [])
            
            # Apply filters
            if args.entity_kind:
                records = [r for r in records if r.get("entity_kind") == args.entity_kind]
            
            if args.record_kind:
                records = [r for r in records if r.get("record_kind") == args.record_kind]
            
            if args.format == "csv":
                return self._export_csv(records, args.output, args.verbose)
            elif args.format == "sqlite":
                return self._export_sqlite(records, registry, args.output, args.verbose)
            else:
                print(f"❌ Unknown format: {args.format}", file=sys.stderr)
                return 1
        
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            import traceback
            if args.verbose:
                traceback.print_exc()
            return 2
    
    def _export_csv(self, records: List[Dict[str, Any]], output_path: str, verbose: bool = False) -> int:
        """Export records to CSV format."""
        import csv
        
        if not records:
            print("⚠ No records to export", file=sys.stderr)
            return 1
        
        # Determine authoritative column order
        # Get all unique columns across records (deterministic order)
        all_columns = set()
        for record in records:
            all_columns.update(record.keys())
        
        # Define canonical ordering (priority columns first, rest alphabetical)
        priority_columns = [
            "record_id", "record_kind", "doc_id", "entity_kind", 
            "filename", "relative_path", "extension", "type_code",
            "module_id", "status", "source_doc_id", "target_doc_id", 
            "edge_kind", "rel_type"
        ]
        
        # Build ordered column list
        columns = []
        for col in priority_columns:
            if col in all_columns:
                columns.append(col)
                all_columns.remove(col)
        
        # Add remaining columns alphabetically
        columns.extend(sorted(all_columns))
        
        if verbose:
            print(f"Exporting {len(records)} records to CSV...")
            print(f"Columns: {len(columns)}")
        
        # Write CSV with deterministic ordering
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            
            # Sort records for deterministic output (by record_kind, then record_id)
            sorted_records = sorted(records, key=lambda r: (r.get("record_kind", ""), r.get("record_id", "")))
            
            for record in sorted_records:
                # Serialize complex fields as JSON strings
                row = {}
                for col in columns:
                    value = record.get(col)
                    if value is None:
                        row[col] = ""
                    elif isinstance(value, (list, dict)):
                        row[col] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[col] = str(value)
                
                writer.writerow(row)
        
        print(f"✅ Exported {len(sorted_records)} records to: {output_path}")
        return 0
    
    def _export_sqlite(
        self, 
        records: List[Dict[str, Any]], 
        registry: Dict[str, Any],
        output_path: str, 
        verbose: bool = False
    ) -> int:
        """Export records to SQLite database."""
        import sqlite3
        
        if verbose:
            print(f"Exporting {len(records)} records to SQLite...")
        
        # Remove existing DB if present (full rebuild)
        if os.path.exists(output_path):
            os.unlink(output_path)
        
        conn = sqlite3.connect(output_path)
        cursor = conn.cursor()
        
        try:
            # Create meta table
            cursor.execute("""
                CREATE TABLE meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            meta = registry.get("meta", {})
            for key, value in meta.items():
                cursor.execute("INSERT INTO meta (key, value) VALUES (?, ?)", 
                             (key, json.dumps(value) if isinstance(value, (dict, list)) else str(value)))
            
            # Create entity_records table
            cursor.execute("""
                CREATE TABLE entity_records (
                    record_id TEXT PRIMARY KEY,
                    doc_id TEXT,
                    entity_kind TEXT,
                    filename TEXT,
                    relative_path TEXT,
                    extension TEXT,
                    type_code TEXT,
                    module_id TEXT,
                    status TEXT,
                    business_criticality TEXT,
                    file_size_bytes INTEGER,
                    line_count INTEGER,
                    sha256_checksum TEXT,
                    created_utc TEXT,
                    updated_utc TEXT,
                    primary_purpose TEXT,
                    notes TEXT,
                    semantic_tags TEXT,
                    quarantine_reason TEXT
                )
            """)
            
            # Create indexes for entity_records
            cursor.execute("CREATE INDEX idx_entity_doc_id ON entity_records(doc_id)")
            cursor.execute("CREATE INDEX idx_entity_kind ON entity_records(entity_kind)")
            cursor.execute("CREATE INDEX idx_entity_module ON entity_records(module_id)")
            cursor.execute("CREATE INDEX idx_entity_status ON entity_records(status)")
            
            # Create edge_records table
            cursor.execute("""
                CREATE TABLE edge_records (
                    record_id TEXT PRIMARY KEY,
                    source_doc_id TEXT,
                    target_doc_id TEXT,
                    edge_kind TEXT,
                    rel_type TEXT,
                    evidence_method TEXT,
                    evidence_locator TEXT,
                    confidence_score REAL,
                    status TEXT,
                    created_utc TEXT,
                    updated_utc TEXT,
                    notes TEXT
                )
            """)
            
            # Create indexes for edge_records
            cursor.execute("CREATE INDEX idx_edge_source ON edge_records(source_doc_id)")
            cursor.execute("CREATE INDEX idx_edge_target ON edge_records(target_doc_id)")
            cursor.execute("CREATE INDEX idx_edge_rel_type ON edge_records(rel_type)")
            cursor.execute("CREATE INDEX idx_edge_kind ON edge_records(edge_kind)")
            
            # Create generator_records table
            cursor.execute("""
                CREATE TABLE generator_records (
                    record_id TEXT PRIMARY KEY,
                    generator_kind TEXT,
                    output_doc_id TEXT,
                    input_doc_ids TEXT,
                    tool TEXT,
                    command TEXT,
                    status TEXT,
                    created_utc TEXT,
                    updated_utc TEXT,
                    notes TEXT
                )
            """)
            
            cursor.execute("CREATE INDEX idx_gen_output ON generator_records(output_doc_id)")
            
            # Insert records
            entity_count = 0
            edge_count = 0
            generator_count = 0
            
            for record in records:
                record_kind = record.get("record_kind")
                
                if record_kind == "entity":
                    cursor.execute("""
                        INSERT INTO entity_records VALUES (
                            :record_id, :doc_id, :entity_kind, :filename, :relative_path,
                            :extension, :type_code, :module_id, :status, :business_criticality,
                            :file_size_bytes, :line_count, :sha256_checksum, :created_utc, :updated_utc,
                            :primary_purpose, :notes, :semantic_tags, :quarantine_reason
                        )
                    """, {
                        "record_id": record.get("record_id"),
                        "doc_id": record.get("doc_id"),
                        "entity_kind": record.get("entity_kind"),
                        "filename": record.get("filename"),
                        "relative_path": record.get("relative_path"),
                        "extension": record.get("extension"),
                        "type_code": record.get("type_code"),
                        "module_id": record.get("module_id"),
                        "status": record.get("status"),
                        "business_criticality": record.get("business_criticality"),
                        "file_size_bytes": record.get("file_size_bytes"),
                        "line_count": record.get("line_count"),
                        "sha256_checksum": record.get("sha256_checksum"),
                        "created_utc": record.get("created_utc"),
                        "updated_utc": record.get("updated_utc"),
                        "primary_purpose": record.get("primary_purpose"),
                        "notes": record.get("notes"),
                        "semantic_tags": json.dumps(record.get("semantic_tags")) if record.get("semantic_tags") else None,
                        "quarantine_reason": record.get("quarantine_reason")
                    })
                    entity_count += 1
                
                elif record_kind == "edge":
                    cursor.execute("""
                        INSERT INTO edge_records VALUES (
                            :record_id, :source_doc_id, :target_doc_id, :edge_kind, :rel_type,
                            :evidence_method, :evidence_locator, :confidence_score, :status,
                            :created_utc, :updated_utc, :notes
                        )
                    """, {
                        "record_id": record.get("record_id"),
                        "source_doc_id": record.get("source_doc_id"),
                        "target_doc_id": record.get("target_doc_id"),
                        "edge_kind": record.get("edge_kind"),
                        "rel_type": record.get("rel_type"),
                        "evidence_method": record.get("evidence_method"),
                        "evidence_locator": record.get("evidence_locator"),
                        "confidence_score": record.get("confidence_score"),
                        "status": record.get("status"),
                        "created_utc": record.get("created_utc"),
                        "updated_utc": record.get("updated_utc"),
                        "notes": record.get("notes")
                    })
                    edge_count += 1
                
                elif record_kind == "generator":
                    cursor.execute("""
                        INSERT INTO generator_records VALUES (
                            :record_id, :generator_kind, :output_doc_id, :input_doc_ids,
                            :tool, :command, :status, :created_utc, :updated_utc, :notes
                        )
                    """, {
                        "record_id": record.get("record_id"),
                        "generator_kind": record.get("generator_kind"),
                        "output_doc_id": record.get("output_doc_id"),
                        "input_doc_ids": json.dumps(record.get("input_doc_ids")) if record.get("input_doc_ids") else None,
                        "tool": record.get("tool"),
                        "command": record.get("command"),
                        "status": record.get("status"),
                        "created_utc": record.get("created_utc"),
                        "updated_utc": record.get("updated_utc"),
                        "notes": record.get("notes")
                    })
                    generator_count += 1
            
            conn.commit()
            
            if verbose:
                print(f"  Entity records: {entity_count}")
                print(f"  Edge records: {edge_count}")
                print(f"  Generator records: {generator_count}")
            
            print(f"✅ Exported to SQLite: {output_path}")
            print(f"   Entities: {entity_count}, Edges: {edge_count}, Generators: {generator_count}")
            return 0
        
        except Exception as e:
            conn.rollback()
            raise
        
        finally:
            conn.close()


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
    validate_parser.add_argument("--include-module", action="store_true", help="Include module assignment validation")
    validate_parser.add_argument("--include-process", action="store_true", help="Include process validation")
    validate_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    # Derive command
    derive_parser = subparsers.add_parser("derive", help="Recompute derived fields")
    derive_parser.add_argument("--dry-run", "-n", action="store_true", help="Show what would change")
    derive_parser.add_argument("--apply", action="store_true", help="Apply changes to registry")
    derive_parser.add_argument("--timestamped-backup", action="store_true", help="Create timestamped backup file")
    derive_parser.add_argument("--report", help="Save detailed change report to JSON file")
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
    export_parser.add_argument("--record-kind", choices=["entity", "edge", "generator"], help="Filter by record kind")
    export_parser.add_argument("--entity-kind", help="Filter by entity kind")
    export_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
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

#!/usr/bin/env python3
# doc_id: 2026011822590002
"""
Direct Registry Integration - Process existing scan CSV and allocate IDs.

Usage:
    python 2026011822590002_register_and_allocate.py --csv ../scan_output/file_scan_20260118_170030.csv --allocate --limit 100
"""

import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime
from typing import Tuple
import json

sys.path.insert(0, str(Path(__file__).parent))

from core.registry_store import RegistryStore
from monitoring.audit_logger import AuditLogger
from validation.validate_uniqueness import UniquenessValidator
from validation.validate_identity_sync import SyncValidator


def register_existing_ids(registry: RegistryStore, audit_logger: AuditLogger, csv_path: str, run_id: str) -> Tuple[int, int]:
    """Register IDs that already exist in filenames."""
    print("\n" + "=" * 70)
    print("STEP 1: Registering Existing IDs from Filenames")
    print("=" * 70 + "\n")
    
    registered = 0
    skipped = 0
    
    # Handle encoding issues
    try:
        f = open(csv_path, 'r', encoding='utf-8', errors='replace')
    except:
        f = open(csv_path, 'r', encoding='latin-1')
    
    try:
        reader = csv.DictReader(f)
        
        for row in reader:
            doc_id = row.get('doc_id', '').strip()
            file_path = row.get('relative_path', '').strip()
            type_code = row.get('type_code', '').strip()
            ns_code = row.get('ns_code', '').strip()
            
            if not doc_id or doc_id == 'UNASSIGNED':
                continue
            
            try:
                action, _ = registry.register_existing_id(
                    doc_id=doc_id,
                    file_path=file_path,
                    allocated_by='import_from_scan',
                    metadata={
                        'imported': True,
                        'type_code': type_code,
                        'ns_code': ns_code
                    }
                )
                
                audit_logger.log_registry_operation(
                    operation='import_existing',
                    details={'doc_id': doc_id, 'file_path': file_path},
                    run_id=run_id
                )
                
                if action == "registered":
                    registered += 1
                    if registered <= 10:
                        print(f"  ✓ {doc_id} → {file_path}")
                else:
                    skipped += 1
            
            except Exception as e:
                print(f"  ✗ Failed {doc_id}: {e}")
    
    finally:
        f.close()
    
    if registered > 10:
        print(f"  ... and {registered - 10} more")
    
    print(f"\n✓ Registered: {registered} | Skipped (already in registry): {skipped}")
    return registered, skipped


def allocate_new_ids(registry: RegistryStore, audit_logger: AuditLogger, csv_path: str, run_id: str, limit: int = None) -> Tuple[int, int]:
    """Allocate new IDs to files that need them."""
    print("\n" + "=" * 70)
    print(f"STEP 2: Allocating New IDs{f' (limit: {limit})' if limit else ''}")
    print("=" * 70 + "\n")
    
    allocated = 0
    failed = 0
    
    # Handle encoding issues
    try:
        f = open(csv_path, 'r', encoding='utf-8', errors='replace')
    except:
        f = open(csv_path, 'r', encoding='latin-1')
    
    try:
        reader = csv.DictReader(f)
        
        for row in reader:
            if limit and allocated >= limit:
                break
            
            doc_id = row.get('doc_id', '').strip()
            file_path = row.get('relative_path', '').strip()
            type_code = row.get('type_code', '').strip()
            ns_code = row.get('ns_code', '').strip()
            needs_id = row.get('needs_id', '').strip().lower() == 'true'
            
            if not needs_id or (doc_id and doc_id != 'UNASSIGNED'):
                continue
            
            if not all([file_path, type_code, ns_code]):
                continue
            
            try:
                existing = registry.get_active_allocation_by_path(file_path)
                if existing:
                    continue

                new_id = registry.allocate_id(
                    ns_code=ns_code,
                    type_code=type_code,
                    file_path=file_path,
                    allocated_by='auto_allocate',
                    metadata={'scan_run': run_id}
                )
                
                audit_logger.log_allocation(
                    doc_id=new_id,
                    file_path=file_path,
                    ns_code=ns_code,
                    type_code=type_code,
                    allocated_by='auto_allocate',
                    run_id=run_id
                )
                
                allocated += 1
                if allocated <= 10:
                    print(f"  ✓ {new_id} → {file_path}")
            
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"  ✗ {file_path}: {e}")
    
    finally:
        f.close()
    
    if allocated > 10:
        print(f"  ... and {allocated - 10} more")
    
    print(f"\n✓ Allocated: {allocated} | Failed: {failed}")
    return allocated, failed


def validate(registry_path: str, csv_path: str):
    """Run validation checks."""
    print("\n" + "=" * 70)
    print("STEP 3: Validation")
    print("=" * 70 + "\n")
    
    print("Checking uniqueness...")
    validator = UniquenessValidator(csv_path, registry_path)
    is_unique = validator.validate()
    
    if is_unique:
        print("  ✓ All IDs unique")
    else:
        print(f"  ✗ {len(validator.errors)} errors")
        for err in validator.errors[:3]:
            print(f"    - {err['type']}: {err['message']}")
    
    print("\nChecking sync...")
    sync_val = SyncValidator(csv_path, registry_path)
    sync_val.validate_sync()
    
    if not sync_val.issues:
        print("  ✓ Filesystem and registry synced")
    else:
        print(f"  ✗ {len(sync_val.issues)} issues")
        for issue in sync_val.issues[:3]:
            print(f"    - {issue['type']}: {issue['message']}")
    
    return is_unique and len(sync_val.issues) == 0


def generate_report(registry: RegistryStore, csv_path: str, run_id: str):
    """Generate final report."""
    print("\n" + "=" * 70)
    print("STEP 4: Report")
    print("=" * 70 + "\n")
    
    stats = registry.get_stats()
    
    # Calculate coverage
    total_files = 0
    files_with_ids = 0
    
    try:
        f = open(csv_path, 'r', encoding='utf-8', errors='replace')
    except:
        f = open(csv_path, 'r', encoding='latin-1')
    
    try:
        reader = csv.DictReader(f)
        for row in reader:
            total_files += 1
            doc_id = row.get('doc_id', '').strip()
            if doc_id and doc_id != 'UNASSIGNED':
                files_with_ids += 1
    finally:
        f.close()
    
    coverage = (files_with_ids / total_files * 100) if total_files > 0 else 0
    
    print("Registry Statistics:")
    print(f"  Total allocations:    {stats['total_allocations']}")
    print(f"  Active:               {stats['active_allocations']}")
    print(f"  Deprecated:           {stats['deprecated_allocations']}")
    print(f"  Registry version:     {stats['registry_version']}")
    
    print("\nCoverage:")
    print(f"  Total files scanned:  {total_files}")
    print(f"  Files with IDs:       {files_with_ids}")
    print(f"  Coverage:             {coverage:.1f}%")
    
    # Save report
    report = {
        'run_id': run_id,
        'timestamp': datetime.now().isoformat(),
        'stats': stats,
        'coverage': {
            'total_files': total_files,
            'files_with_ids': files_with_ids,
            'coverage_pct': coverage
        }
    }
    
    report_path = Path('registry') / f'report_{run_id}.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Report saved: {report_path}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Register and allocate IDs from scan CSV')
    
    parser.add_argument('--csv', required=True, help='Path to scan CSV file')
    parser.add_argument('--allocate', action='store_true', help='Allocate new IDs')
    parser.add_argument('--limit', type=int, help='Limit new allocations')
    parser.add_argument('--registry', default='registry/ID_REGISTRY.json', help='Registry path')
    parser.add_argument('--audit-log', default='registry/identity_audit_log.jsonl', help='Audit log path')
    
    args = parser.parse_args()
    
    run_id = f"register_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print("\n" + "=" * 70)
    print("EAFIX IDENTITY SYSTEM - REGISTRATION & ALLOCATION")
    print("=" * 70)
    print(f"Run ID:   {run_id}")
    print(f"CSV:      {args.csv}")
    print(f"Registry: {args.registry}")
    print("=" * 70)
    
    registry = RegistryStore(args.registry)
    audit_logger = AuditLogger(args.audit_log)
    
    # Step 1: Register existing
    reg_count, skip_count = register_existing_ids(registry, audit_logger, args.csv, run_id)
    
    # Step 2: Allocate new (if requested)
    if args.allocate:
        alloc_count, fail_count = allocate_new_ids(registry, audit_logger, args.csv, run_id, args.limit)
    else:
        print("\n⏭️  Skipping allocation (--allocate not specified)")
        alloc_count = 0
        fail_count = 0
    
    # Step 3: Validate
    is_valid = validate(args.registry, args.csv)
    
    # Step 4: Report
    report = generate_report(registry, args.csv, run_id)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"{'✓ COMPLETE' if is_valid else '⚠️  COMPLETE WITH WARNINGS'}")
    print("=" * 70)
    print(f"Registered existing:  {reg_count}")
    print(f"Allocated new:        {alloc_count}")
    print(f"Coverage:             {report['coverage']['coverage_pct']:.1f}%")
    print(f"Validation:           {'PASS' if is_valid else 'WARNINGS'}")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()

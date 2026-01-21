#!/usr/bin/env python3
# doc_id: 2026011822590001
"""
Scanner with Registry Integration - Full repository ID allocation workflow.

This script:
1. Runs Enhanced File Scanner v2.py
2. Allocates IDs to files that need them
3. Updates the registry
4. Validates uniqueness and sync
5. Generates comprehensive reports

Usage:
    python 2026011822590001_scanner_with_registry.py --scan --allocate
    python 2026011822590001_scanner_with_registry.py --validate-only
    python 2026011822590001_scanner_with_registry.py --full-workflow
"""

import sys
import csv
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import json

# Add DIR_OPT/id_16_digit to path
sys.path.insert(0, str(Path(__file__).parent))

from core.registry_store import RegistryStore
from monitoring.audit_logger import AuditLogger
from validation.validate_uniqueness import UniquenessValidator
from validation.validate_identity_sync import SyncValidator


class ScannerRegistryIntegration:
    """Integrates Enhanced File Scanner with Registry System."""

    def __init__(
        self,
        scanner_path: str,
        registry_path: str,
        audit_log_path: str,
        repo_root: str
    ):
        """
        Initialize integration.
        
        Args:
            scanner_path: Path to Enhanced File Scanner v2.py
            registry_path: Path to ID_REGISTRY.json
            audit_log_path: Path to audit log
            repo_root: Repository root directory
        """
        self.scanner_path = Path(scanner_path)
        self.registry_path = Path(registry_path)
        self.audit_log_path = Path(audit_log_path)
        self.repo_root = Path(repo_root)
        
        self.registry = RegistryStore(str(registry_path))
        self.audit_logger = AuditLogger(str(audit_log_path))
        
        self.scan_csv_path = None
        self.run_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def run_scanner(self) -> Path:
        """
        Run Enhanced File Scanner v2.py.
        
        Returns:
            Path to generated CSV file
        """
        print("=" * 70)
        print("STEP 1: Running Enhanced File Scanner")
        print("=" * 70)
        print()
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.scanner_path)],
                cwd=str(self.scanner_path.parent),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                print(f"Scanner failed with exit code {result.returncode}")
                print(f"Error: {result.stderr}")
                return None
            
            # Find the generated CSV
            scan_output_dir = self.scanner_path.parent / "scan_output"
            csv_files = sorted(scan_output_dir.glob("file_scan_*.csv"))
            
            if csv_files:
                self.scan_csv_path = csv_files[-1]  # Most recent
                print(f"✓ Scanner complete: {self.scan_csv_path}")
                return self.scan_csv_path
            else:
                print("✗ No scan CSV generated")
                return None
        
        except subprocess.TimeoutExpired:
            print("✗ Scanner timeout (exceeded 5 minutes)")
            return None
        except Exception as e:
            print(f"✗ Scanner error: {e}")
            return None

    def register_existing_ids(self, csv_path: Path) -> Tuple[int, int]:
        """
        Register IDs that already exist in filenames.
        
        Args:
            csv_path: Path to scan CSV
            
        Returns:
            Tuple of (registered_count, skipped_count)
        """
        print()
        print("=" * 70)
        print("STEP 2: Registering Existing IDs")
        print("=" * 70)
        print()
        
        registered = 0
        skipped = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                doc_id = row.get('doc_id', '').strip()
                file_path = row.get('relative_path', '').strip()
                type_code = row.get('type_code', '').strip()
                ns_code = row.get('ns_code', '').strip()
                
                # Skip if no ID or unassigned
                if not doc_id or doc_id == 'UNASSIGNED':
                    continue
                
                try:
                    action, _ = self.registry.register_existing_id(
                        doc_id=doc_id,
                        file_path=file_path,
                        allocated_by='scanner_import',
                        metadata={
                            'imported_from_filename': True,
                            'type_code': type_code,
                            'ns_code': ns_code
                        }
                    )
                    
                    # Log registration
                    self.audit_logger.log_registry_operation(
                        operation='import_existing_id',
                        details={
                            'doc_id': doc_id,
                            'file_path': file_path,
                            'type_code': type_code,
                            'ns_code': ns_code
                        },
                        run_id=self.run_id
                    )
                    
                    if action == "registered":
                        registered += 1
                        if registered <= 10:
                            print(f"  ✓ Registered {doc_id} → {file_path}")
                    else:
                        skipped += 1
                
                except Exception as e:
                    print(f"  ✗ Failed to register {doc_id}: {e}")
        
        if registered > 10:
            print(f"  ... and {registered - 10} more")
        
        print()
        print(f"Summary: {registered} registered, {skipped} already in registry")
        
        return registered, skipped

    def allocate_new_ids(self, csv_path: Path, limit: int = None) -> Tuple[int, int]:
        """
        Allocate IDs to files that need them.
        
        Args:
            csv_path: Path to scan CSV
            limit: Optional limit on allocations
            
        Returns:
            Tuple of (allocated_count, failed_count)
        """
        print()
        print("=" * 70)
        print("STEP 3: Allocating New IDs")
        print("=" * 70)
        print()
        
        allocated = 0
        failed = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if limit and allocated >= limit:
                    break
                
                doc_id = row.get('doc_id', '').strip()
                file_path = row.get('relative_path', '').strip()
                type_code = row.get('type_code', '').strip()
                ns_code = row.get('ns_code', '').strip()
                needs_id = row.get('needs_id', '').strip().lower() == 'true'
                
                # Skip if already has ID or doesn't need one
                if not needs_id or (doc_id and doc_id != 'UNASSIGNED'):
                    continue
                
                # Skip if missing required fields
                if not all([file_path, type_code, ns_code]):
                    continue
                
                # Allocate ID
                try:
                    existing = self.registry.get_active_allocation_by_path(file_path)
                    if existing:
                        continue

                    new_id = self.registry.allocate_id(
                        ns_code=ns_code,
                        type_code=type_code,
                        file_path=file_path,
                        allocated_by='scanner_auto_allocate',
                        metadata={
                            'allocated_via': 'scanner_integration',
                            'scan_run_id': self.run_id
                        }
                    )
                    
                    # Log allocation
                    self.audit_logger.log_allocation(
                        doc_id=new_id,
                        file_path=file_path,
                        ns_code=ns_code,
                        type_code=type_code,
                        allocated_by='scanner_auto_allocate',
                        run_id=self.run_id
                    )
                    
                    allocated += 1
                    if allocated <= 10:
                        print(f"  ✓ Allocated {new_id} → {file_path}")
                
                except Exception as e:
                    failed += 1
                    if failed <= 5:
                        print(f"  ✗ Failed: {file_path} - {e}")
        
        if allocated > 10:
            print(f"  ... and {allocated - 10} more")
        
        print()
        print(f"Summary: {allocated} allocated, {failed} failed")
        
        return allocated, failed

    def validate_registry(self, csv_path: Path) -> bool:
        """
        Validate registry uniqueness and sync.
        
        Args:
            csv_path: Path to scan CSV
            
        Returns:
            True if all validations pass
        """
        print()
        print("=" * 70)
        print("STEP 4: Validating Registry")
        print("=" * 70)
        print()
        
        # Uniqueness validation
        print("Checking uniqueness...")
        uniqueness_validator = UniquenessValidator(str(csv_path), str(self.registry_path))
        is_unique = uniqueness_validator.validate()
        
        if is_unique:
            print("  ✓ All IDs are unique")
        else:
            print(f"  ✗ Found {len(uniqueness_validator.errors)} uniqueness errors")
            for error in uniqueness_validator.errors[:5]:
                print(f"    - {error['type']}: {error['message']}")
        
        # Sync validation
        print()
        print("Checking sync...")
        sync_validator = SyncValidator(str(csv_path), str(self.registry_path))
        sync_validator.validate_sync()
        
        if not sync_validator.issues:
            print("  ✓ Filesystem and registry are synced")
        else:
            print(f"  ✗ Found {len(sync_validator.issues)} sync issues")
            for issue in sync_validator.issues[:5]:
                print(f"    - {issue['type']}: {issue['message']}")
        
        print()
        return is_unique and len(sync_validator.issues) == 0

    def generate_report(self) -> Dict:
        """
        Generate comprehensive report.
        
        Returns:
            Report dictionary
        """
        print()
        print("=" * 70)
        print("STEP 5: Generating Report")
        print("=" * 70)
        print()
        
        stats = self.registry.get_stats()
        
        report = {
            'run_id': self.run_id,
            'timestamp': datetime.now().isoformat(),
            'registry_stats': stats,
            'scan_csv': str(self.scan_csv_path) if self.scan_csv_path else None
        }
        
        # Calculate coverage
        if self.scan_csv_path and self.scan_csv_path.exists():
            total_files = 0
            files_with_ids = 0
            
            with open(self.scan_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_files += 1
                    doc_id = row.get('doc_id', '').strip()
                    if doc_id and doc_id != 'UNASSIGNED':
                        files_with_ids += 1
            
            coverage = files_with_ids / total_files if total_files > 0 else 0
            report['coverage'] = {
                'total_files': total_files,
                'files_with_ids': files_with_ids,
                'coverage_percentage': coverage * 100
            }
        
        # Print report
        print("Registry Statistics:")
        print(f"  Total allocations:     {stats['total_allocations']}")
        print(f"  Active allocations:    {stats['active_allocations']}")
        print(f"  Deprecated:            {stats['deprecated_allocations']}")
        print(f"  Superseded:            {stats['superseded_allocations']}")
        print(f"  Registry version:      {stats['registry_version']}")
        
        if 'coverage' in report:
            print()
            print("Coverage:")
            print(f"  Total files:           {report['coverage']['total_files']}")
            print(f"  Files with IDs:        {report['coverage']['files_with_ids']}")
            print(f"  Coverage:              {report['coverage']['coverage_percentage']:.1f}%")
        
        # Save report
        report_path = self.registry_path.parent / f"scan_report_{self.run_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print()
        print(f"✓ Report saved: {report_path}")
        
        return report

    def run_full_workflow(self, allocate: bool = False, limit: int = None):
        """
        Run complete workflow: scan → register → allocate → validate → report.
        
        Args:
            allocate: Whether to allocate new IDs
            limit: Optional limit on new allocations
        """
        print()
        print("=" * 70)
        print("EAFIX IDENTITY SYSTEM - FULL REPOSITORY WORKFLOW")
        print("=" * 70)
        print(f"Run ID: {self.run_id}")
        print(f"Repository: {self.repo_root}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 70)
        
        # Step 1: Scan
        csv_path = self.run_scanner()
        if not csv_path:
            print()
            print("✗ Workflow aborted: Scanner failed")
            return
        
        # Step 2: Register existing IDs
        registered, skipped = self.register_existing_ids(csv_path)
        
        # Step 3: Allocate new IDs (if requested)
        if allocate:
            allocated, failed = self.allocate_new_ids(csv_path, limit)
        else:
            print()
            print("Skipping allocation (--allocate not specified)")
            allocated = 0
            failed = 0
        
        # Step 4: Validate
        is_valid = self.validate_registry(csv_path)
        
        # Step 5: Report
        report = self.generate_report()
        
        # Final summary
        print()
        print("=" * 70)
        print("WORKFLOW COMPLETE")
        print("=" * 70)
        print()
        print(f"Status: {'✓ SUCCESS' if is_valid else '✗ VALIDATION ERRORS'}")
        print(f"Registered existing: {registered}")
        print(f"Allocated new:       {allocated}")
        print(f"Failed:              {failed}")
        print(f"Registry version:    {report['registry_stats']['registry_version']}")
        
        if 'coverage' in report:
            print(f"Coverage:            {report['coverage']['coverage_percentage']:.1f}%")
        
        print()
        print("Files:")
        print(f"  Scan CSV:    {csv_path}")
        print(f"  Registry:    {self.registry_path}")
        print(f"  Audit log:   {self.audit_log_path}")
        print(f"  Report:      {self.registry_path.parent / f'scan_report_{self.run_id}.json'}")
        print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Scanner with Registry Integration - Full workflow automation'
    )
    
    parser.add_argument(
        '--full-workflow',
        action='store_true',
        help='Run complete workflow (scan + register + allocate + validate + report)'
    )
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Run scanner only'
    )
    parser.add_argument(
        '--register',
        action='store_true',
        help='Register existing IDs only'
    )
    parser.add_argument(
        '--allocate',
        action='store_true',
        help='Allocate new IDs'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate only'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of new allocations'
    )
    
    # Paths
    parser.add_argument(
        '--scanner',
        default='Enhanced File Scanner v2.py',
        help='Path to scanner script'
    )
    parser.add_argument(
        '--registry',
        default='registry/ID_REGISTRY.json',
        help='Registry path'
    )
    parser.add_argument(
        '--audit-log',
        default='registry/identity_audit_log.jsonl',
        help='Audit log path'
    )
    parser.add_argument(
        '--repo-root',
        default='..',
        help='Repository root'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    scanner_path = script_dir / args.scanner
    registry_path = script_dir / args.registry
    audit_log_path = script_dir / args.audit_log
    repo_root = script_dir / args.repo_root
    
    # Initialize integration
    integration = ScannerRegistryIntegration(
        scanner_path=str(scanner_path),
        registry_path=str(registry_path),
        audit_log_path=str(audit_log_path),
        repo_root=str(repo_root)
    )
    
    # Execute requested workflow
    if args.full_workflow or (not any([args.scan, args.register, args.validate])):
        # Default: full workflow
        integration.run_full_workflow(allocate=args.allocate, limit=args.limit)
    else:
        # Individual steps
        if args.scan:
            csv_path = integration.run_scanner()
            if csv_path:
                print(f"✓ Scan complete: {csv_path}")
        
        if args.register and integration.scan_csv_path:
            integration.register_existing_ids(integration.scan_csv_path)
        
        if args.allocate and integration.scan_csv_path:
            integration.allocate_new_ids(integration.scan_csv_path, args.limit)
        
        if args.validate and integration.scan_csv_path:
            integration.validate_registry(integration.scan_csv_path)


if __name__ == '__main__':
    main()

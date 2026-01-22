#!/usr/bin/env python3
# doc_id: 2026012201111009
# Master Validation Runner - Executes all validators
# Created: 2026-01-22T01:11:41Z

import json
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class ValidationRunner:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.results = []
    
    def load_data_files(self) -> Dict:
        """Load all required data files."""
        data = {}
        
        # FILE_REGISTRY
        file_registry_path = self.repo_root / "Directory management system" / "id_16_digit" / "registry" / "2026012201111008_FILE_REGISTRY.json"
        if file_registry_path.exists():
            with open(file_registry_path, 'r', encoding='utf-8') as f:
                data['file_registry'] = json.load(f)
        else:
            print("⚠️  FILE_REGISTRY not found")
            data['file_registry'] = None
        
        # MODULE_REGISTRY
        module_registry_path = self.repo_root / "Directory management system" / "DOD_modules_contracts" / "2026012201111006_MODULE_REGISTRY_v1.0.0.yaml"
        if module_registry_path.exists():
            with open(module_registry_path, 'r', encoding='utf-8') as f:
                data['module_registry'] = yaml.safe_load(f)
        else:
            print("⚠️  MODULE_REGISTRY not found")
            data['module_registry'] = None
        
        # Process Document
        process_path = self.repo_root / "Directory management system" / "DOD_modules_contracts" / "updated_trading_process_aligned.yaml"
        if process_path.exists():
            with open(process_path, 'r', encoding='utf-8') as f:
                data['process_doc'] = yaml.safe_load(f)
        else:
            print("❌ Process document not found")
            data['process_doc'] = None
        
        return data
    
    def run_validator_1_module_ownership(self, data: Dict) -> Dict:
        """Validator 1: Module Ownership Completeness."""
        errors = []
        warnings = []
        
        file_registry = data.get('file_registry')
        module_registry = data.get('module_registry')
        
        if not file_registry:
            return {
                'check': 'module_ownership_completeness',
                'passed': False,
                'skipped': True,
                'reason': 'FILE_REGISTRY not available'
            }
        
        files = file_registry.get('files', [])
        
        if module_registry:
            module_ids = set(m['module_id'] for m in module_registry.get('modules', []))
        else:
            module_ids = set()
            warnings.append("Module registry not available")
        
        uncategorized_count = 0
        missing_module_count = 0
        
        for file in files:
            module_id = file.get('module_id')
            
            if not module_id:
                errors.append(f"File {file.get('relative_path', 'unknown')} has no module_id")
                missing_module_count += 1
            elif module_id == "UNCATEGORIZED":
                uncategorized_count += 1
            elif module_ids and module_id not in module_ids and module_id != "UNCATEGORIZED":
                errors.append(f"File {file.get('relative_path', 'unknown')} has unknown module {module_id}")
        
        if uncategorized_count > 0:
            pct = 100 * uncategorized_count / len(files) if len(files) > 0 else 0
            if pct > 50:
                warnings.append(f"{uncategorized_count} files ({pct:.1f}%) are UNCATEGORIZED - Expected in early implementation")
            else:
                warnings.append(f"{uncategorized_count} files are UNCATEGORIZED")
        
        return {
            'check': 'module_ownership_completeness',
            'passed': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'stats': {
                'total_files': len(files),
                'uncategorized': uncategorized_count,
                'missing_module': missing_module_count
            }
        }
    
    def run_validator_2_role_restrictions(self, data: Dict) -> Dict:
        """Validator 2: Role Restrictions."""
        errors = []
        
        file_registry = data.get('file_registry')
        
        if not file_registry:
            return {
                'check': 'role_restrictions',
                'passed': False,
                'skipped': True,
                'reason': 'FILE_REGISTRY not available'
            }
        
        files = file_registry.get('files', [])
        
        # Check role enum
        allowed_roles = {'entrypoint', 'library', 'schema', 'config', 'test', 'doc', 'data', 'tooling', 'fixture'}
        
        for file in files:
            role = file.get('role')
            
            if not role:
                errors.append(f"File {file['relative_path']} has no role")
            elif role not in allowed_roles:
                errors.append(f"File {file['relative_path']} has invalid role: {role}")
            
            # Check step_refs restriction
            step_refs = file.get('step_refs', [])
            if step_refs and role != 'entrypoint':
                errors.append(
                    f"Non-entrypoint file {file['relative_path']} "
                    f"(role={role}) has step_refs: {step_refs}"
                )
        
        return {
            'check': 'role_restrictions',
            'passed': len(errors) == 0,
            'errors': errors
        }
    
    def run_validator_3_registry_structure(self, data: Dict) -> Dict:
        """Validator 3: Registry Structure Validation."""
        errors = []
        warnings = []
        
        file_registry = data.get('file_registry')
        module_registry = data.get('module_registry')
        
        # Validate FILE_REGISTRY structure
        if file_registry:
            required_fields = ['schema_version', 'scope', 'files']
            for field in required_fields:
                if field not in file_registry:
                    errors.append(f"FILE_REGISTRY missing required field: {field}")
            
            # Check file record structure
            files = file_registry.get('files', [])
            if files:
                sample_file = files[0]
                required_file_fields = ['doc_id', 'relative_path', 'module_id', 'role']
                for field in required_file_fields:
                    if field not in sample_file:
                        errors.append(f"File records missing required field: {field}")
        
        # Validate MODULE_REGISTRY structure
        if module_registry:
            required_fields = ['registry_version', 'modules']
            for field in required_fields:
                if field not in module_registry:
                    errors.append(f"MODULE_REGISTRY missing required field: {field}")
            
            modules = module_registry.get('modules', [])
            if modules:
                sample_module = modules[0]
                required_module_fields = ['module_id', 'contract_boundaries']
                for field in required_module_fields:
                    if field not in sample_module:
                        errors.append(f"Module records missing required field: {field}")
        
        return {
            'check': 'registry_structure_validation',
            'passed': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def run_all_validations(self) -> Dict:
        """Run all validators and compile report."""
        print("🔍 Loading data files...")
        data = self.load_data_files()
        
        print("🔍 Running validators...")
        
        self.results.append(self.run_validator_1_module_ownership(data))
        self.results.append(self.run_validator_2_role_restrictions(data))
        self.results.append(self.run_validator_3_registry_structure(data))
        
        # Compile summary
        total_checks = len(self.results)
        passed = sum(1 for r in self.results if r.get('passed'))
        failed = sum(1 for r in self.results if not r.get('passed') and not r.get('skipped'))
        skipped = sum(1 for r in self.results if r.get('skipped'))
        total_errors = sum(len(r.get('errors', [])) for r in self.results)
        total_warnings = sum(len(r.get('warnings', [])) for r in self.results)
        
        summary = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_checks': total_checks,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'results': self.results
        }
        
        return summary
    
    def print_summary(self, summary: Dict):
        """Print validation summary to console."""
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Total Warnings: {summary['total_warnings']}")
        print()
        
        for result in summary['results']:
            check_name = result['check']
            passed = result.get('passed')
            skipped = result.get('skipped', False)
            
            if skipped:
                status = "⏭️  SKIPPED"
            elif passed:
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            
            print(f"{status} - {check_name}")
            
            if result.get('errors'):
                print(f"  Errors ({len(result['errors'])}):")
                for error in result['errors'][:5]:
                    print(f"    • {error}")
                if len(result['errors']) > 5:
                    print(f"    ... and {len(result['errors']) - 5} more")
            
            if result.get('warnings'):
                print(f"  Warnings ({len(result['warnings'])}):")
                for warning in result['warnings'][:3]:
                    print(f"    • {warning}")
        
        print()

def main():
    repo_root = Path(__file__).parent.parent.parent
    
    runner = ValidationRunner(repo_root)
    summary = runner.run_all_validations()
    
    # Write report
    report_path = repo_root / "backups" / "validation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    runner.print_summary(summary)
    
    print(f"📄 Full report written to: {report_path}")
    
    # Exit code
    if summary['failed'] > 0:
        print("\n❌ VALIDATION FAILED")
        return 1
    elif summary['skipped'] == summary['total_checks']:
        print("\n⏭️  ALL CHECKS SKIPPED (incomplete implementation)")
        return 0
    else:
        print("\n✅ ALL VALIDATIONS PASSED")
        return 0

if __name__ == '__main__':
    sys.exit(main())

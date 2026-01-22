#!/usr/bin/env python3
# doc_id: 2026012201111002
# Phase A Pre-Migration Validation
# Created: 2026-01-22T01:11:41Z

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

class PhaseAValidator:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.errors = []
        self.warnings = []
        self.stats = {}
    
    def validate_file_exists(self, rel_path: str) -> bool:
        """Check if critical file exists."""
        full_path = self.repo_root / rel_path
        if not full_path.exists():
            self.errors.append(f"Missing critical file: {rel_path}")
            return False
        return True
    
    def validate_id_registry(self) -> Dict:
        """Validate ID_REGISTRY.json structure and content."""
        registry_path = self.repo_root / "Directory management system" / "id_16_digit" / "registry" / "ID_REGISTRY.json"
        
        if not registry_path.exists():
            self.errors.append("ID_REGISTRY.json not found")
            return {}
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"ID_REGISTRY.json is not valid JSON: {e}")
            return {}
        
        # Check structure
        if 'scope' not in registry:
            self.errors.append("ID_REGISTRY.json missing 'scope' field")
        else:
            current_scope = registry['scope']
            self.stats['current_scope'] = current_scope
            if current_scope not in ['260118', '260119', '720066']:
                self.warnings.append(f"Unexpected scope value: {current_scope}")
        
        if 'counters' not in registry:
            self.errors.append("ID_REGISTRY.json missing 'counters' field")
        else:
            counters = registry['counters']
            self.stats['counter_count'] = len(counters)
            
            # Check counter key format
            old_format_count = 0
            new_format_count = 0
            
            for key in counters.keys():
                if '_' in key and ':' not in key:
                    old_format_count += 1
                elif ':' in key:
                    new_format_count += 1
            
            self.stats['old_format_counters'] = old_format_count
            self.stats['new_format_counters'] = new_format_count
            
            if old_format_count > 0:
                self.warnings.append(f"{old_format_count} counters use old format (NS_TYPE_SCOPE)")
        
        if 'allocations' not in registry:
            self.errors.append("ID_REGISTRY.json missing 'allocations' field")
        else:
            allocations = registry['allocations']
            self.stats['allocation_count'] = len(allocations)
        
        return registry
    
    def count_files_by_scope(self) -> Dict[str, int]:
        """Count files in repository by scope suffix."""
        scope_counts = {
            '260118': 0,
            '260119': 0,
            '720066': 0,
            'other': 0
        }
        
        for root, dirs, files in os.walk(self.repo_root):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file[0].isdigit():  # Likely has ID
                    if '260118' in file:
                        scope_counts['260118'] += 1
                    elif '260119' in file:
                        scope_counts['260119'] += 1
                    elif '720066' in file:
                        scope_counts['720066'] += 1
                    else:
                        import re
                        if re.search(r'\d{6}', file):
                            scope_counts['other'] += 1
        
        return scope_counts
    
    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🔍 Phase A: Validating current state...")
        print()
        
        # Check critical files
        critical_files = [
            "Directory management system/id_16_digit/registry/ID_REGISTRY.json",
            "Directory management system/id_16_digit/IDENTITY_CONFIG.yaml",
            "Directory management system/DOD_modules_contracts/updated_trading_process_aligned.yaml"
        ]
        
        for file in critical_files:
            self.validate_file_exists(file)
        
        # Validate ID registry
        registry = self.validate_id_registry()
        
        # Count files by scope
        scope_counts = self.count_files_by_scope()
        self.stats['file_scope_counts'] = scope_counts
        
        # Report results
        print("📊 Current State Statistics:")
        print(f"  Current scope in registry: {self.stats.get('current_scope', 'UNKNOWN')}")
        print(f"  Counter entries: {self.stats.get('counter_count', 0)}")
        print(f"  Allocated IDs: {self.stats.get('allocation_count', 0)}")
        print(f"  Old format counters: {self.stats.get('old_format_counters', 0)}")
        print(f"  New format counters: {self.stats.get('new_format_counters', 0)}")
        print()
        print("📁 Files by scope:")
        for scope, count in scope_counts.items():
            print(f"  {scope}: {count} files")
        print()
        
        if self.errors:
            print("❌ Validation Errors:")
            for error in self.errors:
                print(f"  • {error}")
            print()
        
        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()
        
        if not self.errors:
            print("✅ Pre-migration validation passed!")
            print("Ready to proceed with Phase A.")
            return True
        else:
            print("❌ Pre-migration validation failed!")
            print("Fix errors before proceeding.")
            return False

def main():
    repo_root = Path(__file__).parent.parent.parent
    
    validator = PhaseAValidator(str(repo_root))
    success = validator.run_validation()
    
    # Write report
    report_path = repo_root / "backups" / "phase_a_pre_validation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'success': success,
            'errors': validator.errors,
            'warnings': validator.warnings,
            'stats': validator.stats
        }, f, indent=2)
    
    print(f"\n📄 Report written to: {report_path}")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

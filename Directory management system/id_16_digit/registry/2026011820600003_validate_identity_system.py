#!/usr/bin/env python3
"""
doc_id: 2026011820600003
Validation Test Script for Identity System Implementation

Validates that Enhanced File Scanner v2.py correctly:
1. Loads IDENTITY_CONFIG.yaml
2. Derives type_code from extensions
3. Derives ns_code from paths
4. Outputs 26-column CSV
5. Populates all identity fields

Usage:
    python 2026011820600003_validate_identity_system.py [scan_csv_path]
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict

try:
    import yaml
except ImportError:
    yaml = None


def load_expected_scope() -> str:
    """Load expected scope from IDENTITY_CONFIG.yaml when available."""
    search_dir = Path(__file__).parent
    candidates = [search_dir / 'IDENTITY_CONFIG.yaml']
    candidates.extend(sorted(search_dir.glob('*_IDENTITY_CONFIG.yaml')))

    for candidate in candidates:
        if not candidate.exists():
            continue
        if yaml is None:
            break
        try:
            raw = yaml.safe_load(candidate.read_text(encoding='utf-8'))
        except Exception:
            continue
        if isinstance(raw, dict):
            scope = str(raw.get('scope', '')).strip()
            if scope:
                return scope

    return '260118'


def validate_csv_schema(csv_path):
    """Validate CSV has required 26 columns."""
    print("=" * 60)
    print("TEST 1: CSV Schema Validation")
    print("=" * 60)
    
    expected_columns = [
        'scan_id', 'scan_root', 'first_seen_utc',
        'relative_path', 'path', 'name', 'extension',
        'size_bytes', 'mtime_utc', 'created_time',
        'is_directory', 'mime_type', 'permissions', 'content_hash',
        'doc_id', 'has_id_prefix', 'current_id_prefix', 'needs_id',
        '0000000000000000_filename',
        'type_code', 'ns_code', 'scope',
        'planned_id', 'planned_rel_path',
        'error', 'error_kind'
    ]
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        actual_columns = reader.fieldnames
    
    if len(actual_columns) != 26:
        print(f"❌ FAIL: Expected 26 columns, got {len(actual_columns)}")
        return False
    
    missing = set(expected_columns) - set(actual_columns)
    extra = set(actual_columns) - set(expected_columns)
    
    if missing:
        print(f"❌ FAIL: Missing columns: {missing}")
        return False
    
    if extra:
        print(f"❌ FAIL: Extra columns: {extra}")
        return False
    
    print(f"✅ PASS: CSV has all 26 required columns")
    return True


def validate_type_derivation(csv_path):
    """Validate type_code derivation from extensions."""
    print("\n" + "=" * 60)
    print("TEST 2: Type Code Derivation")
    print("=" * 60)
    
    expected_mappings = {
        'py': '20',
        'md': '01',
        'txt': '02',
        'csv': '10',
        'json': '11',
        'yaml': '12',
        'yml': '12',
    }
    
    actual_mappings = defaultdict(set)
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['extension'] and row['type_code']:
                actual_mappings[row['extension']].add(row['type_code'])
    
    all_pass = True
    for ext, expected_code in expected_mappings.items():
        if ext in actual_mappings:
            actual_codes = actual_mappings[ext]
            if len(actual_codes) == 1 and expected_code in actual_codes:
                print(f"✅ PASS: .{ext} → type_code {expected_code}")
            else:
                print(f"❌ FAIL: .{ext} expected {expected_code}, got {actual_codes}")
                all_pass = False
        else:
            print(f"⚠️  SKIP: No .{ext} files found in scan")
    
    return all_pass


def validate_namespace_routing(csv_path):
    """Validate ns_code derivation from paths."""
    print("\n" + "=" * 60)
    print("TEST 3: Namespace Code Routing")
    print("=" * 60)
    
    expected_patterns = {
        'docs': '100',
        'data': '110',
        'scripts/python': '200',
        'reports': '420',
    }
    
    found_mappings = defaultdict(set)
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel_path = row['relative_path'].replace('\\', '/')
            if rel_path and row['ns_code']:
                for pattern in expected_patterns.keys():
                    if rel_path.startswith(f"{pattern}/"):
                        found_mappings[pattern].add(row['ns_code'])
    
    all_pass = True
    for pattern, expected_code in expected_patterns.items():
        if pattern in found_mappings:
            actual_codes = found_mappings[pattern]
            if expected_code in actual_codes:
                print(f"✅ PASS: {pattern}/**/* includes ns_code {expected_code}")
            else:
                print(f"❌ FAIL: {pattern}/**/* expected {expected_code}, got {actual_codes}")
                all_pass = False
        else:
            print(f"⚠️  SKIP: No {pattern}/**/* files found in scan")
    
    return all_pass


def validate_scope_consistency(csv_path):
    """Validate all rows have consistent scope."""
    print("\n" + "=" * 60)
    print("TEST 4: Scope Consistency")
    print("=" * 60)
    
    expected_scope = load_expected_scope()
    scopes = set()
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['scope']:
                scopes.add(row['scope'])
    
    if len(scopes) == 0:
        print("❌ FAIL: No scope values found")
        return False
    
    if len(scopes) > 1:
        print(f"❌ FAIL: Multiple scope values found: {scopes}")
        return False
    
    actual_scope = scopes.pop()
    if actual_scope == expected_scope:
        print(f"✅ PASS: All rows have scope = {expected_scope}")
        return True
    else:
        print(f"❌ FAIL: Expected scope {expected_scope}, got {actual_scope}")
        return False


def validate_id_detection(csv_path):
    """Validate ID prefix detection logic."""
    print("\n" + "=" * 60)
    print("TEST 5: ID Prefix Detection")
    print("=" * 60)
    
    with_id = 0
    without_id = 0
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['is_directory'] == 'True':
                continue
            
            if row['has_id_prefix'] == 'True':
                with_id += 1
                # Verify doc_id is populated
                if not row['doc_id'] or len(row['doc_id']) != 16:
                    print(f"❌ FAIL: File with has_id_prefix=True has invalid doc_id: {row['name']}")
                    return False
            else:
                without_id += 1
                # Verify needs_id is True
                if row['needs_id'] != 'True':
                    print(f"❌ FAIL: File without ID has needs_id=False: {row['name']}")
                    return False
    
    print(f"✅ PASS: {with_id} files with existing IDs detected")
    print(f"✅ PASS: {without_id} files needing IDs detected")
    return True


def validate_required_fields(csv_path):
    """Validate required fields are populated."""
    print("\n" + "=" * 60)
    print("TEST 6: Required Field Population")
    print("=" * 60)
    
    required_fields = ['scan_id', 'scan_root', 'first_seen_utc', 'type_code', 'ns_code', 'scope']
    
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        row_count = 0
        for row in reader:
            row_count += 1
            # Skip directories for type_code check
            if row['is_directory'] == 'True':
                continue
            for field in required_fields:
                if not row[field]:
                    print(f"❌ FAIL: Row {row_count} missing required field: {field}")
                    print(f"   File: {row['name']}")
                    return False
    
    print(f"✅ PASS: All {row_count} rows have required fields populated")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python 2026011820600003_validate_identity_system.py <csv_path>")
        print("\nSearching for latest scan CSV...")
        
        # Try to find latest CSV in scan_output
        scan_dir = Path(__file__).parent.parent / 'scan_output'
        if scan_dir.exists():
            csvs = list(scan_dir.glob('file_scan_*.csv'))
            if csvs:
                csv_path = max(csvs, key=lambda p: p.stat().st_mtime)
                print(f"Found: {csv_path}\n")
            else:
                print("❌ No CSV files found in scan_output/")
                sys.exit(1)
        else:
            print("❌ scan_output/ directory not found")
            sys.exit(1)
    else:
        csv_path = Path(sys.argv[1])
    
    if not csv_path.exists():
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)
    
    print(f"Validating: {csv_path}")
    print(f"File size: {csv_path.stat().st_size:,} bytes\n")
    
    tests = [
        ("CSV Schema", validate_csv_schema),
        ("Type Derivation", validate_type_derivation),
        ("Namespace Routing", validate_namespace_routing),
        ("Scope Consistency", validate_scope_consistency),
        ("ID Detection", validate_id_detection),
        ("Required Fields", validate_required_fields),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func(csv_path)
        except Exception as e:
            print(f"❌ FAIL: {test_name} raised exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)
    
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()

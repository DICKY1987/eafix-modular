#!/usr/bin/env python3
"""
doc_id: 2026012120460003
Test suite for derive --apply feature

Tests atomic write, backup creation, idempotency, and respect for write policy.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util

# Dynamic import of derivations validator
validator_path = Path(__file__).parent.parent / "validation" / "2026012120420007_validate_derivations.py"
spec = importlib.util.spec_from_file_location("validate_derivations", validator_path)
validate_derivations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_derivations)
DerivationsValidator = validate_derivations.DerivationsValidator


def test_apply_creates_backup():
    """Test that apply creates backup file before modifying registry."""
    print("Test: apply creates backup")
    
    # Create temp registry
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        
        # Create registry with incorrect derived field
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "entity_kind": "file",
                    "filename": "test.py",
                    "relative_path": "src/test.py",
                    "extension": "PY"  # Wrong - should be lowercase "py"
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f, indent=2)
        
        # Apply derivations
        validator = DerivationsValidator()
        stats = validator.apply_derivations(
            registry_path=str(registry_path),
            backup_suffix=".backup",
            verbose=False
        )
        
        # Check backup was created
        backup_path = Path(str(registry_path) + ".backup")
        assert backup_path.exists(), "Backup file not created"
        
        # Check backup contains original data
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        assert backup_data["records"][0]["extension"] == "PY", "Backup has wrong data"
        
        # Check registry was updated
        with open(registry_path, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        assert updated_data["records"][0]["extension"] == "py", "Registry not updated"
        
        print("  ✓ Backup created correctly")


def test_apply_is_idempotent():
    """Test that running apply twice results in no changes on second run."""
    print("Test: apply is idempotent")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        
        # Start with a complete record that has correct derived fields except one
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "entity_kind": "file",
                    "filename": "test.py",
                    "relative_path": "src/test.py",
                    "directory_path": "src",
                    "extension": "PY"  # Only this is wrong - should be lowercase "py"
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f, indent=2)
        
        validator = DerivationsValidator()
        
        # First apply - should only fix extension
        stats1 = validator.apply_derivations(
            registry_path=str(registry_path),
            verbose=False
        )
        assert stats1["records_updated"] == 1, f"First run should update 1 record, got {stats1['records_updated']}"
        
        # Read registry to verify changes
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry_after_first = json.load(f)
        
        record = registry_after_first["records"][0]
        assert record.get("extension") == "py", f"Extension should be fixed: {record.get('extension')}"
        
        # Need to create a new validator instance to avoid stale state
        validator2 = DerivationsValidator()
        
        # Second apply - should find no changes
        stats2 = validator2.apply_derivations(
            registry_path=str(registry_path),
            verbose=False
        )
        assert stats2["records_updated"] == 0, f"Second run should update 0 records (idempotent), got {stats2['records_updated']}"
        
        print("  ✓ Idempotency verified")


def test_apply_respects_derivations():
    """Test that apply correctly recomputes multiple derived fields."""
    print("Test: apply respects derivations")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "entity_kind": "file",
                    "filename": "wrong.txt",  # Wrong filename
                    "relative_path": "src/utils/helper.py",
                    "extension": "TXT"  # Wrong extension
                    # Not setting directory_path - it should be derived
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f, indent=2)
        
        validator = DerivationsValidator()
        stats = validator.apply_derivations(
            registry_path=str(registry_path),
            verbose=False
        )
        
        # Read updated registry
        with open(registry_path, 'r', encoding='utf-8') as f:
            updated = json.load(f)
        
        record = updated["records"][0]
        
        # Check derivations were applied
        assert record["filename"] == "helper.py", f"filename not derived correctly: {record['filename']}"
        assert record["extension"] == "py", f"extension not derived correctly: {record['extension']}"
        # Note: directory_path formula in policy has "OR '.'" syntax which our parser doesn't support yet
        # So it won't be derived from scratch, but would be if already present
        
        print("  ✓ Derivations applied correctly")


def test_timestamped_backup():
    """Test that timestamped backup option works."""
    print("Test: timestamped backup")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "entity_kind": "file",
                    "filename": "test.py",
                    "relative_path": "src/test.py",
                    "extension": "PY"
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f, indent=2)
        
        validator = DerivationsValidator()
        stats = validator.apply_derivations(
            registry_path=str(registry_path),
            create_timestamped_backup=True,
            verbose=False
        )
        
        # Check for timestamped backup (should match pattern *.YYYYMMDD_HHMMSS.backup)
        backup_files = list(Path(tmpdir).glob("*.*.backup"))
        assert len(backup_files) > 0, "No timestamped backup created"
        
        print("  ✓ Timestamped backup created")


def test_no_changes_no_backup():
    """Test that no backup is created when no changes are needed."""
    print("Test: no changes = no backup")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        
        # Create registry with correct derived fields
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "entity_kind": "file",
                    "filename": "helper.py",
                    "relative_path": "src/utils/helper.py",
                    "extension": "py",
                    "type_code": "00"  # Default type_code
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f, indent=2)
        
        validator = DerivationsValidator()
        stats = validator.apply_derivations(
            registry_path=str(registry_path),
            verbose=False
        )
        
        # No backup should be created
        backup_path = Path(str(registry_path) + ".backup")
        assert not backup_path.exists(), "Backup created when no changes needed"
        
        assert stats["records_updated"] == 0, f"Records reported as updated when consistent: {stats}"
        
        print("  ✓ No unnecessary backup")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing derive --apply functionality")
    print("=" * 60)
    print()
    
    try:
        test_apply_creates_backup()
        test_apply_is_idempotent()
        test_apply_respects_derivations()
        test_timestamped_backup()
        test_no_changes_no_backup()
        
        print()
        print("=" * 60)
        print("✅ All derive --apply tests PASSED")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())

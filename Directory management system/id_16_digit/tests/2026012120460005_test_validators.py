#!/usr/bin/env python3
"""
doc_id: 2026012120460005
Test suite for module assignment and process validators

Tests precedence, conflict detection, and validation rules.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util

# Dynamic imports
def load_validator(filename, class_name):
    validator_path = Path(__file__).parent.parent / "validation" / filename
    spec = importlib.util.spec_from_file_location(filename.replace('.py', ''), validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)

ModuleAssignmentValidator = load_validator("2026012120460001_validate_module_assignment.py", "ModuleAssignmentValidator")
ProcessValidator = load_validator("2026012120460002_validate_process.py", "ProcessValidator")


def test_module_precedence_override():
    """Test that module_id_override takes precedence."""
    print("Test: module override precedence")
    
    validator = ModuleAssignmentValidator()
    
    # Record with override should use override value
    record = {
        "record_id": "ENT-001",
        "record_kind": "entity",
        "relative_path": "core/test.py",  # Would match MOD-CORE
        "module_id": "MOD-OVERRIDE",
        "module_id_override": "MOD-OVERRIDE"
    }
    
    expected, source, reason = validator.compute_expected_module_id(record)
    assert expected == "MOD-OVERRIDE", f"Expected MOD-OVERRIDE, got {expected}"
    assert source == "override", f"Expected source 'override', got {source}"
    
    is_valid, errors = validator.validate_record(record)
    assert is_valid, f"Record should be valid: {errors}"
    
    print("  ✓ Override precedence working")


def test_module_precedence_path_rule():
    """Test that path rules work when no override."""
    print("Test: module path rule matching")
    
    validator = ModuleAssignmentValidator()
    
    # Test each path pattern
    test_cases = [
        ("core/utils.py", "MOD-CORE"),
        ("validation/test.py", "MOD-VALIDATION"),
        ("registry/schema.json", "MOD-REGISTRY"),
        ("automation/cli.py", "MOD-AUTOMATION"),
        ("tests/test_suite.py", "MOD-TESTS"),
        ("docs/README.md", "MOD-DOCS"),
        ("contracts/policy.yaml", "MOD-CONTRACTS"),
        ("hooks/pre-commit.sh", "MOD-HOOKS"),
        ("monitoring/metrics.py", "MOD-MONITORING"),
        ("unknown/file.txt", None),  # No match
    ]
    
    for rel_path, expected_module in test_cases:
        record = {
            "record_id": "ENT-TEST",
            "record_kind": "entity",
            "relative_path": rel_path,
            "module_id": expected_module
        }
        
        computed, source, reason = validator.compute_expected_module_id(record)
        assert computed == expected_module, f"Path {rel_path}: expected {expected_module}, got {computed}"
        
        is_valid, errors = validator.validate_record(record)
        assert is_valid, f"Path {rel_path} should be valid: {errors}"
    
    print("  ✓ Path rules working correctly")


def test_module_conflict_detection():
    """Test that conflicting path rules are detected."""
    print("Test: module conflict detection")
    
    validator = ModuleAssignmentValidator()
    
    # Manually add conflicting rule for testing
    validator.path_rules.append({
        "pattern": "^validation/.*",
        "module_id": "MOD-DIFFERENT"
    })
    
    record = {
        "record_id": "ENT-001",
        "record_kind": "entity",
        "relative_path": "validation/test.py",
        "module_id": "MOD-VALIDATION"
    }
    
    is_valid, errors = validator.validate_record(record)
    assert not is_valid, "Should detect conflict"
    assert len(errors) > 0, "Should have error messages"
    assert "conflicting" in errors[0].lower(), "Error should mention conflict"
    
    print("  ✓ Conflict detection working")


def test_process_validation_basic():
    """Test basic process validation rules."""
    print("Test: process validation basics")
    
    validator = ProcessValidator()
    
    # Valid record with all fields
    valid_record = {
        "record_id": "ENT-001",
        "process_id": "PROC-BUILD",
        "process_step_id": "STEP-COMPILE",
        "process_step_role": "input"
    }
    
    is_valid, errors = validator.validate_record(valid_record)
    assert is_valid, f"Valid record should pass: {errors}"
    
    print("  ✓ Valid process record accepted")


def test_process_step_requires_process():
    """Test that process_step_id requires process_id."""
    print("Test: process_step_id requires process_id")
    
    validator = ProcessValidator()
    
    # Invalid: step without process
    invalid_record = {
        "record_id": "ENT-001",
        "process_step_id": "STEP-COMPILE"
    }
    
    is_valid, errors = validator.validate_record(invalid_record)
    assert not is_valid, "Should reject step without process"
    assert len(errors) > 0, "Should have error"
    assert "process_id" in errors[0].lower(), "Error should mention process_id"
    
    print("  ✓ Step-requires-process rule enforced")


def test_process_role_requires_step_and_process():
    """Test that process_step_role requires both process_id and process_step_id."""
    print("Test: role requires step and process")
    
    validator = ProcessValidator()
    
    # Invalid: role without step
    invalid_record = {
        "record_id": "ENT-001",
        "process_id": "PROC-BUILD",
        "process_step_role": "input"
    }
    
    is_valid, errors = validator.validate_record(invalid_record)
    assert not is_valid, "Should reject role without step"
    assert len(errors) > 0, "Should have error"
    
    print("  ✓ Role-requires-step-and-process rule enforced")


def test_process_invalid_process_id():
    """Test that invalid process_id is detected."""
    print("Test: invalid process_id rejected")
    
    validator = ProcessValidator()
    
    invalid_record = {
        "record_id": "ENT-001",
        "process_id": "PROC-INVALID",
        "process_step_id": "STEP-COMPILE",
        "process_step_role": "input"
    }
    
    is_valid, errors = validator.validate_record(invalid_record)
    assert not is_valid, "Should reject invalid process_id"
    assert "not found" in errors[0].lower(), "Error should mention process not found"
    
    print("  ✓ Invalid process_id rejected")


def test_process_invalid_step_for_process():
    """Test that invalid step for a process is detected."""
    print("Test: invalid step for process rejected")
    
    validator = ProcessValidator()
    
    # STEP-LINT belongs to PROC-BUILD, but using with wrong process
    invalid_record = {
        "record_id": "ENT-001",
        "process_id": "PROC-TEST",
        "process_step_id": "STEP-COMPILE",  # This is PROC-BUILD step
        "process_step_role": "input"
    }
    
    is_valid, errors = validator.validate_record(invalid_record)
    assert not is_valid, "Should reject step not valid for process"
    assert "not valid" in errors[0].lower(), "Error should mention step not valid"
    
    print("  ✓ Invalid step for process rejected")


def test_process_invalid_role_for_step():
    """Test that invalid role for a step is detected."""
    print("Test: invalid role for step rejected")
    
    validator = ProcessValidator()
    
    # STEP-COMPILE allows: input, output, tool, config
    invalid_record = {
        "record_id": "ENT-001",
        "process_id": "PROC-BUILD",
        "process_step_id": "STEP-COMPILE",
        "process_step_role": "fixture"  # Not allowed for STEP-COMPILE
    }
    
    is_valid, errors = validator.validate_record(invalid_record)
    assert not is_valid, "Should reject invalid role for step"
    assert "not allowed" in errors[0].lower(), "Error should mention role not allowed"
    
    print("  ✓ Invalid role for step rejected")


def test_validator_integration():
    """Test validators can process a full registry."""
    print("Test: validator integration with registry")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = Path(tmpdir) / "test_registry.json"
        
        test_registry = {
            "meta": {"version": "1.0"},
            "records": [
                {
                    "record_id": "ENT-001",
                    "record_kind": "entity",
                    "relative_path": "core/utils.py",
                    "module_id": "MOD-CORE",
                    "process_id": "PROC-BUILD",
                    "process_step_id": "STEP-COMPILE",
                    "process_step_role": "input"
                },
                {
                    "record_id": "ENT-002",
                    "record_kind": "entity",
                    "relative_path": "tests/test_suite.py",
                    "module_id": "MOD-TESTS",
                    "process_id": "PROC-TEST",
                    "process_step_id": "STEP-UNIT-TEST",
                    "process_step_role": "test"
                }
            ]
        }
        
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(test_registry, f)
        
        # Test module validator
        mod_validator = ModuleAssignmentValidator()
        is_valid, errors, stats = mod_validator.validate_registry_file(
            registry_path=str(registry_path),
            base_dir=str(tmpdir),
            verbose=False
        )
        assert is_valid, f"Module validation failed: {errors}"
        assert stats["valid"] == 2, f"Expected 2 valid records, got {stats['valid']}"
        
        # Test process validator
        proc_validator = ProcessValidator()
        is_valid, errors, stats = proc_validator.validate_registry_file(
            registry_path=str(registry_path),
            verbose=False
        )
        assert is_valid, f"Process validation failed: {errors}"
        assert stats["valid"] == 2, f"Expected 2 valid records, got {stats['valid']}"
    
    print("  ✓ Validators integrate with full registry")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing module and process validators")
    print("=" * 60)
    print()
    
    try:
        # Module validator tests
        test_module_precedence_override()
        test_module_precedence_path_rule()
        test_module_conflict_detection()
        
        # Process validator tests
        test_process_validation_basic()
        test_process_step_requires_process()
        test_process_role_requires_step_and_process()
        test_process_invalid_process_id()
        test_process_invalid_step_for_process()
        test_process_invalid_role_for_step()
        
        # Integration test
        test_validator_integration()
        
        print()
        print("=" * 60)
        print("✅ All validator tests PASSED")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())

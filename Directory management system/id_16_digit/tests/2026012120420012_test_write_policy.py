#!/usr/bin/env python3
"""
doc_id: 2026012120420012
Tests for Write Policy Validator

Unit tests for column ownership and update policy enforcement.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util
import os

# Dynamic import of validator module
validator_path = Path(__file__).parent.parent / "validation" / "2026012120420006_validate_write_policy.py"
spec = importlib.util.spec_from_file_location("validate_write_policy", validator_path)
validate_write_policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_write_policy)
WritePolicyValidator = validate_write_policy.WritePolicyValidator


def test_tool_only_enforcement():
    """Test that tool_only fields reject user writes."""
    validator = WritePolicyValidator()
    
    # Tool can write tool_only field
    is_valid, error = validator.validate_write(
        column="record_id",
        new_value="REC-000001",
        old_value=None,
        actor="tool"
    )
    assert is_valid, f"Tool should write tool_only field: {error}"
    
    # User cannot write tool_only field
    is_valid, error = validator.validate_write(
        column="record_id",
        new_value="REC-000001",
        old_value=None,
        actor="user"
    )
    assert not is_valid, "User should NOT write tool_only field"
    assert "tool_only" in error.lower()
    
    print("✓ test_tool_only_enforcement PASSED")


def test_user_only_enforcement():
    """Test that user_only fields reject tool writes."""
    validator = WritePolicyValidator()
    
    # User can write user_only field
    is_valid, error = validator.validate_write(
        column="notes",
        new_value="User documentation",
        old_value=None,
        actor="user"
    )
    assert is_valid, f"User should write user_only field: {error}"
    
    # Tool cannot write user_only field
    is_valid, error = validator.validate_write(
        column="notes",
        new_value="Tool-generated note",
        old_value=None,
        actor="tool"
    )
    assert not is_valid, "Tool should NOT write user_only field"
    assert "user_only" in error.lower()
    
    print("✓ test_user_only_enforcement PASSED")


def test_immutable_enforcement():
    """Test that immutable fields cannot be changed."""
    validator = WritePolicyValidator()
    
    # Can set immutable field initially
    is_valid, error = validator.validate_write(
        column="record_id",
        new_value="REC-000001",
        old_value=None,
        actor="tool"
    )
    assert is_valid, f"Should set immutable field initially: {error}"
    
    # Cannot change immutable field
    is_valid, error = validator.validate_write(
        column="record_id",
        new_value="REC-000002",
        old_value="REC-000001",
        actor="tool"
    )
    assert not is_valid, "Should NOT change immutable field"
    assert "immutable" in error.lower()
    
    print("✓ test_immutable_enforcement PASSED")


def test_status_transitions():
    """Test status transition validation."""
    validator = WritePolicyValidator()
    
    # Valid transition: active -> deprecated
    is_valid, error = validator.validate_write(
        column="status",
        new_value="deprecated",
        old_value="active",
        actor="tool"
    )
    assert is_valid, f"Valid status transition should pass: {error}"
    
    # Invalid transition: deprecated -> active (not in allowed list)
    is_valid, error = validator.validate_write(
        column="status",
        new_value="active",
        old_value="deprecated",
        actor="tool"
    )
    assert not is_valid, "Invalid status transition should fail"
    assert "transition" in error.lower()
    
    print("✓ test_status_transitions PASSED")


def test_both_writable():
    """Test that 'both' fields allow user and tool writes."""
    validator = WritePolicyValidator()
    
    # User can write
    is_valid, error = validator.validate_write(
        column="tags",
        new_value=["important", "review"],
        old_value=None,
        actor="user"
    )
    assert is_valid, f"User should write 'both' field: {error}"
    
    # Tool can write
    is_valid, error = validator.validate_write(
        column="tags",
        new_value=["auto-generated"],
        old_value=None,
        actor="tool"
    )
    assert is_valid, f"Tool should write 'both' field: {error}"
    
    print("✓ test_both_writable PASSED")


def test_get_writable_columns():
    """Test getting writable column lists."""
    validator = WritePolicyValidator()
    
    user_writable = validator.get_writable_columns(actor="user")
    tool_writable = validator.get_writable_columns(actor="tool")
    
    # User-only field in user_writable, not in tool_writable
    assert "notes" in user_writable
    assert "notes" not in tool_writable
    
    # Tool-only field in tool_writable, not in user_writable
    assert "record_id" in tool_writable
    assert "record_id" not in user_writable
    
    # Both field in both lists
    assert "tags" in user_writable
    assert "tags" in tool_writable
    
    print("✓ test_get_writable_columns PASSED")


def test_module_override_precedence():
    """Test module_id override enforcement."""
    validator = WritePolicyValidator()
    
    record = {"module_id_override": "MOD-CUSTOM"}
    
    # module_id must match override
    is_valid, error = validator.validate_write(
        column="module_id",
        new_value="MOD-CUSTOM",
        old_value=None,
        actor="tool",
        record=record
    )
    assert is_valid, f"module_id matching override should pass: {error}"
    
    # module_id not matching override should fail
    is_valid, error = validator.validate_write(
        column="module_id",
        new_value="MOD-AUTO",
        old_value=None,
        actor="tool",
        record=record
    )
    assert not is_valid, "module_id not matching override should fail"
    assert "override" in error.lower()
    
    print("✓ test_module_override_precedence PASSED")


def run_all_tests():
    """Run all tests."""
    print("Running Write Policy Validator tests...")
    print()
    
    test_tool_only_enforcement()
    test_user_only_enforcement()
    test_immutable_enforcement()
    test_status_transitions()
    test_both_writable()
    test_get_writable_columns()
    test_module_override_precedence()
    
    print()
    print("✅ All tests PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run_all_tests())
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

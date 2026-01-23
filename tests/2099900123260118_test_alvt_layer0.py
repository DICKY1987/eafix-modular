"""
ALVT Layer 0 Tests
doc_id: 2099900123260118
version: 1.0

Tests for static integrity verification.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

# Import layer0 verifier
import sys
alvt_path = Path(__file__).parent.parent / "tools" / "alvt"
if str(alvt_path) not in sys.path:
    sys.path.insert(0, str(alvt_path))

# Import using proper module name
import importlib.util
spec = importlib.util.spec_from_file_location(
    "layer0_static",
    alvt_path / "2099900121260118_layer0_static.py"
)
layer0_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layer0_module)
Layer0Verifier = layer0_module.Layer0Verifier

__doc_id__ = "2099900123260118"


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create temporary repo structure."""
    return tmp_path


@pytest.fixture
def minimal_contract() -> dict:
    """Create minimal valid contract."""
    return {
        "metadata": {
            "trigger_id": "TEST_TRIGGER",
            "version": "1.0",
            "description": "Test trigger",
            "doc_id": "DOC-TEST-001"
        },
        "required_files": [
            {
                "path": "test_file.py",
                "role": "handler",
                "description": "Test file"
            }
        ],
        "required_nodes": [],
        "required_edges": [],
        "completion_gates": []
    }


def test_layer0_file_exists_pass(temp_repo: Path, minimal_contract: dict):
    """Test Layer 0 passes when all required files exist."""
    # Create required file
    test_file = temp_repo / "test_file.py"
    test_file.write_text("# Test file\n")
    
    # Run verification
    verifier = Layer0Verifier(temp_repo, minimal_contract)
    report = verifier.verify()
    
    # Assertions
    assert report["status"] == "PASS"
    assert report["summary"]["failed"] == 0
    assert any(c["check_id"].startswith("file_exists") and c["passed"] for c in report["checks"])


def test_layer0_file_missing_fail(temp_repo: Path, minimal_contract: dict):
    """Test Layer 0 fails when required file is missing."""
    # Do not create the file
    
    # Run verification
    verifier = Layer0Verifier(temp_repo, minimal_contract)
    report = verifier.verify()
    
    # Assertions
    assert report["status"] == "FAIL"
    assert report["summary"]["failed"] > 0
    
    # Find the file existence check
    file_checks = [c for c in report["checks"] if c["check_id"].startswith("file_exists")]
    assert len(file_checks) > 0
    assert not file_checks[0]["passed"]
    assert "not found" in file_checks[0]["reason"].lower()


def test_layer0_forbidden_pattern_detected(temp_repo: Path, minimal_contract: dict):
    """Test Layer 0 detects forbidden patterns."""
    # Create file with TODO
    test_file = temp_repo / "test_file.py"
    test_file.write_text("# TODO: Implement this\ndef handler(): pass\n")
    
    # Add forbidden pattern to contract
    minimal_contract["forbidden_patterns"] = [
        {
            "pattern": "TODO",
            "reason": "No TODO markers allowed",
            "scope": "required_files"
        }
    ]
    
    # Run verification
    verifier = Layer0Verifier(temp_repo, minimal_contract)
    report = verifier.verify()
    
    # Assertions
    assert report["status"] == "FAIL"
    pattern_checks = [c for c in report["checks"] if "pattern" in c["check_id"]]
    assert len(pattern_checks) > 0
    assert not pattern_checks[0]["passed"]


def test_layer0_no_forbidden_pattern_pass(temp_repo: Path, minimal_contract: dict):
    """Test Layer 0 passes when no forbidden patterns found."""
    # Create clean file
    test_file = temp_repo / "test_file.py"
    test_file.write_text("def handler(): return True\n")
    
    # Add forbidden pattern to contract
    minimal_contract["forbidden_patterns"] = [
        {
            "pattern": "TODO",
            "reason": "No TODO markers allowed",
            "scope": "required_files"
        }
    ]
    
    # Run verification
    verifier = Layer0Verifier(temp_repo, minimal_contract)
    report = verifier.verify()
    
    # Assertions
    assert report["status"] == "PASS"
    assert report["summary"]["failed"] == 0


def test_layer0_config_check_placeholder(temp_repo: Path, minimal_contract: dict):
    """Test Layer 0 config check (placeholder - always passes for now)."""
    # Add config requirement
    minimal_contract["required_config"] = [
        {
            "key": "test.config.key",
            "expected_type": "string"
        }
    ]
    
    # Create required file
    test_file = temp_repo / "test_file.py"
    test_file.write_text("# Config test\n")
    
    # Run verification
    verifier = Layer0Verifier(temp_repo, minimal_contract)
    report = verifier.verify()
    
    # Config checks should exist
    config_checks = [c for c in report["checks"] if "config" in c["check_id"]]
    assert len(config_checks) > 0
    
    # Currently placeholder passes
    assert config_checks[0]["passed"]
    assert "not yet implemented" in config_checks[0]["evidence"].get("note", "").lower()


def test_layer0_report_structure(temp_repo: Path, minimal_contract: dict):
    """Test Layer 0 report has correct structure."""
    # Create required file
    test_file = temp_repo / "test_file.py"
    test_file.write_text("# Test\n")
    
    # Run verification
    verifier = Layer0Verifier(temp_repo, minimal_contract)
    report = verifier.verify()
    
    # Check report structure
    assert "trigger_id" in report
    assert "verification_layer" in report
    assert report["verification_layer"] == "layer0"
    assert "status" in report
    assert report["status"] in ["PASS", "FAIL"]
    assert "timestamp_utc" in report
    assert "checks" in report
    assert isinstance(report["checks"], list)
    assert "summary" in report
    assert "total_checks" in report["summary"]
    assert "passed" in report["summary"]
    assert "failed" in report["summary"]
    
    # Summary should be consistent
    assert report["summary"]["total_checks"] == len(report["checks"])
    assert report["summary"]["passed"] + report["summary"]["failed"] == report["summary"]["total_checks"]


def test_layer0_deterministic_output(temp_repo: Path, minimal_contract: dict):
    """Test Layer 0 produces deterministic output (except timestamps)."""
    # Create required file
    test_file = temp_repo / "test_file.py"
    test_file.write_text("# Test\n")
    
    # Run verification twice
    verifier1 = Layer0Verifier(temp_repo, minimal_contract)
    report1 = verifier1.verify()
    
    verifier2 = Layer0Verifier(temp_repo, minimal_contract)
    report2 = verifier2.verify()
    
    # Remove timestamps for comparison
    report1_copy = report1.copy()
    report2_copy = report2.copy()
    del report1_copy["timestamp_utc"]
    del report2_copy["timestamp_utc"]
    
    # Reports should be identical (except timestamp)
    assert report1_copy == report2_copy


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

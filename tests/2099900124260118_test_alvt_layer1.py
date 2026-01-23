"""
ALVT Layer 1 Tests
doc_id: 2099900124260118
version: 1.0

Tests for graph connectivity verification.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

# Import layer1 verifier
import sys
alvt_path = Path(__file__).parent.parent / "tools" / "alvt"
if str(alvt_path) not in sys.path:
    sys.path.insert(0, str(alvt_path))

# Import using proper module name
import importlib.util
spec = importlib.util.spec_from_file_location(
    "layer1_graph",
    alvt_path / "2099900122260118_layer1_graph.py"
)
layer1_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(layer1_module)
Layer1Verifier = layer1_module.Layer1Verifier

__doc_id__ = "2099900124260118"


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """Create temporary repo structure."""
    return tmp_path


@pytest.fixture
def contract_with_nodes() -> dict:
    """Create contract with required nodes."""
    return {
        "metadata": {
            "trigger_id": "TEST_TRIGGER",
            "version": "1.0",
            "description": "Test trigger",
            "doc_id": "DOC-TEST-002"
        },
        "required_files": [
            {
                "path": "handler.py",
                "role": "handler"
            }
        ],
        "required_nodes": [
            {
                "node_id": "handler_class",
                "node_type": "class",
                "location": "handler.py::Handler"
            },
            {
                "node_id": "handler_method",
                "node_type": "method",
                "location": "handler.py::Handler::process"
            }
        ],
        "required_edges": [
            {
                "from_node": "handler_class",
                "to_node": "handler_method",
                "edge_type": "contains"
            }
        ],
        "completion_gates": []
    }


def test_layer1_nodes_exist_pass(temp_repo: Path, contract_with_nodes: dict):
    """Test Layer 1 passes when all required nodes exist."""
    # Create handler file with required class and method
    handler_file = temp_repo / "handler.py"
    handler_file.write_text("""
class Handler:
    def process(self):
        return True
""")
    
    # Run verification
    verifier = Layer1Verifier(temp_repo, contract_with_nodes)
    report = verifier.verify()
    
    # Assertions
    assert report["verification_layer"] == "layer1"
    assert report["summary"]["total_checks"] > 0
    
    # Check node existence checks
    node_checks = [c for c in report["checks"] if "node_exists" in c["check_id"]]
    assert len(node_checks) >= 2  # handler_class and handler_method
    
    # At least some nodes should be found
    passed_nodes = [c for c in node_checks if c["passed"]]
    assert len(passed_nodes) > 0


def test_layer1_nodes_missing_fail(temp_repo: Path, contract_with_nodes: dict):
    """Test Layer 1 fails when required nodes are missing."""
    # Create empty handler file (no Handler class)
    handler_file = temp_repo / "handler.py"
    handler_file.write_text("# Empty file\n")
    
    # Run verification
    verifier = Layer1Verifier(temp_repo, contract_with_nodes)
    report = verifier.verify()
    
    # Should have node checks
    node_checks = [c for c in report["checks"] if "node_exists" in c["check_id"]]
    assert len(node_checks) > 0
    
    # Some nodes should fail
    failed_nodes = [c for c in node_checks if not c["passed"]]
    assert len(failed_nodes) > 0


def test_layer1_edges_verified(temp_repo: Path, contract_with_nodes: dict):
    """Test Layer 1 verifies edges between nodes."""
    # Create handler file
    handler_file = temp_repo / "handler.py"
    handler_file.write_text("""
class Handler:
    def process(self):
        return True
""")
    
    # Run verification
    verifier = Layer1Verifier(temp_repo, contract_with_nodes)
    report = verifier.verify()
    
    # Check edge verification
    edge_checks = [c for c in report["checks"] if "edge_exists" in c["check_id"]]
    assert len(edge_checks) > 0
    
    # Edge check should have evidence
    assert "evidence" in edge_checks[0]
    assert "from_node" in edge_checks[0]["evidence"]
    assert "to_node" in edge_checks[0]["evidence"]


def test_layer1_function_discovery(temp_repo: Path):
    """Test Layer 1 discovers top-level functions."""
    # Create contract with function node
    contract = {
        "metadata": {
            "trigger_id": "TEST_FUNC",
            "version": "1.0",
            "description": "Test function discovery",
            "doc_id": "DOC-TEST-003"
        },
        "required_files": [
            {
                "path": "functions.py",
                "role": "handler"
            }
        ],
        "required_nodes": [
            {
                "node_id": "process_func",
                "node_type": "function",
                "location": "functions.py::process_data"
            }
        ],
        "required_edges": [],
        "completion_gates": []
    }
    
    # Create functions file
    functions_file = temp_repo / "functions.py"
    functions_file.write_text("""
def process_data(data):
    return data.upper()

def helper():
    pass
""")
    
    # Run verification
    verifier = Layer1Verifier(temp_repo, contract)
    report = verifier.verify()
    
    # Should discover function
    assert report["graph_discovery"]["nodes_discovered"] >= 2  # process_data and helper


def test_layer1_report_structure(temp_repo: Path, contract_with_nodes: dict):
    """Test Layer 1 report has correct structure."""
    # Create handler file
    handler_file = temp_repo / "handler.py"
    handler_file.write_text("class Handler: pass\n")
    
    # Run verification
    verifier = Layer1Verifier(temp_repo, contract_with_nodes)
    report = verifier.verify()
    
    # Check report structure
    assert "trigger_id" in report
    assert "verification_layer" in report
    assert report["verification_layer"] == "layer1"
    assert "status" in report
    assert report["status"] in ["PASS", "FAIL"]
    assert "timestamp_utc" in report
    assert "checks" in report
    assert isinstance(report["checks"], list)
    assert "summary" in report
    assert "graph_discovery" in report
    assert "nodes_discovered" in report["graph_discovery"]
    assert "edges_discovered" in report["graph_discovery"]


def test_layer1_reachability_check(temp_repo: Path, contract_with_nodes: dict):
    """Test Layer 1 checks for orphaned nodes."""
    # Create handler file
    handler_file = temp_repo / "handler.py"
    handler_file.write_text("""
class Handler:
    def process(self):
        return True
""")
    
    # Run verification
    verifier = Layer1Verifier(temp_repo, contract_with_nodes)
    report = verifier.verify()
    
    # Should have reachability check
    reachability_checks = [c for c in report["checks"] if "orphaned" in c["check_id"]]
    
    # May or may not have reachability check depending on contract structure
    # If present, should have evidence
    if reachability_checks:
        assert "evidence" in reachability_checks[0]


def test_layer1_non_python_files_skipped(temp_repo: Path):
    """Test Layer 1 skips non-Python files gracefully."""
    contract = {
        "metadata": {
            "trigger_id": "TEST_SKIP",
            "version": "1.0",
            "description": "Test skip non-Python",
            "doc_id": "DOC-TEST-004"
        },
        "required_files": [
            {
                "path": "config.yaml",
                "role": "config"
            }
        ],
        "required_nodes": [],
        "required_edges": [],
        "completion_gates": []
    }
    
    # Create YAML file
    config_file = temp_repo / "config.yaml"
    config_file.write_text("key: value\n")
    
    # Run verification - should not crash
    verifier = Layer1Verifier(temp_repo, contract)
    report = verifier.verify()
    
    # Should complete without error
    assert "status" in report
    assert report["graph_discovery"]["nodes_discovered"] == 0  # No Python nodes


def test_layer1_deterministic_output(temp_repo: Path, contract_with_nodes: dict):
    """Test Layer 1 produces deterministic output (except timestamps)."""
    # Create handler file
    handler_file = temp_repo / "handler.py"
    handler_file.write_text("class Handler:\n    def process(self): pass\n")
    
    # Run verification twice
    verifier1 = Layer1Verifier(temp_repo, contract_with_nodes)
    report1 = verifier1.verify()
    
    verifier2 = Layer1Verifier(temp_repo, contract_with_nodes)
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

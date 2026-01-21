# doc_id: DOC-AUTOOPS-053
"""Tests for PolicyGate."""

from pathlib import Path

import pytest

from repo_autoops.models.contracts import ModuleContract
from repo_autoops.policy_gate import PolicyGate


@pytest.fixture
def sample_contract(tmp_path: Path) -> ModuleContract:
    """Create sample module contract."""
    return ModuleContract(
        module_id="test_module",
        root=tmp_path / "test_module",
        canonical_allowlist=["*.py", "README.md"],
        generated_patterns=["__pycache__/*", "*.pyc"],
        run_artifact_patterns=["*.log"],
        forbidden_patterns=["*.exe", "secrets.txt"],
    )


def test_policy_gate_initialization(sample_contract: ModuleContract):
    """Test policy gate can be initialized."""
    gate = PolicyGate({"test_module": sample_contract})
    assert "test_module" in gate.contracts


def test_find_module_for_path(sample_contract: ModuleContract, tmp_path: Path):
    """Test finding module for path."""
    module_root = tmp_path / "test_module"
    module_root.mkdir(parents=True, exist_ok=True)
    
    sample_contract.root = module_root
    gate = PolicyGate({"test_module": sample_contract})
    
    test_file = module_root / "test.py"
    module_id = gate.find_module_for_path(test_file)
    assert module_id == "test_module"


def test_classify_canonical_file(sample_contract: ModuleContract, tmp_path: Path):
    """Test classifying canonical file."""
    module_root = tmp_path / "test_module"
    module_root.mkdir(parents=True, exist_ok=True)
    
    sample_contract.root = module_root
    gate = PolicyGate({"test_module": sample_contract})
    
    test_file = module_root / "main.py"
    classification = gate.classify_file(test_file)
    
    assert classification.classification == "canonical"
    assert "allowlist" in classification.reason.lower()


def test_classify_generated_file(sample_contract: ModuleContract, tmp_path: Path):
    """Test classifying generated file."""
    module_root = tmp_path / "test_module"
    module_root.mkdir(parents=True, exist_ok=True)
    
    sample_contract.root = module_root
    gate = PolicyGate({"test_module": sample_contract})
    
    test_file = module_root / "__pycache__" / "test.pyc"
    classification = gate.classify_file(test_file)
    
    assert classification.classification == "generated"


def test_classify_forbidden_file(sample_contract: ModuleContract, tmp_path: Path):
    """Test classifying forbidden file."""
    module_root = tmp_path / "test_module"
    module_root.mkdir(parents=True, exist_ok=True)
    
    sample_contract.root = module_root
    gate = PolicyGate({"test_module": sample_contract})
    
    test_file = module_root / "secrets.txt"
    classification = gate.classify_file(test_file)
    
    assert classification.classification == "quarantine"
    assert "forbidden" in classification.reason.lower()


def test_classify_unknown_file(sample_contract: ModuleContract, tmp_path: Path):
    """Test classifying unknown file."""
    module_root = tmp_path / "test_module"
    module_root.mkdir(parents=True, exist_ok=True)
    
    sample_contract.root = module_root
    gate = PolicyGate({"test_module": sample_contract})
    
    test_file = module_root / "unknown.xyz"
    classification = gate.classify_file(test_file)
    
    assert classification.classification == "quarantine"
    assert "not in any allowlist" in classification.reason.lower()


def test_enforce_contract_missing_required(sample_contract: ModuleContract, tmp_path: Path):
    """Test contract enforcement with missing required files."""
    module_root = tmp_path / "test_module"
    module_root.mkdir(parents=True, exist_ok=True)
    
    sample_contract.root = module_root
    sample_contract.required_paths = ["__init__.py", "main.py"]
    gate = PolicyGate({"test_module": sample_contract})
    
    result = gate.enforce_contract("test_module")
    
    assert "__init__.py" in result["missing"]
    assert "main.py" in result["missing"]

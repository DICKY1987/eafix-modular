#!/usr/bin/env python3
"""
doc_id: 2026012120420016
Integration Tests for Registry Validation System

End-to-end tests validating the complete workflow:
policy loading → validation → normalization → CLI commands.
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_test_registry(path: Path) -> dict:
    """Create a minimal test registry."""
    registry = {
        "meta": {
            "version": "2.1.0",
            "created_utc": "2026-01-21T20:00:00Z",
            "last_updated": "2026-01-21T20:42:00Z"
        },
        "records": [
            {
                "record_kind": "entity",
                "record_id": "REC-000001",
                "entity_id": "ENT-000001",
                "entity_kind": "file",
                "doc_id": "2026012120420001",
                "filename": "test_policy.yaml",
                "relative_path": "contracts/test_policy.yaml",
                "directory_path": "contracts",
                "extension": "yaml",
                "type_code": "01",
                "status": "active",
                "created_utc": "2026-01-21T20:00:00Z",
                "updated_utc": "2026-01-21T20:42:00Z",
                "created_by": "test",
                "updated_by": "test"
            },
            {
                "record_kind": "entity",
                "record_id": "REC-000002",
                "entity_id": "ENT-000002",
                "entity_kind": "transient",
                "transient_id": "TRANS-000001",
                "transient_type": "temp_file",
                "status": "running",
                "ttl_seconds": 3600,
                "expires_utc": "2026-01-21T21:00:00Z",
                "created_utc": "2026-01-21T20:00:00Z",
                "updated_utc": "2026-01-21T20:42:00Z",
                "created_by": "test",
                "updated_by": "test"
            },
            {
                "record_kind": "edge",
                "record_id": "REC-000003",
                "edge_id": "EDGE-20260121-000001",
                "source_entity_id": "ENT-000001",
                "target_entity_id": "ENT-000002",
                "rel_type": "DEPENDS_ON",
                "directionality": "directed",
                "confidence": 0.9,
                "evidence_method": "static_parse",
                "evidence_locator": "test_policy.yaml:15",
                "observed_utc": "2026-01-21T20:42:00Z",
                "tool_version": "scanner-v2.1",
                "status": "active",
                "created_utc": "2026-01-21T20:00:00Z",
                "updated_utc": "2026-01-21T20:42:00Z",
                "created_by": "test",
                "updated_by": "test"
            }
        ]
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    
    return registry


def test_policy_loading():
    """Test that all policy files load correctly."""
    print("Test: Policy Loading")
    
    import importlib.util
    
    base_dir = Path(__file__).parent.parent
    
    policies = [
        ("contracts/2026012120420001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml", "WritePolicyValidator"),
        ("contracts/2026012120420002_UNIFIED_SSOT_REGISTRY_DERIVATIONS.yaml", "DerivationsValidator"),
        ("contracts/2026012120420003_EDGE_EVIDENCE_POLICY.yaml", "EdgeEvidenceValidator")
    ]
    
    for policy_file, validator_class in policies:
        policy_path = base_dir / policy_file
        assert policy_path.exists(), f"Policy file missing: {policy_file}"
        
        # Try loading YAML
        import yaml
        with open(policy_path, 'r', encoding='utf-8') as f:
            policy = yaml.safe_load(f)
        
        assert policy is not None, f"Failed to parse: {policy_file}"
        assert "doc_id" in policy, f"Missing doc_id in: {policy_file}"
        
        print(f"  ✓ {policy_file} (doc_id: {policy['doc_id']})")
    
    print("✅ Policy loading test PASSED\n")


def test_write_policy_validation():
    """Test write policy validator."""
    print("Test: Write Policy Validation")
    
    import importlib.util
    validator_path = Path(__file__).parent.parent / "validation" / "2026012120420006_validate_write_policy.py"
    spec = importlib.util.spec_from_file_location("validate_write_policy", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    WritePolicyValidator = module.WritePolicyValidator
    validator = WritePolicyValidator()
    
    # Test tool_only field
    is_valid, error = validator.validate_write(
        column="record_id",
        new_value="REC-000001",
        old_value=None,
        actor="tool"
    )
    assert is_valid, f"Tool should write tool_only field: {error}"
    
    # Test user cannot write tool_only
    is_valid, error = validator.validate_write(
        column="record_id",
        new_value="REC-000001",
        old_value=None,
        actor="user"
    )
    assert not is_valid, "User should NOT write tool_only field"
    
    print("  ✓ Tool-only enforcement working")
    print("✅ Write policy validation test PASSED\n")


def test_derivations_engine():
    """Test derivations engine."""
    print("Test: Derivations Engine")
    
    import importlib.util
    validator_path = Path(__file__).parent.parent / "validation" / "2026012120420007_validate_derivations.py"
    spec = importlib.util.spec_from_file_location("validate_derivations", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    DerivationEngine = module.DerivationEngine
    engine = DerivationEngine()
    
    # Test BASENAME
    result = engine.evaluate("BASENAME(relative_path)", {"relative_path": "src/module/file.py"})
    assert result == "file.py", f"BASENAME failed: {result}"
    
    # Test DIRNAME
    result = engine.evaluate("DIRNAME(relative_path)", {"relative_path": "src/module/file.py"})
    assert result == "src/module", f"DIRNAME failed: {result}"
    
    # Test EXTENSION
    result = engine.evaluate("EXTENSION(filename)", {"filename": "script.PY"})
    assert result == "py", f"EXTENSION failed: {result}"
    
    # Test UPPER
    result = engine.evaluate("UPPER(rel_type_raw)", {"rel_type_raw": "imports"})
    assert result == "IMPORTS", f"UPPER failed: {result}"
    
    print("  ✓ BASENAME, DIRNAME, EXTENSION, UPPER working")
    print("✅ Derivations engine test PASSED\n")


def test_conditional_enum_validation():
    """Test conditional enum validator."""
    print("Test: Conditional Enum Validation")
    
    import importlib.util
    validator_path = Path(__file__).parent.parent / "validation" / "2026012120420008_validate_conditional_enums.py"
    spec = importlib.util.spec_from_file_location("validate_conditional_enums", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    ConditionalEnumValidator = module.ConditionalEnumValidator
    validator = ConditionalEnumValidator()
    
    # Valid: transient entity with transient status
    record = {
        "record_kind": "entity",
        "entity_kind": "transient",
        "status": "running"
    }
    is_valid, errors = validator.validate_record(record)
    assert is_valid, f"Should allow transient status for transient entity: {errors}"
    
    # Invalid: file entity with transient status
    record = {
        "record_kind": "entity",
        "entity_kind": "file",
        "status": "running"
    }
    is_valid, errors = validator.validate_record(record)
    assert not is_valid, "Should reject transient status for file entity"
    
    print("  ✓ Status-by-entity-kind validation working")
    print("✅ Conditional enum validation test PASSED\n")


def test_edge_evidence_validation():
    """Test edge evidence validator."""
    print("Test: Edge Evidence Validation")
    
    import importlib.util
    validator_path = Path(__file__).parent.parent / "validation" / "2026012120420009_validate_edge_evidence.py"
    spec = importlib.util.spec_from_file_location("validate_edge_evidence", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    EdgeEvidenceValidator = module.EdgeEvidenceValidator
    validator = EdgeEvidenceValidator()
    
    # Valid edge with evidence
    edge = {
        "record_kind": "edge",
        "evidence_method": "static_parse",
        "evidence_locator": "file.py:42",
        "observed_utc": "2026-01-21T20:42:00Z",
        "tool_version": "scanner-v2.1",
        "confidence": 0.9
    }
    is_valid, errors, corrections = validator.validate_edge(edge)
    assert is_valid, f"Valid edge should pass: {errors}"
    
    # Invalid: missing evidence_method
    edge = {
        "record_kind": "edge",
        "confidence": 0.8
    }
    is_valid, errors, corrections = validator.validate_edge(edge)
    assert not is_valid, "Edge without evidence_method should fail"
    
    print("  ✓ Edge evidence validation working")
    print("✅ Edge evidence validation test PASSED\n")


def test_registry_normalization():
    """Test registry normalizer."""
    print("Test: Registry Normalization")
    
    import importlib.util
    validator_path = Path(__file__).parent.parent / "validation" / "2026012120420010_normalize_registry.py"
    spec = importlib.util.spec_from_file_location("normalize_registry", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    RegistryNormalizer = module.RegistryNormalizer
    normalizer = RegistryNormalizer()
    
    # Test path normalization
    record = {
        "record_kind": "entity",
        "relative_path": ".\\src\\file.py"
    }
    normalized = normalizer.normalize_record(record, in_place=False)
    assert normalized["relative_path"] == "src/file.py", f"Path normalization failed: {normalized['relative_path']}"
    
    # Test rel_type uppercase
    record = {
        "record_kind": "edge",
        "rel_type": "imports"
    }
    normalized = normalizer.normalize_record(record, in_place=False)
    assert normalized["rel_type"] == "IMPORTS", f"rel_type normalization failed: {normalized['rel_type']}"
    
    print("  ✓ Path and rel_type normalization working")
    print("✅ Registry normalization test PASSED\n")


def test_end_to_end_workflow():
    """Test complete workflow with temp registry."""
    print("Test: End-to-End Workflow")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        registry_path = tmpdir / "test_registry.json"
        
        # Create test registry
        registry = create_test_registry(registry_path)
        print(f"  ✓ Created test registry: {len(registry['records'])} records")
        
        # Test validators on temp registry
        import importlib.util
        
        # Conditional enum validator
        validator_path = Path(__file__).parent.parent / "validation" / "2026012120420008_validate_conditional_enums.py"
        spec = importlib.util.spec_from_file_location("validate_conditional_enums", validator_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        ConditionalEnumValidator = module.ConditionalEnumValidator
        validator = ConditionalEnumValidator()
        is_valid, errors, stats = validator.validate_registry_file(str(registry_path))
        
        print(f"  ✓ Conditional enum validation: {stats['valid']}/{stats['total']} valid")
        
        # Edge evidence validator
        validator_path = Path(__file__).parent.parent / "validation" / "2026012120420009_validate_edge_evidence.py"
        spec = importlib.util.spec_from_file_location("validate_edge_evidence", validator_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        EdgeEvidenceValidator = module.EdgeEvidenceValidator
        validator = EdgeEvidenceValidator()
        is_valid, errors, stats = validator.validate_registry_file(str(registry_path))
        
        print(f"  ✓ Edge evidence validation: {stats['valid']}/{stats['total_edges']} valid")
        
        # Normalization
        validator_path = Path(__file__).parent.parent / "validation" / "2026012120420010_normalize_registry.py"
        spec = importlib.util.spec_from_file_location("normalize_registry", validator_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        RegistryNormalizer = module.RegistryNormalizer
        normalizer = RegistryNormalizer()
        stats = normalizer.normalize_registry_file(str(registry_path), dry_run=True)
        
        print(f"  ✓ Normalization check: {stats['normalized']} records need normalization")
    
    print("✅ End-to-end workflow test PASSED\n")


def run_all_integration_tests():
    """Run all integration tests."""
    print("="*60)
    print("Integration Tests for Registry Validation System")
    print("="*60)
    print()
    
    test_policy_loading()
    test_write_policy_validation()
    test_derivations_engine()
    test_conditional_enum_validation()
    test_edge_evidence_validation()
    test_registry_normalization()
    test_end_to_end_workflow()
    
    print("="*60)
    print("🎉 All integration tests PASSED")
    print("="*60)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run_all_integration_tests())
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

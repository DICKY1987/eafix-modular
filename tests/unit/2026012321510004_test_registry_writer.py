"""
Unit Tests for Registry Writer

doc_id: 2026012321510004
purpose: Test RegistryWriter policy enforcement, CAS, atomic write, rollback
classification: TEST
version: 1.0
date: 2026-01-23T21:51:00Z
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))
from services.registry_writer.promotion_patch import PromotionPatch
from services.registry_writer.registry_writer_service import RegistryWriter


@pytest.fixture
def temp_registry(tmp_path):
    """Create temporary registry for testing."""
    registry_path = tmp_path / "test_registry.json"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    initial_data = {
        "records": [],
        "metadata": {},
        "schema_version": "2.2"
    }
    
    with open(registry_path, 'w') as f:
        json.dump(initial_data, f)
    
    return registry_path, backup_dir


def test_promotion_patch_validation():
    """Test PromotionPatch validates inputs."""
    # Valid patch
    patch = PromotionPatch(
        patch_id="test-001",
        patch_type="add_entity",
        target_record_id=None,
        changes={"doc_id": "1234567890123456"},
        source="scanner",
        timestamp_utc="2026-01-23T21:51:00Z",
        rationale="Test entity",
        registry_hash="sha256:abc123"
    )
    assert patch.patch_id == "test-001"
    
    # Invalid patch_type
    with pytest.raises(ValueError, match="Invalid patch_type"):
        PromotionPatch(
            patch_id="test-002",
            patch_type="invalid_type",
            target_record_id=None,
            changes={},
            source="scanner",
            timestamp_utc="2026-01-23T21:51:00Z",
            rationale="Test",
            registry_hash="sha256:abc"
        )
    
    # Invalid source
    with pytest.raises(ValueError, match="Invalid source"):
        PromotionPatch(
            patch_id="test-003",
            patch_type="add_entity",
            target_record_id=None,
            changes={},
            source="invalid_source",
            timestamp_utc="2026-01-23T21:51:00Z",
            rationale="Test",
            registry_hash="sha256:abc"
        )
    
    # Missing registry_hash prefix
    with pytest.raises(ValueError, match="registry_hash must start"):
        PromotionPatch(
            patch_id="test-004",
            patch_type="add_entity",
            target_record_id=None,
            changes={},
            source="scanner",
            timestamp_utc="2026-01-23T21:51:00Z",
            rationale="Test",
            registry_hash="abc123"
        )


def test_registry_writer_add_entity(temp_registry):
    """Test adding entity to registry."""
    registry_path, backup_dir = temp_registry
    
    # Monkey-patch RegistryWriter paths
    writer = RegistryWriter()
    writer.registry_path = registry_path
    writer.backup_dir = backup_dir
    writer.lock_path = registry_path.parent / ".lock"
    
    # Compute current hash
    with open(registry_path, 'rb') as f:
        import hashlib
        current_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"
    
    # Create patch
    patch = PromotionPatch(
        patch_id="test-add-001",
        patch_type="add_entity",
        target_record_id=None,
        changes={
            "doc_id": "2026012321510000",
            "entity_kind": "file",
            "relative_path": "test/file.py",
            "status": "active"
        },
        source="scanner",
        timestamp_utc="2026-01-23T21:51:00Z",
        rationale="Test file registration",
        registry_hash=current_hash
    )
    
    # Apply patch
    success, errors = writer.apply_promotion(patch)
    
    assert success, f"Patch failed: {errors}"
    assert len(errors) == 0
    
    # Verify entity was added
    with open(registry_path, 'r') as f:
        data = json.load(f)
    
    assert len(data['records']) == 1
    assert data['records'][0]['doc_id'] == "2026012321510000"
    assert data['records'][0]['record_kind'] == "entity"


def test_write_policy_violation(temp_registry):
    """Test write policy enforcement."""
    registry_path, backup_dir = temp_registry
    
    writer = RegistryWriter()
    writer.registry_path = registry_path
    writer.backup_dir = backup_dir
    writer.lock_path = registry_path.parent / ".lock"
    
    with open(registry_path, 'rb') as f:
        import hashlib
        current_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"
    
    # Try to write tool_only field from manual source
    patch = PromotionPatch(
        patch_id="test-policy-001",
        patch_type="add_entity",
        target_record_id=None,
        changes={
            "doc_id": "2026012321510001",
            "entity_kind": "file",
            "size_bytes": 1234  # tool_only field
        },
        source="manual",  # manual source not allowed for tool_only
        timestamp_utc="2026-01-23T21:51:00Z",
        rationale="Should fail policy check",
        registry_hash=current_hash
    )
    
    success, errors = writer.apply_promotion(patch)
    
    assert not success
    assert any("tool_only" in err for err in errors)


def test_cas_precondition(temp_registry):
    """Test CAS precondition prevents stale writes."""
    registry_path, backup_dir = temp_registry
    
    writer = RegistryWriter()
    writer.registry_path = registry_path
    writer.backup_dir = backup_dir
    writer.lock_path = registry_path.parent / ".lock"
    
    # Use wrong hash
    patch = PromotionPatch(
        patch_id="test-cas-001",
        patch_type="add_entity",
        target_record_id=None,
        changes={"doc_id": "2026012321510002"},
        source="scanner",
        timestamp_utc="2026-01-23T21:51:00Z",
        rationale="Should fail CAS check",
        registry_hash="sha256:wronghash"
    )
    
    success, errors = writer.apply_promotion(patch)
    
    assert not success
    assert any("CAS precondition failed" in err for err in errors)


def test_normalization_applied(temp_registry):
    """Test normalization runs automatically."""
    registry_path, backup_dir = temp_registry
    
    writer = RegistryWriter()
    writer.registry_path = registry_path
    writer.backup_dir = backup_dir
    writer.lock_path = registry_path.parent / ".lock"
    
    with open(registry_path, 'rb') as f:
        import hashlib
        current_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"
    
    # Add entity with lowercase rel_type and backslash path
    patch = PromotionPatch(
        patch_id="test-norm-001",
        patch_type="add_entity",
        target_record_id=None,
        changes={
            "doc_id": "2026012321510003",
            "entity_kind": "file",
            "relative_path": "test\\file.py",  # backslash
            "rel_type": "imports"  # lowercase
        },
        source="scanner",
        timestamp_utc="2026-01-23T21:51:00Z",
        rationale="Test normalization",
        registry_hash=current_hash
    )
    
    success, errors = writer.apply_promotion(patch)
    assert success
    
    with open(registry_path, 'r') as f:
        data = json.load(f)
    
    record = data['records'][0]
    assert record['relative_path'] == "test/file.py"  # normalized to forward slash
    assert record.get('rel_type') == "IMPORTS"  # normalized to uppercase


def test_backup_created(temp_registry):
    """Test backup is created before write."""
    registry_path, backup_dir = temp_registry
    
    writer = RegistryWriter()
    writer.registry_path = registry_path
    writer.backup_dir = backup_dir
    writer.lock_path = registry_path.parent / ".lock"
    
    with open(registry_path, 'rb') as f:
        import hashlib
        current_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"
    
    patch = PromotionPatch(
        patch_id="test-backup-001",
        patch_type="add_entity",
        target_record_id=None,
        changes={"doc_id": "2026012321510004"},
        source="scanner",
        timestamp_utc="2026-01-23T21:51:00Z",
        rationale="Test backup",
        registry_hash=current_hash
    )
    
    success, errors = writer.apply_promotion(patch)
    assert success
    
    # Check backup was created
    backups = list(backup_dir.glob("UNIFIED_SSOT_REGISTRY_*.json"))
    assert len(backups) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

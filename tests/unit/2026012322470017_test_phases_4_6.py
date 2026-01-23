#!/usr/bin/env python3
"""
doc_id: 2026012322470017
Unit Tests for Phases 4-6 Components

Tests reconciler and generator orchestrator.
"""

import pytest
import tempfile
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))

from repo_autoops.automation_descriptor.reconciler import Reconciler
from repo_autoops.automation_descriptor.work_queue import WorkQueue
from services.generator.generator_orchestrator import GeneratorOrchestrator


class TestReconciler:
    """Test reconciliation functionality."""
    
    def test_reconciler_init(self, tmp_path):
        """Test reconciler initialization."""
        queue = WorkQueue(db_path=tmp_path / "test.db")
        registry_path = tmp_path / "registry.json"
        
        reconciler = Reconciler(
            watch_paths=["repo_autoops"],
            registry_path=registry_path,
            queue=queue
        )
        
        assert reconciler is not None
        assert len(reconciler.watch_paths) == 1
    
    def test_reconcile_missing_from_registry(self, tmp_path):
        """Test detecting files missing from registry."""
        queue = WorkQueue(db_path=tmp_path / "test.db")
        registry_path = tmp_path / "registry.json"
        
        # Create empty registry
        with open(registry_path, 'w') as f:
            json.dump({"records": []}, f)
        
        # Create test directory with Python file
        test_dir = tmp_path / "test_scan"
        test_dir.mkdir()
        test_file = test_dir / "test.py"
        test_file.write_text("print('hello')")
        
        reconciler = Reconciler(
            watch_paths=[str(test_dir)],
            registry_path=registry_path,
            queue=queue
        )
        
        stats = reconciler.reconcile()
        
        assert stats["files_scanned"] == 1
        assert stats["registry_records"] == 0
        assert stats["missing_from_registry"] == 1
        assert stats["repairs_enqueued"] == 1


class TestGeneratorOrchestrator:
    """Test generator orchestration."""
    
    def test_generator_orchestrator_init(self, tmp_path):
        """Test generator orchestrator initialization."""
        registry_path = tmp_path / "registry.json"
        
        orchestrator = GeneratorOrchestrator(registry_path)
        
        assert orchestrator is not None
        assert orchestrator.registry_path == registry_path
    
    def test_compute_source_hash(self, tmp_path):
        """Test source hash computation (excludes generators)."""
        registry_path = tmp_path / "registry.json"
        
        # Create registry with entity and generator records
        registry = {
            "records": [
                {"record_kind": "entity", "doc_id": "001", "relative_path": "test.py"},
                {"record_kind": "generator", "generator_id": "gen1"}
            ]
        }
        
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        orchestrator = GeneratorOrchestrator(registry_path)
        source_hash = orchestrator.compute_source_hash()
        
        assert isinstance(source_hash, str)
        assert len(source_hash) == 64  # SHA-256 hex
    
    def test_detect_stale_generators(self, tmp_path):
        """Test stale generator detection."""
        registry_path = tmp_path / "registry.json"
        
        registry = {
            "records": [
                {
                    "record_kind": "generator",
                    "generator_id": "gen1",
                    "last_source_hash": "old_hash"
                }
            ]
        }
        
        with open(registry_path, 'w') as f:
            json.dump(registry, f)
        
        orchestrator = GeneratorOrchestrator(registry_path)
        orchestrator.load_generators()
        
        stale = orchestrator.detect_stale_generators()
        
        assert len(stale) == 1
        assert stale[0] == "gen1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
doc_id: 2026012322470009
Unit Tests for Phase 2 - Event Infrastructure

Tests work queue, lock manager, stability checker, and suppression manager.
"""

import pytest
import time
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[2]))

from repo_autoops.automation_descriptor.work_queue import WorkQueue, WorkItemStatus
from repo_autoops.automation_descriptor.lock_manager import LockManager
from repo_autoops.automation_descriptor.stability_checker import StabilityChecker
from repo_autoops.automation_descriptor.suppression_manager import SuppressionManager


class TestWorkQueue:
    """Test work queue operations."""
    
    def test_enqueue_dequeue(self, tmp_path):
        """Test basic enqueue/dequeue."""
        queue = WorkQueue(db_path=tmp_path / "test.db")
        
        assert queue.enqueue("/path/to/file.py", "FILE_ADDED")
        
        item = queue.dequeue()
        assert item is not None
        assert item['path'] == "/path/to/file.py"
        assert item['event_type'] == "FILE_ADDED"
    
    def test_upsert_by_path(self, tmp_path):
        """Test UPSERT deduplication."""
        queue = WorkQueue(db_path=tmp_path / "test.db")
        
        queue.enqueue("/same/file.py", "FILE_ADDED")
        queue.enqueue("/same/file.py", "FILE_MODIFIED")
        
        depth = queue.get_queue_depth()
        assert depth.get('queued', 0) == 1  # Only one item
    
    def test_mark_completed(self, tmp_path):
        """Test marking items completed."""
        queue = WorkQueue(db_path=tmp_path / "test.db")
        
        queue.enqueue("/test/file.py", "FILE_ADDED")
        item = queue.dequeue()
        queue.mark_completed(item['path'])
        
        depth = queue.get_queue_depth()
        assert depth.get('completed', 0) == 1


class TestLockManager:
    """Test lock manager."""
    
    def test_path_lock(self):
        """Test path-level locking."""
        manager = LockManager()
        
        with manager.path_lock("/test/path.py"):
            stats = manager.get_stats()
            assert stats['path_locks_held'] == 1
        
        stats = manager.get_stats()
        assert stats['path_locks_held'] == 0
    
    def test_doc_id_lock(self):
        """Test doc ID locking."""
        manager = LockManager()
        
        with manager.doc_id_lock("2026012322470001"):
            stats = manager.get_stats()
            assert stats['doc_id_locks_held'] == 1
    
    def test_registry_lock(self):
        """Test registry-wide locking."""
        manager = LockManager()
        
        with manager.registry_lock():
            stats = manager.get_stats()
            assert stats['registry_locked'] is True


class TestStabilityChecker:
    """Test stability checker."""
    
    def test_stable_file(self, tmp_path):
        """Test detecting stable file."""
        checker = StabilityChecker(min_age_seconds=0.1, sample_interval_seconds=0.05)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        time.sleep(0.15)  # Let file age
        
        assert checker.is_stable(test_file) is True
    
    def test_young_file(self, tmp_path):
        """Test detecting young file."""
        checker = StabilityChecker(min_age_seconds=1.0)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # Immediately check (file too young)
        assert checker.is_stable(test_file) is False


class TestSuppressionManager:
    """Test suppression manager."""
    
    def test_register_and_suppress(self):
        """Test operation registration and suppression."""
        manager = SuppressionManager(suppression_window_seconds=0.5)
        
        path = "/test/file.py"
        manager.register_operation(path)
        
        assert manager.should_suppress(path) is True
    
    def test_expiration(self):
        """Test suppression expiration."""
        manager = SuppressionManager(suppression_window_seconds=0.1)
        
        path = "/test/file.py"
        manager.register_operation(path)
        
        assert manager.should_suppress(path) is True
        
        time.sleep(0.15)  # Wait for expiration
        
        assert manager.should_suppress(path) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

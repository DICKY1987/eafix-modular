# doc_id: DOC-AUTOOPS-051
"""Tests for EventQueue."""

import tempfile
from pathlib import Path

import pytest

from repo_autoops.queue import EventQueue


def test_queue_initialization():
    """Test that queue database initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_queue.db"
        queue = EventQueue(db_path)
        assert db_path.exists()
        assert queue.get_pending_count() == 0


def test_enqueue_and_dequeue():
    """Test enqueueing and dequeueing work items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_queue.db"
        queue = EventQueue(db_path)

        # Enqueue an item
        test_path = Path("/test/file.py")
        work_item_id = queue.enqueue(test_path, "modified")
        assert work_item_id.startswith("work_")
        assert queue.get_pending_count() == 1

        # Dequeue the item
        items = queue.dequeue_batch(limit=10)
        assert len(items) == 1
        assert items[0].path == str(test_path)
        assert items[0].event_type == "modified"
        assert items[0].status.value == "processing"

        # Mark as done
        queue.mark_done(work_item_id)
        assert queue.get_pending_count() == 0


def test_deduplication():
    """Test that enqueueing same path updates existing item."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_queue.db"
        queue = EventQueue(db_path)

        test_path = Path("/test/file.py")
        
        # Enqueue same path twice
        id1 = queue.enqueue(test_path, "created")
        id2 = queue.enqueue(test_path, "modified")

        # Should be same work item (deduped)
        assert id1 == id2
        assert queue.get_pending_count() == 1

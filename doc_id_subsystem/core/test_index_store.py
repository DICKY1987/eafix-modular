"""
Tests for common/index_store.py - SQLite-based file index.
"""
# DOC_ID: DOC-TEST-INDEX-STORE-001

import pytest
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.index_store import (
    IndexStore,
    detect_language,
    compute_file_hash,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_index.sqlite"
        yield db_path


@pytest.fixture
def index_store(temp_db):
    """Create IndexStore instance."""
    return IndexStore(temp_db)


class TestIndexStore:
    """Test IndexStore class."""
    
    def test_init_creates_schema(self, temp_db):
        """Test that initialization creates database schema."""
        store = IndexStore(temp_db)
        assert temp_db.exists()
        
        # Verify tables exist
        with store._conn() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = [t[0] for t in tables]
            assert "file_index" in table_names
            assert "scan_runs" in table_names
    
    def test_update_and_get_file_state(self, index_store):
        """Test storing and retrieving file state."""
        state = {
            "ext": ".py",
            "lang": "python",
            "mtime_ns": 1234567890,
            "size": 1024,
            "sha256": "abc123",
            "doc_id": "DOC-TEST-FILE-0001",
            "doc_id_source": "python_comment",
            "parse_status": "ok",
            "last_seen_run_id": "RUN-001"
        }
        
        index_store.update_file_state("test/file.py", state)
        
        retrieved = index_store.get_file_state("test/file.py")
        assert retrieved is not None
        assert retrieved["doc_id"] == "DOC-TEST-FILE-0001"
        assert retrieved["ext"] == ".py"
        assert retrieved["size"] == 1024
    
    def test_get_nonexistent_file_state(self, index_store):
        """Test retrieving state for file not in index."""
        result = index_store.get_file_state("nonexistent/file.py")
        assert result is None
    
    def test_update_overwrites_existing(self, index_store):
        """Test that updating same file overwrites previous state."""
        # Insert initial state
        state1 = {
            "ext": ".py",
            "lang": "python",
            "mtime_ns": 1000,
            "size": 100,
            "sha256": "hash1",
            "doc_id": None,
            "doc_id_source": None,
            "parse_status": "ok",
            "last_seen_run_id": "RUN-001"
        }
        index_store.update_file_state("test.py", state1)
        
        # Update with new state
        state2 = state1.copy()
        state2["mtime_ns"] = 2000
        state2["size"] = 200
        state2["doc_id"] = "DOC-TEST-FILE-0001"
        index_store.update_file_state("test.py", state2)
        
        # Verify latest state
        result = index_store.get_file_state("test.py")
        assert result["mtime_ns"] == 2000
        assert result["size"] == 200
        assert result["doc_id"] == "DOC-TEST-FILE-0001"
    
    def test_get_files_missing_doc_id(self, index_store):
        """Test retrieving files without doc_ids."""
        # Add files with and without doc_ids
        index_store.update_file_state("has_id.py", {
            "ext": ".py",
            "lang": "python",
            "mtime_ns": 1000,
            "size": 100,
            "sha256": "hash1",
            "doc_id": "DOC-TEST-001",
            "doc_id_source": "python_comment",
            "parse_status": "ok",
            "last_seen_run_id": "RUN-001"
        })
        
        index_store.update_file_state("missing_id.py", {
            "ext": ".py",
            "lang": "python",
            "mtime_ns": 2000,
            "size": 200,
            "sha256": "hash2",
            "doc_id": None,
            "doc_id_source": None,
            "parse_status": "ok",
            "last_seen_run_id": "RUN-001"
        })
        
        missing = index_store.get_files_missing_doc_id()
        assert len(missing) == 1
        assert missing[0]["path"] == "missing_id.py"


class TestScanRuns:
    """Test scan run tracking."""
    
    def test_start_and_complete_scan(self, index_store):
        """Test recording scan run start and completion."""
        run_id = "RUN-TEST-001"
        
        # Start scan
        index_store.start_scan_run(run_id)
        
        # Complete scan
        stats = {
            "files_scanned": 100,
            "files_changed": 10,
            "cache_hits": 90
        }
        index_store.mark_scan_complete(run_id, stats)
        
        # Verify completion
        last_run = index_store.get_last_scan_run()
        assert last_run is not None
        assert last_run["run_id"] == run_id
        assert last_run["files_scanned"] == 100
        assert last_run["cache_hits"] == 90
        assert last_run["status"] == "completed"
    
    def test_get_last_scan_run_returns_most_recent(self, index_store):
        """Test that get_last_scan_run returns most recent completed run."""
        # Create multiple runs
        for i in range(3):
            run_id = f"RUN-{i}"
            index_store.start_scan_run(run_id)
            time.sleep(0.01)  # Ensure different timestamps
            index_store.mark_scan_complete(run_id, {
                "files_scanned": i * 10,
                "files_changed": i,
                "cache_hits": 0
            })
        
        last_run = index_store.get_last_scan_run()
        assert last_run["run_id"] == "RUN-2"
        assert last_run["files_scanned"] == 20


class TestStatistics:
    """Test statistics functions."""
    
    def test_get_stats(self, index_store):
        """Test getting index statistics."""
        # Add some files
        for i in range(5):
            index_store.update_file_state(f"file{i}.py", {
                "ext": ".py",
                "lang": "python",
                "mtime_ns": 1000 + i,
                "size": 100,
                "sha256": f"hash{i}",
                "doc_id": f"DOC-TEST-{i:04d}" if i < 3 else None,
                "doc_id_source": "python_comment" if i < 3 else None,
                "parse_status": "ok",
                "last_seen_run_id": "RUN-001"
            })
        
        stats = index_store.get_stats()
        assert stats["total_files"] == 5
        assert stats["files_with_doc_id"] == 3
        assert stats["coverage_pct"] == 60.0
        assert ".py" in stats["top_extensions"]


class TestCleanup:
    """Test cleanup operations."""
    
    def test_cleanup_stale_entries(self, index_store):
        """Test removing entries for deleted files."""
        # Add files
        for i in range(5):
            index_store.update_file_state(f"file{i}.py", {
                "ext": ".py",
                "lang": "python",
                "mtime_ns": 1000,
                "size": 100,
                "sha256": f"hash{i}",
                "doc_id": None,
                "doc_id_source": None,
                "parse_status": "ok",
                "last_seen_run_id": "RUN-001"
            })
        
        # Simulate 2 files deleted (only 3 still exist)
        existing_paths = {"file0.py", "file1.py", "file2.py"}
        removed = index_store.cleanup_stale_entries(existing_paths)
        
        assert removed == 2
        
        # Verify only existing files remain
        stats = index_store.get_stats()
        assert stats["total_files"] == 3
    
    def test_rebuild_index_clears_all_data(self, index_store):
        """Test that rebuild clears all cached data."""
        # Add data
        index_store.update_file_state("test.py", {
            "ext": ".py",
            "lang": "python",
            "mtime_ns": 1000,
            "size": 100,
            "sha256": "hash",
            "doc_id": None,
            "doc_id_source": None,
            "parse_status": "ok",
            "last_seen_run_id": "RUN-001"
        })
        index_store.start_scan_run("RUN-001")
        
        # Rebuild
        index_store.rebuild_index()
        
        # Verify cleared
        stats = index_store.get_stats()
        assert stats["total_files"] == 0
        assert index_store.get_last_scan_run() is None


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_detect_language(self):
        """Test language detection from extension."""
        assert detect_language(Path("test.py")) == "python"
        assert detect_language(Path("test.md")) == "markdown"
        assert detect_language(Path("test.yaml")) == "yaml"
        assert detect_language(Path("test.yml")) == "yaml"
        assert detect_language(Path("test.json")) == "json"
        assert detect_language(Path("test.ps1")) == "powershell"
        assert detect_language(Path("test.sh")) == "shell"
        assert detect_language(Path("test.unknown")) == "unknown"
    
    def test_compute_file_hash(self, tmp_path):
        """Test file hash computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        hash1 = compute_file_hash(test_file)
        assert len(hash1) == 64  # SHA256 hex length
        
        # Same content = same hash
        hash2 = compute_file_hash(test_file)
        assert hash1 == hash2
        
        # Different content = different hash
        test_file.write_text("different content")
        hash3 = compute_file_hash(test_file)
        assert hash1 != hash3


class TestConcurrency:
    """Test thread safety (basic)."""
    
    def test_multiple_connections(self, temp_db):
        """Test that multiple store instances can coexist."""
        store1 = IndexStore(temp_db)
        store2 = IndexStore(temp_db)
        
        # Write with store1
        store1.update_file_state("test.py", {
            "ext": ".py",
            "lang": "python",
            "mtime_ns": 1000,
            "size": 100,
            "sha256": "hash",
            "doc_id": "DOC-TEST-0001",
            "doc_id_source": "python_comment",
            "parse_status": "ok",
            "last_seen_run_id": "RUN-001"
        })
        
        # Read with store2
        result = store2.get_file_state("test.py")
        assert result is not None
        assert result["doc_id"] == "DOC-TEST-0001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

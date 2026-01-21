# doc_id: DOC-AUTOOPS-052
"""Tests for FileWatcher."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from repo_autoops.models.events import EventType, FileEvent
from repo_autoops.watcher import FileWatcher


@pytest.fixture
def tmp_watch_dir(tmp_path: Path) -> Path:
    """Create temporary watch directory."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    return watch_dir


def test_watcher_initialization(tmp_watch_dir: Path):
    """Test watcher can be initialized."""
    watcher = FileWatcher(
        roots=[tmp_watch_dir],
        ignore_patterns=["*.tmp"],
        file_patterns=["*.py"],
        stability_delay=1.0,
    )
    assert watcher.roots == [tmp_watch_dir]
    assert "*.tmp" in watcher.ignore_patterns
    assert "*.py" in watcher.file_patterns


def test_should_ignore(tmp_watch_dir: Path):
    """Test ignore pattern matching."""
    watcher = FileWatcher(
        roots=[tmp_watch_dir],
        ignore_patterns=[".git/", "__pycache__/"],
        file_patterns=[],
    )
    
    assert watcher._should_ignore(tmp_watch_dir / ".git" / "config")
    assert watcher._should_ignore(tmp_watch_dir / "__pycache__" / "module.pyc")
    assert not watcher._should_ignore(tmp_watch_dir / "module.py")


def test_matches_patterns(tmp_watch_dir: Path):
    """Test file pattern matching."""
    watcher = FileWatcher(
        roots=[tmp_watch_dir],
        ignore_patterns=[],
        file_patterns=["*.py", "*.md"],
    )
    
    assert watcher._matches_patterns(Path("test.py"))
    assert watcher._matches_patterns(Path("README.md"))
    assert not watcher._matches_patterns(Path("test.txt"))


def test_callback_registration(tmp_watch_dir: Path):
    """Test callback can be registered."""
    watcher = FileWatcher(
        roots=[tmp_watch_dir],
        ignore_patterns=[],
        file_patterns=[],
    )
    
    callback = MagicMock()
    watcher.add_callback(callback)
    
    assert callback in watcher.callbacks


@pytest.mark.asyncio
async def test_get_content_hash(tmp_watch_dir: Path):
    """Test content hash calculation."""
    watcher = FileWatcher(
        roots=[tmp_watch_dir],
        ignore_patterns=[],
        file_patterns=[],
    )
    
    test_file = tmp_watch_dir / "test.txt"
    test_file.write_text("test content")
    
    hash1 = await watcher._get_content_hash(test_file)
    hash2 = await watcher._get_content_hash(test_file)
    
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 32  # MD5 hash length


@pytest.mark.asyncio
async def test_wait_for_stability_stable_file(tmp_watch_dir: Path):
    """Test stability check for stable file."""
    watcher = FileWatcher(
        roots=[tmp_watch_dir],
        ignore_patterns=[],
        file_patterns=[],
        stability_delay=0.1,  # Short delay for test
    )
    
    test_file = tmp_watch_dir / "stable.txt"
    test_file.write_text("stable content")
    
    is_stable = await watcher._wait_for_stability(test_file)
    assert is_stable


@pytest.mark.asyncio
async def test_wait_for_stability_missing_file(tmp_watch_dir: Path):
    """Test stability check for missing file."""
    watcher = FileWatcher(
        roots=[tmp_watch_dir],
        ignore_patterns=[],
        file_patterns=[],
    )
    
    missing_file = tmp_watch_dir / "missing.txt"
    is_stable = await watcher._wait_for_stability(missing_file)
    assert not is_stable

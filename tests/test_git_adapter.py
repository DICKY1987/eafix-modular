# doc_id: DOC-AUTOOPS-054
"""Tests for GitAdapter."""

from pathlib import Path

import pytest

from repo_autoops.git_adapter import GitAdapter


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository."""
    import subprocess
    
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    
    return repo_dir


def test_git_adapter_initialization_dry_run(git_repo: Path):
    """Test git adapter initialization in dry-run mode."""
    adapter = GitAdapter(git_repo, dry_run=True)
    assert adapter.repo_root == git_repo
    assert adapter.dry_run is True


def test_git_adapter_initialization_live(git_repo: Path):
    """Test git adapter initialization in live mode."""
    adapter = GitAdapter(git_repo, dry_run=False)
    assert adapter.dry_run is False


def test_get_current_branch(git_repo: Path):
    """Test getting current branch."""
    import subprocess
    
    # Create an initial commit so HEAD exists
    test_file = git_repo / "initial.txt"
    test_file.write_text("initial")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_repo, check=True, capture_output=True)
    
    adapter = GitAdapter(git_repo, dry_run=False)
    branch = adapter.get_current_branch()
    assert branch in ["master", "main"]  # Git default branch


def test_stage_files_dry_run(git_repo: Path):
    """Test staging files in dry-run mode."""
    adapter = GitAdapter(git_repo, dry_run=True)
    
    test_file = git_repo / "test.txt"
    test_file.write_text("test content")
    
    result = adapter.stage_files([test_file])
    
    assert result.success
    assert "Staged" in result.message
    assert result.metadata["dry_run"] is True


def test_stage_files_live(git_repo: Path):
    """Test staging files in live mode."""
    adapter = GitAdapter(git_repo, dry_run=False)
    
    test_file = git_repo / "test.txt"
    test_file.write_text("test content")
    
    result = adapter.stage_files([test_file])
    
    assert result.success
    assert result.metadata["dry_run"] is False


def test_commit_dry_run(git_repo: Path):
    """Test commit in dry-run mode."""
    adapter = GitAdapter(git_repo, dry_run=True)
    
    test_file = git_repo / "test.txt"
    test_file.write_text("test content")
    adapter.stage_files([test_file])
    
    result = adapter.commit("Test commit")
    
    assert result.success
    assert "DRY RUN" in result.output


def test_create_branch_dry_run(git_repo: Path):
    """Test branch creation in dry-run mode."""
    adapter = GitAdapter(git_repo, dry_run=True)
    
    result = adapter.create_branch("feature/test")
    
    assert result.success
    assert "feature/test" in result.message


def test_check_clean_tree_clean(git_repo: Path):
    """Test clean tree check with clean repo."""
    adapter = GitAdapter(git_repo, dry_run=False)
    
    # New repo should be clean (no files yet)
    is_clean = adapter.check_clean_tree()
    assert is_clean


def test_check_clean_tree_dirty(git_repo: Path):
    """Test clean tree check with dirty repo."""
    adapter = GitAdapter(git_repo, dry_run=False)
    
    # Add a file to make it dirty
    test_file = git_repo / "test.txt"
    test_file.write_text("test content")
    
    is_clean = adapter.check_clean_tree()
    assert not is_clean


def test_stage_empty_list(git_repo: Path):
    """Test staging empty file list."""
    adapter = GitAdapter(git_repo, dry_run=False)
    
    result = adapter.stage_files([])
    
    assert not result.success
    assert "No files" in result.message

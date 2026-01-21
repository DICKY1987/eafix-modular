# doc_id: DOC-AUTOOPS-055
"""Tests for IdentityPipeline."""

from pathlib import Path

import pytest

from repo_autoops.identity_pipeline import IdentityPipeline


def test_identity_pipeline_initialization():
    """Test identity pipeline initialization."""
    pipeline = IdentityPipeline(mode="draft", dry_run=True)
    assert pipeline.mode == "draft"
    assert pipeline.dry_run is True


def test_generate_prefix():
    """Test prefix generation."""
    pipeline = IdentityPipeline()
    
    prefix = pipeline.generate_prefix()
    
    assert len(prefix) == 16
    assert prefix.isdigit()


def test_has_prefix_with_filename_prefix(tmp_path: Path):
    """Test detecting prefix in filename."""
    pipeline = IdentityPipeline()
    
    test_file = tmp_path / "2026012112345678_test.py"
    test_file.write_text("# test")
    
    assert pipeline.has_prefix(test_file)


def test_has_prefix_with_doc_id_header(tmp_path: Path):
    """Test detecting prefix via doc_id in header."""
    pipeline = IdentityPipeline()
    
    test_file = tmp_path / "test.py"
    test_file.write_text("# doc_id: DOC-TEST-001\nprint('test')")
    
    assert pipeline.has_prefix(test_file)


def test_has_prefix_without_prefix(tmp_path: Path):
    """Test detecting no prefix."""
    pipeline = IdentityPipeline()
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    assert not pipeline.has_prefix(test_file)


def test_assign_prefix_dry_run(tmp_path: Path):
    """Test prefix assignment in dry-run mode."""
    pipeline = IdentityPipeline(dry_run=True)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    result = pipeline.assign_prefix(test_file)
    
    assert result.success
    assert "DRY RUN" in result.message
    assert test_file.exists()  # File not actually renamed


def test_assign_prefix_live(tmp_path: Path):
    """Test prefix assignment in live mode."""
    pipeline = IdentityPipeline(dry_run=False)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    result = pipeline.assign_prefix(test_file)
    
    assert result.success
    assert "new_path" in result.metadata
    
    new_path = Path(result.metadata["new_path"])
    assert new_path.exists()
    assert not test_file.exists()  # Original file renamed


def test_assign_prefix_already_has_prefix(tmp_path: Path):
    """Test assigning prefix to file that already has one."""
    pipeline = IdentityPipeline()
    
    test_file = tmp_path / "2026012112345678_test.py"
    test_file.write_text("print('test')")
    
    result = pipeline.assign_prefix(test_file)
    
    assert result.success
    assert "already has prefix" in result.message


def test_assign_doc_id_python_file_dry_run(tmp_path: Path):
    """Test doc_id assignment to Python file in dry-run."""
    pipeline = IdentityPipeline(dry_run=True)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    result = pipeline.assign_doc_id(test_file, "DOC-TEST-001")
    
    assert result.success
    assert "DRY RUN" in result.message


def test_assign_doc_id_python_file_live(tmp_path: Path):
    """Test doc_id assignment to Python file in live mode."""
    pipeline = IdentityPipeline(dry_run=False)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    result = pipeline.assign_doc_id(test_file, "DOC-TEST-001")
    
    assert result.success
    content = test_file.read_text()
    assert "# doc_id: DOC-TEST-001" in content


def test_assign_doc_id_markdown_file(tmp_path: Path):
    """Test doc_id assignment to Markdown file."""
    pipeline = IdentityPipeline(dry_run=False)
    
    test_file = tmp_path / "README.md"
    test_file.write_text("# Test")
    
    result = pipeline.assign_doc_id(test_file, "DOC-TEST-001")
    
    assert result.success
    content = test_file.read_text()
    assert "<!-- doc_id: DOC-TEST-001 -->" in content


def test_assign_doc_id_already_has_doc_id(tmp_path: Path):
    """Test assigning doc_id to file that already has one."""
    pipeline = IdentityPipeline(dry_run=False)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("# doc_id: DOC-EXISTING-001\nprint('test')")
    
    result = pipeline.assign_doc_id(test_file, "DOC-TEST-001")
    
    assert result.success
    assert "already has doc_id" in result.message


def test_assign_doc_id_unsupported_file_type(tmp_path: Path):
    """Test assigning doc_id to unsupported file type."""
    pipeline = IdentityPipeline(dry_run=False)
    
    test_file = tmp_path / "test.exe"
    test_file.write_bytes(b"binary")
    
    result = pipeline.assign_doc_id(test_file, "DOC-TEST-001")
    
    assert not result.success
    assert "Unsupported file type" in result.message


def test_process_file_with_doc_id(tmp_path: Path):
    """Test processing file with both prefix and doc_id."""
    pipeline = IdentityPipeline(dry_run=False)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    result = pipeline.process_file(test_file, doc_id="DOC-TEST-001")
    
    assert result.success

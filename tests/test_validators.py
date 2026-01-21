# doc_id: DOC-AUTOOPS-056
"""Tests for Validators."""

from pathlib import Path

import pytest

from repo_autoops.validators import DocIdValidator, SecretScanner, ValidationRunner


def test_doc_id_validator_initialization():
    """Test doc_id validator initialization."""
    validator = DocIdValidator(required=True)
    assert validator.required is True


def test_doc_id_validator_pass_with_header(tmp_path: Path):
    """Test doc_id validation passes with valid header."""
    validator = DocIdValidator(required=True)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("# doc_id: DOC-TEST-001\nprint('test')")
    
    result = validator.validate(test_file)
    
    assert result.passed
    assert "DOC-TEST-001" in str(result.details)


def test_doc_id_validator_pass_with_variable(tmp_path: Path):
    """Test doc_id validation passes with Python variable."""
    validator = DocIdValidator(required=True)
    
    test_file = tmp_path / "test.py"
    test_file.write_text('__doc_id__ = "DOC-TEST-001"\nprint("test")')
    
    result = validator.validate(test_file)
    
    assert result.passed


def test_doc_id_validator_fail_required(tmp_path: Path):
    """Test doc_id validation fails when required but missing."""
    validator = DocIdValidator(required=True)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    result = validator.validate(test_file)
    
    assert not result.passed
    assert "required" in result.message.lower()


def test_doc_id_validator_pass_not_required(tmp_path: Path):
    """Test doc_id validation passes when not required and missing."""
    validator = DocIdValidator(required=False)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    result = validator.validate(test_file)
    
    assert result.passed


def test_doc_id_validator_skip_unsupported_type(tmp_path: Path):
    """Test doc_id validator skips unsupported file types."""
    validator = DocIdValidator(required=True)
    
    test_file = tmp_path / "test.exe"
    test_file.write_bytes(b"binary")
    
    result = validator.validate(test_file)
    
    assert result.passed
    assert "does not require" in result.message


def test_secret_scanner_initialization():
    """Test secret scanner initialization."""
    scanner = SecretScanner()
    assert len(scanner.patterns) > 0


def test_secret_scanner_detect_password(tmp_path: Path):
    """Test secret scanner detects password."""
    scanner = SecretScanner()
    
    test_file = tmp_path / "config.py"
    test_file.write_text('PASSWORD = "secret123"')
    
    result = scanner.validate(test_file)
    
    assert not result.passed
    assert "secret" in result.message.lower()


def test_secret_scanner_detect_api_key(tmp_path: Path):
    """Test secret scanner detects API key."""
    scanner = SecretScanner()
    
    test_file = tmp_path / "config.py"
    test_file.write_text('API_KEY = "abc123xyz"')
    
    result = scanner.validate(test_file)
    
    assert not result.passed


def test_secret_scanner_detect_private_key(tmp_path: Path):
    """Test secret scanner detects private key."""
    scanner = SecretScanner()
    
    test_file = tmp_path / "key.pem"
    test_file.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEpQIB...")
    
    result = scanner.validate(test_file)
    
    assert not result.passed
    assert "private_key" in str(result.details)


def test_secret_scanner_pass_clean_file(tmp_path: Path):
    """Test secret scanner passes clean file."""
    scanner = SecretScanner()
    
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    return 'world'")
    
    result = scanner.validate(test_file)
    
    assert result.passed


def test_secret_scanner_skip_binary(tmp_path: Path):
    """Test secret scanner skips binary files."""
    scanner = SecretScanner()
    
    test_file = tmp_path / "test.exe"
    test_file.write_bytes(b"\x00\x01\x02")
    
    result = scanner.validate(test_file)
    
    assert result.passed
    assert "skipped" in result.message.lower()


def test_validation_runner_all_passed(tmp_path: Path):
    """Test validation runner with all validators passing."""
    validators = [
        DocIdValidator(required=False),
        SecretScanner(),
    ]
    runner = ValidationRunner(validators)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")
    
    results = runner.validate_file(test_file)
    
    assert len(results) == 2
    assert runner.all_passed(results)


def test_validation_runner_one_failed(tmp_path: Path):
    """Test validation runner with one validator failing."""
    validators = [
        DocIdValidator(required=True),
        SecretScanner(),
    ]
    runner = ValidationRunner(validators)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('test')")  # No doc_id
    
    results = runner.validate_file(test_file)
    
    assert len(results) == 2
    assert not runner.all_passed(results)


def test_validation_runner_with_secret(tmp_path: Path):
    """Test validation runner detects secret."""
    validators = [
        DocIdValidator(required=False),
        SecretScanner(),
    ]
    runner = ValidationRunner(validators)
    
    test_file = tmp_path / "config.py"
    test_file.write_text('API_KEY = "secret123"')
    
    results = runner.validate_file(test_file)
    
    assert not runner.all_passed(results)

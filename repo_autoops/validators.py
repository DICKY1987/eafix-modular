# doc_id: DOC-AUTOOPS-010
"""Validation plugin system."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Protocol

import structlog

from repo_autoops.models.results import ValidationResult

__doc_id__ = "DOC-AUTOOPS-010"

logger = structlog.get_logger(__name__)


class Validator(Protocol):
    """Protocol for validation plugins."""

    def validate(self, path: Path) -> ValidationResult:
        """Validate a file.

        Args:
            path: File path

        Returns:
            ValidationResult
        """
        ...


class DocIdValidator:
    """Validator for doc_id presence and format."""

    def __init__(self, required: bool = False):
        """Initialize validator.

        Args:
            required: If True, require doc_id on all files
        """
        self.required = required

    def validate(self, path: Path) -> ValidationResult:
        """Validate doc_id in file.

        Args:
            path: File path

        Returns:
            ValidationResult
        """
        if not path.exists():
            return ValidationResult(
                passed=False,
                validator_name="doc_id",
                message="File not found",
            )

        # Check if file type supports doc_id
        if path.suffix not in [".py", ".md", ".txt", ".yaml", ".json"]:
            return ValidationResult(
                passed=True,
                validator_name="doc_id",
                message="File type does not require doc_id",
            )

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ValidationResult(
                passed=False,
                validator_name="doc_id",
                message=f"Failed to read file: {e}",
            )

        # Check for doc_id patterns
        patterns = [
            r"#\s*doc_id:\s*(DOC-\w+-\d+)",  # Python/YAML comment
            r"__doc_id__\s*=\s*['\"]?(DOC-\w+-\d+)['\"]?",  # Python variable
            r"<!--\s*doc_id:\s*(DOC-\w+-\d+)\s*-->",  # Markdown/HTML comment
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                doc_id = match.group(1)
                return ValidationResult(
                    passed=True,
                    validator_name="doc_id",
                    message=f"Valid doc_id found: {doc_id}",
                    details={"doc_id": doc_id},
                )

        # No doc_id found
        if self.required:
            return ValidationResult(
                passed=False,
                validator_name="doc_id",
                message="No doc_id found (required)",
                suggestions=["Add doc_id header comment", "Run identity pipeline"],
            )

        return ValidationResult(
            passed=True,
            validator_name="doc_id",
            message="No doc_id found (not required)",
        )


class SecretScanner:
    """Validator for detecting secrets in files."""

    def __init__(self):
        """Initialize secret scanner."""
        self.patterns = [
            (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^'\"\s]+)", "password"),
            (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([^'\"\s]+)", "api_key"),
            (r"(?i)(secret|token)\s*[:=]\s*['\"]?([^'\"\s]+)", "secret"),
            (r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", "private_key"),
            (r"(?i)aws_access_key_id\s*[:=]\s*['\"]?([A-Z0-9]{20})['\"]?", "aws_key"),
        ]

    def validate(self, path: Path) -> ValidationResult:
        """Scan file for secrets.

        Args:
            path: File path

        Returns:
            ValidationResult
        """
        if not path.exists():
            return ValidationResult(
                passed=False,
                validator_name="secret_scanner",
                message="File not found",
            )

        # Skip binary files
        if path.suffix in [".exe", ".dll", ".so", ".dylib", ".pyc", ".db"]:
            return ValidationResult(
                passed=True,
                validator_name="secret_scanner",
                message="Binary file skipped",
            )

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return ValidationResult(
                passed=False,
                validator_name="secret_scanner",
                message=f"Failed to read file: {e}",
            )

        findings = []

        for pattern, secret_type in self.patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                findings.append({
                    "type": secret_type,
                    "line": line_num,
                    "match": match.group(0)[:50],  # Truncate for safety
                })

        if findings:
            return ValidationResult(
                passed=False,
                validator_name="secret_scanner",
                message=f"Found {len(findings)} potential secret(s)",
                details={"findings": findings},
                suggestions=[
                    "Remove hardcoded secrets",
                    "Use environment variables",
                    "Use secret management system",
                ],
            )

        return ValidationResult(
            passed=True,
            validator_name="secret_scanner",
            message="No secrets detected",
        )


class ValidationRunner:
    """Run multiple validators on files."""

    def __init__(self, validators: List[Validator]):
        """Initialize validation runner.

        Args:
            validators: List of validators to run
        """
        self.validators = validators

    def validate_file(self, path: Path) -> List[ValidationResult]:
        """Run all validators on a file.

        Args:
            path: File path

        Returns:
            List of ValidationResults
        """
        results = []

        for validator in self.validators:
            try:
                result = validator.validate(path)
                results.append(result)
                
                if not result.passed:
                    logger.warning(
                        "validation_failed",
                        path=str(path),
                        validator=result.validator_name,
                        message=result.message,
                    )
            except Exception as e:
                logger.error(
                    "validator_error",
                    path=str(path),
                    validator=getattr(validator, "__name__", type(validator).__name__),
                    error=str(e),
                )
                results.append(
                    ValidationResult(
                        passed=False,
                        validator_name="unknown",
                        message=f"Validator error: {e}",
                    )
                )

        return results

    def all_passed(self, results: List[ValidationResult]) -> bool:
        """Check if all validations passed.

        Args:
            results: List of ValidationResults

        Returns:
            True if all passed
        """
        return all(r.passed for r in results)

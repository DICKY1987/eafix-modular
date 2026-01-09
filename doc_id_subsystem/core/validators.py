"""
Per-language validation gates.
Catch syntax errors before applying patches.

Phase 4 optimization - prevents invalid code from being committed
by running compile/parse checks on staged files.
"""
# DOC_ID: DOC-VALIDATORS-COMMON-VALIDATORS-001

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict
import subprocess
import json
import yaml


class Validator(ABC):
    """Base validator interface."""
    
    @abstractmethod
    def validate(self, file_path: Path) -> Dict:
        """
        Validate file syntax.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Dictionary with:
                - validator: Name of validator
                - file: File path
                - passed: Boolean success/failure
                - error: Error message if failed
        """
        pass


class PythonValidator(Validator):
    """Validate Python syntax with py_compile."""
    
    def validate(self, file_path: Path) -> Dict:
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "validator": "python",
                "file": str(file_path),
                "passed": result.returncode == 0,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                "validator": "python",
                "file": str(file_path),
                "passed": False,
                "error": str(e)
            }


class JSONValidator(Validator):
    """Validate JSON syntax."""
    
    def validate(self, file_path: Path) -> Dict:
        try:
            json.loads(file_path.read_text(encoding="utf-8"))
            return {
                "validator": "json",
                "file": str(file_path),
                "passed": True,
                "error": None
            }
        except json.JSONDecodeError as e:
            return {
                "validator": "json",
                "file": str(file_path),
                "passed": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "validator": "json",
                "file": str(file_path),
                "passed": False,
                "error": str(e)
            }


class YAMLValidator(Validator):
    """Validate YAML syntax."""
    
    def validate(self, file_path: Path) -> Dict:
        try:
            yaml.safe_load(file_path.read_text(encoding="utf-8"))
            return {
                "validator": "yaml",
                "file": str(file_path),
                "passed": True,
                "error": None
            }
        except yaml.YAMLError as e:
            return {
                "validator": "yaml",
                "file": str(file_path),
                "passed": False,
                "error": str(e)
            }
        except Exception as e:
            return {
                "validator": "yaml",
                "file": str(file_path),
                "passed": False,
                "error": str(e)
            }


class PowerShellValidator(Validator):
    """Validate PowerShell syntax."""
    
    def validate(self, file_path: Path) -> Dict:
        try:
            # Use PowerShell's AST parser to check syntax
            script = f"[ScriptBlock]::Create((Get-Content -Raw '{file_path}'))"
            result = subprocess.run(
                ["pwsh", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                "validator": "powershell",
                "file": str(file_path),
                "passed": result.returncode == 0,
                "error": result.stderr if result.returncode != 0 else None
            }
        except FileNotFoundError:
            # PowerShell not available - skip validation
            return {
                "validator": "powershell",
                "file": str(file_path),
                "passed": True,
                "error": "PowerShell not available - validation skipped"
            }
        except Exception as e:
            return {
                "validator": "powershell",
                "file": str(file_path),
                "passed": False,
                "error": str(e)
            }


class ValidatorFactory:
    """Factory for creating appropriate validators."""
    
    @staticmethod
    def get_validator(file_ext: str) -> Validator:
        """
        Get appropriate validator for file type.
        
        Args:
            file_ext: File extension (e.g., ".py", ".json")
            
        Returns:
            Validator instance or None if no validator available
        """
        validators = {
            ".py": PythonValidator,
            ".json": JSONValidator,
            ".yaml": YAMLValidator,
            ".yml": YAMLValidator,
            ".ps1": PowerShellValidator,
        }
        validator_class = validators.get(file_ext.lower())
        if validator_class:
            return validator_class()
        return None
    
    @staticmethod
    def get_all_validators() -> Dict[str, Validator]:
        """Get dictionary of all available validators."""
        return {
            ".py": PythonValidator(),
            ".json": JSONValidator(),
            ".yaml": YAMLValidator(),
            ".yml": YAMLValidator(),
            ".ps1": PowerShellValidator(),
        }

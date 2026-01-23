"""
Normalizer

doc_id: DOC-AUTO-DESC-0011
purpose: Automatic normalization on write
phase: Phase 5 - Registry Writer
contract: frozen_contracts.path_contract (relative_path, POSIX format)
"""

from typing import Dict, Any
from pathlib import Path, PurePosixPath


class Normalizer:
    """
    Automatic normalization on registry write.
    
    Contract (Frozen):
    - Paths: Forward-slash (POSIX), repo-relative
    - Enum values: Uppercase (e.g., "FILE" not "file")
    - Timestamps: ISO 8601 with 'Z' suffix
    """
    
    def normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a registry record.
        
        Args:
            record: Registry record dict
            
        Returns:
            Normalized record (new dict, original unchanged)
        """
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def normalize_path(self, path: str) -> str:
        """
        Normalize path to POSIX forward-slash format.
        
        Args:
            path: Path (may be Windows-style with backslashes)
            
        Returns:
            POSIX-style path with forward slashes
            
        Example:
            "repo_autoops\\tools\\example.py" → "repo_autoops/tools/example.py"
        """
        # Convert to PurePosixPath to normalize separators
        return str(PurePosixPath(path))
        
    def normalize_enum(self, value: str) -> str:
        """
        Normalize enum value to uppercase.
        
        Args:
            value: Enum value
            
        Returns:
            Uppercase enum value
            
        Example:
            "file" → "FILE"
            "python" → "PYTHON"
        """
        return value.upper() if value else value
        
    def normalize_timestamp(self, timestamp: str) -> str:
        """
        Ensure timestamp is ISO 8601 with 'Z' suffix.
        
        Args:
            timestamp: Timestamp string
            
        Returns:
            ISO 8601 timestamp with 'Z' suffix
            
        Example:
            "2026-01-23T14:00:00" → "2026-01-23T14:00:00Z"
        """
        if not timestamp:
            return timestamp
        if not timestamp.endswith('Z'):
            return f"{timestamp}Z"
        return timestamp
        
    def normalize_rel_type(self, rel_type: str) -> str:
        """
        Normalize rel_type enum to uppercase.
        
        Args:
            rel_type: Relationship type
            
        Returns:
            Uppercase rel_type
        """
        return self.normalize_enum(rel_type)

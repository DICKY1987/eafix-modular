"""
File Classifier

doc_id: DOC-AUTO-DESC-0007
purpose: File classification (governed/unmanaged, Python/other)
phase: Phase 3 - ID & Rename
"""

from pathlib import Path
from typing import Tuple, Optional, List
import fnmatch


class Classifier:
    """
    Classifies files as governed/unmanaged and by file kind.
    
    Determines:
    1. Is this file in a governed directory?
    2. What type of file is it? (Python, config, doc, etc.)
    3. Should it be processed by this subsystem?
    """
    
    def __init__(
        self,
        governed_directories: List[str],
        ignore_patterns: Optional[List[str]] = None
    ):
        """
        Initialize classifier.
        
        Args:
            governed_directories: List of directories to watch (repo-relative)
            ignore_patterns: Glob patterns to ignore (e.g., "*.pyc", "__pycache__")
        """
        self.governed_directories = governed_directories
        self.ignore_patterns = ignore_patterns or [
            "*.pyc",
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            ".pytest_cache",
            "*.egg-info",
        ]
        
    def classify(self, path: str) -> Tuple[bool, Optional[str], str]:
        """
        Classify a file.
        
        Args:
            path: File path (repo-relative)
            
        Returns:
            (is_governed, file_kind, reason)
            
        file_kind values:
        - "python": .py file
        - "config": .yml, .yaml, .json, .toml
        - "doc": .md, .rst, .txt
        - "other": Other file type
        - None: Not applicable (ignored/unmanaged)
            
        reason values:
        - "governed": File is in governed directory and should be processed
        - "ignored": File matches ignore pattern
        - "unmanaged": File not in governed directory
        - "wrong_type": File type not supported (Phase 1 = Python only)
        """
        # TODO: Implement in Phase 3
        raise NotImplementedError("Phase 3")
        
    def is_governed(self, path: str) -> bool:
        """
        Check if path is in a governed directory.
        
        Args:
            path: File path (repo-relative)
            
        Returns:
            True if path is under a governed directory
        """
        # TODO: Implement in Phase 3
        raise NotImplementedError("Phase 3")
        
    def should_ignore(self, path: str) -> bool:
        """
        Check if path matches any ignore pattern.
        
        Args:
            path: File path
            
        Returns:
            True if path should be ignored
        """
        path_obj = Path(path)
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path_obj.name, pattern):
                return True
            if any(fnmatch.fnmatch(part, pattern) for part in path_obj.parts):
                return True
        return False
        
    def get_file_kind(self, path: str) -> Optional[str]:
        """
        Determine file kind from extension.
        
        Args:
            path: File path
            
        Returns:
            File kind or None if unknown
        """
        suffix = Path(path).suffix.lower()
        
        if suffix == ".py":
            return "python"
        elif suffix in [".yml", ".yaml", ".json", ".toml"]:
            return "config"
        elif suffix in [".md", ".rst", ".txt"]:
            return "doc"
        else:
            return "other"

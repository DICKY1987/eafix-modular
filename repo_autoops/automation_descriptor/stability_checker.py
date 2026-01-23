"""
Stability Checker

doc_id: DOC-AUTO-DESC-0005
purpose: Min-age + mtime/size sampling before processing
phase: Phase 2 - Infrastructure
"""

import os
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta


class StabilityChecker:
    """
    Ensures files are stable before processing.
    
    Strategy:
    1. Min-age: File must exist for at least min_age seconds
    2. Sampling: Check mtime and size at intervals; file must be unchanged
    
    This prevents processing files that are still being written.
    """
    
    def __init__(
        self,
        min_age: float = 0.75,  # 750ms default
        sample_interval: float = 0.1,  # 100ms
        sample_count: int = 3
    ):
        """
        Initialize stability checker.
        
        Args:
            min_age: Minimum age in seconds before file is eligible
            sample_interval: Time between stability samples (seconds)
            sample_count: Number of stable samples required
        """
        self.min_age = min_age
        self.sample_interval = sample_interval
        self.sample_count = sample_count
        self._file_state: Dict[str, Tuple[float, int]] = {}  # path -> (mtime, size)
        
    def check_stability(self, path: str) -> Tuple[bool, str]:
        """
        Check if file is stable enough to process.
        
        Args:
            path: File path to check
            
        Returns:
            (is_stable, reason)
            
        Reasons:
        - "stable": File is ready to process
        - "too_young": File hasn't existed long enough (min_age)
        - "still_changing": File mtime/size is still changing
        - "missing": File doesn't exist
        """
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def record_sample(self, path: str) -> None:
        """
        Record current mtime/size sample for a file.
        
        Args:
            path: File path
        """
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def clear_sample(self, path: str) -> None:
        """Clear recorded samples for a file."""
        if path in self._file_state:
            del self._file_state[path]
            
    def get_file_age(self, path: str) -> Optional[float]:
        """
        Get age of file in seconds.
        
        Args:
            path: File path
            
        Returns:
            Age in seconds, or None if file doesn't exist
        """
        try:
            stat = os.stat(path)
            return datetime.now().timestamp() - stat.st_mtime
        except FileNotFoundError:
            return None
            
    def get_file_signature(self, path: str) -> Optional[Tuple[float, int]]:
        """
        Get (mtime, size) tuple for file.
        
        Args:
            path: File path
            
        Returns:
            (mtime, size) or None if file doesn't exist
        """
        try:
            stat = os.stat(path)
            return (stat.st_mtime, stat.st_size)
        except FileNotFoundError:
            return None

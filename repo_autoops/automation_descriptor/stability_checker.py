#!/usr/bin/env python3
"""
doc_id: 2026012322470007
Stability Checker - File Stability Verification

Prevents processing of files that are still being written/modified.
Uses min-age + mtime/size sampling to detect stability.
"""

import os
import time
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class StabilityChecker:
    """
    Checks if a file is stable (not actively being written).
    
    Strategy:
    1. Min-age check: File must be at least N seconds old
    2. Sampling: Check mtime + size twice with small delay
    """
    
    def __init__(
        self,
        min_age_seconds: float = 2.0,
        sample_interval_seconds: float = 0.5
    ):
        """Initialize stability checker."""
        self.min_age_seconds = min_age_seconds
        self.sample_interval_seconds = sample_interval_seconds
    
    def is_stable(self, path: Path) -> bool:
        """Check if file is stable."""
        if not path.exists():
            return False
        
        try:
            stat = path.stat()
            age = time.time() - stat.st_mtime
            
            if age < self.min_age_seconds:
                logger.debug(f"File too young: {path}")
                return False
            
            initial_mtime = stat.st_mtime
            initial_size = stat.st_size
            
            time.sleep(self.sample_interval_seconds)
            
            if not path.exists():
                return False
            
            final_stat = path.stat()
            
            if initial_mtime != final_stat.st_mtime or initial_size != final_stat.st_size:
                logger.debug(f"File still changing: {path}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking stability: {e}")
            return False

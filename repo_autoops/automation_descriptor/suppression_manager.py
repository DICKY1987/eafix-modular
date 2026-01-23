#!/usr/bin/env python3
"""
doc_id: 2026012322470008
Suppression Manager - Loop Prevention for Self-Induced Events

Tracks operations performed by the system to suppress resulting filesystem events.
"""

import time
import threading
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class SuppressionManager:
    """Tracks self-induced operations to suppress resulting events."""
    
    def __init__(self, suppression_window_seconds: float = 2.0):
        """Initialize suppression manager."""
        self.suppression_window = suppression_window_seconds
        self._suppressions: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def register_operation(self, path: str):
        """Register a self-induced operation."""
        expiry = time.time() + self.suppression_window
        
        with self._lock:
            self._suppressions[path] = expiry
        
        logger.debug(f"Registered suppression: {path}")
    
    def should_suppress(self, path: str) -> bool:
        """Check if event should be suppressed."""
        current_time = time.time()
        
        with self._lock:
            # Clean expired
            expired = [p for p, exp in self._suppressions.items() if exp < current_time]
            for p in expired:
                del self._suppressions[p]
            
            if path in self._suppressions:
                logger.debug(f"Suppressing event: {path}")
                return True
        
        return False
    
    def get_stats(self) -> dict:
        """Get suppression statistics."""
        current_time = time.time()
        
        with self._lock:
            active = sum(1 for exp in self._suppressions.values() if exp >= current_time)
            return {
                "total_tracked": len(self._suppressions),
                "active_suppressions": active
            }

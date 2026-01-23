#!/usr/bin/env python3
"""
doc_id: 2026012322470006
Lock Manager - Fine-grained Locking for Registry Operations

Three lock granularities:
- Path locks: Prevent concurrent operations on same file
- Doc ID locks: Prevent ID allocation races
- Registry lock: Coarse-grained fallback
"""

import threading
import time
from pathlib import Path
from typing import Optional, Set
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class LockManager:
    """
    Thread-safe lock manager with multiple granularities.
    
    Supports:
    - Path-level locks (most common)
    - Doc ID locks (for allocation)
    - Registry-wide lock (for whole-registry operations)
    """
    
    def __init__(self):
        """Initialize lock manager."""
        self._path_locks: Set[str] = set()
        self._doc_id_locks: Set[str] = set()
        self._registry_locked: bool = False
        self._lock = threading.RLock()
    
    @contextmanager
    def path_lock(self, path: str, timeout: float = 30.0):
        """Acquire path-level lock."""
        start = time.time()
        acquired = False
        
        try:
            while time.time() - start < timeout:
                with self._lock:
                    if path not in self._path_locks and not self._registry_locked:
                        self._path_locks.add(path)
                        acquired = True
                        logger.debug(f"Acquired path lock: {path}")
                        break
                time.sleep(0.01)
            
            if not acquired:
                raise TimeoutError(f"Failed to acquire path lock: {path}")
            
            yield
        finally:
            if acquired:
                with self._lock:
                    self._path_locks.discard(path)
    
    @contextmanager
    def doc_id_lock(self, doc_id: str, timeout: float = 10.0):
        """Acquire doc ID lock."""
        start = time.time()
        acquired = False
        
        try:
            while time.time() - start < timeout:
                with self._lock:
                    if doc_id not in self._doc_id_locks and not self._registry_locked:
                        self._doc_id_locks.add(doc_id)
                        acquired = True
                        break
                time.sleep(0.01)
            
            if not acquired:
                raise TimeoutError(f"Failed to acquire doc_id lock: {doc_id}")
            
            yield
        finally:
            if acquired:
                with self._lock:
                    self._doc_id_locks.discard(doc_id)
    
    @contextmanager
    def registry_lock(self, timeout: float = 60.0):
        """Acquire registry-wide lock."""
        start = time.time()
        acquired = False
        
        try:
            while time.time() - start < timeout:
                with self._lock:
                    if not self._registry_locked and len(self._path_locks) == 0 and len(self._doc_id_locks) == 0:
                        self._registry_locked = True
                        acquired = True
                        break
                time.sleep(0.05)
            
            if not acquired:
                raise TimeoutError("Failed to acquire registry lock")
            
            yield
        finally:
            if acquired:
                with self._lock:
                    self._registry_locked = False
    
    def get_stats(self) -> dict:
        """Get lock statistics."""
        with self._lock:
            return {
                "path_locks_held": len(self._path_locks),
                "doc_id_locks_held": len(self._doc_id_locks),
                "registry_locked": self._registry_locked
            }

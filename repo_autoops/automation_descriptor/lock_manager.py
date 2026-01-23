"""
Lock Manager

doc_id: DOC-AUTO-DESC-0003
purpose: Path, doc_id, and registry locks with total ordering
phase: Phase 2 - Infrastructure
contract: frozen_contracts.lock_contract (path_lock → doc_lock → registry_lock)
"""

from pathlib import Path
from typing import Optional, Set
from contextlib import contextmanager
import time
import hashlib


class LockManager:
    """
    File-based lock manager with total ordering.
    
    Contract (Frozen):
    - Total order: path_lock → doc_lock → registry_lock
    - Never acquire path_lock while holding registry_lock (deadlock prevention)
    - Timeout: 30 seconds default
    - Stale recovery: Locks older than 5 minutes forcibly released
    """
    
    def __init__(self, locks_dir: str, timeout: int = 30, stale_threshold: int = 300):
        """
        Initialize lock manager.
        
        Args:
            locks_dir: Base directory for lock files (.dms/runtime/locks/)
            timeout: Lock acquisition timeout in seconds (default: 30)
            stale_threshold: Stale lock threshold in seconds (default: 300 = 5min)
        """
        self.locks_dir = Path(locks_dir)
        self.timeout = timeout
        self.stale_threshold = stale_threshold
        self._held_locks: Set[Path] = set()
        
    def _ensure_lock_dirs(self) -> None:
        """Create lock directories if they don't exist."""
        # TODO: Implement in Phase 2
        # Create: .dms/runtime/locks/path/
        #         .dms/runtime/locks/doc/
        #         .dms/runtime/locks/registry.lock (file, not dir)
        raise NotImplementedError("Phase 2")
        
    def _path_hash(self, path: str) -> str:
        """
        Generate hash for path lock filename.
        
        Args:
            path: File path (repo-relative)
            
        Returns:
            Hash string for lock filename
        """
        return hashlib.sha256(path.encode()).hexdigest()[:16]
        
    def acquire_path_lock(self, path: str) -> bool:
        """
        Acquire lock on specific file path.
        
        Args:
            path: File path (repo-relative, normalized)
            
        Returns:
            True if lock acquired, False if timeout
            
        Contract:
        - Must be acquired FIRST (before doc_lock or registry_lock)
        """
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def acquire_doc_lock(self, doc_id: str) -> bool:
        """
        Acquire lock on specific doc_id.
        
        Args:
            doc_id: 16-digit document identifier
            
        Returns:
            True if lock acquired, False if timeout
            
        Contract:
        - Must be acquired AFTER path_lock, BEFORE registry_lock
        """
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def acquire_registry_lock(self) -> bool:
        """
        Acquire global registry lock.
        
        Returns:
            True if lock acquired, False if timeout
            
        Contract:
        - Must be acquired LAST (after path_lock and doc_lock)
        - This is a global/scarce resource - hold briefly
        """
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def release_path_lock(self, path: str) -> None:
        """Release path lock."""
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def release_doc_lock(self, doc_id: str) -> None:
        """Release doc_id lock."""
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def release_registry_lock(self) -> None:
        """Release global registry lock."""
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def release_all(self) -> None:
        """Release all locks held by this manager."""
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    def check_stale_locks(self) -> int:
        """
        Check for and clean up stale locks.
        
        Returns:
            Number of stale locks removed
        """
        # TODO: Implement in Phase 2
        raise NotImplementedError("Phase 2")
        
    @contextmanager
    def lock_for_processing(self, path: str, doc_id: Optional[str] = None):
        """
        Context manager for acquiring locks in correct order.
        
        Args:
            path: File path
            doc_id: Optional doc_id (if file already has one)
            
        Usage:
            with lock_mgr.lock_for_processing(path, doc_id):
                # Process file
                # Locks released automatically on exit
        """
        # TODO: Implement in Phase 2
        # Acquire: path → doc (if provided) → registry
        # Release: registry → doc → path (reverse order)
        raise NotImplementedError("Phase 2")

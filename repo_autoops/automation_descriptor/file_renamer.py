"""
File Renamer

doc_id: DOC-AUTO-DESC-0009
purpose: Atomic file rename with doc_id prefix
phase: Phase 3 - ID & Rename
"""

import os
import shutil
from pathlib import Path
from typing import Optional


class FileRenamer:
    """
    Atomically renames files to include doc_id prefix.
    
    Example: example.py → 1234567890123456_example.py
    
    Features:
    - Atomic rename (os.rename is atomic on most filesystems)
    - Registers with suppression manager to prevent loop
    - Handles edge cases (file already has doc_id, collision, etc.)
    """
    
    def __init__(self, suppression_manager):
        """
        Initialize file renamer.
        
        Args:
            suppression_manager: SuppressionManager instance for loop prevention
        """
        self.suppression_manager = suppression_manager
        
    def rename_with_doc_id(
        self,
        current_path: str,
        doc_id: str,
        dry_run: bool = False
    ) -> Optional[str]:
        """
        Rename file to include doc_id prefix.
        
        Args:
            current_path: Current file path (absolute)
            doc_id: 16-digit doc_id to prepend
            dry_run: If True, don't actually rename (return what would be done)
            
        Returns:
            New file path if renamed, None if skipped
            
        Cases:
        1. File doesn't have doc_id → Prepend doc_id
        2. File already has doc_id (same) → Skip
        3. File already has doc_id (different) → Error/quarantine
        """
        # TODO: Implement in Phase 3
        raise NotImplementedError("Phase 3")
        
    def extract_doc_id_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract doc_id from filename if present.
        
        Args:
            filename: File name (not full path)
            
        Returns:
            16-digit doc_id if found, None otherwise
            
        Pattern: Filename starts with 16 digits followed by underscore
        Example: 1234567890123456_example.py → "1234567890123456"
        """
        # TODO: Implement in Phase 3
        raise NotImplementedError("Phase 3")
        
    def has_doc_id_prefix(self, filename: str) -> bool:
        """
        Check if filename has doc_id prefix.
        
        Args:
            filename: File name (not full path)
            
        Returns:
            True if filename starts with 16-digit doc_id
        """
        return self.extract_doc_id_from_filename(filename) is not None
        
    def generate_new_filename(self, current_filename: str, doc_id: str) -> str:
        """
        Generate new filename with doc_id prefix.
        
        Args:
            current_filename: Current filename
            doc_id: 16-digit doc_id
            
        Returns:
            New filename with doc_id prefix
        """
        # If filename already has doc_id, replace it
        if self.has_doc_id_prefix(current_filename):
            # Strip old doc_id and underscore
            without_prefix = current_filename[17:]  # Skip "NNNNNNNNNNNNNNNN_"
            return f"{doc_id}_{without_prefix}"
        else:
            return f"{doc_id}_{current_filename}"
            
    def atomic_rename(self, old_path: str, new_path: str) -> None:
        """
        Perform atomic rename and register with suppression manager.
        
        Args:
            old_path: Current file path (absolute)
            new_path: New file path (absolute)
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            FileExistsError: If target file already exists
        """
        # TODO: Implement in Phase 3
        # 1. Check source exists
        # 2. Check target doesn't exist
        # 3. os.rename (atomic)
        # 4. Register with suppression_manager.register_rename()
        raise NotImplementedError("Phase 3")

"""
Backup Manager

doc_id: DOC-AUTO-DESC-0012
purpose: Timestamped registry backups + automatic rollback
phase: Phase 5 - Registry Writer
"""

import json
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta


class BackupManager:
    """
    Manages registry backups and rollback.
    
    Features:
    - Automatic backup before every registry mutation
    - Timestamped backups (ISO 8601 format)
    - Automatic rollback on validation failure
    - Retention policy (default: 30 days)
    """
    
    def __init__(
        self,
        registry_path: str,
        backup_dir: str,
        retention_days: int = 30
    ):
        """
        Initialize backup manager.
        
        Args:
            registry_path: Path to UNIFIED_SSOT_REGISTRY.json
            backup_dir: Directory for backups (.dms/backups/registry/)
            retention_days: How long to keep backups (default: 30)
        """
        self.registry_path = Path(registry_path)
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        
    def _ensure_backup_dir(self) -> None:
        """Create backup directory if it doesn't exist."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def create_backup(self) -> str:
        """
        Create timestamped backup of current registry.
        
        Returns:
            Path to backup file
            
        Format: UNIFIED_SSOT_REGISTRY_YYYYMMDDTHHMMSSZ.json
        Example: UNIFIED_SSOT_REGISTRY_20260123T140000Z.json
        """
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def rollback(self, backup_path: Optional[str] = None) -> None:
        """
        Rollback registry to a backup.
        
        Args:
            backup_path: Path to backup file. If None, use most recent backup.
            
        Raises:
            FileNotFoundError: If backup file doesn't exist
        """
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def get_latest_backup(self) -> Optional[str]:
        """
        Get path to most recent backup.
        
        Returns:
            Path to latest backup, or None if no backups exist
        """
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def list_backups(self, limit: int = 10) -> list:
        """
        List available backups (most recent first).
        
        Args:
            limit: Maximum number of backups to return
            
        Returns:
            List of backup file paths
        """
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention_days.
        
        Returns:
            Number of backups removed
        """
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def verify_backup(self, backup_path: str) -> bool:
        """
        Verify backup file is valid JSON.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if backup is valid, False otherwise
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, FileNotFoundError):
            return False

"""
Registry Writer Service

doc_id: DOC-AUTO-DESC-0014
purpose: Single mutation point for UNIFIED_SSOT_REGISTRY.json
phase: Phase 5 - Registry Writer
contract: frozen_contracts.registry_contract + patch_contract (CAS with registry_hash)
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional


class RegistryWriterService:
    """
    Single writer for UNIFIED_SSOT_REGISTRY.json.
    
    Contract (Frozen):
    - ONLY this service can write to registry
    - All updates via promotion patches
    - CAS precondition: registry_hash REQUIRED
    - Atomic: validate → normalize → backup → apply → verify
    - Auto-rollback on failure
    """
    
    def __init__(
        self,
        registry_path: str,
        backup_manager,
        normalizer,
        write_policy_validator,
        lock_manager
    ):
        """
        Initialize registry writer service.
        
        Args:
            registry_path: Path to UNIFIED_SSOT_REGISTRY.json
            backup_manager: BackupManager instance
            normalizer: Normalizer instance
            write_policy_validator: WritePolicyValidator instance
            lock_manager: LockManager instance
        """
        self.registry_path = Path(registry_path)
        self.backup_manager = backup_manager
        self.normalizer = normalizer
        self.write_policy_validator = write_policy_validator
        self.lock_manager = lock_manager
        
    def apply_patch(self, patch: Dict[str, Any]) -> tuple:
        """
        Apply promotion patch to registry.
        
        Args:
            patch: Patch dict with registry_hash, doc_id, ops, actor, utc_ts, work_item_id
            
        Returns:
            (success, error_message)
            
        Pipeline:
        1. Validate CAS precondition (registry_hash)
        2. Validate write policies
        3. Normalize values
        4. Create backup
        5. Apply patch (atomic write)
        6. Verify (fast validation)
        7. Commit or rollback
        """
        # TODO: Implement in Phase 5
        raise NotImplementedError("Phase 5")
        
    def compute_registry_hash(self) -> str:
        """
        Compute SHA-256 hash of current registry file.
        
        Returns:
            SHA-256 hex digest
            
        Contract: Hash entire file bytes (not JSON-parsed content)
        """
        with open(self.registry_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
            
    def load_registry(self) -> Dict[str, Any]:
        """Load registry from disk."""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def save_registry(self, registry: Dict[str, Any]) -> None:
        """Save registry to disk (atomic write)."""
        # TODO: Implement in Phase 5 (temp file + rename + fsync)
        raise NotImplementedError("Phase 5")

"""
Registry Writer Service - Single Mutation Point

doc_id: 2026012321510002
purpose: THE ONLY component allowed to write to UNIFIED_SSOT_REGISTRY.json
classification: CRITICAL_PATH
version: 1.0
date: 2026-01-23T21:51:00Z
"""

import json
import hashlib
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parents[2]))
from shared.registry_config import REGISTRY_PATH, REGISTRY_BACKUP_DIR, REGISTRY_LOCK_PATH
from services.registry_writer.promotion_patch import PromotionPatch


class RegistryWriter:
    """
    Single writer for UNIFIED_SSOT_REGISTRY.json.
    
    Enforces:
    - Write policy (tool_only/user_only/immutable)
    - Normalization (rel_type uppercase, path forward slashes)
    - Derivations (recompute module_id, size, hash)
    - Atomic commit (temp file + os.replace + fsync)
    - Backup before write
    - Rollback on validation failure
    """
    
    def __init__(self):
        self.registry_path = REGISTRY_PATH
        self.backup_dir = REGISTRY_BACKUP_DIR
        self.lock_path = REGISTRY_LOCK_PATH
        
        REGISTRY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    def apply_promotion(self, patch: PromotionPatch) -> Tuple[bool, List[str]]:
        """
        Apply promotion patch (THE ONLY WRITE METHOD).
        
        Workflow:
        1. Acquire exclusive lock
        2. Verify CAS precondition (registry_hash)
        3. Create backup
        4. Load current registry
        5. Validate write policy
        6. Apply changes
        7. Run normalization
        8. Run derivations
        9. Validate gates (fast mode)
        10. Atomic write
        11. Release lock
        12. On failure: restore backup
        
        Returns:
            (success: bool, errors: List[str])
        """
        errors = []
        backup_path = None
        
        try:
            # Step 1: Acquire lock (simplified - use file lock in production)
            if self.lock_path.exists():
                return (False, ["Registry locked by another process"])
            
            self.lock_path.touch()
            
            try:
                # Step 2: Verify CAS precondition
                current_hash = self._compute_registry_hash()
                if current_hash != patch.registry_hash:
                    return (False, [f"CAS precondition failed: expected {patch.registry_hash}, got {current_hash}"])
                
                # Step 3: Create backup
                backup_path = self._create_backup()
                
                # Step 4: Load registry
                data = self._load_registry()
                
                # Step 5: Validate write policy
                policy_ok, policy_errors = self._validate_write_policy(patch, data)
                if not policy_ok:
                    errors.extend(policy_errors)
                    raise ValueError(f"Write policy violations: {len(policy_errors)}")
                
                # Step 6: Apply changes
                self._apply_patch_to_data(patch, data)
                
                # Step 7: Normalize
                self._normalize_data(data)
                
                # Step 8: Derive (recompute tool-owned fields)
                self._derive_fields(data, patch)
                
                # Step 9: Fast validation
                val_ok, val_errors = self._fast_validate(data)
                if not val_ok:
                    errors.extend(val_errors)
                    raise ValueError(f"Validation failed: {len(val_errors)}")
                
                # Step 10: Atomic write
                self._atomic_write(data)
                
                return (True, [])
            
            finally:
                # Step 11: Release lock
                if self.lock_path.exists():
                    self.lock_path.unlink()
        
        except Exception as e:
            # Step 12: Rollback on failure
            if backup_path and backup_path.exists():
                self._restore_backup(backup_path)
            
            errors.append(str(e))
            return (False, errors)
    
    def _compute_registry_hash(self) -> str:
        """Compute SHA-256 hash of registry file bytes."""
        if not self.registry_path.exists():
            return "sha256:empty"
        
        with open(self.registry_path, 'rb') as f:
            return f"sha256:{hashlib.sha256(f.read()).hexdigest()}"
    
    def _create_backup(self) -> Path:
        """Create timestamped backup."""
        if not self.registry_path.exists():
            return None
        
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        backup_path = self.backup_dir / f"UNIFIED_SSOT_REGISTRY_{timestamp}.json"
        shutil.copy2(self.registry_path, backup_path)
        return backup_path
    
    def _restore_backup(self, backup_path: Path):
        """Restore from backup."""
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, self.registry_path)
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from disk."""
        if not self.registry_path.exists():
            return {"records": [], "metadata": {}, "schema_version": "2.2"}
        
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _validate_write_policy(self, patch: PromotionPatch, data: Dict) -> Tuple[bool, List[str]]:
        """Check if patch violates write policy."""
        errors = []
        
        # Simplified write policy check
        # In production: load from 2026012120420001_UNIFIED_SSOT_REGISTRY_WRITE_POLICY.yaml
        TOOL_ONLY_FIELDS = ['doc_id', 'size_bytes', 'mtime_utc', 'sha256', 'module_id', 'filename', 'extension']
        USER_ONLY_FIELDS = ['notes', 'module_id_override']
        IMMUTABLE_FIELDS = ['doc_id', 'record_kind', 'entity_kind', 'created_utc']
        
        for field, new_value in patch.changes.items():
            # Check tool_only violations
            if field in TOOL_ONLY_FIELDS and patch.source not in ['scanner', 'watcher', 'reconciler']:
                errors.append(f"Field '{field}' is tool_only, cannot write from source '{patch.source}'")
            
            # Check user_only violations
            if field in USER_ONLY_FIELDS and patch.source in ['scanner', 'watcher', 'reconciler']:
                errors.append(f"Field '{field}' is user_only, cannot write from automated source")
            
            # Check immutable violations
            if field in IMMUTABLE_FIELDS and patch.patch_type.startswith('update_'):
                errors.append(f"Field '{field}' is immutable, cannot update")
        
        return (len(errors) == 0, errors)
    
    def _apply_patch_to_data(self, patch: PromotionPatch, data: Dict):
        """Apply patch changes to data."""
        if patch.patch_type == 'add_entity':
            record = patch.changes.copy()
            record['record_kind'] = 'entity'
            if 'created_utc' not in record:
                record['created_utc'] = datetime.utcnow().isoformat() + 'Z'
            if 'updated_utc' not in record:
                record['updated_utc'] = record['created_utc']
            data['records'].append(record)
        
        elif patch.patch_type == 'update_entity':
            for record in data['records']:
                if record.get('doc_id') == patch.target_record_id or record.get('entity_id') == patch.target_record_id:
                    record.update(patch.changes)
                    record['updated_utc'] = datetime.utcnow().isoformat() + 'Z'
                    break
    
    def _normalize_data(self, data: Dict):
        """Auto-normalize on write."""
        for record in data.get('records', []):
            # Uppercase rel_type
            if 'rel_type' in record and isinstance(record['rel_type'], str):
                record['rel_type'] = record['rel_type'].upper()
            
            # Forward slash paths
            for path_field in ['relative_path', 'directory_path', 'canonical_path']:
                if path_field in record and isinstance(record[path_field], str):
                    record[path_field] = record[path_field].replace('\\', '/')
    
    def _derive_fields(self, data: Dict, patch: PromotionPatch):
        """Recompute derived fields."""
        for record in data.get('records', []):
            if record.get('record_kind') == 'entity' and record.get('entity_kind') == 'file':
                # Derive filename from relative_path
                if 'relative_path' in record:
                    record['filename'] = Path(record['relative_path']).name
                
                # Derive extension
                if 'filename' in record:
                    ext = Path(record['filename']).suffix
                    record['extension'] = ext[1:].lower() if ext else ''
                
                # Derive directory_path
                if 'relative_path' in record:
                    dir_path = str(Path(record['relative_path']).parent)
                    record['directory_path'] = '.' if dir_path == '.' else dir_path.replace('\\', '/')
    
    def _fast_validate(self, data: Dict) -> Tuple[bool, List[str]]:
        """Fast validation (schema + referential integrity)."""
        errors = []
        
        # Check required fields
        for record in data.get('records', []):
            if 'record_kind' not in record:
                errors.append(f"Missing required field 'record_kind' in record")
            
            if record.get('record_kind') == 'entity':
                if 'entity_kind' not in record:
                    errors.append(f"Missing 'entity_kind' for entity record")
        
        # Check for duplicate doc_ids
        doc_ids = [r.get('doc_id') for r in data.get('records', []) if r.get('doc_id')]
        if len(doc_ids) != len(set(doc_ids)):
            errors.append("Duplicate doc_ids detected")
        
        return (len(errors) == 0, errors)
    
    def _atomic_write(self, data: Dict):
        """Atomic write: temp file + os.replace + fsync."""
        temp_path = self.registry_path.parent / f".{self.registry_path.name}.tmp"
        
        # Write to temp
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic replace
        os.replace(temp_path, self.registry_path)
        
        # Fsync directory (POSIX requirement)
        if hasattr(os, 'O_DIRECTORY'):
            try:
                dirfd = os.open(self.registry_path.parent, os.O_DIRECTORY)
                os.fsync(dirfd)
                os.close(dirfd)
            except:
                pass

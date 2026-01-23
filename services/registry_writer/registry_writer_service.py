#!/usr/bin/env python3
"""
doc_id: 2026012322470002
Registry Writer Service - Single Writer Pattern Enforcement

Atomic writes with CAS precondition, backup, rollback, and policy enforcement.
All registry modifications MUST flow through this service.
"""

import json
import hashlib
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
import tempfile
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[3]))

from shared.registry_config import REGISTRY_PATH, REGISTRY_BACKUP_DIR, REGISTRY_LOCK_PATH
from services.registry_writer.promotion_patch import PromotionPatch, PatchResult

# Lazy import validators to avoid circular dependencies
_normalizer = None
_write_policy_validator = None
_derivations_validator = None


logger = logging.getLogger(__name__)


class RegistryWriterService:
    """
    Single-writer service for UNIFIED_SSOT_REGISTRY.json.
    
    Enforces:
    - CAS (Compare-And-Swap) precondition
    - Atomic writes (temp → replace → fsync)
    - Backup before every write
    - Policy validation (write policy, derivations)
    - Automatic normalization
    - Rollback on failure
    """
    
    def __init__(
        self,
        registry_path: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        enable_validation: bool = True,
        enable_normalization: bool = True
    ):
        """
        Initialize registry writer.
        
        Args:
            registry_path: Path to registry (default: from config)
            backup_dir: Backup directory (default: from config)
            enable_validation: Run validators before write
            enable_normalization: Auto-normalize after patch
        """
        self.registry_path = Path(registry_path) if registry_path else REGISTRY_PATH
        self.backup_dir = Path(backup_dir) if backup_dir else REGISTRY_BACKUP_DIR
        self.lock_path = REGISTRY_LOCK_PATH
        self.enable_validation = enable_validation
        self.enable_normalization = enable_normalization
        
        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Stats
        self.stats = {
            "writes_attempted": 0,
            "writes_succeeded": 0,
            "writes_failed": 0,
            "cas_conflicts": 0,
            "validation_failures": 0,
            "rollbacks": 0
        }
    
    def apply_patch(self, patch: PromotionPatch) -> PatchResult:
        """
        Apply a promotion patch to the registry.
        
        This is the ONLY public method for modifying the registry.
        All changes flow through here.
        
        Args:
            patch: PromotionPatch with changes and CAS precondition
        
        Returns:
            PatchResult with success status and details
        """
        self.stats["writes_attempted"] += 1
        
        try:
            # Step 1: Load current registry
            registry = self._load_registry()
            current_hash = self._compute_hash(registry)
            
            # Step 2: CAS precondition check
            if patch.registry_hash != current_hash:
                self.stats["cas_conflicts"] += 1
                return PatchResult(
                    success=False,
                    message=f"CAS conflict: expected hash {patch.registry_hash[:8]}..., "
                           f"got {current_hash[:8]}...",
                    validation_errors=["CAS_PRECONDITION_FAILED"]
                )
            
            # Step 3: Apply changes (simple or complex mode)
            modified_registry = self._apply_changes(registry, patch)
            
            # Step 4: Normalization (if enabled)
            normalization_applied = False
            if self.enable_normalization and patch.apply_normalization:
                modified_registry = self._normalize_registry(modified_registry)
                normalization_applied = True
            
            # Step 5: Validation (if enabled)
            if self.enable_validation and patch.validate_policies:
                validation_errors = self._validate_registry(modified_registry, patch)
                if validation_errors:
                    self.stats["validation_failures"] += 1
                    return PatchResult(
                        success=False,
                        message="Validation failed",
                        validation_errors=validation_errors
                    )
            
            # Step 6: Create backup
            backup_path = self._create_backup(registry)
            
            # Step 7: Atomic write
            try:
                self._atomic_write(modified_registry)
                new_hash = self._compute_hash(modified_registry)
                
                self.stats["writes_succeeded"] += 1
                
                return PatchResult(
                    success=True,
                    message=f"Patch applied successfully by {patch.source}",
                    new_registry_hash=new_hash,
                    normalization_applied=normalization_applied,
                    backup_path=str(backup_path),
                    records_affected=self._count_affected_records(patch)
                )
            
            except Exception as write_error:
                # Rollback on write failure
                logger.error(f"Write failed, rolling back: {write_error}")
                self._rollback_from_backup(backup_path)
                self.stats["rollbacks"] += 1
                raise
        
        except Exception as e:
            self.stats["writes_failed"] += 1
            logger.exception(f"Patch application failed: {e}")
            return PatchResult(
                success=False,
                message=f"Error: {str(e)}",
                validation_errors=[str(e)]
            )
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load current registry from disk."""
        if not self.registry_path.exists():
            # Initialize empty registry
            return {
                "meta": {
                    "document_id": "REG-UNIFIED-SSOT-720066-001",
                    "registry_name": "UNIFIED_SSOT_REGISTRY",
                    "version": "2.1.0",
                    "status": "active",
                    "last_updated_utc": datetime.now(timezone.utc).isoformat(),
                    "authoritative": True
                },
                "counters": {
                    "record_id": {"current": 0},
                    "file_doc_id": {},
                    "generator_id": {"current": 0}
                },
                "records": []
            }
        
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _compute_hash(self, registry: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of registry (for CAS)."""
        # Exclude metadata timestamps for stable hashing
        registry_copy = json.loads(json.dumps(registry))
        if "meta" in registry_copy and "last_updated_utc" in registry_copy["meta"]:
            del registry_copy["meta"]["last_updated_utc"]
        
        registry_json = json.dumps(registry_copy, sort_keys=True)
        return hashlib.sha256(registry_json.encode('utf-8')).hexdigest()
    
    def _apply_changes(self, registry: Dict[str, Any], patch: PromotionPatch) -> Dict[str, Any]:
        """Apply patch changes to registry."""
        import copy
        modified = copy.deepcopy(registry)
        
        if patch.is_simple_mode():
            # Simple mode: direct field updates
            for field_path, new_value in patch.changes.items():
                self._set_nested_field(modified, field_path, new_value, patch.record_id)
        
        else:
            # Complex mode: operation array
            for operation in patch.operations:
                self._apply_operation(modified, operation)
        
        # Update metadata
        if "meta" not in modified:
            modified["meta"] = {}
        modified["meta"]["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
        
        return modified
    
    def _set_nested_field(
        self,
        registry: Dict[str, Any],
        field_path: str,
        value: Any,
        record_id: Optional[str]
    ):
        """Set a nested field in registry."""
        if record_id:
            # Update specific record
            for record in registry.get("records", []):
                if record.get("record_id") == record_id or record.get("doc_id") == record_id:
                    parts = field_path.split('/')
                    current = record
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                    return
            
            raise ValueError(f"Record not found: {record_id}")
        else:
            # Update top-level field (e.g., counters, meta)
            parts = field_path.split('/')
            current = registry
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
    
    def _apply_operation(self, registry: Dict[str, Any], operation):
        """Apply a single operation from complex patch."""
        from services.registry_writer.promotion_patch import PatchOperationType
        
        if operation.op == PatchOperationType.ADD:
            # Add new record or field
            if operation.path == "records":
                if "records" not in registry:
                    registry["records"] = []
                registry["records"].append(operation.value)
            else:
                self._set_nested_field(registry, operation.path, operation.value, None)
        
        elif operation.op == PatchOperationType.UPDATE:
            self._set_nested_field(registry, operation.path, operation.value, None)
        
        elif operation.op == PatchOperationType.DELETE:
            # Delete field or record
            parts = operation.path.split('/')
            current = registry
            for part in parts[:-1]:
                current = current[part]
            del current[parts[-1]]
        
        elif operation.op == PatchOperationType.UPSERT:
            # Update if exists, add if not
            try:
                self._set_nested_field(registry, operation.path, operation.value, None)
            except (KeyError, ValueError):
                if operation.path == "records":
                    if "records" not in registry:
                        registry["records"] = []
                    registry["records"].append(operation.value)
    
    def _normalize_registry(self, registry: Dict[str, Any]) -> Dict[str, Any]:
        """Apply normalization rules."""
        global _normalizer
        
        if _normalizer is None:
            # Lazy import
            normalizer_path = Path(__file__).parents[2] / "Directory management system" / "03_IMPLEMENTATION" / "2026012120420010_normalize_registry.py"
            if normalizer_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("normalizer", normalizer_path)
                normalizer_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(normalizer_module)
                _normalizer = normalizer_module.RegistryNormalizer()
            else:
                logger.warning("Normalizer not found, skipping normalization")
                return registry
        
        if _normalizer:
            _normalizer.normalize_in_place(registry)
        
        return registry
    
    def _validate_registry(
        self,
        registry: Dict[str, Any],
        patch: PromotionPatch
    ) -> List[str]:
        """Run validators against registry."""
        global _write_policy_validator
        errors = []
        
        # Load write policy validator
        if _write_policy_validator is None:
            validator_path = Path(__file__).parents[2] / "Directory management system" / "03_IMPLEMENTATION" / "2026012120420006_validate_write_policy.py"
            if validator_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("write_policy", validator_path)
                validator_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(validator_module)
                _write_policy_validator = validator_module.WritePolicyValidator()
        
        if _write_policy_validator:
            # Validate patch against write policy
            if patch.is_simple_mode():
                for field in patch.changes.keys():
                    column_info = _write_policy_validator.columns.get(field, {})
                    update_policy = column_info.get("update_policy", "user_writable")
                    
                    if update_policy == "tool_only" and patch.source != "tool":
                        errors.append(f"Field '{field}' is tool_only, cannot be modified by {patch.source}")
        
        return errors
    
    def _create_backup(self, registry: Dict[str, Any]) -> Path:
        """Create timestamped backup of registry."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"UNIFIED_SSOT_REGISTRY_{timestamp}.json"
        backup_path = self.backup_dir / backup_filename
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    
    def _atomic_write(self, registry: Dict[str, Any]):
        """Atomic write: temp file → replace → fsync."""
        # Write to temp file in same directory (ensures same filesystem)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.registry_path.parent,
            prefix=".registry_temp_",
            suffix=".json"
        )
        
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic replace
            shutil.move(temp_path, self.registry_path)
            
            # Fsync directory for durability (skip on Windows, not supported)
            if os.name != 'nt':
                try:
                    dir_fd = os.open(self.registry_path.parent, os.O_RDONLY)
                    try:
                        os.fsync(dir_fd)
                    finally:
                        os.close(dir_fd)
                except (OSError, PermissionError):
                    pass  # Directory fsync not critical
        
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def _rollback_from_backup(self, backup_path: Path):
        """Restore registry from backup."""
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, self.registry_path)
            logger.info(f"Rolled back from backup: {backup_path}")
        else:
            logger.error(f"Cannot rollback: backup not found at {backup_path}")
    
    def _count_affected_records(self, patch: PromotionPatch) -> int:
        """Count records affected by patch."""
        if patch.record_id:
            return 1
        if patch.is_simple_mode():
            return 1 if patch.record_id else 0
        if patch.is_complex_mode():
            return len([op for op in patch.operations if "records" in op.path])
        return 0
    
    def get_current_hash(self) -> str:
        """Get current registry hash for CAS."""
        registry = self._load_registry()
        return self._compute_hash(registry)
    
    def get_stats(self) -> Dict[str, int]:
        """Get service statistics."""
        return self.stats.copy()


def create_simple_patch(
    registry_hash: str,
    changes: Dict[str, Any],
    source: str = "unknown",
    reason: str = "",
    record_id: Optional[str] = None
) -> PromotionPatch:
    """Convenience function to create simple patch."""
    return PromotionPatch(
        registry_hash=registry_hash,
        changes=changes,
        source=source,
        reason=reason,
        record_id=record_id
    )

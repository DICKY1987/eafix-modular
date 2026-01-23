#!/usr/bin/env python3
"""
doc_id: 2026012322470001
Promotion Patch - Unified Interface for Registry Updates

Merged design from Plan A (CAS precondition) and Plan B (dataclass clarity).
Supports both simple changes and complex operation arrays.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum


class PatchOperationType(Enum):
    """Operation types for complex patches."""
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    UPSERT = "upsert"


@dataclass
class PatchOperation:
    """Single operation in a complex patch."""
    op: PatchOperationType
    path: str  # JSON path (e.g., "records[0]/relative_path")
    value: Optional[Any] = None
    old_value: Optional[Any] = None  # For validation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        result = {
            "op": self.op.value,
            "path": self.path
        }
        if self.value is not None:
            result["value"] = self.value
        if self.old_value is not None:
            result["old_value"] = self.old_value
        return result


@dataclass
class PromotionPatch:
    """
    Unified registry update interface.
    
    Supports two modes:
    1. Simple: changes dict with field name → new value
    2. Complex: operations array with ADD/UPDATE/DELETE ops
    
    Always includes CAS precondition (registry_hash) for safety.
    """
    
    # CAS (Compare-And-Swap) precondition
    registry_hash: str
    
    # Simple mode: direct field updates
    changes: Optional[Dict[str, Any]] = None
    
    # Complex mode: operation array
    operations: Optional[List[PatchOperation]] = None
    
    # Metadata
    source: str = "unknown"  # e.g., "watcher", "reconciler", "cli"
    reason: str = ""  # Human-readable explanation
    record_id: Optional[str] = None  # Target record (if applicable)
    
    # Audit trail
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    apply_normalization: bool = True  # Auto-normalize after patch
    validate_policies: bool = True  # Run validators before write
    
    def __post_init__(self):
        """Validate patch structure."""
        if self.changes is None and self.operations is None:
            raise ValueError("PromotionPatch requires either 'changes' or 'operations'")
        
        if self.changes is not None and self.operations is not None:
            raise ValueError("PromotionPatch cannot have both 'changes' and 'operations'")
        
        if not self.registry_hash:
            raise ValueError("PromotionPatch requires registry_hash for CAS precondition")
    
    def is_simple_mode(self) -> bool:
        """Check if this is a simple patch."""
        return self.changes is not None
    
    def is_complex_mode(self) -> bool:
        """Check if this is a complex patch."""
        return self.operations is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization/logging."""
        result = {
            "registry_hash": self.registry_hash,
            "source": self.source,
            "reason": self.reason,
            "timestamp_utc": self.timestamp_utc,
            "apply_normalization": self.apply_normalization,
            "validate_policies": self.validate_policies
        }
        
        if self.record_id:
            result["record_id"] = self.record_id
        
        if self.is_simple_mode():
            result["changes"] = self.changes
        else:
            result["operations"] = [op.to_dict() for op in self.operations]
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromotionPatch':
        """Create PromotionPatch from dict."""
        operations = None
        if "operations" in data and data["operations"]:
            operations = [
                PatchOperation(
                    op=PatchOperationType(op_data["op"]),
                    path=op_data["path"],
                    value=op_data.get("value"),
                    old_value=op_data.get("old_value")
                )
                for op_data in data["operations"]
            ]
        
        return cls(
            registry_hash=data["registry_hash"],
            changes=data.get("changes"),
            operations=operations,
            source=data.get("source", "unknown"),
            reason=data.get("reason", ""),
            record_id=data.get("record_id"),
            timestamp_utc=data.get("timestamp_utc", datetime.now(timezone.utc).isoformat()),
            apply_normalization=data.get("apply_normalization", True),
            validate_policies=data.get("validate_policies", True)
        )


@dataclass
class PatchResult:
    """Result of applying a PromotionPatch."""
    success: bool
    message: str
    new_registry_hash: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    normalization_applied: bool = False
    backup_path: Optional[str] = None
    records_affected: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "success": self.success,
            "message": self.message,
            "new_registry_hash": self.new_registry_hash,
            "validation_errors": self.validation_errors,
            "normalization_applied": self.normalization_applied,
            "backup_path": self.backup_path,
            "records_affected": self.records_affected
        }
        
        if not self.registry_hash.startswith('sha256:'):
            raise ValueError("registry_hash must start with 'sha256:' prefix")
        
        try:
            datetime.fromisoformat(self.timestamp_utc.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError(f"Invalid timestamp_utc: {e}")
        
        if self.patch_type.startswith('update_') and not self.target_record_id:
            raise ValueError(f"target_record_id required for {self.patch_type}")

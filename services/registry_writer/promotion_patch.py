"""
Promotion Patch Data Structure

doc_id: 2026012321510001
purpose: Merged interface (Plan A CAS + Plan B dataclass)
classification: CORE_CONTRACT
version: 1.0
date: 2026-01-23T21:51:00Z
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class PromotionPatch:
    """
    Intent to modify registry. Never applied directly.
    
    Merged design resolving Plan A vs Plan B conflict:
    - Plan B: Clear dataclass structure (patch_type, rationale)
    - Plan A: CAS safety (registry_hash) + correlation (work_item_id)
    
    All registry updates MUST go through RegistryWriter.apply_promotion()
    """
    
    patch_id: str
    patch_type: str
    target_record_id: Optional[str]
    changes: Dict[str, Any]
    source: str
    timestamp_utc: str
    rationale: str
    registry_hash: str
    work_item_id: Optional[str] = None
    ops: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        valid_types = [
            'add_entity', 'update_entity', 'delete_entity',
            'add_edge', 'update_edge', 'delete_edge',
            'add_generator', 'update_generator',
            'add_transient', 'update_transient'
        ]
        if self.patch_type not in valid_types:
            raise ValueError(f"Invalid patch_type: {self.patch_type}")
        
        valid_sources = ['watcher', 'manual', 'scanner', 'validator', 'reconciler', 'generator']
        if self.source not in valid_sources:
            raise ValueError(f"Invalid source: {self.source}")
        
        if not self.registry_hash.startswith('sha256:'):
            raise ValueError("registry_hash must start with 'sha256:' prefix")
        
        try:
            datetime.fromisoformat(self.timestamp_utc.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError(f"Invalid timestamp_utc: {e}")
        
        if self.patch_type.startswith('update_') and not self.target_record_id:
            raise ValueError(f"target_record_id required for {self.patch_type}")

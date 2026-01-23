"""
doc_id: 2026012320030001
Registry Configuration - Single Source of Truth for Registry Paths

This module defines the authoritative registry paths used across all components.
All registry-related code MUST import paths from this module.

Usage:
    from shared.registry_config import REGISTRY_PATH, REGISTRY_BACKUP_DIR
    
    # Load registry
    with open(REGISTRY_PATH, 'r') as f:
        data = json.load(f)
"""

from pathlib import Path

# Root directory of the project
PROJECT_ROOT = Path(__file__).parents[1]

# Registry root directory
REGISTRY_ROOT = PROJECT_ROOT / "Directory management system" / "02_DOCUMENTATION" / "id_16_digit" / "registry"

# Single unified registry file (AUTHORITATIVE)
REGISTRY_PATH = REGISTRY_ROOT / "UNIFIED_SSOT_REGISTRY.json"

# Legacy registry (deprecated - for migration only)
LEGACY_REGISTRY_PATH = REGISTRY_ROOT / "ID_REGISTRY.json"

# Backup directory for registry snapshots
REGISTRY_BACKUP_DIR = REGISTRY_ROOT / "backups"

# Lock file for atomic write operations
REGISTRY_LOCK_PATH = REGISTRY_ROOT / ".registry.lock"

# Audit log for registry changes
REGISTRY_AUDIT_LOG = REGISTRY_ROOT / "identity_audit_log.jsonl"

# Ensure directories exist
REGISTRY_ROOT.mkdir(parents=True, exist_ok=True)
REGISTRY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def get_registry_path() -> Path:
    """
    Get the current registry path.
    
    Returns:
        Path to UNIFIED_SSOT_REGISTRY.json
    """
    return REGISTRY_PATH


def get_backup_dir() -> Path:
    """
    Get the registry backup directory.
    
    Returns:
        Path to backup directory
    """
    return REGISTRY_BACKUP_DIR


def validate_registry_exists() -> bool:
    """
    Check if the unified registry file exists.
    
    Returns:
        True if registry exists, False otherwise
    """
    return REGISTRY_PATH.exists()


def initialize_registry_if_missing():
    """
    Create empty registry structure if file doesn't exist.
    """
    if not REGISTRY_PATH.exists():
        import json
        from datetime import datetime
        
        empty_registry = {
            "meta": {
                "document_id": "REG-UNIFIED-SSOT-720066-001",
                "registry_name": "UNIFIED_SSOT_REGISTRY",
                "version": "2.1.0",
                "status": "active",
                "last_updated_utc": datetime.utcnow().isoformat() + "Z",
                "authoritative": True,
                "description": "Single source of truth for all entities, relationships, and generators"
            },
            "counters": {
                "record_id": {"current": 0},
                "file_doc_id": {},
                "asset_id": {},
                "transient_id": {},
                "edge_id": {},
                "generator_id": {"current": 0}
            },
            "records": []
        }
        
        with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(empty_registry, f, indent=2, ensure_ascii=False)

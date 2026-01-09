"""
Shared utilities for DOC_ID system.

Provides common file I/O operations, validation, and helpers.
"""
# DOC_ID: DOC-CORE-COMMON-UTILS-1172

import json
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

from .config import DOC_ID_REGEX
from .errors import (
    RegistryNotFoundError,
    InventoryNotFoundError,
    InvalidDocIDError,
    RegistryCorruptedError,
)


# ============================================================================
# File I/O Helpers
# ============================================================================

def load_yaml(path: Path) -> Dict:
    """
    Load YAML file safely.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Parsed YAML data as dictionary
        
    Raises:
        RegistryNotFoundError: If file doesn't exist
        RegistryCorruptedError: If YAML is invalid
    """
    if yaml is None:
        raise ImportError("PyYAML not installed. Run: pip install pyyaml")
    
    if not path.exists():
        raise RegistryNotFoundError(path)
    
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise RegistryCorruptedError(f"Invalid YAML: {e}")


def save_yaml(path: Path, data: Dict) -> None:
    """
    Save YAML file with consistent formatting.
    
    Args:
        path: Path to save YAML file
        data: Dictionary to serialize
    """
    if yaml is None:
        raise ImportError("PyYAML not installed. Run: pip install pyyaml")
    
    path.write_text(
        yaml.dump(data, sort_keys=False, default_flow_style=False),
        encoding="utf-8"
    )


def load_jsonl(path: Path) -> List[Dict]:
    """
    Load JSONL file (one JSON object per line).
    
    Args:
        path: Path to JSONL file
        
    Returns:
        List of parsed JSON objects
        
    Raises:
        InventoryNotFoundError: If file doesn't exist
    """
    if not path.exists():
        raise InventoryNotFoundError(path)
    
    entries = []
    content = path.read_text(encoding="utf-8").strip()
    
    if not content:
        return entries
    
    for line_num, line in enumerate(content.split("\n"), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as e:
            # Skip invalid lines with warning
            print(f"Warning: Invalid JSON on line {line_num}: {e}")
    
    return entries


def save_jsonl(path: Path, entries: List[Dict]) -> None:
    """
    Save JSONL file (one JSON object per line).
    
    Args:
        path: Path to save JSONL file
        entries: List of dictionaries to serialize
    """
    with open(path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_doc_id(doc_id: str) -> bool:
    """
    Validate doc_id format.
    
    Args:
        doc_id: Doc ID string to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not doc_id or not isinstance(doc_id, str):
        return False
    return bool(DOC_ID_REGEX.match(doc_id))


def validate_doc_id_strict(doc_id: str) -> None:
    """
    Validate doc_id format (raises exception if invalid).
    
    Args:
        doc_id: Doc ID string to validate
        
    Raises:
        InvalidDocIDError: If format is invalid
    """
    if not validate_doc_id(doc_id):
        raise InvalidDocIDError(doc_id)


def extract_category_from_doc_id(doc_id: str) -> Optional[str]:
    """
    Extract category prefix from doc_id.
    
    Args:
        doc_id: Doc ID string (e.g., "DOC-CORE-SCHEDULER-001")
        
    Returns:
        Category prefix (e.g., "CORE") or None if invalid
    """
    if not validate_doc_id(doc_id):
        return None
    
    # Format: DOC-[CATEGORY]-...
    parts = doc_id.split("-")
    if len(parts) >= 3:
        return parts[1]
    
    return None


# ============================================================================
# Path Helpers
# ============================================================================

def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if needed.
    
    Args:
        path: Directory path
        
    Returns:
        The same path (for chaining)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_relative_path(path: Path, base: Path) -> str:
    """
    Get relative path as string.
    
    Args:
        path: Full path
        base: Base path to calculate relative from
        
    Returns:
        Relative path as string with forward slashes
    """
    try:
        rel_path = path.relative_to(base)
        return str(rel_path).replace("\\", "/")
    except ValueError:
        # path is not relative to base
        return str(path).replace("\\", "/")

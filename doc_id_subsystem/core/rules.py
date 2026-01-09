"""
Central rules for doc_id format, validation, and parsing.
Single source of truth for all doc_id operations.

This module consolidates all doc_id rules that were previously scattered
across multiple files. All scripts should import from here.
"""
# DOC_ID: DOC-RULES-COMMON-RULES-001

import re
from typing import Dict, Optional, Tuple
from enum import Enum

# ============================================================================
# Constants
# ============================================================================

# Default digit width for doc_id sequence numbers (supports 0000-9999)
DOC_ID_WIDTH = 4

# Doc ID validation regex
# Format: DOC-CATEGORY-NAME[-PART]*-SEQUENCE
# SEQUENCE: 3 or more digits (backward compatible with 3-digit, default to 4-digit)
DOC_ID_REGEX = re.compile(
    r"^DOC-([A-Z0-9]+)-([A-Z0-9]+(?:-[A-Z0-9]+)*)-([0-9]{3,})$"
)

# Legacy 3-4 digit regex (for backward compatibility checks)
DOC_ID_REGEX_LEGACY = re.compile(
    r"^DOC-[A-Z0-9]+-[A-Z0-9]+(-[A-Z0-9]+)*-[0-9]{3,4}$"
)

# ============================================================================
# Category Prefixes
# ============================================================================

class CategoryPrefix(Enum):
    """Standard doc_id category prefixes."""
    CORE = "CORE"
    SCRIPT = "SCRIPT"
    GUIDE = "GUIDE"
    TEST = "TEST"
    PAT = "PAT"
    SPEC = "SPEC"
    CONFIG = "CONFIG"
    ERROR = "ERROR"
    AIM = "AIM"
    PM = "PM"
    GUI = "GUI"
    GLOSSARY = "GLOSSARY"
    RULES = "RULES"
    INDEX = "INDEX"
    STAGING = "STAGING"
    VALIDATORS = "VALIDATORS"
    PLAN = "PLAN"

# ============================================================================
# Validation Functions
# ============================================================================

def validate_doc_id(doc_id: str) -> bool:
    """
    Validate doc_id format.
    
    Args:
        doc_id: The doc_id string to validate
        
    Returns:
        True if valid format, False otherwise
        
    Example:
        >>> validate_doc_id("DOC-CORE-TEST-0001")
        True
        >>> validate_doc_id("DOC-INVALID")
        False
    """
    if not doc_id:
        return False
    return DOC_ID_REGEX.match(doc_id) is not None

def validate_doc_id_strict(doc_id: str, width: int = DOC_ID_WIDTH) -> bool:
    """
    Validate doc_id format with strict width requirement.
    
    Args:
        doc_id: The doc_id string to validate
        width: Expected digit width (default: 4)
        
    Returns:
        True if valid format with exact width, False otherwise
    """
    if not doc_id:
        return False
    match = DOC_ID_REGEX.match(doc_id)
    if not match:
        return False
    sequence = match.group(3)
    return len(sequence) == width

# ============================================================================
# Parsing Functions
# ============================================================================

def parse_doc_id(doc_id: str) -> Optional[Dict[str, str]]:
    """
    Parse doc_id into components.
    
    Args:
        doc_id: The doc_id string to parse
        
    Returns:
        Dictionary with 'category', 'name', and 'sequence' keys, or None if invalid
        
    Example:
        >>> parse_doc_id("DOC-CORE-TEST-SUITE-0001")
        {'category': 'CORE', 'name': 'TEST-SUITE', 'sequence': '0001'}
    """
    if not doc_id:
        return None
    match = DOC_ID_REGEX.match(doc_id)
    if not match:
        return None
    return {
        "category": match.group(1),
        "name": match.group(2),
        "sequence": match.group(3)
    }

def parse_doc_id_full(doc_id: str) -> Optional[Dict[str, any]]:
    """
    Parse doc_id into components with additional metadata.
    
    Args:
        doc_id: The doc_id string to parse
        
    Returns:
        Dictionary with components plus metadata (sequence_int, width, is_legacy)
    """
    parsed = parse_doc_id(doc_id)
    if not parsed:
        return None
    
    sequence_str = parsed["sequence"]
    sequence_int = int(sequence_str)
    width = len(sequence_str)
    is_legacy = width == 3
    
    return {
        **parsed,
        "sequence_int": sequence_int,
        "width": width,
        "is_legacy": is_legacy
    }

# ============================================================================
# Formatting Functions
# ============================================================================

def format_doc_id(category: str, name: str, sequence: int, width: int = DOC_ID_WIDTH) -> str:
    """
    Format doc_id with proper padding.
    
    Args:
        category: Category prefix (e.g., "CORE", "SCRIPT")
        name: Name component (can include hyphens, e.g., "TEST-SUITE")
        sequence: Sequence number (will be zero-padded)
        width: Digit width for sequence (default: 4)
        
    Returns:
        Formatted doc_id string
        
    Example:
        >>> format_doc_id("CORE", "TEST", 1)
        'DOC-CORE-TEST-0001'
        >>> format_doc_id("SCRIPT", "AUTO-ASSIGN", 42, width=4)
        'DOC-SCRIPT-AUTO-ASSIGN-0042'
    """
    seq_str = str(sequence).zfill(width)
    return f"DOC-{category.upper()}-{name.upper()}-{seq_str}"

def normalize_doc_id(doc_id: str, width: int = DOC_ID_WIDTH) -> Optional[str]:
    """
    Normalize doc_id to standard width.
    
    Converts 3-digit legacy doc_ids to 4-digit format.
    
    Args:
        doc_id: The doc_id to normalize
        width: Target digit width (default: 4)
        
    Returns:
        Normalized doc_id string, or None if invalid
        
    Example:
        >>> normalize_doc_id("DOC-CORE-TEST-001")
        'DOC-CORE-TEST-0001'
    """
    parsed = parse_doc_id(doc_id)
    if not parsed:
        return None
    seq = int(parsed["sequence"])
    return format_doc_id(parsed["category"], parsed["name"], seq, width)

# ============================================================================
# Component Extraction Functions
# ============================================================================

def extract_category(doc_id: str) -> Optional[str]:
    """Extract category prefix from doc_id."""
    parsed = parse_doc_id(doc_id)
    return parsed["category"] if parsed else None

def extract_name(doc_id: str) -> Optional[str]:
    """Extract name component from doc_id."""
    parsed = parse_doc_id(doc_id)
    return parsed["name"] if parsed else None

def extract_sequence(doc_id: str) -> Optional[int]:
    """Extract sequence number from doc_id as integer."""
    parsed = parse_doc_id(doc_id)
    return int(parsed["sequence"]) if parsed else None

# ============================================================================
# Comparison Functions
# ============================================================================

def compare_doc_ids(doc_id1: str, doc_id2: str) -> int:
    """
    Compare two doc_ids for sorting.
    
    Returns:
        -1 if doc_id1 < doc_id2
        0 if equal
        1 if doc_id1 > doc_id2
        
    Comparison order: category, name, sequence
    """
    parsed1 = parse_doc_id_full(doc_id1)
    parsed2 = parse_doc_id_full(doc_id2)
    
    if not parsed1 or not parsed2:
        return 0
    
    # Compare category
    if parsed1["category"] != parsed2["category"]:
        return -1 if parsed1["category"] < parsed2["category"] else 1
    
    # Compare name
    if parsed1["name"] != parsed2["name"]:
        return -1 if parsed1["name"] < parsed2["name"] else 1
    
    # Compare sequence (numerical)
    if parsed1["sequence_int"] != parsed2["sequence_int"]:
        return -1 if parsed1["sequence_int"] < parsed2["sequence_int"] else 1
    
    return 0

def doc_ids_match(doc_id1: str, doc_id2: str, ignore_width: bool = True) -> bool:
    """
    Check if two doc_ids match semantically.
    
    Args:
        doc_id1: First doc_id
        doc_id2: Second doc_id
        ignore_width: If True, DOC-CORE-TEST-001 matches DOC-CORE-TEST-0001
        
    Returns:
        True if doc_ids match semantically
    """
    if ignore_width:
        # Normalize both to same width
        norm1 = normalize_doc_id(doc_id1, DOC_ID_WIDTH)
        norm2 = normalize_doc_id(doc_id2, DOC_ID_WIDTH)
        return norm1 == norm2 if norm1 and norm2 else False
    else:
        return doc_id1 == doc_id2

# ============================================================================
# Range Functions
# ============================================================================

def is_sequence_exhausted(sequence: int, width: int = DOC_ID_WIDTH) -> bool:
    """
    Check if sequence number is approaching width limit.
    
    Args:
        sequence: Current sequence number
        width: Digit width
        
    Returns:
        True if at or above 90% of max capacity
    """
    max_value = (10 ** width) - 1
    threshold = max_value * 0.9
    return sequence >= threshold

def get_next_width(current_width: int) -> int:
    """Get next digit width when current is exhausted."""
    return current_width + 1

def max_sequence_for_width(width: int) -> int:
    """Get maximum sequence number for given width."""
    return (10 ** width) - 1

# ============================================================================
# Utility Functions
# ============================================================================

def is_legacy_format(doc_id: str) -> bool:
    """Check if doc_id uses legacy 3-digit format."""
    parsed = parse_doc_id_full(doc_id)
    return parsed["is_legacy"] if parsed else False

def suggest_next_sequence(category: str, existing_sequences: list) -> int:
    """
    Suggest next sequence number for category.
    
    Args:
        category: Category prefix
        existing_sequences: List of existing sequence numbers
        
    Returns:
        Next available sequence number
    """
    if not existing_sequences:
        return 1
    return max(existing_sequences) + 1

# ============================================================================
# Export All
# ============================================================================

__all__ = [
    # Constants
    "DOC_ID_WIDTH",
    "DOC_ID_REGEX",
    "DOC_ID_REGEX_LEGACY",
    "CategoryPrefix",
    
    # Validation
    "validate_doc_id",
    "validate_doc_id_strict",
    
    # Parsing
    "parse_doc_id",
    "parse_doc_id_full",
    
    # Formatting
    "format_doc_id",
    "normalize_doc_id",
    
    # Component Extraction
    "extract_category",
    "extract_name",
    "extract_sequence",
    
    # Comparison
    "compare_doc_ids",
    "doc_ids_match",
    
    # Range Functions
    "is_sequence_exhausted",
    "get_next_width",
    "max_sequence_for_width",
    
    # Utility
    "is_legacy_format",
    "suggest_next_sequence",
]

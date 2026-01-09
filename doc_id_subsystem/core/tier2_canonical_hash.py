# DOC_ID: DOC-SCRIPT-1008
"""
Tier 2 Canonical Hash Extractor
DOC_LINK: A-REGV3-EXTRACT-002
Work ID: WORK-REGV3-001
BDD Spec: specs/behaviors/BDD-REGV3-CANONICAL-HASH-002.yaml

Generates structure-preserving SHA256 hashes for JSON/YAML files.
Ignores formatting differences (whitespace, key order).
"""

import json
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_canonical_hash(file_path: str, trace_id: Optional[str] = None) -> Optional[str]:
    """
    Extract canonical hash for JSON/YAML files.
    
    Args:
        file_path: Path to file to hash
        trace_id: Trace ID for observability (optional)
    
    Returns:
        SHA256 hash of canonical form, or None if not JSON/YAML
    """
    path = Path(file_path)
    
    # Add trace_id to log context if provided
    log_extra = {"trace_id": trace_id} if trace_id else {}
    
    # Only process JSON/YAML files
    if path.suffix.lower() not in ['.json', '.yaml', '.yml']:
        logger.debug(f"Skipping non-JSON/YAML file: {file_path}", extra=log_extra)
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse based on file type
        if path.suffix.lower() == '.json':
            data = json.loads(content)
        else:  # .yaml or .yml
            data = yaml.safe_load(content)
        
        # Convert to canonical JSON form (sorted keys, no whitespace)
        # Per SYSTEM_DETERMINISM_CONTRACT.json: sort_keys=True, separators=(',', ':')
        canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        
        # Compute SHA256 hash
        hash_obj = hashlib.sha256(canonical_json.encode('utf-8'))
        canonical_hash = hash_obj.hexdigest()
        
        logger.info(
            f"Extracted canonical hash for {file_path}: {canonical_hash[:8]}...",
            extra=log_extra
        )
        
        return canonical_hash
        
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        logger.warning(
            f"Failed to parse {file_path} as JSON/YAML: {e}",
            extra=log_extra
        )
        return None
    except Exception as e:
        logger.error(
            f"Error extracting canonical hash from {file_path}: {e}",
            extra=log_extra
        )
        return None


if __name__ == "__main__":
    # Test with sample JSON
    import tempfile
    
    # Test JSON
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"b": 2, "a": 1}')
        temp_json = f.name
    
    hash1 = extract_canonical_hash(temp_json, trace_id="test-canonical-hash")
    print(f"JSON hash: {hash1}")
    
    # Test with differently formatted JSON (should produce same hash)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{\n  "a": 1,\n  "b": 2\n}')
        temp_json2 = f.name
    
    hash2 = extract_canonical_hash(temp_json2, trace_id="test-canonical-hash")
    print(f"JSON hash (reformatted): {hash2}")
    print(f"Hashes match: {hash1 == hash2}")
    
    # Test Python file (should return None)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('print("test")')
        temp_py = f.name
    
    hash3 = extract_canonical_hash(temp_py, trace_id="test-canonical-hash")
    print(f"Python file hash: {hash3}")
    
    # Cleanup
    import os
    os.unlink(temp_json)
    os.unlink(temp_json2)
    os.unlink(temp_py)

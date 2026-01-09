#!/usr/bin/env python3
"""
AUTO-002: Doc-ID Scope Classifier
Determines category for files in eafix-modular based on path/type
"""
DOC_ID: DOC-CORE-1-CORE-OPERATIONS-CLASSIFY-SCOPE-1153

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def classify_file(file_path: str) -> str:
    """Classify files into categories based on eafix-modular structure."""
    path_lower = file_path.lower().replace('\\', '/')
    
    # Services
    if '/services/' in path_lower:
        if '/src/' in path_lower:
            if 'main.py' in path_lower or 'router' in path_lower:
                return 'api'
            elif 'models.py' in path_lower or 'schema' in path_lower:
                return 'model'
            else:
                return 'service'
        elif '/tests/' in path_lower:
            return 'test'
        else:
            return 'service'
    
    # Shared modules
    if '/shared/' in path_lower:
        return 'shared'
    
    # Tests
    if '/tests/' in path_lower or 'test_' in path_lower or path_lower.endswith('_test.py'):
        return 'test'
    
    # Contracts
    if '/contracts/' in path_lower or 'contract' in path_lower:
        return 'contract'
    
    # Scripts
    if '/scripts/' in path_lower or '/ci/' in path_lower or path_lower.endswith('.sh'):
        return 'script'
    
    # Infrastructure
    if any(x in path_lower for x in ['/deploy/', '/dag/', 'docker', 'compose']):
        return 'infra'
    
    # Documentation
    if path_lower.endswith(('.md', '.rst', '.txt')):
        if 'readme' in path_lower or '/docs/' in path_lower:
            return 'doc'
    
    # Configuration
    if path_lower.endswith(('.yaml', '.yml', '.json', '.toml', '.ini', '.env')):
        return 'config'
    
    # Legacy P_ directories
    if '/p_' in path_lower or path_lower.startswith('p_'):
        return 'legacy'
    
    # Default based on extension
    if path_lower.endswith('.py'):
        return 'service'
    
    return 'config'

# Files/directories that REQUIRE doc_id
REQUIRES_DOC_ID = [
    "*.py",
    "*.md",
    "*.json",
    "*.yaml",
    "*.yml",
    "*.sh",
    "*.ps1",
    "*.bat",
    "Dockerfile*",
    "*.toml"
]

# Excluded patterns (no doc_id needed)
EXCLUDE_PATTERNS = [
    ".git/*",
    "node_modules/*",
    "venv/*",
    ".venv/*",
    "*.pyc",
    "*.pyo",
    "__pycache__/*",
    ".pytest_cache/*",
    "logs/*",
    "run/*",
    "out/*",
    ".aider*",
    ".claude/*",
    "*.db",
    "*.sqlite"
]

def classify_scope(filepath: str, output: str):
    """Classify if file requires doc_id and determine category."""
    results = {
        "task_id": "AUTO-002",
        "timestamp": datetime.utcnow().isoformat(),
        "filepath": filepath,
        "requires_doc_id": False,
        "category": "",
        "reason": "",
        "file_type": ""
    }
    
    try:
        path = Path(filepath)
        
        # Check exclusions first
        for pattern in EXCLUDE_PATTERNS:
            if path.match(pattern):
                results["requires_doc_id"] = False
                results["reason"] = f"Excluded by pattern: {pattern}"
                results["file_type"] = "excluded"
                results["category"] = "excluded"
                break
        else:
            # Check inclusions
            for pattern in REQUIRES_DOC_ID:
                if path.match(pattern):
                    results["requires_doc_id"] = True
                    results["reason"] = f"Matches pattern: {pattern}"
                    results["file_type"] = path.suffix
                    results["category"] = classify_file(str(path))
                    break
            else:
                results["requires_doc_id"] = False
                results["reason"] = "Does not match any doc_id pattern"
                results["file_type"] = path.suffix or "no_extension"
                results["category"] = "excluded"
        
    except Exception as e:
        results["error"] = str(e)
    
    # Write output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify doc_id scope")
    parser.add_argument("--filepath", required=True, help="File path to classify")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    
    args = parser.parse_args()
    sys.exit(classify_scope(args.filepath, args.output))

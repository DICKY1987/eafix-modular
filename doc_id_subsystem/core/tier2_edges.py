# DOC_ID: DOC-SCRIPT-1009
"""
Tier 2 Edges Extractor
DOC_LINK: A-REGV3-EXTRACT-004
Work ID: WORK-REGV3-001
BDD Spec: specs/behaviors/BDD-REGV3-EDGES-004.yaml

Extracts dependency edges (imports) from Python files.
"""

import ast
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def extract_edges(
    file_path: str,
    file_uid: str,
    revision_id: int,
    trace_id: Optional[str] = None,
    run_id: Optional[str] = None
) -> List[Dict]:
    """
    Extract import dependency edges from Python file.
    
    Args:
        file_path: Path to Python file
        file_uid: Unique file identifier
        revision_id: Revision ID for this extraction
        trace_id: Trace ID for observability
        run_id: Run ID for observability
    
    Returns:
        List of edge dicts ready for code_edges table insertion
    """
    path = Path(file_path)
    
    log_extra = {}
    if trace_id:
        log_extra["trace_id"] = trace_id
    if run_id:
        log_extra["run_id"] = run_id
    
    # Only process Python files
    if path.suffix.lower() != '.py':
        logger.debug(f"Skipping non-Python file: {file_path}", extra=log_extra)
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
        
        edges = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # Handle: import os, import sys
                for alias in node.names:
                    edge = {
                        'file_uid': file_uid,
                        'revision_id': revision_id,
                        'edge_type': 'import',
                        'source_symbol': None,
                        'target_symbol': None,
                        'target_module': alias.name,
                        'line_number': node.lineno
                    }
                    edges.append(edge)
            
            elif isinstance(node, ast.ImportFrom):
                # Handle: from pathlib import Path
                module = node.module or ''
                for alias in node.names:
                    edge = {
                        'file_uid': file_uid,
                        'revision_id': revision_id,
                        'edge_type': 'import',
                        'source_symbol': alias.name,
                        'target_symbol': alias.name,
                        'target_module': module,
                        'line_number': node.lineno
                    }
                    edges.append(edge)
        
        # Sort by (target_module, line_number) for determinism
        edges.sort(key=lambda e: (e['target_module'] or '', e['line_number']))
        
        logger.info(
            f"Extracted {len(edges)} import edges from {file_path}",
            extra=log_extra
        )
        
        return edges
        
    except SyntaxError as e:
        logger.warning(
            f"Syntax error in {file_path}, cannot extract edges: {e}",
            extra=log_extra
        )
        return []
    except Exception as e:
        logger.error(
            f"Error extracting edges from {file_path}: {e}",
            extra=log_extra
        )
        return []


if __name__ == "__main__":
    # Test extraction
    import tempfile
    
    test_code = '''
import os
import sys
from pathlib import Path
from typing import List, Dict

def example():
    pass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_py = f.name
    
    edges = extract_edges(temp_py, "test-file-uid", 1, trace_id="test-edges", run_id="test-run")
    
    print(f"Extracted {len(edges)} edges:")
    for edge in edges:
        source = edge['source_symbol'] or '(module)'
        target = edge['target_module']
        print(f"  Line {edge['line_number']}: {source} -> {target}")
    
    import os
    os.unlink(temp_py)

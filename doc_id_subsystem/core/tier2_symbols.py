# DOC_ID: DOC-SCRIPT-1010
"""
Tier 2 Symbols Extractor
DOC_LINK: A-REGV3-EXTRACT-003
Work ID: WORK-REGV3-001
BDD Spec: specs/behaviors/BDD-REGV3-SYMBOLS-003.yaml

Extracts code symbols (functions, classes, imports) from Python files.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Add parent directory to path to import tree_sitter_extractor
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "1_CORE_OPERATIONS"))

try:
    from tree_sitter_extractor import extract_python_structure
except ImportError:
    extract_python_structure = None

logger = logging.getLogger(__name__)


def extract_symbols(
    file_path: str,
    file_uid: str,
    revision_id: int,
    trace_id: Optional[str] = None,
    run_id: Optional[str] = None
) -> List[Dict]:
    """
    Extract code symbols from Python file.
    
    Args:
        file_path: Path to Python file
        file_uid: Unique file identifier
        revision_id: Revision ID for this extraction
        trace_id: Trace ID for observability
        run_id: Run ID for observability
    
    Returns:
        List of symbol dicts ready for database insertion
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
    
    if extract_python_structure is None:
        logger.warning("tree_sitter_extractor not available, using fallback", extra=log_extra)
        return _extract_symbols_fallback(file_path, file_uid, revision_id)
    
    try:
        # Use tree-sitter extractor
        structure = extract_python_structure(file_path)
        
        symbols = []
        
        # Extract functions
        for func in structure.get('functions', []):
            symbol = {
                'file_uid': file_uid,
                'revision_id': revision_id,
                'symbol_type': 'function',
                'symbol_name': func['name'],
                'line_start': func.get('line_start'),
                'line_end': func.get('line_end'),
                'visibility': _determine_visibility(func['name']),
                'is_async': 1 if func.get('is_async', False) else 0,
                'is_generator': 1 if func.get('is_generator', False) else 0,
                'complexity_score': func.get('complexity', 0)
            }
            symbols.append(symbol)
        
        # Extract classes
        for cls in structure.get('classes', []):
            symbol = {
                'file_uid': file_uid,
                'revision_id': revision_id,
                'symbol_type': 'class',
                'symbol_name': cls['name'],
                'line_start': cls.get('line_start'),
                'line_end': cls.get('line_end'),
                'visibility': _determine_visibility(cls['name']),
                'is_async': 0,
                'is_generator': 0,
                'complexity_score': 0
            }
            symbols.append(symbol)
            
            # Extract methods from class
            for method in cls.get('methods', []):
                symbol = {
                    'file_uid': file_uid,
                    'revision_id': revision_id,
                    'symbol_type': 'method',
                    'symbol_name': f"{cls['name']}.{method['name']}",
                    'line_start': method.get('line_start'),
                    'line_end': method.get('line_end'),
                    'visibility': _determine_visibility(method['name']),
                    'is_async': 1 if method.get('is_async', False) else 0,
                    'is_generator': 1 if method.get('is_generator', False) else 0,
                    'complexity_score': method.get('complexity', 0)
                }
                symbols.append(symbol)
        
        # Extract imports
        for imp in structure.get('imports', []):
            symbol = {
                'file_uid': file_uid,
                'revision_id': revision_id,
                'symbol_type': 'import',
                'symbol_name': imp.get('name', imp.get('module', 'unknown')),
                'line_start': imp.get('line'),
                'line_end': imp.get('line'),
                'visibility': 'public',
                'is_async': 0,
                'is_generator': 0,
                'complexity_score': 0
            }
            symbols.append(symbol)
        
        # Sort by (line_start, symbol_name) for determinism
        symbols.sort(key=lambda s: (s['line_start'] or 0, s['symbol_name']))
        
        logger.info(
            f"Extracted {len(symbols)} symbols from {file_path}",
            extra=log_extra
        )
        
        return symbols
        
    except Exception as e:
        logger.error(
            f"Error extracting symbols from {file_path}: {e}",
            extra=log_extra
        )
        return []


def _determine_visibility(name: str) -> str:
    """Determine visibility from naming convention."""
    if name.startswith('__') and not name.endswith('__'):
        return 'private'
    elif name.startswith('_'):
        return 'protected'
    else:
        return 'public'


def _extract_symbols_fallback(file_path: str, file_uid: str, revision_id: int) -> List[Dict]:
    """Fallback symbol extraction using simple regex/ast parsing."""
    import ast
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
        
        symbols = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append({
                    'file_uid': file_uid,
                    'revision_id': revision_id,
                    'symbol_type': 'function',
                    'symbol_name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                    'visibility': _determine_visibility(node.name),
                    'is_async': 1 if isinstance(node, ast.AsyncFunctionDef) else 0,
                    'is_generator': 0,
                    'complexity_score': 0
                })
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    'file_uid': file_uid,
                    'revision_id': revision_id,
                    'symbol_type': 'class',
                    'symbol_name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                    'visibility': _determine_visibility(node.name),
                    'is_async': 0,
                    'is_generator': 0,
                    'complexity_score': 0
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    symbols.append({
                        'file_uid': file_uid,
                        'revision_id': revision_id,
                        'symbol_type': 'import',
                        'symbol_name': alias.name,
                        'line_start': node.lineno,
                        'line_end': node.lineno,
                        'visibility': 'public',
                        'is_async': 0,
                        'is_generator': 0,
                        'complexity_score': 0
                    })
        
        symbols.sort(key=lambda s: (s['line_start'], s['symbol_name']))
        return symbols
        
    except Exception as e:
        logger.error(f"Fallback extraction failed for {file_path}: {e}")
        return []


if __name__ == "__main__":
    # Test extraction
    import tempfile
    
    test_code = '''
import os
from pathlib import Path

def public_func():
    pass

def _private_func():
    pass

class MyClass:
    def method(self):
        pass
    
    def _private_method(self):
        pass
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_py = f.name
    
    symbols = extract_symbols(temp_py, "test-file-uid", 1, trace_id="test-symbols", run_id="test-run")
    
    print(f"Extracted {len(symbols)} symbols:")
    for symbol in symbols:
        print(f"  {symbol['symbol_type']:10} {symbol['symbol_name']:30} visibility={symbol['visibility']}")
    
    import os
    os.unlink(temp_py)

"""
Descriptor Extractor

doc_id: DOC-AUTO-DESC-0010
purpose: Wraps python_ast_parser.py, produces promotion payload
phase: Phase 4 - Parser & Descriptor
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib


class DescriptorExtractor:
    """
    Extracts descriptor from Python files via AST parsing.
    
    Wraps the existing python_ast_parser.py and produces:
    1. Full descriptor JSON artifact
    2. Promotion payload (20 columns for registry columns 81-100)
    """
    
    def __init__(self, parser_path: str, descriptor_dir: str):
        """
        Initialize descriptor extractor.
        
        Args:
            parser_path: Path to python_ast_parser.py
            descriptor_dir: Directory for descriptor artifacts (.dms/artifacts/python_descriptor/)
        """
        self.parser_path = Path(parser_path)
        self.descriptor_dir = Path(descriptor_dir)
        
    def extract(
        self,
        file_path: str,
        doc_id: str,
        relative_path: str
    ) -> Dict[str, Any]:
        """
        Extract descriptor and promotion payload from Python file.
        
        Args:
            file_path: Absolute path to Python file
            doc_id: 16-digit doc_id
            relative_path: Repo-relative path
            
        Returns:
            Dict with:
            - descriptor: Full descriptor dict (to save as JSON)
            - promotion_payload: 20-column dict for registry update
            - source_sha256: Hash of source file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            SyntaxError: If Python file has syntax errors (logged, not fatal)
        """
        # TODO: Implement in Phase 4
        raise NotImplementedError("Phase 4")
        
    def _parse_python_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Python file via AST parser.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Parse results dict
        """
        # TODO: Implement in Phase 4
        # Import and call python_ast_parser.py
        raise NotImplementedError("Phase 4")
        
    def _build_descriptor(
        self,
        parse_results: Dict[str, Any],
        doc_id: str,
        relative_path: str,
        source_sha256: str
    ) -> Dict[str, Any]:
        """
        Build full descriptor JSON from parse results.
        
        Args:
            parse_results: Output from AST parser
            doc_id: 16-digit doc_id
            relative_path: Repo-relative path
            source_sha256: SHA-256 of source file
            
        Returns:
            Descriptor dict matching PYTHON_FILE_DESCRIPTOR.yml schema
        """
        # TODO: Implement in Phase 4
        raise NotImplementedError("Phase 4")
        
    def _build_promotion_payload(
        self,
        parse_results: Dict[str, Any],
        descriptor_path: str,
        descriptor_sha256: str
    ) -> Dict[str, Any]:
        """
        Build promotion payload (20 columns for registry).
        
        Args:
            parse_results: Output from AST parser
            descriptor_path: Path to saved descriptor artifact
            descriptor_sha256: SHA-256 of descriptor JSON
            
        Returns:
            Dict with keys:
            - py_parse_status: "ok" | "syntax_error" | "encoding_error" | "missing_file" | "timeout"
            - py_parsed_utc: ISO 8601 timestamp
            - py_parser_id: Parser identifier
            - py_parser_version: Parser version
            - py_parse_error_count: Number of parse errors
            - py_parse_error_first: First error message
            - py_module_qualname: Module qualified name
            - py_is_package_init: Boolean
            - py_has_main_guard: Boolean
            - py_entrypoint_symbol: Main entrypoint symbol
            - py_cli_framework: "none" | "argparse" | "click" | "typer" | "fire" | "docopt" | "unknown"
            - py_imports_local: List[str]
            - py_imports_external: List[str]
            - py_imports_local_count: int
            - py_imports_external_count: int
            - py_function_count: int
            - py_class_count: int
            - py_docstring_1l: First line of module docstring
            - py_descriptor_path: Path to descriptor artifact
            - py_descriptor_sha256: SHA-256 of descriptor JSON
        """
        # TODO: Implement in Phase 4
        raise NotImplementedError("Phase 4")
        
    def save_descriptor(
        self,
        descriptor: Dict[str, Any],
        doc_id: str
    ) -> str:
        """
        Save descriptor to artifact directory.
        
        Args:
            descriptor: Descriptor dict
            doc_id: 16-digit doc_id
            
        Returns:
            Path to saved descriptor file
        """
        # TODO: Implement in Phase 4
        # Save as: .dms/artifacts/python_descriptor/{doc_id}.v1.json
        raise NotImplementedError("Phase 4")
        
    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute SHA-256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA-256 hex digest
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

#!/usr/bin/env python3
# DOC_ID: DOC-SERVICE-0021
"""
Comprehensive Codebase Analysis Tool

Generates machine-readable JSON documentation describing the entire EAFIX
Modular Trading System codebase structure, components, entities, and dependencies.

Output format: Single JSON object for AI consumption.
"""

import ast
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Directories to exclude from analysis
EXCLUDE_DIRS = {
    ".git", ".github", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".aider.tags.cache.v4", ".aider", ".claude", "node_modules",
    ".venv", "venv", "env", ".env", "*.egg-info", ".eggs",
    "dist", "build", ".tox"
}

# File extensions to exclude
EXCLUDE_FILES = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".egg-info",
    ".swp", ".swo", ".DS_Store", "Thumbs.db"
}

# Language mapping by extension
LANGUAGE_MAP = {
    ".py": "Python",
    ".md": "Markdown",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".mq4": "MQL4",
    ".sh": "Shell",
    ".bash": "Shell",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".html": "HTML",
    ".css": "CSS",
    ".sql": "SQL",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".conf": "Config",
    ".xml": "XML",
    ".csv": "CSV",
    ".txt": "Text",
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "Taskfile": "Taskfile"
}


class CodebaseAnalyzer:
    """Main analyzer class for codebase documentation generation."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.project_name = self.root_path.name
        self.files_data: List[Dict[str, Any]] = []
        self.language_counts: Dict[str, int] = defaultdict(int)
        self.internal_deps: Dict[str, List[str]] = defaultdict(list)
        self.external_deps: Dict[str, Set[str]] = defaultdict(set)

    def should_exclude_dir(self, dirname: str) -> bool:
        """Check if directory should be excluded."""
        return dirname in EXCLUDE_DIRS or dirname.startswith(".")

    def should_exclude_file(self, filename: str) -> bool:
        """Check if file should be excluded."""
        ext = Path(filename).suffix
        return ext in EXCLUDE_FILES or filename.startswith(".")

    def get_language(self, filepath: Path) -> Optional[str]:
        """Determine programming language from file extension."""
        if filepath.name in LANGUAGE_MAP:
            return LANGUAGE_MAP[filepath.name]

        ext = filepath.suffix.lower()
        return LANGUAGE_MAP.get(ext)

    def get_relative_path(self, filepath: Path) -> str:
        """Get relative path from project root."""
        try:
            return str(filepath.relative_to(self.root_path))
        except ValueError:
            return str(filepath)

    def analyze_python_file(self, filepath: Path) -> Dict[str, Any]:
        """Analyze Python file using AST to extract entities and dependencies."""
        entities = {
            "classes": [],
            "functions": [],
            "variables": []
        }
        dependencies = {
            "internal": [],
            "external": []
        }

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))

            # Extract top-level entities
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    methods = [
                        m.name for m in node.body
                        if isinstance(m, ast.FunctionDef)
                    ]
                    entities["classes"].append({
                        "name": node.name,
                        "methods": methods
                    })

                elif isinstance(node, ast.FunctionDef):
                    params = [arg.arg for arg in node.args.args]
                    entities["functions"].append({
                        "name": node.name,
                        "parameters": params
                    })

                elif isinstance(node, ast.Assign):
                    # Extract module-level constants (ALL_CAPS naming convention)
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id.isupper() or target.id.startswith("_"):
                                entities["variables"].append({
                                    "name": target.id,
                                    "kind": "constant" if target.id.isupper() else "private"
                                })

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        if self.is_internal_module(module_name):
                            dependencies["internal"].append(module_name)
                        else:
                            dependencies["external"].append(module_name.split(".")[0])

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if self.is_internal_module(node.module):
                            dependencies["internal"].append(node.module)
                        else:
                            dependencies["external"].append(node.module.split(".")[0])

        except (SyntaxError, UnicodeDecodeError, Exception) as e:
            # If parsing fails, return empty entities
            pass

        # Remove duplicates from dependencies
        dependencies["internal"] = list(set(dependencies["internal"]))
        dependencies["external"] = list(set(dependencies["external"]))

        return {
            "entities": entities,
            "dependencies": dependencies
        }

    def is_internal_module(self, module_name: str) -> bool:
        """Check if module is internal to the project."""
        # Check if it starts with known internal prefixes
        internal_prefixes = [
            "services.", "shared.", "contracts.", "tests.",
            "P_", "scripts.", "compliance.", "observability."
        ]
        return any(module_name.startswith(prefix) for prefix in internal_prefixes)

    def analyze_file(self, filepath: Path) -> Dict[str, Any]:
        """Analyze a single file and extract metadata."""
        rel_path = self.get_relative_path(filepath)
        language = self.get_language(filepath)

        if language:
            self.language_counts[language] += 1

        file_info = {
            "path": rel_path.replace("\\", "/"),
            "name": filepath.name,
            "language": language,
            "size_bytes": filepath.stat().st_size if filepath.exists() else 0,
            "summary": self.infer_file_purpose(filepath, rel_path),
            "entities": {
                "classes": [],
                "functions": [],
                "variables": []
            },
            "dependencies": {
                "internal": [],
                "external": []
            }
        }

        # Analyze Python files for entities and dependencies
        if language == "Python" and filepath.suffix == ".py":
            analysis = self.analyze_python_file(filepath)
            file_info["entities"] = analysis["entities"]
            file_info["dependencies"] = analysis["dependencies"]

            # Track dependencies for dependency map
            rel_path_key = rel_path.replace("\\", "/")
            if analysis["dependencies"]["internal"]:
                self.internal_deps[rel_path_key] = analysis["dependencies"]["internal"]
            for ext_dep in analysis["dependencies"]["external"]:
                self.external_deps[ext_dep].add(rel_path_key)

        return file_info

    def infer_file_purpose(self, filepath: Path, rel_path: str) -> str:
        """Infer file purpose from path and name."""
        path_lower = rel_path.lower().replace("\\", "/")
        name_lower = filepath.name.lower()

        # Configuration files
        if name_lower in ["pyproject.toml", "setup.py", "setup.cfg"]:
            return "Python project configuration"
        if name_lower in ["makefile", "taskfile.yml"]:
            return "Build automation"
        if name_lower == "dockerfile":
            return "Container definition"
        if name_lower in ["docker-compose.yml", "docker-compose.yaml"]:
            return "Container orchestration"
        if name_lower == ".pre-commit-config.yaml":
            return "Pre-commit hooks configuration"

        # Service files
        if "services/" in path_lower:
            if name_lower == "main.py":
                return "Service entry point (FastAPI)"
            if name_lower == "main_enterprise.py":
                return "Enterprise service implementation (BaseEnterpriseService)"
            if name_lower == "config.py":
                return "Service configuration (Pydantic Settings)"
            if name_lower == "health.py":
                return "Health check endpoint"
            if name_lower == "metrics.py":
                return "Prometheus metrics collection"

        # Common patterns
        if "base_service.py" in name_lower:
            return "BaseEnterpriseService foundation class"
        if "test_" in name_lower or "/tests/" in path_lower:
            return "Test suite"
        if "readme" in name_lower:
            return "Documentation"
        if "schema.json" in name_lower:
            return "JSON Schema definition"
        if "requirements.txt" in name_lower:
            return "Python dependencies"

        # Contract files
        if "contracts/" in path_lower:
            if ".json" in name_lower:
                return "Event contract definition"
            if "models" in path_lower:
                return "Pydantic contract model"

        # Domain knowledge
        if path_lower.startswith("p_"):
            return "Domain knowledge specification"

        # Documentation
        if "docs/" in path_lower:
            if "adr/" in path_lower:
                return "Architectural Decision Record"
            if "runbooks/" in path_lower:
                return "Operational runbook"
            if "gaps/" in path_lower:
                return "Production readiness gap analysis"

        # Default
        if filepath.suffix == ".py":
            return "Python module"
        if filepath.suffix == ".md":
            return "Documentation"
        if filepath.suffix in [".yaml", ".yml"]:
            return "YAML configuration"
        if filepath.suffix == ".json":
            return "JSON data file"

        return "Source file"

    def walk_codebase(self):
        """Walk codebase and collect all file metadata."""
        print(f"Analyzing codebase at: {self.root_path}")

        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Filter out excluded directories
            dirnames[:] = [
                d for d in dirnames
                if not self.should_exclude_dir(d)
            ]

            for filename in filenames:
                if self.should_exclude_file(filename):
                    continue

                filepath = Path(dirpath) / filename

                try:
                    file_info = self.analyze_file(filepath)
                    self.files_data.append(file_info)
                except Exception as e:
                    print(f"Warning: Failed to analyze {filepath}: {e}", file=sys.stderr)

        print(f"Analyzed {len(self.files_data)} files")

    def build_dependency_map(self) -> Dict[str, Any]:
        """Build internal and external dependency maps."""
        return {
            "internal": dict(self.internal_deps),
            "external": {
                ext_dep: list(files)
                for ext_dep, files in self.external_deps.items()
            }
        }

    def build_language_summary(self) -> List[Dict[str, Any]]:
        """Build language summary with file counts."""
        return [
            {"language": lang, "file_count": count}
            for lang, count in sorted(
                self.language_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]

    def generate_notes(self) -> List[str]:
        """Generate analysis notes."""
        notes = []

        # Count microservices
        services_count = sum(
            1 for f in self.files_data
            if f["path"].startswith("services/") and
            "/" not in f["path"][9:] and  # Top-level service dirs
            f["language"] == "Python"
        )

        if services_count > 0:
            notes.append(
                f"BaseEnterpriseService provides unified observability across {services_count} microservices"
            )

        # Check for contracts
        contract_events = sum(
            1 for f in self.files_data
            if "contracts/events/" in f["path"] and f["language"] == "JSON"
        )
        if contract_events > 0:
            notes.append(
                f"Contract-driven development with {contract_events} event types in contracts/"
            )

        # Check for MQL4 integration
        mql4_files = sum(1 for f in self.files_data if f["language"] == "MQL4")
        if mql4_files > 0:
            notes.append("Cross-language parity: Python ↔ MQL4 for hybrid ID system")

        # Check for test coverage
        test_files = sum(
            1 for f in self.files_data
            if "test_" in f["name"] or "/tests/" in f["path"]
        )
        if test_files > 0:
            notes.append(f"{test_files} test files with 80% coverage threshold enforced")

        return notes

    def generate_json(self, output_path: str) -> Dict[str, Any]:
        """Generate final JSON structure."""
        self.walk_codebase()

        output_abs_path = str(Path(output_path).resolve())

        json_doc = {
            "project": {
                "name": self.project_name,
                "path": str(self.root_path),
                "language_summary": self.build_language_summary(),
                "dependency_map": self.build_dependency_map(),
                "files": self.files_data,
                "notes": self.generate_notes(),
                "extensions": {
                    "download_url": output_abs_path,
                    "extra": {
                        "analysis_timestamp": datetime.now().astimezone().isoformat(),
                        "analyzer_version": "1.0.0",
                        "total_files": len(self.files_data),
                        "microservices": {
                            "count": sum(
                                1 for f in self.files_data
                                if f["path"].startswith("services/") and
                                f["path"].count("/") == 1
                            ),
                            "pattern": "BaseEnterpriseService inheritance",
                            "communication": ["Redis pub/sub", "HTTP REST", "WebSocket"]
                        },
                        "contracts": {
                            "events": sum(
                                1 for f in self.files_data
                                if "contracts/events/" in f["path"]
                            ),
                            "schemas": ["JSON Schema", "CSV Schema", "Pydantic models"]
                        },
                        "domain_knowledge": {
                            "p_folders": len(set(
                                f["path"].split("/")[0]
                                for f in self.files_data
                                if f["path"].startswith("P_")
                            )),
                            "specifications": "P_techspec/, P_project_knowledge/",
                            "integration": "P_mql4/ (MetaTrader)"
                        },
                        "test_coverage": {
                            "threshold": "80%",
                            "branch_coverage": True,
                            "frameworks": ["pytest", "contract testing", "property-based"]
                        }
                    }
                }
            }
        }

        return json_doc


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate comprehensive codebase JSON documentation"
    )
    parser.add_argument(
        "--root",
        default=os.getcwd(),
        help="Root directory of codebase (default: current directory)"
    )
    parser.add_argument(
        "--output",
        default="codebase_analysis.json",
        help="Output JSON file path (default: codebase_analysis.json)"
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation (default: 2, use 0 for compact)"
    )

    args = parser.parse_args()

    analyzer = CodebaseAnalyzer(args.root)

    print("=" * 60)
    print("EAFIX Codebase Analysis Tool")
    print("=" * 60)

    try:
        json_doc = analyzer.generate_json(args.output)

        # Write JSON to file
        with open(args.output, "w", encoding="utf-8") as f:
            if args.indent > 0:
                json.dump(json_doc, f, indent=args.indent, ensure_ascii=False)
            else:
                json.dump(json_doc, f, ensure_ascii=False)

        print(f"\n[SUCCESS] Analysis complete!")
        print(f"[OUTPUT] File written to: {Path(args.output).resolve()}")
        print(f"[STATS] Total files analyzed: {len(json_doc['project']['files'])}")
        print(f"[STATS] Languages detected: {len(json_doc['project']['language_summary'])}")
        print(f"[STATS] File size: {Path(args.output).stat().st_size / 1024 / 1024:.2f} MB")

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

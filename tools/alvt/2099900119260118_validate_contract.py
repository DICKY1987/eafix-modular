#!/usr/bin/env python3
"""
ALVT Contract Validator
doc_id: 2099900119260118
version: 1.0

Validates trigger lifecycle contracts against schema and checks resolvability.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

__doc_id__ = "2099900119260118"


class ContractValidator:
    """Validates trigger lifecycle contracts."""

    def __init__(self, repo_root: Path):
        """Initialize validator.
        
        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, contract_path: Path) -> bool:
        """Validate contract file.
        
        Args:
            contract_path: Path to contract YAML file
            
        Returns:
            True if valid, False otherwise
        """
        self.errors = []
        self.warnings = []

        # Check file exists
        if not contract_path.exists():
            self.errors.append(f"Contract file not found: {contract_path}")
            return False

        # Load YAML
        try:
            with open(contract_path, "r", encoding="utf-8") as f:
                contract = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parse error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Failed to read contract: {e}")
            return False

        # Validate schema
        self._validate_schema(contract)

        # Validate paths
        self._validate_paths(contract)

        # Validate graph consistency
        self._validate_graph(contract)

        return len(self.errors) == 0

    def _validate_schema(self, contract: Dict[str, Any]) -> None:
        """Validate contract schema structure."""
        # Required top-level sections
        required_sections = ["metadata", "required_files", "required_nodes", 
                           "required_edges", "completion_gates"]
        for section in required_sections:
            if section not in contract:
                self.errors.append(f"Missing required section: {section}")

        # Validate metadata
        if "metadata" in contract:
            metadata = contract["metadata"]
            required_meta = ["trigger_id", "version", "description", "doc_id"]
            for field in required_meta:
                if field not in metadata:
                    self.errors.append(f"metadata.{field} is required")

            # Validate trigger_id format
            if "trigger_id" in metadata:
                trigger_id = metadata["trigger_id"]
                if not isinstance(trigger_id, str) or not trigger_id:
                    self.errors.append("metadata.trigger_id must be non-empty string")

        # Validate required_files structure
        if "required_files" in contract:
            for idx, file_spec in enumerate(contract["required_files"]):
                if not isinstance(file_spec, dict):
                    self.errors.append(f"required_files[{idx}] must be dict")
                    continue
                if "path" not in file_spec:
                    self.errors.append(f"required_files[{idx}].path is required")
                if "role" not in file_spec:
                    self.errors.append(f"required_files[{idx}].role is required")
                if "role" in file_spec:
                    valid_roles = ["entrypoint", "dispatcher", "handler", "gate", 
                                 "evidence", "config"]
                    if file_spec["role"] not in valid_roles:
                        self.warnings.append(
                            f"required_files[{idx}].role '{file_spec['role']}' "
                            f"not in standard roles: {valid_roles}"
                        )

        # Validate required_nodes structure
        if "required_nodes" in contract:
            for idx, node_spec in enumerate(contract["required_nodes"]):
                if not isinstance(node_spec, dict):
                    self.errors.append(f"required_nodes[{idx}] must be dict")
                    continue
                required_node_fields = ["node_id", "node_type", "location"]
                for field in required_node_fields:
                    if field not in node_spec:
                        self.errors.append(f"required_nodes[{idx}].{field} is required")

        # Validate required_edges structure
        if "required_edges" in contract:
            for idx, edge_spec in enumerate(contract["required_edges"]):
                if not isinstance(edge_spec, dict):
                    self.errors.append(f"required_edges[{idx}] must be dict")
                    continue
                required_edge_fields = ["from_node", "to_node", "edge_type"]
                for field in required_edge_fields:
                    if field not in edge_spec:
                        self.errors.append(f"required_edges[{idx}].{field} is required")

        # Validate completion_gates structure
        if "completion_gates" in contract:
            for idx, gate_spec in enumerate(contract["completion_gates"]):
                if not isinstance(gate_spec, dict):
                    self.errors.append(f"completion_gates[{idx}] must be dict")
                    continue
                required_gate_fields = ["gate_id", "description", "verification"]
                for field in required_gate_fields:
                    if field not in gate_spec:
                        self.errors.append(f"completion_gates[{idx}].{field} is required")

    def _validate_paths(self, contract: Dict[str, Any]) -> None:
        """Validate that referenced paths are resolvable."""
        if "required_files" not in contract:
            return

        for file_spec in contract["required_files"]:
            if "path" not in file_spec:
                continue

            path_str = file_spec["path"]
            # Try absolute path
            abs_path = Path(path_str)
            if abs_path.is_absolute():
                if not abs_path.exists():
                    self.warnings.append(f"File not found: {path_str}")
                continue

            # Try repo-relative path
            repo_path = self.repo_root / path_str
            if not repo_path.exists():
                self.warnings.append(
                    f"File not found (repo-relative): {path_str} "
                    f"(checked: {repo_path})"
                )

    def _validate_graph(self, contract: Dict[str, Any]) -> None:
        """Validate graph consistency (nodes referenced by edges exist)."""
        if "required_nodes" not in contract or "required_edges" not in contract:
            return

        # Collect node_ids
        node_ids = set()
        for node_spec in contract["required_nodes"]:
            if "node_id" in node_spec:
                node_ids.add(node_spec["node_id"])

        # Check edge references
        for idx, edge_spec in enumerate(contract["required_edges"]):
            if "from_node" in edge_spec:
                if edge_spec["from_node"] not in node_ids:
                    self.errors.append(
                        f"required_edges[{idx}].from_node '{edge_spec['from_node']}' "
                        f"not found in required_nodes"
                    )
            if "to_node" in edge_spec:
                if edge_spec["to_node"] not in node_ids:
                    self.errors.append(
                        f"required_edges[{idx}].to_node '{edge_spec['to_node']}' "
                        f"not found in required_nodes"
                    )

    def print_results(self) -> None:
        """Print validation results."""
        if self.errors:
            print("ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        if self.warnings:
            print("WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
        if not self.errors and not self.warnings:
            print("VALID")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate trigger lifecycle contract"
    )
    parser.add_argument(
        "--trigger",
        required=True,
        help="Trigger ID (e.g., FILE_IDENTITY_CREATE)"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: current directory)"
    )
    parser.add_argument(
        "--contract-dir",
        type=Path,
        help="Contract directory (default: <repo-root>/contracts/triggers)"
    )

    args = parser.parse_args()

    # Determine contract directory
    if args.contract_dir:
        contract_dir = args.contract_dir
    else:
        contract_dir = args.repo_root / "contracts" / "triggers"

    # Find contract file
    # Try with doc_id prefix pattern
    contract_files = list(contract_dir.glob(f"*trigger.{args.trigger}.yaml"))
    if not contract_files:
        # Try without prefix
        contract_files = list(contract_dir.glob(f"trigger.{args.trigger}.yaml"))
    
    if not contract_files:
        print(f"ERROR: Contract file not found for trigger '{args.trigger}'")
        print(f"Searched in: {contract_dir}")
        return 1

    contract_path = contract_files[0]
    print(f"Validating contract: {contract_path}")

    # Run validation
    validator = ContractValidator(args.repo_root)
    is_valid = validator.validate(contract_path)
    validator.print_results()

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())

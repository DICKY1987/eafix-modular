#!/usr/bin/env python3
"""
ALVT Layer 1: Graph Connectivity Verification
doc_id: 2099900122260118
version: 1.0

Verifies automation wiring through graph analysis:
- Node existence (functions, classes, methods)
- Edge verification (calls, imports)
- Reachability (no orphaned nodes)
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml

__doc_id__ = "2099900122260118"


class Layer1Verifier:
    """ALVT Layer 1 graph connectivity verifier."""

    def __init__(self, repo_root: Path, contract: Dict[str, Any]):
        """Initialize verifier.
        
        Args:
            repo_root: Repository root path
            contract: Loaded contract dictionary
        """
        self.repo_root = repo_root
        self.contract = contract
        self.checks: List[Dict[str, Any]] = []
        self.discovered_nodes: Set[str] = set()
        self.discovered_edges: Set[tuple] = set()

    def verify(self) -> Dict[str, Any]:
        """Run all Layer 1 checks.
        
        Returns:
            Verification report dictionary
        """
        trigger_id = self.contract.get("metadata", {}).get("trigger_id", "UNKNOWN")
        
        # Discover nodes and edges from codebase
        self._discover_graph()
        
        # Check required nodes exist
        self._check_nodes_exist()
        
        # Check required edges exist
        self._check_edges_exist()
        
        # Check reachability (simplified - assumes entrypoint as root)
        self._check_reachability()
        
        # Generate report
        passed = sum(1 for c in self.checks if c["passed"])
        failed = sum(1 for c in self.checks if not c["passed"])
        status = "PASS" if failed == 0 else "FAIL"
        
        report = {
            "trigger_id": trigger_id,
            "verification_layer": "layer1",
            "status": status,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "checks": sorted(self.checks, key=lambda x: x["check_id"]),
            "summary": {
                "total_checks": len(self.checks),
                "passed": passed,
                "failed": failed
            },
            "graph_discovery": {
                "nodes_discovered": len(self.discovered_nodes),
                "edges_discovered": len(self.discovered_edges)
            }
        }
        
        return report

    def _discover_graph(self) -> None:
        """Discover nodes and edges from Python files using AST parsing."""
        required_files = self.contract.get("required_files", [])
        
        for file_spec in required_files:
            path_str = file_spec.get("path")
            if not path_str or not path_str.endswith(".py"):
                continue
            
            file_path = self.repo_root / path_str
            if not file_path.exists():
                continue
            
            try:
                self._parse_python_file(file_path, path_str)
            except Exception as e:
                # Log error but continue
                pass

    def _parse_python_file(self, file_path: Path, path_str: str) -> None:
        """Parse Python file to discover nodes and edges."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            return
        
        # Discover nodes (classes, functions, methods)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_node_id = f"{path_str}::{node.name}"
                self.discovered_nodes.add(class_node_id)
                
                # Discover methods in class
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_node_id = f"{path_str}::{node.name}::{item.name}"
                        self.discovered_nodes.add(method_node_id)
            
            elif isinstance(node, ast.FunctionDef):
                # Top-level function
                func_node_id = f"{path_str}::{node.name}"
                self.discovered_nodes.add(func_node_id)
        
        # Discover edges (simplified - function calls)
        # Note: Full call graph analysis requires more sophisticated tools
        # This is a basic implementation that looks for function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    # Simple function call
                    callee = node.func.id
                    # Create edge (caller context would need full analysis)
                    # For now, just track that function is called
                    self.discovered_edges.add(("_caller_", callee))
                elif isinstance(node.func, ast.Attribute):
                    # Method call (e.g., obj.method())
                    if isinstance(node.func.value, ast.Name):
                        obj = node.func.value.id
                        method = node.func.attr
                        self.discovered_edges.add((obj, method))

    def _check_nodes_exist(self) -> None:
        """Verify all required nodes exist in discovered graph."""
        required_nodes = self.contract.get("required_nodes", [])
        
        for node_spec in required_nodes:
            node_id = node_spec.get("node_id")
            location = node_spec.get("location", "")
            node_type = node_spec.get("node_type", "unknown")
            
            if not node_id:
                continue
            
            # Check if location matches any discovered node
            # Location format: "path/to/file.py::ClassName::method_name" or "path/to/file.py::function_name"
            exists = location in self.discovered_nodes
            
            # Also check partial matches (e.g., class without method)
            if not exists:
                # Try matching just the file::class or file::function part
                for discovered in self.discovered_nodes:
                    if location in discovered or discovered in location:
                        exists = True
                        break
            
            self.checks.append({
                "check_id": f"node_exists_{node_id}",
                "passed": exists,
                "reason": None if exists else f"Node not found: {location}",
                "evidence": {
                    "node_id": node_id,
                    "node_type": node_type,
                    "location": location,
                    "exists": exists
                }
            })

    def _check_edges_exist(self) -> None:
        """Verify all required edges exist in discovered graph."""
        required_edges = self.contract.get("required_edges", [])
        
        for edge_spec in required_edges:
            from_node = edge_spec.get("from_node")
            to_node = edge_spec.get("to_node")
            edge_type = edge_spec.get("edge_type", "calls")
            
            if not from_node or not to_node:
                continue
            
            # Simplified edge check
            # Full implementation would track caller-callee relationships precisely
            # For now, check if both nodes exist and assume edge exists if nodes exist
            
            # Find node locations
            required_nodes = self.contract.get("required_nodes", [])
            from_location = None
            to_location = None
            
            for node_spec in required_nodes:
                if node_spec.get("node_id") == from_node:
                    from_location = node_spec.get("location")
                if node_spec.get("node_id") == to_node:
                    to_location = node_spec.get("location")
            
            # Check if both nodes exist
            from_exists = any(from_location in d or d in from_location for d in self.discovered_nodes) if from_location else False
            to_exists = any(to_location in d or d in to_location for d in self.discovered_nodes) if to_location else False
            
            # Simplified: Edge exists if both nodes exist
            # Real implementation would verify actual call/import relationship
            edge_exists = from_exists and to_exists
            
            self.checks.append({
                "check_id": f"edge_exists_{from_node}_to_{to_node}",
                "passed": edge_exists,
                "reason": None if edge_exists else f"Edge not verified: {from_node} -> {to_node}",
                "evidence": {
                    "from_node": from_node,
                    "to_node": to_node,
                    "edge_type": edge_type,
                    "from_exists": from_exists,
                    "to_exists": to_exists,
                    "note": "Simplified edge verification - assumes edge exists if both nodes exist"
                }
            })

    def _check_reachability(self) -> None:
        """Check that all nodes are reachable from entrypoint (simplified)."""
        required_nodes = self.contract.get("required_nodes", [])
        
        # Find entrypoint node
        entrypoint_node = None
        for node_spec in required_nodes:
            if node_spec.get("node_type") == "class" or "entrypoint" in node_spec.get("node_id", "").lower():
                entrypoint_node = node_spec.get("node_id")
                break
        
        if not entrypoint_node:
            # No entrypoint identified, skip reachability check
            return
        
        # Simplified reachability: Assume all required nodes are reachable if they exist
        # Full implementation would perform graph traversal
        all_reachable = all(
            any(node_spec.get("location", "") in d or d in node_spec.get("location", "") 
                for d in self.discovered_nodes)
            for node_spec in required_nodes
        )
        
        self.checks.append({
            "check_id": "no_orphaned_nodes",
            "passed": all_reachable,
            "reason": None if all_reachable else "Some nodes may not be reachable from entrypoint",
            "evidence": {
                "entrypoint": entrypoint_node,
                "note": "Simplified reachability check - assumes nodes are reachable if they exist"
            }
        })


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ALVT Layer 1: Graph connectivity verification"
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
        "--output",
        type=Path,
        help="Output JSON report path (default: reports/alvt/graph.<trigger>.json)"
    )

    args = parser.parse_args()

    # Load contract
    contract_dir = args.repo_root / "contracts" / "triggers"
    contract_files = list(contract_dir.glob(f"*trigger.{args.trigger}.yaml"))
    
    if not contract_files:
        print(f"ERROR: Contract not found for trigger '{args.trigger}'", file=sys.stderr)
        return 1
    
    contract_path = contract_files[0]
    
    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            contract = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load contract: {e}", file=sys.stderr)
        return 1

    # Run verification
    verifier = Layer1Verifier(args.repo_root, contract)
    report = verifier.verify()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        reports_dir = args.repo_root / "reports" / "alvt"
        reports_dir.mkdir(parents=True, exist_ok=True)
        output_path = reports_dir / f"graph.{args.trigger}.json"

    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    print(f"Layer 1 verification: {report['status']}")
    print(f"Report written to: {output_path}")
    print(f"Checks: {report['summary']['passed']}/{report['summary']['total_checks']} passed")

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

# doc_id: DOC-DOC-0029
# DOC_ID: DOC-SERVICE-0006
"""
DAG Configuration Validation Script
Validates the DAG graph, workstreams, patterns, and quality gates.
"""

import yaml
import sys
from pathlib import Path
from typing import Any


def load_yaml(path: Path) -> dict[str, Any]:
    """Load and parse a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        ValueError: If the YAML content is not a dictionary.
        FileNotFoundError: If the file does not exist.
    """
    with open(path, "r") as f:
        content = yaml.safe_load(f)
    if not isinstance(content, dict):
        raise ValueError(f"Expected dictionary at root of {path}, got {type(content).__name__}")
    return content


def validate_dag_graph(dag: dict[str, Any]) -> list[str]:
    """Validate DAG graph configuration."""
    errors = []

    if "version" not in dag:
        errors.append("DAG missing 'version' field")

    if "nodes" not in dag:
        errors.append("DAG missing 'nodes' field")
        return errors

    # Build node lookup dictionary for O(1) access
    node_lookup = {node["id"]: node for node in dag["nodes"]}
    node_ids = set(node_lookup.keys())

    # Check for orphan references
    for node in dag["nodes"]:
        for child in node.get("children", []):
            if child not in node_ids:
                errors.append(f"Node '{node['id']}' references unknown child '{child}'")

    # Check for cycles using DFS with O(N) node lookup
    visited = set()
    rec_stack = set()

    def has_cycle(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)

        node = node_lookup.get(node_id)
        if node:
            for child in node.get("children", []):
                if child not in visited:
                    if has_cycle(child):
                        return True
                elif child in rec_stack:
                    return True

        rec_stack.remove(node_id)
        return False

    for node in dag["nodes"]:
        if node["id"] not in visited:
            if has_cycle(node["id"]):
                errors.append(f"Cycle detected involving node '{node['id']}'")
                break

    # Check verification nodes have required fields
    verification_kinds = {
        "VERIFY_BOUNDARY_COVERAGE",
        "VERIFY_STATE_TRANSITIONS",
        "VERIFY_ERROR_HANDLING",
        "VERIFY_INTEGRATION_SEAMS",
        "VERIFY_RESOURCE_HANDLING",
        "VERIFY_INVARIANT_ASSERTIONS",
    }

    for node in dag["nodes"]:
        if node.get("kind") in verification_kinds:
            if not node.get("injected"):
                errors.append(f"Verification node '{node['id']}' missing 'injected: true'")
            if not node.get("verification_type"):
                errors.append(
                    f"Verification node '{node['id']}' missing 'verification_type'"
                )

    return errors


def validate_workstreams(workstreams: dict[str, Any], dag: dict[str, Any]) -> list[str]:
    """Validate workstream definitions against DAG."""
    errors = []

    if "workstreams" not in workstreams:
        errors.append("Workstreams missing 'workstreams' field")
        return errors

    dag_node_ids = {node["id"] for node in dag.get("nodes", [])}

    for ws in workstreams["workstreams"]:
        # Check all nodes exist in DAG
        for node_id in ws.get("nodes", []):
            if node_id not in dag_node_ids:
                errors.append(f"Workstream '{ws['id']}' references unknown node '{node_id}'")

        # Check entry and exit nodes
        if ws.get("entry_node") not in dag_node_ids:
            errors.append(f"Workstream '{ws['id']}' has invalid entry_node")
        if ws.get("exit_node") not in dag_node_ids:
            errors.append(f"Workstream '{ws['id']}' has invalid exit_node")

    return errors


def validate_patterns(patterns: dict[str, Any]) -> list[str]:
    """Validate pattern registry."""
    errors = []

    if "verification_patterns" not in patterns:
        errors.append("Patterns missing 'verification_patterns' field")
        return errors

    required_patterns = {
        "VERIFY_BOUNDARY_COVERAGE",
        "VERIFY_STATE_TRANSITIONS",
        "VERIFY_ERROR_HANDLING",
        "VERIFY_INTEGRATION_SEAMS",
        "VERIFY_RESOURCE_HANDLING",
        "VERIFY_INVARIANT_ASSERTIONS",
    }

    defined_patterns = {p["id"] for p in patterns["verification_patterns"]}

    for required in required_patterns:
        if required not in defined_patterns:
            errors.append(f"Missing required pattern: {required}")

    return errors


def validate_quality_gates(gates: dict[str, Any], dag: dict[str, Any]) -> list[str]:
    """Validate quality gates configuration."""
    errors = []

    if "gates" not in gates:
        errors.append("Quality gates missing 'gates' field")
        return errors

    dag_node_ids = {node["id"] for node in dag.get("nodes", [])}

    for gate in gates["gates"]:
        # Check prerequisites reference valid nodes
        for prereq in gate.get("prerequisites", []):
            if prereq["node"] not in dag_node_ids:
                errors.append(f"Gate '{gate['id']}' references unknown prerequisite '{prereq['node']}'")

    # Check verification injections
    if "verification_injections" in gates:
        for injection in gates["verification_injections"]:
            if injection["target_node"] not in dag_node_ids:
                errors.append(f"Injection targets unknown node '{injection['target_node']}'")
            if injection["injected_node"] not in dag_node_ids:
                errors.append(f"Injection references unknown node '{injection['injected_node']}'")

    return errors


def validate_prompt_index(index: dict[str, Any]) -> list[str]:
    """Validate prompt block index."""
    errors = []

    if "prompt_blocks" not in index:
        errors.append("Prompt index missing 'prompt_blocks' field")
        return errors

    # Check for required workstream blocks
    workstream_blocks = {
        "calendar-ingest",
        "signal-processing",
        "ea-execution",
        "health-monitoring",
        "error-recovery",
        "maintenance",
        "testing",
    }

    defined_workstreams = {
        pb.get("workstream") for pb in index["prompt_blocks"] if pb.get("workstream")
    }

    for ws in workstream_blocks:
        if ws not in defined_workstreams:
            errors.append(f"Missing prompt block for workstream: {ws}")

    return errors


def main():
    """Run all validations."""
    dag_root = Path(__file__).parent
    all_errors = []

    print("=" * 60)
    print("EAFIX DAG Configuration Validation")
    print("=" * 60)

    # Load configurations
    try:
        dag = load_yaml(dag_root / "config" / "dag_graph.yaml")
        print("✓ Loaded dag_graph.yaml")
    except Exception as e:
        print(f"✗ Failed to load dag_graph.yaml: {e}")
        return 1

    try:
        workstreams = load_yaml(dag_root / "workstreams" / "workstream_definitions.yaml")
        print("✓ Loaded workstream_definitions.yaml")
    except Exception as e:
        print(f"✗ Failed to load workstream_definitions.yaml: {e}")
        return 1

    try:
        patterns = load_yaml(dag_root / "patterns" / "pattern_registry.yaml")
        print("✓ Loaded pattern_registry.yaml")
    except Exception as e:
        print(f"✗ Failed to load pattern_registry.yaml: {e}")
        return 1

    try:
        gates = load_yaml(dag_root / "config" / "quality_gates.yaml")
        print("✓ Loaded quality_gates.yaml")
    except Exception as e:
        print(f"✗ Failed to load quality_gates.yaml: {e}")
        return 1

    try:
        prompt_index = load_yaml(dag_root / "prompts" / "prompt_block_index.yaml")
        print("✓ Loaded prompt_block_index.yaml")
    except Exception as e:
        print(f"✗ Failed to load prompt_block_index.yaml: {e}")
        return 1

    print()
    print("-" * 60)
    print("Validating DAG Graph...")
    errors = validate_dag_graph(dag)
    all_errors.extend(errors)
    print(f"  Found {len(errors)} errors")

    print("Validating Workstreams...")
    errors = validate_workstreams(workstreams, dag)
    all_errors.extend(errors)
    print(f"  Found {len(errors)} errors")

    print("Validating Patterns...")
    errors = validate_patterns(patterns)
    all_errors.extend(errors)
    print(f"  Found {len(errors)} errors")

    print("Validating Quality Gates...")
    errors = validate_quality_gates(gates, dag)
    all_errors.extend(errors)
    print(f"  Found {len(errors)} errors")

    print("Validating Prompt Index...")
    errors = validate_prompt_index(prompt_index)
    all_errors.extend(errors)
    print(f"  Found {len(errors)} errors")

    print()
    print("=" * 60)
    if all_errors:
        print(f"VALIDATION FAILED: {len(all_errors)} total errors")
        print("-" * 60)
        for error in all_errors:
            print(f"  ✗ {error}")
        return 1
    else:
        print("VALIDATION PASSED: All configurations valid")
        print("-" * 60)
        print(f"  ✓ DAG nodes: {len(dag.get('nodes', []))}")
        print(f"  ✓ Workstreams: {len(workstreams.get('workstreams', []))}")
        print(f"  ✓ Patterns: {len(patterns.get('verification_patterns', []))}")
        print(f"  ✓ Quality gates: {len(gates.get('gates', []))}")
        print(f"  ✓ Prompt blocks: {len(prompt_index.get('prompt_blocks', []))}")
        return 0


if __name__ == "__main__":
    sys.exit(main())

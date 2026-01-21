# DOC_LINK: DOC-CORE-STATE-DAG-UTILS-170
"""Canonical DAG representation and analysis.

This module is the ONE TRUE PLACE for all DAG logic in the pipeline.

All workstream dependency graph operations MUST use the functions defined here:
- build_dependency_graph: Create canonical DepGraph from bundles
- detect_cycles: Find dependency cycles
- compute_topological_levels: Compute parallel execution waves
- compute_critical_path: Find longest path through DAG
- analyze_bundles: One-shot analysis returning DagAnalysis

All DAG consumers (parallelism_detector, plan_validator, scheduler) MUST
operate on the shared DepGraph representation rather than re-implementing
graph logic.

Requirement IDs:
- DAG-IMPL-001: All Phase/Workstream DAG operations MUST use dag_utils.py
- DAG-IMPL-002: All DAG consumers MUST use shared DepGraph representation
- DAG-IMPL-003: Cycle detection MUST be applied before computing topological levels
"""

# DOC_ID: DOC-CORE-STATE-DAG-UTILS-170

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class WorkstreamBundle:
    """Minimal workstream bundle for DAG analysis.
    
    This is a lightweight data structure used by DAG utilities.
    """
    id: str
    openspec_change: str
    ccpm_issue: int
    gate: int
    files_scope: tuple[str, ...]
    depends_on: tuple[str, ...]

# Canonical DAG representation used across the codebase
DepGraph = Dict[str, Set[str]]  # node_id -> set of node_ids it depends on


@dataclass(frozen=True)
class DagAnalysis:
    """Complete DAG analysis result.

    This is the standard struct passed between modules that need DAG info.
    """

    dep_graph: DepGraph  # Forward graph (node -> dependencies)
    reverse_graph: DepGraph  # Reverse graph (node -> dependents)
    topo_levels: List[Set[str]]  # Execution waves (empty if cycles exist)
    cycles: List[List[str]]  # List of cycles (empty if valid DAG)
    critical_path: List[str]  # Longest path through DAG
    critical_path_weight: float  # Total weight of critical path


def build_dependency_graph(
    bundles: Sequence[WorkstreamBundle],
) -> DepGraph:
    """Build canonical dependency graph from WorkstreamBundle.depends_on.

    Returns:
        DepGraph where dep_graph[ws_id] = set of workstream_ids that ws_id depends on

    Note:
        This is the FORWARD graph: node -> its prerequisites.
        Use build_reverse_graph() to get node -> its dependents.
    """
    dep_graph: DepGraph = {}

    # First, ensure every bundle id is present in the graph
    for bundle in bundles:
        dep_graph.setdefault(bundle.id, set())

    # Then, add edges from depends_on
    for bundle in bundles:
        for dep in sorted(set(bundle.depends_on or [])):
            # Auto-add missing dependencies (they may be in other phases)
            if dep not in dep_graph:
                dep_graph[dep] = set()
            dep_graph[bundle.id].add(dep)

    return dep_graph


def build_reverse_graph(dep_graph: DepGraph) -> DepGraph:
    """Compute reverse adjacency (who depends on this node).

    Args:
        dep_graph: Forward dependency graph

    Returns:
        Reverse graph where reverse_graph[ws_id] = set of workstream_ids that depend on ws_id
    """
    reverse_graph: DepGraph = {node: set() for node in dep_graph}

    for node, deps in dep_graph.items():
        for dep in deps:
            if dep not in reverse_graph:
                reverse_graph[dep] = set()
            reverse_graph[dep].add(node)

    return reverse_graph


def detect_cycles(dep_graph: DepGraph) -> List[List[str]]:
    """Detect cycles in dependency graph using DFS.

    Returns:
        List of cycles, where each cycle is a list of node_ids.
        Empty list if DAG is valid (no cycles).

    Algorithm:
        DFS with three states (unvisited=0, in_stack=1, visited=2).
        When we encounter a node in_stack, we've found a cycle.
    """
    visited: Dict[str, int] = {node: 0 for node in dep_graph}
    cycles: List[List[str]] = []

    def dfs(node: str, path: List[str]) -> None:
        if visited[node] == 1:  # in_stack - found a cycle
            # Extract cycle from path
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])  # Don't add node again!
            return
        if visited[node] == 2:  # already visited
            return

        visited[node] = 1  # mark in_stack
        for dep in sorted(dep_graph.get(node, set())):
            dfs(dep, path + [node])  # Add current node to path before recursing
        visited[node] = 2  # mark visited

    for node in sorted(dep_graph.keys()):
        if visited[node] == 0:
            dfs(node, [])  # Start with empty path

    # Normalize cycles: rotate to smallest, deduplicate
    norm_cycles: List[List[str]] = []
    seen: Set[Tuple[str, ...]] = set()

    for cycle in cycles:
        if not cycle:
            continue

        # Rotate to start at lexicographically smallest node
        min_idx = min(range(len(cycle)), key=lambda i: cycle[i])
        ordered = cycle[min_idx:] + cycle[:min_idx]

        cycle_tuple = tuple(ordered)
        if cycle_tuple not in seen:
            seen.add(cycle_tuple)
            norm_cycles.append(ordered)

    return norm_cycles


def compute_topological_levels(
    dep_graph: DepGraph,
) -> List[Set[str]]:
    """Compute topological sort as parallel execution waves.

    Uses Kahn's algorithm to emit "waves" of nodes that can execute in parallel.

    Args:
        dep_graph: Forward dependency graph

    Returns:
        List of sets, where each set is a "wave" of nodes with no dependencies
        between them (can run in parallel).

    Raises:
        ValueError: If cycles are detected (cannot compute topological sort)

    Note:
        Callers SHOULD call detect_cycles() first and handle cycles explicitly.
        This function raises as a safety check.
    """
    # Calculate in-degree (number of unresolved dependencies)
    in_degree: Dict[str, int] = {node: 0 for node in dep_graph}
    for node, deps in dep_graph.items():
        in_degree[node] = len(deps)

    # Start with all nodes that have no dependencies
    ready = sorted(n for n, deg in in_degree.items() if deg == 0)
    levels: List[Set[str]] = []
    processed: Set[str] = set()

    while ready:
        level = set(ready)
        levels.append(level)
        processed.update(ready)

        next_ready: List[str] = []

        # For each node in this wave, decrement in_degree of its dependents
        for node in ready:
            # Find all nodes that depend on this one
            for dependent, deps in dep_graph.items():
                if node in deps and dependent not in processed:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_ready.append(dependent)

        ready = sorted(set(next_ready))

    # If any node still has in_degree > 0, there is a cycle
    unprocessed = [n for n, deg in in_degree.items() if deg > 0]
    if unprocessed:
        raise ValueError(
            f"Cycle detected; cannot compute topological levels. "
            f"Unprocessed nodes: {unprocessed}"
        )

    return levels


def compute_critical_path(
    dep_graph: DepGraph,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[List[str], float]:
    """Compute critical path (longest path) through the DAG.

    Args:
        dep_graph: Forward dependency graph
        weights: Optional node weights (cost/duration). Defaults to 1.0 per node.

    Returns:
        (path_node_ids, total_weight) where path_node_ids is ordered from start to end

    Algorithm:
        Dynamic programming over topologically sorted nodes.
        For each node, compute longest path TO that node, then trace back.
    """
    if not dep_graph:
        return ([], 0.0)

    # Default weight = 1.0 per node
    node_weights = weights or {node: 1.0 for node in dep_graph}

    # Get topological levels (raises if cycle exists)
    try:
        levels = compute_topological_levels(dep_graph)
    except ValueError:
        # Can't compute critical path in a cyclic graph
        return ([], 0.0)

    # Flatten levels to get topological order
    topo_order = [node for level in levels for node in sorted(level)]

    # DP: longest_path[node] = (weight, predecessor)
    longest_path: Dict[str, Tuple[float, Optional[str]]] = {}

    for node in dep_graph:
        longest_path[node] = (node_weights.get(node, 1.0), None)

    # Process nodes in topological order
    for node in topo_order:
        node_weight = node_weights.get(node, 1.0)
        current_weight, _ = longest_path[node]

        # Update all dependents
        reverse_graph = build_reverse_graph(dep_graph)
        for dependent in reverse_graph.get(node, set()):
            dependent_weight = node_weights.get(dependent, 1.0)
            new_weight = current_weight + dependent_weight

            if new_weight > longest_path[dependent][0]:
                longest_path[dependent] = (new_weight, node)

    # Find node with maximum weight
    if not longest_path:
        return ([], 0.0)

    end_node = max(longest_path.keys(), key=lambda n: longest_path[n][0])
    max_weight, _ = longest_path[end_node]

    # Trace back to build path
    path: List[str] = []
    current: Optional[str] = end_node

    while current is not None:
        path.append(current)
        _, pred = longest_path[current]
        current = pred

    path.reverse()
    return (path, max_weight)


def analyze_bundles(
    bundles: Sequence[WorkstreamBundle],
    weights: Optional[Dict[str, float]] = None,
) -> DagAnalysis:
    """One-shot DAG analysis used by most callers.

    This is the primary entry point for modules that need complete DAG analysis.

    Args:
        bundles: List of workstream bundles to analyze
        weights: Optional node weights for critical path calculation

    Returns:
        DagAnalysis with complete graph analysis

    Note:
        If cycles are detected, topo_levels will be empty and critical_path
        will be empty. Callers MUST check analysis.cycles before using
        topo_levels or critical_path.
    """
    dep_graph = build_dependency_graph(bundles)
    reverse_graph = build_reverse_graph(dep_graph)
    cycles = detect_cycles(dep_graph)

    # Only compute topo_levels and critical_path if DAG is valid
    if cycles:
        topo_levels: List[Set[str]] = []
        critical_path: List[str] = []
        critical_path_weight = 0.0
    else:
        topo_levels = compute_topological_levels(dep_graph)
        critical_path, critical_path_weight = compute_critical_path(dep_graph, weights)

    return DagAnalysis(
        dep_graph=dep_graph,
        reverse_graph=reverse_graph,
        topo_levels=topo_levels,
        cycles=cycles,
        critical_path=critical_path,
        critical_path_weight=critical_path_weight,
    )

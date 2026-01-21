# DOC_LINK: DOC-CORE-STATE-TEST-DAG-UTILS-126
"""Tests for canonical DAG utilities.

Validates DAG-IMPL-001, DAG-IMPL-002, DAG-IMPL-003 requirements.
"""

# DOC_ID: DOC-CORE-STATE-TEST-DAG-UTILS-126

import pytest
import sys
from pathlib import Path

# Import from new location using importlib
try:
    from . import dag_utils
    from .dag_utils import (
        WorkstreamBundle,
        DagAnalysis,
        analyze_bundles,
        build_dependency_graph,
        build_reverse_graph,
        compute_critical_path,
        compute_topological_levels,
        detect_cycles,
    )
except ImportError:
    # Fallback: load module using importlib
    import importlib.util
    dag_utils_path = Path(__file__).parent / 'dag_utils.py'
    if dag_utils_path.exists():
        spec = importlib.util.spec_from_file_location("dag_utils", dag_utils_path)
        dag_utils = importlib.util.module_from_spec(spec)
        sys.modules["dag_utils"] = dag_utils
        spec.loader.exec_module(dag_utils)
        
        WorkstreamBundle = dag_utils.WorkstreamBundle
        DagAnalysis = dag_utils.DagAnalysis
        analyze_bundles = dag_utils.analyze_bundles
        build_dependency_graph = dag_utils.build_dependency_graph
        build_reverse_graph = dag_utils.build_reverse_graph
        compute_critical_path = dag_utils.compute_critical_path
        compute_topological_levels = dag_utils.compute_topological_levels
        detect_cycles = dag_utils.detect_cycles
    else:
        pytest.skip("dag_utils module not found", allow_module_level=True)


def make_bundle(ws_id: str, depends_on: list[str] | None = None) -> WorkstreamBundle:
    """Helper to create minimal WorkstreamBundle for testing."""
    return WorkstreamBundle(
        id=ws_id,
        openspec_change="test-change",
        ccpm_issue=1,
        gate=1,
        files_scope=(),
        depends_on=tuple(depends_on or []),
    )


class TestBuildDependencyGraph:
    """Test canonical DepGraph construction."""

    def test_empty_bundles(self):
        graph = build_dependency_graph([])
        assert graph == {}

    def test_single_bundle_no_deps(self):
        bundles = [make_bundle("ws-a")]
        graph = build_dependency_graph(bundles)
        assert graph == {"ws-a": set()}

    def test_linear_chain(self):
        """A -> B -> C"""
        bundles = [
            make_bundle("ws-a"),
            make_bundle("ws-b", ["ws-a"]),
            make_bundle("ws-c", ["ws-b"]),
        ]
        graph = build_dependency_graph(bundles)
        assert graph == {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-b"},
        }

    def test_parallel_branches(self):
        """A -> B, A -> C (B and C can run in parallel)"""
        bundles = [
            make_bundle("ws-a"),
            make_bundle("ws-b", ["ws-a"]),
            make_bundle("ws-c", ["ws-a"]),
        ]
        graph = build_dependency_graph(bundles)
        assert graph == {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-a"},
        }

    def test_diamond_dependency(self):
        """
        A -> B -> D
        A -> C -> D
        """
        bundles = [
            make_bundle("ws-a"),
            make_bundle("ws-b", ["ws-a"]),
            make_bundle("ws-c", ["ws-a"]),
            make_bundle("ws-d", ["ws-b", "ws-c"]),
        ]
        graph = build_dependency_graph(bundles)
        assert graph == {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-a"},
            "ws-d": {"ws-b", "ws-c"},
        }

    def test_missing_dependency_auto_added(self):
        """Dependencies not in bundle list are auto-added."""
        bundles = [make_bundle("ws-b", ["ws-a"])]
        graph = build_dependency_graph(bundles)
        assert "ws-a" in graph
        assert graph["ws-a"] == set()


class TestBuildReverseGraph:
    """Test reverse graph construction."""

    def test_empty_graph(self):
        reverse = build_reverse_graph({})
        assert reverse == {}

    def test_linear_chain(self):
        """A -> B -> C becomes C <- B <- A"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-b"},
        }
        reverse = build_reverse_graph(dep_graph)
        assert reverse == {
            "ws-a": {"ws-b"},
            "ws-b": {"ws-c"},
            "ws-c": set(),
        }

    def test_diamond_dependency(self):
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-a"},
            "ws-d": {"ws-b", "ws-c"},
        }
        reverse = build_reverse_graph(dep_graph)
        assert reverse == {
            "ws-a": {"ws-b", "ws-c"},
            "ws-b": {"ws-d"},
            "ws-c": {"ws-d"},
            "ws-d": set(),
        }


class TestDetectCycles:
    """Test cycle detection (DAG-IMPL-003)."""

    def test_no_cycles_empty_graph(self):
        cycles = detect_cycles({})
        assert cycles == []

    def test_no_cycles_linear_chain(self):
        """A -> B -> C has no cycles"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-b"},
        }
        cycles = detect_cycles(dep_graph)
        assert cycles == []

    def test_no_cycles_diamond(self):
        """Diamond dependency has no cycles"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-a"},
            "ws-d": {"ws-b", "ws-c"},
        }
        cycles = detect_cycles(dep_graph)
        assert cycles == []

    def test_simple_cycle_two_nodes(self):
        """A -> B -> A"""
        dep_graph = {
            "ws-a": {"ws-b"},
            "ws-b": {"ws-a"},
        }
        cycles = detect_cycles(dep_graph)
        assert len(cycles) == 1
        # Cycle should be normalized to start at 'ws-a' (lexicographically smallest)
        assert cycles[0] == ["ws-a", "ws-b"]

    def test_simple_cycle_three_nodes(self):
        """A -> B -> C -> A"""
        dep_graph = {
            "ws-a": {"ws-c"},
            "ws-b": {"ws-a"},
            "ws-c": {"ws-b"},
        }
        cycles = detect_cycles(dep_graph)
        assert len(cycles) == 1
        assert cycles[0] == ["ws-a", "ws-c", "ws-b"]

    def test_self_cycle(self):
        """A -> A"""
        dep_graph = {
            "ws-a": {"ws-a"},
        }
        cycles = detect_cycles(dep_graph)
        assert len(cycles) == 1
        assert cycles[0] == ["ws-a"]

    def test_multiple_cycles(self):
        """Two separate cycles"""
        dep_graph = {
            "ws-a": {"ws-b"},
            "ws-b": {"ws-a"},
            "ws-c": {"ws-d"},
            "ws-d": {"ws-c"},
        }
        cycles = detect_cycles(dep_graph)
        assert len(cycles) == 2
        # Both cycles should be normalized
        assert ["ws-a", "ws-b"] in cycles
        assert ["ws-c", "ws-d"] in cycles


class TestComputeTopologicalLevels:
    """Test parallel wave computation (DAG-IMPL-003)."""

    def test_empty_graph(self):
        levels = compute_topological_levels({})
        assert levels == []

    def test_single_node(self):
        levels = compute_topological_levels({"ws-a": set()})
        assert levels == [{"ws-a"}]

    def test_linear_chain(self):
        """A -> B -> C produces 3 waves"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-b"},
        }
        levels = compute_topological_levels(dep_graph)
        assert levels == [
            {"ws-a"},
            {"ws-b"},
            {"ws-c"},
        ]

    def test_parallel_branches(self):
        """A -> B, A -> C produces 2 waves: [A], [B, C]"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-a"},
        }
        levels = compute_topological_levels(dep_graph)
        assert levels == [
            {"ws-a"},
            {"ws-b", "ws-c"},
        ]

    def test_diamond_dependency(self):
        """
        A -> B -> D
        A -> C -> D
        Produces: [A], [B, C], [D]
        """
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-a"},
            "ws-d": {"ws-b", "ws-c"},
        }
        levels = compute_topological_levels(dep_graph)
        assert levels == [
            {"ws-a"},
            {"ws-b", "ws-c"},
            {"ws-d"},
        ]

    def test_multiple_roots(self):
        """A, B, C all independent"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": set(),
            "ws-c": set(),
        }
        levels = compute_topological_levels(dep_graph)
        assert levels == [{"ws-a", "ws-b", "ws-c"}]

    def test_cycle_raises_error(self):
        """Cycle should raise ValueError"""
        dep_graph = {
            "ws-a": {"ws-b"},
            "ws-b": {"ws-a"},
        }
        with pytest.raises(ValueError, match="Cycle detected"):
            compute_topological_levels(dep_graph)


class TestComputeCriticalPath:
    """Test critical path calculation."""

    def test_empty_graph(self):
        path, weight = compute_critical_path({})
        assert path == []
        assert weight == 0.0

    def test_single_node(self):
        path, weight = compute_critical_path({"ws-a": set()})
        assert path == ["ws-a"]
        assert weight == 1.0

    def test_linear_chain_uniform_weights(self):
        """A -> B -> C with weight 1.0 each"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-b"},
        }
        path, weight = compute_critical_path(dep_graph)
        assert path == ["ws-a", "ws-b", "ws-c"]
        assert weight == 3.0

    def test_linear_chain_custom_weights(self):
        """A(2) -> B(3) -> C(1) = 6.0"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-b"},
        }
        weights = {"ws-a": 2.0, "ws-b": 3.0, "ws-c": 1.0}
        path, weight = compute_critical_path(dep_graph, weights)
        assert path == ["ws-a", "ws-b", "ws-c"]
        assert weight == 6.0

    def test_diamond_critical_path(self):
        """
        A(1) -> B(5) -> D(1)  = 7.0 (critical path)
        A(1) -> C(2) -> D(1)  = 4.0
        """
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-a"},
            "ws-d": {"ws-b", "ws-c"},
        }
        weights = {"ws-a": 1.0, "ws-b": 5.0, "ws-c": 2.0, "ws-d": 1.0}
        path, weight = compute_critical_path(dep_graph, weights)
        assert path == ["ws-a", "ws-b", "ws-d"]
        assert weight == 7.0

    def test_parallel_branches(self):
        """A -> B(10), A -> C(2): B path is critical"""
        dep_graph = {
            "ws-a": set(),
            "ws-b": {"ws-a"},
            "ws-c": {"ws-a"},
        }
        weights = {"ws-a": 1.0, "ws-b": 10.0, "ws-c": 2.0}
        path, weight = compute_critical_path(dep_graph, weights)
        assert path == ["ws-a", "ws-b"]
        assert weight == 11.0

    def test_cycle_returns_empty(self):
        """Cycle should return empty path"""
        dep_graph = {
            "ws-a": {"ws-b"},
            "ws-b": {"ws-a"},
        }
        path, weight = compute_critical_path(dep_graph)
        assert path == []
        assert weight == 0.0


class TestAnalyzeBundles:
    """Test one-shot analysis function."""

    def test_empty_bundles(self):
        analysis = analyze_bundles([])
        assert analysis.dep_graph == {}
        assert analysis.reverse_graph == {}
        assert analysis.topo_levels == []
        assert analysis.cycles == []
        assert analysis.critical_path == []
        assert analysis.critical_path_weight == 0.0

    def test_valid_dag(self):
        """Valid DAG produces complete analysis"""
        bundles = [
            make_bundle("ws-a"),
            make_bundle("ws-b", ["ws-a"]),
            make_bundle("ws-c", ["ws-a"]),
            make_bundle("ws-d", ["ws-b", "ws-c"]),
        ]
        analysis = analyze_bundles(bundles)

        # Should have valid graphs
        assert len(analysis.dep_graph) == 4
        assert len(analysis.reverse_graph) == 4

        # No cycles
        assert analysis.cycles == []

        # Should have 3 levels
        assert len(analysis.topo_levels) == 3
        assert analysis.topo_levels[0] == {"ws-a"}
        assert analysis.topo_levels[1] == {"ws-b", "ws-c"}
        assert analysis.topo_levels[2] == {"ws-d"}

        # Should have critical path (A -> B -> D = 3 nodes)
        assert len(analysis.critical_path) > 0
        assert analysis.critical_path_weight == 3.0

    def test_dag_with_cycles(self):
        """Cycles should prevent topo_levels and critical_path"""
        bundles = [
            make_bundle("ws-a", ["ws-b"]),
            make_bundle("ws-b", ["ws-a"]),
        ]
        analysis = analyze_bundles(bundles)

        # Should detect cycle
        assert len(analysis.cycles) == 1

        # topo_levels and critical_path should be empty
        assert analysis.topo_levels == []
        assert analysis.critical_path == []
        assert analysis.critical_path_weight == 0.0

    def test_custom_weights(self):
        """Custom weights should affect critical path"""
        bundles = [
            make_bundle("ws-a"),
            make_bundle("ws-b", ["ws-a"]),
        ]
        weights = {"ws-a": 10.0, "ws-b": 5.0}
        analysis = analyze_bundles(bundles, weights)

        assert analysis.critical_path == ["ws-a", "ws-b"]
        assert analysis.critical_path_weight == 15.0


class TestDagRequirements:
    """Validate DAG-IMPL-* requirements."""

    def test_dag_impl_001_single_source_of_truth(self):
        """DAG-IMPL-001: All operations in dag_utils.py"""
        # This is validated by module structure - all functions defined here
        from core.state import dag_utils as m010003_dag_utils

        required_functions = [
            "build_dependency_graph",
            "build_reverse_graph",
            "detect_cycles",
            "compute_topological_levels",
            "compute_critical_path",
            "analyze_bundles",
        ]

        for func_name in required_functions:
            assert hasattr(dag_utils, func_name), f"Missing {func_name}"

    def test_dag_impl_002_shared_depgraph_type(self):
        """DAG-IMPL-002: All consumers use DepGraph type"""
        from modules.core_state.m010003_dag_utils import DepGraph

        # DepGraph should be Dict[str, Set[str]]
        bundles = [make_bundle("ws-a"), make_bundle("ws-b", ["ws-a"])]
        graph = build_dependency_graph(bundles)

        assert isinstance(graph, dict)
        for node_id, deps in graph.items():
            assert isinstance(node_id, str)
            assert isinstance(deps, set)

    def test_dag_impl_003_cycles_before_topo(self):
        """DAG-IMPL-003: Cycle detection before topological levels"""
        bundles = [
            make_bundle("ws-a", ["ws-b"]),
            make_bundle("ws-b", ["ws-a"]),
        ]

        # analyze_bundles should detect cycles and skip topo computation
        analysis = analyze_bundles(bundles)
        assert len(analysis.cycles) > 0
        assert analysis.topo_levels == []

        # Calling compute_topological_levels directly should raise
        dep_graph = build_dependency_graph(bundles)
        with pytest.raises(ValueError):
            compute_topological_levels(dep_graph)

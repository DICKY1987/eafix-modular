# DOC_LINK: DOC-TEST-ENGINE-TEST-DAG-BUILDER-116
"""
Tests for DAG Builder
"""

# DOC_ID: DOC-TEST-ENGINE-TEST-DAG-BUILDER-116

import pytest
import sys
from pathlib import Path

# Import from new location using importlib
try:
    from .dag_builder import DAGBuilder
except ImportError:
    # Fallback: load module using importlib
    import importlib.util
    dag_builder_path = Path(__file__).parent / 'dag_builder.py'
    if dag_builder_path.exists():
        spec = importlib.util.spec_from_file_location("dag_builder", dag_builder_path)
        dag_builder = importlib.util.module_from_spec(spec)
        sys.modules["dag_builder"] = dag_builder
        spec.loader.exec_module(dag_builder)
        
        DAGBuilder = dag_builder.DAGBuilder
    else:
        pytest.skip("dag_builder module not found", allow_module_level=True)


def test_simple_dag():
    """Test simple DAG with linear dependencies."""
    workstreams = [
        {"workstream_id": "a", "dependencies": []},
        {"workstream_id": "b", "dependencies": ["a"]},
        {"workstream_id": "c", "dependencies": ["b"]},
    ]

    builder = DAGBuilder()
    plan = builder.build_from_workstreams(workstreams)

    assert plan["validated"] is True
    assert plan["total_workstreams"] == 3
    assert plan["total_waves"] == 3
    assert plan["waves"] == [["a"], ["b"], ["c"]]


def test_parallel_dag():
    """Test DAG with parallel branches."""
    workstreams = [
        {"workstream_id": "a", "dependencies": []},
        {"workstream_id": "b", "dependencies": ["a"]},
        {"workstream_id": "c", "dependencies": ["a"]},
        {"workstream_id": "d", "dependencies": ["b", "c"]},
    ]

    builder = DAGBuilder()
    plan = builder.build_from_workstreams(workstreams)

    assert plan["validated"] is True
    assert plan["total_waves"] == 3
    assert "a" in plan["waves"][0]
    assert set(plan["waves"][1]) == {"b", "c"}
    assert "d" in plan["waves"][2]


def test_cycle_detection():
    """Test cycle detection."""
    workstreams = [
        {"workstream_id": "a", "dependencies": ["b"]},
        {"workstream_id": "b", "dependencies": ["a"]},
    ]

    builder = DAGBuilder()

    with pytest.raises(ValueError, match="Dependency cycles"):
        builder.build_from_workstreams(workstreams)


def test_no_dependencies():
    """Test workstreams with no dependencies."""
    workstreams = [
        {"workstream_id": "a"},
        {"workstream_id": "b"},
        {"workstream_id": "c"},
    ]

    builder = DAGBuilder()
    plan = builder.build_from_workstreams(workstreams)

    assert plan["total_waves"] == 1
    assert set(plan["waves"][0]) == {"a", "b", "c"}

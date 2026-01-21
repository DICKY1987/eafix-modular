# DOC_LINK: DOC-CORE-ENGINE-DAG-BUILDER-147
"""
DAG Builder - Constructs Execution DAG from Workstreams
Performs topological sort for wave-based parallel execution
"""

# DOC_ID: DOC-CORE-ENGINE-DAG-BUILDER-147

from collections import defaultdict, deque
from typing import Dict, List, Optional


class DAGBuilder:
    """Build directed acyclic graph from workstream dependencies."""

    def __init__(self):
        self.graph = defaultdict(list)
        self.in_degree = defaultdict(int)
        self.workstreams = {}

    def build_from_workstreams(self, workstreams: List[Dict]) -> Dict:
        """Build execution plan from workstreams."""
        # Build graph
        for ws in workstreams:
            ws_id = ws.get("workstream_id") or ws.get("id")
            self.workstreams[ws_id] = ws

            deps = ws.get("dependencies", []) or ws.get("depends_on", [])
            if isinstance(deps, str):
                deps = [deps] if deps else []

            for dep in deps:
                self.graph[dep].append(ws_id)
                self.in_degree[ws_id] += 1

            # Ensure all nodes exist in in_degree
            if ws_id not in self.in_degree:
                self.in_degree[ws_id] = 0

        # Validate DAG
        cycles = self.detect_cycles()
        if cycles:
            raise ValueError(f"Dependency cycles detected: {cycles}")

        # Topological sort to get waves
        waves = self.topological_sort()

        return {
            "waves": waves,
            "total_workstreams": len(workstreams),
            "total_waves": len(waves),
            "graph": dict(self.graph),
            "validated": True,
        }

    def extract_dependencies(self, workstream: Dict) -> List[str]:
        """Extract dependencies from workstream."""
        deps = workstream.get("dependencies", []) or workstream.get("depends_on", [])
        if isinstance(deps, str):
            return [deps] if deps else []
        return deps if deps else []

    def topological_sort(self) -> List[List[str]]:
        """Perform topological sort using Kahn's algorithm, returning waves."""
        waves = []
        in_degree_copy = self.in_degree.copy()
        queue = deque([node for node in in_degree_copy if in_degree_copy[node] == 0])

        while queue:
            wave = []
            wave_size = len(queue)

            for _ in range(wave_size):
                node = queue.popleft()
                wave.append(node)

                for neighbor in self.graph[node]:
                    in_degree_copy[neighbor] -= 1
                    if in_degree_copy[neighbor] == 0:
                        queue.append(neighbor)

            if wave:
                waves.append(wave)

        return waves

    def detect_cycles(self) -> Optional[List[str]]:
        """Detect cycles using DFS."""
        visited = set()
        rec_stack = set()
        cycle_path = []

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle_path.extend(path[cycle_start:])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in list(self.graph.keys()):
            if node not in visited:
                if dfs(node, []):
                    return cycle_path

        return None

    def validate_dag(self) -> bool:
        """Validate DAG has no cycles."""
        return self.detect_cycles() is None

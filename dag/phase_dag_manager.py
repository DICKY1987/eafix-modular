# DOC_LINK: DOC-CORE-CORE-PHASE-DAG-MANAGER-397
"""
Phase DAG Manager
Manages phase dependencies and execution order
"""
# DOC_ID: DOC-CORE-CORE-PHASE-DAG-MANAGER-397

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path
from collections import defaultdict, deque

class PhaseStatus(Enum):
    """Phase execution status"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class PhaseNode:
    """Represents a phase in the DAG"""
    phase_id: str
    dependencies: List[str]
    contract_version: str
    status: PhaseStatus
    parallel_safe: bool = True
    timeout_minutes: int = 60

class PhaseDependencyDAG:
    """Manages phase dependency graph and execution order"""
    
    def __init__(self, dag_path: Path):
        self.dag_path = dag_path
        self.nodes: Dict[str, PhaseNode] = {}
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._load_dag()
    
    def _load_dag(self):
        """Load DAG from YAML definition"""
        with open(self.dag_path) as f:
            dag_data = yaml.safe_load(f)
        
        # Build nodes
        for phase_id, phase_config in dag_data.get("phases", {}).items():
            node = PhaseNode(
                phase_id=phase_id,
                dependencies=phase_config.get("dependencies", []),
                contract_version=phase_config.get("contract_version", "1.0.0"),
                status=PhaseStatus.PENDING,
                parallel_safe=phase_config.get("parallel_safe", True),
                timeout_minutes=phase_config.get("timeout_minutes", 60)
            )
            self.nodes[phase_id] = node
            
            # Build adjacency lists
            for dep in node.dependencies:
                self.adjacency[dep].add(phase_id)
                self.reverse_adjacency[phase_id].add(dep)
    
    def get_execution_order(self) -> List[List[str]]:
        """Get topological execution order with parallel batches"""
        # Khan's algorithm for topological sort with level tracking
        in_degree = {node_id: len(self.reverse_adjacency[node_id]) 
                    for node_id in self.nodes}
        
        levels: List[List[str]] = []
        ready = deque([node_id for node_id, degree in in_degree.items() 
                      if degree == 0])
        
        while ready:
            # All nodes in current level can execute in parallel
            current_level = []
            level_size = len(ready)
            
            for _ in range(level_size):
                node_id = ready.popleft()
                current_level.append(node_id)
                
                # Reduce in-degree of dependent nodes
                for dependent in self.adjacency[node_id]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        ready.append(dependent)
            
            levels.append(current_level)
        
        # Check for cycles
        if sum(len(level) for level in levels) != len(self.nodes):
            raise ValueError("Cycle detected in phase DAG")
        
        return levels
    
    def get_ready_phases(self) -> List[str]:
        """Get phases ready to execute (dependencies satisfied)"""
        ready = []
        for node_id, node in self.nodes.items():
            if node.status != PhaseStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_satisfied = all(
                self.nodes[dep].status == PhaseStatus.COMPLETED
                for dep in node.dependencies
            )
            
            if deps_satisfied:
                ready.append(node_id)
        
        return ready
    
    def mark_completed(self, phase_id: str):
        """Mark phase as completed"""
        self.nodes[phase_id].status = PhaseStatus.COMPLETED
    
    def mark_failed(self, phase_id: str):
        """Mark phase as failed and propagate to dependents"""
        self.nodes[phase_id].status = PhaseStatus.FAILED
        
        # Mark all transitive dependents as skipped
        to_skip = list(self.adjacency[phase_id])
        visited = set()
        
        while to_skip:
            dependent = to_skip.pop()
            if dependent in visited:
                continue
            visited.add(dependent)
            
            self.nodes[dependent].status = PhaseStatus.SKIPPED
            to_skip.extend(self.adjacency[dependent])
    
    def get_critical_path(self) -> List[str]:
        """Find longest path (critical path) through DAG"""
        # Calculate earliest start times
        topo_order = [p for level in self.get_execution_order() for p in level]
        earliest = {phase_id: 0 for phase_id in self.nodes}
        
        for phase_id in topo_order:
            node = self.nodes[phase_id]
            for dep in node.dependencies:
                earliest[phase_id] = max(
                    earliest[phase_id],
                    earliest[dep] + self.nodes[dep].timeout_minutes
                )
        
        # Backtrack to find critical path
        end_phase = max(earliest.items(), key=lambda x: x[1])[0]
        path = []
        current = end_phase
        
        while current:
            path.append(current)
            node = self.nodes[current]
            
            if not node.dependencies:
                break
            
            # Find dependency on critical path
            critical_dep = max(
                node.dependencies,
                key=lambda d: earliest[d]
            )
            current = critical_dep
        
        return list(reversed(path))
    
    def validate_dag(self) -> Tuple[bool, List[str]]:
        """Validate DAG structure"""
        errors = []
        
        # Check for undefined dependencies
        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    errors.append(f"Phase {node_id} depends on undefined phase {dep}")
        
        # Check for cycles
        try:
            self.get_execution_order()
        except ValueError as e:
            errors.append(str(e))
        
        # Check for orphaned phases (no path from root)
        # Find root nodes (no dependencies)
        roots = [nid for nid, node in self.nodes.items() if not node.dependencies]
        if not roots:
            errors.append("No root phases found (all phases have dependencies)")
        
        return len(errors) == 0, errors
    
    def export_dot(self) -> str:
        """Export DAG as Graphviz DOT format"""
        dot = "digraph PhaseDependencyDAG {\n"
        dot += "  rankdir=LR;\n"
        dot += "  node [shape=box];\n\n"
        
        # Nodes
        for node_id, node in self.nodes.items():
            color = {
                PhaseStatus.PENDING: "lightgray",
                PhaseStatus.READY: "yellow",
                PhaseStatus.RUNNING: "lightblue",
                PhaseStatus.COMPLETED: "lightgreen",
                PhaseStatus.FAILED: "red",
                PhaseStatus.SKIPPED: "orange"
            }[node.status]
            
            dot += f'  "{node_id}" [fillcolor={color}, style=filled];\n'
        
        # Edges
        dot += "\n"
        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                dot += f'  "{dep}" -> "{node_id}";\n'
        
        dot += "}\n"
        return dot
    
    def get_parallel_batches(self) -> List[List[str]]:
        """Get phases grouped by parallel execution batches"""
        execution_order = self.get_execution_order()
        
        # Filter out non-parallel-safe phases
        batches = []
        for level in execution_order:
            parallel = [p for p in level if self.nodes[p].parallel_safe]
            sequential = [p for p in level if not self.nodes[p].parallel_safe]
            
            # Add parallel batch
            if parallel:
                batches.append(parallel)
            
            # Add sequential phases as individual batches
            for phase in sequential:
                batches.append([phase])
        
        return batches

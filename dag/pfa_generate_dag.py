#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-GENERATE-DAG-948
"""
PFA Generate DAG - Automated DAG Generation from Process Steps

Automatically generates DAG (Directed Acyclic Graph) from process steps by:
1. Analyzing step dependencies (explicit depends_on, implicit from phases)
2. Detecting artifact-based dependencies (file producer/consumer)
3. Inferring operation sequencing from operation_kind taxonomy
4. Building execution waves for parallel processing
5. Computing critical path and execution estimates

Usage:
    python pfa_generate_dag.py [schema_file] [--output dag|waves|graphviz] [--phase PHASE]
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-GENERATE-DAG-948

import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from datetime import datetime
from collections import defaultdict, deque


class DAGGenerator:
    """Generate execution DAG from process steps."""
    
    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.schema = None
        self.steps = []
        self.dag = {}
        self.reverse_dag = {}
        self.waves = []
        
        # Artifact tracking for implicit dependencies
        self.artifact_producers: Dict[str, List[str]] = defaultdict(list)
        self.artifact_consumers: Dict[str, List[str]] = defaultdict(list)
        
        # Phase ordering
        self.phase_order = [
            '1_BOOTSTRAP',
            '2_DISCOVERY',
            '3_DESIGN',
            '4_APPROVAL',
            '5_REGISTRATION',
            '6_EXECUTION',
            '7_CONSOLIDATION',
            '8_MAINTENANCE',
            '9_SYNC_AND_FINALIZE'
        ]
        
        # Operation kind dependencies (some operations must follow others)
        self.operation_sequencing = {
            'validation': ['initialization'],
            'transformation': ['discovery', 'analysis'],
            'generation': ['design', 'approval'],
            'execution': ['registration', 'generation'],
            'aggregation': ['execution'],
            'persistence': ['aggregation', 'transformation'],
            'synchronization': ['persistence'],
            'reporting': ['aggregation', 'consolidation']
        }
    
    def load_schema(self) -> None:
        """Load process steps schema."""
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            self.schema = yaml.safe_load(f)
        self.steps = self.schema.get('steps', [])
        print(f"Loaded {len(self.steps)} process steps")
    
    def extract_explicit_dependencies(self) -> None:
        """Extract explicitly declared dependencies from steps."""
        for step in self.steps:
            step_id = step.get('step_id')
            self.dag[step_id] = set()
            
            # Explicit depends_on
            depends_on = step.get('depends_on', [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                self.dag[step_id].add(dep)
    
    def analyze_artifact_dependencies(self) -> None:
        """Infer dependencies from artifact production/consumption."""
        # First pass: identify producers and consumers
        for step in self.steps:
            step_id = step.get('step_id')
            
            # Artifacts created
            artifacts_created = step.get('artifacts_created', [])
            for artifact in artifacts_created:
                self.artifact_producers[artifact].append(step_id)
            
            # Artifacts updated (also produces)
            artifacts_updated = step.get('artifacts_updated', [])
            for artifact in artifacts_updated:
                self.artifact_producers[artifact].append(step_id)
            
            # Check inputs for artifact consumption
            inputs = step.get('inputs', [])
            for input_spec in inputs:
                if isinstance(input_spec, str):
                    # Parse "artifact_name: type" or just "artifact_name"
                    artifact_name = input_spec.split(':')[0].strip()
                    self.artifact_consumers[artifact_name].append(step_id)
            
            # Check artifact_registry_refs
            for ref in step.get('artifact_registry_refs', []):
                self.artifact_consumers[ref].append(step_id)
        
        # Second pass: create dependencies
        for artifact, consumers in self.artifact_consumers.items():
            producers = self.artifact_producers.get(artifact, [])
            
            # Each consumer depends on all producers of that artifact
            for consumer in consumers:
                for producer in producers:
                    if consumer != producer:  # No self-loops
                        self.dag[consumer].add(producer)
    
    def infer_phase_dependencies(self) -> None:
        """Infer dependencies based on phase ordering."""
        steps_by_phase: Dict[str, List[str]] = defaultdict(list)
        
        # Group steps by phase
        for step in self.steps:
            phase = step.get('universal_phase')
            step_id = step.get('step_id')
            if phase:
                steps_by_phase[phase].append(step_id)
        
        # For each phase, steps in later phases depend on completion of earlier phases
        for i, phase in enumerate(self.phase_order):
            if phase not in steps_by_phase:
                continue
            
            # Get all steps from previous phases
            previous_phase_steps = []
            for prev_phase in self.phase_order[:i]:
                previous_phase_steps.extend(steps_by_phase.get(prev_phase, []))
            
            # If a step has no explicit dependencies, it depends on last step of previous phase
            if previous_phase_steps:
                last_prev_step = previous_phase_steps[-1]
                
                for step_id in steps_by_phase[phase]:
                    if not self.dag.get(step_id):
                        # Only add phase dependency if no explicit deps
                        self.dag[step_id].add(last_prev_step)
    
    def infer_operation_dependencies(self) -> None:
        """Infer dependencies based on operation kind sequencing."""
        steps_by_operation: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Group steps by operation kind
        for step in self.steps:
            op_kind = step.get('operation_kind')
            if op_kind:
                steps_by_operation[op_kind].append(step)
        
        # Apply operation sequencing rules
        for op_kind, prerequisites in self.operation_sequencing.items():
            if op_kind not in steps_by_operation:
                continue
            
            for step in steps_by_operation[op_kind]:
                step_id = step.get('step_id')
                
                # Find steps with prerequisite operations in same phase
                step_phase = step.get('universal_phase')
                
                for prereq_op in prerequisites:
                    if prereq_op not in steps_by_operation:
                        continue
                    
                    for prereq_step in steps_by_operation[prereq_op]:
                        prereq_phase = prereq_step.get('universal_phase')
                        
                        # Only add dependency if in same phase or earlier
                        if self._phase_order(prereq_phase) <= self._phase_order(step_phase):
                            self.dag[step_id].add(prereq_step.get('step_id'))
    
    def _phase_order(self, phase: str) -> int:
        """Get numeric order of phase."""
        try:
            return self.phase_order.index(phase)
        except ValueError:
            return 999  # Unknown phases go last
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the DAG using DFS."""
        visited = {step_id: 0 for step_id in self.dag}
        cycles = []
        stack = []
        
        def dfs(node: str) -> bool:
            if visited[node] == 1:  # In current path
                # Found cycle
                cycle_start = stack.index(node)
                cycles.append(stack[cycle_start:] + [node])
                return True
            
            if visited[node] == 2:  # Already processed
                return False
            
            visited[node] = 1
            stack.append(node)
            
            for dep in self.dag.get(node, set()):
                if dep in self.dag:
                    dfs(dep)
            
            stack.pop()
            visited[node] = 2
            return False
        
        for node in self.dag:
            if visited[node] == 0:
                dfs(node)
        
        return cycles
    
    def compute_execution_waves(self) -> List[List[str]]:
        """Compute topological ordering as execution waves using Kahn's algorithm."""
        in_degree = {node: 0 for node in self.dag}
        
        # Compute in-degrees
        for node, deps in self.dag.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[node] += 1
        
        # Build reverse graph
        self.reverse_dag = {node: set() for node in self.dag}
        for node, deps in self.dag.items():
            for dep in deps:
                if dep in self.reverse_dag:
                    self.reverse_dag[dep].add(node)
        
        # Kahn's algorithm with wave tracking
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        waves = []
        
        while queue:
            wave = []
            wave_size = len(queue)
            
            for _ in range(wave_size):
                node = queue.popleft()
                wave.append(node)
                
                # Reduce in-degree of dependents
                for dependent in self.reverse_dag[node]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
            
            waves.append(wave)
        
        self.waves = waves
        return waves
    
    def compute_critical_path(self) -> Tuple[List[str], float]:
        """Compute critical path (longest path through DAG)."""
        # Assign default duration to each step (1 unit)
        durations = {step['step_id']: 1.0 for step in self.steps}
        
        # Distance from start (longest path to each node)
        distances = {node: 0.0 for node in self.dag}
        predecessors = {node: None for node in self.dag}
        
        # Process nodes in topological order (by waves)
        for wave in self.waves:
            for node in wave:
                for dep in self.dag[node]:
                    new_dist = distances[dep] + durations[dep]
                    if new_dist > distances[node]:
                        distances[node] = new_dist
                        predecessors[node] = dep
        
        # Find end node (max distance)
        end_node = max(distances.items(), key=lambda x: x[1])[0]
        total_duration = distances[end_node]
        
        # Reconstruct path
        path = []
        current = end_node
        while current is not None:
            path.append(current)
            current = predecessors[current]
        
        path.reverse()
        return path, total_duration
    
    def generate_dag_json(self) -> Dict[str, Any]:
        """Generate DAG as JSON structure."""
        cycles = self.detect_cycles()
        
        if cycles:
            print(f"WARNING: {len(cycles)} cycles detected in DAG")
        
        waves = self.compute_execution_waves()
        critical_path, critical_duration = self.compute_critical_path()
        
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source_schema': str(self.schema_path),
                'total_steps': len(self.steps),
                'total_waves': len(waves),
                'has_cycles': len(cycles) > 0,
                'critical_path_duration': critical_duration
            },
            'nodes': [
                {
                    'step_id': step['step_id'],
                    'name': step['name'],
                    'phase': step.get('universal_phase'),
                    'operation_kind': step.get('operation_kind'),
                    'dependencies': list(self.dag.get(step['step_id'], set()))
                }
                for step in self.steps
            ],
            'edges': [
                {'from': dep, 'to': step_id}
                for step_id, deps in self.dag.items()
                for dep in deps
            ],
            'waves': [
                {
                    'wave_number': i,
                    'steps': wave,
                    'parallelism': len(wave)
                }
                for i, wave in enumerate(waves)
            ],
            'critical_path': critical_path,
            'cycles': cycles if cycles else []
        }
    
    def generate_graphviz(self) -> str:
        """Generate Graphviz DOT format for visualization."""
        dot = ["digraph ProcessSteps {"]
        dot.append("  rankdir=LR;")
        dot.append("  node [shape=box];")
        
        # Define nodes with colors by phase
        phase_colors = {
            '1_BOOTSTRAP': '#e1f5fe',
            '2_DISCOVERY': '#f3e5f5',
            '3_DESIGN': '#fff9c4',
            '4_APPROVAL': '#ffccbc',
            '5_REGISTRATION': '#c8e6c9',
            '6_EXECUTION': '#b3e5fc',
            '7_CONSOLIDATION': '#f8bbd0',
            '8_MAINTENANCE': '#dcedc8',
            '9_SYNC_AND_FINALIZE': '#d1c4e9'
        }
        
        for step in self.steps:
            step_id = step['step_id']
            name = step['name'][:30] + '...' if len(step['name']) > 30 else step['name']
            phase = step.get('universal_phase', '')
            color = phase_colors.get(phase, '#ffffff')
            
            dot.append(f'  "{step_id}" [label="{step_id}\\n{name}", fillcolor="{color}", style=filled];')
        
        # Define edges
        for step_id, deps in self.dag.items():
            for dep in deps:
                dot.append(f'  "{dep}" -> "{step_id}";')
        
        dot.append("}")
        return "\n".join(dot)
    
    def generate(self, filter_phase: Optional[str] = None) -> Dict[str, Any]:
        """Generate complete DAG analysis."""
        print("Generating DAG from process steps...")
        
        self.load_schema()
        
        # Filter by phase if specified
        if filter_phase:
            self.steps = [s for s in self.steps if s.get('universal_phase') == filter_phase]
            print(f"Filtered to {len(self.steps)} steps in phase {filter_phase}")
        
        print("Extracting explicit dependencies...")
        self.extract_explicit_dependencies()
        
        print("Analyzing artifact-based dependencies...")
        self.analyze_artifact_dependencies()
        
        print("Inferring phase-based dependencies...")
        self.infer_phase_dependencies()
        
        print("Inferring operation-based dependencies...")
        self.infer_operation_dependencies()
        
        print("Computing execution waves...")
        dag_json = self.generate_dag_json()
        
        print(f"\n{'='*60}")
        print("DAG Generation Complete")
        print(f"{'='*60}")
        print(f"Total steps: {dag_json['metadata']['total_steps']}")
        print(f"Total edges: {len(dag_json['edges'])}")
        print(f"Execution waves: {dag_json['metadata']['total_waves']}")
        print(f"Critical path duration: {dag_json['metadata']['critical_path_duration']:.1f} units")
        
        if dag_json['metadata']['has_cycles']:
            print(f"⚠️  WARNING: {len(dag_json['cycles'])} cycles detected!")
        else:
            print("✓ No cycles detected (valid DAG)")
        
        return dag_json


def main():
    schema_path = None
    output_format = 'dag'
    filter_phase = None
    
    for arg in sys.argv[1:]:
        if arg.startswith('--output='):
            output_format = arg.split('=')[1]
        elif arg.startswith('--phase='):
            filter_phase = arg.split('=')[1]
        elif not arg.startswith('--'):
            schema_path = Path(arg)
    
    if schema_path is None:
        schema_path = Path(__file__).parent.parent / 'schemas' / 'unified' / 'PFA_E2E_WITH_FILES.yaml'
    
    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        sys.exit(1)
    
    generator = DAGGenerator(schema_path)
    dag_data = generator.generate(filter_phase=filter_phase)
    
    # Output
    workspace = Path(__file__).parent.parent / 'workspace'
    workspace.mkdir(exist_ok=True)
    
    if output_format == 'waves':
        # Output just the execution waves
        output_file = workspace / 'execution_waves.json'
        waves_data = {'waves': dag_data['waves'], 'metadata': dag_data['metadata']}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(waves_data, f, indent=2)
        print(f"\nWaves written to: {output_file}")
    
    elif output_format == 'graphviz':
        # Output Graphviz DOT format
        output_file = workspace / 'process_dag.dot'
        dot_content = generator.generate_graphviz()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dot_content)
        print(f"\nGraphviz DOT written to: {output_file}")
        print("Render with: dot -Tpng process_dag.dot -o process_dag.png")
    
    else:  # dag (default)
        # Output full DAG JSON
        output_file = workspace / 'process_dag.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dag_data, f, indent=2)
        print(f"\nDAG JSON written to: {output_file}")
        
        # Also output YAML for easier reading
        output_file_yaml = workspace / 'process_dag.yaml'
        with open(output_file_yaml, 'w', encoding='utf-8') as f:
            yaml.dump(dag_data, f, default_flow_style=False, sort_keys=False)
        print(f"DAG YAML written to: {output_file_yaml}")


if __name__ == '__main__':
    main()

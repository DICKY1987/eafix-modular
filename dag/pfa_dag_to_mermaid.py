#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-DAG-TO-MERMAID-946
"""
PFA DAG to Mermaid - Convert Process DAG to Mermaid Diagram

Converts generated process DAG to Mermaid flowchart format for
easy visualization in markdown files, GitHub, and documentation.

Usage:
    python pfa_dag_to_mermaid.py [dag_file] [--by-phase] [--by-wave] [--critical-path]
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-DAG-TO-MERMAID-946

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Set


class MermaidGenerator:
    """Generate Mermaid diagrams from process DAG."""
    
    def __init__(self, dag_data: Dict[str, Any]):
        self.dag_data = dag_data
        self.nodes = {n['step_id']: n for n in dag_data['nodes']}
        self.edges = dag_data['edges']
        self.waves = dag_data.get('waves', [])
        self.critical_path = set(dag_data.get('critical_path', []))
        
        # Phase colors for Mermaid
        self.phase_colors = {
            '1_BOOTSTRAP': 'lightblue',
            '2_DISCOVERY': 'lightpink',
            '3_DESIGN': 'lightyellow',
            '4_APPROVAL': 'lightcoral',
            '5_REGISTRATION': 'lightgreen',
            '6_EXECUTION': 'lightcyan',
            '7_CONSOLIDATION': 'plum',
            '8_MAINTENANCE': 'lightgray',
            '9_SYNC_AND_FINALIZE': 'lavender'
        }
    
    def _sanitize_id(self, step_id: str) -> str:
        """Sanitize step ID for Mermaid."""
        return step_id.replace('-', '_').replace('.', '_')
    
    def _sanitize_label(self, text: str, max_len: int = 30) -> str:
        """Sanitize text for Mermaid label."""
        if len(text) > max_len:
            text = text[:max_len] + '...'
        return text.replace('"', "'").replace('\n', ' ')
    
    def generate_full_dag(self) -> str:
        """Generate full DAG as Mermaid flowchart."""
        lines = ['```mermaid', 'flowchart LR']
        
        # Define nodes
        for step_id, node in self.nodes.items():
            safe_id = self._sanitize_id(step_id)
            label = self._sanitize_label(node['name'])
            
            # Highlight critical path
            if step_id in self.critical_path:
                lines.append(f'    {safe_id}["{step_id}<br/>{label}"]:::criticalPath')
            else:
                lines.append(f'    {safe_id}["{step_id}<br/>{label}"]')
        
        # Define edges
        for edge in self.edges:
            from_id = self._sanitize_id(edge['from'])
            to_id = self._sanitize_id(edge['to'])
            lines.append(f'    {from_id} --> {to_id}')
        
        # Style critical path
        lines.append('    classDef criticalPath fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px')
        
        lines.append('```')
        return '\n'.join(lines)
    
    def generate_by_phase(self) -> str:
        """Generate DAG grouped by phase."""
        lines = ['```mermaid', 'flowchart TB']
        
        # Group nodes by phase
        phases: Dict[str, List[str]] = {}
        for step_id, node in self.nodes.items():
            phase = node.get('phase', 'UNKNOWN')
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(step_id)
        
        # Generate subgraphs for each phase
        for phase in sorted(phases.keys()):
            lines.append(f'    subgraph {phase}')
            
            for step_id in phases[phase]:
                node = self.nodes[step_id]
                safe_id = self._sanitize_id(step_id)
                label = self._sanitize_label(node['name'], max_len=25)
                
                if step_id in self.critical_path:
                    lines.append(f'        {safe_id}["{label}"]:::criticalPath')
                else:
                    lines.append(f'        {safe_id}["{label}"]')
            
            lines.append('    end')
        
        # Add edges
        for edge in self.edges:
            from_id = self._sanitize_id(edge['from'])
            to_id = self._sanitize_id(edge['to'])
            lines.append(f'    {from_id} --> {to_id}')
        
        # Styling
        lines.append('    classDef criticalPath fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px')
        
        lines.append('```')
        return '\n'.join(lines)
    
    def generate_by_wave(self) -> str:
        """Generate DAG showing execution waves."""
        lines = ['```mermaid', 'flowchart LR']
        
        # Generate columns for each wave
        for wave_data in self.waves:
            wave_num = wave_data['wave_number']
            steps = wave_data['steps']
            
            lines.append(f'    subgraph Wave_{wave_num}["Wave {wave_num} ({len(steps)} parallel)"]')
            
            for step_id in steps:
                if step_id in self.nodes:
                    node = self.nodes[step_id]
                    safe_id = self._sanitize_id(step_id)
                    label = self._sanitize_label(node['name'], max_len=20)
                    
                    if step_id in self.critical_path:
                        lines.append(f'        {safe_id}["{label}"]:::criticalPath')
                    else:
                        lines.append(f'        {safe_id}["{label}"]')
            
            lines.append('    end')
        
        # Add edges between waves
        for edge in self.edges:
            from_id = self._sanitize_id(edge['from'])
            to_id = self._sanitize_id(edge['to'])
            lines.append(f'    {from_id} -.-> {to_id}')
        
        # Styling
        lines.append('    classDef criticalPath fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px')
        
        lines.append('```')
        return '\n'.join(lines)
    
    def generate_critical_path_only(self) -> str:
        """Generate diagram showing only critical path."""
        lines = ['```mermaid', 'flowchart LR']
        
        # Show only critical path nodes
        critical_nodes = [step_id for step_id in self.critical_path if step_id in self.nodes]
        
        for step_id in critical_nodes:
            node = self.nodes[step_id]
            safe_id = self._sanitize_id(step_id)
            label = self._sanitize_label(node['name'])
            phase = node.get('phase', 'UNKNOWN')
            
            lines.append(f'    {safe_id}["{step_id}<br/>{label}<br/>[{phase}]"]:::criticalPath')
        
        # Add edges only between critical path nodes
        for i in range(len(critical_nodes) - 1):
            from_id = self._sanitize_id(critical_nodes[i])
            to_id = self._sanitize_id(critical_nodes[i + 1])
            lines.append(f'    {from_id} ==> {to_id}')
        
        # Styling
        lines.append('    classDef criticalPath fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px')
        
        lines.append('```')
        return '\n'.join(lines)
    
    def generate_summary(self) -> str:
        """Generate markdown summary with metrics."""
        meta = self.dag_data['metadata']
        
        md = f"""# Process DAG Summary

**Generated**: {meta['generated_at']}  
**Source**: {meta['source_schema']}

## Metrics

- **Total Steps**: {meta['total_steps']}
- **Total Dependencies**: {len(self.edges)}
- **Execution Waves**: {meta['total_waves']}
- **Critical Path Duration**: {meta['critical_path_duration']:.1f} units
- **Maximum Parallelism**: {max((w['parallelism'] for w in self.waves), default=0)}

## Wave Distribution

| Wave | Steps | Parallelism |
|------|-------|-------------|
"""
        
        for wave in self.waves:
            md += f"| {wave['wave_number']} | {len(wave['steps'])} | {wave['parallelism']} |\n"
        
        md += "\n## Critical Path\n\n"
        for i, step_id in enumerate(self.critical_path, 1):
            if step_id in self.nodes:
                node = self.nodes[step_id]
                md += f"{i}. **{step_id}**: {node['name']} `[{node.get('phase')}]`\n"
        
        return md


def main():
    dag_file = None
    mode = 'full'
    
    for arg in sys.argv[1:]:
        if arg == '--by-phase':
            mode = 'by-phase'
        elif arg == '--by-wave':
            mode = 'by-wave'
        elif arg == '--critical-path':
            mode = 'critical-path'
        elif not arg.startswith('--'):
            dag_file = Path(arg)
    
    if dag_file is None:
        dag_file = Path(__file__).parent.parent / 'workspace' / 'process_dag.json'
    
    if not dag_file.exists():
        print(f"ERROR: DAG file not found: {dag_file}")
        print("Generate it first with: python pfa_generate_dag.py")
        sys.exit(1)
    
    # Load DAG
    with open(dag_file, 'r', encoding='utf-8') as f:
        dag_data = json.load(f)
    
    generator = MermaidGenerator(dag_data)
    
    # Generate appropriate diagram
    workspace = Path(__file__).parent.parent / 'workspace'
    
    if mode == 'by-phase':
        output_file = workspace / 'process_dag_by_phase.md'
        content = "# Process DAG - Grouped by Phase\n\n"
        content += generator.generate_summary() + "\n\n"
        content += "## DAG Visualization\n\n"
        content += generator.generate_by_phase()
    
    elif mode == 'by-wave':
        output_file = workspace / 'process_dag_by_wave.md'
        content = "# Process DAG - Execution Waves\n\n"
        content += generator.generate_summary() + "\n\n"
        content += "## Wave-Based Execution Plan\n\n"
        content += generator.generate_by_wave()
    
    elif mode == 'critical-path':
        output_file = workspace / 'process_dag_critical_path.md'
        content = "# Process DAG - Critical Path\n\n"
        content += generator.generate_summary() + "\n\n"
        content += "## Critical Path (Longest Execution Path)\n\n"
        content += generator.generate_critical_path_only()
    
    else:  # full
        output_file = workspace / 'process_dag_full.md'
        content = "# Process DAG - Full Visualization\n\n"
        content += generator.generate_summary() + "\n\n"
        content += "## Complete DAG\n\n"
        content += generator.generate_full_dag()
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Mermaid diagram written to: {output_file}")
    print(f"\nPreview in:")
    print(f"  - GitHub (renders Mermaid automatically)")
    print(f"  - VS Code (with Markdown Preview Mermaid extension)")
    print(f"  - https://mermaid.live (paste diagram code)")


if __name__ == '__main__':
    main()

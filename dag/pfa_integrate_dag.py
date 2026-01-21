#!/usr/bin/env python3
# DOC_LINK: DOC-SCRIPT-TOOLS-PFA-INTEGRATE-DAG-951
"""
PFA Integrate DAG - Wire DAG Generation into Pipeline

Integrates automated DAG generation into the process step pipeline:
1. Watches for schema changes
2. Automatically regenerates DAG when steps change
3. Updates schema with dependency information
4. Validates DAG structure
5. Triggers downstream updates

Usage:
    python pfa_integrate_dag.py [--watch] [--once] [--update-schema]
"""
DOC_ID: DOC-SCRIPT-TOOLS-PFA-INTEGRATE-DAG-951

import sys
import DOC-ERROR-UTILS-TIME-145__time
import yaml
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import hashlib
import subprocess


class DAGIntegrator:
    """Integrate DAG generation into process pipeline."""
    
    def __init__(self, update_schema: bool = False):
        self.update_schema = update_schema
        self.process_lib = Path(__file__).parent.parent
        self.schemas_dir = self.process_lib / 'schemas'
        self.workspace = self.process_lib / 'workspace'
        self.tools_dir = self.process_lib / 'tools'
        
        # Track hashes
        self.file_hashes: Dict[str, str] = {}
    
    def compute_hash(self, filepath: Path) -> str:
        """Compute SHA256 hash of file."""
        if not filepath.exists():
            return ""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def detect_schema_changes(self) -> bool:
        """Detect if unified schema has changed."""
        schema_file = self.schemas_dir / 'unified' / 'PFA_E2E_WITH_FILES.yaml'
        
        if not schema_file.exists():
            return False
        
        current_hash = self.compute_hash(schema_file)
        previous_hash = self.file_hashes.get(str(schema_file), "")
        
        if current_hash != previous_hash:
            self.file_hashes[str(schema_file)] = current_hash
            return True
        
        return False
    
    def generate_dag(self) -> bool:
        """Generate DAG from current schema."""
        print(f"\n{'='*60}")
        print("Generating Process DAG")
        print(f"{'='*60}")
        
        try:
            dag_generator = self.tools_dir / 'pfa_generate_dag.py'
            
            result = subprocess.run(
                [sys.executable, str(dag_generator), '--output=dag'],
                capture_output=True,
                text=True,
                cwd=str(self.process_lib)
            )
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"✗ Error generating DAG: {result.stderr}")
                return False
        
        except Exception as e:
            print(f"✗ Error generating DAG: {e}")
            return False
    
    def generate_visualizations(self) -> bool:
        """Generate Mermaid visualizations."""
        print(f"\n{'='*60}")
        print("Generating DAG Visualizations")
        print(f"{'='*60}")
        
        try:
            mermaid_generator = self.tools_dir / 'pfa_dag_to_mermaid.py'
            
            modes = ['--by-phase', '--by-wave', '--critical-path']
            
            for mode in modes:
                result = subprocess.run(
                    [sys.executable, str(mermaid_generator), mode],
                    capture_output=True,
                    text=True,
                    cwd=str(self.process_lib)
                )
                
                if result.returncode == 0:
                    print(f"✓ Generated {mode.replace('--', '')}")
                else:
                    print(f"✗ Error generating {mode}: {result.stderr}")
            
            return True
        
        except Exception as e:
            print(f"✗ Error generating visualizations: {e}")
            return False
    
    def update_schema_with_dag(self) -> bool:
        """Update schema with DAG dependency information."""
        if not self.update_schema:
            return True
        
        print(f"\n{'='*60}")
        print("Updating Schema with DAG Dependencies")
        print(f"{'='*60}")
        
        try:
            # Load DAG
            dag_file = self.workspace / 'process_dag.json'
            if not dag_file.exists():
                print("⚠ DAG file not found, skipping schema update")
                return False
            
            with open(dag_file, 'r', encoding='utf-8') as f:
                dag_data = json.load(f)
            
            # Load schema
            schema_file = self.schemas_dir / 'unified' / 'PFA_E2E_WITH_FILES.yaml'
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)
            
            # Update steps with dependency info
            dag_nodes = {n['step_id']: n for n in dag_data['nodes']}
            
            updates_made = 0
            for step in schema.get('steps', []):
                step_id = step.get('step_id')
                
                if step_id in dag_nodes:
                    dag_node = dag_nodes[step_id]
                    
                    # Add computed dependencies (don't override explicit ones)
                    if not step.get('depends_on') and dag_node['dependencies']:
                        step['computed_dependencies'] = dag_node['dependencies']
                        updates_made += 1
            
            # Add DAG metadata
            if 'meta' not in schema:
                schema['meta'] = {}
            
            schema['meta']['dag_metadata'] = {
                'last_generated': datetime.now().isoformat(),
                'total_dependencies': len(dag_data['edges']),
                'execution_waves': dag_data['metadata']['total_waves'],
                'critical_path_duration': dag_data['metadata']['critical_path_duration'],
                'has_cycles': dag_data['metadata']['has_cycles']
            }
            
            # Write updated schema
            backup_file = self.workspace / f"schema_backup_{int(time.time())}.yaml"
            with open(backup_file, 'w', encoding='utf-8') as f:
                yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            print(f"Backup created: {backup_file}")
            
            with open(schema_file, 'w', encoding='utf-8') as f:
                yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            print(f"✓ Updated schema with {updates_made} computed dependencies")
            print(f"✓ Added DAG metadata to schema")
            
            return True
        
        except Exception as e:
            print(f"✗ Error updating schema: {e}")
            return False
    
    def validate_dag(self) -> bool:
        """Validate DAG structure."""
        print(f"\n{'='*60}")
        print("Validating DAG Structure")
        print(f"{'='*60}")
        
        try:
            dag_file = self.workspace / 'process_dag.json'
            
            if not dag_file.exists():
                print("⚠ DAG file not found")
                return False
            
            with open(dag_file, 'r', encoding='utf-8') as f:
                dag_data = json.load(f)
            
            meta = dag_data['metadata']
            
            # Check for cycles
            if meta['has_cycles']:
                print(f"✗ DAG has cycles: {len(dag_data.get('cycles', []))} detected")
                return False
            
            print(f"✓ No cycles detected (valid DAG)")
            print(f"✓ {meta['total_steps']} steps")
            print(f"✓ {len(dag_data['edges'])} dependencies")
            print(f"✓ {meta['total_waves']} execution waves")
            
            return True
        
        except Exception as e:
            print(f"✗ Error validating DAG: {e}")
            return False
    
    def run_once(self) -> bool:
        """Run DAG generation pipeline once."""
        print(f"\n{'='*70}")
        print(f"DAG Integration Pipeline - {datetime.now().isoformat()}")
        print(f"{'='*70}")
        
        success = True
        
        # 1. Generate DAG
        if not self.generate_dag():
            success = False
        
        # 2. Validate DAG
        if not self.validate_dag():
            success = False
        
        # 3. Generate visualizations
        if not self.generate_visualizations():
            success = False
        
        # 4. Update schema (if enabled)
        if self.update_schema:
            if not self.update_schema_with_dag():
                success = False
        
        print(f"\n{'='*60}")
        if success:
            print("✓ DAG Integration Complete")
        else:
            print("⚠ DAG Integration completed with warnings")
        print(f"{'='*60}")
        
        return success
    
    def watch(self, interval: int = 30) -> None:
        """Watch for schema changes and regenerate DAG."""
        print(f"Starting DAG integration watcher (checking every {interval}s)")
        print("Press Ctrl+C to stop")
        
        # Initialize hashes
        self.detect_schema_changes()
        
        try:
            while True:
                if self.detect_schema_changes():
                    print(f"\n[{datetime.now().isoformat()}] Schema change detected")
                    self.run_once()
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\nWatcher stopped")


def main():
    watch_mode = False
    once_mode = False
    update_schema = False
    interval = 30
    
    for arg in sys.argv[1:]:
        if arg == '--watch':
            watch_mode = True
        elif arg == '--once':
            once_mode = True
        elif arg == '--update-schema':
            update_schema = True
        elif arg.startswith('--interval='):
            interval = int(arg.split('=')[1])
    
    integrator = DAGIntegrator(update_schema=update_schema)
    
    if watch_mode:
        integrator.watch(interval=interval)
    else:
        integrator.run_once()


if __name__ == '__main__':
    main()

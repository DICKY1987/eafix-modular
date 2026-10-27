#!/usr/bin/env python3
"""
PyTest Verification Plugin (MOD-005)
Runs Python tests as part of verification checkpoint.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

class PyTestPlugin:
    """Plugin for running pytest verification checks."""
    
    def __init__(self):
        self.name = "pytest"
        self.description = "Run Python tests with pytest"
        self.version = "1.0.0"
        
    def discover(self) -> Dict[str, Any]:
        """Discover if pytest is available and find test files."""
        
        # Check if pytest is installed
        try:
            result = subprocess.run(['pytest', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            pytest_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest_available = False
        
        # Find test files
        test_files = []
        current_dir = Path.cwd()
        
        # Common test file patterns
        test_patterns = ['test_*.py', '*_test.py', 'tests/*.py', 'test/**/*.py']
        
        for pattern in test_patterns:
            test_files.extend(current_dir.glob(pattern))
        
        return {
            'plugin_name': self.name,
            'available': pytest_available,
            'test_files_found': len(test_files),
            'test_files': [str(f) for f in test_files[:10]],  # Limit to first 10
            'prerequisites': ['pytest'],
            'supported_checkpoints': ['pre_commit', 'pre_merge', 'post_implementation']
        }
    
    def run(self, checkpoint_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run pytest verification."""
        
        config = config or {}
        test_path = config.get('test_path', '.')
        coverage = config.get('coverage', True)
        verbose = config.get('verbose', True)
        timeout = config.get('timeout', 300)  # 5 minutes default
        
        # Build pytest command
        cmd = ['pytest']
        
        if coverage:
            cmd.extend(['--cov=.', '--cov-report=term-missing'])
        
        if verbose:
            cmd.append('-v')
        
        # Add test path
        cmd.append(test_path)
        
        # Additional arguments from config
        extra_args = config.get('extra_args', [])
        if extra_args:
            cmd.extend(extra_args)
        
        start_time = subprocess.run(['date', '+%s'], capture_output=True, text=True)
        start_timestamp = start_time.stdout.strip() if start_time.returncode == 0 else "unknown"
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=Path.cwd()
            )
            
            # Parse pytest output for test results
            stdout_lines = result.stdout.split('\n')
            
            # Extract test summary (look for lines like "=== X passed, Y failed in Zs ===")
            test_summary = ""
            for line in reversed(stdout_lines):
                if "passed" in line and ("failed" in line or "error" in line or "skipped" in line):
                    test_summary = line.strip()
                    break
                elif line.strip().endswith("passed"):
                    test_summary = line.strip()
                    break
            
            # Determine status
            if result.returncode == 0:
                status = "PASS"
                message = "All tests passed successfully"
            else:
                status = "FAIL"
                if "FAILED" in result.stdout:
                    failed_count = result.stdout.count("FAILED")
                    message = f"Tests failed ({failed_count} failures detected)"
                else:
                    message = "Test execution failed"
            
            return {
                'plugin_name': self.name,
                'checkpoint_id': checkpoint_id,
                'status': status,
                'message': message,
                'summary': test_summary,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd),
                'timestamp': start_timestamp,
                'artifacts': {
                    'coverage_report': 'coverage data available' if coverage else 'coverage not requested'
                }
            }
            
        except subprocess.TimeoutExpired:
            return {
                'plugin_name': self.name,
                'checkpoint_id': checkpoint_id,
                'status': 'TIMEOUT',
                'message': f'Tests timed out after {timeout} seconds',
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Process killed due to timeout ({timeout}s)',
                'command': ' '.join(cmd),
                'timestamp': start_timestamp
            }
            
        except Exception as e:
            return {
                'plugin_name': self.name,
                'checkpoint_id': checkpoint_id,
                'status': 'ERROR',
                'message': f'Plugin execution error: {str(e)}',
                'exit_code': -2,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(cmd),
                'timestamp': start_timestamp
            }
    
    def report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable report from results."""
        
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌', 
            'TIMEOUT': '⏰',
            'ERROR': '⚠️'
        }
        
        emoji = status_emoji.get(results['status'], '❓')
        
        report = f"{emoji} PyTest Verification ({results['checkpoint_id']})\n"
        report += f"Status: {results['status']}\n"
        report += f"Message: {results['message']}\n"
        
        if results.get('summary'):
            report += f"Summary: {results['summary']}\n"
        
        if results['status'] == 'FAIL' and results.get('stderr'):
            report += f"\nErrors:\n{results['stderr'][:500]}...\n"
        
        return report

def main():
    """CLI interface for the pytest plugin."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PyTest verification plugin")
    parser.add_argument("action", choices=["discover", "run", "report"], help="Action to perform")
    parser.add_argument("--checkpoint", default="manual", help="Checkpoint ID")
    parser.add_argument("--config", help="Configuration JSON string")
    
    args = parser.parse_args()
    
    plugin = PyTestPlugin()
    
    if args.action == "discover":
        result = plugin.discover()
        print(json.dumps(result, indent=2))
        
    elif args.action == "run":
        config = {}
        if args.config:
            try:
                config = json.loads(args.config)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON config: {e}", file=sys.stderr)
                sys.exit(1)
        
        result = plugin.run(args.checkpoint, config)
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        if result['status'] == 'PASS':
            sys.exit(0)
        else:
            sys.exit(1)
            
    elif args.action == "report":
        # Read results from stdin
        try:
            results = json.load(sys.stdin)
            report = plugin.report(results)
            print(report)
        except json.JSONDecodeError:
            print("Error: Expected JSON input for report generation", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
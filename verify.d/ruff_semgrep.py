#!/usr/bin/env python3
"""
Ruff + Semgrep Security/Quality Plugin (MOD-005)
Combines linting with security scanning.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

class RuffSemgrepPlugin:
    """Plugin for code quality and security scanning."""
    
    def __init__(self):
        self.name = "ruff_semgrep"
        self.description = "Code quality (ruff) and security scanning (semgrep)"
        self.version = "1.0.0"
        
    def discover(self) -> Dict[str, Any]:
        """Discover available tools and Python files."""
        
        # Check tool availability
        ruff_available = self._check_tool_availability('ruff', ['--version'])
        semgrep_available = self._check_tool_availability('semgrep', ['--version'])
        
        # Find Python files
        python_files = list(Path.cwd().glob('**/*.py'))
        
        return {
            'plugin_name': self.name,
            'available': ruff_available or semgrep_available,
            'tools': {
                'ruff': {
                    'available': ruff_available,
                    'purpose': 'linting and formatting'
                },
                'semgrep': {
                    'available': semgrep_available,
                    'purpose': 'security scanning'
                }
            },
            'python_files_found': len(python_files),
            'prerequisites': ['ruff', 'semgrep'],
            'supported_checkpoints': ['pre_commit', 'pre_merge', 'security_scan']
        }
    
    def _check_tool_availability(self, tool: str, args: List[str]) -> bool:
        """Check if a tool is available."""
        try:
            result = subprocess.run([tool] + args, 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def run(self, checkpoint_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run ruff and semgrep verification."""
        
        config = config or {}
        target_path = config.get('target_path', '.')
        
        results = {
            'plugin_name': self.name,
            'checkpoint_id': checkpoint_id,
            'status': 'PASS',
            'message': 'All checks passed',
            'results': {}
        }
        
        # Run Ruff (linting)
        if config.get('run_ruff', True):
            ruff_result = self._run_ruff(target_path, config.get('ruff_config', {}))
            results['results']['ruff'] = ruff_result
            
            if ruff_result['status'] != 'PASS':
                results['status'] = 'FAIL'
                results['message'] = 'Code quality issues detected'
        
        # Run Semgrep (security)
        if config.get('run_semgrep', True):
            semgrep_result = self._run_semgrep(target_path, config.get('semgrep_config', {}))
            results['results']['semgrep'] = semgrep_result
            
            if semgrep_result['status'] in ['FAIL', 'WARNING']:
                if results['status'] == 'PASS':
                    results['status'] = semgrep_result['status']
                    results['message'] = 'Security issues detected'
                elif results['status'] == 'FAIL' and semgrep_result['status'] == 'FAIL':
                    results['message'] = 'Code quality and security issues detected'
        
        return results
    
    def _run_ruff(self, target_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run ruff linting."""
        
        # Build ruff command
        cmd = ['ruff', 'check']
        
        if config.get('fix', False):
            cmd.append('--fix')
        
        if config.get('format', 'text') == 'json':
            cmd.append('--format=json')
        
        cmd.append(target_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            issues_count = 0
            issues = []
            
            if result.stdout:
                if '--format=json' in cmd:
                    try:
                        issues_data = json.loads(result.stdout)
                        issues = issues_data if isinstance(issues_data, list) else []
                        issues_count = len(issues)
                    except json.JSONDecodeError:
                        issues_count = result.stdout.count('\n')
                else:
                    issues_count = len([line for line in result.stdout.split('\n') if line.strip()])
            
            status = 'PASS' if result.returncode == 0 else 'FAIL'
            message = f"Ruff found {issues_count} issues" if issues_count > 0 else "No linting issues found"
            
            return {
                'tool': 'ruff',
                'status': status,
                'message': message,
                'issues_count': issues_count,
                'exit_code': result.returncode,
                'stdout': result.stdout[:1000],  # Limit output
                'stderr': result.stderr[:1000],
                'command': ' '.join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'tool': 'ruff',
                'status': 'TIMEOUT',
                'message': 'Ruff execution timed out',
                'issues_count': 0,
                'exit_code': -1,
                'stderr': 'Process timed out after 60 seconds'
            }
        except Exception as e:
            return {
                'tool': 'ruff',
                'status': 'ERROR',
                'message': f'Ruff execution error: {str(e)}',
                'issues_count': 0,
                'exit_code': -2,
                'stderr': str(e)
            }
    
    def _run_semgrep(self, target_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run semgrep security scanning."""
        
        # Build semgrep command
        cmd = ['semgrep', '--config=auto', '--json']
        
        # Add severity filter if specified
        severity = config.get('severity', 'INFO')
        cmd.extend(['--severity', severity])
        
        cmd.append(target_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            findings = []
            high_severity_count = 0
            
            if result.stdout:
                try:
                    output_data = json.loads(result.stdout)
                    findings = output_data.get('results', [])
                    
                    # Count high-severity findings
                    high_severity_count = len([f for f in findings 
                                             if f.get('extra', {}).get('severity') in ['ERROR', 'WARNING']])
                    
                except json.JSONDecodeError:
                    pass
            
            # Determine status based on findings
            if high_severity_count > 0:
                status = 'FAIL'
                message = f"Semgrep found {high_severity_count} high-severity security issues"
            elif len(findings) > 0:
                status = 'WARNING'  
                message = f"Semgrep found {len(findings)} low-severity issues"
            else:
                status = 'PASS'
                message = "No security issues detected"
            
            return {
                'tool': 'semgrep',
                'status': status,
                'message': message,
                'findings_count': len(findings),
                'high_severity_count': high_severity_count,
                'exit_code': result.returncode,
                'stdout': result.stdout[:2000],  # Limit output
                'stderr': result.stderr[:1000],
                'command': ' '.join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'tool': 'semgrep',
                'status': 'TIMEOUT',
                'message': 'Semgrep execution timed out',
                'findings_count': 0,
                'exit_code': -1,
                'stderr': 'Process timed out after 120 seconds'
            }
        except Exception as e:
            return {
                'tool': 'semgrep',
                'status': 'ERROR',
                'message': f'Semgrep execution error: {str(e)}',
                'findings_count': 0,
                'exit_code': -2,
                'stderr': str(e)
            }
    
    def report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable report."""
        
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌',
            'WARNING': '⚠️', 
            'TIMEOUT': '⏰',
            'ERROR': '⚠️'
        }
        
        emoji = status_emoji.get(results['status'], '❓')
        
        report = f"{emoji} Code Quality & Security Scan ({results['checkpoint_id']})\n"
        report += f"Overall Status: {results['status']}\n"
        report += f"Message: {results['message']}\n\n"
        
        # Ruff results
        if 'ruff' in results['results']:
            ruff = results['results']['ruff']
            ruff_emoji = status_emoji.get(ruff['status'], '❓')
            report += f"{ruff_emoji} Ruff (Linting): {ruff['message']}\n"
        
        # Semgrep results
        if 'semgrep' in results['results']:
            semgrep = results['results']['semgrep']
            semgrep_emoji = status_emoji.get(semgrep['status'], '❓')
            report += f"{semgrep_emoji} Semgrep (Security): {semgrep['message']}\n"
        
        return report

def main():
    """CLI interface for the ruff+semgrep plugin."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ruff+Semgrep verification plugin")
    parser.add_argument("action", choices=["discover", "run", "report"], help="Action to perform")
    parser.add_argument("--checkpoint", default="manual", help="Checkpoint ID")
    parser.add_argument("--config", help="Configuration JSON string")
    
    args = parser.parse_args()
    
    plugin = RuffSemgrepPlugin()
    
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
        elif result['status'] == 'WARNING':
            sys.exit(2)  # Warning exit code
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
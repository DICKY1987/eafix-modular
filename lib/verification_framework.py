"""
Verification Checkpoints Plugin Framework (MOD-005)
Standardizes gates (lint, tests, schema validators, security scans) as plugins invoked at checkpoints.
"""

import json
import subprocess
import sys
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class VerificationFramework:
    """Manages verification plugins and checkpoint execution."""
    
    def __init__(self, plugins_dir: str = "verify.d"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins = {}
        self.plugin_configs = {}
        
        # Load plugins
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all plugins from the plugins directory."""
        
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {self.plugins_dir}")
            return
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith('__'):
                continue  # Skip __init__.py, etc.
            
            try:
                plugin_name = plugin_file.stem
                
                # Load plugin module dynamically
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for plugin class (convention: CapitalizedName + Plugin)
                    class_name = ''.join(word.capitalize() for word in plugin_name.split('_')) + 'Plugin'
                    
                    if hasattr(module, class_name):
                        plugin_class = getattr(module, class_name)
                        self.plugins[plugin_name] = plugin_class()
                        logger.info(f"Loaded plugin: {plugin_name}")
                    else:
                        logger.warning(f"Plugin class {class_name} not found in {plugin_file}")
                
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file}: {e}")
    
    def discover_plugins(self) -> Dict[str, Any]:
        """Discover all available plugins and their capabilities."""
        
        plugin_info = {}
        
        for plugin_name, plugin in self.plugins.items():
            try:
                if hasattr(plugin, 'discover'):
                    info = plugin.discover()
                    plugin_info[plugin_name] = info
                else:
                    # Basic info for plugins without discover method
                    plugin_info[plugin_name] = {
                        'plugin_name': plugin_name,
                        'available': True,
                        'description': getattr(plugin, 'description', 'No description'),
                        'version': getattr(plugin, 'version', 'unknown')
                    }
            except Exception as e:
                logger.error(f"Failed to discover plugin {plugin_name}: {e}")
                plugin_info[plugin_name] = {
                    'plugin_name': plugin_name,
                    'available': False,
                    'error': str(e)
                }
        
        return {
            'framework_version': '1.0.0',
            'plugins_directory': str(self.plugins_dir),
            'total_plugins': len(plugin_info),
            'available_plugins': len([p for p in plugin_info.values() if p.get('available', False)]),
            'plugins': plugin_info
        }
    
    def run_checkpoint(self, checkpoint_id: str, plugins: Optional[List[str]] = None, 
                      config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run verification checkpoint with specified plugins."""
        
        config = config or {}
        
        # Determine which plugins to run
        if plugins is None:
            # Run all available plugins
            plugins_to_run = list(self.plugins.keys())
        else:
            # Run only specified plugins
            plugins_to_run = [p for p in plugins if p in self.plugins]
        
        logger.info(f"Running checkpoint '{checkpoint_id}' with {len(plugins_to_run)} plugins")
        
        start_time = time.time()
        checkpoint_result = {
            'checkpoint_id': checkpoint_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'PASS',
            'message': 'All verifications passed',
            'total_plugins': len(plugins_to_run),
            'passed_plugins': 0,
            'failed_plugins': 0,
            'plugin_results': {},
            'execution_time_seconds': 0
        }
        
        # Run each plugin
        for plugin_name in plugins_to_run:
            plugin = self.plugins[plugin_name]
            plugin_config = config.get(plugin_name, {})
            
            logger.info(f"Running plugin: {plugin_name}")
            
            try:
                if hasattr(plugin, 'run'):
                    result = plugin.run(checkpoint_id, plugin_config)
                    checkpoint_result['plugin_results'][plugin_name] = result
                    
                    # Update overall status
                    if result.get('status') in ['PASS', 'SKIP']:
                        checkpoint_result['passed_plugins'] += 1
                    else:
                        checkpoint_result['failed_plugins'] += 1
                        checkpoint_result['status'] = 'FAIL'
                        checkpoint_result['message'] = 'One or more verifications failed'
                else:
                    # Plugin doesn't have run method
                    checkpoint_result['plugin_results'][plugin_name] = {
                        'plugin_name': plugin_name,
                        'status': 'ERROR',
                        'message': 'Plugin does not implement run method'
                    }
                    checkpoint_result['failed_plugins'] += 1
                    checkpoint_result['status'] = 'FAIL'
                    
            except Exception as e:
                logger.error(f"Plugin {plugin_name} execution failed: {e}")
                checkpoint_result['plugin_results'][plugin_name] = {
                    'plugin_name': plugin_name,
                    'status': 'ERROR',
                    'message': f'Plugin execution error: {str(e)}',
                    'error': str(e)
                }
                checkpoint_result['failed_plugins'] += 1
                checkpoint_result['status'] = 'FAIL'
        
        checkpoint_result['execution_time_seconds'] = round(time.time() - start_time, 2)
        
        # Log summary
        if checkpoint_result['status'] == 'PASS':
            logger.info(f"✅ Checkpoint '{checkpoint_id}' PASSED ({checkpoint_result['passed_plugins']}/{checkpoint_result['total_plugins']} plugins)")
        else:
            logger.error(f"❌ Checkpoint '{checkpoint_id}' FAILED ({checkpoint_result['failed_plugins']}/{checkpoint_result['total_plugins']} plugins failed)")
        
        return checkpoint_result
    
    def generate_report(self, checkpoint_result: Dict[str, Any], format: str = 'text') -> str:
        """Generate human-readable report from checkpoint results."""
        
        if format == 'json':
            return json.dumps(checkpoint_result, indent=2)
        
        # Text format report
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌',
            'SKIP': '⏭️',
            'WARNING': '⚠️',
            'ERROR': '⚠️',
            'TIMEOUT': '⏰'
        }
        
        overall_emoji = status_emoji.get(checkpoint_result['status'], '❓')
        
        report = f"\n{overall_emoji} Verification Checkpoint: {checkpoint_result['checkpoint_id']}\n"
        report += f"Status: {checkpoint_result['status']}\n"
        report += f"Message: {checkpoint_result['message']}\n"
        report += f"Execution Time: {checkpoint_result['execution_time_seconds']}s\n"
        report += f"Results: {checkpoint_result['passed_plugins']}/{checkpoint_result['total_plugins']} plugins passed\n"
        report += f"Timestamp: {checkpoint_result['timestamp']}\n\n"
        
        # Individual plugin results
        report += "Plugin Results:\n"
        report += "-" * 50 + "\n"
        
        for plugin_name, plugin_result in checkpoint_result['plugin_results'].items():
            plugin_emoji = status_emoji.get(plugin_result.get('status'), '❓')
            report += f"{plugin_emoji} {plugin_name}: {plugin_result.get('message', 'No message')}\n"
            
            # Add additional details for failed plugins
            if plugin_result.get('status') in ['FAIL', 'ERROR'] and plugin_result.get('stderr'):
                stderr = plugin_result['stderr'][:200]  # Limit error output
                report += f"    Error: {stderr}{'...' if len(plugin_result.get('stderr', '')) > 200 else ''}\n"
        
        report += "-" * 50 + "\n"
        
        return report
    
    def get_available_checkpoints(self) -> List[str]:
        """Get list of supported checkpoint types from all plugins."""
        
        checkpoints = set()
        
        for plugin in self.plugins.values():
            try:
                if hasattr(plugin, 'discover'):
                    info = plugin.discover()
                    supported = info.get('supported_checkpoints', [])
                    checkpoints.update(supported)
            except Exception as e:
                logger.warning(f"Could not get checkpoints from plugin: {e}")
        
        return sorted(list(checkpoints))

def main():
    """CLI interface for the verification framework."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verification Checkpoints Framework")
    parser.add_argument("command", 
                       choices=["discover", "run", "list-checkpoints", "list-plugins"],
                       help="Command to execute")
    parser.add_argument("--checkpoint", help="Checkpoint ID to run")
    parser.add_argument("--plugins", nargs="*", help="Specific plugins to run")
    parser.add_argument("--config", help="Configuration JSON string")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--plugins-dir", default="verify.d", help="Plugins directory")
    
    args = parser.parse_args()
    
    framework = VerificationFramework(args.plugins_dir)
    
    if args.command == "discover":
        result = framework.discover_plugins()
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"Verification Framework Discovery:")
            print(f"Plugins Directory: {result['plugins_directory']}")
            print(f"Total Plugins: {result['total_plugins']}")
            print(f"Available Plugins: {result['available_plugins']}")
            print("\\nPlugins:")
            for name, info in result['plugins'].items():
                status = "✅" if info.get('available') else "❌"
                print(f"  {status} {name}: {info.get('description', 'No description')}")
    
    elif args.command == "list-checkpoints":
        checkpoints = framework.get_available_checkpoints()
        if args.format == "json":
            print(json.dumps({"checkpoints": checkpoints}, indent=2))
        else:
            print("Available Checkpoints:")
            for checkpoint in checkpoints:
                print(f"  • {checkpoint}")
    
    elif args.command == "list-plugins":
        plugins = list(framework.plugins.keys())
        if args.format == "json":
            print(json.dumps({"plugins": plugins}, indent=2))
        else:
            print("Loaded Plugins:")
            for plugin in plugins:
                print(f"  • {plugin}")
    
    elif args.command == "run":
        if not args.checkpoint:
            print("Error: --checkpoint is required for run command", file=sys.stderr)
            sys.exit(1)
        
        config = {}
        if args.config:
            try:
                config = json.loads(args.config)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON config: {e}", file=sys.stderr)
                sys.exit(1)
        
        result = framework.run_checkpoint(args.checkpoint, args.plugins, config)
        
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            report = framework.generate_report(result)
            print(report)
        
        # Exit with appropriate code
        if result['status'] == 'PASS':
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
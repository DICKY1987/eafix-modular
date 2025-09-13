#!/usr/bin/env python3
"""
Schema Validation Plugin (MOD-005)
Validates JSON/YAML files against schemas.
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema
from jsonschema import validate, ValidationError

class SchemaValidationPlugin:
    """Plugin for validating files against schemas."""
    
    def __init__(self):
        self.name = "schema_validate"
        self.description = "Validate JSON/YAML files against schemas"
        self.version = "1.0.0"
        
    def discover(self) -> Dict[str, Any]:
        """Discover schema files and validation targets."""
        
        current_dir = Path.cwd()
        
        # Find schema files
        schema_files = []
        schema_patterns = ['**/*.schema.json', '**/schemas/*.json', 'specs/schemas/*.json']
        for pattern in schema_patterns:
            schema_files.extend(current_dir.glob(pattern))
        
        # Find potential validation targets
        json_files = list(current_dir.glob('**/*.json'))
        yaml_files = []
        yaml_patterns = ['**/*.yaml', '**/*.yml']
        for pattern in yaml_patterns:
            yaml_files.extend(current_dir.glob(pattern))
        
        # Check jsonschema availability
        jsonschema_available = True
        try:
            import jsonschema
        except ImportError:
            jsonschema_available = False
        
        return {
            'plugin_name': self.name,
            'available': jsonschema_available,
            'schema_files_found': len(schema_files),
            'json_files_found': len(json_files),
            'yaml_files_found': len(yaml_files),
            'schema_files': [str(f) for f in schema_files],
            'prerequisites': ['jsonschema', 'pyyaml'],
            'supported_checkpoints': ['pre_commit', 'pre_merge', 'schema_validation']
        }
    
    def run(self, checkpoint_id: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run schema validation."""
        
        config = config or {}
        
        results = {
            'plugin_name': self.name,
            'checkpoint_id': checkpoint_id,
            'status': 'PASS',
            'message': 'All schema validations passed',
            'validations': []
        }
        
        # Get validation rules from config
        validation_rules = config.get('validation_rules', self._get_default_validation_rules())
        
        total_validations = 0
        failed_validations = 0
        
        for rule in validation_rules:
            try:
                rule_result = self._validate_rule(rule)
                results['validations'].append(rule_result)
                
                total_validations += 1
                if rule_result['status'] != 'PASS':
                    failed_validations += 1
                    
            except Exception as e:
                error_result = {
                    'rule_name': rule.get('name', 'unknown'),
                    'status': 'ERROR',
                    'message': f'Validation rule error: {str(e)}',
                    'error': str(e)
                }
                results['validations'].append(error_result)
                total_validations += 1
                failed_validations += 1
        
        # Update overall status
        if failed_validations > 0:
            results['status'] = 'FAIL'
            results['message'] = f'{failed_validations}/{total_validations} validations failed'
        else:
            results['message'] = f'All {total_validations} validations passed'
        
        return results
    
    def _get_default_validation_rules(self) -> List[Dict[str, Any]]:
        """Get default validation rules for common files."""
        
        rules = []
        
        # Check for workflow template schema
        template_schema = Path('specs/schemas/workflow_template.json')
        if template_schema.exists():
            # Find template files to validate
            template_files = list(Path.cwd().glob('**/*template*.json'))
            for template_file in template_files:
                rules.append({
                    'name': f'validate_{template_file.name}',
                    'schema_file': str(template_schema),
                    'target_file': str(template_file),
                    'description': f'Validate {template_file.name} against workflow template schema'
                })
        
        # Check for OpenAPI specs
        openapi_files = list(Path.cwd().glob('specs/openapi/*.yml')) + list(Path.cwd().glob('specs/openapi/*.yaml'))
        for openapi_file in openapi_files:
            rules.append({
                'name': f'validate_{openapi_file.name}',
                'schema_type': 'openapi',
                'target_file': str(openapi_file),
                'description': f'Validate {openapi_file.name} as OpenAPI specification'
            })
        
        # Check for configuration files
        config_files = ['config/tools.yaml', 'config/integrations.json']
        for config_file in config_files:
            if Path(config_file).exists():
                rules.append({
                    'name': f'validate_{Path(config_file).name}',
                    'schema_type': 'basic_json_yaml',
                    'target_file': config_file,
                    'description': f'Basic validation for {config_file}'
                })
        
        return rules
    
    def _validate_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single rule."""
        
        rule_name = rule.get('name', 'unnamed_rule')
        target_file = Path(rule.get('target_file', ''))
        
        if not target_file.exists():
            return {
                'rule_name': rule_name,
                'status': 'SKIP',
                'message': f'Target file does not exist: {target_file}',
                'target_file': str(target_file)
            }
        
        try:
            # Load target file
            target_data = self._load_file(target_file)
            
            # Determine validation method
            schema_file = rule.get('schema_file')
            schema_type = rule.get('schema_type', 'json_schema')
            
            if schema_file:
                # Validate against specific schema file
                return self._validate_against_schema_file(rule_name, target_data, schema_file, str(target_file))
            elif schema_type == 'openapi':
                # Validate as OpenAPI spec
                return self._validate_openapi(rule_name, target_data, str(target_file))
            elif schema_type == 'basic_json_yaml':
                # Basic JSON/YAML syntax validation
                return self._validate_basic_syntax(rule_name, target_data, str(target_file))
            else:
                return {
                    'rule_name': rule_name,
                    'status': 'ERROR',
                    'message': 'Unknown schema type or missing schema file',
                    'target_file': str(target_file)
                }
                
        except Exception as e:
            return {
                'rule_name': rule_name,
                'status': 'FAIL',
                'message': f'Validation failed: {str(e)}',
                'target_file': str(target_file),
                'error': str(e)
            }
    
    def _load_file(self, file_path: Path) -> Any:
        """Load JSON or YAML file."""
        
        content = file_path.read_text(encoding='utf-8')
        
        if file_path.suffix.lower() in ['.yml', '.yaml']:
            return yaml.safe_load(content)
        else:
            return json.loads(content)
    
    def _validate_against_schema_file(self, rule_name: str, target_data: Any, 
                                    schema_file: str, target_file: str) -> Dict[str, Any]:
        """Validate target data against a schema file."""
        
        schema_path = Path(schema_file)
        if not schema_path.exists():
            return {
                'rule_name': rule_name,
                'status': 'ERROR',
                'message': f'Schema file does not exist: {schema_file}',
                'target_file': target_file
            }
        
        # Load schema
        schema_data = self._load_file(schema_path)
        
        # Validate
        try:
            validate(instance=target_data, schema=schema_data)
            return {
                'rule_name': rule_name,
                'status': 'PASS',
                'message': 'Schema validation passed',
                'target_file': target_file,
                'schema_file': schema_file
            }
        except ValidationError as e:
            return {
                'rule_name': rule_name,
                'status': 'FAIL',
                'message': f'Schema validation failed: {e.message}',
                'target_file': target_file,
                'schema_file': schema_file,
                'validation_error': e.message,
                'error_path': list(e.path) if e.path else []
            }
    
    def _validate_openapi(self, rule_name: str, target_data: Any, target_file: str) -> Dict[str, Any]:
        """Validate OpenAPI specification."""
        
        # Basic OpenAPI structure validation
        required_fields = ['openapi', 'info', 'paths']
        missing_fields = [field for field in required_fields if field not in target_data]
        
        if missing_fields:
            return {
                'rule_name': rule_name,
                'status': 'FAIL',
                'message': f'Missing required OpenAPI fields: {", ".join(missing_fields)}',
                'target_file': target_file,
                'missing_fields': missing_fields
            }
        
        # Check OpenAPI version
        openapi_version = target_data.get('openapi', '')
        if not openapi_version.startswith('3.'):
            return {
                'rule_name': rule_name,
                'status': 'FAIL',
                'message': f'Unsupported OpenAPI version: {openapi_version} (expected 3.x)',
                'target_file': target_file
            }
        
        return {
            'rule_name': rule_name,
            'status': 'PASS',
            'message': 'OpenAPI specification structure is valid',
            'target_file': target_file,
            'openapi_version': openapi_version
        }
    
    def _validate_basic_syntax(self, rule_name: str, target_data: Any, target_file: str) -> Dict[str, Any]:
        """Basic syntax validation for JSON/YAML."""
        
        # If we got here, the file was successfully parsed
        return {
            'rule_name': rule_name,
            'status': 'PASS',
            'message': 'File syntax is valid',
            'target_file': target_file,
            'data_type': type(target_data).__name__
        }
    
    def report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable report."""
        
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌',
            'SKIP': '⏭️',
            'ERROR': '⚠️'
        }
        
        emoji = status_emoji.get(results['status'], '❓')
        
        report = f"{emoji} Schema Validation ({results['checkpoint_id']})\n"
        report += f"Overall Status: {results['status']}\n"
        report += f"Message: {results['message']}\n\n"
        
        if results.get('validations'):
            report += "Individual Validations:\n"
            for validation in results['validations']:
                val_emoji = status_emoji.get(validation['status'], '❓')
                report += f"  {val_emoji} {validation['rule_name']}: {validation['message']}\n"
        
        return report

def main():
    """CLI interface for the schema validation plugin."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Schema validation plugin")
    parser.add_argument("action", choices=["discover", "run", "report"], help="Action to perform")
    parser.add_argument("--checkpoint", default="manual", help="Checkpoint ID")
    parser.add_argument("--config", help="Configuration JSON string")
    
    args = parser.parse_args()
    
    plugin = SchemaValidationPlugin()
    
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
#!/usr/bin/env python3
"""
JSON Schema Validator

Validates JSON data against schema files and Pydantic models.
Used in CI/CD pipeline and for runtime validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import jsonschema
from jsonschema import Draft202012Validator

from .models import (
    IndicatorRecord, OrderIn, OrderOut, HybridId,
    ActiveCalendarSignal, ReentryDecision, TradeResult, HealthMetric
)

logger = logging.getLogger(__name__)


class JSONSchemaValidator:
    """Validates JSON data against schemas and Pydantic models."""
    
    def __init__(self, schema_dir: Optional[Path] = None):
        """Initialize validator with schema directory."""
        if schema_dir is None:
            schema_dir = Path(__file__).parent / "schemas" / "json"
        
        self.schema_dir = Path(schema_dir)
        self.schemas: Dict[str, dict] = {}
        self.load_schemas()
    
    def load_schemas(self) -> None:
        """Load all JSON schema files."""
        if not self.schema_dir.exists():
            logger.warning(f"Schema directory not found: {self.schema_dir}")
            return
        
        for schema_file in self.schema_dir.glob("*.json"):
            try:
                with open(schema_file, 'r') as f:
                    schema = json.load(f)
                    self.schemas[schema_file.stem] = schema
                    logger.debug(f"Loaded schema: {schema_file.stem}")
            except Exception as e:
                logger.error(f"Failed to load schema {schema_file}: {e}")
    
    def validate_json_against_schema(self, data: dict, schema_name: str) -> tuple[bool, List[str]]:
        """Validate JSON data against a schema file."""
        if schema_name not in self.schemas:
            return False, [f"Schema not found: {schema_name}"]
        
        schema = self.schemas[schema_name]
        validator = Draft202012Validator(schema)
        
        errors = []
        try:
            # Validate against JSON schema
            for error in validator.iter_errors(data):
                errors.append(f"Path {'.'.join(str(p) for p in error.absolute_path)}: {error.message}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return len(errors) == 0, errors
    
    def validate_pydantic_model(self, data: dict, model_class) -> tuple[bool, List[str]]:
        """Validate data against Pydantic model."""
        try:
            model_class(**data)
            return True, []
        except Exception as e:
            return False, [str(e)]
    
    def validate_indicator_record(self, data: dict) -> tuple[bool, List[str]]:
        """Validate indicator record against both schema and model."""
        # Validate against JSON schema
        schema_valid, schema_errors = self.validate_json_against_schema(data, "indicator_record.schema")
        
        # Validate against Pydantic model
        model_valid, model_errors = self.validate_pydantic_model(data, IndicatorRecord)
        
        # Combine results
        all_valid = schema_valid and model_valid
        all_errors = schema_errors + model_errors
        
        return all_valid, all_errors
    
    def validate_order_in(self, data: dict) -> tuple[bool, List[str]]:
        """Validate order in against both schema and model."""
        schema_valid, schema_errors = self.validate_json_against_schema(data, "orders_in.schema")
        model_valid, model_errors = self.validate_pydantic_model(data, OrderIn)
        
        return schema_valid and model_valid, schema_errors + model_errors
    
    def validate_order_out(self, data: dict) -> tuple[bool, List[str]]:
        """Validate order out against both schema and model."""
        schema_valid, schema_errors = self.validate_json_against_schema(data, "orders_out.schema")
        model_valid, model_errors = self.validate_pydantic_model(data, OrderOut)
        
        return schema_valid and model_valid, schema_errors + model_errors
    
    def validate_hybrid_id(self, data: dict) -> tuple[bool, List[str]]:
        """Validate hybrid ID against both schema and model."""
        schema_valid, schema_errors = self.validate_json_against_schema(data, "hybrid_id.schema") 
        model_valid, model_errors = self.validate_pydantic_model(data, HybridId)
        
        return schema_valid and model_valid, schema_errors + model_errors
    
    def validate_all_fixtures(self) -> Dict[str, Dict[str, Any]]:
        """Validate all fixture files in tests/contracts/fixtures/."""
        results = {}
        
        fixtures_dir = Path(__file__).parent.parent / "tests" / "contracts" / "fixtures"
        if not fixtures_dir.exists():
            logger.warning(f"Fixtures directory not found: {fixtures_dir}")
            return results
        
        # Validate JSON fixtures
        json_fixtures = {
            "indicator_record_valid.json": self.validate_indicator_record,
            "orders_in_valid.json": self.validate_order_in,
            "orders_out_valid.json": self.validate_order_out,
            "hybrid_id_valid.json": self.validate_hybrid_id,
        }
        
        for fixture_file, validator_func in json_fixtures.items():
            fixture_path = fixtures_dir / fixture_file
            if fixture_path.exists():
                try:
                    with open(fixture_path, 'r') as f:
                        data = json.load(f)
                    
                    valid, errors = validator_func(data)
                    results[fixture_file] = {
                        "valid": valid,
                        "errors": errors,
                        "path": str(fixture_path)
                    }
                except Exception as e:
                    results[fixture_file] = {
                        "valid": False,
                        "errors": [f"Failed to load fixture: {e}"],
                        "path": str(fixture_path)
                    }
            else:
                results[fixture_file] = {
                    "valid": False,
                    "errors": [f"Fixture file not found: {fixture_path}"],
                    "path": str(fixture_path)
                }
        
        return results
    
    def generate_validation_report(self) -> str:
        """Generate a comprehensive validation report."""
        report_lines = []
        report_lines.append("# Contract Validation Report")
        report_lines.append(f"Generated at: {json.dumps(str(__import__('datetime').datetime.utcnow()))}")
        report_lines.append("")
        
        # Schema loading status
        report_lines.append("## Schema Loading Status")
        report_lines.append(f"Loaded schemas: {len(self.schemas)}")
        for schema_name in sorted(self.schemas.keys()):
            report_lines.append(f"- LOADED: {schema_name}")
        report_lines.append("")
        
        # Fixture validation results
        report_lines.append("## Fixture Validation Results") 
        fixture_results = self.validate_all_fixtures()
        
        total_fixtures = len(fixture_results)
        valid_fixtures = sum(1 for r in fixture_results.values() if r["valid"])
        
        report_lines.append(f"Total fixtures: {total_fixtures}")
        report_lines.append(f"Valid fixtures: {valid_fixtures}")
        report_lines.append(f"Invalid fixtures: {total_fixtures - valid_fixtures}")
        report_lines.append("")
        
        for fixture_name, result in sorted(fixture_results.items()):
            status = "PASS" if result["valid"] else "FAIL"
            report_lines.append(f"### {status}: {fixture_name}")
            if not result["valid"]:
                for error in result["errors"]:
                    report_lines.append(f"  - {error}")
            report_lines.append("")
        
        return "\n".join(report_lines)


def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate JSON contracts")
    parser.add_argument("--schema-dir", type=Path, help="Schema directory path")
    parser.add_argument("--report", action="store_true", help="Generate validation report")
    parser.add_argument("--file", type=Path, help="Validate specific JSON file")
    parser.add_argument("--schema", type=str, help="Schema name for file validation")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create validator
    validator = JSONSchemaValidator(args.schema_dir)
    
    if args.report:
        # Generate full validation report
        report = validator.generate_validation_report()
        print(report)
        
        # Write to file
        report_path = Path("contract_validation_report.md")
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\nReport written to: {report_path}")
    
    elif args.file and args.schema:
        # Validate specific file
        try:
            with open(args.file, 'r') as f:
                data = json.load(f)
            
            valid, errors = validator.validate_json_against_schema(data, args.schema)
            
            if valid:
                print(f"✓ {args.file} is valid against {args.schema}")
            else:
                print(f"✗ {args.file} is invalid against {args.schema}")
                for error in errors:
                    print(f"  - {error}")
                exit(1)
                
        except Exception as e:
            print(f"✗ Failed to validate {args.file}: {e}")
            exit(1)
    
    else:
        # Default: validate all fixtures
        results = validator.validate_all_fixtures()
        
        total = len(results)
        valid = sum(1 for r in results.values() if r["valid"])
        
        print(f"Validated {total} fixtures: {valid} valid, {total - valid} invalid")
        
        if total - valid > 0:
            print("\nInvalid fixtures:")
            for name, result in results.items():
                if not result["valid"]:
                    print(f"  ✗ {name}")
                    for error in result["errors"][:3]:  # Show first 3 errors
                        print(f"    - {error}")
            exit(1)
        else:
            print("All fixtures valid!")


if __name__ == "__main__":
    main()
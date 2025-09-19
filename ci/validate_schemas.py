#!/usr/bin/env python3
"""
Schema Validation for CI Pipeline

Validates all JSON schemas in the contracts registry.
Supports both old (contracts/events) and new (contracts/schemas/json) locations.
"""
import json
import pathlib
import sys
from jsonschema import Draft202012Validator

def validate_schemas_in_directory(schema_dir: pathlib.Path, description: str):
    """Validate all schemas in a directory."""
    schemas = list(schema_dir.glob("*.json"))
    
    if not schemas:
        print(f"No schemas found in {schema_dir}")
        return 0
    
    print(f"\n=== Validating {description} ===")
    valid_count = 0
    
    for p in schemas:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(data)
            print(f"+ Schema OK: {p.name}")
            valid_count += 1
        except Exception as e:
            print(f"- Schema INVALID: {p.name} - {e}", file=sys.stderr)
    
    print(f"Validated {valid_count}/{len(schemas)} schemas in {description}")
    return valid_count, len(schemas)

def main():
    """Main validation function."""
    total_valid = 0
    total_schemas = 0
    
    # Check new contract structure
    new_schema_dir = pathlib.Path("contracts/schemas/json")
    if new_schema_dir.exists():
        valid, total = validate_schemas_in_directory(new_schema_dir, "JSON Contract Schemas")
        total_valid += valid
        total_schemas += total
    
    # Check legacy event schemas for backward compatibility
    legacy_schema_dir = pathlib.Path("contracts/events")
    if legacy_schema_dir.exists():
        valid, total = validate_schemas_in_directory(legacy_schema_dir, "Legacy Event Schemas")
        total_valid += valid
        total_schemas += total
    
    # Check if we found any schemas at all
    if total_schemas == 0:
        print("No schemas found in contracts/schemas/json or contracts/events", file=sys.stderr)
        sys.exit(1)
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"Total schemas validated: {total_valid}/{total_schemas}")
    
    if total_valid == total_schemas:
        print("+ All schemas are valid!")
        sys.exit(0)
    else:
        print(f"- {total_schemas - total_valid} schema(s) failed validation")
        sys.exit(1)

if __name__ == "__main__":
    main()

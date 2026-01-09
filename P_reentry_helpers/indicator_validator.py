# DOC_ID: DOC-LEGACY-0012
"""
indicator_validator.py — Validate indicator records against JSON Schema.

Prefers `jsonschema` if available; otherwise falls back to a lightweight validator
(types, required, enum, pattern, min/max).

Usage:
    from reentry_helpers.indicator_validator import validate_file

    valids, invalids = validate_file("indicator_records.json", "indicator_record.schema.json")
    for bad in invalids:
        print(bad["errors"])
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json, re, os

def _simple_validate_record(inst: Any, schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    def type_check(val, typ: str) -> bool:
        if typ == "object": return isinstance(val, dict)
        if typ == "array": return isinstance(val, list)
        if typ == "string": return isinstance(val, str)
        if typ == "number": return isinstance(val, (int,float)) and not isinstance(val, bool)
        if typ == "integer": return isinstance(val, int) and not isinstance(val, bool)
        if typ == "boolean": return isinstance(val, bool)
        return True

    def _v(inst, sch, path=""):
        # type
        if "type" in sch and not type_check(inst, sch["type"]):
            errors.append(f"{path}: expected type {sch['type']} but got {type(inst).__name__}")
            return

        # required & properties
        if sch.get("type") == "object":
            req = sch.get("required", [])
            for r in req:
                if not isinstance(inst, dict) or r not in inst:
                    errors.append(f"{path}: missing required '{r}'")
            props = sch.get("properties", {})
            if isinstance(inst, dict):
                for k, v in inst.items():
                    if k in props:
                        _v(v, props[k], f"{path}.{k}" if path else k)
                    else:
                        if not sch.get("additionalProperties", True):
                            errors.append(f"{path}: additional property '{k}' not allowed")

        # array items
        if sch.get("type") == "array":
            item_schema = sch.get("items", {})
            if isinstance(inst, list):
                for i, el in enumerate(inst):
                    _v(el, item_schema, f"{path}[{i}]")

        # enum
        if "enum" in sch and inst not in sch["enum"]:
            errors.append(f"{path}: value '{inst}' not in enum {sch['enum']}")

        # pattern
        if "pattern" in sch and isinstance(inst, str):
            if re.match(sch["pattern"], inst) is None:
                errors.append(f"{path}: value '{inst}' does not match pattern {sch['pattern']}")

        # numeric bounds
        if "minimum" in sch and isinstance(inst, (int,float)) and inst < sch["minimum"]:
            errors.append(f"{path}: value {inst} < minimum {sch['minimum']}")
        if "maximum" in sch and isinstance(inst, (int,float)) and inst > sch["maximum"]:
            errors.append(f"{path}: value {inst} > maximum {sch['maximum']}")

    _v(inst, schema, "")
    return errors

def _validate_with_jsonschema(record: Any, schema: Dict[str, Any]) -> List[str]:
    try:
        import jsonschema # type: ignore
    except Exception:
        return _simple_validate_record(record, schema)
    try:
        jsonschema.validate(instance=record, schema=schema) # type: ignore
        return []
    except Exception as e:
        # Attempt to extract all errors with Draft7Validator if available
        try:
            from jsonschema import Draft7Validator # type: ignore
            v = Draft7Validator(schema)
            errs = [f"{e.path}: {e.message}" for e in v.iter_errors(record)]
            return errs or [str(e)]
        except Exception:
            return [str(e)]

def validate_records(records: List[Dict[str, Any]], schema: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    valids, invalids = [], []
    for rec in records:
        errs = _validate_with_jsonschema(rec, schema)
        if errs:
            invalids.append({"record": rec, "errors": errs})
        else:
            valids.append(rec)
    return valids, invalids

def validate_file(records_path: str, schema_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    with open(records_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Records file must contain a JSON list")
    return validate_records(data, schema)

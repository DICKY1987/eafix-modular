#!/usr/bin/env python3
"""Schema loading and extraction helpers for manifest generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_schema(schema_path: Path) -> dict[str, Any]:
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _resolve_ref(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    if "$ref" not in node:
        return node
    ref = node["$ref"]
    if not ref.startswith("#/$defs/"):
        return node
    return schema["$defs"][ref.split("/")[-1]]


def _field_descriptor(schema: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    resolved = _resolve_ref(schema, node)
    out: dict[str, Any] = {
        "type": resolved.get("type"),
        "nullable": isinstance(resolved.get("type"), list) and "null" in resolved["type"],
    }
    if "enum" in resolved:
        out["enum"] = resolved["enum"]
    if "const" in resolved:
        out["const"] = resolved["const"]
    if resolved.get("type") == "object":
        out["required"] = resolved.get("required", [])
        out["properties"] = {
            key: _field_descriptor(schema, value)
            for key, value in resolved.get("properties", {}).items()
        }
        out["additional_properties"] = resolved.get("additionalProperties", True)
    if resolved.get("type") == "array":
        items = resolved.get("items", {})
        out["items"] = _field_descriptor(schema, items if isinstance(items, dict) else {})
        out["minItems"] = resolved.get("minItems")
    return out


def build_schema_field_map(schema: dict[str, Any]) -> dict[str, Any]:
    top = {
        key: _field_descriptor(schema, value)
        for key, value in schema.get("properties", {}).items()
    }
    return {
        "schema_id": schema.get("$id"),
        "schema_version_const": schema.get("properties", {}).get("schema_version", {}).get("const"),
        "required_top_level_fields": schema.get("required", []),
        "top_level_fields": top,
        "definitions": {
            key: _field_descriptor(schema, value)
            for key, value in schema.get("$defs", {}).items()
            if isinstance(value, dict)
        },
    }

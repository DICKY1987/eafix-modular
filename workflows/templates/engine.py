from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, Optional


@dataclass
class RenderResult:
    content: str
    template_name: str


_TEMPLATES: Dict[str, str] = {
    # Phase 0/1 basics
    "taskfile_minimal": """
version: '3'
tasks:
  up:
    cmds:
      - docker compose up -d
    silent: true
""".lstrip(),
    "makefile_minimal": """
.PHONY: test
test:
	pytest -q
""".lstrip(),
    "mit_license": """
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
""".lstrip(),
    "codeowners_min": "* @DICKY1987\n",
    "security_min": """
# Security Policy

Please report suspected vulnerabilities privately per SECURITY.md guidance.
""".lstrip(),
    "issue_bug": """
---
name: Bug report
about: Create a report to help us improve
labels: bug
---
""".lstrip(),
    "issue_feature": """
---
name: Feature request
about: Suggest an idea for this project
labels: enhancement
---
""".lstrip(),
    "docs_readme": "# Documentation\n\nStart here for project docs.\n",
    # Phase 2 schemas (minimal placeholders)
    "schema_price_tick": """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PriceTick",
  "type": "object",
  "properties": {
    "symbol": {"type": "string"},
    "bid": {"type": "number"},
    "ask": {"type": "number"},
    "ts": {"type": "string", "format": "date-time"}
  },
  "required": ["symbol", "bid", "ask", "ts"]
}
""".lstrip(),
    "schema_indicator_vector": """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IndicatorVector",
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "values": {"type": "array", "items": {"type": "number"}}
  },
  "required": ["name", "values"]
}
""".lstrip(),
    "schema_signal": """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Signal",
  "type": "object",
  "properties": {
    "type": {"type": "string"},
    "confidence": {"type": "number"}
  },
  "required": ["type", "confidence"]
}
""".lstrip(),
    "schema_order_intent": """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OrderIntent",
  "type": "object",
  "properties": {
    "symbol": {"type": "string"},
    "side": {"type": "string", "enum": ["buy","sell"]},
    "qty": {"type": "number"}
  },
  "required": ["symbol", "side", "qty"]
}
""".lstrip(),
    "schema_execution_report": """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExecutionReport",
  "type": "object",
  "properties": {
    "order_id": {"type": "string"},
    "status": {"type": "string"}
  },
  "required": ["order_id", "status"]
}
""".lstrip(),
    "schema_calendar_event": """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CalendarEvent",
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "time": {"type": "string", "format": "date-time"}
  },
  "required": ["name", "time"]
}
""".lstrip(),
    "schema_reentry_decision": """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReentryDecision",
  "type": "object",
  "properties": {
    "reason": {"type": "string"},
    "score": {"type": "number"}
  },
  "required": ["reason", "score"]
}
""".lstrip(),
    "mql4_contract_parsers": """
// Placeholder MQL4 parsers for contracts
// Implement actual JSON parsing in MQL4 environment
""".lstrip(),
}


def has_template(name: str) -> bool:
    return name in _TEMPLATES


def render_template(name: str, context: Optional[Dict[str, str]] = None) -> RenderResult:
    if name not in _TEMPLATES:
        raise KeyError(f"Unknown template: {name}")
    raw = _TEMPLATES[name]
    ctx = {"generated": datetime.utcnow().isoformat(), **(context or {})}
    try:
        content = Template(raw).safe_substitute(**ctx)
    except Exception:
        content = raw
    return RenderResult(content=content, template_name=name)


def write_file(path: Path, content: str, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


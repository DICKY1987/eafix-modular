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
    # Phase 5 libs
    "logging_json": """
import json, logging, sys

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "name": record.name,
            "msg": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)

def configure_json_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
""".lstrip(),
    "metrics_prometheus": """
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['route', 'method', 'code'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['route'])

def prometheus_wsgi_app(environ, start_response):
    data = generate_latest()
    start_response('200 OK', [('Content-Type', CONTENT_TYPE_LATEST)])
    return [data]
""".lstrip(),
    "otel_tracing_http": """
# Placeholder for OpenTelemetry HTTP tracing setup
def init_tracing(service_name: str = 'cli-multi-rapid') -> None:
    # Integrate OpenTelemetry SDK here if desired
    return None
""".lstrip(),
    # Phase 7: Kubernetes/Helm
    "helm_chart_yaml": """
apiVersion: v2
name: cli-multi-rapid
description: A Helm chart for deploying cli-multi-rapid services
type: application
version: 0.1.0
appVersion: "0.1.0"
""".lstrip(),
    "helm_values_yaml": """
replicaCount: 1
image:
  repository: ghcr.io/dicky1987/cli-multi-rapid
  tag: latest
  pullPolicy: IfNotPresent
service:
  type: ClusterIP
  port: 8080
resources: {}
nodeSelector: {}
tolerations: []
affinity: {}
""".lstrip(),
    "helm_deployment_yaml": """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "cli-multi-rapid.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ include "cli-multi-rapid.name" . }}
  template:
    metadata:
      labels:
        app: {{ include "cli-multi-rapid.name" . }}
    spec:
      containers:
        - name: app
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 8080
          resources: {{- toYaml .Values.resources | nindent 12 }}
""".lstrip(),
    "helm_service_yaml": """
apiVersion: v1
kind: Service
metadata:
  name: {{ include "cli-multi-rapid.fullname" . }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: 8080
      protocol: TCP
      name: http
  selector:
    app: {{ include "cli-multi-rapid.name" . }}
""".lstrip(),
    "helm_helpers_tpl": """
{{- define "cli-multi-rapid.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "cli-multi-rapid.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
""".lstrip(),
    "k8s_networkpolicy_allowlist_yaml": """
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allowlist-between-services
spec:
  podSelector: {}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector: {}
""".lstrip(),
    "external_secrets_eso_yaml": """
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: sample-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: default
    kind: ClusterSecretStore
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
    - secretKey: DROP_TOKEN
      remoteRef:
        key: /cli-multi-rapid/drop-token
""".lstrip(),
    # Phase 5a compliance
    "compliance_rules_json": """
{
  "rules": [
    {"id": "COV_MIN", "desc": "Coverage must be >=85%", "type": "coverage", "min": 0.85},
    {"id": "NO_SECRETS", "desc": "No secrets committed", "type": "secrets"}
  ]
}
""".lstrip(),
    "runbook_emergency_recovery_md": """
# Emergency Recovery Runbook

1. Identify incident scope and impacted services.
2. Roll back to last known-good release tag.
3. Restore data from backups if corruption detected.
4. Verify service health and notify stakeholders.
""".lstrip(),
    "compliance_service_py": """
from __future__ import annotations

import json
from pathlib import Path


def evaluate_rules(rules_path: str = "policy/compliance_rules.json") -> bool:
    p = Path(rules_path)
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return isinstance(data.get("rules", []), list)
    except Exception:
        return False


if __name__ == "__main__":  # manual check
    ok = evaluate_rules()
    print({"ok": ok})
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
    # Phase 3 CI/CD
    "precommit_full": """
repos:
- repo: https://github.com/psf/black
  rev: 24.4.2
  hooks:
  - id: black
- repo: https://github.com/charliermarsh/ruff-pre-commit
  rev: v0.5.6
  hooks:
  - id: ruff
    args: ["--fix"]
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.10.0
  hooks:
  - id: mypy
    additional_dependencies: ["types-requests"]
""".lstrip(),
    "ci_matrix": """
name: CI
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -U pip
      - run: pip install pre-commit ruff mypy pytest coverage
      - run: pre-commit run -a || true
      - run: pytest -q --cov=src --cov-report=term-missing --cov-fail-under=85
""".lstrip(),
    "build_publish_sbom_cosign": """
name: build-publish
on:
  push:
    tags: [ "v*" ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -U pip build cyclonedx-bom
      - run: python -m build
      - run: cyclonedx-bom -o sbom.json
      - uses: actions/upload-artifact@v4
        with:
          name: artifacts
          path: |
            dist/*
            sbom.json
""".lstrip(),
    "release_notes": """
name: release
on:
  workflow_dispatch:
  push:
    tags: [ "v*" ]
jobs:
  notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create Release Notes
        run: |
          echo "# Release $GITHUB_REF_NAME" > RELEASE_NOTES.md
          echo "\nArtifacts in build-publish workflow artifacts." >> RELEASE_NOTES.md
      - uses: softprops/action-gh-release@v2
        with:
          body_path: RELEASE_NOTES.md
""".lstrip(),
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

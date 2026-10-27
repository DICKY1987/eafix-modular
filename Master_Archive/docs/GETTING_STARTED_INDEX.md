# Getting Started

This repository includes a simple hello-world workflow and orchestration tools to help you validate your setup.

Quick links
- Orchestrator status: `python -m workflows.orchestrator status`
- List streams: `python -m workflows.orchestrator list-streams`
- Run hello world locally: `pwsh -NoProfile -File scripts/run_workflow.ps1`

Cost reporting
- Emit sample token metrics: `pwsh -NoProfile -File scripts/emit_tokens.ps1 -Out artifacts/tokens.json`
- Generate cost report (JSON/CSV): `pwsh -NoProfile -File scripts/report_costs.ps1 -OutDir artifacts/cost`
- CI publishes artifacts automatically; PRs show a cost summary.

Artifacts
- Hello world artifacts are written to `artifacts/hello_world/` when the workflow runs.

Requirements
- Python 3.11+
- PowerShell (Windows PowerShell or pwsh)
- Optional: pre-commit for local linting

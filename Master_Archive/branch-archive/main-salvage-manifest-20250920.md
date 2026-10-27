# Branch Archive: main — Salvage Manifest

**Archive date:** 2025-09-20  
**Archive tag:** `archive/main-superproject-20250920`  
**Archive root:** `branch-archive/main/`

## Purpose

This manifest documents the historical content salvaged from the `main` branch before it was deleted as part of the branch consolidation effort (Phase 7). All salvaged items are preserved here for **historical reference only** and do not supersede active `master` authority files.

## Constraints

- All content in `branch-archive/main/` is **read-only historical reference**.
- No salvaged file should be executed or imported from this location.
- Scripts under `branch-archive/main/.ai/scripts/` reference `origin/main`; those references are intentionally preserved as historical record and must not be used in active automation.
- This manifest must remain at `branch-archive/main-salvage-manifest-20250920.md` (not moved under `branch-archive/main/`).

## Salvaged Files (53 items)

### AI / Automation Scripts

| Archive path | Notes |
|---|---|
| `.ai/scripts/orchestrate.ps1` | Orchestration script; references `origin/main` — historical only |
| `.ai/scripts/run-triage.ps1` | Triage delegation script — historical only |
| `.ai/workflows/agent_jobs.yaml` | Agent job definitions — historical only |

### CODEX Implementation

| Archive path |
|---|
| `CODEX_IMPLEMENTATION/README_CODEX_INSTRUCTIONS.md` |
| `CODEX_IMPLEMENTATION/implementation_plans/phase1_recovery_integration.md` |
| `CODEX_IMPLEMENTATION/integration_specs/guardian_system_integration.md` |
| `CODEX_IMPLEMENTATION/integration_specs/vscode_workflow_integration.md` |
| `CODEX_IMPLEMENTATION/source_files/automated_recovery_system.py` |
| `CODEX_IMPLEMENTATION/source_files/predictive_failure_detector.py` |
| `CODEX_IMPLEMENTATION/source_files/self_healing_service_manager.py` |
| `CODEX_IMPLEMENTATION/source_files/updatesfor_CLITOOL.json` |
| `CODEX_IMPLEMENTATION/vscode_configuration/README_VSCODE_SETUP.md` |
| `CODEX_IMPLEMENTATION/vscode_configuration/launch.json` |
| `CODEX_IMPLEMENTATION/vscode_configuration/settings.json` |
| `CODEX_IMPLEMENTATION/vscode_configuration/tasks.json` |

### Capabilities

| Archive path |
|---|
| `capabilities/capability_bindings.yaml` |
| `capabilities/cost_limits.yaml` |
| `capabilities/tool_registry.yaml` |

### Catalog

| Archive path |
|---|
| `catalog/domains/build.json` |
| `catalog/domains/git.json` |
| `catalog/domains/k8s.json` |
| `catalog/domains/security.json` |
| `catalog/domains/versioning.json` |
| `catalog/index.json` |
| `catalog/maturity/validated.json` |

### LangGraph

| Archive path |
|---|
| `langgraph_cli.py` |
| `langgraph_git_integration.py` |

### PowerShell Modules

| Archive path |
|---|
| `ps/TradingOps/TradingOps.psd1` |
| `ps/TradingOps/TradingOps.psm1` |
| `ps/install_codex_vscode_profile.ps1` |

### Specs

| Archive path |
|---|
| `specs/fixtures/enhanced_dashboard.sample.json` |
| `specs/openapi/orchestrator-enhanced.yml` |
| `specs/schemas/context_analysis.json` |
| `specs/schemas/live_update.json` |
| `specs/schemas/notification_rule.json` |
| `specs/schemas/workflow_template.json` |
| `specs/websocket/events.yml` |

### Verification

| Archive path |
|---|
| `verify.d/pytest.py` |
| `verify.d/ruff_semgrep.py` |
| `verify.d/schema_validate.py` |

### Workflows

| Archive path |
|---|
| `workflows/__init__.py` |
| `workflows/execution_roadmap.py` |
| `workflows/hello_world/steps/00_validate_inputs.ps1` |
| `workflows/hello_world/steps/10_run_task.ps1` |
| `workflows/hello_world/steps/90_publish_artifacts.ps1` |
| `workflows/hello_world/workflow.yaml` |
| `workflows/orchestrator.py` |
| `workflows/phase_definitions/complete_implementation.yaml` |
| `workflows/phase_definitions/multi_stream.yaml` |
| `workflows/phase_definitions/phase_plan_task.yaml` |
| `workflows/plans/enhanced_workflow_plan.json` |
| `workflows/roadmap_state.json` |
| `workflows/templates/engine.py` |

## Active paths NOT added

The following root-level paths were **not** created; all content lives exclusively under `branch-archive/main/`:

- `.ai/`
- `CODEX_IMPLEMENTATION/`
- `catalog/`
- `capabilities/`
- `ps/`
- `specs/`
- `verify.d/`
- `workflows/` (salvage workflows only)
- `langgraph_cli.py`
- `langgraph_git_integration.py`

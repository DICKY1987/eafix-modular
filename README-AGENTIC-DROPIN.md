This repository includes an agentic drop-in bundle that provides:

- An agentic config and lightweight router (`agentic/`)
- A symbiotic CLI runner (`scripts/symbiotic.py`) that generates a plan, runs validators/mutators, enforces gates, and logs to `.ai/.ai-audit.jsonl`
- A GitHub workflow (`.github/workflows/agentic.yml`) that runs SAST/SCA, lint, type checks, and tests with coverage ≥85%
- VS Code tasks (`.vscode/tasks.json`) to trigger the symbiotic flow and monitor audit and git diffs

Quick start

- Create and activate a virtualenv; install tooling used by the workflow (ruff, mypy, bandit, radon, pytest, coverage, hypothesis, semgrep, pip-audit, PyYAML, gitleaks), or run via CI only.
- Run: `python scripts/symbiotic.py "One-line feature description"`
- Inspect `.ai/manifest.json`, audit log `.ai/.ai-audit.jsonl`, and git diff.

Windows note

- The provided VS Code tasks use POSIX shells (e.g., `. .venv/bin/activate`, `tail`, `watch`). On Windows, adapt these commands to PowerShell equivalents (e.g., `./.venv/Scripts/Activate.ps1`, `Get-Content -Wait`, scheduled git diff).

Hooks setup

- Set repo hooks path and ensure executability of pre-push gate:
  - POSIX: `bash scripts/install_hooks.sh`
  - PowerShell: `./scripts/install_hooks.ps1`
  - Manually: `git config core.hooksPath .githooks`

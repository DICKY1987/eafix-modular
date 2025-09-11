# Symbiotic CLI Workflow — Organized Specification

This document distills your chat into a clean, reusable workflow you can drop into your repos.

## 1) What it does
From a plain-English request (e.g., "Add a CSV export API with 85% coverage"), the system plans, edits, tests, validates, and commits — with live dashboards and strict guardrails.

## 2) Roles & Tools
- **Cockpit agent**: Claude Code **or** OpenAI Codex CLI (auto-edit for tests).
- **Orchestrator**: `scripts/symbiotic.py` (runs validators & gates in parallel).
- **Validators**: ruff, mypy, semgrep, bandit, gitleaks, pytest/coverage, hypothesis (optional: hyperfine, pip-licenses).

## 3) Contract
Cockpit must emit JSON after edits:
```json
{"plan":"...", "changed_files":["..."], "followups":["..."]}
```

## 4) Pipeline (happy path)
1. Preflight → create `ai/feature` branch, snapshot.
2. Plan → Claude plans edits and emits manifest.
3. Implement → apply edits in allowlisted dirs.
4. Validate (parallel) → ruff/mypy/semgrep/bandit/gitleaks.
5. Repair loop (1 pass) if any validator fails.
6. Tests → Codex generates pytest for `manifest.changed_files`; run test suite.
7. Gates → coverage ≥ 85%; complexity delta ≤ +20%; licenses allowed; perf no regression (optional).
8. Checkpoint → commit/tag `tested`.
9. Docs → generate docstrings/markdown for changed areas.
10. Finalize → commit + write audit event to `.ai-audit.jsonl`.

## 5) Dynamic pipeline
Pick extra validators by intent: API/auth → security; frontend → prettier/eslint; data/ETL → Great Expectations/dbt.

## 6) VS Code cockpit (Windows/Linux/macOS)
- Task: **Feature (prompt)** → streams full run (Claude → Codex → validators).
- Dashboard: **Open** Audit log / Git diffs / Test watch in side terminals.
- Tasks: `Validate (fast)` and `Perf Gate` run the gates on demand.

## 7) Safety
Directory allowlist; shell allowlist; denylist patterns (eval/os.system/DROP TABLE); timeouts and cost ceilings; auto-commit checkpoints.

---

See the YAML for machine-readable structure and the Mermaid diagram for the flow.
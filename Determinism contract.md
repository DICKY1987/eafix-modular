Determinism Contract (Agentic Drop-in)

Scope
- Establish a predictable, auditable flow for agent-assisted changes.

Principles
- Reproducibility: Same prompt and codebase state produce the same manifest.
- Observability: All agent actions and validations are logged to `.ai/.ai-audit.jsonl`.
- Safety: Validators (SAST/SCA/lint/type/tests) run before mutators; coverage ≥85% gates changes.
- Least-privilege: Router defaults to OSS path unless cost and confidence permit LLM usage.

Artifacts
- Manifest: `.ai/manifest.json` captures the plan and changed files.
- Audit: `.ai/.ai-audit.jsonl` captures timestamps and tool actions.

Workflow Summary
1) Preflight git snapshot (no-op if clean).
2) Route and generate plan (LLM vs OSS decision).
3) Run read-only validators (semgrep, bandit, gitleaks, mypy, radon).
4) Run code mutators (ruff format/fix).
5) Run tests with coverage gate (≥85%).
6) Enforce additional gates, if any.

Windows considerations
- Replace POSIX shell snippets in tasks with PowerShell equivalents.


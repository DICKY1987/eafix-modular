# Agentic CLI Tools for Rapid Development (v2)

This version expands the original document to include **Gemini CLI, ChatGPT CLI/Agent, and GitHub Copilot**, and adds a concrete **Parallel Workflows + Auto‑Git** section.

---

## 1) Claude Code
### Strengths
- Native Anthropic integration; terminal-native agent for refactors/migrations.
- Parallel tool execution; large context; good safety guardrails.
### Weaknesses
- Model lock-in to Claude; closed-source; limited custom plugins.
### Best Use
- Architectural refactors, structured migrations, safe large-scale edits.

## 2) Aider
### Strengths
- Multi-file edits; strong Git integration; LLM-flexible (Claude/GPT/DeepSeek/local).
### Weaknesses
- CLI learning curve; limited IDE UI; may drift without tight prompts.
### Best Use
- Fast, granular, Git-backed code edits across polyglot repos.

## 3) Cline
### Strengths
- Executes commands/tests; file-aware chat; MCP tool extensibility; snapshots.
### Weaknesses
- No long-term memory; auto-approve can repeat mistakes; feature-rich complexity.
### Best Use
- Execution/validation, DevOps-style automation, end-to-end checks.

## 4) Gemini CLI (Google)
### Strengths
- Open-source agent; multimodal (text+vision); Google Cloud/Workspace APIs; works with LangGraph/CrewAI/LlamaIndex.
### Weaknesses
- Younger ecosystem; Google lock-in if not extended; evolving memory.
### Best Use
- Multimodal R&D, GCP-centric workflows, doc/sheets/search-integrated tasks.

## 5) ChatGPT CLI / Agent (OpenAI)
### Strengths
- Agent mode (research + coding + operations); Deep Research; Codex-style coding; Operator for UI tasks.
### Weaknesses
- Closed ecosystem; can be token-intensive; strict guardrails.
### Best Use
- Knowledge-heavy workflows (research → code), enterprise productivity.

## 6) GitHub Copilot
### Strengths
- Deep IDE integration; Copilot Chat/Workspace; huge adoption; enterprise controls.
### Weaknesses
- Not fully agentic; limited autonomous execution.
### Best Use
- Inline coding companion; pairs well with CLI agents for execution.

---

## 7) Pairings (Cheat Sheet)
- **Claude Code + Aider** → plan/refactor + granular Git-backed edits.
- **Aider + Cline** → generate/edit + run tests/commands; close loop quickly.
- **Claude Code + Cline** → safe large refactor + real execution validation.
- **Gemini CLI + Cline** → multimodal/gen + DevOps/test automation.
- **Copilot + Aider** → IDE suggestions + deterministic CLI commits.
- **ChatGPT Agent + (Aider|Cline)** → research/specs/ADRs + enforcement & tests.

---

## 8) Parallel Workflows + Auto‑Git (Quick Start)
**Isolate each agent in a Git worktree** with its own branch:
```bash
git worktree add ../wt-aider feat/ui-aider
git worktree add ../wt-cline fix/api-cline
git worktree add ../wt-claude refactor/core-claude
```

**Commit policy**
- Commit on green tests or every 10 minutes max.
- Conventional Commits + trailers:
```
feat(ui): sortable table

Tool: Aider
Job: 2025-08-23T01:42:13Z
```

**Pre-commit hooks** (black, ruff, mypy, gitleaks) before every commit.

**Orchestrate** with a tiny PowerShell script and VS Code `tasks.json` to run jobs in parallel, rebase from `main`, run tests, **auto-commit/push**, and open PRs.

---

## 9) Minimal Files to Add
- `.ai/workflows/agent_jobs.yaml` — declarative job manifest
- `.ai/scripts/orchestrate.ps1` — Windows-first orchestrator
- `.vscode/tasks.json` — one-click parallel jobs
- `.github/workflows/ci.yml` — hooks/tests/coverage required for merge
- `.gitmessage.txt` — commit template with Tool/Job trailers

---

## 10) TL;DR
Use **worktrees + pre-commit + merge queue** to keep many agentic CLIs fast and safe. Mix tools by strengths: **Claude/ChatGPT for planning & research**, **Aider for edits**, **Cline for execution**, **Gemini for multimodal & GCP**, **Copilot in-IDE**.

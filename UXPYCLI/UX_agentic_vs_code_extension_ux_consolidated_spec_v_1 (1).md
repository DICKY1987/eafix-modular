# Agentic VS Code Extension UX — Consolidated Spec v1.0

## 1) Purpose & Scope
A single, coherent UX blueprint that merges the two source documents into an implementable interface spec for a VS Code extension that orchestrates multi‑agent AI workflows, guardrails, and cost‑aware task execution. This spec is the builder’s guide for UI layout, interactions, error handling, and configuration flows.

---

## 2) Personas & Primary Goals
- **Solo Dev / Power User**: Wants fast, minimal friction; prefers inline cues over heavy UI.
- **Team Dev / Reviewer**: Needs guardrail previews, policy transparency, and reproducible tasks.
- **Ops/Lead**: Wants policy profiles, cost ceilings, and auditability without deep involvement.

**Goals**
- Run AI tasks with context from the codebase quickly.
- See guardrail issues before committing/pushing.
- Keep configuration in sync and editable via a clear Settings UX.
- Prevent expensive mistakes using proactive checks and cost cues.

---

## 3) UX Principles
- **Context before chrome**: surface info where work happens (editor, status bar) before opening big views.
- **Proactive prevention** over reactive error spam.
- **Progressive disclosure**: short message → details → debug.
- **Single source of truth**: the extension writes to project files atomically; mirrors VS Code settings where helpful.

---

## 4) Information Architecture
### 4.1 Containers & Views
- **Activity Bar Container**: `Agentic`
- **Two Layout Modes** (switchable):
  - **Unified Console** (one Webview with tabs)
  - **Panels Mode** (three Webviews): Logs, Guardrails, Tasks
- **Global Config View**: `Agentic Settings` (dedicated Webview)

### 4.2 Unified Console Tabs
- **Console**: Streamed logs & task outputs with filters/search.
- **Tasks**: Launch/history with progress and resume controls.
- **Guardrails**: Branch/pattern checks, staged diff violations.
- **Config (lite)**: Quick toggles; deep edits open the Settings view.

### 4.3 Panels Mode Views
- **Logs** (focused streaming + filters)
- **Guardrails** (violations, allowed patterns, branch policies)
- **Tasks** (queue, run, resume, cost caps)

### 4.4 Always‑On UI
- **Status Bar**: lane/branch, guardrail badge, cost warning icon.
- **Explorer Decorations**: 🚫 badge for files outside allowed patterns.
- **Editor Inline Hints**: contextual warnings & quick actions.

---

## 5) Primary Screens (Key Elements)
### 5.1 Unified Console (tabbed)
- Toolbar: *Run Task*, *Guardrail Check*, *Create Lane*, *Push → PR*.
- Stream area with level toggles (info/warn/error), copy, and save log.

### 5.2 Logs Panel
- Live tail with debounce, filters (taskId, agent, level), find.
- Sticky task header with elapsed time, cost estimate, cancel.

### 5.3 Guardrails Panel
- Current branch policy preview (allowed prefixes, protected branches).
- **Staged Violations List** with inline fixes:
  - Add pattern → appends to `.ai/guard/allowed_patterns.txt`.
  - Move file suggestion or one‑time override env.
- “Dry‑run pre‑commit” button + results summary.

### 5.4 Tasks Panel
- **Templates** (saved prompts/commands) with one‑click run.
- Context capture: current file, selection, tests to run, cost cap.
- Queue/history; resume failed tasks (phase‑aware).

### 5.5 Config View (full editor)
Tabs: **General**, **Lanes**, **Guardrails**, **Tasks**, **Integrations**, **Secrets**.
- JSON‑schema validated forms; diff preview on save; atomic writes.
- Profiles: *Strict*, *Relaxed*, *Local‑Only* (merge fragments to config).
- Optional auto‑commit on config changes (chore(config): …).

---

## 6) Key Interactions & Flows
### 6.1 Run AI Task (context‑aware)
1) User selects code → *Run Task*.
2) Preflight: keys, quota, lane/branch, guardrails, cost estimate.
3) Execute via orchestrator; stream logs; show cost ticker.
4) On partial failure, present **Resume Options** (retry phase, switch agent, show partial artifacts).

### 6.2 Guardrail Pre‑Commit Preview
1) Detect staged files.
2) Compare to allowed patterns and branch policy.
3) Non‑modal inline warnings (explorer + editor) with quick fixes.

### 6.3 Lane Management
- *Create Lane*: name from template (e.g., `lane/ai-coding/<slug>`).
- Auto‑switch branch, set allowed paths, update status bar.
- Suggest lane creation if editing critical areas on `main`.

### 6.4 Commit Assistant
- Generate Conventional Commit message from staged diff.
- Block when policy demands; show reason & fix buttons.

---


## 6A) Decision Logic — State Machines

Below are state-machine definitions (XState-style) for each primary user intent. Guards are pure predicates; actions are side-effecting effects that call VS Code APIs, orchestrator services, or file/Git utilities. All machines emit structured telemetry to `.ai/logs/*.jsonl`.

> **Naming**: guards use `g.*`, actions use `a.*`, services use `svc.*`.

---

### XState: Code Assistance Intent
```json
{
  "id": "code_assist",
  "initial": "preflight",
  "context": {"file": null, "selection": null, "lane": null, "patterns": [], "costCap": 0, "estimate": null, "agent": null},
  "states": {
    "preflight": {
      "always": [
        {"cond": "g.isLaneAllowed", "target": "checkPatterns"},
        {"target": "laneBlocked", "actions": ["a.ui.promptCreateLane"]}
      ]
    },
    "laneBlocked": {
      "on": {
        "CREATE_LANE": {"target": "creatingLane"},
        "OVERRIDE_ONCE": {"target": "checkPatterns", "actions": ["a.guard.overrideOnce"]},
        "CANCEL": {"target": "cancelled"}
      }
    },
    "creatingLane": {
      "invoke": {"src": "svc.createLaneAndUpdateContext"},
      "on": {"done": {"target": "checkPatterns"}, "error": {"target": "failed", "actions": ["a.ui.showGitError"]}}
    },
    "checkPatterns": {
      "always": [
        {"cond": "g.fileMatchesPatterns", "target": "estimateCost"},
        {"target": "patternViolation", "actions": ["a.ui.showGuardrailFixes"]}
      ]
    },
    "patternViolation": {
      "on": {
        "ADD_PATTERN": {"target": "updatingPatterns"},
        "USE_ANYWAY": {"target": "estimateCost"},
        "MOVE_FILE": {"target": "movingFile"},
        "CANCEL": {"target": "cancelled"}
      }
    },
    "updatingPatterns": {"invoke": {"src": "svc.addPattern"}, "on": {"done": {"target": "estimateCost"}, "error": {"target": "failed"}}},
    "movingFile": {"invoke": {"src": "svc.moveFile"}, "on": {"done": {"target": "estimateCost"}, "error": {"target": "failed"}}},
    "estimateCost": {
      "invoke": {"src": "svc.estimateTaskCost", "onDone": {"actions": ["a.ctx.setEstimate", "a.ctx.setRecommendedAgent"]}},
      "always": [
        {"cond": "g.isHighCost", "target": "confirmCost"},
        {"target": "execute"}
      ]
    },
    "confirmCost": {
      "on": {
        "APPROVE": {"target": "execute"},
        "USE_AIDER": {"target": "execute", "actions": ["a.ctx.useAider"]},
        "CANCEL": {"target": "cancelled"}
      }
    },
    "execute": {
      "invoke": {"src": "svc.routeToAgent"},
      "on": {
        "done": {"target": "completed", "actions": ["a.ui.presentOutcome"]},
        "error": {"target": "failed", "actions": ["a.ui.showRecoveryOptions"]}
      }
    },
    "completed": {"type": "final"},
    "failed": {"type": "final"},
    "cancelled": {"type": "final"}
  }
}
```

---

### XState: Branch/Lane Management Intent
```json
{
  "id": "lane_mgmt",
  "initial": "preflight",
  "context": {"branchClean": true, "laneType": null, "suggestedName": null},
  "states": {
    "preflight": {
      "always": [
        {"cond": "g.isBranchClean", "target": "chooseLaneType"},
        {"target": "dirtyBranch", "actions": ["a.ui.showUncommittedChanges"]}
      ]
    },
    "dirtyBranch": {
      "on": {
        "STASH_CONTINUE": {"target": "stashThenContinue", "actions": ["a.git.stash"]},
        "COMMIT_FIRST": {"target": "cancelled", "actions": ["a.ui.promptCommit"]},
        "CANCEL": {"target": "cancelled"}
      }
    },
    "stashThenContinue": {"always": {"target": "chooseLaneType"}},
    "chooseLaneType": {"on": {"SELECT": {"target": "generateName", "actions": ["a.ctx.setLaneType"]}}},
    "generateName": {"invoke": {"src": "svc.suggestBranchName"}, "on": {"done": {"target": "createLane", "actions": ["a.ctx.setSuggestedName"]}, "error": {"target": "failed"}}},
    "createLane": {"invoke": {"src": "svc.createLaneAndGuardrails"}, "on": {"done": {"target": "completed", "actions": ["a.ui.toastLaneCreated"]}, "error": {"target": "failed", "actions": ["a.ui.showGitError"]}}},
    "completed": {"type": "final"},
    "failed": {"type": "final"},
    "cancelled": {"type": "final"}
  }
}
```

---

### XState: Pre-Commit Validation Intent
```json
{
  "id": "precommit",
  "initial": "scanStaged",
  "states": {
    "scanStaged": {
      "invoke": {"src": "svc.scanStagedFiles"},
      "always": [
        {"cond": "g.hasGuardrailViolations", "target": "violations"},
        {"target": "checkBranchName"}
      ]
    },
    "violations": {
      "entry": ["a.ui.showViolationSummary"],
      "on": {
        "FIX_PATTERNS": {"target": "fixingPatterns", "actions": ["a.guard.updatePatterns"]},
        "OVERRIDE": {"target": "checkBranchName", "actions": ["a.guard.overrideOnce"]},
        "UNSTAGE": {"target": "scanStaged", "actions": ["a.git.unstage"]}
      }
    },
    "fixingPatterns": {"invoke": {"src": "svc.addPatterns"}, "on": {"done": "scanStaged", "error": "failed"}},
    "checkBranchName": {"always": [
      {"cond": "g.branchAllowed", "target": "validateCommitMsg"},
      {"target": "branchViolation", "actions": ["a.ui.blockMainCommit"]}
    ]},
    "branchViolation": {"on": {"CREATE_LANE": "creatingLane", "OVERRIDE": "validateCommitMsg", "CANCEL": "cancelled"}},
    "creatingLane": {"invoke": {"src": "svc.createLaneAndUpdateContext"}, "on": {"done": "validateCommitMsg", "error": "failed"}},
    "validateCommitMsg": {"always": [
      {"cond": "g.commitMsgValid", "target": "allowCommit"},
      {"target": "suggestMsg", "actions": ["a.ui.suggestConventionalCommit"]}
    ]},
    "suggestMsg": {"on": {"USE_SUGGESTION": "allowCommit", "EDIT": "allowCommit", "SKIP": "allowCommit"}},
    "allowCommit": {"invoke": {"src": "svc.commit"}, "on": {"done": {"target": "completed", "actions": ["a.telemetry.postCommit"]}, "error": "failed"}},
    "completed": {"type": "final"},
    "failed": {"type": "final"},
    "cancelled": {"type": "final"}
  }
}
```

---

### XState: Cost/Quota Management Intent
```json
{
  "id": "cost_quota",
  "initial": "openPanel",
  "states": {
    "openPanel": {"entry": ["a.ui.showCostPanel"], "always": "checkLimits"},
    "checkLimits": {"always": [
      {"cond": "g.approachingLimit", "target": "warn"},
      {"target": "normal"}
    ]},
    "warn": {
      "on": {
        "SWITCH_TO_AIDER": {"actions": ["a.routing.useAider"]},
        "INCREASE_LIMIT": {"actions": ["a.config.increaseDailyCap"]},
        "VIEW_DETAILS": {"actions": ["a.ui.showCostBreakdown"]}
      }
    },
    "normal": {
      "on": {
        "SET_DAILY_CAP": {"actions": ["a.config.setDailyCap"]},
        "ENABLE_WARNINGS": {"actions": ["a.config.enableWarnings"]},
        "OFFLINE_MODE": {"actions": ["a.routing.enableOffline"]}
      }
    }
  }
}
```

---

### XState: Error Recovery Intent
```json
{
  "id": "error_recovery",
  "initial": "categorize",
  "context": {"category": null},
  "states": {
    "categorize": {"invoke": {"src": "svc.detectErrorCategory"}, "on": {"done": [{"cond": "g.isInfra", "target": "infra"}, {"cond": "g.isAiService", "target": "aiService"}, {"cond": "g.isGuardrail", "target": "guardrail"}, {"target": "taskExec"}]}},
    "infra": {
      "entry": ["a.ui.showInfraIssue"],
      "on": {
        "START_SERVICES": {"actions": ["a.infra.startCompose"]},
        "OFFLINE": {"actions": ["a.routing.enableOffline"]},
        "VIEW_LOGS": {"actions": ["a.ui.openLogs"]}
      }
    },
    "aiService": {
      "entry": ["a.ui.showAiStatus"],
      "on": {
        "FALLBACK": {"actions": ["a.routing.fallbackAgent"]},
        "RETRY_LATER": {},
        "STATUS": {"actions": ["a.ui.openStatusPage"]}
      }
    },
    "guardrail": {"entry": ["a.ui.explainViolation"], "on": {"FIX_CONFIG": {"actions": ["a.guard.updateConfig"]}, "OVERRIDE_ONCE": {}, "CREATE_EXCEPTION": {"actions": ["a.guard.createException"]}}},
    "taskExec": {"entry": ["a.ui.showPartialFailure"], "on": {"RESUME": {"actions": ["a.tasks.resumeWithContext"]}, "SWITCH_AGENT": {"actions": ["a.routing.switchAgent"]}, "MANUAL": {}}}
  }
}
```

---

### XState: Configuration Management Intent
```json
{
  "id": "config_mgmt",
  "initial": "entryPoint",
  "states": {
    "entryPoint": {
      "on": {
        "OPEN_QUICK": "quick",
        "OPEN_COMMON": "common",
        "OPEN_ADVANCED": "advanced"
      }
    },
    "quick": {"on": {"TOGGLE": {"actions": ["a.settings.toggleQuick"]}, "OPEN_ADVANCED": "advanced"}},
    "common": {"on": {"UPDATE": {"target": "validate", "actions": ["a.ctx.setDraft"]}}},
    "advanced": {"on": {"UPDATE": {"target": "validate", "actions": ["a.ctx.setDraft"]}}},
    "validate": {"invoke": {"src": "svc.validateSchema"}, "on": {"done": "preview", "error": {"target": "invalid", "actions": ["a.ui.showSchemaErrors"]}}},
    "invalid": {"on": {"EDIT": ["common", "advanced"]}},
    "preview": {"entry": ["a.ui.showDiff"], "always": "conflicts"},
    "conflicts": {"invoke": {"src": "svc.detectConflicts"}, "on": {"done": [{"cond": "g.hasConflicts", "target": "resolve"}, {"target": "write"}], "error": "write"}},
    "resolve": {"on": {"USE_PROJECT": {"actions": ["a.config.useProject"]}, "USE_VSCODE": {"actions": ["a.config.useVSCode"]}, "MERGE": {"actions": ["a.config.merge"]}, "CONTINUE": "write"}},
    "write": {"invoke": {"src": "svc.writeAtomic"}, "on": {"done": "completed", "error": "failed"}},
    "completed": {"type": "final"},
    "failed": {"type": "final"}
  }
}
```

---

**Guard Catalog (non-exhaustive)**: `g.isLaneAllowed`, `g.fileMatchesPatterns`, `g.isHighCost`, `g.isBranchClean`, `g.hasGuardrailViolations`, `g.branchAllowed`, `g.commitMsgValid`, `g.approachingLimit`, `g.isInfra`, `g.isAiService`, `g.isGuardrail`, `g.hasConflicts`.

**Action Catalog (non-exhaustive)**: UI (`a.ui.*`), Guardrail (`a.guard.*`), Routing (`a.routing.*`), Git (`a.git.*`), Config (`a.config.*`), Infra (`a.infra.*`), Tasks (`a.tasks.*`), Context helpers (`a.ctx.*`).

## 7) Error Messaging System (Progressive Disclosure)
**Envelope**
- Title, concise message, category, probable cause, next actions.
- Levels: Hint → Warning → Error → Debug.

**Examples**
- **Infrastructure**: “Redis not running” → actions: *Start Redis*, *Check Docker*, *Use Offline Mode*.
- **AI Quota**: “Claude daily limit reached” → actions: *Fallback to Aider*, *Retry later (ETA)*, *Raise cap*.
- **Guardrail**: “Commit blocked (2 files outside patterns)” → actions: *Add pattern*, *Override once*, *Move file*.
- **Task Failure**: “Phase ‘implementation’ timed out” → actions: *Resume with agent X*, *Retry phase only*, *Open partial results*.

**Grouping & Debounce**
- Collapse repeated low‑level errors into a single grouped notification with counts.

---

## 8) Proactive Prevention (“Doctor” Checks)
Run before expensive operations:
- API keys present & valid.
- Service quotas within caps.
- Docker/Compose services healthy.
- Git status clean; correct lane.
- Guardrail violations forecast.
- Cost estimate under threshold.

---

## 9) Configuration Model (Authoritative Files)
- `.ai/framework-config.json` — routing, lanes, tasks, defaults.
- `.ai/guard/allowed_patterns.txt` — glob patterns.
- `.ai/guard/branch_prefixes.txt` — permitted prefixes.
- `.env` — keys and endpoints (handled with masked fields).

**JSON Schema Sketch**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agentic Framework Config",
  "type": "object",
  "properties": {
    "routing": {
      "type": "object",
      "properties": {
        "defaultAgent": {"type": "string", "enum": ["auto","claude","gemini","aider","ollama"]},
        "maxTaskCost": {"type": "number", "minimum": 0},
        "offlineOnly": {"type": "boolean"},
        "quotaWarn": {"type": "number", "minimum": 0, "maximum": 1}
      },
      "required": ["defaultAgent"]
    },
    "lanes": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "branchPrefix": {"type": "string"}, "defaultAgent": {"type": "string"}, "allowedPaths": {"type": "array", "items": {"type": "string"}}}, "required": ["name","branchPrefix"]}},
    "tasks": {"type": "array", "items": {"type": "object", "properties": {"label": {"type": "string"}, "command": {"type": "string"}, "args": {"type": "array", "items": {"type": "string"}}, "lane": {"type": "string"}, "maxCost": {"type": "number"}}, "required": ["label","command"]}}
  }
}
```

---

## 10) VS Code Integration Contracts
- **Settings** (`agenticDev.*`): `layoutMode`, `defaultAgent`, `maxTaskCost`, `offlineOnly`.
- **Commands**: `Agentic: Toggle Layout`, `Create Lane`, `Run Guardrail Check`, `Run Task`.
- **Task Provider**: dynamic tasks (status/execute/test) bridged to orchestrator.
- **Context Keys**: `agenticDev.layoutMode` controls view visibility.
- **Webview Messaging**: JSON events (`log`, `task`, `guardrail`, `configChanged`).

---

## 11) MVP Checklist (Build First)
- Unified Console with tabs and live logs.
- Guardrail dry‑run preview with staged file violations + quick fixes.
- Context menu “Run AI task on selection” with preflight.
- Status bar badges (lane, guardrail, cost warning).
- Config View (General + Guardrails) with schema validation & atomic writes.

**Success Criteria**
- No UI thread blocking; sub‑200ms interactions.
- Clear, actionable errors; zero “Something went wrong”.
- Config edits stay in sync across files and settings.

---


## 11A) Ticket Checklist — MVP → Phase 2 (Commands · Guards · Actions)

> Each ticket references: **Command** (VS Code entry), **Guards** (preconditions), **Actions** (effects/services), and **Artifacts** (files/config touched).

### MVP Tickets
1. **CA-01 · Ask AI About This (editor/context)**  
   **Guards**: `g.isLaneAllowed`, `g.fileMatchesPatterns`, `g.isHighCost`  
   **Actions**: `a.ui.promptCreateLane`, `a.guard.overrideOnce`, `a.ctx.useAider`, `a.ui.presentOutcome`, `svc.routeToAgent`  
   **Artifacts**: `.ai/framework-config.json`, `.ai/logs/*.jsonl`
2. **GR-01 · Guardrail Dry-Run Preview (command)**  
   **Guards**: `g.hasGuardrailViolations`, `g.branchAllowed`  
   **Actions**: `a.ui.showViolationSummary`, `a.guard.updatePatterns`, `a.git.unstage`, `svc.createLaneAndUpdateContext`  
   **Artifacts**: `.ai/guard/*`
3. **LM-01 · Create Agentic Lane (command)**  
   **Guards**: `g.isBranchClean`  
   **Actions**: `a.git.stash`, `svc.suggestBranchName`, `svc.createLaneAndGuardrails`, `a.ui.toastLaneCreated`  
   **Artifacts**: Git branch, `.ai/guard/*`
4. **SB-01 · Status Bar Badges (lane/guardrail/cost)**  
   **Guards**: n/a  
   **Actions**: `a.settings.toggleQuick`, `a.ui.showCostPanel`  
   **Artifacts**: settings.json
5. **CFG-01 · Config View (General + Guardrails) with schema validation**  
   **Guards**: `g.hasConflicts`  
   **Actions**: `svc.validateSchema`, `a.ui.showDiff`, `svc.detectConflicts`, `svc.writeAtomic`  
   **Artifacts**: `.ai/framework-config.json`, `.vscode/settings.json`

### Phase 2 Tickets
6. **CM-02 · Commit Assistant (Conventional Commit)**  
   **Guards**: `g.commitMsgValid`  
   **Actions**: `a.ui.suggestConventionalCommit`, `svc.commit`, `a.telemetry.postCommit`  
   **Artifacts**: `.ai/logs/*.jsonl`
7. **LM-02 · Lane Picker & Auto-Branch Creation**  
   **Guards**: `g.isBranchClean`  
   **Actions**: `a.git.stash`, `svc.suggestBranchName`, `svc.createLaneAndGuardrails`
8. **CA-02 · Resume Failed Task (phase-aware)**  
   **Guards**: n/a  
   **Actions**: `a.tasks.resumeWithContext`, `a.routing.switchAgent`, `a.ui.showRecoveryOptions`  
   **Artifacts**: `.ai/logs/*.jsonl`
9. **COST-02 · Cost Warnings + Optimization Suggestions**  
   **Guards**: `g.approachingLimit`  
   **Actions**: `a.ui.showCostBreakdown`, `a.routing.useAider`, `a.config.setDailyCap`
10. **PR-01 · Push Lane → PR with Policy Checks**  
   **Guards**: `g.branchAllowed`  
   **Actions**: `svc.pushBranch`, `svc.createPullRequest`, `a.ui.showPolicyReport`

---

**Traceability Note**: Each ticket maps to a state node or transition in the machines above. When implementing, keep guard/action names identical across code, telemetry, and docs for grep‑ability and audit.

## 12) Phase 2
- Lane picker + auto branch creation.
- Commit Assistant (Conventional Commit generation).
- Resume failed tasks (phase‑aware), partial artifact viewer.
- Profiles (Strict / Relaxed / Local‑Only) + one‑click switch.

---

## 13) Stretch Goals
- Quota/Cost surface only when relevant (contextual warnings, not dashboards).
- DAG visualizer for workflow status (read‑only).
- PR automation: Push lane → PR with policy checks.

---

## 14) Observability & Telemetry
- Local logs to `.ai/logs/*.jsonl` with taskId, agent, cost, duration.
- Optional Prometheus/Grafana endpoints for org setups.
- Redact secrets; opt‑in only.

---

## 15) Accessibility & Performance
- Keyboard reachable: tabs, actions, lists.
- Screen reader labels (ARIA) for tabs and buttons.
- Debounce/batch stream updates; cap DOM nodes; recycle rows.

---

## 16) Risks & Mitigations
- **Config drift** → single write path + diff preview; background watchers.
- **Feature bloat** → start minimal; hide advanced controls by default.
- **Trust boundaries** → explicit confirmations for spend/commits; profiles.

---

## 17) Open Questions
- Should one‑time guardrail overrides be logged to an audit file?
- Default agent per lane vs global default precedence?
- Auto‑commit for config changes enabled by default?

---

## 18) Glossary
- **Lane**: policy‑aware feature branch with allowed paths and defaults.
- **Guardrails**: commit/push checks enforced in hooks & previewed in UI.
- **Preflight/Doctor**: proactive validation run before expensive steps.

---

## 19) Appendices
- **Event Payloads** (examples):
```json
{ "type": "guardrail", "branch": "lane/ai-coding/auth", "violations": [{"file": "docs/readme.md", "reason": "outside allowed"}] }
{ "type": "task", "id": "T-1029", "phase": "implementation", "status": "failed", "reason": "timeout", "partial": {"plan": "..."} }
{ "type": "log", "level": "warn", "msg": "quota at 80%", "service": "claude" }
```


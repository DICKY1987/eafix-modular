# VS Code Triage Pack — Drop-In Files

This pack makes **VS Code the primary diagnostic engine** in your agentic workflow. It adds a triage overlay for AIS, a runnable workflow, a lightweight router policy, a VS Code extension to export diagnostics to JSON, and orchestration glue.

---

## 📁 File Tree
```
project-root/
├─ ais/
│  └─ TRIAGE_OVERLAY.yaml
├─ .ai/
│  ├─ tmp/
│  │  └─ .gitkeep
│  ├─ router/
│  │  └─ policy.yaml
│  ├─ schemas/
│  │  └─ diagnostics.schema.json
│  └─ workflows/
│     └─ PY_EDIT_TRIAGE.yaml
├─ extensions/
│  └─ agentic-diagnostics-export/
│     ├─ package.json
│     ├─ tsconfig.json
│     └─ src/
│        └─ extension.ts
└─ scripts/
   ├─ run-triage.ps1
   └─ orchestrator_switch_patch.ps1  # (safe switch snippet to paste into your orchestrator)
```

> Notes
> - Keep `.ai/tmp` in Git to persist diagnostic artifacts; `.gitkeep` is included.
> - The VS Code extension is local-only; you can package or sideload.

---

## 1) `ais/TRIAGE_OVERLAY.yaml`
```yaml
triage:
  analyzers:
    - python
    - mypy
    - ruff
    - eslint
    - typescript
  output_file: ".ai/tmp/diagnostics.json"
  categories: ["syntax","import","type","lint","logic","architecture","security","complex"]
  routing:
    syntax:         { target: "auto_fixer",    max_cost_usd: 0 }
    import:         { target: "auto_fixer",    max_cost_usd: 0 }
    lint:           { target: "auto_fixer",    max_cost_usd: 0 }
    type:           { target: "aider_local",   max_cost_usd: 0 }
    logic:          { target: "aider_local",   max_cost_usd: 0 }
    architecture:   { target: "claude_code",   max_cost_usd: 1.00 }
    security:       { target: "manual_review", max_cost_usd: 0 }
    complex:        { target: "claude_code",   max_cost_usd: 1.50 }
  thresholds:
    max_files_simple: 5
    max_errors_simple: 15
    forbid_codes: ["SQLI","SECRETS"]
```

---

## 2) `.ai/workflows/PY_EDIT_TRIAGE.yaml`
```yaml
version: 2
metadata: { id: PY_EDIT_TRIAGE, name: "VS Code First: Diagnose→Route→Fix" }

defaults:
  git: { lane: "py_edit", commit_prefix: "triage-fix:" }
  timeout_seconds: 180

steps:
  - id: "1.001"
    name: "Pre-checks"
    actor: constraint_engine
    actions:
      - { type: run_constraint_set, params: { set: "pre_execution" } }

  - id: "1.002"
    name: "VS Code Diagnostic Analysis"
    actor: vscode_diagnostics
    timeout: 60
    actions:
      - { type: ensure_workspace, params: { path: ".vscode-workspace.code-workspace" } }
      - { type: run_diagnostics, params: { analyzers: "{{triage.analyzers}}", output: "{{triage.output_file}}" } }

  - id: "1.003"
    name: "Categorize & Route"
    actor: issue_router
    actions:
      - { type: categorize_issues, params: { input: "{{triage.output_file}}", categories: "{{triage.categories}}" } }
      - { type: choose_targets, params: { routing: "{{triage.routing}}", thresholds: "{{triage.thresholds}}" } }

  - id: "1.004"
    name: "Execute Fixes in Parallel"
    actor: system
    parallel: true
    tasks:
      auto_fixes:
        condition: "has(auto_fixer)"
        actions:
          - { type: run_cmd, params: { cmd: "ruff check --fix {{files.auto_fixer}}" } }
          - { type: run_cmd, params: { cmd: "isort {{files.auto_fixer}}" } }
          - { type: run_cmd, params: { cmd: "black {{files.auto_fixer}}" } }

      local_ai_fixes:
        condition: "has(aider_local)"
        actions:
          - type: cli_execute
            params:
              command: 'aider --yes --file {{files.aider_local}}'
              prompt: |
                Fix only the listed diagnostics from {{triage.output_file}}.
                Keep behavior identical; do not introduce new code paths.

      premium_ai_fixes:
        condition: "has(claude_code)"
        actions:
          - type: cli_execute
            params:
              command: 'claude code --files {{files.claude_code}}'
              prompt: |
                Address ONLY diagnostics listed in {{triage.output_file}}.
                Keep tests green; avoid broad refactors.

  - id: "1.005"
    name: "Quality Gate"
    actor: system
    parallel: true
    actions:
      - { type: run_cmd, params: { cmd: "ruff check" } }
      - { type: run_cmd, params: { cmd: "mypy" } }
      - { type: run_cmd, params: { cmd: "pytest -q" } }

  - id: "1.006"
    name: "Commit & Push"
    actor: system
    actions:
      - { type: commit, params: { message: "{{defaults.git.commit_prefix}} VS Code triage fixes" } }
      - { type: push, params: { lane: "{{defaults.git.lane}}" } }
```

---

## 3) `.ai/router/policy.yaml`
```yaml
weights:
  base:
    auto_fixer:    1.0
    aider_local:   1.0
    claude_code:   1.0
  by_category:
    syntax:        { auto_fixer: 2.0 }
    import:        { auto_fixer: 2.0 }
    lint:          { auto_fixer: 1.5 }
    type:          { aider_local: 1.5 }
    logic:         { aider_local: 1.0 }
    architecture:  { claude_code: 2.0 }
    security:      { manual: 9.9 }
  by_complexity:
    files_over_5:   { claude_code: 1.0, aider_local: -0.5 }
    errors_over_15: { claude_code: 1.0 }
quota_guards:
  claude_code:
    daily_fraction_threshold: 0.8
    fallback: aider_local
```

---

## 4) `.ai/schemas/diagnostics.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "VS Code Diagnostics Export",
  "type": "object",
  "required": ["schema_version", "items"],
  "properties": {
    "schema_version": { "type": "integer", "minimum": 1 },
    "generated_at": { "type": "string" },
    "workspace": { "type": "string" },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["file","analyzer","code","severity","message","category"],
        "properties": {
          "file": { "type": "string" },
          "analyzer": { "type": "string" },
          "code": { "type": "string" },
          "severity": { "type": "string", "enum": ["info","warning","error"] },
          "message": { "type": "string" },
          "category": { "type": "string", "enum": ["syntax","import","type","lint","logic","architecture","security","complex"] },
          "quick_fix": { "type": "boolean" },
          "range": {
            "type": "object",
            "properties": {
              "start": { "type": "array", "items": { "type": "integer" }, "minItems": 2, "maxItems": 2 },
              "end":   { "type": "array", "items": { "type": "integer" }, "minItems": 2, "maxItems": 2 }
            }
          }
        }
      }
    }
  }
}
```

---

## 5) `extensions/agentic-diagnostics-export/package.json`
```json
{
  "name": "agentic-diagnostics-export",
  "displayName": "Agentic Diagnostics Export",
  "description": "Export VS Code diagnostics to .ai/tmp/diagnostics.json for agentic routing.",
  "version": "0.0.1",
  "publisher": "your-org",
  "engines": { "vscode": "^1.92.0" },
  "categories": ["Other"],
  "activationEvents": ["onCommand:agentic.exportDiagnostics"],
  "contributes": {
    "commands": [
      { "command": "agentic.exportDiagnostics", "title": "Agentic: Export Diagnostics" }
    ]
  },
  "main": "./out/extension.js",
  "scripts": {
    "compile": "tsc -p .",
    "build": "tsc -p ."
  },
  "devDependencies": {
    "@types/vscode": "^1.92.0",
    "typescript": "^5.5.0",
    "tslib": "^2.6.3"
  }
}
```

### `extensions/agentic-diagnostics-export/tsconfig.json`
```json
{
  "compilerOptions": {
    "module": "commonjs",
    "target": "es2020",
    "outDir": "out",
    "lib": ["es2020"],
    "sourceMap": true,
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"]
}
```

### `extensions/agentic-diagnostics-export/src/extension.ts`
```ts
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

type VRange = { start: [number, number]; end: [number, number] };

function categorize(source?: string, code?: string | number, message?: string): string {
  const c = String(code ?? '').toLowerCase();
  const msg = (message ?? '').toLowerCase();
  if (source === 'mypy') return 'type';
  if (source === 'ruff') return 'lint';
  if (source === 'eslint') {
    if (c.startsWith('import/')) return 'import';
    return 'lint';
  }
  if (source === 'typescript') {
    if (msg.includes('cannot find module')) return 'import';
    return 'type';
  }
  if (msg.includes('syntax')) return 'syntax';
  return 'logic';
}

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('agentic.exportDiagnostics', async () => {
    const diags = vscode.languages.getDiagnostics();
    const items: any[] = [];
    for (const [uri, list] of diags) {
      for (const d of list) {
        const codeVal = (typeof d.code === 'object' && d.code) ? (d.code as any).value ?? '' : d.code ?? '';
        const range: VRange = {
          start: [d.range.start.line, d.range.start.character],
          end: [d.range.end.line, d.range.end.character]
        };
        items.push({
          file: vscode.workspace.asRelativePath(uri),
          analyzer: d.source ?? 'vscode',
          code: String(codeVal),
          severity: ['error','warning','info','hint'][d.severity] ?? 'info',
          range,
          message: d.message,
          category: categorize(d.source, codeVal, d.message),
          quick_fix: !!d.tags?.includes(vscode.DiagnosticTag.Unnecessary)
        });
      }
    }
    const payload = {
      schema_version: 1,
      generated_at: new Date().toISOString(),
      workspace: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '.',
      items
    };
    const out = path.resolve(vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '.', '.ai', 'tmp', 'diagnostics.json');
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, JSON.stringify(payload, null, 2), 'utf8');
    vscode.window.showInformationMessage(`Agentic diagnostics exported → ${out}`);
  });
  context.subscriptions.push(disposable);
}

export function deactivate() {}
```

---

## 6) `scripts/run-triage.ps1`
```powershell
param(
  [string[]]$Files = @('src/**/*.py'),
  [string]$Prompt = 'Fix issues from VS Code triage',
  [int]$TimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-Workspace {
  param([string]$Path = '.vscode-workspace.code-workspace')
  if (-not (Test-Path -LiteralPath $Path)) {
    $ws = @{ folders = @(@{ path = '.' }) } | ConvertTo-Json -Depth 5
    Set-Content -LiteralPath $Path -Value $ws -Encoding UTF8
  }
  return $Path
}

function Start-VsCodeDiagnostics {
  param([string]$WorkspacePath, [int]$WaitSeconds = 30)
  & code $WorkspacePath --command agentic.exportDiagnostics | Out-Null
  $diagPath = '.ai/tmp/diagnostics.json'
  $deadline = (Get-Date).AddSeconds($WaitSeconds)
  while (-not (Test-Path $diagPath) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 250 }
  if (-not (Test-Path $diagPath)) { throw "Diagnostics export timed out after $WaitSeconds seconds." }
  return (Get-Content $diagPath -Raw | ConvertFrom-Json).items
}

function Group-IssuesByCategory {
  param($Items)
  $map = @{ auto_fixer=@(); aider_local=@(); claude_code=@(); manual_review=@() }
  foreach ($i in $Items) {
    switch ($i.category) {
      'syntax' { $map.auto_fixer += $i }
      'import' { $map.auto_fixer += $i }
      'lint'   { $map.auto_fixer += $i }
      'type'   { $map.aider_local += $i }
      'logic'  { $map.aider_local += $i }
      'architecture' { $map.claude_code += $i }
      'security' { $map.manual_review += $i }
      default { $map.aider_local += $i }
    }
  }
  return $map
}

function Invoke-AutoFixers {
  param($Items)
  $targets = ($Items | Select-Object -Expand file -Unique)
  if ($targets) {
    $joined = ($targets -join ' ')
    Write-Host "🔧 Auto-fixing: $joined" -ForegroundColor Green
    cmd /c "ruff check --fix $joined"
    cmd /c "isort $joined"
    cmd /c "black $joined"
  }
}

function Invoke-AiderLocal {
  param($Items, [string]$Prompt)
  $targets = ($Items | Select-Object -Expand file -Unique)
  if ($targets) {
    $joined = ($targets -join ' ')
    Write-Host "🤖 Aider(local) on: $joined" -ForegroundColor Cyan
    cmd /c "aider --yes --file $joined --message `"Fix only diagnostics listed in .ai/tmp/diagnostics.json. $Prompt`""
  }
}

function Invoke-ClaudeCode {
  param($Items, [string]$Prompt)
  $targets = ($Items | Select-Object -Expand file -Unique)
  if ($targets) {
    $joined = ($targets -join ' ')
    Write-Host "🧠 Claude Code on: $joined" -ForegroundColor Yellow
    cmd /c "claude code --files $joined --message `"Address ONLY diagnostics in .ai/tmp/diagnostics.json. $Prompt`""
  }
}

function Run-QualityGate {
  Write-Host '✅ Quality gate: ruff/mypy/pytest' -ForegroundColor Magenta
  cmd /c "ruff check"
  cmd /c "mypy"
  cmd /c "pytest -q"
}

function Commit-And-Push {
  param([string]$MessagePrefix = 'triage-fix:')
  git add -A
  if (-not (git diff --cached --quiet)) {
    git commit -m "$MessagePrefix VS Code triage fixes"
    git push
  } else {
    Write-Host 'No changes to commit.' -ForegroundColor DarkGray
  }
}

# Entry
$workspace = Ensure-Workspace
$items = Start-VsCodeDiagnostics -WorkspacePath $workspace -WaitSeconds $TimeoutSeconds
$route = Group-IssuesByCategory -Items $items

if ($route.auto_fixer.Count) { Invoke-AutoFixers -Items $route.auto_fixer }
if ($route.aider_local.Count) { Invoke-AiderLocal -Items $route.aider_local -Prompt $Prompt }
if ($route.claude_code.Count) { Invoke-ClaudeCode -Items $route.claude_code -Prompt $Prompt }

Run-QualityGate
Commit-And-Push
```

---

## 7) `scripts/orchestrator_switch_patch.ps1`
Paste into your orchestrator’s command switch (non-destructive, safe to merge):
```powershell
# Add near other commands in scripts/orchestrator.ps1
param(
  [Parameter(Mandatory=$true)][string]$Command,
  [string[]]$Files,
  [string]$Prompt
)

switch -Regex ($Command) {
  '^start-triage$' {
    & "$PSScriptRoot/run-triage.ps1" -Files $Files -Prompt $Prompt
    break
  }
}
```

---

## 8) `.ai/tmp/.gitkeep`
```text
# keep diagnostic artifacts directory in Git
```

---

## 9) Quickstart

```bash
# 1) Install the extension (from the folder)
# In VS Code: Developer: Install Extension from Location… → extensions/agentic-diagnostics-export

# 2) Run the triage workflow via orchestrator
pwsh scripts/orchestrator.ps1 -Command start-triage -Files "src/**/*.py" -Prompt "Stabilize types and imports"

# Or call the workflow runner directly (if you wire workflows):
# pwsh scripts/orchestrator.ps1 -Command run-workflow -WorkflowId PY_EDIT_TRIAGE
```

---

### Implementation Notes
- The extension exports **all open workspace diagnostics**; analyzers configured in your workspace/settings govern what appears.
- Auto-fixers operate only on files with issues to minimize diff noise.
- Premium routing is quota-aware when you connect this to your router; the provided policy file is deterministic and cheap-first.


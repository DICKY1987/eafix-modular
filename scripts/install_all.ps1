<# 
install_all.ps1 — Windows universal installer for Agentic Framework v3 toolchain
Adds unattended aliases/env + GUARDRAILS (allowed paths, lane-only branches, git hooks).
Can be run in regular PowerShell - will use package managers safely without elevation.
Safe to re-run. 
#>

$ErrorActionPreference = "Stop"

Write-Host "==> Agentic Framework v3 — Windows Installer with Guardrails" -ForegroundColor Cyan

function Test-Command($name) {
  return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

# 1) Core tools via winget if available
if (-not (Test-Command "winget")) {
  Write-Warning "winget not found. Please install Git, Python, Node.js, GitHub CLI, and Docker Desktop manually."
} else {
  Write-Host "[*] Ensuring core apps via winget" -ForegroundColor Yellow
  winget install --id Git.Git -e -h --accept-source-agreements --accept-package-agreements || $true
  winget install --id Python.Python.3.11 -e -h --accept-source-agreements --accept-package-agreements || $true
  winget install --id OpenJS.NodeJS.LTS -e -h --accept-source-agreements --accept-package-agreements || $true
  winget install --id GitHub.cli -e -h --accept-source-agreements --accept-package-agreements || $true
  winget install --id Docker.DockerDesktop -e -h --accept-source-agreements --accept-package-agreements || $true
  # Ollama (optional)
  winget install --id Ollama.Ollama -e -h --accept-source-agreements --accept-package-agreements || $true
}

# 2) Python venv & deps
if (-not (Test-Command "python")) { $python = "py" } else { $python = "python" }
Write-Host "[*] Creating Python virtualenv (.venv)" -ForegroundColor Yellow
& $python -m venv .venv
$venvActivate = Join-Path ".venv" "Scripts\Activate.ps1"
. $venvActivate

Write-Host "[*] Upgrading pip" -ForegroundColor Yellow
python -m pip install --upgrade pip wheel

Write-Host "[*] Installing Python dependencies" -ForegroundColor Yellow
python -m pip install `
  langgraph langchain-anthropic langchain-google-genai langchain-community `
  crewai fastapi typer rich structlog sqlmodel redis pydantic httpx `
  click nox prometheus-client aider-chat

# 3) Node/NPM-based CLIs
if (Test-Command "npm") {
  Write-Host "[*] Installing Claude Code CLI" -ForegroundColor Yellow
  npm install -g @anthropic-ai/claude-code 2>$null || Write-Warning "Skipped @anthropic-ai/claude-code"
  Write-Host "[*] Installing OpenAI Codex CLI (guarded)" -ForegroundColor Yellow
  npm install -g @openai/codex 2>$null || Write-Warning "Skipped @openai/codex (may be unavailable)"
} else {
  Write-Warning "npm not found — skipping Node-based CLIs"
}

# 4) GitHub Copilot CLI (gh extension)
if (Test-Command "gh") {
  Write-Host "[*] Installing GitHub Copilot CLI (gh extension)" -ForegroundColor Yellow
  gh extension install github/gh-copilot 2>$null || Write-Warning "gh-copilot install skipped/failed"
} else {
  Write-Warning "gh not found — cannot install Copilot CLI"
}

# 5) .env setup
Write-Host "[*] Setting up .env" -ForegroundColor Yellow
if (Test-Path ".env") {
  Write-Host "    .env already exists — leaving as-is"
} elseif (Test-Path ".env.example") {
  Copy-Item ".env.example" ".env" -Force
  Write-Host "    Copied .env.example -> .env"
} else {
  @"
# Fill in your API keys and settings
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
LANGSMITH_API_KEY=
REDIS_URL=redis://localhost:6379
"@ | Out-File -Encoding utf8 ".env"
  Write-Host "    Created minimal .env (please fill in your keys)"
}

# 6) Bake unattended aliases/env into PowerShell profile
Write-Host "[*] Baking CLI defaults (non-interactive aliases/env) into PowerShell profile" -ForegroundColor Yellow
$aiDir = Join-Path $HOME ".ai"
New-Item -ItemType Directory -Path $aiDir -Force | Out-Null
$cliSnippet = Join-Path $aiDir "cli_defaults.ps1"

@'
# --- Agentic Framework v3 CLI defaults (PowerShell) ---
# Aider: auto-accept edits
$env:AIDER_YES_ALWAYS = "1"
function aider-auto { aider --yes-always @Args }
function aider-auto-compat { aider --yes @Args }

# Claude Code CLI: skip permission prompts (DANGEROUS — use on disposable branches)
function claude-auto { claude --dangerously-skip-permissions @Args }

# Codex CLI: full-auto (read/write/execute in sandbox, if available)
function codex-auto { codex --full-auto @Args }

# GitHub Copilot CLI helpers (still interactive by design)
Set-Alias ghs "gh"
function ghs { gh copilot suggest @Args }
Set-Alias ghe "gh"
function ghe { gh copilot explain @Args }
'@ | Out-File -Encoding utf8 $cliSnippet

if (-not (Test-Path $PROFILE)) {
  New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}
$sourceLine = '. "$HOME\.ai\cli_defaults.ps1"'
if (-not (Select-String -Path $PROFILE -Pattern [regex]::Escape($sourceLine) -Quiet)) {
  Add-Content -Path $PROFILE -Value $sourceLine
}

# 7) GUARDRAILS: allowed patterns + lane-only branches + git hooks
Write-Host "[*] Installing Git guardrails (allowed paths, lane-only branches, hooks)" -ForegroundColor Yellow
New-Item -ItemType Directory -Path ".ai\guard" -Force | Out-Null
@"
src/**
tests/**
"@ | Out-File -Encoding utf8 ".ai\guard\allowed_patterns.txt"
@"
lane/
feature/
hotfix/
bugfix/
"@ | Out-File -Encoding utf8 ".ai\guard\branches_allowed_prefixes.txt"

# Git hooks are POSIX shell scripts (git runs them via sh on Windows too)
New-Item -ItemType Directory -Path ".git\hooks" -Force | Out-Null

$preCommit = @'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${GUARD_ALLOW_ANY:-}" == "1" ]]; then exit 0; fi
ALLOWED_FILE=".ai/guard/allowed_patterns.txt"
BRANCHES_FILE=".ai/guard/branches_allowed_prefixes.txt"
PROTECTED_BRANCHES_REGEX="^(main|master|develop)$"
current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
if [[ "$current_branch" =~ $PROTECTED_BRANCHES_REGEX ]] && [[ "${ALLOW_PROTECTED:-}" != "1" ]]; then
  echo "❌ Commit blocked: branch '$current_branch' is protected. Set ALLOW_PROTECTED=1 to override." >&2
  exit 1
fi
if [[ -f "$BRANCHES_FILE" ]]; then
  allowed_prefix=0
  while IFS= read -r pref; do
    [[ -z "$pref" ]] && continue
    if [[ "$current_branch" == "$pref"* ]]; then allowed_prefix=1; break; fi
  done < "$BRANCHES_FILE"
  if [[ $allowed_prefix -eq 0 && "${ALLOW_BRANCH_ANY:-}" != "1" ]]; then
    echo "❌ Commit blocked: branch '$current_branch' not in allowed prefixes. Use lane/ or feature/ or set ALLOW_BRANCH_ANY=1." >&2
    exit 1
  fi
fi
mapfile -t files < <(git diff --cached --name-only --diff-filter=ACMR)
[[ ${#files[@]} -eq 0 ]] && exit 0
[[ ! -f "$ALLOWED_FILE" ]] && exit 0
while IFS= read -r pattern; do
  [[ -z "$pattern" ]] && continue
  allowed_patterns+=("$pattern")
done < "$ALLOWED_FILE"
fail=0
for f in "${files[@]}"; do
  case "$f" in
    src/*|tests/*) matched=1 ;;
    *) matched=0 ;;
  esac
  if [[ $matched -eq 0 ]]; then
    echo "❌ Commit blocked: '$f' is outside allowed paths. Allowed: $(tr '\n' ' ' < "$ALLOWED_FILE")" >&2
    fail=1
  fi
done
[[ $fail -ne 0 ]] && { echo "Hint: adjust .ai/guard/allowed_patterns.txt or set GUARD_ALLOW_ANY=1 to override." >&2; exit 1; }
exit 0
'@
$prePush = @'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${ALLOW_PROTECTED_PUSH:-}" == "1" ]]; then exit 0; fi
protected_regex="^(main|master|develop)$"
while read -r local_ref local_sha remote_ref remote_sha; do
  branch="${local_ref#refs/heads/}"
  if [[ "$branch" =~ $protected_regex ]]; then
    echo "❌ Push blocked: pushing to protected branch '$branch' is disabled. Open a PR from a lane/ or feature/ branch, or set ALLOW_PROTECTED_PUSH=1." >&2
    exit 1
  fi
done
exit 0
'@
$commitMsg = @'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${ALLOW_ANY_MESSAGE:-}" == "1" ]]; then exit 0; fi
msg_file="$1"
msg="$(head -n1 "$msg_file" | tr -d "\r")"
pattern="^(feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)(\([a-z0-9._-]+\))?: .+"
if ! [[ "$msg" =~ $pattern ]]; then
  echo "⚠️  Commit message not in Conventional Commits format." >&2
  echo "    Example: feat(auth): add JWT rotation" >&2
  echo "    Set ALLOW_ANY_MESSAGE=1 to override." >&2
  exit 1
fi
exit 0
'@

Set-Content -Path ".git\hooks\pre-commit" -Value $preCommit -NoNewline -Encoding ascii
Set-Content -Path ".git\hooks\pre-push" -Value $prePush -NoNewline -Encoding ascii
Set-Content -Path ".git\hooks\commit-msg" -Value $commitMsg -NoNewline -Encoding ascii

# Mark as executable when possible (Git for Windows respects the presence; chmod may be no-op)
try { & git update-index --chmod=+x .git/hooks/pre-commit } catch {}
try { & git update-index --chmod=+x .git/hooks/pre-push } catch {}
try { & git update-index --chmod=+x .git/hooks/commit-msg } catch {}

Write-Host "`n==> Installation complete." -ForegroundColor Green
Write-Host "Non-interactive defaults added; Git guardrails enabled."
Write-Host "Restart PowerShell (or run: . $PROFILE) and try: python agentic_framework_v3.py status"

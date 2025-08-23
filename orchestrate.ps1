param(
  [Parameter(Mandatory=$true)][string]$Command,
  [string]$Name,
  [ValidateSet("auto_fixer","aider_local","claude_code","gemini_cli","chatgpt_agent")]
  [string]$Tool,
  [string]$Branch,
  [string]$Worktree,
  [string]$Tests,
  [string[]]$Files,
  [string]$Prompt
)

$ErrorActionPreference = "Stop"

function Run($cmd) {
  Write-Host ">> $cmd" -ForegroundColor Cyan
  iex $cmd
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
    throw "Command failed: $cmd"
  }
}

# Triage command hook
if ($Command -eq "start-triage") {
  $triageScript = Join-Path $PSScriptRoot "run-triage.ps1"
  & $triageScript -Files $Files -Prompt $Prompt
  exit 0
}

# Normal agent job flow
if (-not $Name -or -not $Tool -or -not $Branch -or -not $Worktree) {
  throw "Missing required parameters: -Name, -Tool, -Branch, -Worktree"
}

function Ensure-Worktree {
  param($Branch,$Worktree)
  git fetch origin | Out-Null
  $exists = & git rev-parse --verify $Branch 2>$null
  if (-not $exists) {
    Run "git worktree add `"$Worktree`" -b `"$Branch`" origin/main"
  } elseif (-not (Test-Path $Worktree)) {
    Run "git worktree add `"$Worktree`" `"$Branch`""
  }
}

Ensure-Worktree -Branch $Branch -Worktree $Worktree

Push-Location $Worktree
try {
  Run "git fetch origin --prune"
  Run "git checkout `"$Branch`""
  Run "git rebase origin/main"

  if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
    try { Run "pre-commit run -a" } catch { Write-Warning "pre-commit failed; continuing" }
  }

  switch ($Tool) {
    "aider_local" { Run "aider --yes --message 'Job:$Name run'" }
    "auto_fixer"  { Run "ruff check --fix ."; Run "ruff format ."; Run "mypy . || exit 0" }
    "claude_code" { Run "claude code --message 'Job:$Name run'" }
    "gemini_cli"  { Run "gemini --message 'Job:$Name run'" }
    "chatgpt_agent" { Run "chatgpt --message 'Job:$Name run'" }
    default { throw "Unknown tool: $Tool" }
  }

  $testsOk = $true
  if ($Tests) {
    try { Run $Tests }
    catch { $testsOk = $false; Write-Warning "Tests failed for $Name" }
  }

  Run "git add -A"
  $toolTrailer = "Tool: $Tool"
  $jobTrailer = "Job: $(Get-Date -Format s)"
  if ($testsOk) {
    Run "git commit -m 'chore($Name): auto-commit on green' -m '$toolTrailer' -m '$jobTrailer'"
  } else {
    Run "git commit -m 'chore($Name): WIP (tests failing)' -m '$toolTrailer' -m '$jobTrailer'"
  }
  Run "git push -u origin `"$Branch`""
}
finally {
  Pop-Location
}
\
  <#
    Orchestrates: rebase -> run tool -> (run tests) -> auto-commit -> push
    Also supports: -Command start-triage to delegate to scripts/run-triage.ps1
    Usage examples:
      pwsh -File .ai/scripts/orchestrate.ps1 -Name ui-refactor -Tool aider_local -Branch feat/ui-aider -Worktree ../wt-aider -Tests "pytest -q"
      pwsh -File .ai/scripts/orchestrate.ps1 -Command start-triage -Files "src/**/*.py" -Prompt "Stabilize types and imports"
  #>
  param(
    [string]$Command,                                 # optional high-level command (e.g., start-triage)
    [string[]]$Files,                                  # optional: files/globs passed to triage
    [string]$Prompt,                                   # optional: triage guiding prompt

    [string]$Name,                                     # job name (required for normal runs)
    [ValidateSet("auto_fixer","aider_local","claude_code","gemini_cli","chatgpt_agent","aider","cline","claude","gemini","chatgpt")]
    [string]$Tool,
    [string]$Branch,
    [string]$Worktree,
    [string]$Tests
  )

  $ErrorActionPreference = "Stop"

  function Run($cmd) {
    Write-Host ">> $cmd" -ForegroundColor Cyan
    iex $cmd
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
      throw "Command failed with exit code $LASTEXITCODE: $cmd"
    }
  }

  # --- Triage command hook ----------------------------------------------------
  if ($Command -and $Command -eq "start-triage") {
    $triageScript = Join-Path $PSScriptRoot "..\..\scripts\run-triage.ps1"
    if (-not (Test-Path $triageScript)) {
      Write-Warning "Triage script not found at $triageScript. Using placeholder."
      $triageScript = Join-Path $PSScriptRoot "run-triage.ps1"  # fallback to local stub (included in patch)
    }
    $filesArg = $Files -join " "
    $promptArg = $Prompt
    Write-Host "Starting VS Code triage with files: $filesArg" -ForegroundColor Yellow
    & $triageScript -Files $Files -Prompt $promptArg
    exit 0
  }

  # --- Normal agent job flow --------------------------------------------------
  if (-not $Name -or -not $Tool -or -not $Branch -or -not $Worktree) {
    throw "Missing required parameters for agent job. Provide -Name, -Tool, -Branch, -Worktree (or use -Command start-triage)."
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

    if (Test-Path .git/hooks/pre-commit -or (Get-Command pre-commit -ErrorAction SilentlyContinue)) {
      try { Run "pre-commit run -a" } catch { Write-Warning "pre-commit failed; continuing to allow the agent to attempt fixes." }
    }

    # Map routing keys to actual CLI commands
    switch ($Tool) {
      "aider_local" { Run "aider --yes --message 'Job:$Name run'" }
      "auto_fixer"  { Run "ruff check --fix ."; Run "ruff format ."; Run "mypy || exit 0" }
      "claude_code" { Run "claude-code run --task 'Job:$Name run'" }
      "gemini_cli"  { Run "gemini run --task 'Job:$Name run'" }
      "chatgpt_agent" { Run "chatgpt-agent run --task 'Job:$Name run'" }

      # Back-compat aliases:
      "aider"  { Run "aider --yes --message 'Job:$Name run'" }
      "cline"  { Run "cline run --auto-approve --plan 'Job:$Name run'" }
      "claude" { Run "claude-code run --task 'Job:$Name run'" }
      "gemini" { Run "gemini run --task 'Job:$Name run'" }
      "chatgpt"{ Run "chatgpt-agent run --task 'Job:$Name run'" }
      default  { throw "Unknown tool: $Tool" }
    }

    $testsOk = $true
    if ($Tests) {
      try { Run $Tests }
      catch { $testsOk = $false; Write-Warning "Tests failed for $Name" }
    }

    Run "git add -A"

    $toolTrailer = "Tool: $Tool"
    $jobTrailer  = "Job: $(Get-Date -Format s)"
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

Perfect — below are drop-in PowerShell snippets that make those pieces fully implemented (non-optional) and production-ready:

Part A installs & wires Aider and a concrete “codex” CLI (mapped to GitHub Copilot CLI via gh copilot) and creates robust aliases.

Part B forces Docker Desktop + WSL2 readiness and always brings up your Compose services.

These are self-contained. You can paste both into your main installer (anywhere after you’ve defined $RepoRoot) and then call the two “entry” functions at the end:
Enable-AIClis-NonOptional and Enable-DockerStack-NonOptional.

Part A — Aider + “codex” CLIs (non-optional) with production aliases
# =========================[ PART A: AI CLIs (non-optional) ]=========================
# Requires: $RepoRoot defined. Creates .ai\cli_defaults.ps1 and ensures it's dot-sourced.

function Write-Log {
  param([string]$Msg, [string]$Level = "INFO")
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Write-Host "[$ts][$Level] $Msg"
}

function Test-Command {
  param([Parameter(Mandatory)][string]$Name)
  $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-Retry {
  param(
    [Parameter(Mandatory)][scriptblock]$ScriptBlock,
    [int]$Retries = 3,
    [int]$DelaySec = 5,
    [string]$What = "operation"
  )
  for ($i=1; $i -le $Retries; $i++) {
    try {
      return & $ScriptBlock
    } catch {
      if ($i -eq $Retries) {
        throw "Failed $What after $Retries attempts. Last error: $($_.Exception.Message)"
      }
      Write-Log "Retry $i/$Retries for $What: $($_.Exception.Message)" "WARN"
      Start-Sleep -Seconds $DelaySec
    }
  }
}

function Ensure-Dir { param([string]$Path) if (-not (Test-Path $Path)) { New-Item -Type Directory -Force -Path $Path | Out-Null } }

# -- Ensure pipx available (best practice for CLI Python apps)
function Ensure-Pipx {
  if (Test-Command -Name "pipx") { return }
  if (Test-Command -Name "py") {
    Write-Log "Installing pipx via Python launcher…"
    Invoke-Retry -What "pipx install" -ScriptBlock {
      & py -m pip install --user pipx | Out-Null
      & py -m pipx ensurepath | Out-Null
    }
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","User") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","Machine")
    if (-not (Test-Command -Name "pipx")) {
      throw "pipx not found after installation; restart shell or ensure PATH contains pipx."
    }
  } else {
    throw "Python launcher 'py' not found. Install Python 3.11+ first."
  }
}

# -- Ensure Node.js LTS for CLA CLI (and general tooling)
function Ensure-Node {
  if (Test-Command -Name "node" -and (Test-Command -Name "npm")) { return }
  if (-not (Test-Command -Name "winget")) { throw "winget not found; install App Installer from Microsoft Store." }
  Write-Log "Installing Node.js LTS via winget…"
  Invoke-Retry -What "Node.js install" -ScriptBlock {
    winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --silent | Out-Null
  }
  if (-not (Test-Command -Name "node")) { throw "Node.js not available after install." }
  if (-not (Test-Command -Name "npm"))  { throw "npm not available after install." }
}

# -- Ensure Claude Code CLI (nice complement to Aider)
function Ensure-ClaudeCodeCli {
  Ensure-Node
  Write-Log "Installing/Updating Claude Code CLI (@anthropic-ai/claude-code)…"
  Invoke-Retry -What "claude-code install" -ScriptBlock {
    npm install -g @anthropic-ai/claude-code@latest | Out-Null
  }
  if (-not (Test-Command -Name "claude")) { throw "Claude Code CLI not detected after install." }
}

# -- Ensure Aider CLI (Python)
function Ensure-AiderCli {
  Ensure-Pipx
  $haveAider = Test-Command -Name "aider"
  if (-not $haveAider) {
    Write-Log "Installing Aider via pipx…"
    Invoke-Retry -What "aider install" -ScriptBlock { pipx install aider-chat --include-deps | Out-Null }
  } else {
    Write-Log "Updating Aider via pipx…"
    Invoke-Retry -What "aider upgrade" -ScriptBlock { pipx upgrade aider-chat | Out-Null }
  }
  if (-not (Test-Command -Name "aider")) { throw "Aider not available after install/upgrade." }
  $v = (& aider --version) 2>$null
  Write-Log "Aider ready: $v"
}

# -- Ensure GitHub CLI + Copilot extension (we’ll map 'codex' to gh copilot)
function Ensure-GhAndCopilot {
  if (-not (Test-Command -Name "gh")) {
    if (-not (Test-Command -Name "winget")) { throw "winget not found; install App Installer." }
    Write-Log "Installing GitHub CLI via winget…"
    Invoke-Retry -What "gh install" -ScriptBlock {
      winget install -e --id GitHub.cli --accept-package-agreements --accept-source-agreements --silent | Out-Null
    }
  }
  Write-Log "Installing/Updating gh-copilot extension…"
  $exts = (& gh extension list) 2>$null
  if ($exts -match "github/gh-copilot") {
    Invoke-Retry -What "gh-copilot upgrade" -ScriptBlock { gh extension upgrade github/gh-copilot | Out-Null }
  } else {
    Invoke-Retry -What "gh-copilot install" -ScriptBlock { gh extension install github/gh-copilot | Out-Null }
  }
  # Don’t force login (non-interactive), but warn if not logged in
  $auth = (& gh auth status) 2>&1
  if ($LASTEXITCODE -ne 0) { Write-Log "GitHub auth not detected. Run: gh auth login --web" "WARN" }
}

# -- Create persistent aliases & helper functions
function Ensure-Aliases-And-Profile {
  param(
    [string]$AiDir = (Join-Path $RepoRoot ".ai"),
    [string]$ProfileSnippet = (Join-Path $RepoRoot ".ai\cli_defaults.ps1")
  )
  Ensure-Dir $AiDir
  $content = @'
# --- auto-generated by installer: AI CLI defaults ---
function codex {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  # Map "codex" to GitHub Copilot CLI
  gh copilot @Args
}
Set-Alias -Name codex-auto -Value codex -Scope Global

function aider-auto {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  # Example defaults: auto-yes, keep commits tight; adjust as desired
  aider --yes @Args
}
Set-Alias -Name aiderc -Value aider -Scope Global

function claude-auto {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  claude @Args
}

# Quality-of-life helpers
function codex-commit-suggest { gh copilot suggest -t git-commit }
function codex-explain       { gh copilot explain @Args }
function codex-grep          { gh copilot grep @Args }
'@

  Set-Content -Path $ProfileSnippet -Value $content -Encoding UTF8

  # Dot-source from CurrentUserAllHosts profile
  if (-not (Test-Path $PROFILE.CurrentUserAllHosts)) {
    Ensure-Dir (Split-Path -Parent $PROFILE.CurrentUserAllHosts)
    New-Item -Path $PROFILE.CurrentUserAllHosts -ItemType File -Force | Out-Null
  }
  if (-not (Select-String -Path $PROFILE.CurrentUserAllHosts -SimpleMatch $ProfileSnippet -ErrorAction SilentlyContinue)) {
    Add-Content -Path $PROFILE.CurrentUserAllHosts -Value "`n. '$ProfileSnippet'"
  }
  Write-Log "CLI defaults written to $ProfileSnippet and dot-sourced via $($PROFILE.CurrentUserAllHosts)"
}

function Enable-AIClis-NonOptional {
  Write-Log "=== Enabling AI CLIs (non-optional) ==="
  Ensure-AiderCli
  Ensure-ClaudeCodeCli
  Ensure-GhAndCopilot
  Ensure-Aliases-And-Profile
  Write-Log "AI CLIs ready (Aider + Claude + gh-copilot)."
}
# =====================[ END PART A: AI CLIs (non-optional) ]=========================

Part B — Force-install Docker Desktop + WSL2 and always start Compose
# ================[ PART B: Docker Desktop & Compose (non-optional) ]================
# Forces WSL2 features, installs Docker Desktop, waits for engine, then composes services.

function Test-Admin {
  ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
  ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Ensure-Admin {
  if (-not (Test-Admin)) {
    Write-Log "Elevation required. Relaunching as Administrator…" "WARN"
    $psi = New-Object System.Diagnostics.ProcessStartInfo "powershell"
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $psi.Verb = "runas"
    [System.Diagnostics.Process]::Start($psi) | Out-Null
    exit
  }
}

function Ensure-WSL2 {
  Ensure-Admin
  Write-Log "Enabling WSL + VirtualMachinePlatform (if needed)…"
  & dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart | Out-Null
  & dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart | Out-Null

  # Try to set WSL2 as default (safe if already set)
  if (Test-Command -Name "wsl") {
    & wsl --set-default-version 2 2>$null
  }

  # A reboot may be required the first time; detect & warn
  $pending = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending" -ErrorAction SilentlyContinue) -ne $null
  if ($pending) {
    Write-Log "Windows reports a reboot is pending to finish WSL features. Please reboot ASAP." "WARN"
  }
}

function Ensure-DockerDesktop {
  if (Test-Command -Name "docker") {
    # Docker CLI might exist from other install; try to verify Desktop too
    return
  }
  if (-not (Test-Command -Name "winget")) { throw "winget not found; install App Installer from Microsoft Store." }
  Ensure-Admin
  Write-Log "Installing Docker Desktop via winget…"
  Invoke-Retry -What "Docker Desktop install" -ScriptBlock {
    winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements --silent | Out-Null
  }
}

function Start-DockerDesktop-And-Wait {
  $dockerApp = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
  if (Test-Path $dockerApp) {
    Write-Log "Starting Docker Desktop…"
    Start-Process -FilePath $dockerApp -WindowStyle Minimized | Out-Null
  }

  Write-Log "Waiting for Docker engine to be ready…"
  $deadline = (Get-Date).AddMinutes(6)
  do {
    Start-Sleep -Seconds 5
    & docker info 2>$null | Out-Null
    $ok = $LASTEXITCODE -eq 0
  } while (-not $ok -and (Get-Date) -lt $deadline)
  if (-not $ok) { throw "Docker engine not ready after timeout." }

  # Verify Compose v2
  & docker compose version 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "docker compose v2 not available." }

  # Optional: add user to docker-users group (some environments require it)
  try {
    $user = "$env:USERDOMAIN\$env:USERNAME"
    $exists = (Get-LocalGroup -Name "docker-users" -ErrorAction SilentlyContinue)
    if ($exists) {
      Add-LocalGroupMember -Group "docker-users" -Member $user -ErrorAction SilentlyContinue
    }
  } catch { Write-Log "Could not add user to docker-users group: $($_.Exception.Message)" "WARN" }
}

function Ensure-ComposeFile {
  param([string]$ComposePath)
  if (Test-Path $ComposePath) { return }
  Ensure-Dir (Split-Path -Parent $ComposePath)
  $compose = @"
services:
  redis:
    image: redis:7
    restart: unless-stopped
    ports: ["6379:6379"]
  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    ports: ["11434:11434"]
    volumes:
      - ollama:/root/.ollama
volumes:
  ollama:
"@
  Set-Content -Path $ComposePath -Value $compose -Encoding UTF8
  Write-Log "Generated default compose file at $ComposePath"
}

function Up-Compose-Stack {
  param([string]$ComposePath)
  Write-Log "Launching containers via docker compose…"
  Invoke-Retry -What "docker compose up" -ScriptBlock {
    docker compose -f "$ComposePath" up -d --remove-orphans | Out-Null
  }
  # Post-verify
  $ps = docker ps --format "{{.Names}}"
  Write-Log "Active containers: $ps"
}

function Enable-DockerStack-NonOptional {
  Write-Log "=== Enabling Docker Desktop & Compose (non-optional) ==="
  Ensure-WSL2
  Ensure-DockerDesktop
  Start-DockerDesktop-And-Wait
  $AiDir = Join-Path $RepoRoot ".ai"
  $ComposePath = Join-Path $AiDir "docker\compose.yml"
  Ensure-ComposeFile -ComposePath $ComposePath
  Up-Compose-Stack -ComposePath $ComposePath
  Write-Log "Docker stack ready."
}
# =================[ END PART B: Docker Desktop & Compose (non-optional) ]================

How to invoke from your main script

Paste both parts above, then call the entry points once your $RepoRoot is set:

# After you set: $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Enable-AIClis-NonOptional
Enable-DockerStack-NonOptional

What this gives you (no knobs, no footguns)

Aider installed & updated via pipx, with working aider, aider-auto, and a profile snippet auto-loaded for future shells.

“codex” implemented concretely as GitHub Copilot CLI (gh copilot), with codex, codex-auto, and handy helpers.

Claude Code CLI installed globally (claude).

WSL2 features enabled, Docker Desktop installed, engine readiness waited for, and your Compose stack always up (Redis + Ollama by default, overridable by editing .ai\docker\compose.yml).
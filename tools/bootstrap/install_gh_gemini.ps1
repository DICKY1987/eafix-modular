#requires -Version 5.1
[CmdletBinding()]
param(
  [switch]$Force
)

Write-Host "[setup] Starting GitHub CLI + Gemini CLI bootstrap..." -ForegroundColor Cyan

function Test-Command {
  param([string]$Name)
  $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Ensure-Winget {
  if (Test-Command winget) { return }
  Write-Warning "winget not found. On Windows 11/10, install 'App Installer' from Microsoft Store. Aborting."
  throw "winget is required. Install App Installer, then re-run."
}

function Install-WingetPackage {
  param(
    [Parameter(Mandatory)] [string]$Id,
    [string]$Name
  )
  $display = if ($Name) { $Name } else { $Id }
  Write-Host "[winget] Installing $display ..." -ForegroundColor Yellow
  $args = @('install','-e','--id', $Id,'--accept-package-agreements','--accept-source-agreements')
  $proc = Start-Process -FilePath winget -ArgumentList $args -NoNewWindow -PassThru -Wait
  if ($proc.ExitCode -ne 0) { throw "Failed to install $display via winget (exit $($proc.ExitCode))" }
}

function Ensure-PathContains {
  param([string]$PathEntry)
  $current = [Environment]::GetEnvironmentVariable('Path','User')
  if (-not ($current -split ';' | Where-Object { $_ -ieq $PathEntry })) {
    [Environment]::SetEnvironmentVariable('Path', ($current.TrimEnd(';') + ';' + $PathEntry), 'User')
    Write-Host "[env] Added to PATH (User): $PathEntry" -ForegroundColor Green
  }
}

try {
  Ensure-Winget

  # 1) NodeJS LTS (needed for Gemini CLI)
  Install-WingetPackage -Id 'OpenJS.NodeJS.LTS' -Name 'NodeJS LTS'

  # 2) GitHub CLI
  Install-WingetPackage -Id 'GitHub.cli' -Name 'GitHub CLI (gh)'

  # 3) Gemini CLI (global via npm)
  Write-Host "[npm] Installing @google/gemini-cli@latest ..." -ForegroundColor Yellow
  $npm = (Get-Command npm -ErrorAction Stop).Source
  $proc = Start-Process -FilePath $npm -ArgumentList @('install','-g','@google/gemini-cli@latest') -NoNewWindow -PassThru -Wait
  if ($proc.ExitCode -ne 0) { throw "npm global install failed (exit $($proc.ExitCode))" }

  # Ensure typical npm global bin path is on PATH for this user
  $npmUserBin = Join-Path $env:APPDATA 'npm'
  if (Test-Path $npmUserBin) { Ensure-PathContains -PathEntry $npmUserBin }

  # 4) Versions
  Write-Host "\n[versions]" -ForegroundColor Cyan
  & node -v
  & npm -v
  & gh --version
  & gemini --version

  Write-Host "\n[ok] Bootstrap complete. Next steps:" -ForegroundColor Cyan
  Write-Host "  • Run: gh auth login    (choose GitHub.com → HTTPS → Login with a web browser)" -ForegroundColor Gray
  Write-Host "  • Run: gemini            (choose Login with Google OR set GEMINI_API_KEY from .env)" -ForegroundColor Gray
}
catch {
  Write-Error $_
  exit 1
}
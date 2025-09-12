$ErrorActionPreference = 'Stop'
Write-Host "Configuring Git hooks to use .githooks..."
& git config core.hooksPath .githooks

if (Test-Path .githooks\pre-push) {
  try {
    & git update-index --chmod=+x .githooks/pre-push | Out-Null
  } catch { }
}

Write-Host "Done. Hooks path set to .githooks"


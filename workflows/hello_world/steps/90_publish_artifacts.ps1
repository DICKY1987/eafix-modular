$ErrorActionPreference = 'Stop'

Write-Host "[hello_world] Publishing artifacts (noop for local run)..."
if (-not (Test-Path 'artifacts/hello_world/hello.txt')) {
  Write-Warning "No artifact found; did 10_run_task.ps1 run?"
}
exit 0

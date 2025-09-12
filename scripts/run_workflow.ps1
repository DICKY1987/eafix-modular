Param(
  [string]$Name = 'World'
)

$ErrorActionPreference = 'Stop'
Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "[run_workflow] Starting hello_world..."
& 'workflows/hello_world/steps/00_validate_inputs.ps1' -Name $Name
& 'workflows/hello_world/steps/10_run_task.ps1'
& 'workflows/hello_world/steps/90_publish_artifacts.ps1'

if (Test-Path 'artifacts/hello_world/hello.txt') {
  Write-Host "[run_workflow] Artifact ready: artifacts/hello_world/hello.txt"
}
Write-Host "[run_workflow] Completed."

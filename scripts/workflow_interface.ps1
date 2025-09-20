$ErrorActionPreference = 'Stop'

# Navigate to repo
Set-Location -Path "$PSScriptRoot\.." | Out-Null

# Activate virtual environment if present
$venv = Join-Path -Path (Get-Location) -ChildPath ".venv\Scripts\Activate.ps1"
if (Test-Path $venv) { . $venv }

# Ensure Python sees src and repo root
$env:PYTHONPATH = "src;$(Get-Location)"

# Show streams map as the default interface
python -m workflows.orchestrator list-streams

# Keep session open
Write-Host "`nTip: Run 'python -m workflows.orchestrator run-stream stream-a --dry-run' to plan a stream."

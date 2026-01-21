param(
  [ValidateSet("validation", "acceptance")]
  [string]$Mode = "validation"
)

$moduleRoot = Split-Path -Parent $PSScriptRoot
$requiredPaths = @(
  "module.manifest.yaml",
  "schemas\module.manifest.schema.json",
  "scripts\validate_structure.ps1",
  "README.md",
  "DEEP_DIVE.md",
  "WORKFLOW.md",
  "SCHEMA_ADDITIONS.md",
  "ARTIFACT_INVENTORY.md"
)

$missing = @()
foreach ($rel in $requiredPaths) {
  $path = Join-Path $moduleRoot $rel
  if (-not (Test-Path -LiteralPath $path)) {
    $missing += $rel
  }
}

$evidenceDir = Join-Path $moduleRoot ("evidence\\" + $Mode)
if (-not (Test-Path -LiteralPath $evidenceDir)) {
  New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
}

$reportPath = Join-Path $evidenceDir ("structure_" + $Mode + ".json")
$report = [pscustomobject]@{
  timestamp = (Get-Date -Format "s")
  mode = $Mode
  ok = ($missing.Count -eq 0)
  missing = $missing
}
$report | ConvertTo-Json -Depth 3 | Set-Content -Path $reportPath -Encoding ascii

if ($missing.Count -gt 0) {
  exit 1
}

exit 0

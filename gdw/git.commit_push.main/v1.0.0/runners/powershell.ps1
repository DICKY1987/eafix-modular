Param(
  [Parameter(Mandatory=$false)][switch]$DryRun = $true,
  [Parameter(Mandatory=$false)][string]$Spec = "",
  [Parameter(Mandatory=$false)][string]$InputsJson = "{}"
)
Write-Host "[GDW-PowerShell] Running git.commit_push.main DryRun=$DryRun Spec=$Spec Inputs=$InputsJson"
exit 0


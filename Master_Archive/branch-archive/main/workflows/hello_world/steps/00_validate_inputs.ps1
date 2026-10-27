Param(
  [string]$Name = 'World'
)

Write-Host "[hello_world] Validating inputs..."
if ([string]::IsNullOrWhiteSpace($Name)) {
  Write-Error "Name is required"
  exit 1
}
Write-Host "[hello_world] Name = $Name"
exit 0

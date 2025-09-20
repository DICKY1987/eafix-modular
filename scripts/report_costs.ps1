Param(
  [string]$OutDir = 'artifacts/cost',
  [string]$MetricsPath = 'artifacts/tokens.json',
  [double]$InputRatePer1k = 0.3,
  [double]$OutputRatePer1k = 0.6
)

$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Sum-Tokens($value) {
  if ($null -eq $value) { return 0 }
  if ($value -is [array]) {
    return ([int]((($value | ForEach-Object { [int]$_ }) | Measure-Object -Sum).Sum))
  }
  try { return [int]$value } catch { return 0 }
}

if (Test-Path $MetricsPath) {
  $metrics = Get-Content -Raw -Path $MetricsPath | ConvertFrom-Json
  $input_tokens = Sum-Tokens $metrics.input_tokens
  $output_tokens = Sum-Tokens $metrics.output_tokens
  $cache_read_input_tokens = Sum-Tokens $metrics.cache_read_input_tokens
  $cache_creation_input_tokens = Sum-Tokens $metrics.cache_creation_input_tokens
} else {
  $input_tokens = 0
  $output_tokens = 0
  $cache_read_input_tokens = 0
  $cache_creation_input_tokens = 0
}

$effective_input_tokens = $input_tokens + $cache_read_input_tokens + $cache_creation_input_tokens
$input_cost  = [Math]::Round(($effective_input_tokens / 1000.0) * $InputRatePer1k, 6)
$output_cost = [Math]::Round(($output_tokens / 1000.0) * $OutputRatePer1k, 6)
$total_cost  = [Math]::Round(($input_cost + $output_cost), 6)

$obj = [ordered]@{
  run_id = [guid]::NewGuid().ToString()
  timestamp = (Get-Date).ToString('o')
  input_tokens = $input_tokens
  output_tokens = $output_tokens
  cache_read_input_tokens = $cache_read_input_tokens
  cache_creation_input_tokens = $cache_creation_input_tokens
  effective_input_tokens = $effective_input_tokens
  input_rate_per_1k = $InputRatePer1k
  output_rate_per_1k = $OutputRatePer1k
  input_cost = $input_cost
  output_cost = $output_cost
  total_cost = $total_cost
}

$jsonPath = Join-Path $OutDir 'cost_report.json'
$csvPath  = Join-Path $OutDir 'cost_report.csv'

$obj | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 -Path $jsonPath
$obj | ConvertTo-Csv -NoTypeInformation | Set-Content -Encoding UTF8 -Path $csvPath

Write-Host "[cost] Wrote JSON: $jsonPath"
Write-Host "[cost] Wrote CSV : $csvPath"

exit 0

Param(
  [string]$Out = 'artifacts/tokens.json',
  [int]$InputTokens = 1200,
  [int]$OutputTokens = 400,
  [int]$CacheReadInputTokens = 200,
  [int]$CacheCreationInputTokens = 100
)

$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Out) | Out-Null

$obj = [ordered]@{
  input_tokens = @($InputTokens)
  output_tokens = @($OutputTokens)
  cache_read_input_tokens = @($CacheReadInputTokens)
  cache_creation_input_tokens = @($CacheCreationInputTokens)
}

$obj | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 -Path $Out
Write-Host "[tokens] Wrote metrics: $Out"
exit 0

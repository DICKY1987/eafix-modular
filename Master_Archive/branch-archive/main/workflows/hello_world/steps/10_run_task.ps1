$ErrorActionPreference = 'Stop'

New-Item -ItemType Directory -Force -Path 'artifacts/hello_world' | Out-Null
$out = "artifacts/hello_world/hello.txt"
"Hello from hello_world workflow at $(Get-Date -Format o)" | Set-Content -Encoding UTF8 $out
Write-Host "[hello_world] Wrote artifact: $out"
exit 0

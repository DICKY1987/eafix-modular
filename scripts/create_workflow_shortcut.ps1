$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$script = Join-Path $repo 'scripts/workflow_interface.ps1'
$args = "-NoExit -ExecutionPolicy Bypass -File `"$script`""
$sc = Join-Path $env:USERPROFILE 'Desktop/Workflow Interface.lnk'

$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut($sc)
$lnk.TargetPath = $ps
$lnk.Arguments = $args
$lnk.WorkingDirectory = $repo
$lnk.IconLocation = 'powershell.exe,0'
$lnk.Save()

Write-Host "Created shortcut: $sc"

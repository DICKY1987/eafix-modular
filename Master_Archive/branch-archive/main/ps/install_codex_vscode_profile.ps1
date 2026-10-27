Param(
    [ValidateSet('merge','copy')]
    [string]$Mode = 'merge',
    [switch]$Backup
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $repoRoot

$python = "$repoRoot\.venv\Scripts\python.exe"
$fallbackPython = 'python'
if (-not (Test-Path $python)) { $python = $fallbackPython }

$argsList = @('scripts/merge_vscode_configs.py', '--mode', $Mode)
if ($Backup) { $argsList += '--backup' }

& $python @argsList


Param(
    [Parameter(Mandatory=$false, ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path "$PSScriptRoot\..\").Path
$env:PYTHONPATH = Join-Path $repoRoot 'gui_terminal\src'
python -m gui_terminal.main @Args


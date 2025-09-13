# Launch Separate VS Code Instance with CLI Multi-Rapid Workflow System
# This script opens a new VS Code window with the workflow system pre-configured

param(
    [string]$WorkspaceFolder = $PSScriptRoot,
    [switch]$Debug,
    [switch]$DryRun
)

Write-Host "🚀 Launching CLI Multi-Rapid Workflow System..." -ForegroundColor Green
Write-Host "📁 Workspace: $WorkspaceFolder" -ForegroundColor Cyan

# Ensure we're in the correct directory
Set-Location $WorkspaceFolder

# Check if VS Code is available
if (-not (Get-Command "code" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ VS Code 'code' command not found in PATH" -ForegroundColor Red
    Write-Host "💡 Please ensure VS Code is installed and added to PATH" -ForegroundColor Yellow
    exit 1
}

# Launch VS Code with the workspace file
$workspaceFile = Join-Path $WorkspaceFolder "workflow-vscode.code-workspace"

$codeArgs = @(
    "--new-window",
    $workspaceFile
)

if ($Debug) {
    $codeArgs += "--verbose"
    Write-Host "🐛 Debug mode enabled" -ForegroundColor Magenta
}

Write-Host "🏁 Starting VS Code with workflow system..." -ForegroundColor Green

if ($DryRun) {
    Write-Host "🧪 DRY RUN - Would execute:" -ForegroundColor Yellow
    Write-Host "code $($codeArgs -join ' ')" -ForegroundColor White
    Write-Host "📋 Workspace file: $workspaceFile" -ForegroundColor Cyan
} else {
    # Launch VS Code with workspace
    Start-Process "code" -ArgumentList $codeArgs -NoNewWindow
    
    # Wait a moment then launch the CLI system in separate terminal
    Start-Sleep -Seconds 2
    
    Write-Host "✅ VS Code launched successfully!" -ForegroundColor Green
    Write-Host "🔧 Opening workflow terminal..." -ForegroundColor Cyan
    
    # Launch workflow terminal
    $terminalTitle = "CLI Multi-Rapid Workflow System"
    $terminalCmd = @"
title $terminalTitle && cd /d "$WorkspaceFolder" && echo 🚀 CLI Multi-Rapid Workflow System Ready! && echo. && echo Available Commands: && echo   • cli-multi-rapid phase stream list && echo   • cli-multi-rapid phase stream run stream-a --dry && echo   • cli-multi-rapid workflow-status && echo   • cli-multi-rapid compliance check && echo. && cli-multi-rapid --help
"@
    
    Start-Process "cmd" -ArgumentList "/k", $terminalCmd
}

Write-Host "🎉 Workflow system launch complete!" -ForegroundColor Green
Write-Host "📝 Quick Start Commands:" -ForegroundColor White
Write-Host "  • cli-multi-rapid phase stream list" -ForegroundColor Gray
Write-Host "  • cli-multi-rapid phase stream run stream-a --dry" -ForegroundColor Gray
Write-Host "  • cli-multi-rapid workflow-status" -ForegroundColor Gray
Write-Host "  • cli-multi-rapid compliance check" -ForegroundColor Gray
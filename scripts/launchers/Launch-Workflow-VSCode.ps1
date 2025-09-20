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

# Create a temporary workspace file for the workflow system
$workspaceConfig = @{
    folders = @(
        @{
            name = "CLI Multi-Rapid DEV"
            path = $WorkspaceFolder
        }
    )
    settings = @{
        "terminal.integrated.defaultProfile.windows" = "CLI Multi-Rapid"
        "workbench.startupEditor" = "none"
        "window.title" = "🚀 CLI Multi-Rapid Workflow System - $(Split-Path $WorkspaceFolder -Leaf)"
        "codex.workflowMode" = $true
        "codex.autoLaunch" = $true
    }
    extensions = @{
        recommendations = @(
            "ms-python.python",
            "ms-python.vscode-pylance", 
            "ms-vscode.powershell"
        )
    }
}

$workspaceFile = Join-Path $env:TEMP "cli-multi-rapid-workflow.code-workspace"
$workspaceConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $workspaceFile -Encoding UTF8

Write-Host "⚙️ Workspace configuration created: $workspaceFile" -ForegroundColor Yellow

# Launch VS Code with the workspace
$codeArgs = @(
    "--new-window"
    "--folder-uri", "file:///$($WorkspaceFolder -replace '\\', '/')"
)

if ($Debug) {
    $codeArgs += "--verbose"
    Write-Host "🐛 Debug mode enabled" -ForegroundColor Magenta
}

Write-Host "🏁 Starting VS Code with workflow system..." -ForegroundColor Green

if ($DryRun) {
    Write-Host "🧪 DRY RUN - Would execute:" -ForegroundColor Yellow
    Write-Host "code $($codeArgs -join ' ')" -ForegroundColor White
} else {
    # Launch VS Code
    Start-Process "code" -ArgumentList $codeArgs -NoNewWindow
    
    # Wait a moment then launch the CLI system
    Start-Sleep -Seconds 3
    
    Write-Host "✅ VS Code launched successfully!" -ForegroundColor Green
    Write-Host "🔧 Starting CLI Multi-Rapid system..." -ForegroundColor Cyan
    
    # Launch CLI system in new terminal
    $terminalCmd = "cli-multi-rapid --help"
    Start-Process "cmd" -ArgumentList "/k", "cd /d `"$WorkspaceFolder`" && echo 🚀 CLI Multi-Rapid System Ready! && echo Type: cli-multi-rapid --help to start && $terminalCmd"
}

Write-Host "🎉 Workflow system launch complete!" -ForegroundColor Green
Write-Host "📝 Available commands:" -ForegroundColor White
Write-Host "  • cli-multi-rapid phase stream list" -ForegroundColor Gray
Write-Host "  • cli-multi-rapid phase stream run stream-a --dry" -ForegroundColor Gray
Write-Host "  • cli-multi-rapid workflow-status" -ForegroundColor Gray
Write-Host "  • cli-multi-rapid compliance check" -ForegroundColor Gray
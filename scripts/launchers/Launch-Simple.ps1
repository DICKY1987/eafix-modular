# Simple VS Code Workflow Launcher
param(
    [switch]$DryRun
)

$workspaceFile = "workflow-vscode.code-workspace"

Write-Host "🚀 Launching CLI Multi-Rapid Workflow System..." -ForegroundColor Green

if ($DryRun) {
    Write-Host "🧪 DRY RUN - Would execute: code --new-window $workspaceFile" -ForegroundColor Yellow
} else {
    code --new-window $workspaceFile
    Write-Host "✅ VS Code workflow system launched!" -ForegroundColor Green
}

Write-Host "📝 Available commands in the new VS Code instance:" -ForegroundColor White
Write-Host "  • cli-multi-rapid phase stream list" -ForegroundColor Gray
Write-Host "  • cli-multi-rapid workflow-status" -ForegroundColor Gray
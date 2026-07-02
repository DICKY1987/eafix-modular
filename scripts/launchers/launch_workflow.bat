@echo off
echo 🚀 Launching CLI Multi-Rapid Workflow System...

REM Check if VS Code is available
where code >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ VS Code 'code' command not found in PATH
    echo 💡 Please ensure VS Code is installed and added to PATH
    pause
    exit /b 1
)

REM Launch VS Code with the workflow workspace
echo 🏁 Starting VS Code with workflow system...
code --new-window workflow-vscode.code-workspace

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Launch workflow terminal
echo ✅ VS Code launched successfully!
echo 🔧 Opening workflow terminal...
start "CLI Multi-Rapid Workflow" cmd /k "cd /d %~dp0 && echo 🚀 CLI Multi-Rapid Workflow System Ready! && echo. && echo Available Commands: && echo   • cli-multi-rapid phase stream list && echo   • cli-multi-rapid phase stream run stream-a --dry && echo   • cli-multi-rapid workflow-status && echo   • cli-multi-rapid compliance check && echo."

echo 🎉 Workflow system launch complete!
echo 📝 Quick Start Commands:
echo   • cli-multi-rapid phase stream list
echo   • cli-multi-rapid workflow-status
echo   • cli-multi-rapid compliance check
pause
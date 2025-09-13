# CLI Multi-Rapid System - Launch Menu
param()

Write-Host "================================" -ForegroundColor Green
Write-Host "  CLI Multi-Rapid System" -ForegroundColor Green  
Write-Host "  Enterprise Orchestration Platform" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host

# Change to correct directory
Set-Location "C:\Users\Richard Wilks\cli_multi_rapid_DEV"

Write-Host "Choose your interface:" -ForegroundColor Cyan
Write-Host "  1. Open in VS Code (Full IDE experience)" -ForegroundColor Yellow
Write-Host "  2. Command Line Interface (Terminal only)" -ForegroundColor Yellow
Write-Host "  3. Quick system test" -ForegroundColor Yellow
Write-Host "  4. Exit" -ForegroundColor Yellow
Write-Host

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" { 
        Write-Host "Opening VS Code with CLI Multi-Rapid integration..." -ForegroundColor Green
        Start-Process "code.exe" -ArgumentList "`"C:\Users\Richard Wilks\cli_multi_rapid_DEV`"" -NoNewWindow
        Write-Host "VS Code should open with:"
        Write-Host "  • All CLI Multi-Rapid tasks in Command Palette"
        Write-Host "  • Integrated terminal ready to use"
        Write-Host "  • Debug configurations available"
        Write-Host "  • Press Ctrl+Shift+P and type 'CLI Multi-Rapid'"
    }
    "2" { 
        Write-Host "Starting CLI interface..." -ForegroundColor Green
        Write-Host "Available commands:"
        Write-Host "  cli-multi-rapid --help"
        Write-Host "  cli-multi-rapid phase stream list"
        Write-Host "  cli-multi-rapid phase stream run stream-a --dry"
        Write-Host
        & powershell -NoExit -Command "Write-Host 'CLI Multi-Rapid System Ready!' -ForegroundColor Green"
    }
    "3" { 
        Write-Host "Running quick system test..." -ForegroundColor Green
        & cli-multi-rapid greet "System Test"
        Write-Host
        & cli-multi-rapid phase stream list
        Write-Host "Test completed! Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    "4" { 
        Write-Host "Goodbye!" -ForegroundColor Green
        exit
    }
    default { 
        Write-Host "Invalid choice. Opening VS Code by default..." -ForegroundColor Red
        Start-Process "code.exe" -ArgumentList "`"C:\Users\Richard Wilks\cli_multi_rapid_DEV`"" -NoNewWindow
    }
}
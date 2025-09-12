# CLI Multi-Rapid System Launcher
param()

Write-Host "================================" -ForegroundColor Green
Write-Host "  CLI Multi-Rapid System" -ForegroundColor Green  
Write-Host "  Enterprise Orchestration Platform" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host

# Change to correct directory
Set-Location "C:\Users\Richard Wilks\cli_multi_rapid_DEV"

# Test system
Write-Host "System Status:" -ForegroundColor Yellow
try {
    $result = & cli-multi-rapid phase stream list 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "System: READY" -ForegroundColor Green
        Write-Host "Streams: Available" -ForegroundColor Green
    } else {
        Write-Host "System: NOT READY" -ForegroundColor Red
        Write-Host "Please check installation" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host "System: ERROR" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host
Write-Host "Quick Commands:" -ForegroundColor Cyan
Write-Host "  cli-multi-rapid --help"
Write-Host "  cli-multi-rapid phase stream list"
Write-Host "  cli-multi-rapid phase stream run stream-a --dry"
Write-Host "  cli-multi-rapid workflow-status"
Write-Host

# Keep window open
Write-Host "System ready! Type commands above or press Ctrl+C to exit." -ForegroundColor Green
Write-Host

# Start interactive PowerShell session
& powershell -NoExit -Command "Write-Host 'CLI Multi-Rapid System Ready - Type cli-multi-rapid --help to start' -ForegroundColor Green"
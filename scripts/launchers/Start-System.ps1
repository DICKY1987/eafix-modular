#!/usr/bin/env pwsh

Write-Host "================================" -ForegroundColor Green
Write-Host "  CLI Multi-Rapid System" -ForegroundColor Green  
Write-Host "  Enterprise Orchestration Platform" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host

# Change to correct directory
Set-Location "C:\Users\Richard Wilks\cli_multi_rapid_DEV"

# Show system status
Write-Host "📊 System Status:" -ForegroundColor Yellow
try {
    $streams = & cli-multi-rapid phase stream list | ConvertFrom-Json
    Write-Host "✅ Workflow System: READY" -ForegroundColor Green
    Write-Host "✅ Available Streams: $($streams.Count)" -ForegroundColor Green
    Write-Host
} catch {
    Write-Host "❌ System not ready" -ForegroundColor Red
    exit 1
}

# Interactive menu
do {
    Write-Host "🎯 Quick Actions:" -ForegroundColor Cyan
    Write-Host "  1. Show all streams"
    Write-Host "  2. Run Foundation & Infrastructure (Stream A)"  
    Write-Host "  3. Run Schema & Validation (Stream B)"
    Write-Host "  4. System status"
    Write-Host "  5. Full help"
    Write-Host "  q. Quit"
    Write-Host

    $choice = Read-Host "Select option (1-5 or q)"

    switch ($choice) {
        "1" { 
            & cli-multi-rapid phase stream list
        }
        "2" { 
            Write-Host "🚀 Running Stream A (Foundation & Infrastructure)..." -ForegroundColor Yellow
            & cli-multi-rapid phase stream run stream-a --dry
        }
        "3" { 
            Write-Host "🚀 Running Stream B (Schema & Validation)..." -ForegroundColor Yellow
            & cli-multi-rapid phase stream run stream-b --dry
        }
        "4" { 
            & cli-multi-rapid workflow-status
        }
        "5" { 
            & cli-multi-rapid --help
        }
        "q" { 
            Write-Host "Goodbye! 👋" -ForegroundColor Green
            break
        }
        default { 
            Write-Host "Invalid choice. Please select 1-5 or q." -ForegroundColor Red
        }
    }
    Write-Host
} while ($choice -ne "q")
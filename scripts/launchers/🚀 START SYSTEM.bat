@echo off
title CLI Multi-Rapid System
color 0A
cd /d "C:\Users\Richard Wilks\cli_multi_rapid_DEV"

echo.
echo    ==========================================
echo    🚀 CLI Multi-Rapid Enterprise System 🚀
echo    ==========================================
echo.
echo    System starting...
echo.

timeout /t 2 /nobreak >nul

echo    ✅ System Ready!
echo.
echo    Try these commands:
echo    • cli-multi-rapid phase stream list
echo    • cli-multi-rapid phase stream run stream-a --dry  
echo    • cli-multi-rapid workflow-status
echo.

cmd /k "echo Type 'cli-multi-rapid --help' to see all commands && echo."
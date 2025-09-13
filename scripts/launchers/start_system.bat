@echo off
cd /d "C:\Users\Richard Wilks\cli_multi_rapid_DEV"
echo ================================
echo   CLI Multi-Rapid System Ready
echo ================================
echo.
echo Available commands:
echo   help           - Show all commands
echo   status         - System status
echo   streams        - List workflow streams
echo   run [stream]   - Execute workflow
echo   quit           - Exit system
echo.

:menu
set /p choice="Enter command (or 'help'): "

if /i "%choice%"=="help" (
    cli-multi-rapid --help
    goto menu
)
if /i "%choice%"=="status" (
    cli-multi-rapid workflow-status
    goto menu
)
if /i "%choice%"=="streams" (
    cli-multi-rapid phase stream list
    goto menu
)
if /i "%choice%"=="quit" (
    echo Goodbye!
    exit /b
)
if /i "%choice%"=="run stream-a" (
    cli-multi-rapid phase stream run stream-a --dry
    goto menu
)
if /i "%choice%"=="run stream-b" (
    cli-multi-rapid phase stream run stream-b --dry
    goto menu
)

echo Unknown command. Type 'help' for available commands.
goto menu
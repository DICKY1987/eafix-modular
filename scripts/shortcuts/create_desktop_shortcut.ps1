#!/usr/bin/env pwsh

# Create desktop shortcut for CLI Multi-Rapid System
$WshShell = New-Object -comObject WScript.Shell
$Desktop = $WshShell.SpecialFolders("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\CLI Multi-Rapid System.lnk")

# Shortcut properties
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"C:\Users\Richard Wilks\cli_multi_rapid_DEV\Start-System.ps1`""
$Shortcut.WorkingDirectory = "C:\Users\Richard Wilks\cli_multi_rapid_DEV"
$Shortcut.WindowStyle = 1
$Shortcut.Description = "CLI Multi-Rapid Enterprise Orchestration System"
$Shortcut.IconLocation = "powershell.exe,0"

# Save the shortcut
$Shortcut.Save()

Write-Host "Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host "Look for 'CLI Multi-Rapid System' on your desktop" -ForegroundColor Yellow
Write-Host "Double-click it to start the system with interactive menu" -ForegroundColor Cyan
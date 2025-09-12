# Create VS Code desktop shortcut for CLI Multi-Rapid System
$WshShell = New-Object -comObject WScript.Shell
$Desktop = $WshShell.SpecialFolders("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\🚀 CLI Multi-Rapid VS Code.lnk")

# VS Code shortcut properties
$Shortcut.TargetPath = "code.exe"
$Shortcut.Arguments = "`"C:\Users\Richard Wilks\cli_multi_rapid_DEV`" --new-window"
$Shortcut.WorkingDirectory = "C:\Users\Richard Wilks\cli_multi_rapid_DEV"
$Shortcut.WindowStyle = 1
$Shortcut.Description = "CLI Multi-Rapid System in VS Code"
$Shortcut.IconLocation = "code.exe,0"

# Save the shortcut
$Shortcut.Save()

Write-Host "VS Code shortcut created successfully!" -ForegroundColor Green
Write-Host "Desktop shortcut: 🚀 CLI Multi-Rapid VS Code" -ForegroundColor Yellow
Write-Host "This will open the project in VS Code with all integrated features" -ForegroundColor Cyan
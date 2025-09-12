# Create single unified desktop shortcut
$WshShell = New-Object -comObject WScript.Shell
$Desktop = $WshShell.SpecialFolders("Desktop")

# Remove any existing CLI Multi-Rapid shortcuts
Get-ChildItem $Desktop | Where-Object {$_.Name -like "*CLI*" -or $_.Name -like "*Multi*"} | Remove-Item -Force -ErrorAction SilentlyContinue

# Create the single unified shortcut
$Shortcut = $WshShell.CreateShortcut("$Desktop\CLI Multi-Rapid System.lnk")
$Shortcut.TargetPath = "code.exe"
$Shortcut.Arguments = "`"C:\Users\Richard Wilks\cli_multi_rapid_DEV`""
$Shortcut.WorkingDirectory = "C:\Users\Richard Wilks\cli_multi_rapid_DEV"
$Shortcut.WindowStyle = 1
$Shortcut.Description = "CLI Multi-Rapid Enterprise Orchestration Platform"
$Shortcut.Save()

Write-Host "Created single desktop shortcut: CLI Multi-Rapid System" -ForegroundColor Green
Write-Host "Double-click to open the full program in VS Code" -ForegroundColor Yellow  
Write-Host "Access all features via Ctrl+Shift+P -> CLI Multi-Rapid" -ForegroundColor Cyan
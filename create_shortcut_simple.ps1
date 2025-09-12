# Create simple desktop shortcut
$WshShell = New-Object -comObject WScript.Shell
$Desktop = $WshShell.SpecialFolders("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\CLI Multi-Rapid System.lnk")

$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"C:\Users\Richard Wilks\cli_multi_rapid_DEV\Launch-System.ps1`""
$Shortcut.WorkingDirectory = "C:\Users\Richard Wilks\cli_multi_rapid_DEV"
$Shortcut.WindowStyle = 1
$Shortcut.Description = "CLI Multi-Rapid Enterprise System"

$Shortcut.Save()

Write-Host "Desktop shortcut updated successfully!" -ForegroundColor Green
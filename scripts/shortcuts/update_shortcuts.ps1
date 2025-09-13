# Update desktop shortcuts to launch VS Code interface
$WshShell = New-Object -comObject WScript.Shell
$Desktop = $WshShell.SpecialFolders("Desktop")

# Update the PowerShell shortcut to use the menu
$Shortcut = $WshShell.CreateShortcut("$Desktop\CLI Multi-Rapid System.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"C:\Users\Richard Wilks\cli_multi_rapid_DEV\Launch-Menu.ps1`""
$Shortcut.WorkingDirectory = "C:\Users\Richard Wilks\cli_multi_rapid_DEV"
$Shortcut.WindowStyle = 1
$Shortcut.Description = "CLI Multi-Rapid Enterprise System - Choose Interface"
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()

Write-Host "Updated PowerShell shortcut to show interface menu" -ForegroundColor Green

# Create a direct VS Code shortcut  
$VSCodeShortcut = $WshShell.CreateShortcut("$Desktop\🚀 CLI Multi-Rapid VS Code.lnk")
$VSCodeShortcut.TargetPath = "code.exe"
$VSCodeShortcut.Arguments = "`"C:\Users\Richard Wilks\cli_multi_rapid_DEV`""
$VSCodeShortcut.WorkingDirectory = "C:\Users\Richard Wilks\cli_multi_rapid_DEV"
$VSCodeShortcut.WindowStyle = 1
$VSCodeShortcut.Description = "CLI Multi-Rapid System - Direct VS Code Launch"
$VSCodeShortcut.Save()

Write-Host "Created direct VS Code shortcut" -ForegroundColor Green
Write-Host
Write-Host "Desktop shortcuts updated:" -ForegroundColor Yellow
Write-Host "  • CLI Multi-Rapid System.lnk - Shows menu to choose interface"
Write-Host "  • 🚀 CLI Multi-Rapid VS Code.lnk - Opens directly in VS Code"
Write-Host "  • 🚀 CLI Multi-Rapid System.bat - Terminal only (unchanged)"
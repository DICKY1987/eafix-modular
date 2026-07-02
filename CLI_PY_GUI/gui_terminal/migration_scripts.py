#!/usr/bin/env python3
"""
Migration scripts to replace VS Code interface with Python GUI
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Any


class VSCodeMigrator:
    """Migrate VS Code configuration to Python GUI"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.vscode_dir = self.project_root / ".vscode"
        self.backup_dir = self.project_root / ".vscode_backup"
        
    def analyze_current_config(self) -> Dict[str, Any]:
        """Analyze current VS Code configuration"""
        config_analysis = {
            "tasks": [],
            "debug_configs": [],
            "settings": {},
            "extensions": []
        }
        
        # Analyze tasks.json
        tasks_file = self.vscode_dir / "tasks.json"
        if tasks_file.exists():
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
                config_analysis["tasks"] = tasks_data.get("tasks", [])
                
        # Analyze launch.json
        launch_file = self.vscode_dir / "launch.json"
        if launch_file.exists():
            with open(launch_file, 'r', encoding='utf-8') as f:
                launch_data = json.load(f)
                config_analysis["debug_configs"] = launch_data.get("configurations", [])
                
        # Analyze settings.json
        settings_file = self.vscode_dir / "settings.json"
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                config_analysis["settings"] = json.load(f)
                
        # Analyze extensions.json
        extensions_file = self.vscode_dir / "extensions.json"
        if extensions_file.exists():
            with open(extensions_file, 'r', encoding='utf-8') as f:
                extensions_data = json.load(f)
                config_analysis["extensions"] = extensions_data.get("recommendations", [])
                
        return config_analysis
    
    def extract_commands_from_tasks(self, tasks: List[Dict]) -> Dict[str, List[tuple]]:
        """Extract commands from VS Code tasks and categorize them"""
        categories = {
            "CLI Platform": [],
            "Development": [],
            "Workflows": [],
            "Git & Monitoring": [],
            "Testing": [],
            "Other": []
        }
        
        for task in tasks:
            label = task.get("label", "Unknown")
            command = task.get("command", "")
            
            # Add arguments if present
            if "args" in task:
                if isinstance(task["args"], list):
                    command += " " + " ".join(task["args"])
                    
            # Categorize based on label content
            if any(keyword in label.lower() for keyword in ["cli", "multi-rapid", "workflow", "compliance"]):
                categories["CLI Platform"].append((label, command))
            elif any(keyword in label.lower() for keyword in ["test", "pytest"]):
                categories["Testing"].append((label, command))
            elif any(keyword in label.lower() for keyword in ["lint", "format", "security", "install", "setup"]):
                categories["Development"].append((label, command))
            elif any(keyword in label.lower() for keyword in ["git", "monitor", "health"]):
                categories["Git & Monitoring"].append((label, command))
            elif any(keyword in label.lower() for keyword in ["phase", "stream", "orchestrator"]):
                categories["Workflows"].append((label, command))
            else:
                categories["Other"].append((label, command))
                
        return categories
    
    def create_gui_config(self, commands: Dict[str, List[tuple]]) -> str:
        """Generate Python GUI configuration code"""
        config_code = '''"""
Generated GUI configuration from VS Code tasks
"""

GUI_COMMAND_CATEGORIES = {
'''
        
        for category, task_list in commands.items():
            if not task_list:
                continue
                
            config_code += f'    "{category}": [\n'
            for label, command in task_list:
                # Clean up label for GUI display
                clean_label = label.replace("CLI: ", "").replace("Workflow: ", "").replace("Test: ", "")
                config_code += f'        ("{clean_label}", "{command}"),\n'
            config_code += '    ],\n'
            
        config_code += '}\n'
        
        return config_code
    
    def backup_vscode_config(self):
        """Backup current VS Code configuration"""
        if self.vscode_dir.exists():
            print(f"📋 Backing up VS Code configuration to {self.backup_dir}")
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            shutil.copytree(self.vscode_dir, self.backup_dir)
            print("✅ Backup completed")
        else:
            print("⚠️ No VS Code configuration found")
    
    def create_launch_script(self):
        """Create new launch script for GUI"""
        launch_script = '''#!/usr/bin/env python3
"""
CLI Multi-Rapid GUI Launcher
Replaces VS Code interface launcher
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 50)
    print("  CLI Multi-Rapid Enterprise System")
    print("  Choose Interface:")
    print("=" * 50)
    print()
    print("1. Python GUI Terminal (Recommended)")
    print("2. Command Line Only")
    print("3. Restore VS Code Interface")
    print("4. Exit")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        print("🚀 Starting Python GUI Terminal...")
        try:
            subprocess.run([sys.executable, "gui/cli_terminal_gui.py"])
        except FileNotFoundError:
            print("❌ GUI not found. Run: python gui/cli_terminal_gui.py")
            
    elif choice == "2":
        print("🖥️ Opening command line interface...")
        subprocess.run([sys.executable, "-m", "src.cli_multi_rapid.cli", "--help"])
        input("Press Enter to continue...")
        
    elif choice == "3":
        print("📝 Restoring VS Code interface...")
        restore_vscode_config()
        
    elif choice == "4":
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice")

def restore_vscode_config():
    """Restore VS Code configuration from backup"""
    backup_dir = Path(".vscode_backup")
    vscode_dir = Path(".vscode")
    
    if backup_dir.exists():
        if vscode_dir.exists():
            shutil.rmtree(vscode_dir)
        shutil.copytree(backup_dir, vscode_dir)
        print("✅ VS Code configuration restored")
        print("💡 Run 'code .' to open in VS Code")
    else:
        print("❌ No VS Code backup found")

if __name__ == "__main__":
    main()
'''
        
        launch_file = self.project_root / "launch_interface.py"
        with open(launch_file, 'w', encoding='utf-8') as f:
            f.write(launch_script)
            
        print(f"✅ Created launch script: {launch_file}")
    
    def update_powershell_launcher(self):
        """Update PowerShell launcher to use GUI"""
        ps_script = '''# CLI Multi-Rapid System - Updated Launch Menu
param()

Write-Host "================================" -ForegroundColor Green
Write-Host "  CLI Multi-Rapid System" -ForegroundColor Green  
Write-Host "  Enterprise Orchestration Platform" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host

# Change to correct directory
Set-Location "C:\\Users\\Richard Wilks\\cli_multi_rapid_DEV"

Write-Host "Choose your interface:" -ForegroundColor Cyan
Write-Host "  1. Python GUI Terminal (New - Recommended)" -ForegroundColor Yellow
Write-Host "  2. Command Line Interface (Terminal only)" -ForegroundColor Yellow
Write-Host "  3. Restore VS Code Interface" -ForegroundColor Yellow
Write-Host "  4. Quick system test" -ForegroundColor Yellow
Write-Host "  5. Exit" -ForegroundColor Yellow
Write-Host

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" { 
        Write-Host "🚀 Starting Python GUI Terminal..." -ForegroundColor Green
        python gui/cli_terminal_gui.py
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
        Write-Host "📝 Restoring VS Code interface..." -ForegroundColor Green
        python scripts/restore_vscode.py
        Write-Host "💡 Run 'code .' to open in VS Code" -ForegroundColor Cyan
    }
    "4" { 
        Write-Host "Running quick system test..." -ForegroundColor Green
        & cli-multi-rapid greet "System Test"
        Write-Host
        & cli-multi-rapid phase stream list
        Write-Host "Test completed! Press any key to exit..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    "5" { 
        Write-Host "Goodbye!" -ForegroundColor Green
        exit
    }
    default { 
        Write-Host "Invalid choice. Starting GUI by default..." -ForegroundColor Red
        python gui/cli_terminal_gui.py
    }
}
'''
        
        ps_file = self.project_root / "Launch-Menu.ps1"
        with open(ps_file, 'w', encoding='utf-8') as f:
            f.write(ps_script)
            
        print(f"✅ Updated PowerShell launcher: {ps_file}")
    
    def migrate_to_gui(self):
        """Complete migration from VS Code to GUI"""
        print("🚀 Starting migration from VS Code to Python GUI...")
        print()
        
        # Step 1: Analyze current config
        print("📋 Analyzing VS Code configuration...")
        config = self.analyze_current_config()
        print(f"   Found {len(config['tasks'])} tasks")
        print(f"   Found {len(config['debug_configs'])} debug configurations")
        print(f"   Found {len(config['extensions'])} recommended extensions")
        
        # Step 2: Extract commands
        print("📊 Extracting commands from tasks...")
        commands = self.extract_commands_from_tasks(config['tasks'])
        for category, task_list in commands.items():
            if task_list:
                print(f"   {category}: {len(task_list)} commands")
        
        # Step 3: Backup VS Code config
        self.backup_vscode_config()
        
        # Step 4: Create GUI directory structure
        print("📁 Creating GUI directory structure...")
        gui_dir = self.project_root / "gui"
        gui_dir.mkdir(exist_ok=True)
        
        # Step 5: Generate GUI config
        print("⚙️ Generating GUI configuration...")
        gui_config = self.create_gui_config(commands)
        config_file = gui_dir / "gui_config.py"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(gui_config)
        print(f"   Created: {config_file}")
        
        # Step 6: Create launch scripts
        print("📜 Creating launch scripts...")
        self.create_launch_script()
        self.update_powershell_launcher()
        
        # Step 7: Create requirements file for GUI
        print("📦 Creating GUI requirements...")
        requirements = """# GUI Terminal Requirements
PyQt6>=6.4.0
asyncio
pathlib
"""
        req_file = gui_dir / "requirements.txt"
        with open(req_file, 'w') as f:
            f.write(requirements)
        print(f"   Created: {req_file}")
        
        # Step 8: Disable VS Code (optional)
        print("🔧 Preparing VS Code transition...")
        self.create_vscode_transition_notice()
        
        print()
        print("✅ Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Install GUI requirements: pip install -r gui/requirements.txt")
        print("2. Test GUI: python gui/cli_terminal_gui.py")
        print("3. Update shortcuts to use new launcher")
        print("4. If needed, restore VS Code: python scripts/restore_vscode.py")
        
    def create_vscode_transition_notice(self):
        """Create a notice in VS Code directory"""
        notice = """# VS Code Configuration - MIGRATED TO GUI

This project has been migrated from VS Code interface to a dedicated Python GUI terminal.

## What happened:
- Your VS Code configuration has been backed up to `.vscode_backup/`
- A new Python GUI terminal interface has been created
- All VS Code tasks are now available as GUI buttons

## To use the new interface:
```bash
python gui/cli_terminal_gui.py
```

## To restore VS Code interface:
```bash
python scripts/restore_vscode.py
```

## Your backed up VS Code files:
- `.vscode_backup/tasks.json` - All your tasks
- `.vscode_backup/launch.json` - Debug configurations  
- `.vscode_backup/settings.json` - IDE settings
- `.vscode_backup/extensions.json` - Recommended extensions

The GUI interface provides the same functionality with better terminal integration.
"""
        
        readme_file = self.vscode_dir / "README_MIGRATION.md"
        readme_file.parent.mkdir(exist_ok=True)
        with open(readme_file, 'w') as f:
            f.write(notice)


def create_restore_script():
    """Create script to restore VS Code configuration"""
    restore_script = '''#!/usr/bin/env python3
"""
Restore VS Code configuration from backup
"""

import shutil
from pathlib import Path

def main():
    project_root = Path(".")
    vscode_dir = project_root / ".vscode"
    backup_dir = project_root / ".vscode_backup"
    
    if not backup_dir.exists():
        print("❌ No VS Code backup found")
        print("💡 The backup should be in .vscode_backup/")
        return
    
    print("🔄 Restoring VS Code configuration...")
    
    # Remove current .vscode if it exists
    if vscode_dir.exists():
        shutil.rmtree(vscode_dir)
        
    # Restore from backup
    shutil.copytree(backup_dir, vscode_dir)
    
    print("✅ VS Code configuration restored!")
    print("📁 Files restored:")
    for file in vscode_dir.rglob("*"):
        if file.is_file():
            print(f"   {file}")
            
    print()
    print("💡 You can now use:")
    print("   code .    # Open in VS Code")
    print("   F1 > Tasks: Run Task    # Access all original tasks")

if __name__ == "__main__":
    main()
'''
    
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    restore_file = scripts_dir / "restore_vscode.py"
    with open(restore_file, 'w') as f:
        f.write(restore_script)
        
    print(f"✅ Created restore script: {restore_file}")


def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate VS Code to Python GUI")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without doing it")
    
    args = parser.parse_args()
    
    migrator = VSCodeMigrator(args.project_root)
    
    if args.dry_run:
        print("🔍 DRY RUN - Analyzing what would be migrated:")
        config = migrator.analyze_current_config()
        commands = migrator.extract_commands_from_tasks(config['tasks'])
        
        print(f"📋 Found {len(config['tasks'])} VS Code tasks")
        print(f"🔧 Found {len(config['debug_configs'])} debug configurations")
        print(f"🔌 Found {len(config['extensions'])} extension recommendations")
        print()
        print("📊 Command categories that would be created:")
        for category, task_list in commands.items():
            if task_list:
                print(f"   {category}: {len(task_list)} commands")
                for label, command in task_list[:3]:  # Show first 3
                    print(f"      - {label}")
                if len(task_list) > 3:
                    print(f"      ... and {len(task_list) - 3} more")
        print()
        print("Run without --dry-run to perform the migration")
    else:
        migrator.migrate_to_gui()
        create_restore_script()


if __name__ == "__main__":
    main()

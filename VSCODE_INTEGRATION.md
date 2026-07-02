# VS Code Integration Guide

## 🚀 CLI Multi-Rapid System in VS Code

This guide shows you all the ways to use the CLI Multi-Rapid Enterprise System directly within VS Code.

## 🎯 Quick Start Options

### 1. Command Palette (Easiest)
Press `Ctrl+Shift+P` and type "CLI Multi-Rapid" to see all available commands:
- 🚀 **Launch CLI Multi-Rapid System** - Opens help and system overview
- 📋 **List Workflow Streams** - Shows all 5 available streams (A-E) 
- 🏗️ **Run Stream A (Foundation)** - Executes foundation workflow
- 📊 **Show System Status** - Displays system health and metrics
- 🎯 **Quick Test** - Tests basic system functionality
- 💻 **Open CLI Multi-Rapid Terminal** - Opens terminal ready to use

### 2. Tasks Menu (Most Features)
Press `Ctrl+Shift+P` → "Tasks: Run Task" to access:
- **🚀 CLI: System Help** - Complete command reference
- **📋 CLI: List All Streams** - Stream details with phases
- **🏗️ CLI: Run Stream A (Foundation)** - Foundation & Infrastructure stream
- **📊 CLI: System Status** - Comprehensive status report
- **✅ CLI: Compliance Check** - System compliance validation
- **🎯 CLI: Quick Test** - Basic functionality test

### 3. Debug Configuration (Advanced)
Press `F5` or go to "Run and Debug" panel:
- **🚀 CLI Multi-Rapid: System Help** - Launch with debugging
- **📋 CLI Multi-Rapid: List Streams** - Debug stream listing
- **🏗️ CLI Multi-Rapid: Run Stream A** - Debug stream execution
- **🎯 CLI Multi-Rapid: Quick Test** - Debug basic commands

### 4. Integrated Terminal
Choose "CLI Multi-Rapid" terminal profile:
- Terminal automatically navigates to correct directory
- Shows welcome message with ready-to-use commands
- Pre-configured with proper environment

## 🎨 Visual Integration

### Status Bar
Look at the bottom of VS Code:
- **🚀 Codex Implementation Active** - Shows current implementation status
- **99% Target** - Platform completion progress

### Title Bar
VS Code window title shows: `"Repository — 🚀 Codex Implementation Active — 99% Target"`

### Color Theme
- Green status bar indicates system is ready
- Custom colors highlight the active enterprise system

## 📝 Available Commands

### Basic Commands
```bash
cli-multi-rapid --help              # System overview
cli-multi-rapid greet "Developer"   # Test basic functionality
```

### Workflow Operations  
```bash
cli-multi-rapid phase stream list           # List all 5 streams
cli-multi-rapid phase stream run stream-a --dry   # Run Foundation stream
cli-multi-rapid phase run phase0 --dry     # Run specific phase
```

### System Status
```bash
cli-multi-rapid workflow-status     # Detailed status report
cli-multi-rapid compliance check    # Compliance validation
```

## 🔧 Configuration Features

### Python Integration
- **Auto-formatting** with Black on save
- **Import organization** with isort
- **Type checking** with mypy
- **Linting** with ruff and flake8

### File Associations
- `.mqh` and `.mq4` files → C language support
- `.ps1` files → PowerShell syntax highlighting

### Testing Integration
- **pytest** configured for the test suite
- **Coverage** reporting enabled
- **Test discovery** on file save

## 🚦 Status Indicators

### Green Status Bar = System Ready
- All dependencies installed
- CLI system operational
- Workflows available

### Enterprise Features Active
- **Codex Implementation** running (Phase 1)
- **Recovery System** enabled
- **Self-Healing Services** operational
- **Cross-Language Bridge** active

## 💡 Pro Tips

1. **Quick Access**: Add tasks to keybindings for instant access
2. **Terminal Profile**: Use "CLI Multi-Rapid" terminal for best experience  
3. **Command Palette**: Type "CLI" to quickly find all system commands
4. **Debug Mode**: Use F5 to debug any CLI operation
5. **Status Monitoring**: Watch status bar for system health

## 🔍 Troubleshooting

### If Commands Don't Work
1. Open "CLI Multi-Rapid" terminal profile
2. Check that you see "🚀 CLI Multi-Rapid System Ready!"
3. Try `cli-multi-rapid --help` to verify installation

### If Terminal Doesn't Open Correctly  
1. Use Command Palette → "Terminal: Select Default Profile"
2. Choose "CLI Multi-Rapid" 
3. Open new terminal with `Ctrl+Shift+``

### If Tasks Fail
1. Check VS Code is opened in the `cli_multi_rapid_DEV` directory
2. Verify Python interpreter is set correctly
3. Try running the command manually in terminal first

## 🎉 You're All Set!

The CLI Multi-Rapid Enterprise System is now fully integrated into your VS Code environment. Use any of the methods above to interact with the 98% complete enterprise orchestration platform!

**Most Popular Starting Points:**
1. `Ctrl+Shift+P` → "CLI Multi-Rapid: Launch"
2. `Ctrl+Shift+P` → "Tasks: Run Task" → "🚀 CLI: System Help"
3. Open "CLI Multi-Rapid" terminal and type `cli-multi-rapid --help`
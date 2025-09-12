# VS Code Setup - CLI Multi-Rapid Enterprise Platform

## ✅ Current Status: FULLY CONFIGURED

Your development environment for the CLI Multi-Rapid Enterprise Orchestration Platform is **fully configured and ready for development**.

## 📋 **Installed CLI Tools & Configuration**

### **Core Development Tools** ✅
- **Python 3.11.9** - Main development language
- **Git 2.47.1** - Version control
- **Pip 25.2** - Package manager (upgraded)

### **Python Development Tools** ✅
- **Black 25.1.0** - Code formatter
- **isort 6.0.1** - Import sorter  
- **MyPy** - Type checker
- **Flake8 7.3.0** - Linter
- **Ruff** - Fast linter
- **Bandit** - Security linter
- **Nox 2025.5.1** - Testing automation
- **Pytest 8.4.1** - Testing framework
- **pytest-cov 6.2.1** - Coverage reporting
- **Rich 14.1.0** - Terminal formatting

### **VS Code Configuration Files** ✅

#### `.vscode/settings.json`
- **Python interpreter**: `./venv/Scripts/python.exe`
- **Formatting**: Black with line length 88
- **Linting**: Flake8, MyPy, Bandit enabled
- **Testing**: Pytest configuration
- **Auto-formatting**: On save and paste
- **File exclusions**: `__pycache__`, `.pytest_cache`, etc.

#### `.vscode/extensions.json`
Recommended extensions for optimal development:
- `ms-python.python` - Python support
- `ms-python.black-formatter` - Code formatting
- `charliermarsh.ruff` - Fast linting
- `ryanluker.vscode-coverage-gutters` - Coverage display
- `eamodio.gitlens` - Git integration
- Plus 15+ additional productivity extensions

#### `.vscode/tasks.json`
**22+ VS Code tasks** available via `Ctrl+Shift+P > Tasks: Run Task`:

**CLI Multi-Rapid Platform Tasks:**
- `CLI: Test Enhanced Commands`
- `CLI: Workflow Status`
- `CLI: Compliance Report`
- `Workflow: Execute Phase`
- `Roadmap: Implementation Status`
- `Bridge: Test Cross-Language System`
- `Validation: Final Production Launch`

**Development Tasks:**
- `Setup: Install Requirements`
- `Setup: Install Dev Tools`
- `Test: Run All Tests`
- `Lint: Format Code`
- `Security: Run Security Scan`

#### `.vscode/launch.json`
**12+ debug configurations** available via `F5`:
- CLI Multi-Rapid commands with different arguments
- Workflow orchestrator debugging
- Cross-language bridge testing
- Pytest test debugging
- FastAPI server debugging

## 🚀 **Getting Started in VS Code**

### **1. Open Project**
```bash
cd "C:\Users\Richard Wilks\cli_multi_rapid_DEV"
code .
```

### **2. Install Recommended Extensions**
VS Code will prompt to install recommended extensions from `.vscode/extensions.json`

### **3. Available Commands in VS Code**

#### **Via Command Palette** (`Ctrl+Shift+P`)
- `Tasks: Run Task` - Access all 22+ development tasks
- `Python: Select Interpreter` - Choose Python interpreter
- `Python: Run Python File in Terminal` - Run current file

#### **Via Debug Panel** (`F5` or `Ctrl+Shift+D`)
- Select any of 12+ debug configurations
- Set breakpoints and debug CLI commands
- Debug workflow orchestration and cross-language bridge

### **4. Essential VS Code Tasks for CLI Multi-Rapid**

#### **Test the Platform** 
- `CLI: Test Enhanced Commands` - Verify CLI functionality
- `CLI: Workflow Status` - Check workflow orchestration 
- `Bridge: Test Cross-Language System` - Test Python↔MQL4↔PowerShell bridge

#### **Development Workflow**
- `Lint: Format Code` - Format with Black + isort
- `Test: Run All Tests` - Execute full test suite with coverage
- `Security: Run Security Scan` - Run Bandit security checks

#### **Platform Management**
- `Workflow: Execute Phase` - Run specific workflow phases
- `Roadmap: Implementation Status` - Check 98% completion status
- `Validation: Final Production Launch` - Production deployment validation

## 🎯 **Enterprise Platform Features Available**

### **Enhanced CLI Integration** ✅
```bash
# Available via VS Code tasks or terminal:
python -m src.cli_multi_rapid.cli --help
python -m src.cli_multi_rapid.cli workflow-status  
python -m src.cli_multi_rapid.cli compliance report
```

### **Cross-Language Bridge System** ✅  
```bash
# Test full bridge system:
python test_cross_language_bridge.py

# Components: Python↔MQL4↔PowerShell communication
# - Unified configuration management
# - Cross-system health checking
# - Standardized error handling
```

### **Workflow Orchestration** ✅
```bash
# 13-phase implementation framework:
python -m workflows.orchestrator status
python -m workflows.execution_roadmap status  # 98% complete!

# Execute specific phases:
python -m workflows.orchestrator run-phase phase1
```

## 📊 **Development Environment Status**

| Component | Status | Configuration |
|-----------|--------|---------------|
| **VS Code Settings** | ✅ **Configured** | Auto-format, linting, testing |
| **Extensions** | ✅ **Recommended** | 15+ productivity extensions |
| **Tasks** | ✅ **22+ Available** | CLI, workflow, testing tasks |
| **Debug Configs** | ✅ **12+ Available** | All platform components |
| **CLI Tools** | ✅ **Installed** | Black, MyPy, Pytest, Nox, etc. |
| **Platform** | ✅ **98% Complete** | Production ready |

## 🎉 **Ready for Development!**

Your CLI Multi-Rapid Enterprise Orchestration Platform development environment is **fully configured** and **production ready**.

**Next steps:**
1. **Open VS Code**: `code .` in the project directory
2. **Install extensions** when prompted
3. **Start developing** with full enterprise capabilities
4. **Use tasks and debugging** for optimal workflow

**The 98% complete enterprise platform is at your fingertips!** 🚀
## Codex VS Code Config Package

- Source: `CODEX_IMPLEMENTATION/vscode_configuration/` (specialized tasks and debug configs)
- Default `.vscode/` remains the primary, stable profile for this repo.

Install or merge Codex configs into `.vscode` with backup:

- Windows (PowerShell): `./ps/install_codex_vscode_profile.ps1 -Mode merge -Backup`
- macOS/Linux: `bash scripts/install_codex_vscode_profile.sh --mode merge --backup`

Notes:
- Merge keeps existing `.vscode` entries and adds non-duplicates by label/name.
- Use `-Mode copy` to overwrite `.vscode` with Codex files (not recommended).
- Backups are created as `.vscode.backup-YYYYMMDD-HHMMSS/` when `-Backup`/`--backup` is used.

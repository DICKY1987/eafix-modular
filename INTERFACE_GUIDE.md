# Interface Selection Guide

This repository now supports **dual interface options** with **Python GUI as the primary interface**.

## Quick Start - Python GUI (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Launch Python GUI Terminal
cli-multi-rapid gui

# If PyQt6 not installed, runs in headless mode automatically
```

## Interface Options

### 🎯 **Primary: Python GUI Terminal**
- **Branch**: `main` (current)
- **Location**: `gui_terminal/` directory
- **Technology**: PyQt6-based GUI with headless fallback
- **Launch**: `cli-multi-rapid gui`
- **Features**:
  - Real-time terminal widget with PTY/ConPTY backend
  - Cost integration and budget tracking
  - Security policy enforcement
  - Plugin system for extensions
  - Cross-platform (Windows/Linux/macOS)
  - Graceful degradation to headless mode

### 🔧 **Alternative: VS Code Extension**
- **Branch**: `interface/vscode-only`
- **Location**: `vscode-extension/` directory
- **Technology**: TypeScript-based VS Code extension
- **Switch**: `git checkout interface/vscode-only`
- **Features**:
  - Real-time workflow cockpit WebView
  - Command palette integration
  - WebSocket-based live updates
  - Built-in extension package ready for installation

## Branch Structure

```
main (Python GUI + GDW Framework)
├── gui_terminal/                    # Python GUI components
├── vscode-extension/                # VS Code extension (also available here)
├── gdw/                            # Generic Deterministic Workflows
└── [complete enterprise framework]

interface/vscode-only (VS Code Extension Only)
├── vscode-extension/                # VS Code extension components
├── gdw/                            # Generic Deterministic Workflows
└── [enterprise framework without Python GUI]

Backup Branches:
├── backup-gdw-vscode-20240914      # GDW + VS Code backup
└── backup-vscode-interface-20240914 # VS Code interface backup
```

## New Capabilities (Main Branch)

### Generic Deterministic Workflows (GDW)
```bash
cli-multi-rapid gdw list              # List available workflows
cli-multi-rapid gdw run <workflow>    # Execute workflow
cli-multi-rapid gdw validate <spec>   # Validate workflow spec
cli-multi-rapid gdw chain <chain>     # Execute workflow chains
```

### Pre-built Workflows
- `git.commit_push.main` - Git operations with multi-runner support
- `k8s.deploy.rolling` - Kubernetes deployment with rollout monitoring
- `security.scan.trivy` - Container security scanning
- `version.bump.semver` - Semantic version management
- `build.container.sign` - Container building and signing

## Switching Between Interfaces

### To VS Code Extension
```bash
git stash  # Save any changes
git checkout interface/vscode-only
code --install-extension vscode-extension/cli-multi-rapid-cockpit-0.1.0.vsix
```

### Back to Python GUI
```bash
git checkout main
git stash pop  # Restore changes if needed
cli-multi-rapid gui
```

## Dependencies

### Python GUI (Primary)
- **Required**: Python 3.8+, basic CLI dependencies
- **Optional**: PyQt6 (for GUI mode - fallback to headless if missing)
- **Install**: `pip install PyQt6` (optional)

### VS Code Extension (Alternative)
- **Required**: VS Code, Node.js (for development)
- **No additional Python dependencies**

## Migration Path

If you were using the VS Code extension:
1. Your VS Code extension is preserved on `interface/vscode-only` branch
2. The main branch now features the enhanced Python GUI system
3. All enterprise features are available on both branches
4. GDW framework adds deterministic workflow capabilities

The Python GUI provides a more integrated, standalone experience while the VS Code extension offers tight IDE integration. Choose based on your workflow preferences.
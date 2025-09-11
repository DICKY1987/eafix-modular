# Enhanced AI Toolchain Installer - New Features

This document describes the new configurable features added to the AI Toolchain Installer, making it more flexible and comprehensive while maintaining backward compatibility.

## 🆕 What's New

### 1. **Aider AI Coding Assistant**
- Automatic installation via pipx
- Configurable through `install.aider` setting
- Includes `aider-auto` alias for streamlined usage
- Version checking and updates during installation

### 2. **pipx Package Manager**
- Dedicated Python CLI tool manager
- Handles Aider and other Python CLI installations
- Configurable via `install.pipx` setting
- Automatic PATH management

### 3. **WSL2 Feature Enablement**
- Automatic enablement of Windows Subsystem for Linux
- Virtual Machine Platform feature activation
- WSL2 as default version configuration
- Admin privileges required, graceful fallback if not available
- Configurable via `install.wsl2_features` setting

### 4. **Enhanced Docker Management**
- **Auto-start Docker Desktop**: Automatically launch Docker Desktop
- **Engine Wait Logic**: Wait for Docker engine to be ready with configurable timeout
- **User Group Management**: Automatically add user to docker-users group
- **Robust Compose Operations**: Enhanced compose startup with container verification
- All features configurable via `docker.*` settings

### 5. **Advanced AI CLI Aliases**
- **Codex Mapping**: Maps `codex` command to GitHub Copilot CLI
- **Quality-of-Life Helpers**: `codex-commit-suggest`, `codex-explain`, `codex-grep`
- **Advanced AI Functions**: `ai-commit`, `ai-explain-error` for automated workflows
- All configurable via `aliases.*` settings

### 6. **Enhanced Doctor Function**
- Comprehensive health checks for all new components
- Version verification for Aider, Claude Code CLI
- Docker Compose service status checking
- WSL2 status verification
- pipx package manager validation

## 📋 Configuration Options

All new features are controlled via the enhanced configuration system:

```json
{
  "install": {
    "docker": true,          // Enable Docker Desktop installation
    "aider": true,           // Install Aider AI coding assistant
    "pipx": true,            // Install pipx package manager
    "wsl2_features": false   // Enable WSL2 features (requires admin)
  },
  "docker": {
    "auto_start_desktop": false,      // Auto-start Docker Desktop
    "wait_for_engine": true,          // Wait for engine readiness
    "add_user_to_group": true,        // Add user to docker-users
    "startup_timeout_minutes": 6      // Engine startup timeout
  },
  "aliases": {
    "enable_advanced": true,          // Advanced AI helper functions
    "enable_codex_mapping": true,     // Map codex to gh copilot
    "enable_qol_helpers": true        // Quality-of-life helpers
  }
}
```

## 🚀 Usage Examples

### Minimal Setup (Basic Python + Node.js)
```powershell
# Edit .ai/ai-config.json:
{
  "install": {
    "docker": false,
    "aider": false,
    "pipx": false
  },
  "aliases": {
    "enable_advanced": false,
    "enable_codex_mapping": false
  }
}
```

### Full AI Development Environment
```powershell
# Edit .ai/ai-config.json:
{
  "install": {
    "docker": true,
    "aider": true,
    "pipx": true,
    "wsl2_features": true
  },
  "docker": {
    "auto_start_desktop": true,
    "wait_for_engine": true
  },
  "aliases": {
    "enable_advanced": true,
    "enable_codex_mapping": true,
    "enable_qol_helpers": true
  }
}
```

### Docker-Focused Setup
```powershell
# Edit .ai/ai-config.json:
{
  "install": {
    "docker": true,
    "wsl2_features": true
  },
  "docker": {
    "auto_start_desktop": true,
    "startup_timeout_minutes": 10
  }
}
```

## 🔧 New CLI Aliases & Functions

### Basic Aliases (Always Available)
- `claude-auto` - Claude Code CLI with default args
- `ghs` - GitHub Copilot suggest shorthand
- `ghe` - GitHub Copilot explain shorthand

### Aider Integration (if enabled)
- `aider-auto` - Aider with --yes flag for non-interactive use
- `aiderc` - Alias for standard aider command

### Codex Mapping (if enabled)
- `codex` - Maps to `gh copilot` command
- `codex-auto` - Alias for codex command

### Quality-of-Life Helpers (if enabled)
- `codex-commit-suggest` - Get AI commit message suggestions
- `codex-explain` - Explain code or commands with AI
- `codex-grep` - AI-powered grep functionality

### Advanced AI Functions (if enabled)
- `ai-commit [message]` - Auto-commit with AI-generated message
- `ai-explain-error "command"` - Explain command errors with AI

## 🛡️ Safety & Backward Compatibility

### Default Behavior
- All new features are **opt-in** via configuration
- Existing installations continue to work unchanged
- Default configuration maintains previous behavior
- WSL2 features require admin and are disabled by default

### Error Handling
- Graceful fallbacks when tools are unavailable
- Admin privilege checks with appropriate warnings
- Comprehensive logging for troubleshooting
- Dry-run mode supports all new features

### Security Considerations
- pipx provides isolated Python CLI environments
- User group management only adds to docker-users
- WSL2 features only enable Microsoft-provided components
- All installations use official sources (winget, pipx, npm)

## 📊 Feature Comparison

| Feature | Original | Enhanced |
|---------|----------|----------|
| Python Tools | pip only | pip + pipx for CLI tools |
| Docker | Basic install | Full lifecycle management |
| AI CLIs | Claude Code only | Claude + Aider + advanced aliases |
| WSL2 | Assumed ready | Automatic enablement |
| Aliases | Basic shortcuts | Configurable advanced helpers |
| Health Checks | Basic commands | Comprehensive validation |

## 🔄 Migration Guide

### From Original Script
1. Copy your existing `.ai/ai-config.json` (if any)
2. Run the enhanced script - it will work with existing configuration
3. Optionally enable new features by editing the config file
4. Re-run to apply new features: `pwsh -File .\ai_toolchain_installer_complete.ps1`

### Enabling New Features
1. Edit `.ai/ai-config.json` to enable desired features
2. Re-run the installer to apply changes
3. Open a new terminal to load new aliases
4. Run the doctor check: Use the `-Verbose` flag to see detailed status

## 📚 Example Commands

```powershell
# Run with all features enabled
pwsh -File .\ai_toolchain_installer_complete.ps1 -StartCompose -LoginGh -Verbose

# Dry run with new features
pwsh -File .\ai_toolchain_installer_complete.ps1 -DryRun -Verbose

# Install Docker with auto-start (requires admin for WSL2)
# Edit config to enable docker.auto_start_desktop and install.wsl2_features
pwsh -File .\ai_toolchain_installer_complete.ps1 -InstallDocker -Force
```

The enhanced installer provides a comprehensive, configurable AI development environment while maintaining the simplicity and safety of the original design.
#!/bin/bash
# Cross-Platform Zero-Touch Multi-CLI AI Tool Setup
# Works on macOS, Linux, and Windows (via WSL)

set -euo pipefail

# Configuration
WORKSPACE_ROOT="$(pwd)"
AI_DIR="$WORKSPACE_ROOT/.ai"
LOG_FILE="$AI_DIR/setup-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directories
mkdir -p "$AI_DIR"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')
    local log_entry="[$timestamp] [$level] $message"
    
    case $level in
        "ERROR") echo -e "${RED}$log_entry${NC}" ;;
        "WARNING") echo -e "${YELLOW}$log_entry${NC}" ;;
        "SUCCESS") echo -e "${GREEN}$log_entry${NC}" ;;
        "INFO") echo -e "${BLUE}$log_entry${NC}" ;;
        *) echo "$log_entry" ;;
    esac
    
    echo "$log_entry" >> "$LOG_FILE"
}

# Detect OS and package manager
detect_system() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            OS="ubuntu"
            PKG_MANAGER="apt"
        elif command -v pacman >/dev/null 2>&1; then
            OS="arch"
            PKG_MANAGER="pacman"
        elif command -v dnf >/dev/null 2>&1; then
            OS="fedora"
            PKG_MANAGER="dnf"
        else
            OS="linux"
            PKG_MANAGER="manual"
        fi
    else
        OS="unknown"
        PKG_MANAGER="manual"
    fi
    
    log "INFO" "Detected OS: $OS, Package Manager: $PKG_MANAGER"
}

# Test if a command is available and working
test_command() {
    local cmd="$1"
    local test_args="${2:---version}"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        if $cmd $test_args >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Install package based on OS
install_package() {
    local package="$1"
    local brew_name="${2:-$package}"
    local apt_name="${3:-$package}"
    
    case $PKG_MANAGER in
        "brew")
            if ! brew list "$brew_name" >/dev/null 2>&1; then
                log "INFO" "Installing $package via brew..."
                brew install "$brew_name"
            fi
            ;;
        "apt")
            if ! dpkg -l | grep -q "$apt_name"; then
                log "INFO" "Installing $package via apt..."
                sudo apt update -y
                sudo apt install -y "$apt_name"
            fi
            ;;
        "pacman")
            if ! pacman -Q "$apt_name" >/dev/null 2>&1; then
                log "INFO" "Installing $package via pacman..."
                sudo pacman -S --noconfirm "$apt_name"
            fi
            ;;
        "dnf")
            if ! rpm -q "$apt_name" >/dev/null 2>&1; then
                log "INFO" "Installing $package via dnf..."
                sudo dnf install -y "$apt_name"
            fi
            ;;
        *)
            log "WARNING" "Manual installation required for $package"
            ;;
    esac
}

# Install prerequisites
install_prerequisites() {
    log "INFO" "Installing prerequisites..."
    
    # Install package manager if needed (macOS)
    if [[ "$OS" == "macos" ]] && ! command -v brew >/dev/null 2>&1; then
        log "INFO" "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv)" || eval "$(/usr/local/bin/brew shellenv)"
    fi
    
    # Install curl and git (essential)
    install_package "curl" "curl" "curl"
    install_package "git" "git" "git"
    
    # Install Node.js
    if ! test_command "node"; then
        case $PKG_MANAGER in
            "brew") install_package "nodejs" "node" ;;
            "apt") 
                curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
                sudo apt-get install -y nodejs
                ;;
            *) install_package "nodejs" "nodejs" "nodejs" ;;
        esac
    fi
    
    # Install Python
    if ! test_command "python3"; then
        install_package "python" "python@3.11" "python3"
    fi
    
    # Install pip
    if ! test_command "pip3"; then
        case $PKG_MANAGER in
            "apt") sudo apt install -y python3-pip ;;
            *) log "WARNING" "pip3 installation may be needed manually" ;;
        esac
    fi
    
    log "SUCCESS" "Prerequisites installed"
}

# Install GitHub CLI
install_github_cli() {
    log "INFO" "Installing GitHub CLI..."
    
    if test_command "gh"; then
        log "SUCCESS" "GitHub CLI already installed"
    else
        case $PKG_MANAGER in
            "brew")
                brew install gh
                ;;
            "apt")
                # Official GitHub CLI repository
                curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
                sudo apt update
                sudo apt install gh -y
                ;;
            *)
                # Fallback to manual installation
                log "WARNING" "Manual GitHub CLI installation required"
                ;;
        esac
    fi
    
    # Install Copilot extension
    if test_command "gh"; then
        log "INFO" "Installing GitHub Copilot CLI extension..."
        gh extension install github/gh-copilot --force || log "WARNING" "Failed to install Copilot extension"
        log "SUCCESS" "GitHub CLI setup complete"
    fi
}

# Install Claude Code CLI
install_claude_code() {
    log "INFO" "Installing Claude Code CLI..."
    
    if test_command "claude"; then
        log "SUCCESS" "Claude Code CLI already installed"
        return
    fi
    
    if test_command "npm"; then
        npm install -g @anthropic-ai/claude-code
        
        if test_command "claude"; then
            log "SUCCESS" "Claude Code CLI installed"
        else
            log "ERROR" "Claude Code CLI installation failed"
        fi
    else
        log "ERROR" "npm not available for Claude Code installation"
    fi
}

# Install Aider
install_aider() {
    log "INFO" "Installing Aider..."
    
    if test_command "aider"; then
        log "SUCCESS" "Aider already installed"
        return
    fi
    
    # Install via pip
    if test_command "pip3"; then
        pip3 install --user aider-chat
        
        # Add user bin to PATH if needed
        export PATH="$HOME/.local/bin:$PATH"
        
        if test_command "aider"; then
            log "SUCCESS" "Aider installed"
        else
            log "ERROR" "Aider installation failed"
        fi
    else
        log "ERROR" "pip3 not available for Aider installation"
    fi
}

# Install OpenAI CLI
install_openai_cli() {
    log "INFO" "Installing OpenAI CLI..."
    
    if test_command "openai"; then
        log "SUCCESS" "OpenAI CLI already installed"
        return
    fi
    
    if test_command "npm"; then
        npm install -g openai
        
        if test_command "openai"; then
            log "SUCCESS" "OpenAI CLI installed"
        else
            log "ERROR" "OpenAI CLI installation failed"
        fi
    else
        log "ERROR" "npm not available for OpenAI CLI installation"
    fi
}

# Setup authentication
setup_authentication() {
    log "INFO" "Setting up authentication..."
    
    # GitHub CLI
    if test_command "gh"; then
        if ! gh auth status >/dev/null 2>&1; then
            log "WARNING" "GitHub CLI not authenticated. Run 'gh auth login' manually."
        else
            log "SUCCESS" "GitHub CLI already authenticated"
        fi
    fi
    
    # Other tools typically require manual setup
    log "INFO" "Add API keys to .env file for other tools"
}

# Create VS Code workspace configuration
create_vscode_workspace() {
    log "INFO" "Creating VS Code workspace configuration..."
    
    local vscode_dir="$WORKSPACE_ROOT/.vscode"
    mkdir -p "$vscode_dir"
    
    # Create settings.json
    cat > "$vscode_dir/settings.json" << 'EOF'
{
    "task.allowAutomaticTasks": "on",
    "terminal.integrated.tabs.enabled": true,
    "terminal.integrated.defaultProfile.linux": "bash",
    "terminal.integrated.defaultProfile.osx": "zsh"
}
EOF

    # Create tasks.json with auto-starting terminals
    cat > "$vscode_dir/tasks.json" << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Launch GitHub Copilot Terminal",
            "type": "shell",
            "command": "bash",
            "args": [
                "-c",
                "echo -e '\\033[32mGitHub Copilot CLI Ready\\033[0m'; echo -e '\\033[36mUsage: gh copilot suggest \"your question\"\\033[0m'; gh auth status 2>/dev/null || echo 'Run: gh auth login'; exec bash"
            ],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new",
                "showReuseMessage": true,
                "clear": false,
                "group": "ai-tools"
            },
            "runOptions": {
                "runOn": "folderOpen"
            }
        },
        {
            "label": "Launch Claude Code Terminal",
            "type": "shell",
            "command": "bash",
            "args": [
                "-c",
                "echo -e '\\033[34mClaude Code CLI Ready\\033[0m'; echo -e '\\033[36mUsage: claude \"your prompt\"\\033[0m'; claude --version 2>/dev/null || echo 'Claude may need authentication'; exec bash"
            ],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new",
                "showReuseMessage": true,
                "clear": false,
                "group": "ai-tools"
            },
            "runOptions": {
                "runOn": "folderOpen"
            }
        },
        {
            "label": "Launch Aider Terminal",
            "type": "shell",
            "command": "bash",
            "args": [
                "-c",
                "echo -e '\\033[35mAider AI Pair Programmer Ready\\033[0m'; echo -e '\\033[36mUsage: aider file1.py file2.py\\033[0m'; aider --version 2>/dev/null || echo 'Aider not found'; exec bash"
            ],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new",
                "showReuseMessage": true,
                "clear": false,
                "group": "ai-tools"
            },
            "runOptions": {
                "runOn": "folderOpen"
            }
        },
        {
            "label": "Launch OpenAI CLI Terminal",
            "type": "shell",
            "command": "bash",
            "args": [
                "-c",
                "echo -e '\\033[33mOpenAI CLI Ready\\033[0m'; echo -e '\\033[36mSet OPENAI_API_KEY environment variable to use\\033[0m'; openai --version 2>/dev/null || echo 'OpenAI CLI not found'; exec bash"
            ],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new",
                "showReuseMessage": true,
                "clear": false,
                "group": "ai-tools"
            },
            "runOptions": {
                "runOn": "folderOpen"
            }
        },
        {
            "label": "Launch All AI Tools",
            "dependsOrder": "parallel",
            "dependsOn": [
                "Launch GitHub Copilot Terminal",
                "Launch Claude Code Terminal",
                "Launch Aider Terminal",
                "Launch OpenAI CLI Terminal"
            ],
            "runOptions": {
                "runOn": "folderOpen"
            }
        }
    ]
}
EOF
    
    log "SUCCESS" "VS Code workspace configuration created"
}

# Create environment file
create_environment_file() {
    log "INFO" "Creating environment file..."
    
    local env_file="$WORKSPACE_ROOT/.env"
    
    if [[ ! -f "$env_file" ]]; then
        cat > "$env_file" << 'EOF'
# AI CLI Tools Environment Configuration
# Add your API keys here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (for Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Other optional keys
GROQ_API_KEY=your_groq_api_key_here
TOGETHER_API_KEY=your_together_api_key_here

# GitHub token (usually handled by gh CLI)
# GITHUB_TOKEN=your_github_token_here
EOF
        log "SUCCESS" "Environment file created"
    else
        log "INFO" "Environment file already exists"
    fi
    
    # Ensure .env is in .gitignore
    local gitignore_file="$WORKSPACE_ROOT/.gitignore"
    if ! grep -q "^\.env$" "$gitignore_file" 2>/dev/null; then
        echo ".env" >> "$gitignore_file"
        log "INFO" "Added .env to .gitignore"
    fi
}

# Test all tools
test_all_tools() {
    log "INFO" "Testing all CLI tools..."
    
    local tools=(
        "gh:GitHub CLI"
        "claude:Claude Code"
        "aider:Aider"
        "openai:OpenAI CLI"
    )
    
    local all_working=true
    
    for tool_info in "${tools[@]}"; do
        IFS=':' read -r cmd name <<< "$tool_info"
        
        if test_command "$cmd"; then
            log "SUCCESS" "$name: Working"
        else
            log "ERROR" "$name: Not found or failed"
            all_working=false
        fi
    done
    
    # Test GitHub Copilot extension
    if test_command "gh" && gh extension list | grep -q copilot; then
        log "SUCCESS" "GitHub Copilot extension: Working"
    else
        log "ERROR" "GitHub Copilot extension: Not found"
        all_working=false
    fi
    
    if $all_working; then
        log "SUCCESS" "All tools are working!"
    else
        log "WARNING" "Some tools need attention"
    fi
    
    return $([ "$all_working" = true ])
}

# Create quick start guide
create_quick_start() {
    log "INFO" "Creating quick start guide..."
    
    cat > "$WORKSPACE_ROOT/AI-TOOLS-QUICKSTART.md" << 'EOF'
# AI Tools Quick Start Guide

## Setup Complete!

Your workspace is now configured with 4 AI CLI tools, each in its own terminal window.

## Tools Available

### 1. GitHub Copilot CLI
- **Terminal**: Green header
- **Usage**: `gh copilot suggest "your question"`
- **Purpose**: Get coding suggestions and explanations

### 2. Claude Code CLI  
- **Terminal**: Blue header
- **Usage**: `claude "your prompt"`
- **Purpose**: Advanced code analysis and generation

### 3. Aider AI Pair Programmer
- **Terminal**: Magenta header  
- **Usage**: `aider file1.py file2.py`
- **Purpose**: AI-powered code editing and refactoring

### 4. OpenAI CLI
- **Terminal**: Yellow header
- **Usage**: `openai api chat.completions.create -m gpt-4 --messages '[{"role":"user","content":"Hello"}]'`
- **Purpose**: Direct OpenAI API access

## Next Steps

1. **Add API Keys**: Edit `.env` file with your API keys
2. **Authentication**: 
   - Run `gh auth login` for GitHub
   - Claude may require manual authentication on first use
   - Set `OPENAI_API_KEY` in environment
3. **Start Coding**: Open any file and use the AI tools!

## Tips

- Each terminal is pre-loaded and ready to use
- Use `Ctrl+`` (backtick) to open/close terminal panel
- Switch between terminals using the terminal tabs
- All tools work together - use the best tool for each task

## Platform Notes

- **macOS**: Tools installed via Homebrew where possible
- **Linux**: Tools installed via system package manager
- **All platforms**: Node.js tools installed via npm

Happy coding with AI assistance!
EOF
    
    log "SUCCESS" "Quick start guide created"
}

# Main execution
main() {
    log "INFO" "Starting zero-touch AI CLI tools setup..."
    log "INFO" "Working directory: $WORKSPACE_ROOT"
    log "INFO" "Log file: $LOG_FILE"
    
    detect_system
    
    # Install everything
    install_prerequisites
    install_github_cli
    install_claude_code
    install_aider
    install_openai_cli
    
    # Setup environment
    setup_authentication
    create_vscode_workspace
    create_environment_file
    create_quick_start
    
    # Test and report
    log "INFO" "Testing installation..."
    if test_all_tools; then
        log "SUCCESS" "=== SETUP COMPLETE ==="
        log "SUCCESS" "All tools are working correctly!"
        log "INFO" "Open this folder in VS Code to see the 4 AI terminals"
    else
        log "WARNING" "=== SETUP COMPLETE WITH ISSUES ==="
        log "WARNING" "Some tools may need manual configuration"
        log "INFO" "Check the quick start guide for details"
    fi
    
    # Open VS Code if available
    if command -v code >/dev/null 2>&1; then
        log "INFO" "Opening VS Code..."
        code "$WORKSPACE_ROOT"
    else
        log "WARNING" "VS Code not found. Install VS Code and open this folder manually."
    fi
    
    log "INFO" "Log file saved to: $LOG_FILE"
}

# Run the main function
main "$@"
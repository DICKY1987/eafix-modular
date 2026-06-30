#!/bin/bash
# Free-Tier Multi-Agent Framework Setup
# Installs all free and open-source tools for the orchestrator

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

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
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        PKG_MANAGER="manual"
    else
        OS="unknown"
        PKG_MANAGER="manual"
    fi
    
    log_info "Detected OS: $OS, Package Manager: $PKG_MANAGER"
}

# Install prerequisites
install_prerequisites() {
    log_info "Installing prerequisites..."
    
    case $PKG_MANAGER in
        "brew")
            brew update
            brew install curl git jq python3 node npm
            ;;
        "apt")
            sudo apt update
            sudo apt install -y curl git jq python3 python3-pip nodejs npm
            ;;
        "pacman")
            sudo pacman -Sy curl git jq python python-pip nodejs npm
            ;;
        "dnf")
            sudo dnf install -y curl git jq python3 python3-pip nodejs npm
            ;;
        *)
            log_warning "Manual installation required for prerequisites"
            ;;
    esac
    
    log_success "Prerequisites installed"
}

# Install Ollama for local models
install_ollama() {
    log_info "Installing Ollama..."
    
    if command -v ollama >/dev/null 2>&1; then
        log_success "Ollama already installed"
        return
    fi
    
    if [[ "$OS" == "windows" ]]; then
        log_warning "Please install Ollama manually from https://ollama.ai/download/windows"
        return
    fi
    
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Start Ollama service
    if [[ "$OS" == "macos" ]]; then
        ollama serve &
    elif [[ "$OS" == "linux" ]]; then
        systemctl --user enable ollama
        systemctl --user start ollama
    fi
    
    log_success "Ollama installed"
}

# Pull essential local models
setup_local_models() {
    log_info "Setting up local models..."
    
    if ! command -v ollama >/dev/null 2>&1; then
        log_error "Ollama not found. Please install Ollama first."
        return
    fi
    
    # Essential models for coding
    models=(
        "codellama:7b-instruct"  # Primary coding model
        "codegemma:2b"           # Fast lightweight model
        "llama3.1:8b"            # General purpose
    )
    
    for model in "${models[@]}"; do
        log_info "Pulling model: $model"
        ollama pull "$model"
    done
    
    log_success "Local models setup complete"
}

# Install AI coding tools
install_ai_tools() {
    log_info "Installing AI coding tools..."
    
    # Aider - AI pair programmer
    pip3 install aider-chat
    
    # Continue CLI (if available)
    npm install -g @continuedev/cli || log_warning "Continue CLI not available via npm"
    
    log_success "AI tools installed"
}

# Install code quality tools
install_quality_tools() {
    log_info "Installing code quality tools..."
    
    # Python tools
    pip3 install ruff black pylint bandit safety
    
    # JavaScript tools
    npm install -g eslint prettier @eslint/config eslint-plugin-security
    
    # SQL tools
    pip3 install sqlfluff
    
    # General tools
    case $PKG_MANAGER in
        "brew")
            brew install sonarqube shellcheck hadolint
            ;;
        "apt")
            sudo apt install -y shellcheck
            # SonarQube requires manual setup
            ;;
        "pacman")
            sudo pacman -S shellcheck
            ;;
        *)
            log_warning "Some quality tools require manual installation"
            ;;
    esac
    
    log_success "Quality tools installed"
}

# Install security tools
install_security_tools() {
    log_info "Installing security scanning tools..."
    
    # OWASP Dependency Check
    case $PKG_MANAGER in
        "brew")
            brew install dependency-check
            ;;
        *)
            # Download manually
            mkdir -p ~/.local/bin
            DEPCHECK_VERSION="8.4.0"
            curl -L "https://github.com/jeremylong/DependencyCheck/releases/download/v${DEPCHECK_VERSION}/dependency-check-${DEPCHECK_VERSION}-release.zip" -o /tmp/depcheck.zip
            unzip /tmp/depcheck.zip -d ~/.local/
            ln -sf ~/.local/dependency-check/bin/dependency-check.sh ~/.local/bin/dependency-check
            ;;
    esac
    
    # Trivy scanner
    case $PKG_MANAGER in
        "brew")
            brew install trivy
            ;;
        "apt")
            sudo apt-get install wget apt-transport-https gnupg lsb-release
            wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
            echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
            sudo apt-get update
            sudo apt-get install trivy
            ;;
        *)
            # Install via binary
            TRIVY_VERSION="0.45.0"
            curl -L "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" | tar xz -C ~/.local/bin/
            ;;
    esac
    
    # Semgrep
    pip3 install semgrep
    
    # GitLeaks
    case $PKG_MANAGER in
        "brew")
            brew install gitleaks
            ;;
        *)
            GITLEAKS_VERSION="8.18.0"
            curl -L "https://github.com/zricethezav/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" | tar xz -C ~/.local/bin/
            ;;
    esac
    
    log_success "Security tools installed"
}

# Install infrastructure tools
install_infrastructure_tools() {
    log_info "Installing infrastructure tools..."
    
    # OpenTofu (open-source Terraform alternative)
    case $PKG_MANAGER in
        "brew")
            brew install opentofu
            ;;
        "apt")
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://get.opentofu.org/opentofu.gpg | sudo tee /etc/apt/keyrings/opentofu.gpg >/dev/null
            echo "deb [signed-by=/etc/apt/keyrings/opentofu.gpg] https://packages.opentofu.org/opentofu/tofu/any/ any main" | sudo tee /etc/apt/sources.list.d/opentofu.list
            sudo apt update
            sudo apt install tofu
            ;;
        *)
            # Manual installation
            TOFU_VERSION="1.6.0"
            curl -L "https://github.com/opentofu/opentofu/releases/download/v${TOFU_VERSION}/tofu_${TOFU_VERSION}_linux_amd64.zip" -o /tmp/tofu.zip
            unzip /tmp/tofu.zip -d ~/.local/bin/
            ;;
    esac
    
    # Ansible
    pip3 install ansible
    
    # Checkov for IaC security
    pip3 install checkov
    
    log_success "Infrastructure tools installed"
}

# Install documentation tools
install_documentation_tools() {
    log_info "Installing documentation tools..."
    
    # OpenAPI Generator
    case $PKG_MANAGER in
        "brew")
            brew install openapi-generator
            ;;
        *)
            npm install -g @openapitools/openapi-generator-cli
            ;;
    esac
    
    # MkDocs
    pip3 install mkdocs mkdocs-material
    
    # Markdown tools
    npm install -g markdownlint-cli
    
    log_success "Documentation tools installed"
}

# Install monitoring tools
install_monitoring_tools() {
    log_info "Installing monitoring tools..."
    
    # Prometheus and Grafana require manual setup or Docker
    log_warning "Prometheus and Grafana setup requires manual configuration"
    
    # Basic monitoring tools
    case $PKG_MANAGER in
        "brew")
            brew install htop btop
            ;;
        "apt")
            sudo apt install -y htop
            ;;
        "pacman")
            sudo pacman -S htop btop
            ;;
    esac
    
    log_success "Basic monitoring tools installed"
}

# Setup framework configuration
setup_framework_config() {
    log_info "Setting up framework configuration..."
    
    mkdir -p .ai
    
    # Copy configuration if it doesn't exist
    if [[ ! -f ".ai/framework-config.json" ]]; then
        log_info "Creating default framework configuration..."
        cat > .ai/framework-config.json << 'EOF'
{
  "framework": {
    "name": "Free-Tier Multi-Agent Orchestrator",
    "version": "1.0.0"
  },
  "quotaManagement": {
    "enabled": true,
    "services": {
      "gemini": {
        "dailyLimit": 1000,
        "priority": 1
      },
      "codeium": {
        "dailyLimit": "unlimited",
        "priority": 2
      }
    }
  },
  "localModels": {
    "enabled": true,
    "provider": "ollama",
    "models": {
      "coding": {
        "name": "codellama:7b-instruct"
      },
      "fast": {
        "name": "codegemma:2b"
      }
    }
  },
  "lanes": {
    "ai_coding": {
      "worktreePath": ".worktrees/ai-coding",
      "branch": "lane/ai-coding",
      "allowedPatterns": ["src/**", "lib/**"],
      "commitPrefix": "ai:"
    },
    "quality": {
      "worktreePath": ".worktrees/quality",
      "branch": "lane/quality",
      "allowedPatterns": ["**/*.js", "**/*.py"],
      "commitPrefix": "quality:"
    },
    "security": {
      "worktreePath": ".worktrees/security",
      "branch": "lane/security",
      "allowedPatterns": ["**/*"],
      "commitPrefix": "security:"
    }
  }
}
EOF
    fi
    
    # Create quota tracker
    if [[ ! -f ".ai/quota-tracker.json" ]]; then
        cat > .ai/quota-tracker.json << 'EOF'
{
  "lastReset": "2024-01-01",
  "services": {}
}
EOF
    fi
    
    log_success "Framework configuration created"
}

# Create helper scripts
create_helper_scripts() {
    log_info "Creating helper scripts..."
    
    mkdir -p .ai/scripts
    
    # Quick lane starter
    cat > .ai/scripts/quick-start.sh << 'EOF'
#!/bin/bash
# Quick start script for common operations

case "$1" in
    "code")
        ./orchestrator.ps1 -Command start-lane -Lane ai_coding
        ;;
    "quality")
        ./orchestrator.ps1 -Command start-lane -Lane quality
        ;;
    "security")
        ./orchestrator.ps1 -Command start-lane -Lane security
        ;;
    "status")
        ./orchestrator.ps1 -Command status
        ;;
    *)
        echo "Usage: $0 {code|quality|security|status}"
        ;;
esac
EOF
    
    chmod +x .ai/scripts/quick-start.sh
    
    # Cost monitoring script
    cat > .ai/scripts/cost-monitor.py << 'EOF'
#!/usr/bin/env python3
import json
import datetime

def check_quotas():
    try:
        with open('.ai/quota-tracker.json', 'r') as f:
            tracker = json.load(f)
        
        with open('.ai/framework-config.json', 'r') as f:
            config = json.load(f)
        
        print("🎯 Quota Status:")
        total_savings = 0
        
        for service_name, service_config in config['quotaManagement']['services'].items():
            usage = tracker['services'].get(service_name, 0)
            limit = service_config.get('dailyLimit', 'unlimited')
            
            if limit == 'unlimited':
                print(f"  {service_name}: {usage} requests (unlimited)")
            else:
                percentage = (usage / limit) * 100
                print(f"  {service_name}: {usage}/{limit} ({percentage:.1f}%)")
                
                # Estimate savings (assuming $0.01 per request if paid)
                estimated_cost = usage * 0.01
                total_savings += estimated_cost
        
        print(f"\n💰 Estimated savings today: ${total_savings:.2f}")
        
    except FileNotFoundError:
        print("❌ Configuration files not found. Run setup first.")

if __name__ == "__main__":
    check_quotas()
EOF
    
    chmod +x .ai/scripts/cost-monitor.py
    
    log_success "Helper scripts created"
}

# Main installation function
main() {
    echo -e "${BLUE}"
    echo "🚀 Free-Tier Multi-Agent Framework Setup"
    echo "========================================"
    echo -e "${NC}"
    
    detect_system
    
    # Create .local/bin if it doesn't exist
    mkdir -p ~/.local/bin
    export PATH="$HOME/.local/bin:$PATH"
    
    # Install components
    install_prerequisites
    install_ollama
    install_ai_tools
    install_quality_tools
    install_security_tools
    install_infrastructure_tools
    install_documentation_tools
    install_monitoring_tools
    
    # Setup framework
    setup_framework_config
    create_helper_scripts
    
    # Setup local models (optional, takes time)
    read -p "Setup local models now? This will download several GB of data. (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_local_models
    else
        log_info "Skipping local models setup. Run 'ollama pull codellama:7b-instruct' later."
    fi
    
    echo -e "${GREEN}"
    echo "✅ Setup Complete!"
    echo "=================="
    echo -e "${NC}"
    echo "Next steps:"
    echo "1. Run: ./orchestrator.ps1 -Command init"
    echo "2. Run: ./orchestrator.ps1 -Command status"
    echo "3. Start a lane: ./orchestrator.ps1 -Command start-lane -Lane ai_coding"
    echo ""
    echo "💡 Quick access: .ai/scripts/quick-start.sh code"
    echo "📊 Monitor costs: .ai/scripts/cost-monitor.py"
    echo ""
    echo "🎯 You now have access to:"
    echo "  - Free AI coding with Gemini CLI (1000 requests/day)"
    echo "  - Unlimited local AI with Ollama"
    echo "  - Complete free security scanning suite"
    echo "  - Open-source code quality tools"
    echo "  - Free infrastructure automation"
    echo ""
    echo "💰 Estimated monthly savings: $200-500+ vs paid alternatives"
}

# Run main function
main "$@"
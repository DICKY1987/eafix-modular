#!/bin/bash

# EAFIX Developer Environment Setup Script
# This script sets up a complete development environment for the EAFIX trading system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.11"
NODE_VERSION="18"
DOCKER_COMPOSE_VERSION="2.20.0"

echo -e "${BLUE}🚀 EAFIX Developer Environment Setup${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    OS="unknown"
fi

echo -e "${BLUE}Detected OS: ${OS}${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install package manager (if needed)
install_package_manager() {
    echo -e "${YELLOW}📦 Setting up package manager...${NC}"
    
    if [[ "$OS" == "macos" ]]; then
        if ! command_exists brew; then
            echo -e "${YELLOW}Installing Homebrew...${NC}"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        else
            echo -e "${GREEN}✅ Homebrew already installed${NC}"
        fi
    elif [[ "$OS" == "linux" ]]; then
        if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
            sudo apt update
            echo -e "${GREEN}✅ Package manager ready (apt)${NC}"
        elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
            sudo yum update -y
            echo -e "${GREEN}✅ Package manager ready (yum)${NC}"
        fi
    elif [[ "$OS" == "windows" ]]; then
        if ! command_exists choco; then
            echo -e "${YELLOW}Please install Chocolatey manually: https://chocolatey.org/install${NC}"
            echo -e "${YELLOW}Then re-run this script${NC}"
            exit 1
        else
            echo -e "${GREEN}✅ Chocolatey already installed${NC}"
        fi
    fi
    echo ""
}

# Function to install Python
install_python() {
    echo -e "${YELLOW}🐍 Setting up Python ${PYTHON_VERSION}...${NC}"
    
    if command_exists python3 && [[ "$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)" == "$PYTHON_VERSION" ]]; then
        echo -e "${GREEN}✅ Python ${PYTHON_VERSION} already installed${NC}"
    else
        if [[ "$OS" == "macos" ]]; then
            brew install python@${PYTHON_VERSION}
        elif [[ "$OS" == "linux" ]]; then
            if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
                sudo apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev
            elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
                sudo yum install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-devel
            fi
        elif [[ "$OS" == "windows" ]]; then
            choco install python --version=${PYTHON_VERSION}
        fi
        echo -e "${GREEN}✅ Python ${PYTHON_VERSION} installed${NC}"
    fi
    echo ""
}

# Function to install Poetry
install_poetry() {
    echo -e "${YELLOW}📚 Setting up Poetry...${NC}"
    
    if command_exists poetry; then
        echo -e "${GREEN}✅ Poetry already installed${NC}"
    else
        echo -e "${YELLOW}Installing Poetry...${NC}"
        curl -sSL https://install.python-poetry.org | python3 -
        
        # Add to PATH
        export PATH="$HOME/.local/bin:$PATH"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc 2>/dev/null || true
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
        
        echo -e "${GREEN}✅ Poetry installed${NC}"
    fi
    
    # Configure Poetry
    if command_exists poetry; then
        poetry config virtualenvs.in-project true
        echo -e "${GREEN}✅ Poetry configured (virtualenvs in project)${NC}"
    fi
    echo ""
}

# Function to install Docker
install_docker() {
    echo -e "${YELLOW}🐳 Setting up Docker...${NC}"
    
    if command_exists docker; then
        echo -e "${GREEN}✅ Docker already installed${NC}"
    else
        echo -e "${YELLOW}Installing Docker...${NC}"
        if [[ "$OS" == "macos" ]]; then
            echo -e "${YELLOW}Please install Docker Desktop manually: https://www.docker.com/products/docker-desktop${NC}"
            echo -e "${YELLOW}Then re-run this script${NC}"
            exit 1
        elif [[ "$OS" == "linux" ]]; then
            if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
                sudo apt install -y docker.io docker-compose
                sudo systemctl start docker
                sudo systemctl enable docker
                sudo usermod -aG docker $USER
            elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
                sudo yum install -y docker docker-compose
                sudo systemctl start docker
                sudo systemctl enable docker
                sudo usermod -aG docker $USER
            fi
        elif [[ "$OS" == "windows" ]]; then
            echo -e "${YELLOW}Please install Docker Desktop manually: https://www.docker.com/products/docker-desktop${NC}"
            echo -e "${YELLOW}Then re-run this script${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Docker installed${NC}"
        echo -e "${YELLOW}⚠️  Please log out and back in to apply Docker group membership${NC}"
    fi
    echo ""
}

# Function to install Node.js (for some dev tools)
install_nodejs() {
    echo -e "${YELLOW}📦 Setting up Node.js...${NC}"
    
    if command_exists node && [[ "$(node --version | cut -d'v' -f2 | cut -d'.' -f1)" == "$NODE_VERSION" ]]; then
        echo -e "${GREEN}✅ Node.js ${NODE_VERSION} already installed${NC}"
    else
        if [[ "$OS" == "macos" ]]; then
            brew install node@${NODE_VERSION}
        elif [[ "$OS" == "linux" ]]; then
            curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif [[ "$OS" == "windows" ]]; then
            choco install nodejs --version=${NODE_VERSION}
        fi
        echo -e "${GREEN}✅ Node.js ${NODE_VERSION} installed${NC}"
    fi
    echo ""
}

# Function to install development tools
install_dev_tools() {
    echo -e "${YELLOW}🔧 Setting up development tools...${NC}"
    
    # Git
    if ! command_exists git; then
        echo -e "${YELLOW}Installing Git...${NC}"
        if [[ "$OS" == "macos" ]]; then
            brew install git
        elif [[ "$OS" == "linux" ]]; then
            if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
                sudo apt install -y git
            elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
                sudo yum install -y git
            fi
        elif [[ "$OS" == "windows" ]]; then
            choco install git
        fi
    else
        echo -e "${GREEN}✅ Git already installed${NC}"
    fi
    
    # curl
    if ! command_exists curl; then
        echo -e "${YELLOW}Installing curl...${NC}"
        if [[ "$OS" == "macos" ]]; then
            brew install curl
        elif [[ "$OS" == "linux" ]]; then
            if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
                sudo apt install -y curl
            elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
                sudo yum install -y curl
            fi
        elif [[ "$OS" == "windows" ]]; then
            # curl is usually pre-installed on Windows 10+
            echo -e "${GREEN}✅ curl available${NC}"
        fi
    else
        echo -e "${GREEN}✅ curl already installed${NC}"
    fi
    
    # jq (JSON processor)
    if ! command_exists jq; then
        echo -e "${YELLOW}Installing jq...${NC}"
        if [[ "$OS" == "macos" ]]; then
            brew install jq
        elif [[ "$OS" == "linux" ]]; then
            if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
                sudo apt install -y jq
            elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
                sudo yum install -y jq
            fi
        elif [[ "$OS" == "windows" ]]; then
            choco install jq
        fi
    else
        echo -e "${GREEN}✅ jq already installed${NC}"
    fi
    
    # make
    if ! command_exists make; then
        echo -e "${YELLOW}Installing make...${NC}"
        if [[ "$OS" == "macos" ]]; then
            xcode-select --install 2>/dev/null || echo "Command Line Tools already installed"
        elif [[ "$OS" == "linux" ]]; then
            if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
                sudo apt install -y build-essential
            elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
                sudo yum groupinstall -y "Development Tools"
            fi
        elif [[ "$OS" == "windows" ]]; then
            choco install make
        fi
    else
        echo -e "${GREEN}✅ make already installed${NC}"
    fi
    
    echo ""
}

# Function to install database clients
install_database_clients() {
    echo -e "${YELLOW}🗄️ Setting up database clients...${NC}"
    
    # PostgreSQL client
    if ! command_exists psql; then
        echo -e "${YELLOW}Installing PostgreSQL client...${NC}"
        if [[ "$OS" == "macos" ]]; then
            brew install postgresql
        elif [[ "$OS" == "linux" ]]; then
            if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
                sudo apt install -y postgresql-client
            elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
                sudo yum install -y postgresql
            fi
        elif [[ "$OS" == "windows" ]]; then
            choco install postgresql
        fi
    else
        echo -e "${GREEN}✅ PostgreSQL client already installed${NC}"
    fi
    
    # Redis client
    if ! command_exists redis-cli; then
        echo -e "${YELLOW}Installing Redis client...${NC}"
        if [[ "$OS" == "macos" ]]; then
            brew install redis
        elif [[ "$OS" == "linux" ]]; then
            if [[ "$DISTRO" == "Ubuntu" || "$DISTRO" == "Debian" ]]; then
                sudo apt install -y redis-tools
            elif [[ "$DISTRO" == "CentOS" || "$DISTRO" == "RedHat" ]]; then
                sudo yum install -y redis
            fi
        elif [[ "$OS" == "windows" ]]; then
            echo -e "${YELLOW}⚠️  Redis CLI not easily available on Windows. Use Docker for Redis access.${NC}"
        fi
    else
        echo -e "${GREEN}✅ Redis client already installed${NC}"
    fi
    
    echo ""
}

# Function to set up the project
setup_project() {
    echo -e "${YELLOW}📁 Setting up EAFIX project...${NC}"
    
    # Install Python dependencies
    if command_exists poetry && [ -f "pyproject.toml" ]; then
        echo -e "${YELLOW}Installing Python dependencies...${NC}"
        poetry install
        echo -e "${GREEN}✅ Python dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️  pyproject.toml not found or Poetry not available${NC}"
    fi
    
    # Set up pre-commit hooks
    if command_exists poetry; then
        echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
        poetry run pre-commit install
        echo -e "${GREEN}✅ Pre-commit hooks installed${NC}"
    fi
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating default .env file...${NC}"
        cat > .env << EOF
# EAFIX Development Environment Configuration
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://eafix:password@localhost:5432/eafix_dev
LOG_LEVEL=INFO
DEBUG=true

# Service Configuration
DATA_INGESTOR_PORT=8081
INDICATOR_ENGINE_PORT=8082
SIGNAL_GENERATOR_PORT=8083
RISK_MANAGER_PORT=8084
EXECUTION_ENGINE_PORT=8085
CALENDAR_INGESTOR_PORT=8086
REENTRY_MATRIX_SVC_PORT=8087
REPORTER_PORT=8088
GUI_GATEWAY_PORT=8080

# External APIs (configure as needed)
BROKER_API_URL=https://api.broker.com
MARKET_DATA_URL=https://api.marketdata.com
EOF
        echo -e "${GREEN}✅ Default .env file created${NC}"
    else
        echo -e "${GREEN}✅ .env file already exists${NC}"
    fi
    
    echo ""
}

# Function to create development utilities
create_dev_utilities() {
    echo -e "${YELLOW}🛠️ Creating development utilities...${NC}"
    
    # Create development scripts directory
    mkdir -p scripts/dev
    
    # Create quick development commands script
    cat > scripts/dev/dev-commands.sh << 'EOF'
#!/bin/bash

# Quick development commands for EAFIX

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

case "$1" in
    "start")
        echo -e "${BLUE}🚀 Starting EAFIX development environment...${NC}"
        docker compose -f deploy/compose/docker-compose.yml up -d
        echo -e "${GREEN}✅ Services started${NC}"
        echo -e "${BLUE}🌐 GUI Gateway: http://localhost:8080${NC}"
        echo -e "${BLUE}📊 Grafana: http://localhost:3000${NC}"
        ;;
    "stop")
        echo -e "${YELLOW}🛑 Stopping EAFIX development environment...${NC}"
        docker compose -f deploy/compose/docker-compose.yml down
        echo -e "${GREEN}✅ Services stopped${NC}"
        ;;
    "restart")
        echo -e "${YELLOW}🔄 Restarting EAFIX development environment...${NC}"
        docker compose -f deploy/compose/docker-compose.yml down
        sleep 2
        docker compose -f deploy/compose/docker-compose.yml up -d
        echo -e "${GREEN}✅ Services restarted${NC}"
        ;;
    "logs")
        service=${2:-""}
        if [ -n "$service" ]; then
            echo -e "${BLUE}📋 Showing logs for $service...${NC}"
            docker compose -f deploy/compose/docker-compose.yml logs -f "$service"
        else
            echo -e "${BLUE}📋 Showing logs for all services...${NC}"
            docker compose -f deploy/compose/docker-compose.yml logs -f
        fi
        ;;
    "health")
        echo -e "${BLUE}🏥 Checking service health...${NC}"
        make health-check
        ;;
    "test")
        echo -e "${BLUE}🧪 Running tests...${NC}"
        poetry run pytest
        ;;
    "format")
        echo -e "${BLUE}🎨 Formatting code...${NC}"
        poetry run black services/
        poetry run isort services/
        echo -e "${GREEN}✅ Code formatted${NC}"
        ;;
    "lint")
        echo -e "${BLUE}🔍 Linting code...${NC}"
        poetry run flake8 services/
        poetry run mypy services/*/src
        ;;
    "clean")
        echo -e "${YELLOW}🧹 Cleaning up...${NC}"
        docker system prune -f
        poetry run pre-commit clean
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        echo -e "${GREEN}✅ Cleanup completed${NC}"
        ;;
    "reset")
        echo -e "${RED}🔥 Resetting development environment...${NC}"
        echo -e "${YELLOW}⚠️  This will remove all containers and volumes!${NC}"
        read -p "Type 'RESET' to confirm: " confirm
        if [ "$confirm" = "RESET" ]; then
            docker compose -f deploy/compose/docker-compose.yml down -v
            docker system prune -af
            echo -e "${GREEN}✅ Environment reset${NC}"
        else
            echo -e "${BLUE}Reset cancelled${NC}"
        fi
        ;;
    *)
        echo -e "${BLUE}EAFIX Development Commands:${NC}"
        echo ""
        echo "  start     - Start all services"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  logs [service] - Show logs (optionally for specific service)"
        echo "  health    - Check service health"
        echo "  test      - Run tests"
        echo "  format    - Format code"
        echo "  lint      - Lint code"
        echo "  clean     - Clean up temporary files"
        echo "  reset     - Reset entire environment"
        echo ""
        echo -e "${BLUE}Examples:${NC}"
        echo "  $0 start"
        echo "  $0 logs signal-generator"
        echo "  $0 test"
        ;;
esac
EOF
    
    chmod +x scripts/dev/dev-commands.sh
    echo -e "${GREEN}✅ Development commands script created${NC}"
    
    # Create alias suggestion
    cat > scripts/dev/setup-aliases.sh << 'EOF'
#!/bin/bash

# Add these aliases to your shell profile (~/.bashrc, ~/.zshrc, etc.)

echo "# EAFIX Development Aliases"
echo "alias eafix='./scripts/dev/dev-commands.sh'"
echo "alias eafix-start='./scripts/dev/dev-commands.sh start'"
echo "alias eafix-stop='./scripts/dev/dev-commands.sh stop'"
echo "alias eafix-logs='./scripts/dev/dev-commands.sh logs'"
echo "alias eafix-health='./scripts/dev/dev-commands.sh health'"
echo "alias eafix-test='./scripts/dev/dev-commands.sh test'"
echo ""
echo "To add these aliases, run:"
echo "echo '# EAFIX Aliases' >> ~/.bashrc"
echo "./scripts/dev/setup-aliases.sh >> ~/.bashrc"
echo "source ~/.bashrc"
EOF
    
    chmod +x scripts/dev/setup-aliases.sh
    echo -e "${GREEN}✅ Alias setup script created${NC}"
    
    echo ""
}

# Function to setup IDE configurations
setup_ide_configs() {
    echo -e "${YELLOW}💻 Setting up IDE configurations...${NC}"
    
    # VS Code settings
    mkdir -p .vscode
    
    cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".venv": true,
        ".mypy_cache": true,
        ".pytest_cache": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests",
        "-v"
    ],
    "docker.enableDockerComposeLanguageService": true
}
EOF
    
    cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Signal Generator",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/services/signal-generator/src/main.py",
            "env": {
                "REDIS_URL": "redis://localhost:6379",
                "LOG_LEVEL": "DEBUG"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Debug Risk Manager",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/services/risk-manager/src/main.py",
            "env": {
                "REDIS_URL": "redis://localhost:6379",
                "DATABASE_URL": "postgresql://eafix:password@localhost:5432/eafix_dev",
                "LOG_LEVEL": "DEBUG"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v"],
            "console": "integratedTerminal"
        }
    ]
}
EOF
    
    cat > .vscode/tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start EAFIX Services",
            "type": "shell",
            "command": "make docker-up",
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Stop EAFIX Services",
            "type": "shell",
            "command": "make docker-down",
            "group": "build"
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "poetry run pytest",
            "group": "test"
        },
        {
            "label": "Format Code",
            "type": "shell",
            "command": "make format",
            "group": "build"
        },
        {
            "label": "Lint Code",
            "type": "shell",
            "command": "make lint",
            "group": "build"
        }
    ]
}
EOF
    
    cat > .vscode/extensions.json << 'EOF'
{
    "recommendations": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.mypy-type-checker",
        "ms-python.black-formatter",
        "ms-python.isort",
        "ms-vscode.docker",
        "ms-azuretools.vscode-docker",
        "redhat.vscode-yaml",
        "ms-vscode.makefile-tools",
        "tamasfe.even-better-toml",
        "charliermarsh.ruff"
    ]
}
EOF
    
    echo -e "${GREEN}✅ VS Code configuration created${NC}"
    
    # PyCharm/IntelliJ settings hint
    cat > .idea-settings.md << 'EOF'
# PyCharm/IntelliJ IDEA Setup

## Python Interpreter
- Go to Settings → Project → Python Interpreter
- Add interpreter from existing environment: `.venv/bin/python`

## Code Style
- Settings → Editor → Code Style → Python
- Import scheme from: https://github.com/psf/black/blob/main/docs/compatible_configs/.idea/codeStyles/Black.xml

## Run Configurations
Create run configurations for:
- Signal Generator: `services/signal-generator/src/main.py`
- Risk Manager: `services/risk-manager/src/main.py`
- Tests: `pytest` with working directory as project root

## Plugins
Install these plugins:
- Docker
- Makefile Language
- TOML
EOF
    
    echo -e "${GREEN}✅ IDE configuration files created${NC}"
    echo ""
}

# Function to create development documentation
create_dev_docs() {
    echo -e "${YELLOW}📖 Creating development documentation...${NC}"
    
    mkdir -p docs/development
    
    cat > docs/development/getting-started.md << 'EOF'
# Getting Started with EAFIX Development

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd eafix-modular
   ```

2. **Run the setup script:**
   ```bash
   ./scripts/dev-setup.sh
   ```

3. **Start the development environment:**
   ```bash
   make docker-up
   # OR
   ./scripts/dev/dev-commands.sh start
   ```

4. **Run tests to verify setup:**
   ```bash
   make test-all
   ```

## Development Workflow

### Daily Development
```bash
# Start services
eafix-start

# Check health
eafix-health

# Make changes to code...

# Run tests
eafix-test

# Format and lint
make format
make lint

# View logs
eafix-logs signal-generator
```

### Before Committing
```bash
# Run all quality checks
make lint
make test-all
make contracts-validate-full

# Pre-commit hooks will run automatically
git commit -m "Your commit message"
```

## Service Development

### Running Individual Services
```bash
# Start infrastructure (Redis, PostgreSQL)
docker compose up -d redis postgres

# Run service locally for debugging
cd services/signal-generator
poetry run python -m src.main
```

### Debugging
- Use VS Code launch configurations for debugging
- Set breakpoints in your IDE
- Use `poetry run python -m pdb` for command-line debugging

### Testing
```bash
# Run all tests
make test-all

# Run service-specific tests
cd services/signal-generator
poetry run pytest

# Run with coverage
poetry run pytest --cov=src
```

## Architecture Overview

### Services
- **GUI Gateway (8080)**: API gateway and web interface
- **Data Ingestor (8081)**: Market data ingestion and normalization
- **Indicator Engine (8082)**: Technical indicator calculations
- **Signal Generator (8083)**: Trading signal generation
- **Risk Manager (8084)**: Risk validation and position sizing
- **Execution Engine (8085)**: Order execution and broker communication
- **Calendar Ingestor (8086)**: Economic calendar data processing
- **Reentry Matrix Service (8087)**: Re-entry decision logic
- **Reporter (8088)**: Reporting and analytics

### Data Flow
```
Market Data → Data Ingestor → Indicator Engine → Signal Generator
                                                       ↓
                                               Risk Manager ← Position Data
                                                       ↓
                                               Execution Engine → Broker API
                                                       ↓
                                                   Reporter
```

## Common Tasks

### Adding a New Service
1. Copy service template from `templates/service/`
2. Update service name and port in `docker-compose.yml`
3. Add service to `Makefile` targets
4. Create tests in `tests/services/`
5. Update documentation

### Adding New Dependencies
```bash
# Add to specific service
cd services/signal-generator
poetry add requests

# Add development dependency
poetry add --dev pytest-mock
```

### Database Changes
1. Create migration script in `migrations/`
2. Test migration on development database
3. Update schema documentation
4. Add rollback procedure

## Troubleshooting

### Common Issues
- **Port conflicts**: Check if ports 8080-8088 are available
- **Docker issues**: Try `docker system prune -f`
- **Poetry issues**: Delete `.venv` and run `poetry install`
- **Database connection**: Ensure PostgreSQL container is running

### Getting Help
- Check `docs/runbooks/common-issues.md`
- Ask in #eafix-dev Slack channel
- Review existing issues in GitHub

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and add tests
3. Ensure all quality checks pass
4. Create pull request with description
5. Address review feedback
EOF
    
    cat > docs/development/architecture.md << 'EOF'
# EAFIX Architecture Guide

## System Overview

EAFIX is a microservices-based trading system designed for high-frequency financial operations with strict reliability and performance requirements.

## Core Principles

### Event-Driven Architecture
- Services communicate via Redis pub/sub for async operations
- HTTP APIs for synchronous request/response patterns
- Message schemas enforced via contract testing

### Defensive Design
- Fail-safe defaults for trading operations
- Circuit breakers for external dependencies
- Comprehensive input validation
- Graceful degradation under load

### Observability First
- Structured logging with correlation IDs
- Prometheus metrics for all services
- Distributed tracing readiness
- Health checks at multiple levels

## Service Architecture

### Core Trading Pipeline
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Data Ingestor  │───▶│ Indicator Engine │───▶│ Signal Generator│
│     (8081)      │    │      (8082)      │    │     (8083)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Reporter     │◀───│ Execution Engine │◀───│  Risk Manager   │
│     (8088)      │    │      (8085)      │    │     (8084)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Supporting Services
- **GUI Gateway (8080)**: API gateway, web UI, service orchestration
- **Calendar Ingestor (8086)**: Economic calendar processing
- **Reentry Matrix Service (8087)**: Re-entry decision logic

### Infrastructure Services
- **Redis (6379)**: Message bus, caching, session storage
- **PostgreSQL (5432)**: Persistent data, configuration, audit logs
- **Prometheus (9090)**: Metrics collection and alerting
- **Grafana (3000)**: Monitoring dashboards

## Data Flow Patterns

### Price Data Flow
1. **Ingestion**: MT4/DDE → Data Ingestor
2. **Processing**: Raw ticks → Normalized price events
3. **Distribution**: Redis pub/sub → Indicator Engine
4. **Calculation**: Technical indicators computed
5. **Signal Generation**: Trading rules applied
6. **Risk Assessment**: Position sizing and validation
7. **Execution**: Orders sent to broker
8. **Reporting**: Results tracked and analyzed

### Event Schema Evolution
- Schema versioning (e.g., `PriceTick@1.0`)
- Backward compatibility enforcement
- Contract testing validates schema adherence
- Graceful handling of unknown fields

## Configuration Management

### Environment-Based Config
- Development: `.env` files
- Staging: Environment variables
- Production: Kubernetes secrets/configmaps

### Service Discovery
- Docker Compose: Service names
- Kubernetes: Service objects
- Health checks: `/healthz` endpoints

## Security Architecture

### Authentication & Authorization
- Service-to-service: mTLS (planned)
- API access: JWT tokens
- Database: Role-based access control

### Data Protection
- Secrets management via environment variables
- No hardcoded credentials
- Audit logging for sensitive operations

### Network Security
- Service mesh for production (Istio)
- Network policies in Kubernetes
- Minimal attack surface

## Scalability Patterns

### Horizontal Scaling
- Stateless services scale independently
- Load balancing via service mesh
- Database connection pooling

### Performance Optimization
- Redis caching for frequently accessed data
- Database indexing for trading queries
- Async processing where possible

### Resource Management
- Memory limits per service
- CPU resource allocation
- Disk space monitoring

## Testing Strategy

### Test Pyramid
- **Unit Tests**: Service logic, pure functions
- **Integration Tests**: Service interactions, database operations
- **Contract Tests**: API compatibility between services
- **End-to-End Tests**: Complete trading workflows

### Test Environments
- **Local**: Developer machine with Docker Compose
- **CI**: GitHub Actions with containerized services
- **Staging**: Production-like environment for integration testing

## Deployment Architecture

### Container Strategy
- Multi-stage Dockerfiles for smaller images
- Security scanning with Trivy
- Image signing with Cosign
- Registry: GitHub Container Registry

### Orchestration
- **Development**: Docker Compose
- **Production**: Kubernetes with Helm
- **Service Mesh**: Istio for traffic management

### Release Strategy
- Blue-green deployments for zero downtime
- Canary releases for high-risk changes
- Automated rollback on failure detection

## Monitoring & Alerting

### Metrics Collection
- **Golden Signals**: Latency, traffic, errors, saturation
- **Business Metrics**: Trading P&L, signal accuracy, execution rates
- **System Metrics**: Resource usage, database performance

### Alert Hierarchy
- **P0**: Complete system outage, data corruption
- **P1**: Trading system degradation, partial outages
- **P2**: Individual service issues, performance degradation
- **P3**: Minor issues, maintenance alerts

## Disaster Recovery

### Backup Strategy
- Database: Daily full backups, continuous WAL archiving
- Configuration: Version controlled, multiple environments
- Monitoring: Backup validation and restore testing

### Failover Procedures
- Database: Read replicas with automatic promotion
- Services: Multiple availability zones
- Data: Cross-region replication for critical data

## Development Guidelines

### Code Standards
- **Python**: Black formatting, isort imports, flake8 linting
- **Type Hints**: Required for all public interfaces
- **Documentation**: Docstrings for all public methods
- **Testing**: Minimum 80% code coverage

### Service Standards
- **Health Checks**: `/healthz` and `/readyz` endpoints
- **Metrics**: Prometheus exposition format
- **Logging**: Structured JSON with correlation IDs
- **Configuration**: Environment variable based

### API Design
- **REST**: For synchronous operations
- **Events**: For asynchronous notifications
- **Versioning**: URL path versioning (`/api/v1/`)
- **Documentation**: OpenAPI/Swagger specs
EOF
    
    echo -e "${GREEN}✅ Development documentation created${NC}"
    echo ""
}

# Function to run final verification
run_verification() {
    echo -e "${YELLOW}🔍 Running final verification...${NC}"
    
    # Check if key commands are available
    commands_to_check=("python3" "poetry" "docker" "git" "make" "curl" "jq")
    
    for cmd in "${commands_to_check[@]}"; do
        if command_exists "$cmd"; then
            echo -e "${GREEN}✅ $cmd available${NC}"
        else
            echo -e "${RED}❌ $cmd not found${NC}"
        fi
    done
    
    echo ""
    
    # Test project setup (if in project directory)
    if [ -f "pyproject.toml" ]; then
        echo -e "${YELLOW}Testing project setup...${NC}"
        
        if poetry check; then
            echo -e "${GREEN}✅ Poetry configuration valid${NC}"
        else
            echo -e "${RED}❌ Poetry configuration invalid${NC}"
        fi
        
        if [ -f ".env" ]; then
            echo -e "${GREEN}✅ Environment configuration exists${NC}"
        else
            echo -e "${YELLOW}⚠️  No .env file found${NC}"
        fi
        
        if [ -f "deploy/compose/docker-compose.yml" ]; then
            echo -e "${GREEN}✅ Docker Compose configuration exists${NC}"
        else
            echo -e "${YELLOW}⚠️  No Docker Compose configuration found${NC}"
        fi
    fi
    
    echo ""
}

# Main execution
main() {
    install_package_manager
    install_python
    install_poetry
    install_docker
    install_nodejs
    install_dev_tools
    install_database_clients
    setup_project
    create_dev_utilities
    setup_ide_configs
    create_dev_docs
    run_verification
    
    echo -e "${GREEN}🎉 EAFIX Development Environment Setup Complete!${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Restart your terminal or run: source ~/.bashrc"
    echo "2. Add development aliases: ./scripts/dev/setup-aliases.sh >> ~/.bashrc"
    echo "3. Start the development environment: make docker-up"
    echo "4. Run tests to verify everything works: make test-all"
    echo "5. Open the project in your IDE (VS Code config included)"
    echo ""
    echo -e "${BLUE}Quick Commands:${NC}"
    echo "- make docker-up          # Start all services"
    echo "- make health-check       # Check system health"
    echo "- make test-all           # Run all tests"
    echo "- make runbooks           # Open operational runbooks"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "- docs/development/getting-started.md"
    echo "- docs/development/architecture.md"
    echo "- docs/runbooks/index.md"
    echo ""
    echo -e "${YELLOW}⚠️  If you installed Docker, please log out and back in to apply group membership changes.${NC}"
}

# Run main function
main "$@"
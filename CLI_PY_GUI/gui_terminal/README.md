# CLI Multi-Rapid GUI Terminal

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://pypi.org/project/PyQt6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Enterprise-grade GUI terminal with PTY support, advanced security features, and seamless integration with the CLI Multi-Rapid platform.

## 🚀 Features

### Core Terminal Functionality
- **True PTY/ConPTY Support**: Cross-platform pseudo-terminal implementation
- **Advanced Terminal Emulation**: Full ANSI escape sequence support
- **Tabbed Interface**: Multiple terminal sessions with session management
- **Command History**: Persistent command history with search capabilities
- **Copy/Paste**: Intelligent clipboard integration with bracketed paste mode

### Enterprise Security
- **Policy-Based Security**: Configurable command filtering and validation
- **Resource Limits**: CPU, memory, and execution time constraints
- **Audit Logging**: Comprehensive audit trails with integrity verification
- **Compliance Rules**: Customizable security compliance enforcement
- **Real-time Monitoring**: Security violation detection and reporting

### Platform Integration
- **WebSocket Communication**: Real-time integration with CLI Multi-Rapid platform
- **Cost Tracking**: Automated cost monitoring with budget alerts
- **Enterprise Connectors**: JIRA, Slack, GitHub, and Microsoft Teams integration
- **Workflow Orchestration**: Advanced workflow execution and monitoring

### Advanced Features
- **Plugin System**: Extensible plugin architecture with hot-reloading
- **Theme Support**: Customizable themes and appearance settings
- **Session Persistence**: Save and restore terminal sessions
- **Performance Optimization**: Lazy loading and virtual scrolling
- **Cross-Platform**: Windows, macOS, and Linux support

## 📋 Requirements

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM recommended
- **Disk Space**: 100MB for installation

### Dependencies
- PyQt6 (GUI framework)
- pywinpty (Windows PTY support)
- ptyprocess (Unix PTY support)
- websockets (Real-time communication)
- pydantic (Data validation)
- pyyaml (Configuration management)

## 🔧 Installation

### From Source
```bash
# Clone the repository
git clone https://github.com/cli-multi-rapid/gui-terminal.git
cd gui-terminal

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Using pip
```bash
pip install cli-multi-rapid-gui-terminal
```

## 🚦 Quick Start

### Basic Usage
```bash
# Start the GUI terminal
gui-terminal

# Start with specific shell
gui-terminal --shell bash

# Start in specific directory
gui-terminal --working-dir /home/user/projects

# Enable debug logging
gui-terminal --log-level DEBUG
```

### Configuration
Create a configuration file at `~/.gui_terminal/config.yaml`:

```yaml
terminal:
  default_shell: "auto"
  font_family: "Consolas"
  font_size: 12
  rows: 24
  cols: 80

security:
  audit_logging: true
  policy_file: "security_policies.yaml"
  resource_limits:
    max_memory_mb: 512
    max_cpu_percent: 50

platform_integration:
  websocket_url: "ws://localhost:8000/ws"
  cost_tracking_enabled: true
```

## 📖 Documentation

### User Guides
- [User Guide](docs/user_guide.md) - Complete user documentation
- [Administrator Guide](docs/administrator_guide.md) - System administration
- [Plugin Development](docs/plugin_development.md) - Creating custom plugins

### Technical Documentation
- [API Reference](docs/api_reference.md) - Complete API documentation
- [Security Guide](docs/security_guide.md) - Security configuration
- [Integration Guide](docs/integration_guide.md) - Platform integration

## 🔒 Security

### Security Features
- **Command Filtering**: Whitelist/blacklist command validation
- **Resource Limits**: Prevent resource abuse
- **Audit Trails**: Comprehensive logging with integrity verification
- **Policy Enforcement**: Configurable security policies
- **Violation Detection**: Real-time security monitoring

### Default Security Policy
The terminal ships with a secure default configuration:
- Whitelist-based command filtering
- Resource limits (512MB memory, 50% CPU)
- Audit logging enabled
- Dangerous pattern detection

### Customizing Security
Create `~/.gui_terminal/security_policies.yaml`:

```yaml
command_filtering:
  mode: "whitelist"
  allowed_commands:
    - "ls"
    - "pwd"
    - "cd"
    - "python"
    - "git"

resource_limits:
  max_memory_mb: 1024
  max_cpu_percent: 75
  max_execution_time: 600

compliance_rules:
  prevent_privilege_escalation:
    enabled: true
    patterns: ["sudo", "su", "runas"]
    action: "block"
```

## 🔌 Plugin Development

### Creating a Plugin
```python
from gui_terminal.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self, name, version="1.0.0"):
        super().__init__(name, version)

    def initialize(self, config):
        self.logger.info("MyPlugin initialized")
        return True

    def get_info(self):
        return {
            "name": "My Plugin",
            "version": "1.0.0",
            "description": "Example plugin",
            "author": "Your Name"
        }

    def on_command_executed(self, command, session_id, context):
        self.logger.info(f"Command executed: {command}")

# Plugin metadata
PLUGIN_INFO = {
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "Example plugin for demonstration",
    "author": "Your Name",
    "type": "base"
}
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m security

# Run with coverage
pytest --cov=gui_terminal --cov-report=html

# Run performance tests
pytest -m "not expensive"  # Skip expensive tests
```

### Test Categories
- **Unit Tests**: Core component testing
- **Integration Tests**: Platform integration testing
- **Security Tests**: Security policy validation
- **UI Tests**: GUI functionality testing
- **Performance Tests**: Performance and scalability testing

## 🚀 Development

### Development Setup
```bash
# Clone the repository
git clone https://github.com/cli-multi-rapid/gui-terminal.git
cd gui-terminal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run code quality checks
black src tests
ruff src tests
mypy src
```

### Project Structure
```
gui-terminal/
├── src/gui_terminal/          # Main source code
│   ├── core/                  # Core terminal components
│   ├── ui/                    # User interface components
│   ├── security/              # Security framework
│   ├── config/                # Configuration management
│   ├── plugins/               # Plugin system
│   └── integrations/          # Platform integrations
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── security/              # Security tests
├── docs/                      # Documentation
└── config/                    # Configuration files
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Reporting Issues
- [Bug Reports](https://github.com/cli-multi-rapid/gui-terminal/issues/new?template=bug_report.md)
- [Feature Requests](https://github.com/cli-multi-rapid/gui-terminal/issues/new?template=feature_request.md)
- [Security Issues](mailto:security@cli-multi-rapid.com)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PyQt](https://www.riverbankcomputing.com/software/pyqt/) for the excellent GUI framework
- [winpty](https://github.com/rprichard/winpty) for Windows PTY support
- [CLI Multi-Rapid Platform](https://cli-multi-rapid.com) for enterprise integration

## 📞 Support

- **Documentation**: [docs.cli-multi-rapid.com](https://docs.cli-multi-rapid.com)
- **Community**: [Discord](https://discord.gg/cli-multi-rapid)
- **Enterprise Support**: [enterprise@cli-multi-rapid.com](mailto:enterprise@cli-multi-rapid.com)

---

**CLI Multi-Rapid GUI Terminal** - Enterprise-grade terminal emulation with advanced security and platform integration.
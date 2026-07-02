"""
Settings Manager for CLI Multi-Rapid GUI Terminal
Advanced configuration management with validation and schema support
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class TerminalConfig:
    """Terminal-specific configuration"""
    default_shell: str = "auto"
    startup_command: Optional[str] = None
    working_directory: str = "~"
    rows: int = 24
    cols: int = 80
    font_family: str = "Consolas"
    font_size: int = 12
    enable_unicode: bool = True
    enable_ansi_colors: bool = True


@dataclass
class SecurityConfig:
    """Security configuration"""
    policy_file: str = "security_policies.yaml"
    audit_logging: bool = True
    resource_limits: Dict[str, Union[int, float]] = field(default_factory=lambda: {
        "max_memory_mb": 512,
        "max_cpu_percent": 50,
        "max_execution_time": 300
    })
    command_filtering_enabled: bool = True
    require_confirmation: list = field(default_factory=lambda: ["rm", "del", "format", "sudo"])


@dataclass
class PlatformIntegrationConfig:
    """Platform integration configuration"""
    websocket_url: str = "ws://localhost:8000/ws"
    cost_tracking_enabled: bool = True
    enterprise_integrations: Dict[str, bool] = field(default_factory=lambda: {
        "jira_enabled": False,
        "slack_enabled": False,
        "github_enabled": False,
        "teams_enabled": False
    })
    api_key: str = ""
    auth_token: str = ""


@dataclass
class UIConfig:
    """User interface configuration"""
    theme: str = "default"
    show_status_bar: bool = True
    show_toolbar: bool = True
    enable_tabs: bool = True
    window_opacity: float = 1.0
    always_on_top: bool = False


@dataclass
class PluginConfig:
    """Plugin system configuration"""
    enabled: bool = True
    auto_load: bool = True
    plugin_directories: list = field(default_factory=lambda: [
        "~/.gui_terminal/plugins",
        "/opt/gui_terminal/plugins"
    ])
    disabled_plugins: list = field(default_factory=list)


@dataclass
class PerformanceConfig:
    """Performance and optimization configuration"""
    max_buffer_chars: int = 1_000_000
    poll_interval_ms: int = 30
    enable_lazy_loading: bool = True
    enable_virtual_scrolling: bool = True
    max_concurrent_sessions: int = 10


@dataclass
class ApplicationConfig:
    """Main application configuration"""
    name: str = "CLI Multi-Rapid GUI Terminal"
    version: str = "1.0.0"
    terminal: TerminalConfig = field(default_factory=TerminalConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    platform_integration: PlatformIntegrationConfig = field(default_factory=PlatformIntegrationConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    debug_mode: bool = False


class SettingsManager:
    """
    Advanced settings manager with schema validation and hot-reloading
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = ApplicationConfig()
        self.watchers = []  # File system watchers for hot-reload

        self.load_config()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        config_dir = Path.home() / ".gui_terminal"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.yaml")

    def load_config(self):
        """Load configuration from file"""
        try:
            config_file = Path(self.config_path)

            if not config_file.exists():
                logger.info(f"Config file not found, creating default: {self.config_path}")
                self.save_config()
                return

            # Determine file format
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            # Merge with default configuration
            if data:
                self._merge_config(self.config, data)

            logger.info(f"Configuration loaded from: {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Using default configuration")

    def save_config(self):
        """Save current configuration to file"""
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert config to dictionary
            config_dict = asdict(self.config)

            # Save based on file extension
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2)

            logger.info(f"Configuration saved to: {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def _merge_config(self, target_config, source_data):
        """Recursively merge configuration data"""
        for key, value in source_data.items():
            if hasattr(target_config, key):
                target_attr = getattr(target_config, key)

                # Handle nested dataclass objects
                if hasattr(target_attr, '__dataclass_fields__'):
                    if isinstance(value, dict):
                        self._merge_config(target_attr, value)
                else:
                    # Direct assignment for simple values
                    setattr(target_config, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")

    def get_terminal_config(self) -> Dict[str, Any]:
        """Get terminal configuration as dictionary"""
        return asdict(self.config.terminal)

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration as dictionary"""
        return asdict(self.config.security)

    def get_platform_config(self) -> Dict[str, Any]:
        """Get platform integration configuration as dictionary"""
        return asdict(self.config.platform_integration)

    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration as dictionary"""
        return asdict(self.config.ui)

    def get_plugin_config(self) -> Dict[str, Any]:
        """Get plugin configuration as dictionary"""
        return asdict(self.config.plugins)

    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration as dictionary"""
        return asdict(self.config.performance)

    def update_config(self, section: str, key: str, value: Any):
        """Update a specific configuration value"""
        try:
            if hasattr(self.config, section):
                section_obj = getattr(self.config, section)
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)
                    logger.info(f"Updated {section}.{key} = {value}")
                else:
                    logger.error(f"Unknown configuration key: {section}.{key}")
            else:
                logger.error(f"Unknown configuration section: {section}")
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = ApplicationConfig()
        logger.info("Configuration reset to defaults")

    def validate_config(self) -> tuple[bool, list]:
        """Validate current configuration"""
        errors = []

        # Validate terminal configuration
        if self.config.terminal.rows < 1 or self.config.terminal.rows > 200:
            errors.append("Terminal rows must be between 1 and 200")

        if self.config.terminal.cols < 1 or self.config.terminal.cols > 500:
            errors.append("Terminal columns must be between 1 and 500")

        if self.config.terminal.font_size < 6 or self.config.terminal.font_size > 72:
            errors.append("Font size must be between 6 and 72")

        # Validate security configuration
        if self.config.security.resource_limits["max_memory_mb"] < 64:
            errors.append("Max memory must be at least 64 MB")

        if self.config.security.resource_limits["max_execution_time"] < 1:
            errors.append("Max execution time must be at least 1 second")

        # Validate performance configuration
        if self.config.performance.max_buffer_chars < 1000:
            errors.append("Max buffer chars must be at least 1000")

        if self.config.performance.poll_interval_ms < 10:
            errors.append("Poll interval must be at least 10ms")

        # Validate UI configuration
        if not (0.1 <= self.config.ui.window_opacity <= 1.0):
            errors.append("Window opacity must be between 0.1 and 1.0")

        return len(errors) == 0, errors

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        return {
            "config_path": self.config_path,
            "terminal": {
                "shell": self.config.terminal.default_shell,
                "size": f"{self.config.terminal.cols}x{self.config.terminal.rows}",
                "font": f"{self.config.terminal.font_family} {self.config.terminal.font_size}pt"
            },
            "security": {
                "enabled": self.config.security.audit_logging,
                "policy_file": self.config.security.policy_file
            },
            "platform": {
                "websocket": self.config.platform_integration.websocket_url,
                "cost_tracking": self.config.platform_integration.cost_tracking_enabled
            },
            "plugins": {
                "enabled": self.config.plugins.enabled,
                "count": len(self.config.plugins.plugin_directories)
            }
        }

    def export_config(self, export_path: str, format: str = "yaml"):
        """Export configuration to file"""
        try:
            export_file = Path(export_path)
            config_dict = asdict(self.config)

            if format.lower() == "yaml":
                with open(export_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2)

            logger.info(f"Configuration exported to: {export_path}")

        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")

    def import_config(self, import_path: str):
        """Import configuration from file"""
        try:
            import_file = Path(import_path)

            if not import_file.exists():
                raise FileNotFoundError(f"Import file not found: {import_path}")

            # Load configuration
            if import_file.suffix.lower() in ['.yaml', '.yml']:
                with open(import_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                with open(import_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            # Create new config and merge
            new_config = ApplicationConfig()
            if data:
                self._merge_config(new_config, data)

            # Validate before applying
            old_config = self.config
            self.config = new_config
            is_valid, errors = self.validate_config()

            if is_valid:
                self.save_config()
                logger.info(f"Configuration imported from: {import_path}")
            else:
                self.config = old_config
                raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise
"""
Base Plugin Interface
Abstract base class for all GUI terminal plugins
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """
    Abstract base class for all plugins
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.enabled = True
        self.config = {}
        self.logger = logging.getLogger(f"plugin.{name}")

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with configuration

        Args:
            config: Plugin configuration dictionary

        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information

        Returns:
            dict: Plugin information including name, version, description, etc.
        """
        pass

    def shutdown(self):
        """
        Shutdown the plugin and clean up resources
        """
        self.logger.info(f"Plugin {self.name} shutting down")

    def enable(self):
        """Enable the plugin"""
        self.enabled = True
        self.logger.info(f"Plugin {self.name} enabled")

    def disable(self):
        """Disable the plugin"""
        self.enabled = False
        self.logger.info(f"Plugin {self.name} disabled")

    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.enabled

    def update_config(self, config: Dict[str, Any]):
        """Update plugin configuration"""
        self.config.update(config)

    # Event handlers (optional to override)
    def on_terminal_start(self, session_id: str, context: Dict[str, Any]):
        """Called when a terminal session starts"""
        pass

    def on_terminal_stop(self, session_id: str, context: Dict[str, Any]):
        """Called when a terminal session stops"""
        pass

    def on_command_executed(self, command: str, session_id: str, context: Dict[str, Any]):
        """Called when a command is executed"""
        pass

    def on_output_received(self, output: str, session_id: str, context: Dict[str, Any]):
        """Called when output is received from terminal"""
        pass

    def on_error_occurred(self, error: str, session_id: str, context: Dict[str, Any]):
        """Called when an error occurs"""
        pass

    def on_platform_event(self, event: Dict[str, Any]):
        """Called when a platform event is received"""
        pass

    def on_cost_update(self, cost_data: Dict[str, Any]):
        """Called when cost data is updated"""
        pass

    def on_security_violation(self, violation: Dict[str, Any]):
        """Called when a security violation occurs"""
        pass


class UIPlugin(BasePlugin):
    """
    Base class for UI plugins that can add interface elements
    """

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """
        Get menu items to add to the application menu

        Returns:
            list: List of menu item definitions
        """
        return []

    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        """
        Get toolbar items to add to the application toolbar

        Returns:
            list: List of toolbar item definitions
        """
        return []

    def get_context_menu_items(self) -> List[Dict[str, Any]]:
        """
        Get context menu items for terminal context menu

        Returns:
            list: List of context menu item definitions
        """
        return []

    def create_settings_widget(self):
        """
        Create settings widget for plugin configuration

        Returns:
            QWidget or None: Settings widget or None if no settings
        """
        return None


class CommandPlugin(BasePlugin):
    """
    Base class for plugins that add custom commands
    """

    @abstractmethod
    def get_commands(self) -> Dict[str, Callable]:
        """
        Get custom commands provided by this plugin

        Returns:
            dict: Dictionary of command name -> handler function
        """
        pass

    def handle_command(self, command: str, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle custom command execution

        Args:
            command: Command name
            args: Command arguments
            context: Execution context

        Returns:
            dict: Command execution result
        """
        commands = self.get_commands()
        if command in commands:
            try:
                return commands[command](args, context)
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        else:
            return {
                'success': False,
                'error': f'Unknown command: {command}'
            }


class IntegrationPlugin(BasePlugin):
    """
    Base class for plugins that integrate with external services
    """

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the integrated service

        Returns:
            dict: Service information
        """
        return {}

    def test_connection(self) -> bool:
        """
        Test connection to the integrated service

        Returns:
            bool: True if connection successful, False otherwise
        """
        return False

    def send_notification(self, message: str, level: str = "info") -> bool:
        """
        Send notification through the integrated service

        Args:
            message: Notification message
            level: Notification level (info, warning, error)

        Returns:
            bool: True if notification sent successfully
        """
        return False

    def upload_data(self, data: Dict[str, Any]) -> bool:
        """
        Upload data to the integrated service

        Args:
            data: Data to upload

        Returns:
            bool: True if upload successful
        """
        return False


class SecurityPlugin(BasePlugin):
    """
    Base class for security-related plugins
    """

    def validate_command(self, command: str, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate command for security compliance

        Args:
            command: Command to validate
            args: Command arguments
            context: Execution context

        Returns:
            dict: Validation result with 'allowed' boolean and 'violations' list
        """
        return {
            'allowed': True,
            'violations': []
        }

    def scan_output(self, output: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan command output for security issues

        Args:
            output: Command output to scan
            context: Execution context

        Returns:
            dict: Scan result with 'issues' list
        """
        return {
            'issues': []
        }

    def get_security_rules(self) -> List[Dict[str, Any]]:
        """
        Get security rules provided by this plugin

        Returns:
            list: List of security rule definitions
        """
        return []
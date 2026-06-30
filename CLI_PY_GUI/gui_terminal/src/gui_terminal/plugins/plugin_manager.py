"""
Plugin Manager
Advanced plugin system with dependency resolution and hot-reloading
"""

import os
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Callable
import logging

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QFileSystemWatcher
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal, QFileSystemWatcher
    PYQT_VERSION = 5

from .base_plugin import BasePlugin, UIPlugin, CommandPlugin, IntegrationPlugin, SecurityPlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for plugin metadata and dependencies"""

    def __init__(self):
        self.plugins = {}
        self.dependencies = {}

    def register_plugin(self, plugin_id: str, plugin_info: Dict[str, Any]):
        """Register plugin information"""
        self.plugins[plugin_id] = plugin_info
        self.dependencies[plugin_id] = plugin_info.get('dependencies', [])

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin information"""
        return self.plugins.get(plugin_id)

    def get_load_order(self) -> List[str]:
        """Get plugins in dependency-resolved load order"""
        visited = set()
        temp_visited = set()
        result = []

        def visit(plugin_id: str):
            if plugin_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving {plugin_id}")
            if plugin_id in visited:
                return

            temp_visited.add(plugin_id)

            # Visit dependencies first
            for dep in self.dependencies.get(plugin_id, []):
                if dep in self.plugins:
                    visit(dep)

            temp_visited.remove(plugin_id)
            visited.add(plugin_id)
            result.append(plugin_id)

        for plugin_id in self.plugins:
            if plugin_id not in visited:
                visit(plugin_id)

        return result

    def check_dependencies(self, plugin_id: str) -> List[str]:
        """Check missing dependencies for a plugin"""
        missing = []
        for dep in self.dependencies.get(plugin_id, []):
            if dep not in self.plugins:
                missing.append(dep)
        return missing


class PluginManager(QObject):
    """
    Advanced plugin manager with hot-reloading and dependency resolution
    """

    plugin_loaded = pyqtSignal(str)  # plugin_id
    plugin_unloaded = pyqtSignal(str)  # plugin_id
    plugin_error = pyqtSignal(str, str)  # plugin_id, error_message

    def __init__(self, plugin_directories: Optional[List[str]] = None):
        super().__init__()

        # Plugin storage
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_modules: Dict[str, Any] = {}
        self.registry = PluginRegistry()

        # Configuration
        self.plugin_directories = plugin_directories or self._get_default_directories()
        self.enabled_plugins = set()
        self.disabled_plugins = set()

        # File system watcher for hot-reloading
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self._on_file_changed)

        # Event handlers
        self.event_handlers = {
            'terminal_start': [],
            'terminal_stop': [],
            'command_executed': [],
            'output_received': [],
            'error_occurred': [],
            'platform_event': [],
            'cost_update': [],
            'security_violation': []
        }

        # Load plugins
        self.discover_plugins()
        self.load_all_plugins()

    def _get_default_directories(self) -> List[str]:
        """Get default plugin directories"""
        return [
            str(Path.home() / ".gui_terminal" / "plugins"),
            str(Path(__file__).parent / "builtin"),
            str(Path.cwd() / "plugins")
        ]

    def discover_plugins(self):
        """Discover available plugins"""
        for directory in self.plugin_directories:
            if not Path(directory).exists():
                continue

            for plugin_path in Path(directory).iterdir():
                if plugin_path.is_file() and plugin_path.suffix == '.py':
                    self._discover_file_plugin(plugin_path)
                elif plugin_path.is_dir() and (plugin_path / '__init__.py').exists():
                    self._discover_directory_plugin(plugin_path)

    def _discover_file_plugin(self, plugin_path: Path):
        """Discover plugin from Python file"""
        try:
            plugin_id = plugin_path.stem

            # Try to load plugin metadata
            spec = importlib.util.spec_from_file_location(plugin_id, plugin_path)
            if not spec or not spec.loader:
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get plugin info
            plugin_info = getattr(module, 'PLUGIN_INFO', {
                'name': plugin_id,
                'version': '1.0.0',
                'description': 'No description provided',
                'author': 'Unknown',
                'type': 'base'
            })

            plugin_info['path'] = str(plugin_path)
            plugin_info['module'] = module

            self.registry.register_plugin(plugin_id, plugin_info)
            logger.info(f"Discovered plugin: {plugin_id}")

        except Exception as e:
            logger.warning(f"Failed to discover plugin {plugin_path}: {e}")

    def _discover_directory_plugin(self, plugin_path: Path):
        """Discover plugin from directory"""
        try:
            plugin_id = plugin_path.name

            # Load plugin metadata
            metadata_file = plugin_path / 'plugin.json'
            if metadata_file.exists():
                with open(metadata_file) as f:
                    plugin_info = json.load(f)
            else:
                plugin_info = {
                    'name': plugin_id,
                    'version': '1.0.0',
                    'description': 'No description provided',
                    'author': 'Unknown',
                    'type': 'base'
                }

            plugin_info['path'] = str(plugin_path)

            self.registry.register_plugin(plugin_id, plugin_info)
            logger.info(f"Discovered plugin: {plugin_id}")

        except Exception as e:
            logger.warning(f"Failed to discover plugin {plugin_path}: {e}")

    def load_all_plugins(self):
        """Load all discovered plugins in dependency order"""
        load_order = self.registry.get_load_order()

        for plugin_id in load_order:
            if plugin_id not in self.disabled_plugins:
                self.load_plugin(plugin_id)

    def load_plugin(self, plugin_id: str) -> bool:
        """Load a specific plugin"""
        if plugin_id in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} already loaded")
            return True

        plugin_info = self.registry.get_plugin_info(plugin_id)
        if not plugin_info:
            logger.error(f"Plugin {plugin_id} not found")
            return False

        # Check dependencies
        missing_deps = self.registry.check_dependencies(plugin_id)
        if missing_deps:
            error_msg = f"Missing dependencies for {plugin_id}: {missing_deps}"
            logger.error(error_msg)
            self.plugin_error.emit(plugin_id, error_msg)
            return False

        try:
            # Load plugin module
            plugin_module = self._load_plugin_module(plugin_info)
            if not plugin_module:
                return False

            # Find plugin class
            plugin_class = self._find_plugin_class(plugin_module)
            if not plugin_class:
                error_msg = f"No plugin class found in {plugin_id}"
                logger.error(error_msg)
                self.plugin_error.emit(plugin_id, error_msg)
                return False

            # Create plugin instance
            plugin_instance = plugin_class(plugin_id, plugin_info.get('version', '1.0.0'))

            # Initialize plugin
            config = plugin_info.get('config', {})
            if not plugin_instance.initialize(config):
                error_msg = f"Plugin {plugin_id} initialization failed"
                logger.error(error_msg)
                self.plugin_error.emit(plugin_id, error_msg)
                return False

            # Register plugin
            self.loaded_plugins[plugin_id] = plugin_instance
            self.plugin_modules[plugin_id] = plugin_module
            self.enabled_plugins.add(plugin_id)

            # Register event handlers
            self._register_event_handlers(plugin_id, plugin_instance)

            # Watch plugin file for changes
            plugin_path = plugin_info.get('path', '')
            if plugin_path and Path(plugin_path).is_file():
                self.file_watcher.addPath(plugin_path)

            logger.info(f"Plugin {plugin_id} loaded successfully")
            self.plugin_loaded.emit(plugin_id)
            return True

        except Exception as e:
            error_msg = f"Failed to load plugin {plugin_id}: {e}"
            logger.error(error_msg)
            self.plugin_error.emit(plugin_id, error_msg)
            return False

    def _load_plugin_module(self, plugin_info: Dict[str, Any]):
        """Load plugin module from file or directory"""
        plugin_path = Path(plugin_info['path'])

        if plugin_path.is_file():
            # Load from Python file
            spec = importlib.util.spec_from_file_location(
                plugin_info['name'], plugin_path
            )
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        elif plugin_path.is_dir():
            # Load from directory
            sys.path.insert(0, str(plugin_path.parent))
            try:
                module = importlib.import_module(plugin_path.name)
                return module
            finally:
                sys.path.pop(0)

        return None

    def _find_plugin_class(self, module) -> Optional[Type[BasePlugin]]:
        """Find plugin class in module"""
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                issubclass(obj, BasePlugin) and
                obj != BasePlugin):
                return obj
        return None

    def _register_event_handlers(self, plugin_id: str, plugin: BasePlugin):
        """Register plugin event handlers"""
        handlers = {
            'terminal_start': plugin.on_terminal_start,
            'terminal_stop': plugin.on_terminal_stop,
            'command_executed': plugin.on_command_executed,
            'output_received': plugin.on_output_received,
            'error_occurred': plugin.on_error_occurred,
            'platform_event': plugin.on_platform_event,
            'cost_update': plugin.on_cost_update,
            'security_violation': plugin.on_security_violation
        }

        for event_type, handler in handlers.items():
            self.event_handlers[event_type].append((plugin_id, handler))

    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a specific plugin"""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} not loaded")
            return False

        try:
            # Get plugin instance
            plugin = self.loaded_plugins[plugin_id]

            # Shutdown plugin
            plugin.shutdown()

            # Unregister event handlers
            for event_type in self.event_handlers:
                self.event_handlers[event_type] = [
                    (pid, handler) for pid, handler in self.event_handlers[event_type]
                    if pid != plugin_id
                ]

            # Remove from loaded plugins
            del self.loaded_plugins[plugin_id]
            if plugin_id in self.plugin_modules:
                del self.plugin_modules[plugin_id]

            self.enabled_plugins.discard(plugin_id)

            # Stop watching file
            plugin_info = self.registry.get_plugin_info(plugin_id)
            if plugin_info:
                plugin_path = plugin_info.get('path', '')
                if plugin_path and Path(plugin_path).is_file():
                    self.file_watcher.removePath(plugin_path)

            logger.info(f"Plugin {plugin_id} unloaded successfully")
            self.plugin_unloaded.emit(plugin_id)
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False

    def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a plugin"""
        if plugin_id in self.loaded_plugins:
            self.unload_plugin(plugin_id)

        # Rediscover plugin
        plugin_info = self.registry.get_plugin_info(plugin_id)
        if plugin_info:
            plugin_path = Path(plugin_info['path'])
            if plugin_path.is_file():
                self._discover_file_plugin(plugin_path)
            elif plugin_path.is_dir():
                self._discover_directory_plugin(plugin_path)

        return self.load_plugin(plugin_id)

    def _on_file_changed(self, file_path: str):
        """Handle plugin file change for hot-reloading"""
        # Find plugin by file path
        plugin_id = None
        for pid, plugin_info in self.registry.plugins.items():
            if plugin_info.get('path') == file_path:
                plugin_id = pid
                break

        if plugin_id:
            logger.info(f"Plugin file changed: {plugin_id}, reloading...")
            self.reload_plugin(plugin_id)

    def get_loaded_plugins(self) -> Dict[str, BasePlugin]:
        """Get all loaded plugins"""
        return self.loaded_plugins.copy()

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get specific plugin instance"""
        return self.loaded_plugins.get(plugin_id)

    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        plugin = self.loaded_plugins.get(plugin_id)
        if plugin:
            plugin.enable()
            self.enabled_plugins.add(plugin_id)
            self.disabled_plugins.discard(plugin_id)
            return True
        return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        plugin = self.loaded_plugins.get(plugin_id)
        if plugin:
            plugin.disable()
            self.disabled_plugins.add(plugin_id)
            self.enabled_plugins.discard(plugin_id)
            return True
        return False

    def dispatch_event(self, event_type: str, *args, **kwargs):
        """Dispatch event to all registered handlers"""
        if event_type not in self.event_handlers:
            return

        for plugin_id, handler in self.event_handlers[event_type]:
            plugin = self.loaded_plugins.get(plugin_id)
            if plugin and plugin.is_enabled():
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in plugin {plugin_id} event handler: {e}")

    def get_ui_plugins(self) -> List[UIPlugin]:
        """Get all loaded UI plugins"""
        return [p for p in self.loaded_plugins.values() if isinstance(p, UIPlugin)]

    def get_command_plugins(self) -> List[CommandPlugin]:
        """Get all loaded command plugins"""
        return [p for p in self.loaded_plugins.values() if isinstance(p, CommandPlugin)]

    def get_integration_plugins(self) -> List[IntegrationPlugin]:
        """Get all loaded integration plugins"""
        return [p for p in self.loaded_plugins.values() if isinstance(p, IntegrationPlugin)]

    def get_security_plugins(self) -> List[SecurityPlugin]:
        """Get all loaded security plugins"""
        return [p for p in self.loaded_plugins.values() if isinstance(p, SecurityPlugin)]

    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins"""
        status = {}

        for plugin_id, plugin_info in self.registry.plugins.items():
            is_loaded = plugin_id in self.loaded_plugins
            is_enabled = plugin_id in self.enabled_plugins

            status[plugin_id] = {
                'name': plugin_info.get('name', plugin_id),
                'version': plugin_info.get('version', '1.0.0'),
                'type': plugin_info.get('type', 'base'),
                'loaded': is_loaded,
                'enabled': is_enabled,
                'path': plugin_info.get('path', ''),
                'dependencies': plugin_info.get('dependencies', []),
                'missing_dependencies': self.registry.check_dependencies(plugin_id) if not is_loaded else []
            }

        return status
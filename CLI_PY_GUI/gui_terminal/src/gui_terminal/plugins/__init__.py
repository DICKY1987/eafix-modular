"""
Plugin system for CLI Multi-Rapid GUI Terminal
"""

from .plugin_manager import PluginManager
from .base_plugin import BasePlugin

__all__ = [
    "PluginManager",
    "BasePlugin"
]
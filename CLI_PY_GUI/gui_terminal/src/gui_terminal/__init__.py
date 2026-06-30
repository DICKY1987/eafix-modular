"""
CLI Multi-Rapid GUI Terminal - Enterprise Edition
A comprehensive enterprise-grade GUI terminal with PTY support and platform integration.
"""

__version__ = "1.0.0"
__author__ = "CLI Multi-Rapid Team"

from .main import main
from .core.terminal_widget import EnterpriseTerminalWidget
from .ui.main_window import MainWindow

__all__ = [
    "main",
    "EnterpriseTerminalWidget",
    "MainWindow",
]
"""
Main Window Implementation
Enterprise GUI terminal main window with tabbed sessions and advanced features
"""

import os
import sys
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QTabWidget, QMenuBar, QMenu, QStatusBar, QToolBar,
                               QAction, QMessageBox, QDialog, QFileDialog,
                               QSplitter, QTextEdit, QLabel, QPushButton)
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSettings
    from PyQt6.QtGui import QIcon, QKeySequence, QFont, QAction as QActionAlias
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QTabWidget, QMenuBar, QMenu, QStatusBar, QToolBar,
                               QAction, QMessageBox, QDialog, QFileDialog,
                               QSplitter, QTextEdit, QLabel, QPushButton)
    from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSettings
    from PyQt5.QtGui import QIcon, QKeySequence, QFont
    PYQT_VERSION = 5

from ..core.terminal_widget import EnterpriseTerminalWidget
from ..config.settings import SettingsManager
from ..security.policy_manager import SecurityPolicyManager
from .status_bar import StatusBar
from .toolbar import Toolbar

logger = logging.getLogger(__name__)


class TabManager(QTabWidget):
    """Enhanced tab manager for terminal sessions"""

    tab_closed = pyqtSignal(int)
    tab_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

        # Connections
        self.tabCloseRequested.connect(self._close_tab)
        self.currentChanged.connect(self.tab_changed.emit)

    def _close_tab(self, index: int):
        """Handle tab close request"""
        if self.count() <= 1:
            # Don't close the last tab
            return

        widget = self.widget(index)
        if widget:
            # Stop terminal session if active
            if hasattr(widget, 'pty_backend') and widget.pty_backend.is_session_active():
                reply = QMessageBox.question(
                    self, "Close Tab",
                    "Terminal session is active. Close anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Clean up and remove tab
            if hasattr(widget, 'stop_session'):
                widget.stop_session()

            self.removeTab(index)
            widget.deleteLater()
            self.tab_closed.emit(index)

    def add_terminal_tab(self, title: str = "Terminal") -> EnterpriseTerminalWidget:
        """Add a new terminal tab"""
        terminal_widget = EnterpriseTerminalWidget()
        index = self.addTab(terminal_widget, title)
        self.setCurrentIndex(index)
        return terminal_widget

    def get_current_terminal(self) -> Optional[EnterpriseTerminalWidget]:
        """Get currently active terminal widget"""
        current_widget = self.currentWidget()
        if isinstance(current_widget, EnterpriseTerminalWidget):
            return current_widget
        return None


class MainWindow(QMainWindow):
    """
    Main application window with enterprise features
    """

    def __init__(self, settings_manager: Optional[SettingsManager] = None,
                 security_manager: Optional[SecurityPolicyManager] = None):
        super().__init__()

        # Dependency injection
        self.settings_manager = settings_manager
        self.security_manager = security_manager

        # Application state
        self.settings = QSettings("CLI Multi-Rapid", "GUI Terminal")
        self.session_counter = 1

        # UI components
        self.tab_manager = None
        self.status_bar_widget = None
        self.toolbar_widget = None
        self.splitter = None
        self.info_panel = None

        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second

        self.setup_ui()
        self.setup_menus()
        self.setup_shortcuts()
        self.setup_connections()
        self.restore_window_state()

        logger.info("Main window initialized")

    def setup_ui(self):
        """Setup the main user interface"""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for terminal and info panel
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tab manager for terminals
        self.tab_manager = TabManager()
        self.splitter.addWidget(self.tab_manager)

        # Info panel (initially hidden)
        self.info_panel = QTextEdit()
        self.info_panel.setMaximumWidth(300)
        self.info_panel.hide()
        self.splitter.addWidget(self.info_panel)

        layout.addWidget(self.splitter)

        # Create initial terminal tab
        self.add_new_tab()

        # Status bar
        self.status_bar_widget = StatusBar()
        self.setStatusBar(self.status_bar_widget)

        # Toolbar
        self.toolbar_widget = Toolbar()
        self.addToolBar(self.toolbar_widget)

        # Window properties
        self.setWindowTitle("CLI Multi-Rapid GUI Terminal")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        # Apply theme
        self.apply_theme()

    def setup_menus(self):
        """Setup application menus"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_tab_action = QAction("&New Tab", self)
        new_tab_action.setShortcut(QKeySequence.StandardKey.AddTab)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

        close_tab_action = QAction("&Close Tab", self)
        if PYQT_VERSION == 6:
            close_tab_action.setShortcut(QKeySequence.StandardKey.Close)
        else:
            close_tab_action.setShortcut(QKeySequence.Close)
        close_tab_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_tab_action)

        file_menu.addSeparator()

        preferences_action = QAction("&Preferences", self)
        if PYQT_VERSION == 6:
            preferences_action.setShortcut(QKeySequence.StandardKey.Preferences)
        else:
            preferences_action.setShortcut(QKeySequence("Ctrl+,"))
        preferences_action.triggered.connect(self.show_preferences)
        file_menu.addAction(preferences_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy_selection)
        edit_menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.paste_clipboard)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        clear_action = QAction("C&lear", self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.triggered.connect(self.clear_terminal)
        edit_menu.addAction(clear_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        fullscreen_action = QAction("&Full Screen", self)
        fullscreen_action.setShortcut(QKeySequence.StandardKey.FullScreen)
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        info_panel_action = QAction("&Info Panel", self)
        info_panel_action.setShortcut(QKeySequence("Ctrl+I"))
        info_panel_action.setCheckable(True)
        info_panel_action.triggered.connect(self.toggle_info_panel)
        view_menu.addAction(info_panel_action)

        # Terminal menu
        terminal_menu = menubar.addMenu("&Terminal")

        start_session_action = QAction("&Start Session", self)
        start_session_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        start_session_action.triggered.connect(self.start_terminal_session)
        terminal_menu.addAction(start_session_action)

        stop_session_action = QAction("S&top Session", self)
        stop_session_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        stop_session_action.triggered.connect(self.stop_terminal_session)
        terminal_menu.addAction(stop_session_action)

        terminal_menu.addSeparator()

        interrupt_action = QAction("&Interrupt (Ctrl+C)", self)
        interrupt_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        interrupt_action.triggered.connect(self.send_interrupt)
        terminal_menu.addAction(interrupt_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_shortcuts(self):
        """Setup additional keyboard shortcuts"""
        # Tab navigation
        for i in range(1, 10):
            shortcut = QKeySequence(f"Ctrl+{i}")
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked, idx=i-1: self.switch_to_tab(idx))
            self.addAction(action)

    def setup_connections(self):
        """Setup signal connections"""
        # Tab manager connections
        self.tab_manager.tab_closed.connect(self.on_tab_closed)
        self.tab_manager.tab_changed.connect(self.on_tab_changed)

        # Toolbar connections
        self.toolbar_widget.new_tab_requested.connect(self.add_new_tab)
        self.toolbar_widget.close_tab_requested.connect(self.close_current_tab)
        self.toolbar_widget.clear_requested.connect(self.clear_terminal)
        self.toolbar_widget.start_session_requested.connect(self.start_terminal_session)
        self.toolbar_widget.stop_session_requested.connect(self.stop_terminal_session)

    def add_new_tab(self):
        """Add a new terminal tab"""
        tab_title = f"Terminal {self.session_counter}"
        self.session_counter += 1

        terminal_widget = self.tab_manager.add_terminal_tab(tab_title)

        # Configure terminal widget
        if self.settings_manager:
            # Configure with settings
            pass

        if self.security_manager:
            # Configure with security manager
            pass

        # Connect terminal signals
        terminal_widget.session_started.connect(self.on_session_started)
        terminal_widget.session_ended.connect(self.on_session_ended)
        terminal_widget.command_executed.connect(self.on_command_executed)

        logger.info(f"Added new terminal tab: {tab_title}")

    def close_current_tab(self):
        """Close current terminal tab"""
        current_index = self.tab_manager.currentIndex()
        if current_index >= 0:
            self.tab_manager._close_tab(current_index)

    def switch_to_tab(self, index: int):
        """Switch to tab by index"""
        if 0 <= index < self.tab_manager.count():
            self.tab_manager.setCurrentIndex(index)

    def copy_selection(self):
        """Copy terminal selection to clipboard"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal and hasattr(terminal, 'terminal_display'):
            terminal.terminal_display.copy()

    def paste_clipboard(self):
        """Paste clipboard content to terminal"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal and hasattr(terminal, 'terminal_display'):
            terminal.terminal_display.paste()

    def clear_terminal(self):
        """Clear current terminal"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal:
            terminal.clear_terminal()

    def start_terminal_session(self):
        """Start terminal session in current tab"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal:
            terminal.start_session()

    def stop_terminal_session(self):
        """Stop terminal session in current tab"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal:
            terminal.stop_session()

    def send_interrupt(self):
        """Send interrupt signal to current terminal"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal:
            import signal
            terminal.send_signal(signal.SIGINT)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def toggle_info_panel(self):
        """Toggle info panel visibility"""
        if self.info_panel.isVisible():
            self.info_panel.hide()
        else:
            self.info_panel.show()
            self.update_info_panel()

    def update_info_panel(self):
        """Update info panel content"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal:
            session_info = terminal.get_session_info()
            info_text = f"""
<h3>Session Information</h3>
<p><b>Status:</b> {'Active' if session_info['active'] else 'Inactive'}</p>
<p><b>Uptime:</b> {session_info['uptime']:.1f} seconds</p>
<p><b>Commands:</b> {session_info['command_count']}</p>
<p><b>Working Directory:</b> {session_info['working_directory']}</p>

<h3>Security Status</h3>
<p><b>Policy Enabled:</b> {'Yes' if self.security_manager else 'No'}</p>
            """
            if self.security_manager:
                policy_status = self.security_manager.get_policy_status()
                info_text += f"""
<p><b>Violations:</b> {policy_status['violations_count']}</p>
<p><b>Command Mode:</b> {policy_status['command_mode']}</p>
                """

            self.info_panel.setHtml(info_text)

    def show_preferences(self):
        """Show preferences dialog"""
        # TODO: Implement preferences dialog
        QMessageBox.information(self, "Preferences", "Preferences dialog not yet implemented")

    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>CLI Multi-Rapid GUI Terminal</h2>
        <p>Version 1.0.0</p>
        <p>Enterprise-grade GUI terminal with PTY support</p>
        <p>Built with PyQt and advanced security features</p>
        """
        QMessageBox.about(self, "About", about_text)

    def apply_theme(self):
        """Apply application theme"""
        if self.settings_manager:
            ui_config = self.settings_manager.get_ui_config()
            theme = ui_config.get('theme', 'default')

            if theme == 'dark':
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #2b2b2b;
                        color: #ffffff;
                    }
                    QTabWidget::pane {
                        border: 1px solid #3c3c3c;
                        background-color: #2b2b2b;
                    }
                    QTabBar::tab {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        padding: 8px 12px;
                        margin-right: 2px;
                    }
                    QTabBar::tab:selected {
                        background-color: #4a4a4a;
                    }
                    QMenuBar {
                        background-color: #3c3c3c;
                        color: #ffffff;
                    }
                    QMenuBar::item:selected {
                        background-color: #4a4a4a;
                    }
                    QMenu {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        border: 1px solid #555555;
                    }
                    QMenu::item:selected {
                        background-color: #4a4a4a;
                    }
                """)

    def update_status(self):
        """Update status bar information"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal:
            session_info = terminal.get_session_info()
            self.status_bar_widget.update_session_info(session_info)

        # Update info panel if visible
        if self.info_panel.isVisible():
            self.update_info_panel()

    def on_session_started(self):
        """Handle session started event"""
        self.status_bar_widget.set_status("Session started")
        logger.info("Terminal session started")

    def on_session_ended(self):
        """Handle session ended event"""
        self.status_bar_widget.set_status("Session ended")
        logger.info("Terminal session ended")

    def on_command_executed(self, command: str):
        """Handle command executed event"""
        logger.info(f"Command executed: {command}")

    def on_tab_closed(self, index: int):
        """Handle tab closed event"""
        if self.tab_manager.count() == 0:
            # Add a new tab if all tabs were closed
            self.add_new_tab()

    def on_tab_changed(self, index: int):
        """Handle tab changed event"""
        self.update_status()

    def set_startup_options(self, command: Optional[str] = None, working_dir: Optional[str] = None):
        """Set startup options for the terminal"""
        terminal = self.tab_manager.get_current_terminal()
        if terminal:
            terminal.set_startup_options(command, working_dir)

    def closeEvent(self, event):
        """Handle window close event"""
        # Check for active sessions
        active_sessions = 0
        for i in range(self.tab_manager.count()):
            terminal = self.tab_manager.widget(i)
            if terminal and hasattr(terminal, 'pty_backend') and terminal.pty_backend.is_session_active():
                active_sessions += 1

        if active_sessions > 0:
            reply = QMessageBox.question(
                self, "Close Application",
                f"There are {active_sessions} active terminal sessions. Close anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        # Save window state
        self.save_window_state()

        # Stop all sessions
        for i in range(self.tab_manager.count()):
            terminal = self.tab_manager.widget(i)
            if terminal and hasattr(terminal, 'stop_session'):
                terminal.stop_session()

        event.accept()
        logger.info("Application closed")

    def save_window_state(self):
        """Save window state and geometry"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("splitterState", self.splitter.saveState())

    def restore_window_state(self):
        """Restore window state and geometry"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        window_state = self.settings.value("windowState")
        if window_state:
            self.restoreState(window_state)

        splitter_state = self.settings.value("splitterState")
        if splitter_state:
            self.splitter.restoreState(splitter_state)
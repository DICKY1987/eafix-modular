"""
Toolbar Implementation
Action toolbar with terminal operations and quick access buttons
"""

import logging
from typing import Optional

try:
    from PyQt6.QtWidgets import QToolBar, QAction, QPushButton, QComboBox, QLabel, QSeparator
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QIcon, QKeySequence
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import QToolBar, QAction, QPushButton, QComboBox, QLabel, QSeparator
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QIcon, QKeySequence
    PYQT_VERSION = 5

logger = logging.getLogger(__name__)


class Toolbar(QToolBar):
    """Enhanced toolbar with terminal operations"""

    # Signals
    new_tab_requested = pyqtSignal()
    close_tab_requested = pyqtSignal()
    start_session_requested = pyqtSignal()
    stop_session_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    shell_changed = pyqtSignal(str)
    font_size_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terminal Actions")
        self.setMovable(False)
        self.setup_actions()

    def setup_actions(self):
        """Setup toolbar actions and widgets"""
        # Tab management
        self.new_tab_action = QAction("New Tab", self)
        self.new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        self.new_tab_action.setToolTip("Create new terminal tab (Ctrl+T)")
        self.new_tab_action.triggered.connect(self.new_tab_requested.emit)
        self.addAction(self.new_tab_action)

        self.close_tab_action = QAction("Close Tab", self)
        self.close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        self.close_tab_action.setToolTip("Close current tab (Ctrl+W)")
        self.close_tab_action.triggered.connect(self.close_tab_requested.emit)
        self.addAction(self.close_tab_action)

        self.addSeparator()

        # Session management
        self.start_session_action = QAction("Start Session", self)
        self.start_session_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.start_session_action.setToolTip("Start terminal session (Ctrl+Shift+S)")
        self.start_session_action.triggered.connect(self.start_session_requested.emit)
        self.addAction(self.start_session_action)

        self.stop_session_action = QAction("Stop Session", self)
        self.stop_session_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self.stop_session_action.setToolTip("Stop terminal session (Ctrl+Shift+T)")
        self.stop_session_action.triggered.connect(self.stop_session_requested.emit)
        self.addAction(self.stop_session_action)

        self.addSeparator()

        # Terminal operations
        self.clear_action = QAction("Clear", self)
        self.clear_action.setShortcut(QKeySequence("Ctrl+L"))
        self.clear_action.setToolTip("Clear terminal (Ctrl+L)")
        self.clear_action.triggered.connect(self.clear_requested.emit)
        self.addAction(self.clear_action)

        self.addSeparator()

        # Shell selector
        self.addWidget(QLabel("Shell:"))
        self.shell_combo = QComboBox()
        self.shell_combo.addItems([
            "auto", "bash", "zsh", "fish", "cmd", "powershell", "pwsh"
        ])
        self.shell_combo.setToolTip("Select shell type")
        self.shell_combo.currentTextChanged.connect(self.shell_changed.emit)
        self.addWidget(self.shell_combo)

        self.addSeparator()

        # Font size control
        self.addWidget(QLabel("Font Size:"))
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems([
            "8", "9", "10", "11", "12", "13", "14", "16", "18", "20", "24"
        ])
        self.font_size_combo.setCurrentText("12")
        self.font_size_combo.setToolTip("Select font size")
        self.font_size_combo.currentTextChanged.connect(
            lambda text: self.font_size_changed.emit(int(text))
        )
        self.addWidget(self.font_size_combo)

        self.addSeparator()

        # Quick action buttons
        self.interrupt_button = QPushButton("Interrupt")
        self.interrupt_button.setToolTip("Send interrupt signal (Ctrl+C)")
        self.interrupt_button.clicked.connect(self.send_interrupt)
        self.addWidget(self.interrupt_button)

        self.eof_button = QPushButton("EOF")
        self.eof_button.setToolTip("Send EOF signal (Ctrl+D)")
        self.eof_button.clicked.connect(self.send_eof)
        self.addWidget(self.eof_button)

    def send_interrupt(self):
        """Send interrupt signal to terminal"""
        # This would be connected to the main window
        logger.info("Interrupt signal requested")

    def send_eof(self):
        """Send EOF signal to terminal"""
        # This would be connected to the main window
        logger.info("EOF signal requested")

    def update_session_state(self, active: bool):
        """Update toolbar based on session state"""
        self.start_session_action.setEnabled(not active)
        self.stop_session_action.setEnabled(active)
        self.interrupt_button.setEnabled(active)
        self.eof_button.setEnabled(active)

    def set_shell(self, shell: str):
        """Set current shell in combo box"""
        index = self.shell_combo.findText(shell)
        if index >= 0:
            self.shell_combo.setCurrentIndex(index)

    def set_font_size(self, size: int):
        """Set current font size in combo box"""
        index = self.font_size_combo.findText(str(size))
        if index >= 0:
            self.font_size_combo.setCurrentIndex(index)
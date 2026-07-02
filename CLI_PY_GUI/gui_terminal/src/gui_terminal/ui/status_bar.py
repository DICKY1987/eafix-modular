"""
Status Bar Implementation
Enhanced status bar with session information and system metrics
"""

import os
import logging
from typing import Dict, Any, Optional

try:
    from PyQt6.QtWidgets import QStatusBar, QLabel, QProgressBar, QWidget, QHBoxLayout
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import QStatusBar, QLabel, QProgressBar, QWidget, QHBoxLayout
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    PYQT_VERSION = 5

logger = logging.getLogger(__name__)


class StatusBar(QStatusBar):
    """Enhanced status bar with detailed session information"""

    def __init__(self):
        super().__init__()
        self.setup_widgets()

    def setup_widgets(self):
        """Setup status bar widgets"""
        # Main status message
        self.status_label = QLabel("Ready")
        self.addWidget(self.status_label)

        # Spacer
        self.addWidget(QWidget(), 1)

        # Session information
        self.session_label = QLabel("No session")
        self.session_label.setMinimumWidth(150)
        self.addPermanentWidget(self.session_label)

        # Working directory
        self.cwd_label = QLabel(f"CWD: {os.getcwd()}")
        self.cwd_label.setMinimumWidth(200)
        self.addPermanentWidget(self.cwd_label)

        # Security status
        self.security_label = QLabel("Security: ON")
        self.security_label.setMinimumWidth(100)
        self.addPermanentWidget(self.security_label)

        # Performance indicator
        self.perf_label = QLabel("CPU: 0% | MEM: 0MB")
        self.perf_label.setMinimumWidth(150)
        self.addPermanentWidget(self.perf_label)

        # Connection status
        self.connection_label = QLabel("Disconnected")
        self.connection_label.setStyleSheet("color: red")
        self.addPermanentWidget(self.connection_label)

    def set_status(self, message: str):
        """Set main status message"""
        self.status_label.setText(message)

    def update_session_info(self, session_info: Dict[str, Any]):
        """Update session information display"""
        if session_info.get('active', False):
            uptime = session_info.get('uptime', 0)
            command_count = session_info.get('command_count', 0)
            self.session_label.setText(f"Session: {uptime:.0f}s, Commands: {command_count}")
            self.session_label.setStyleSheet("color: green")
        else:
            self.session_label.setText("No session")
            self.session_label.setStyleSheet("")

        # Update working directory
        cwd = session_info.get('working_directory', os.getcwd())
        self.cwd_label.setText(f"CWD: {os.path.basename(cwd) if len(cwd) > 30 else cwd}")

    def update_security_status(self, enabled: bool, violations: int = 0):
        """Update security status"""
        if enabled:
            if violations > 0:
                self.security_label.setText(f"Security: ON ({violations} violations)")
                self.security_label.setStyleSheet("color: orange")
            else:
                self.security_label.setText("Security: ON")
                self.security_label.setStyleSheet("color: green")
        else:
            self.security_label.setText("Security: OFF")
            self.security_label.setStyleSheet("color: red")

    def update_performance_metrics(self, cpu_percent: float, memory_mb: float):
        """Update performance metrics"""
        self.perf_label.setText(f"CPU: {cpu_percent:.1f}% | MEM: {memory_mb:.0f}MB")

        # Color coding for performance
        if cpu_percent > 80 or memory_mb > 500:
            self.perf_label.setStyleSheet("color: red")
        elif cpu_percent > 50 or memory_mb > 300:
            self.perf_label.setStyleSheet("color: orange")
        else:
            self.perf_label.setStyleSheet("color: green")

    def update_connection_status(self, connected: bool, service: str = ""):
        """Update platform connection status"""
        if connected:
            self.connection_label.setText(f"Connected ({service})" if service else "Connected")
            self.connection_label.setStyleSheet("color: green")
        else:
            self.connection_label.setText("Disconnected")
            self.connection_label.setStyleSheet("color: red")

    def show_progress(self, message: str, progress: int):
        """Show progress bar with message"""
        # Remove existing progress widgets
        self.clearMessage()

        # Create progress widget
        progress_widget = QWidget()
        layout = QHBoxLayout(progress_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        progress_label = QLabel(message)
        progress_bar = QProgressBar()
        progress_bar.setValue(progress)
        progress_bar.setMaximumWidth(200)

        layout.addWidget(progress_label)
        layout.addWidget(progress_bar)

        # Add to status bar
        self.addWidget(progress_widget)

    def hide_progress(self):
        """Hide progress bar"""
        # Clear all temporary widgets
        self.clearMessage()

    def show_temporary_message(self, message: str, timeout: int = 3000):
        """Show temporary message"""
        self.showMessage(message, timeout)
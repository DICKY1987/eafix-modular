"""
Enterprise Terminal Widget Implementation
Advanced terminal widget with full PTY support and enterprise features
"""

import os
import sys
import signal
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path

try:
    from PyQt6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QTextCursor, QKeyEvent, QResizeEvent
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    from PyQt5.QtCore import Qt, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont, QTextCursor, QKeyEvent, QResizeEvent
    PYQT_VERSION = 5

from .pty_backend import PTYBackend, CommandResult
from ..config.settings import SettingsManager
from ..security.policy_manager import SecurityPolicyManager

logger = logging.getLogger(__name__)


class TerminalDisplay(QTextEdit):
    """Enhanced terminal display widget"""

    input_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setup_terminal()
        self.command_history = []
        self.history_index = -1
        self.current_input_line = ""
        self.prompt_length = 0

    def setup_terminal(self):
        """Setup terminal appearance and behavior"""
        # Terminal appearance
        font = QFont("Consolas", 12)
        if not font.exactMatch():
            # Fallback fonts
            for font_name in ["Monaco", "Courier New", "monospace"]:
                font = QFont(font_name, 12)
                if font.exactMatch():
                    break

        font.setFixedPitch(True)
        self.setFont(font)

        # Dark terminal theme
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                selection-background-color: #404040;
                selection-color: #ffffff;
            }
        """)

        # Terminal settings
        self.setAcceptRichText(False)
        self.setUndoRedoEnabled(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        # Enable mouse selection but disable editing
        self.setReadOnly(False)  # We'll handle input manually

    def append_output(self, text: str):
        """Append output to terminal with proper formatting"""
        # Move cursor to end
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)

        # Auto-scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_current_line(self):
        """Clear current input line"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

    def show_prompt(self, prompt: str = "$ "):
        """Show command prompt"""
        self.append_output(prompt)
        self.prompt_length = len(prompt)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events for terminal input"""
        key = event.key()
        modifiers = event.modifiers()

        # Handle special key combinations
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_C:
                # Ctrl+C - send interrupt signal
                self.input_received.emit('\x03')
                return
            elif key == Qt.Key.Key_D:
                # Ctrl+D - send EOF
                self.input_received.emit('\x04')
                return
            elif key == Qt.Key.Key_Z:
                # Ctrl+Z - send suspend signal
                self.input_received.emit('\x1a')
                return
            elif key == Qt.Key.Key_L:
                # Ctrl+L - clear screen
                self.clear()
                return

        # Handle Enter key
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Get current line text
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            line_text = cursor.selectedText()

            # Remove prompt from line
            if len(line_text) >= self.prompt_length:
                command_text = line_text[self.prompt_length:]
                if command_text.strip():
                    self.command_history.append(command_text)
                    self.history_index = len(self.command_history)

                # Send command
                self.append_output('\n')
                self.input_received.emit(command_text + '\n')
            else:
                self.append_output('\n')
                self.input_received.emit('\n')
            return

        # Handle history navigation
        if key == Qt.Key.Key_Up:
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self._replace_current_line(self.command_history[self.history_index])
            return

        if key == Qt.Key.Key_Down:
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self._replace_current_line(self.command_history[self.history_index])
            elif self.history_index >= len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self._replace_current_line("")
            return

        # Handle backspace
        if key == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            line_start = cursor.position()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            current_pos = cursor.position()

            # Don't delete past the prompt
            if current_pos > line_start + self.prompt_length:
                cursor.deletePreviousChar()
            return

        # Handle regular character input
        if event.text() and ord(event.text()[0]) >= 32:  # Printable characters
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(event.text())
            self.setTextCursor(cursor)

    def _replace_current_line(self, text: str):
        """Replace current input line with text"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)

        # Keep the prompt, replace everything after it
        prompt_end = cursor.position() + self.prompt_length
        cursor.setPosition(prompt_end)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(text)
        self.setTextCursor(cursor)


class EnterpriseTerminalWidget(QWidget):
    """
    Enterprise-grade terminal widget with full PTY support
    """

    session_started = pyqtSignal()
    session_ended = pyqtSignal()
    command_executed = pyqtSignal(str)

    def __init__(self, config_manager: Optional[SettingsManager] = None,
                 security_manager: Optional[SecurityPolicyManager] = None,
                 audit_logger=None):
        super().__init__()

        # Dependency injection
        self.config_manager = config_manager
        self.security_manager = security_manager
        self.audit_logger = audit_logger

        # Core components
        self.pty_backend = PTYBackend()
        self.setup_ui()
        self.setup_connections()

        # Session state
        self.current_session_id = None
        self.session_info = {
            'start_time': None,
            'command_count': 0,
            'working_directory': os.getcwd()
        }

        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second

    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Terminal display
        self.terminal_display = TerminalDisplay()
        layout.addWidget(self.terminal_display)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.cwd_label = QLabel(f"CWD: {os.getcwd()}")
        self.session_label = QLabel("No session")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.cwd_label)
        status_layout.addWidget(self.session_label)

        layout.addLayout(status_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Session")
        self.stop_button = QPushButton("Stop Session")
        self.clear_button = QPushButton("Clear")

        self.stop_button.setEnabled(False)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def setup_connections(self):
        """Setup signal connections"""
        # PTY backend connections
        self.pty_backend.output_received.connect(self.handle_output)
        self.pty_backend.process_finished.connect(self.handle_process_finished)
        self.pty_backend.error_occurred.connect(self.handle_error)

        # Terminal display connections
        self.terminal_display.input_received.connect(self.handle_input)

        # Button connections
        self.start_button.clicked.connect(self.start_session)
        self.stop_button.clicked.connect(self.stop_session)
        self.clear_button.clicked.connect(self.clear_terminal)

    def start_session(self, command: Optional[str] = None, working_dir: Optional[str] = None):
        """Start new terminal session"""
        try:
            # Get configuration
            if working_dir is None:
                working_dir = os.getcwd()

            if self.config_manager:
                config = self.config_manager.get_terminal_config()
                if command is None:
                    command = config.get('default_shell', 'auto')
                if command == 'auto':
                    command = None  # Let PTY backend determine default

            # Security validation
            if self.security_manager and command:
                is_valid, violations = self.security_manager.validate_command(command, [], working_dir)
                if not is_valid:
                    self.terminal_display.append_output(f"Security violation: {'; '.join(violations)}\n")
                    return

            # Start PTY session
            self.pty_backend.start_session(
                command=command,
                cwd=working_dir
            )

            # Update UI state
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Starting session...")

            # Initialize session
            import time
            self.session_info['start_time'] = time.time()
            self.session_info['command_count'] = 0
            self.session_info['working_directory'] = working_dir

            # Show initial prompt
            self.terminal_display.show_prompt("$ ")

            # Audit logging
            if self.audit_logger:
                self.audit_logger.log_session_start(command or "default", working_dir)

            self.session_started.emit()
            logger.info(f"Terminal session started: {command or 'default shell'}")

        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            self.handle_error(str(e))

    def stop_session(self):
        """Stop current terminal session"""
        try:
            self.pty_backend.stop_session()

            # Update UI state
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText("Session stopped")
            self.session_label.setText("No session")

            # Audit logging
            if self.audit_logger:
                self.audit_logger.log_session_end(self.session_info)

            self.session_ended.emit()
            logger.info("Terminal session stopped")

        except Exception as e:
            logger.error(f"Failed to stop session: {e}")
            self.handle_error(str(e))

    def handle_input(self, text: str):
        """Handle input from terminal display"""
        if self.pty_backend.is_session_active():
            # Security validation for commands
            if self.security_manager and text.strip():
                command_parts = text.strip().split()
                if command_parts:
                    is_valid, violations = self.security_manager.validate_command(
                        command_parts[0], command_parts[1:], self.session_info['working_directory']
                    )
                    if not is_valid:
                        self.terminal_display.append_output(f"Security violation: {'; '.join(violations)}\n")
                        self.terminal_display.show_prompt("$ ")
                        return

            # Send input to PTY
            self.pty_backend.send_input(text)

            # Update command count
            if text.strip():
                self.session_info['command_count'] += 1
                self.command_executed.emit(text.strip())

                # Audit logging
                if self.audit_logger:
                    self.audit_logger.log_command(text.strip(), self.session_info)

    def handle_output(self, text: str):
        """Handle output from PTY backend"""
        self.terminal_display.append_output(text)

    def handle_process_finished(self, result: CommandResult):
        """Handle process completion"""
        self.terminal_display.append_output(f"\nProcess exited with code {result.exit_code}\n")
        self.terminal_display.show_prompt("$ ")

        # Update status
        status_text = f"Exit code: {result.exit_code}, Time: {result.execution_time:.2f}s"
        self.status_label.setText(status_text)

    def handle_error(self, error_message: str):
        """Handle errors from PTY backend"""
        self.terminal_display.append_output(f"\nError: {error_message}\n")
        self.status_label.setText(f"Error: {error_message}")

        # Reset UI state
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def clear_terminal(self):
        """Clear terminal display"""
        self.terminal_display.clear()
        if self.pty_backend.is_session_active():
            self.terminal_display.show_prompt("$ ")

    def send_signal(self, sig: signal.Signals):
        """Send signal to current process"""
        if self.pty_backend.is_session_active():
            self.pty_backend.send_signal(sig)

    def resize_terminal(self, cols: int, rows: int):
        """Resize terminal"""
        if self.pty_backend.is_session_active():
            self.pty_backend.resize_terminal(cols, rows)

    def update_status(self):
        """Update status information"""
        if self.pty_backend.is_session_active():
            uptime = time.time() - self.session_info['start_time'] if self.session_info['start_time'] else 0
            self.session_label.setText(f"Session: {uptime:.0f}s, Commands: {self.session_info['command_count']}")
            self.status_label.setText("Session active")

    def get_session_info(self) -> Dict[str, Any]:
        """Return current session information for status bar"""
        return {
            'active': self.pty_backend.is_session_active(),
            'uptime': time.time() - self.session_info['start_time'] if self.session_info['start_time'] else 0,
            'command_count': self.session_info['command_count'],
            'working_directory': self.session_info['working_directory'],
            'status': self.status_label.text()
        }

    def set_startup_options(self, command: Optional[str] = None, working_dir: Optional[str] = None):
        """Set startup options for the terminal"""
        if working_dir:
            self.session_info['working_directory'] = working_dir
            self.cwd_label.setText(f"CWD: {working_dir}")

        # Auto-start if command specified
        if command:
            self.start_session(command, working_dir)

    def resizeEvent(self, event: QResizeEvent):
        """Handle widget resize event"""
        super().resizeEvent(event)

        # Calculate terminal size in characters
        font_metrics = self.terminal_display.fontMetrics()
        char_width = font_metrics.averageCharWidth()
        char_height = font_metrics.height()

        terminal_width = self.terminal_display.width()
        terminal_height = self.terminal_display.height()

        cols = max(1, terminal_width // char_width)
        rows = max(1, terminal_height // char_height)

        # Resize PTY if session is active
        if self.pty_backend.is_session_active():
            self.pty_backend.resize_terminal(cols, rows)
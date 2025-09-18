"""Simple CLI execution interface for GUI terminal."""

from typing import Optional
import subprocess
import threading
import time
import sys

try:
    from PyQt6 import QtWidgets, QtCore, QtGui
    PyQt6Available = True
except ImportError:
    PyQt6Available = False
    # Create dummy classes for when PyQt6 is not available
    class QtWidgets:
        class QWidget:
            def __init__(self, parent=None): pass
        class QVBoxLayout:
            def __init__(self, parent=None): pass
        class QHBoxLayout:
            def __init__(self): pass
        class QLabel:
            def __init__(self, text=""): pass
        class QLineEdit:
            def __init__(self): pass
        class QPushButton:
            def __init__(self, text=""): pass
        class QTextEdit:
            def __init__(self): pass
        class QFrame:
            def __init__(self): pass
        class QListWidget:
            def __init__(self): pass
    class QtCore:
        class Qt:
            class Key:
                Key_Up = None
                Key_Down = None
            class ConnectionType:
                QueuedConnection = None
        pyqtSlot = lambda *args, **kwargs: lambda func: func
        class QMetaObject:
            @staticmethod
            def invokeMethod(*args, **kwargs): pass
        Q_ARG = lambda *args: None
    class QtGui:
        class QFont:
            def __init__(self, family="", size=10): pass
        class QTextCursor:
            class MoveOperation:
                End = None
            class SelectionType:
                LineUnderCursor = None

from ..security.policy_manager import PolicyManager


if PyQt6Available:
    class CLIExecutionInterface(QtWidgets.QWidget):
        """Simple command input/output interface focused on CLI execution."""

        def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
            super().__init__(parent)
            self.policy_manager = PolicyManager()
            self.command_history = []
            self.history_index = -1
            self.current_process: Optional[subprocess.Popen] = None
            self._setup_ui()

        def _setup_ui(self):
            """Set up the simple CLI interface layout."""
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(8)

            # Header
            header_label = QtWidgets.QLabel("CLI Multi-Rapid Terminal")
            header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d3748; margin-bottom: 10px;")
            layout.addWidget(header_label)

            # Command input section
            input_layout = QtWidgets.QHBoxLayout()

            input_label = QtWidgets.QLabel("Command:")
            input_label.setMinimumWidth(70)
            input_layout.addWidget(input_label)

            self.command_input = QtWidgets.QLineEdit()
            self.command_input.setPlaceholderText("Enter command (e.g., cli-multi-rapid --help)")
            self.command_input.returnPressed.connect(self._execute_command)
            self.command_input.keyPressEvent = self._handle_key_press
            input_layout.addWidget(self.command_input)

            self.execute_button = QtWidgets.QPushButton("Execute")
            self.execute_button.clicked.connect(self._execute_command)
            self.execute_button.setMinimumWidth(80)
            input_layout.addWidget(self.execute_button)

            layout.addLayout(input_layout)

            # Output display
            output_label = QtWidgets.QLabel("Output:")
            layout.addWidget(output_label)

            self.output_display = QtWidgets.QTextEdit()
            self.output_display.setReadOnly(True)
            self.output_display.setFont(QtGui.QFont("Consolas", 10))
            self.output_display.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
            layout.addWidget(self.output_display, stretch=1)

            # Status bar
            self.status_bar = QtWidgets.QLabel("Ready")
            self.status_bar.setStyleSheet("color: #666; font-size: 12px; padding: 4px;")
            layout.addWidget(self.status_bar)

            # Command history (optional, collapsed by default)
            self.history_widget = self._create_history_widget()
            layout.addWidget(self.history_widget)
            self.history_widget.setVisible(False)

        def _create_history_widget(self):
            """Create command history widget."""
            history_frame = QtWidgets.QFrame()
            history_frame.setFrameStyle(QtWidgets.QFrame.Shape.Box)
            history_frame.setMaximumHeight(150)

            history_layout = QtWidgets.QVBoxLayout(history_frame)

            history_header = QtWidgets.QHBoxLayout()
            history_label = QtWidgets.QLabel("Command History:")
            history_header.addWidget(history_label)

            toggle_button = QtWidgets.QPushButton("Hide")
            toggle_button.setMaximumWidth(60)
            toggle_button.clicked.connect(lambda: self._toggle_history())
            history_header.addWidget(toggle_button)

            history_layout.addLayout(history_header)

            self.history_list = QtWidgets.QListWidget()
            self.history_list.itemDoubleClicked.connect(self._use_history_command)
            history_layout.addWidget(self.history_list)

            return history_frame

        def _handle_key_press(self, event):
            """Handle key presses in command input (arrow keys for history)."""
            if event.key() == QtCore.Qt.Key.Key_Up:
                self._navigate_history(-1)
            elif event.key() == QtCore.Qt.Key.Key_Down:
                self._navigate_history(1)
            else:
                # Call the original keyPressEvent
                QtWidgets.QLineEdit.keyPressEvent(self.command_input, event)

        def _navigate_history(self, direction: int):
            """Navigate command history with arrow keys."""
            if not self.command_history:
                return

            if direction == -1 and self.history_index > 0:
                self.history_index -= 1
            elif direction == 1 and self.history_index < len(self.command_history) - 1:
                self.history_index += 1

            if 0 <= self.history_index < len(self.command_history):
                self.command_input.setText(self.command_history[self.history_index])

        def _execute_command(self):
            """Execute the entered command with security policy checks."""
            command = self.command_input.text().strip()
            if not command:
                return

            # Add to history
            if command not in self.command_history:
                self.command_history.append(command)
                self.history_list.addItem(command)
            self.history_index = len(self.command_history)

            # Security policy check
            if not self.policy_manager.is_command_allowed(command):
                self._append_output(f"❌ Command blocked by security policy: {command}", "error")
                self.status_bar.setText("Command blocked")
                return

            # Clear input and show execution status
            self.command_input.clear()
            self.status_bar.setText("Executing...")
            self.execute_button.setEnabled(False)

            # Execute command in background thread
            self._append_output(f"$ {command}", "command")
            thread = threading.Thread(target=self._run_command, args=(command,))
            thread.daemon = True
            thread.start()

        def _run_command(self, command: str):
            """Run command in subprocess and capture output."""
            try:
                # Start process
                self.current_process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    universal_newlines=True
                )

                # Read output line by line
                output_lines = []
                while True:
                    line = self.current_process.stdout.readline()
                    if line:
                        output_lines.append(line.rstrip())
                        # Update UI from main thread
                        QtCore.QMetaObject.invokeMethod(
                            self,
                            "_append_output",
                            QtCore.Qt.ConnectionType.QueuedConnection,
                            QtCore.Q_ARG(str, line.rstrip()),
                            QtCore.Q_ARG(str, "output")
                        )
                    elif self.current_process.poll() is not None:
                        break
                    time.sleep(0.01)

                # Get return code
                return_code = self.current_process.wait()

                # Update UI with completion status
                if return_code == 0:
                    status_msg = f"✅ Command completed successfully"
                    status_color = "success"
                else:
                    status_msg = f"❌ Command failed (exit code: {return_code})"
                    status_color = "error"

                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_append_output",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, status_msg),
                    QtCore.Q_ARG(str, status_color)
                )

                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_command_finished",
                    QtCore.Qt.ConnectionType.QueuedConnection
                )

            except Exception as e:
                error_msg = f"❌ Error executing command: {str(e)}"
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_append_output",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, error_msg),
                    QtCore.Q_ARG(str, "error")
                )
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_command_finished",
                    QtCore.Qt.ConnectionType.QueuedConnection
                )

        @QtCore.pyqtSlot(str, str)
        def _append_output(self, text: str, msg_type: str = "output"):
            """Append text to output display with appropriate formatting."""
            cursor = self.output_display.textCursor()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)

            # Set color based on message type
            if msg_type == "command":
                cursor.insertHtml(f'<span style="color: #00ff00; font-weight: bold;">{text}</span><br>')
            elif msg_type == "error":
                cursor.insertHtml(f'<span style="color: #ff4444;">{text}</span><br>')
            elif msg_type == "success":
                cursor.insertHtml(f'<span style="color: #44ff44;">{text}</span><br>')
            else:
                cursor.insertHtml(f'<span style="color: #ffffff;">{text}</span><br>')

            # Auto-scroll to bottom
            self.output_display.ensureCursorVisible()

        @QtCore.pyqtSlot()
        def _command_finished(self):
            """Reset UI state after command completion."""
            self.execute_button.setEnabled(True)
            self.status_bar.setText("Ready")
            self.current_process = None

        def _toggle_history(self):
            """Toggle command history visibility."""
            is_visible = self.history_widget.isVisible()
            self.history_widget.setVisible(not is_visible)

            # Update toggle button text
            toggle_button = self.history_widget.findChild(QtWidgets.QPushButton)
            if toggle_button:
                toggle_button.setText("Show" if is_visible else "Hide")

        def _use_history_command(self, item):
            """Use selected history command."""
            self.command_input.setText(item.text())
            self.command_input.setFocus()

else:
    # Headless fallback for when PyQt6 is not available
    class CLIExecutionInterface:
        """Headless CLI interface fallback."""

        def __init__(self, parent=None):
            self.policy_manager = PolicyManager()
            print("CLI Multi-Rapid Terminal (Headless Mode)")
            print("Type 'exit' to quit\n")

        def run(self):
            """Run headless CLI interface."""
            while True:
                try:
                    command = input("$ ").strip()

                    if command.lower() in ['exit', 'quit']:
                        print("Goodbye!")
                        break

                    if not command:
                        continue

                    if not self.policy_manager.is_command_allowed(command):
                        print(f"❌ Command blocked by security policy: {command}")
                        continue

                    # Execute command
                    try:
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True
                        )

                        if result.stdout:
                            print(result.stdout)
                        if result.stderr:
                            print(f"Error: {result.stderr}", file=sys.stderr)

                        if result.returncode == 0:
                            print("✅ Command completed successfully")
                        else:
                            print(f"❌ Command failed (exit code: {result.returncode})")

                    except Exception as e:
                        print(f"❌ Error executing command: {e}")

                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except EOFError:
                    print("\nGoodbye!")
                    break
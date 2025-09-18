"""
PTY-backed Terminal Tab with Command Runner - GUI Terminal Implementation
Provides true terminal parity with CLI while maintaining GUI convenience
"""

import os
import sys
import pty
import select
import signal
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QPushButton, QLabel, QStatusBar, QTabWidget, QMainWindow,
    QToolBar, QMenuBar, QSplitter, QScrollBar
)
from PyQt6.QtCore import (
    QThread, pyqtSignal, QTimer, QProcess, QObject, Qt
)
from PyQt6.QtGui import (
    QFont, QTextCursor, QKeySequence, QAction, QTextCharFormat, QColor
)

if sys.platform == "win32":
    import winpty  # pip install pywinpty


@dataclass
class CommandRequest:
    """JSON contract for command execution"""
    tool: str
    args: List[str] = None
    env: Dict[str, str] = None
    cwd: str = None
    timeout_sec: int = 300
    interactive: bool = True
    shell: bool = False
    
    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.env is None:
            self.env = {}
        if self.cwd is None:
            self.cwd = os.getcwd()


@dataclass
class CommandResponse:
    """JSON contract for command results"""
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    artifacts: List[str] = None
    duration: float = 0.0
    command_preview: str = ""
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class PTYWorker(QThread):
    """Cross-platform PTY worker for true terminal emulation"""
    
    data_received = pyqtSignal(bytes)
    process_finished = pyqtSignal(int)
    
    def __init__(self, command_req: CommandRequest):
        super().__init__()
        self.command_req = command_req
        self.master_fd = None
        self.slave_fd = None
        self.process = None
        self.running = False
        
        # Build command preview
        cmd_parts = [self.command_req.tool] + self.command_req.args
        self.command_req.command_preview = " ".join(cmd_parts)
        
    def run(self):
        """Execute command in PTY with platform-specific handling"""
        if sys.platform == "win32":
            self._run_windows()
        else:
            self._run_unix()
            
    def _run_unix(self):
        """Unix/Linux/macOS PTY implementation"""
        try:
            # Create PTY pair
            self.master_fd, self.slave_fd = pty.openpty()
            
            # Fork process
            pid = os.fork()
            
            if pid == 0:  # Child process
                os.close(self.master_fd)
                os.setsid()
                os.dup2(self.slave_fd, 0)  # stdin
                os.dup2(self.slave_fd, 1)  # stdout
                os.dup2(self.slave_fd, 2)  # stderr
                os.close(self.slave_fd)
                
                # Set environment
                env = os.environ.copy()
                env.update(self.command_req.env)
                env['TERM'] = 'xterm-256color'
                env['COLUMNS'] = '80'
                env['LINES'] = '24'
                
                # Change directory
                os.chdir(self.command_req.cwd)
                
                # Execute command
                cmd_parts = [self.command_req.tool] + self.command_req.args
                os.execvpe(cmd_parts[0], cmd_parts, env)
                
            else:  # Parent process
                os.close(self.slave_fd)
                self.running = True
                
                while self.running:
                    # Use select to check for data
                    ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                    
                    if ready:
                        try:
                            data = os.read(self.master_fd, 1024)
                            if data:
                                self.data_received.emit(data)
                            else:
                                break
                        except OSError:
                            break
                
                # Wait for process to finish
                try:
                    _, exit_code = os.waitpid(pid, 0)
                    exit_code = os.WEXITSTATUS(exit_code)
                except:
                    exit_code = -1
                    
                self.process_finished.emit(exit_code)
                
        except Exception as e:
            print(f"PTY error: {e}")
            self.process_finished.emit(-1)
        finally:
            if self.master_fd:
                os.close(self.master_fd)
                
    def _run_windows(self):
        """Windows ConPTY implementation using winpty"""
        try:
            # Build command line
            cmd_parts = [self.command_req.tool] + self.command_req.args
            cmdline = subprocess.list2cmdline(cmd_parts)
            
            # Set up environment
            env = os.environ.copy()
            env.update(self.command_req.env)
            
            # Create winpty process
            self.process = winpty.PtyProcess.spawn(
                cmdline,
                cwd=self.command_req.cwd,
                env=env
            )
            
            self.running = True
            
            while self.running and self.process.isalive():
                try:
                    # Read data with timeout
                    data = self.process.read(1024, blocking=False)
                    if data:
                        self.data_received.emit(data.encode('utf-8'))
                    else:
                        self.msleep(50)  # Small delay to prevent busy waiting
                        
                except Exception as e:
                    if "timeout" not in str(e).lower():
                        print(f"Read error: {e}")
                        break
                        
            exit_code = self.process.exitstatus if hasattr(self.process, 'exitstatus') else 0
            self.process_finished.emit(exit_code)
            
        except Exception as e:
            print(f"Windows PTY error: {e}")
            self.process_finished.emit(-1)
            
    def write_to_pty(self, data: bytes):
        """Write data to PTY (user input)"""
        try:
            if sys.platform == "win32" and self.process:
                self.process.write(data.decode('utf-8'))
            elif self.master_fd:
                os.write(self.master_fd, data)
        except Exception as e:
            print(f"PTY write error: {e}")
            
    def resize_pty(self, cols: int, rows: int):
        """Resize PTY to match terminal widget"""
        try:
            if sys.platform == "win32" and self.process:
                self.process.setwinsize(rows, cols)
            elif self.master_fd:
                import struct, fcntl, termios
                s = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, s)
        except Exception as e:
            print(f"PTY resize error: {e}")
            
    def terminate(self):
        """Terminate the PTY process"""
        self.running = False
        try:
            if sys.platform == "win32" and self.process:
                self.process.terminate()
            elif self.master_fd:
                os.close(self.master_fd)
        except:
            pass


class TerminalWidget(QTextEdit):
    """Terminal widget with ANSI support and PTY integration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Terminal styling
        font = QFont("Consolas", 10)  # Windows-friendly monospace
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.setFont(font)
        
        # Dark terminal theme
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #404040;
            }
        """)
        
        self.setAcceptRichText(False)
        
        # ANSI color map (basic 16 colors)
        self.ansi_colors = {
            30: QColor(0, 0, 0),        # Black
            31: QColor(205, 49, 49),    # Red
            32: QColor(13, 188, 121),   # Green
            33: QColor(229, 229, 16),   # Yellow
            34: QColor(36, 114, 200),   # Blue
            35: QColor(188, 63, 188),   # Magenta
            36: QColor(17, 168, 205),   # Cyan
            37: QColor(229, 229, 229),  # White
        }
        
    def append_data(self, data: bytes):
        """Append raw terminal data with ANSI processing"""
        try:
            text = data.decode('utf-8', errors='replace')
            self.process_ansi_text(text)
            
            # Auto-scroll to bottom
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            print(f"Terminal append error: {e}")
            
    def process_ansi_text(self, text: str):
        """Basic ANSI escape sequence processing"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        i = 0
        while i < len(text):
            if text[i] == '\x1b' and i + 1 < len(text) and text[i + 1] == '[':
                # Found ANSI escape sequence
                j = i + 2
                while j < len(text) and text[j] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
                    j += 1
                    
                if j < len(text):
                    # Extract sequence
                    seq = text[i + 2:j]
                    cmd = text[j]
                    
                    if cmd == 'm':  # Color/style command
                        self.apply_ansi_style(seq, cursor)
                    # Could add cursor movement, clearing, etc. here
                    
                    i = j + 1
                else:
                    # Malformed sequence, just add the character
                    cursor.insertText(text[i])
                    i += 1
            else:
                # Regular character
                cursor.insertText(text[i])
                i += 1
                
        self.setTextCursor(cursor)
        
    def apply_ansi_style(self, seq: str, cursor: QTextCursor):
        """Apply ANSI color/style codes"""
        if not seq or seq == '0':  # Reset
            fmt = QTextCharFormat()
            cursor.setCharFormat(fmt)
            return
            
        try:
            codes = [int(x) for x in seq.split(';') if x.isdigit()]
            fmt = cursor.charFormat()
            
            for code in codes:
                if 30 <= code <= 37:  # Foreground colors
                    fmt.setForeground(self.ansi_colors.get(code, QColor(204, 204, 204)))
                elif 40 <= code <= 47:  # Background colors
                    fmt.setBackground(self.ansi_colors.get(code - 10, QColor(0, 0, 0)))
                elif code == 1:  # Bold
                    fmt.setFontWeight(QFont.Weight.Bold)
                elif code == 4:  # Underline
                    fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                    
            cursor.setCharFormat(fmt)
        except:
            pass  # Ignore malformed codes


class TerminalTab(QWidget):
    """Single terminal tab with PTY backend"""
    
    def __init__(self, command_req: CommandRequest, parent=None):
        super().__init__(parent)
        self.command_req = command_req
        self.pty_worker = None
        
        self.setup_ui()
        self.start_pty()
        
    def setup_ui(self):
        """Setup terminal tab UI"""
        layout = QVBoxLayout(self)
        
        # Command preview strip
        preview_layout = QHBoxLayout()
        preview_label = QLabel("Command:")
        preview_label.setStyleSheet("font-weight: bold; color: #888;")
        
        cmd_display = QLabel(self.command_req.command_preview)
        cmd_display.setStyleSheet("font-family: monospace; background: #2d2d2d; padding: 4px; border-radius: 3px;")
        cmd_display.setWordWrap(True)
        
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(cmd_display, 1)
        layout.addLayout(preview_layout)
        
        # Terminal widget
        self.terminal = TerminalWidget()
        layout.addWidget(self.terminal, 1)
        
        # Input line for interactive commands
        self.input_line = QLineEdit()
        self.input_line.setFont(QFont("Consolas", 10))
        self.input_line.setPlaceholderText("Type commands here...")
        self.input_line.returnPressed.connect(self.send_input)
        layout.addWidget(self.input_line)
        
        # Status info
        status_layout = QHBoxLayout()
        self.status_label = QLabel(f"CWD: {self.command_req.cwd}")
        self.exit_code_label = QLabel("Running...")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.exit_code_label)
        layout.addLayout(status_layout)
        
    def start_pty(self):
        """Start the PTY worker thread"""
        self.pty_worker = PTYWorker(self.command_req)
        self.pty_worker.data_received.connect(self.terminal.append_data)
        self.pty_worker.process_finished.connect(self.on_process_finished)
        self.pty_worker.start()
        
    def send_input(self):
        """Send input to PTY"""
        if self.pty_worker:
            text = self.input_line.text() + '\n'
            self.pty_worker.write_to_pty(text.encode('utf-8'))
            self.input_line.clear()
            
    def on_process_finished(self, exit_code: int):
        """Handle process completion"""
        self.exit_code_label.setText(f"Exit Code: {exit_code}")
        if exit_code == 0:
            self.exit_code_label.setStyleSheet("color: green;")
        else:
            self.exit_code_label.setStyleSheet("color: red;")
            
    def closeEvent(self, event):
        """Cleanup when tab closes"""
        if self.pty_worker:
            self.pty_worker.terminate()
            self.pty_worker.wait(3000)  # Wait up to 3 seconds
        event.accept()


class CommandRunner:
    """Unified command runner with JSON contract"""
    
    def __init__(self):
        self.default_shell = self._detect_shell()
        
    def _detect_shell(self) -> str:
        """Detect user's preferred shell"""
        if sys.platform == "win32":
            # Check for PowerShell vs CMD
            if shutil.which("pwsh"):
                return "pwsh"
            elif shutil.which("powershell"):
                return "powershell"
            else:
                return "cmd"
        else:
            return os.environ.get("SHELL", "/bin/bash")
            
    def create_request(self, command: str, **kwargs) -> CommandRequest:
        """Create command request from command string"""
        # Parse command into tool and args
        if sys.platform == "win32":
            # Windows command parsing
            parts = command.split()
        else:
            # Unix shell parsing (simplified)
            parts = command.split()
            
        tool = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        # Build request
        req = CommandRequest(tool=tool, args=args)
        
        # Override with provided kwargs
        for key, value in kwargs.items():
            if hasattr(req, key):
                setattr(req, key, value)
                
        return req
        
    def validate_request(self, req: CommandRequest) -> Tuple[bool, str]:
        """Validate command request for security"""
        # Basic security checks
        if not req.tool:
            return False, "No command specified"
            
        # Check if tool exists
        if not shutil.which(req.tool):
            return False, f"Command not found: {req.tool}"
            
        # Prevent shell injection in basic cases
        dangerous_chars = ['&', '|', ';', '$', '`']
        if any(char in req.tool for char in dangerous_chars):
            return False, "Potentially unsafe command detected"
            
        return True, "OK"


# Quick Actions derived from VS Code tasks (example data)
QUICK_ACTIONS = {
    "CLI Platform": [
        ("Multi-Rapid Help", "cli-multi-rapid --help"),
        ("List Phases", "cli-multi-rapid phase stream list"),
        ("System Status", "cli-multi-rapid system status"),
    ],
    "Development": [
        ("Install Dependencies", "pip install -r requirements.txt"),
        ("Run Tests", "pytest -v"),
        ("Format Code", "black ."),
        ("Type Check", "mypy src/"),
    ],
    "Workflows": [
        ("Stream A (Dry)", "cli-multi-rapid phase stream run stream-a --dry"),
        ("Validate Config", "cli-multi-rapid validate"),
        ("Health Check", "cli-multi-rapid health"),
    ],
}


class TerminalGUI(QMainWindow):
    """Main GUI application window"""
    
    def __init__(self):
        super().__init__()
        self.command_runner = CommandRunner()
        self.tab_counter = 0
        
        self.setup_ui()
        self.setWindowTitle("CLI Multi-Rapid Terminal")
        self.resize(1200, 800)
        
    def setup_ui(self):
        """Setup main GUI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Command bar
        cmd_layout = QHBoxLayout()
        cmd_layout.addWidget(QLabel("Command:"))
        
        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Consolas", 10))
        self.command_input.returnPressed.connect(self.run_command_from_input)
        cmd_layout.addWidget(self.command_input, 1)
        
        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self.run_command_from_input)
        cmd_layout.addWidget(run_btn)
        
        layout.addLayout(cmd_layout)
        
        # Quick Actions toolbar
        self.setup_quick_actions(layout)
        
        # Terminal tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tab_widget, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status()
        
        # Start with a default tab
        self.new_tab("cli-multi-rapid --help")
        
    def setup_quick_actions(self, layout):
        """Setup Quick Actions toolbar"""
        for category, actions in QUICK_ACTIONS.items():
            group_layout = QHBoxLayout()
            group_layout.addWidget(QLabel(f"{category}:"))
            
            for label, command in actions:
                btn = QPushButton(label)
                btn.clicked.connect(lambda checked, cmd=command: self.run_command(cmd))
                btn.setMaximumWidth(120)
                group_layout.addWidget(btn)
                
            group_layout.addStretch()
            layout.addLayout(group_layout)
            
    def run_command_from_input(self):
        """Run command from input field"""
        command = self.command_input.text().strip()
        if command:
            self.run_command(command)
            self.command_input.clear()
            
    def run_command(self, command: str):
        """Run command in new tab"""
        try:
            req = self.command_runner.create_request(command)
            valid, msg = self.command_runner.validate_request(req)
            
            if not valid:
                self.status_bar.showMessage(f"Error: {msg}", 5000)
                return
                
            self.new_tab_with_request(req)
            
        except Exception as e:
            self.status_bar.showMessage(f"Error: {e}", 5000)
            
    def new_tab(self, command: str):
        """Create new terminal tab"""
        req = self.command_runner.create_request(command)
        self.new_tab_with_request(req)
        
    def new_tab_with_request(self, req: CommandRequest):
        """Create new terminal tab with specific request"""
        self.tab_counter += 1
        tab = TerminalTab(req)
        
        tab_title = f"{req.tool} ({self.tab_counter})"
        index = self.tab_widget.addTab(tab, tab_title)
        self.tab_widget.setCurrentIndex(index)
        
    def close_tab(self, index):
        """Close terminal tab"""
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        if widget:
            widget.close()
            
    def update_status(self):
        """Update status bar"""
        cwd = os.getcwd()
        shell = self.command_runner.default_shell
        python_path = sys.executable
        
        status_text = f"CWD: {cwd} | Shell: {shell} | Python: {python_path}"
        self.status_bar.showMessage(status_text)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("CLI Multi-Rapid Terminal")
    app.setApplicationVersion("1.0.0")
    
    window = TerminalGUI()
    window.show()
    
    sys.exit(app.exec())

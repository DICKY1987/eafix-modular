#!/usr/bin/env python3
"""
CLI Multi-Rapid Terminal GUI
Replaces VS Code interface with a dedicated terminal application
"""

import sys
import os
import subprocess
import asyncio
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QToolBar, QStatusBar,
    QTabWidget, QGroupBox, QGridLayout, QLabel, QSplitter
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QAction, QIcon, QPalette, QColor


class CLIExecutorThread(QThread):
    """Execute CLI commands in background thread"""
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    command_finished = pyqtSignal(int)
    
    def __init__(self, command, working_dir=None):
        super().__init__()
        self.command = command
        self.working_dir = working_dir or os.getcwd()
        self.process = None
        
    def run(self):
        try:
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            while True:
                output = self.process.stdout.readline()
                if output == '' and self.process.poll() is not None:
                    break
                if output:
                    self.output_received.emit(output.strip())
            
            # Get any remaining error output
            stderr = self.process.stderr.read()
            if stderr:
                self.error_received.emit(stderr.strip())
                
            return_code = self.process.wait()
            self.command_finished.emit(return_code)
            
        except Exception as e:
            self.error_received.emit(f"Error executing command: {str(e)}")
            self.command_finished.emit(-1)


class TerminalWidget(QTextEdit):
    """Terminal output display widget"""
    
    def __init__(self):
        super().__init__()
        self.setup_appearance()
        self.command_history = []
        
    def setup_appearance(self):
        # Terminal-like appearance
        font = QFont("Consolas", 10)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Dark theme
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                selection-background-color: #0066cc;
            }
        """)
        
        self.setReadOnly(True)
        
    def append_output(self, text, color="white"):
        """Append colored text to terminal"""
        if color == "red":
            formatted_text = f'<span style="color: #ff6b6b;">{text}</span>'
        elif color == "green":
            formatted_text = f'<span style="color: #51cf66;">{text}</span>'
        elif color == "yellow":
            formatted_text = f'<span style="color: #ffd43b;">{text}</span>'
        elif color == "cyan":
            formatted_text = f'<span style="color: #22d3ee;">{text}</span>'
        else:
            formatted_text = text
            
        self.append(formatted_text)
        # Auto-scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class CommandInputWidget(QLineEdit):
    """Command input with history support"""
    command_entered = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.command_history = []
        self.history_index = -1
        self.setPlaceholderText("Enter CLI command (press Tab for suggestions)...")
        
        # Styling
        self.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d30;
                color: white;
                border: 1px solid #404040;
                padding: 8px;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            command = self.text().strip()
            if command:
                self.command_entered.emit(command)
                self.add_to_history(command)
                self.clear()
        elif event.key() == Qt.Key.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down:
            self.navigate_history(1)
        else:
            super().keyPressEvent(event)
            
    def add_to_history(self, command):
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
    def navigate_history(self, direction):
        if not self.command_history:
            return
            
        self.history_index += direction
        self.history_index = max(0, min(self.history_index, len(self.command_history)))
        
        if self.history_index < len(self.command_history):
            self.setText(self.command_history[self.history_index])


class QuickActionsWidget(QWidget):
    """Quick action buttons panel"""
    button_clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # VS Code tasks converted to buttons
        self.create_task_group("CLI Platform", [
            ("📋 Help", "cli-multi-rapid --help"),
            ("📊 Status", "cli-multi-rapid workflow-status"),
            ("✅ Compliance", "cli-multi-rapid compliance report"),
            ("🎯 Quick Test", 'cli-multi-rapid greet "GUI User"'),
        ], layout)
        
        self.create_task_group("Workflows", [
            ("📋 List Streams", "cli-multi-rapid phase stream list"),
            ("🏗️ Run Stream A", "cli-multi-rapid phase stream run stream-a --dry"),
            ("📊 Stream Status", "python -m workflows.orchestrator status"),
            ("🔧 Execute Phase", "python -m workflows.orchestrator run-phase phase1"),
        ], layout)
        
        self.create_task_group("Development", [
            ("🧪 Run Tests", "pytest tests/ -v --cov=src"),
            ("🎨 Format Code", "black src/ tests/ && isort src/ tests/"),
            ("🔒 Security Scan", "bandit -r src/ -f json"),
            ("🔧 Install Deps", "pip install -r requirements.txt"),
        ], layout)
        
        self.setLayout(layout)
        
    def create_task_group(self, title, tasks, parent_layout):
        """Create a group of task buttons"""
        group_box = QGroupBox(title)
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #404040;
                border-radius: 5px;
                margin: 5px 0px;
                padding-top: 10px;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        grid_layout = QGridLayout()
        
        for i, (name, command) in enumerate(tasks):
            button = QPushButton(name)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #0066cc;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0052a3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """)
            button.clicked.connect(lambda checked, cmd=command: self.button_clicked.emit(cmd))
            grid_layout.addWidget(button, i // 2, i % 2)
            
        group_box.setLayout(grid_layout)
        parent_layout.addWidget(group_box)


class CLIMultiRapidGUI(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_executor = None
        self.working_directory = Path("C:/Users/Richard Wilks/cli_multi_rapid_DEV")
        self.setup_ui()
        self.setup_theme()
        self.show_welcome_message()
        
    def setup_ui(self):
        self.setWindowTitle("CLI Multi-Rapid Enterprise System - Terminal Interface")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with splitter
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Create horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Quick actions
        self.quick_actions = QuickActionsWidget()
        self.quick_actions.button_clicked.connect(self.execute_command)
        self.quick_actions.setMaximumWidth(300)
        splitter.addWidget(self.quick_actions)
        
        # Right panel - Terminal
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout()
        
        # Terminal output
        self.terminal = TerminalWidget()
        terminal_layout.addWidget(self.terminal)
        
        # Command input
        self.command_input = CommandInputWidget()
        self.command_input.command_entered.connect(self.execute_command)
        terminal_layout.addWidget(self.command_input)
        
        terminal_widget.setLayout(terminal_layout)
        splitter.addWidget(terminal_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
        
    def setup_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: white;
            }
            QWidget {
                background-color: #1e1e1e;
                color: white;
            }
            QGroupBox {
                background-color: #2d2d30;
            }
        """)
        
    def create_toolbar(self):
        """Create main toolbar"""
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2d2d30;
                border: none;
                spacing: 5px;
            }
        """)
        
        # Add common actions
        help_action = QAction("📋 Help", self)
        help_action.triggered.connect(lambda: self.execute_command("cli-multi-rapid --help"))
        toolbar.addAction(help_action)
        
        status_action = QAction("📊 Status", self)
        status_action.triggered.connect(lambda: self.execute_command("cli-multi-rapid workflow-status"))
        toolbar.addAction(status_action)
        
        streams_action = QAction("🔄 Streams", self)
        streams_action.triggered.connect(lambda: self.execute_command("cli-multi-rapid phase stream list"))
        toolbar.addAction(streams_action)
        
        toolbar.addSeparator()
        
        clear_action = QAction("🧹 Clear", self)
        clear_action.triggered.connect(self.terminal.clear)
        toolbar.addAction(clear_action)
        
        self.addToolBar(toolbar)
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #0066cc;
                color: white;
                border: none;
            }
        """)
        
        # Add status items
        self.status_bar.showMessage("🚀 CLI Multi-Rapid System Ready | 99% Target")
        
        # Add permanent widgets
        self.python_label = QLabel("Python 3.11.9")
        self.python_label.setStyleSheet("color: white; margin-right: 10px;")
        self.status_bar.addPermanentWidget(self.python_label)
        
        # Time label
        self.time_label = QLabel()
        self.time_label.setStyleSheet("color: white;")
        self.status_bar.addPermanentWidget(self.time_label)
        
        # Update time every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()
        
        self.setStatusBar(self.status_bar)
        
    def update_time(self):
        """Update time display"""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)
        
    def show_welcome_message(self):
        """Display welcome message"""
        self.terminal.append_output("=" * 60, "cyan")
        self.terminal.append_output("  CLI Multi-Rapid Enterprise System", "cyan")
        self.terminal.append_output("  Terminal GUI Interface", "cyan")
        self.terminal.append_output("=" * 60, "cyan")
        self.terminal.append_output("")
        self.terminal.append_output("🚀 System Ready!", "green")
        self.terminal.append_output("📊 Platform Status: 99% Complete", "green")
        self.terminal.append_output("🎯 Working Directory: " + str(self.working_directory), "yellow")
        self.terminal.append_output("")
        self.terminal.append_output("💡 Use the buttons on the left or type commands below", "cyan")
        self.terminal.append_output("")
        self.show_prompt()
        
    def show_prompt(self):
        """Show command prompt"""
        prompt = f"{self.working_directory.name}> "
        self.terminal.append_output(prompt, "white")
        
    def execute_command(self, command):
        """Execute a command"""
        if self.current_executor and self.current_executor.isRunning():
            self.terminal.append_output("⚠️ Command already running. Please wait...", "yellow")
            return
            
        # Display the command being executed
        self.terminal.append_output(f"$ {command}", "cyan")
        
        # Update status
        self.status_bar.showMessage(f"Executing: {command}")
        
        # Create and start executor thread
        self.current_executor = CLIExecutorThread(command, str(self.working_directory))
        self.current_executor.output_received.connect(lambda text: self.terminal.append_output(text, "white"))
        self.current_executor.error_received.connect(lambda text: self.terminal.append_output(text, "red"))
        self.current_executor.command_finished.connect(self.command_completed)
        self.current_executor.start()
        
    def command_completed(self, return_code):
        """Handle command completion"""
        if return_code == 0:
            self.terminal.append_output("✅ Command completed successfully", "green")
        else:
            self.terminal.append_output(f"❌ Command failed with return code: {return_code}", "red")
            
        self.terminal.append_output("")
        self.show_prompt()
        self.status_bar.showMessage("🚀 CLI Multi-Rapid System Ready | 99% Target")


def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("CLI Multi-Rapid Terminal GUI")
    app.setApplicationVersion("1.0")
    
    # Apply dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    # Create and show main window
    window = CLIMultiRapidGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

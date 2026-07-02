from __future__ import annotations

try:
    from PyQt6 import QtWidgets, QtGui, QtCore  # type: ignore
    from gui_terminal.core.terminal_widget import TerminalWidget
    from gui_terminal.security.policy_manager import PolicyManager
    from gui_terminal.core.cost_integration import CostTrackerBridge, CostEvent
    from gui_terminal.core.logging_config import StructuredLogger, LoggerConfig
    from gui_terminal.ui.cli_interface import CLIExecutionInterface
except Exception:  # pragma: no cover - allow headless import
    QtWidgets = None  # type: ignore
    QtGui = None  # type: ignore
    QtCore = None  # type: ignore
    TerminalWidget = None  # type: ignore
    PolicyManager = None  # type: ignore
    CostTrackerBridge = None  # type: ignore
    CostEvent = None  # type: ignore
    StructuredLogger = None  # type: ignore
    LoggerConfig = None  # type: ignore
    CLIExecutionInterface = None  # type: ignore


class MainWindow:  # pragma: no cover - constructed only when PyQt present
    def __init__(self, config: dict | None = None) -> None:
        self.title = "CLI Multi-Rapid Terminal"
        self._cfg = config or {}
        if QtWidgets is None:
            # Headless placeholder retains API compatibility
            self._w = None
            return

        self._w = QtWidgets.QMainWindow()
        self._w.setWindowTitle(self.title)

        # Create single CLI interface (simplified)
        self._setup_single_interface()

        # Initialize component managers (for backward compatibility)
        self._policy = PolicyManager() if PolicyManager else None
        self._logger = StructuredLogger(LoggerConfig(audit_log_file="./gui_terminal_audit.log")) if StructuredLogger else None
        self._cost = CostTrackerBridge() if CostTrackerBridge else None

        # Status bar
        status = QtWidgets.QStatusBar()
        self._w.setStatusBar(status)
        status.showMessage("CLI Terminal Ready - Professional command-line interface with enterprise security")

        # Toolbar for essential actions
        toolbar = self._w.addToolBar("Actions")

        # Settings action
        settings_action = toolbar.addAction("⚙️ Settings")
        settings_action.setToolTip("Open application settings")
        settings_action.triggered.connect(self._open_settings)  # type: ignore[attr-defined]

        # Help action
        help_action = toolbar.addAction("❓ Help")
        help_action.setToolTip("Open help documentation")
        help_action.triggered.connect(self._open_help)  # type: ignore[attr-defined]

    def _setup_single_interface(self):
        """Setup the simplified single CLI interface"""
        if CLIExecutionInterface:
            self.cli_interface = CLIExecutionInterface()
            self._w.setCentralWidget(self.cli_interface)


    # --- Qt-backed methods ---
    def widget(self):  # return underlying QWidget for app wrapping
        return self._w

    def show(self) -> None:
        if self._w:
            self._w.resize(1000, 600)  # Focused window size for single interface
            self._w.show()

    def _open_settings(self):
        """Open application settings dialog"""
        from PyQt6.QtWidgets import QMessageBox  # type: ignore
        QMessageBox.information(self._w, "Settings", "Settings dialog would open here.\nConfigure: API keys, security policies, command aliases, and interface preferences.")

    def _open_help(self):
        """Open help documentation"""
        from PyQt6.QtWidgets import QMessageBox  # type: ignore
        help_text = """CLI Multi-Rapid Terminal Help

💻 Terminal Interface:
• Professional command-line interface with enterprise security
• Real-time command execution with output streaming
• Command history with arrow key navigation
• Security policy enforcement prevents unauthorized commands

🔒 Security Features:
• Policy-based command filtering and validation
• Audit logging for compliance and tracking
• Resource limit enforcement
• Enterprise-grade security controls

⚙️ Features:
• Command history management
• Real-time output display with color coding
• Background command execution
• Cross-platform compatibility

🚀 Usage:
• Type commands in the input field
• Press Enter or click Execute to run
• Use arrow keys to navigate command history
• All commands are validated by security policies

Enterprise backend systems remain fully operational including cost tracking, audit logging, and integration capabilities."""
        QMessageBox.information(self._w, "Help", help_text)

    # --- Simplified interface methods ---
    def get_cli_interface(self):
        """Get the CLI interface for external access"""
        return getattr(self, 'cli_interface', None)

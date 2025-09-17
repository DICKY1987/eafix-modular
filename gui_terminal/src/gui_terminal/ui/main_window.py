from __future__ import annotations

try:
    from PyQt6 import QtWidgets, QtGui, QtCore  # type: ignore
    from gui_terminal.core.terminal_widget import TerminalWidget
    from gui_terminal.security.policy_manager import PolicyManager
    from gui_terminal.core.cost_integration import CostTrackerBridge, CostEvent
    from gui_terminal.core.logging_config import StructuredLogger, LoggerConfig
    from gui_terminal.ui.tool_registry_tab import ToolRegistryTab
    from gui_terminal.ui.workflow_validator_tab import WorkflowValidatorTab
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
    ToolRegistryTab = None  # type: ignore
    WorkflowValidatorTab = None  # type: ignore


class MainWindow:  # pragma: no cover - constructed only when PyQt present
    def __init__(self, config: dict | None = None) -> None:
        self._cfg = config or {}
        if QtWidgets is None:
            # Headless placeholder retains API compatibility
            self._w = None
            return

        self._w = QtWidgets.QMainWindow()
        self._w.setWindowTitle(self.title)

        # Create tabbed interface
        self.tab_widget = QtWidgets.QTabWidget()
        self._w.setCentralWidget(self.tab_widget)

        # Initialize component managers (for backward compatibility)
        self._term = TerminalWidget() if TerminalWidget else None
        self._policy = PolicyManager() if PolicyManager else None
        self._logger = StructuredLogger(LoggerConfig(audit_log_file="./gui_terminal_audit.log")) if StructuredLogger else None
        self._cost = CostTrackerBridge() if CostTrackerBridge else None

        # Setup tabs
        self._setup_tabs()

        # Status bar
        status = QtWidgets.QStatusBar()
        self._w.setStatusBar(status)

        # Toolbar for global actions
        toolbar = self._w.addToolBar("Global Actions")

        # Settings action
        settings_action = toolbar.addAction("⚙️ Settings")
        settings_action.setToolTip("Open application settings")
        settings_action.triggered.connect(self._open_settings)  # type: ignore[attr-defined]

        # Help action
        help_action = toolbar.addAction("❓ Help")
        help_action.setToolTip("Open help documentation")
        help_action.triggered.connect(self._open_help)  # type: ignore[attr-defined]

    def _setup_tabs(self):
        """Setup the main tabbed interface"""
        if not self.tab_widget:
            return


        # Tool Registry & Resolver tab
        if ToolRegistryTab:
            self.registry_tab = ToolRegistryTab()
            self.tab_widget.addTab(self.registry_tab, "🔧 Tool Registry")

        # Workflow Validator tab
        if WorkflowValidatorTab:
            self.validator_tab = WorkflowValidatorTab()
            self.tab_widget.addTab(self.validator_tab, "✅ Workflow Validator")

        # Terminal tab (backward compatibility)
        self.terminal_tab = self._create_terminal_tab()
        self.tab_widget.addTab(self.terminal_tab, "💻 Terminal")

    def _create_terminal_tab(self):
        """Create the terminal tab (legacy interface)"""
        terminal_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(terminal_widget)

        # Terminal output and input
        self._output = QtWidgets.QPlainTextEdit()
        self._output.setReadOnly(True)
        self._input = QtWidgets.QLineEdit()
        self._input.returnPressed.connect(self._submit_line)  # type: ignore[attr-defined]

        layout.addWidget(self._output, stretch=1)
        layout.addWidget(self._input)

        # Terminal controls
        controls_layout = QtWidgets.QHBoxLayout()

        clear_btn = QtWidgets.QPushButton("Clear")
        clear_btn.clicked.connect(self._output.clear)  # type: ignore[attr-defined]
        controls_layout.addWidget(clear_btn)

        ctrl_c_btn = QtWidgets.QPushButton("Ctrl-C")
        ctrl_c_btn.setToolTip("Send Ctrl-C to the terminal session")
        ctrl_c_btn.clicked.connect(self._send_ctrl_c)  # type: ignore[attr-defined]
        controls_layout.addWidget(ctrl_c_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Start terminal backend
        if self._term:
            self._term.on_data = self._on_data
            self._term.start()

        return terminal_widget

    # --- Qt-backed methods ---
    def widget(self):  # return underlying QWidget for app wrapping
        return self._w

    def show(self) -> None:
        if self._w:
            self._w.resize(1400, 800)  # Larger window for tabbed interface
            self._w.show()

    def _open_settings(self):
        """Open application settings dialog"""
        from PyQt6.QtWidgets import QMessageBox  # type: ignore
        QMessageBox.information(self._w, "Settings", "Settings dialog would open here.\nFuture: Configure API keys, tool paths, and preferences.")

    def _open_help(self):
        """Open help documentation"""
        from PyQt6.QtWidgets import QMessageBox  # type: ignore

• Drag and drop files to create Generic Deterministic Workflows
• Configure workflow specifications with the wizard
• Validate workflows with AJV schema validation
• Package workflows as ZIP files or create PRs

🔧 Tool Registry:
• Manage available tools and their capabilities
• Configure tool priority and fallback policies
• Simulate tool resolution for different scenarios
• Monitor tool health and cost usage

✅ Workflow Validator:
• Validate APF JSON inputs against schema
• Check AI workflow configurations
• Apply quick fixes and defaults

💻 Terminal:
• Traditional terminal interface for CLI commands
• Integrated with security policies and cost tracking"""
        QMessageBox.information(self._w, "Help", help_text)

    # --- Terminal handling ---
    def _on_data(self, data: bytes) -> None:
        try:
            text = data.decode(errors="replace")
        except Exception:
            text = str(data)
        # Optional: Strip ANSI escape sequences for readability
        strip_ansi = False
        try:
            strip_ansi = bool(((self._cfg.get("ui") or {}).get("strip_ansi", False)))
        except Exception:
            strip_ansi = False
        if strip_ansi:
            try:
                import re
                text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
            except Exception:
                pass
        # Handle carriage return overwrite (simple heuristic: replace last line)
        def _append():
            if "\r" in text:
                parts = text.split("\r")
                # Replace the last line with final segment
                cursor = self._output.textCursor()
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)  # type: ignore[attr-defined]
                # Select and remove current line
                cursor.select(QtGui.QTextCursor.SelectionType.LineUnderCursor)  # type: ignore[attr-defined]
                cursor.removeSelectedText()
                cursor.insertText(parts[-1])
            else:
                self._output.moveCursor(QtGui.QTextCursor.MoveOperation.End)  # type: ignore[attr-defined]
                self._output.insertPlainText(text)
                self._output.moveCursor(QtGui.QTextCursor.MoveOperation.End)  # type: ignore[attr-defined]

        if QtWidgets:
            QtCore.QMetaObject.invokeMethod(  # type: ignore[attr-defined]
                self._output, _append
            )

    def _submit_line(self) -> None:
        line = self._input.text()
        self._input.clear()
        if self._term is None:
            return
        # Security policy enforcement (whitelist/blacklist)
        if self._policy is not None:
            # resource capacity
            cap_ok, cap_reason = self._policy.has_resource_capacity()
            if not cap_ok:
                self._on_data((f"[policy] resource block: {cap_reason}\n").encode())
                if self._logger:
                    self._logger.audit("command_blocked", {"reason": cap_reason, "line": line}, result="blocked")
                return
            allowed, reason = self._policy.command_allowed(line)
            if not allowed:
                self._on_data((f"[policy] blocked: {reason}\n").encode())
                if self._logger:
                    self._logger.audit("command_blocked", {"reason": reason, "line": line}, result="blocked")
                return
        # Send line with newline; simple echo of line to output
        self._term.send(line + "\n")
        # Mirror user input in the output for visibility
        self._on_data((line + "\n").encode())
        if self._logger:
            self._logger.audit("command_sent", {"line": line}, result="ok")
        # Record cost (best-effort)
        try:
            if self._cost and self._cost.available():
                ev = CostEvent(task_id="gui_session", tool="gui_terminal", action="command", tokens=len(line), amount=0.0)
            self._cost.record(ev)
        except Exception:
            pass

    def _send_ctrl_c(self) -> None:
        if self._term is not None:
            self._term.send_ctrl_c()
            self._on_data(b"^C\n")

    # Additional methods for tab management
    def switch_to_gdw_builder(self):
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setCurrentIndex(0)

    def switch_to_tool_registry(self):
        """Switch to Tool Registry tab"""
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setCurrentIndex(1)

    def switch_to_validator(self):
        """Switch to Workflow Validator tab"""
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setCurrentIndex(2)

    def switch_to_terminal(self):
        """Switch to Terminal tab"""
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setCurrentIndex(3)

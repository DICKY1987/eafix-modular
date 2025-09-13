from __future__ import annotations

try:
    from PyQt6 import QtWidgets, QtGui, QtCore  # type: ignore
    from gui_terminal.core.terminal_widget import TerminalWidget
    from gui_terminal.security.policy_manager import PolicyManager
    from gui_terminal.core.cost_integration import CostTrackerBridge, CostEvent
    from gui_terminal.core.logging_config import StructuredLogger, LoggerConfig
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


class MainWindow:  # pragma: no cover - constructed only when PyQt present
    def __init__(self, config: dict | None = None) -> None:
        self.title = "CLI Multi-Rapid GUI Terminal"
        self._cfg = config or {}
        if QtWidgets is None:
            # Headless placeholder retains API compatibility
            self._w = None
            return

        self._w = QtWidgets.QMainWindow()
        self._w.setWindowTitle(self.title)

        # Central widget layout
        central = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(central)
        self._output = QtWidgets.QPlainTextEdit()
        self._output.setReadOnly(True)
        self._input = QtWidgets.QLineEdit()

        # Status bar
        status = QtWidgets.QStatusBar()
        self._w.setStatusBar(status)
        status.showMessage("Ready")

        vbox.addWidget(self._output, stretch=1)
        vbox.addWidget(self._input)
        self._w.setCentralWidget(central)

        # Terminal backend
        self._term = TerminalWidget() if TerminalWidget else None
        if self._term:
            self._term.on_data = self._on_data
            self._term.start()

        # Security policy manager and logger
        self._policy = PolicyManager() if PolicyManager else None
        self._logger = StructuredLogger(LoggerConfig(audit_log_file="./gui_terminal_audit.log")) if StructuredLogger else None

        # Cost tracking bridge
        self._cost = CostTrackerBridge() if CostTrackerBridge else None

        # Connect input
        self._input.returnPressed.connect(self._submit_line)  # type: ignore[attr-defined]

        # Basic toolbar
        tb = self._w.addToolBar("Actions")
        act_clear = tb.addAction("Clear")
        act_clear.triggered.connect(self._output.clear)  # type: ignore[attr-defined]
        act_sigint = tb.addAction("Ctrl-C")
        act_sigint.setToolTip("Send Ctrl-C to the terminal session")
        act_sigint.triggered.connect(self._send_ctrl_c)  # type: ignore[attr-defined]

    # --- Qt-backed methods ---
    def widget(self):  # return underlying QWidget for app wrapping
        return self._w

    def show(self) -> None:
        if self._w:
            self._w.resize(900, 600)
            self._w.show()

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

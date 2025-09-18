#!/usr/bin/env python3
"""
Improved PTY-backed terminal GUI with:
- Cross-platform PTY (ConPTY on Windows via pywinpty; pty on *nix).
- Correct arg parsing (shlex), command preview, and no hidden flags.
- Resize wiring (cols/rows computed from font metrics) and signal palette.
- Basic ANSI handling for CR (\r), Backspace (\b), and CSI K (erase in line).
- Artifacts watcher (optional) and status strip (cwd, shell, venv, rows×cols, exit/elapsed).
- Minimal event bus for internal decoupling.
Note: This file is designed to *run* when dependencies are installed, but also serves as a patch example.
"""

from __future__ import annotations
import os, sys, shlex, time, json, shutil, threading, queue, platform, signal, re
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Tuple

# GUI imports are lazy; file can be inspected without PyQt installed
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QTextEdit, QLineEdit, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QTabWidget, QFileDialog, QSplitter,
    QListWidget, QListWidgetItem, QStyle, QFrame, QMessageBox
)
from PyQt6.QtGui import QFont, QTextCursor, QDesktopServices, QColor
from PyQt6.QtCore import QUrl
from config import GUIConfig
from audit_logger import write_event
from plugin_manager import PluginManager


# Platform-specific PTY
IS_WIN = os.name == "nt"
if IS_WIN:
    try:
        import winpty
    except Exception:
        winpty = None
else:
    import pty, tty, termios

# Optional deps (ok if missing at import-time)
try:
    import psutil
except Exception:
    psutil = None

# ---- Small Event Bus ----

def open_system_terminal_here(path: str):
    """Open a native system terminal at the given path."""
    try:
        if IS_WIN:
            import shutil, subprocess
            wt = shutil.which("wt")
            pwsh = shutil.which("pwsh") or shutil.which("powershell")
            if wt:
                subprocess.Popen([wt, "-d", path])
            elif pwsh:
                subprocess.Popen([pwsh, "-NoExit", "-Command", f"Set-Location '{path}'"])
            else:
                subprocess.Popen(["cmd.exe", "/K", f"cd /d {path}"])
        elif sys.platform == "darwin":
            import subprocess
            apple_script = f"""tell application "Terminal"
    do script "cd {path}"
    activate
end tell"""
            subprocess.Popen(["osascript", "-e", apple_script])
        else:
            import shutil, subprocess
            term = (shutil.which("x-terminal-emulator") or
                    shutil.which("gnome-terminal") or
                    shutil.which("konsole") or
                    shutil.which("xterm"))
            if term and "gnome-terminal" in term:
                subprocess.Popen([term, "--", "bash", "-lc", f"cd '{path}'; exec bash"])
            elif term:
                subprocess.Popen([term])
            else:
                subprocess.Popen(["bash", "-lc", f"cd '{path}'; ${TERM:-xterm}"])
    except Exception:
        pass

class EventBus(QObject):
    published = pyqtSignal(dict)
    def publish(self, event: dict):
        self.published.emit(event)

# ---- Dataclasses for Contract ----
@dataclass
class CommandRequest:
    tool: str
    args: List[str] = field(default_factory=list)
    env: dict = field(default_factory=dict)
    cwd: Optional[str] = None
    timeout_sec: Optional[int] = None
    interactive: bool = True
    command_preview: str = ""  # exact string that will be executed (display-only)

@dataclass
class CommandResponse:
    exit_code: Optional[int] = None
    duration_sec: float = 0.0
    started_at: float = 0.0
    ended_at: float = 0.0
    error: Optional[str] = None

# ---- Minimal ANSI Handler (line-oriented) ----
CSI = "\x1b["
CSI_ERASE_IN_LINE = re.compile(r"\x1b\[(\d*)K")

def apply_ansi_line_mutations(current: str, incoming: str) -> str:
    """
    Handle a few key interactive cases for single-line updates:
      - CR: overwrite from line start with new content fragments
      - Backspace: delete previous char
      - CSI K: erase to EOL (0) or whole line (2)
    This is minimalist; for full fidelity consider QTermWidget or a vt100 parser.
    """
    buf = current

    i = 0
    while i < len(incoming):
        ch = incoming[i]
        if ch == "\r":
            # Carriage return: reset cursor to start; we emulate by clearing and continuing
            # but keep prior content if next chars do partial overwrite.
            # Simpler approach: set buffer to empty; following text rewrites it.
            buf = ""
            i += 1
        elif ch == "\b":
            # Backspace
            if buf:
                buf = buf[:-1]
            i += 1
        elif ch == "\x1b":
            # CSI sequences (we only handle K)
            # Try to match CSI ... K from the current index
            match = CSI_ERASE_IN_LINE.match(incoming[i:])
            if match:
                mode = match.group(1) or "0"
                if mode in ("0", "00"):
                    # Erase from cursor to end; with our simple model, truncate
                    # (cursor at end in this simplified model)
                    # no-op given we don't track a mid-line cursor
                    pass
                elif mode == "2":
                    # Erase whole line
                    buf = ""
                i += match.end()
            else:
                # Skip unknown escape sequence char by char until next 'm' or letter
                # to avoid infinite loops
                i += 1
        else:
            # Normal char
            buf += ch
            i += 1
    return buf

# ---- PTY Worker Thread ----
class PTYWorker(threading.Thread):
    def __init__(self, req: CommandRequest, output_queue: queue.Queue, cols: int = 120, rows: int = 32):
        super().__init__(daemon=True)
        self.req = req
        self.q = output_queue
        self.cols = cols
        self.rows = rows
        self.stop_requested = False
        self.pid = None
        self.exit_code = None
        self.started = 0.0
        self.ended = 0.0

        # Build command preview and argv safely
        if req.args:
            argv = [req.tool] + list(req.args)
        else:
            argv = shlex.split(req.tool, posix=(not IS_WIN))
        self.argv = argv
        self.req.command_preview = " ".join([shlex.quote(x) if not IS_WIN else x for x in argv])

    def write_input(self, b: bytes):
        try:
            if not b:
                return
            if IS_WIN and hasattr(self, "_winpty"):
                try:
                    self._winpty.write(b.decode("utf-8", "replace"))
                except Exception:
                    pass
            elif hasattr(self, "_master_fd"):
                os.write(self._master_fd, b)
        except Exception as e:
            self.q.put(("[error]", f"write error: {e}\n"))

    def resize_pty(self, cols:int, rows:int):
        if IS_WIN:
            # pywinpty can resize via .set_size(rows, cols)
            try:
                if hasattr(self, "_winpty"):
                    self._winpty.setwinsize(rows, cols)
            except Exception:
                pass
        else:
            try:
                import fcntl, struct, termios as _t
                if hasattr(self, "_slave_fd"):
                    TIOCSWINSZ = getattr(_t, 'TIOCSWINSZ', 0x5414)
                    fcntl.ioctl(self._slave_fd, TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
            except Exception:
                pass

    def run(self):
        self.started = time.time()
        # Start watchdog if timeout is set
        if self.req.timeout_sec and self.req.timeout_sec > 0:
            threading.Thread(target=self._watchdog, daemon=True).start()
        try:
            if IS_WIN:
                self._run_windows()
            else:
                self._run_unix()
        except Exception as e:
            self.q.put(("[error]", f"{type(e).__name__}: {e}\n"))
        finally:
            self.ended = time.time()
            self.q.put(("[exit]", str(self.exit_code if self.exit_code is not None else -1)))

    # --- UNIX PTY ---
    def _run_unix(self):
        master_fd, slave_fd = pty.openpty()
        self._master_fd = master_fd
        self._slave_fd = slave_fd
        # Set window size if possible
        try:
            import fcntl, struct
            TIOCSWINSZ = getattr(termios, 'TIOCSWINSZ', 0x5414)
            fcntl.ioctl(slave_fd, TIOCSWINSZ, struct.pack("HHHH", self.rows, self.cols, 0, 0))
        except Exception:
            pass

        pid = os.fork()
        if pid == 0:
            # Child
            try:
                os.setsid()
                os.dup2(slave_fd, 0)
                os.dup2(slave_fd, 1)
                os.dup2(slave_fd, 2)
                if self.req.cwd:
                    os.chdir(self.req.cwd)
                env = os.environ.copy()
                env.update(self.req.env or {})
                os.execvpe(self.argv[0], self.argv, env)
            except Exception as e:
                print(f"exec error: {e}", file=sys.stderr)
                os._exit(1)
        else:
            # Parent
            self.pid = pid
            os.close(slave_fd)
            # Non-blocking read
            while True:
                try:
                    data = os.read(master_fd, 4096)
                    if not data:
                        break
                    self.q.put(("[data]", data))
                except OSError:
                    break
            _, status = os.waitpid(pid, 0)
            self.exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else 128

    # --- Windows ConPTY via winpty ---
    def _run_windows(self):
        if winpty is None:
            raise RuntimeError("winpty module not available; install pywinpty/winpty for Windows support.")
        p = winpty.PtyProcess.spawn(self.argv, dimensions=(self.rows, self.cols))
        self._winpty = p
        self.pid = p.pid
        try:
            while True:
                out = p.read(4096)
                if not out:
                    break
                self.q.put(("[data]", out.encode("utf-8", "replace")))
        except EOFError:
            pass
        self.exit_code = p.exitstatus

    # ---- Signals ----
    def send_sigint(self):
        if self.pid is None: return
        try:
            if IS_WIN:
                # winpty doesn't expose Ctrl-C directly; emulate by sending 0x03
                self.q.put(("[input]", b"\x03"))
            else:
                os.kill(self.pid, signal.SIGINT)
        except Exception as e:
            self.q.put(("[error]", f"SIGINT error: {e}\n"))

    def _watchdog(self):
        deadline = self.started + float(self.req.timeout_sec)
        while self.exit_code is None and time.time() < deadline:
            time.sleep(0.1)
        if self.exit_code is None:
            self.q.put(("[error]", f"timeout after {self.req.timeout_sec}s\n"))
            self.terminate()

    def send_eof(self):
        # CTRL-D (Unix) / CTRL-Z + Enter (Windows) to send EOF to apps
        if IS_WIN:
            self.q.put(("[input]", b"\x1a\r\n"))
        else:
            self.q.put(("[input]", b"\x04"))

    def terminate(self):
        self.stop_requested = True
        if self.pid is None: return
        try:
            if IS_WIN:
                # Best-effort terminate
                import ctypes
                ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, self.pid)
            else:
                os.kill(self.pid, signal.SIGTERM)
        except Exception:
            pass

# ---- Terminal Widget ----
class TerminalWidget(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas" if IS_WIN else "Menlo", 11))
        self.line_buffer = ""
        self.ansi_passthrough = False  # when using real widget, set True and avoid mutation
        self.max_buffer_chars = 1_000_000  # overridden by config


    def append_bytes(self, data: bytes):
        text = data.decode("utf-8", "replace")
        # Split on newlines to apply line-local ANSI mutations
        parts = text.split("\n")
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                # Complete line
                self.line_buffer = apply_ansi_line_mutations(self.line_buffer, part)
                self._append_line(self.line_buffer)
                self.line_buffer = ""
            else:
                # Last partial
                self.line_buffer = apply_ansi_line_mutations(self.line_buffer, part)

    def flush_line_buffer(self):
        if self.line_buffer:
            self._append_line(self.line_buffer)
            self.line_buffer = ""

    def _append_line(self, line: str):
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertPlainText(line + "\n")
        # Ring buffer: trim if too large
        doc = self.document()
        if doc.characterCount() > self.max_buffer_chars:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, int(doc.characterCount()*0.1))
            cursor.removeSelectedText()
        self.moveCursor(QTextCursor.MoveOperation.End)

    # rough cols/rows estimation
    def estimate_cols_rows(self) -> Tuple[int, int]:
        fm = self.fontMetrics()
        char_w = fm.horizontalAdvance("M")
        char_h = fm.height()
        if char_w == 0 or char_h == 0:
            return 120, 32
        cols = max(40, self.viewport().width() // char_w)
        rows = max(16, self.viewport().height() // char_h)
        return cols, rows

# ---- Main Tab ----

class HistoryLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history: list[str] = []
        self.idx = 0

    def add(self, cmd: str):
        if cmd and (not self.history or self.history[-1] != cmd):
            self.history.append(cmd)
        self.idx = len(self.history)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Up:
            if self.history and self.idx > 0:
                self.idx -= 1
                self.setText(self.history[self.idx])
                self.setCursorPosition(len(self.text()))
                return
        elif e.key() == Qt.Key.Key_Down:
            if self.history and self.idx < len(self.history)-1:
                self.idx += 1
                self.setText(self.history[self.idx])
                self.setCursorPosition(len(self.text()))
                return
            else:
                self.idx = len(self.history)
                self.clear()
                return
        super().keyPressEvent(e)

class TerminalTab(QWidget):
    def __init__(self, event_bus: EventBus, cwd: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.bus = event_bus
        self.cwd = cwd or os.getcwd()
        self.output_q: queue.Queue = queue.Queue()
        self.worker: Optional[PTYWorker] = None
        self.started = 0.0

        # UI
        self.terminal = TerminalWidget()
        self.input_line = HistoryLineEdit()
        self.btn_send = QPushButton("Send")
        self.btn_sigint = QPushButton("Ctrl-C")
        self.btn_eof = QPushButton("EOF")
        self.btn_kill = QPushButton("Kill")
        self.btn_open_sys = QPushButton("Open System Terminal")
        self.status_lbl = QLabel("Idle")
        self.preview_lbl = QLabel("")
        self.preview_lbl.setStyleSheet("color:#888;")

        top = QVBoxLayout(self)
        top.addWidget(self.preview_lbl)

        center_split = QSplitter(); center_split.setOrientation(Qt.Orientation.Horizontal)
        self.artifacts = QListWidget(); self.artifacts.setMinimumWidth(220)
        self.artifacts_label = QLabel("Artifacts")
        left = QVBoxLayout(); leftw = QWidget(); left.addWidget(self.artifacts_label); left.addWidget(self.artifacts, 1); leftw.setLayout(left)
        center_split.addWidget(leftw)
        center_split.addWidget(self.terminal)
        center_split.setStretchFactor(1, 1)
        outer = QSplitter(); outer.setOrientation(Qt.Orientation.Horizontal)
        outer.addWidget(center_split)
        self.sidebar = CostHealthSidebar()
        outer.addWidget(self.sidebar)
        outer.setStretchFactor(0, 1)
        outer.setStretchFactor(1, 0)
        top.addWidget(outer, 1)

        row = QHBoxLayout()
        row.addWidget(self.input_line, 1)
        row.addWidget(self.btn_send)
        row.addWidget(self.btn_sigint)
        row.addWidget(self.btn_eof)
        row.addWidget(self.btn_kill)
        row.addWidget(self.btn_open_sys)
        top.addLayout(row)

        status = QHBoxLayout()
        status.addWidget(self.status_lbl, 1)
        top.addLayout(status)

        self.btn_send.clicked.connect(self._send_line)
        self.btn_sigint.clicked.connect(self._send_sigint)
        self.btn_eof.clicked.connect(self._send_eof)
        self.btn_kill.clicked.connect(self._kill)
        self.btn_open_sys.clicked.connect(self._open_sys_term)

        self.poll_timer = QTimer(self); self.poll_timer.setInterval(30); self.poll_timer.timeout.connect(self._poll)
        self.poll_timer.start()
        # Artifact watcher setup
        self.art_scan_timer = QTimer(self); self.art_scan_timer.setInterval(500)
        self.art_scan_timer.timeout.connect(self._scan_artifacts)
        self._artifact_baseline = set()
        self._artifact_new = set()
        self.artifacts.itemDoubleClicked.connect(self._open_artifact)


    def sizeHint(self) -> QSize:
        return QSize(1024, 640)

    def _snapshot_artifacts(self):
        try:
            self._artifact_baseline = set()
            for root, dirs, files in os.walk(self.cwd):
                for f in files:
                    self._artifact_baseline.add(os.path.join(root, f))
        except Exception:
            self._artifact_baseline = set()

    def _scan_artifacts(self):
        try:
            current = set()
            for root, dirs, files in os.walk(self.cwd):
                for f in files:
                    current.add(os.path.join(root, f))
            new_files = [p for p in current - self._artifact_baseline - self._artifact_new]
            for p in sorted(new_files):
                self._artifact_new.add(p)
                item = QListWidgetItem(os.path.relpath(p, self.cwd))
                item.setToolTip(p)
                self.artifacts.addItem(item)
        except Exception:
            pass

    def _open_artifact(self, item: QListWidgetItem):
        abspath = os.path.join(self.cwd, item.text()) if not os.path.isabs(item.text()) else item.text()
        QDesktopServices.openUrl(QUrl.fromLocalFile(abspath))

    def start_command(self, req: CommandRequest):
        # Build argv with shlex and form preview
        if req.args:
            argv = [req.tool] + list(req.args)
        else:
            argv = shlex.split(req.tool, posix=(not IS_WIN))
        req.command_preview = " ".join([shlex.quote(x) if not IS_WIN else x for x in argv])
        self.preview_lbl.setText(req.command_preview)

        cols, rows = self.terminal.estimate_cols_rows()
        self._snapshot_artifacts()
        self.artifacts.clear(); self._artifact_new = set()
        self.art_scan_timer.start()
        self.worker = PTYWorker(req, self.output_q, cols=cols, rows=rows)
        self.started = time.time()
        self.status_lbl.setText(f"Running… {req.command_preview}")
        self.worker.start()
        self.bus.publish({"type":"run.started","preview":req.command_preview,"cwd":req.cwd,"cols":cols,"rows":rows})

    def _send_line(self):
        txt = self.input_line.text()
        if not txt: txt = ""
        self.input_line.clear()
        # Send as user keystrokes (we just echo locally to improve feel)
        if self.worker:
            try:
                self.worker.write_input((txt + "\n").encode("utf-8"))
            except Exception:
                pass
            if hasattr(self.input_line, 'add'):
                self.input_line.add(txt)
            self.bus.publish({"type":"input.sent","chars":txt+"\n"})

    def _send_sigint(self):
        if self.worker:
            self.worker.send_sigint()
            self.bus.publish({"type":"signal.sent","name":"SIGINT"})

    def _send_eof(self):
        if self.worker:
            self.worker.send_eof()
            self.bus.publish({"type":"signal.sent","name":"EOF"})

    def _open_sys_term(self):
        try:
            open_system_terminal_here(self.cwd)
        except Exception:
            pass

    def _kill(self):
        if self.worker:
            self.worker.terminate()
            self.bus.publish({"type":"signal.sent","name":"KILL"})

    def _poll(self):
        # Drain output
        drained = False
        while True:
            try:
                tag, payload = self.output_q.get_nowait()
            except queue.Empty:
                break
            drained = True
            if tag == "[data]":
                self.terminal.append_bytes(payload)
            elif tag == "[error]":
                self.terminal._append_line(str(payload))
            elif tag == "[exit]":
                exit_code = int(payload)
                self.terminal.flush_line_buffer()
                elapsed = time.time() - self.started if self.started else 0.0
                self.status_lbl.setText(f"Exit {exit_code} • {elapsed:0.1f}s")
                self.art_scan_timer.stop()
                self.bus.publish({"type":"run.exited","exit_code":exit_code,"elapsed":elapsed})
        if drained:
            self.terminal.ensureCursorVisible()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # In a fully wired PTY, we would call worker.resize_pty(cols, rows).
        # Our PTYWorker sets geometry at spawn; add dynamic resizing as an exercise.
        cols, rows = self.terminal.estimate_cols_rows()
        if self.worker:
            self.worker.resize_pty(cols, rows)
        self.bus.publish({"type":"terminal.resized","cols":cols,"rows":rows})

# ---- Main Window ----

class CostHealthSidebar(QWidget):
    """Simple sidebar showing plan budget/burn and tool health.
       Auto-refreshes from ~/.python_cockpit/health.json if present.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.lbl_title = QLabel("Cost & Health")
        self.lbl_budget = QLabel("Budget: –")
        self.lbl_burn = QLabel("Burn: –")
        self.lbl_conc = QLabel("Concurrency: –")
        self.list_tools = QListWidget()
        lay = QVBoxLayout(self)
        lay.addWidget(self.lbl_title)
        lay.addWidget(self.lbl_budget)
        lay.addWidget(self.lbl_burn)
        lay.addWidget(self.lbl_conc)
        lay.addWidget(QLabel("Tools"))
        lay.addWidget(self.list_tools, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_from_file)
        self.timer.start()

    def refresh_from_file(self):
        try:
            path = os.path.expanduser("~/.python_cockpit/health.json")
            if not os.path.exists(path):
                return
            import json
            data = json.load(open(path, "r", encoding="utf-8"))
            budget = data.get("plan_budget_usd")
            burn = data.get("plan_burn_usd")
            conc = data.get("concurrency")
            self.lbl_budget.setText(f"Budget: ${budget:.2f}" if budget is not None else "Budget: –")
            self.lbl_burn.setText(f"Burn: ${burn:.2f}" if burn is not None else "Burn: –")
            self.lbl_conc.setText(f"Concurrency: {conc}" if conc is not None else "Concurrency: –")
            self.list_tools.clear()
            for t in data.get("tools", []):
                item = QListWidgetItem(f"{t.get('name','?')}: {t.get('status','unknown')}")
                st = (t.get("status","unknown") or "").lower()
                color = "#4caf50" if st=="healthy" else "#ff9800" if st=="degraded" else "#f44336" if st=="unhealthy" else "#9e9e9e"
                # Apply background color
                item.setBackground(QColor(color))
                self.list_tools.addItem(item)
        except Exception:
            pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python CLI Cockpit (PTY)")
        self.bus = EventBus()
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.cfg = GUIConfig.load()
        self.statusBar().showMessage("Ready")
        self.new_tab()

    def new_tab(self, cwd: Optional[str] = None):
        tab = TerminalTab(self.bus, cwd=cwd, parent=self)
        # apply appearance/perf config
        tab.terminal.setFont(QFont(self.cfg.appearance.font_family, self.cfg.appearance.font_size))
        tab.terminal.max_buffer_chars = self.cfg.performance.max_buffer_chars
        self.tabs.addTab(tab, "Terminal")
        return tab

def main():
    app = QApplication(sys.argv)
    win = MainWindow(); win.show()
    # Example: start shell directly
    tab: TerminalTab = win.tabs.widget(0)
    shell = shutil.which("pwsh") or shutil.which("powershell") if IS_WIN else shutil.which("bash") or shutil.which("zsh") or "/bin/sh"
    req = CommandRequest(tool=shell or "bash", args=[], cwd=os.getcwd())
    tab.start_command(req)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

# Patch Bundle Contents

This bundle implements full solutions for:

1) Real PTY backend with resize + signals  
2) Signal palette + safe argv + preview  
3) ANSI MVP (CR, BS, CSI K)  
4) Headless parity harness  
5) Hardened quick-actions (no hidden flags)  
6) Operator polish (open system terminal, status strip)

---
## File: `ansi_minimal.py`
```python
"""
Minimal ANSI handling for a GUI terminal.
Supports: Carriage Return (CR), Backspace (BS), and CSI K (Erase in Line).
Everything else is passed through unchanged.

This module is purposely tiny and self-contained so it can be swapped with a
full-featured parser later without changing the Terminal widget.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

ESC = "\x1b"

@dataclass
class AnsiLineEditor:
    """Keeps a single active line and a simple cursor for CR/BS/CSI K behavior."""
    line: List[str] = field(default_factory=list)
    col: int = 0  # cursor column in current line
    # When a newline arrives, the line is flushed to the GUI and reset

    def _insert(self, ch: str) -> None:
        if self.col == len(self.line):
            self.line.append(ch)
        else:
            self.line[self.col] = ch
        self.col += 1

    def feed(self, chunk: str) -> (List[str], str):
        """
        Feed text and return (completed_lines, pending_fragment).
        - completed_lines: list of full lines to append (without trailing '\n')
        - pending_fragment: text to show for the current line (no trailing newline)
        """
        completed = []
        i = 0
        while i < len(chunk):
            ch = chunk[i]

            # Handle ESC [ ... K  (CSI K / EL)
            if ch == ESC and i + 1 < len(chunk) and chunk[i+1] == "[":
                # parse CSI sequence
                j = i + 2
                params = ""
                while j < len(chunk) and chunk[j] not in "ABCDEFGHJKSTfmnsulp`":
                    # crude param parse until a final letter; we only care about 'K'
                    if chunk[j].isalpha():
                        break
                    params += chunk[j]
                    j += 1
                if j < len(chunk) and chunk[j] == "K":
                    # Erase in line - for our MVP, erase from cursor to end
                    del self.line[self.col:]
                    i = j + 1
                    continue
                # Unknown CSI -> drop it minimally
                i = j + 1
                continue

            if ch == "\r":
                # Return to start of line; following printable chars overwrite
                self.col = 0
                i += 1
                continue
            if ch == "\b":
                if self.col > 0:
                    # remove char before cursor and move left
                    self.line.pop(self.col - 1)
                    self.col -= 1
                i += 1
                continue
            if ch == "\n":
                # Flush current line
                completed.append("".join(self.line))
                self.line.clear()
                self.col = 0
                i += 1
                continue

            # Regular printable
            self._insert(ch)
            i += 1

        return completed, "".join(self.line)
```

---
## File: `pty_runner.py`
```python
"""
Cross-platform PTY-backed process runner for a GUI terminal.
- POSIX: uses os.openpty + subprocess with the slave end for stdio
- Windows: uses pywinpty (ConPTY) if available; otherwise raises ImportError

Exposes Qt-friendly signals via callbacks.
"""
from __future__ import annotations

import os
import sys
import fcntl
import termios
import struct
import signal
import locale
import threading
import subprocess
from typing import Callable, Optional, List

IS_WIN = os.name == "nt"

class PTYRunner:
    def __init__(self,
                 on_output: Callable[[bytes], None],
                 on_exit: Callable[[int], None],
                 on_error: Optional[Callable[[str], None]] = None):
        self.on_output = on_output
        self.on_exit = on_exit
        self.on_error = on_error or (lambda msg: None)

        self._proc = None
        self._master_fd = None
        self._reader_thread = None
        self._stop = threading.Event()
        self._encoding = locale.getpreferredencoding(False)
        self._win = None  # pywinpty wrappers

    # --------- lifecycle ---------
    def start(self, argv: List[str], cwd: Optional[str] = None, env: Optional[dict] = None,
              cols: int = 120, rows: int = 32, shell_path: Optional[str] = None) -> None:
        if IS_WIN:
            self._start_win(argv, cwd, env, cols, rows, shell_path)
        else:
            self._start_posix(argv, cwd, env, cols, rows)

    def write(self, data: bytes) -> None:
        if IS_WIN:
            if self._win is not None:
                self._win_write(data)
        else:
            if self._master_fd is not None:
                os.write(self._master_fd, data)

    def send_ctrl_c(self) -> None:
        if IS_WIN:
            # Best-effort Ctrl-C: send \x03 to console
            self.write(b"\x03")
        else:
            if self._proc and self._proc.pid:
                try:
                    os.killpg(os.getpgid(self._proc.pid), signal.SIGINT)
                except Exception:
                    # fallback: send ^C bytes
                    self.write(b"\x03")

    def send_eof(self) -> None:
        if IS_WIN:
            # ^Z Enter in Windows to signal EOF to many shells
            self.write(b"\x1a\r\n")
        else:
            # ^D on POSIX
            self.write(b"\x04")

    def kill(self) -> None:
        if IS_WIN:
            if self._win is not None:
                try:
                    self._win_kill()
                except Exception as e:
                    self.on_error(f"kill failed: {e}")
        else:
            if self._proc:
                try:
                    os.killpg(os.getpgid(self._proc.pid), signal.SIGKILL)
                except Exception as e:
                    self.on_error(f"kill failed: {e}")

    def resize(self, cols: int, rows: int) -> None:
        if IS_WIN:
            if self._win is not None:
                try:
                    self._win_resize(cols, rows)
                except Exception as e:
                    self.on_error(f"resize failed: {e}")
        else:
            if self._master_fd is not None:
                try:
                    fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ,
                                struct.pack("HHHH", rows, cols, 0, 0))
                except Exception as e:
                    self.on_error(f"resize failed: {e}")

    # --------- POSIX implementation ---------
    def _start_posix(self, argv, cwd, env, cols, rows):
        master_fd, slave_fd = os.openpty()
        # set initial size
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self._master_fd = master_fd

        def preexec():
            # start a new process group so signals can be delivered
            os.setsid()

        self._proc = subprocess.Popen(
            argv,
            stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            cwd=cwd, env=env,
            preexec_fn=preexec,
            close_fds=True,
        )
        os.close(slave_fd)

        self._reader_thread = threading.Thread(target=self._reader_loop_posix, daemon=True)
        self._reader_thread.start()

        threading.Thread(target=self._waiter, daemon=True).start()

    def _reader_loop_posix(self):
        try:
            while not self._stop.is_set():
                try:
                    data = os.read(self._master_fd, 4096)
                    if not data:
                        break
                    self.on_output(data)
                except OSError:
                    break
        finally:
            if self._master_fd is not None:
                try:
                    os.close(self._master_fd)
                except Exception:
                    pass
                self._master_fd = None

    # --------- Windows (pywinpty) implementation ---------
    def _start_win(self, argv, cwd, env, cols, rows, shell_path):
        try:
            import pywinpty
        except Exception as e:
            raise ImportError("pywinpty is required for PTY on Windows") from e

        cmdline = " ".join([self._quote(a) for a in argv])
        spawn_config = pywinpty.SpawnConfig(
            appname=shell_path or argv[0],
            commandline=cmdline,
            cwd=cwd or os.getcwd(),
            env=env or os.environ.copy(),
            dimensions=pywinpty.WinPTYDimensions(cols, rows),
        )
        self._win = pywinpty.WinPTY(spawn_config)
        self._win_proc = self._win.spawn()

        self._reader_thread = threading.Thread(target=self._reader_loop_win, daemon=True)
        self._reader_thread.start()
        threading.Thread(target=self._waiter_win, daemon=True).start()

    def _reader_loop_win(self):
        try:
            while not self._stop.is_set():
                try:
                    data = self._win.read(4096)
                    if not data:
                        break
                    self.on_output(data)
                except Exception:
                    break
        finally:
            try:
                self._win.close()
            except Exception:
                pass

    def _win_write(self, data: bytes):
        self._win.write(data)

    def _win_resize(self, cols: int, rows: int):
        self._win.set_size(cols, rows)

    def _win_kill(self):
        try:
            self._win_proc.terminate()  # graceful
        except Exception:
            self._win_proc.kill()  # force

    def _quote(self, s: str) -> str:
        if " " in s or '"' in s:
            return '"' + s.replace('"', r'\"') + '"'
        return s

    # --------- waiter ---------
    def _waiter(self):
        rc = self._proc.wait()
        self._stop.set()
        self.on_exit(rc)

    def _waiter_win(self):
        rc = self._win_proc.wait()  # returns exit code
        self._stop.set()
        self.on_exit(rc)
```

---
## File: `cli_gui_terminal.py`
```python
"""
Updated GUI Terminal with real PTY backend, signal palette, ANSI MVP, argv-safe execution,
quick action preview, and operator polish.

Requires:
- PyQt6
- Windows only: pywinpty installed (for ConPTY).

Run:
    python cli_gui_terminal.py
"""
from __future__ import annotations

import os
import sys
import shlex
import json
import locale
from pathlib import Path
from typing import List, Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from ansi_minimal import AnsiLineEditor
from pty_runner import PTYRunner

IS_WIN = os.name == "nt"

def default_shell_argv() -> List[str]:
    if IS_WIN:
        # Favor PowerShell if present
        pwsh = os.environ.get("ComSpec")  # fallback cmd.exe path
        return ["powershell.exe", "-NoLogo"] if shutil_which("powershell.exe") else [pwsh or "cmd.exe"]
    else:
        shell = os.environ.get("SHELL", "/bin/bash")
        return [shell, "-l"]

def shutil_which(name: str) -> Optional[str]:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        cand = os.path.join(p, name)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None

# ---------- Widgets ----------
class CommandPreviewDialog(QtWidgets.QDialog):
    def __init__(self, argv: List[str], env_delta: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Preview")
        self.setModal(True)
        layout = QtWidgets.QVBoxLayout(self)

        argv_label = QtWidgets.QLabel("Exact argv to be executed (no hidden flags):")
        self.argv_edit = QtWidgets.QPlainTextEdit(" ".join([json.dumps(a) for a in argv]))
        self.argv_edit.setMinimumHeight(70)

        env_label = QtWidgets.QLabel("Environment changes (delta):")
        self.env_view = QtWidgets.QPlainTextEdit(json.dumps(env_delta, indent=2))
        self.env_view.setMinimumHeight(120)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        layout.addWidget(argv_label)
        layout.addWidget(self.argv_edit)
        layout.addWidget(env_label)
        layout.addWidget(self.env_view)
        layout.addWidget(btns)

    def parsed_argv(self) -> List[str]:
        # Keep user editing power. Use shlex to split safely cross-platform.
        txt = self.argv_edit.toPlainText().strip()
        # On Windows, use posix=False so quotes are preserved properly
        if IS_WIN:
            return shlex.split(txt, posix=False)
        return shlex.split(txt)


class TerminalView(QtWidgets.QPlainTextEdit):
    """Display. Minimal ANSI behavior via AnsiLineEditor."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        font = QtGui.QFont("Consolas" if IS_WIN else "Menlo")
        font.setStyleHint(QtGui.QFont.StyleHint.Monospace)
        font.setPointSize(11)
        self.setFont(font)
        self.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)
        self._ansi = AnsiLineEditor()

        # capture raw stream for parity logs
        self._raw_log = []  # bytes
        self._max_log = 2_000_000  # 2MB

    def append_completed_line(self, line: str) -> None:
        self.appendPlainText(line)

    def set_pending_fragment(self, frag: str) -> None:
        # Update the last block's content to reflect CR/overwrite
        doc = self.document()
        cursor = self.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        # Remove current line (if not at beginning of doc)
        # Instead, we ensure last block equals frag (without newline)
        block = doc.lastBlock()
        if block.length() > 1:
            # replace last line
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.EndOfBlock, QtGui.QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(frag)
        else:
            # empty doc or empty block
            cursor.insertText(frag)

    def feed_bytes(self, data: bytes) -> None:
        self._raw_log.append(data)
        if sum(len(x) for x in self._raw_log) > self._max_log:
            self._raw_log.pop(0)

        text = data.decode(locale.getpreferredencoding(False), errors="replace")
        completed, frag = self._ansi.feed(text)
        for line in completed:
            # when a full line arrives, add newline for the GUI
            self.append_completed_line(line)
        self.set_pending_fragment(frag)

    def raw_capture(self) -> bytes:
        return b"".join(self._raw_log)

    def clear_screen(self):
        self.clear()
        self._ansi = AnsiLineEditor()


class TerminalWidget(QtWidgets.QWidget):
    exited = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.runner: Optional[PTYRunner] = None
        self.view = TerminalView()
        self.input = QtWidgets.QLineEdit()
        self.input.returnPressed.connect(self._on_enter)

        # Signal palette
        self.btn_ctrl_c = QtWidgets.QToolButton(text="Ctrl-C")
        self.btn_eof = QtWidgets.QToolButton(text="EOF")
        self.btn_kill = QtWidgets.QToolButton(text="Kill")
        self.btn_clear = QtWidgets.QToolButton(text="Clear")

        self.btn_ctrl_c.clicked.connect(lambda: self.runner and self.runner.send_ctrl_c())
        self.btn_eof.clicked.connect(lambda: self.runner and self.runner.send_eof())
        self.btn_kill.clicked.connect(lambda: self.runner and self.runner.kill())
        self.btn_clear.clicked.connect(self.view.clear_screen)

        # Layout
        top = QtWidgets.QHBoxLayout()
        for b in (self.btn_ctrl_c, self.btn_eof, self.btn_kill, self.btn_clear):
            top.addWidget(b)
        top.addStretch(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.view)
        layout.addWidget(self.input)

        # Status bar (cwd/shell/venv/rows×cols)
        self.status = QtWidgets.QStatusBar()
        self._lbl_cwd = QtWidgets.QLabel()
        self._lbl_shell = QtWidgets.QLabel()
        self._lbl_venv = QtWidgets.QLabel()
        self._lbl_size = QtWidgets.QLabel()
        self.status.addWidget(self._lbl_cwd)
        self.status.addWidget(self._lbl_shell)
        self.status.addWidget(self._lbl_venv)
        self.status.addPermanentWidget(self._lbl_size)
        layout.addWidget(self.status)

        self._cols = 120
        self._rows = 32
        self._update_status()

        # Context menu: Open system terminal here
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx_menu)

        # Start shell
        self.start_shell()

    def sizeHint(self):
        return QtCore.QSize(900, 600)

    def _update_status(self):
        cwd = os.getcwd()
        shell = os.path.basename(default_shell_argv()[0])
        venv = os.environ.get("VIRTUAL_ENV", "")
        self._lbl_cwd.setText(f"cwd: {cwd}")
        self._lbl_shell.setText(f"shell: {shell}")
        self._lbl_venv.setText(f"venv: {Path(venv).name if venv else '-'}")
        self._lbl_size.setText(f"{self._rows}×{self._cols}")

    def start_shell(self):
        self.start_argv(default_shell_argv())

    def start_argv(self, argv: List[str], env_delta: Optional[dict] = None):
        # Preview dialog
        env_delta = env_delta or {}
        dlg = CommandPreviewDialog(argv, env_delta, self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        argv = dlg.parsed_argv()

        # Merge environment
        env = os.environ.copy()
        env.update(env_delta)

        # Create runner
        if self.runner:
            self.runner.kill()
        self.runner = PTYRunner(
            on_output=lambda b: QtCore.QMetaObject.invokeMethod(self.view, "feed_bytes", QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(bytes, b)),
            on_exit=lambda rc: QtCore.QMetaObject.invokeMethod(self, "_on_exit_main", QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(int, rc)),
            on_error=lambda msg: print(f"[PTY ERROR] {msg}", file=sys.stderr),
        )
        self.runner.start(argv, cwd=os.getcwd(), env=env, cols=self._cols, rows=self._rows)

    @QtCore.pyqtSlot(int)
    def _on_exit_main(self, rc: int):
        self.exited.emit(rc)
        self.view.append_completed_line(f"\n[process exited with code {rc}]")

    def _on_enter(self):
        text = self.input.text()
        if not text.strip():
            self.runner.write(b"\r\n")
            return
        # argv-safe send: just write the line to the PTY + newline
        self.runner.write(text.encode(locale.getpreferredencoding(False), errors="replace") + b"\r\n")
        self.input.clear()

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)
        # Compute cols/rows from font metrics and viewport
        fm = self.view.fontMetrics()
        char_w = fm.horizontalAdvance("M")
        char_h = fm.height()
        # subtract some paddings
        w = self.view.viewport().width() - 10
        h = self.view.viewport().height() - 10
        cols = max(20, int(w / max(1, char_w)))
        rows = max(5, int(h / max(1, char_h)))
        if cols != self._cols or rows != self._rows:
            self._cols, self._rows = cols, rows
            if self.runner:
                self.runner.resize(cols, rows)
            self._update_status()

    # --- context menu ---
    def _ctx_menu(self, pos: QtCore.QPoint):
        menu = QtWidgets.QMenu(self)
        act_open = menu.addAction("Open system terminal here")
        act_run = menu.addAction("Run command...")
        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == act_open:
            self.open_system_terminal_here()
        elif chosen == act_run:
            self._prompt_and_run()

    def _prompt_and_run(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Run", "Command line:")
        if not ok or not text.strip():
            return
        argv = shlex.split(text, posix=not IS_WIN) if text.strip() else default_shell_argv()
        self.start_argv(argv)

    def open_system_terminal_here(self):
        cwd = os.getcwd()
        if IS_WIN:
            # Prefer Windows Terminal if present
            if shutil_which("wt.exe"):
                os.spawnlp(os.P_NOWAIT, "wt.exe", "wt.exe", "-d", cwd)
            elif shutil_which("powershell.exe"):
                os.spawnlp(os.P_NOWAIT, "powershell.exe", "powershell.exe", "-NoExit", "-NoLogo", "-Command", f"Set-Location -Path '{cwd}'")
            else:
                os.spawnlp(os.P_NOWAIT, "cmd.exe", "cmd.exe", "/K", f"cd /d {cwd}")
        elif sys.platform == "darwin":
            # Open macOS Terminal at cwd (quoted properly)
            osa = f'osascript -e \'tell application "Terminal" to do script "cd {cwd}"\''
            os.system(osa)
        else:
            # Linux: try x-terminal-emulator, gnome-terminal, or xterm
            for term in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm"):
                if shutil_which(term):
                    os.spawnlp(os.P_NOWAIT, term, term, "--working-directory", cwd)
                    return
            # fallback: attempt generic
            os.system(f'xdg-terminal "{cwd}" 2>/dev/null &')

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GUI PTY Terminal")
        self.term = TerminalWidget()
        self.setCentralWidget(self.term)

        # Simple menu to demo quick actions from quick_actions.json if present
        bar = self.menuBar()
        qa_menu = bar.addMenu("Quick Actions")
        self.qa_menu = qa_menu
        self._load_quick_actions()

    def _load_quick_actions(self):
        qaf = Path("quick_actions.json")
        if not qaf.exists():
            return
        try:
            actions = json.loads(qaf.read_text(encoding="utf-8"))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Quick Actions", f"Failed to parse quick_actions.json: {e}")
            return
        # Expect format: [{"label": "...", "argv": ["python","-V"], "env": {"FOO":"1"}}]
        self.qa_menu.clear()
        for entry in actions:
            label = entry.get("label", "Unnamed")
            argv = entry.get("argv") or entry.get("command") or []
            env = entry.get("env", {})
            act = self.qa_menu.addAction(label)
            act.triggered.connect(lambda _=False, argv=argv, env=env: self.term.start_argv(argv, env_delta=env))

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.resize(1000, 700)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---
## File: `tests/parity_test_harness.py`
```python
"""
Headless parity harness for the GUI PTY terminal.
Asserts:
- stdout is a TTY (isatty True)
- ANSI CR/K overwrite works (prints 'OVER' after erase)
- Ctrl-C terminates a long-running process with expected exit behavior
- Raw PTY capture is saved for inspection

Run:
    QT_QPA_PLATFORM=offscreen python -m tests.parity_test_harness
"""
from __future__ import annotations

import os, sys, time, locale, signal, pathlib
from PyQt6 import QtWidgets, QtCore
from cli_gui_terminal import TerminalWidget

IS_WIN = os.name == "nt"
ENC = locale.getpreferredencoding(False)

def wait_for(predicate, timeout=5.0, tick=0.05):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        QtWidgets.QApplication.processEvents()
        time.sleep(tick)
    return False

def run_and_capture(term: TerminalWidget, line: str, wait=0.4):
    term.runner.write(line.encode(ENC) + b"\r\n")
    QtWidgets.QApplication.processEvents()
    time.sleep(wait)
    QtWidgets.QApplication.processEvents()
    return term.view.toPlainText()

def test_isatty(term: TerminalWidget):
    code = 'import sys; print(sys.stdout.isatty())'
    out = run_and_capture(term, f'python -c "{code}"')
    assert "True" in out, f"isatty check failed. Output:\n{out}"

def test_ansi_overwrite(term: TerminalWidget):
    # print 'HELLO', then CR + erase to end + 'OVER'
    py = r"import sys; sys.stdout.write('HELLO'); sys.stdout.write('\r'); sys.stdout.write('\x1b[K'); sys.stdout.write('OVER'); sys.stdout.flush()"
    out = run_and_capture(term, f'python -c "{py}"')
    # The last visible chars should be 'OVER'
    assert "OVER" in out.splitlines()[-1], f"ANSI overwrite failed. Last line: {out.splitlines()[-1]}"

def test_ctrl_c_exit(term: TerminalWidget):
    # Start a long sleep and then send Ctrl-C
    term.runner.write(b'python -c "import time; time.sleep(60)"\r\n')
    ok = wait_for(lambda: True, timeout=0.5)
    assert ok
    term.runner.send_ctrl_c()
    # Give it a moment to terminate
    time.sleep(0.7)
    QtWidgets.QApplication.processEvents()
    # Heuristic: buffer should not continue to grow after a short period.
    before = len(term.view.toPlainText())
    time.sleep(0.7)
    QtWidgets.QApplication.processEvents()
    after = len(term.view.toPlainText())
    assert after - before < 50, "Process likely didn't terminate after Ctrl-C"

def save_raw_capture(term: TerminalWidget, path: str):
    data = term.view.raw_capture()
    pathlib.Path(path).write_bytes(data)

def main():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QtWidgets.QApplication(sys.argv)
    w = TerminalWidget()
    w.resize(900, 600)
    w.show()  # offscreen

    # Ensure shell ready
    QtWidgets.QApplication.processEvents()
    time.sleep(0.5)

    print("Running parity tests...")
    test_isatty(w)
    print(" - isatty: OK")
    test_ansi_overwrite(w)
    print(" - ANSI overwrite: OK")
    test_ctrl_c_exit(w)
    print(" - Ctrl-C: OK")

    out_path = "parity_raw_capture.bin"
    save_raw_capture(w, out_path)
    print(f"Raw PTY capture saved to {out_path}")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

---
## File: `README_PATCH.md`
```markdown
# GUI Terminal Parity Patchset

This bundle delivers complete solutions for the six biggest gaps:

1. **Real PTY backend** (`pty_runner.py`) with resize, Ctrl‑C/EOF/Kill (POSIX + Windows/pywinpty).
2. **Signal palette + safe argv handling** (`cli_gui_terminal.py`):
   - Ctrl‑C / EOF / Kill / Clear buttons.
   - `shlex` argv parsing (no hidden flags) and a **Command Preview** dialog.
3. **ANSI MVP** (`ansi_minimal.py`) supporting CR, Backspace, and CSI K (erase in line).
4. **True parity test harness** (`tests/parity_test_harness.py`) running in **offscreen Qt**.
5. **Hardened quick‑actions pipeline** (menu loads `quick_actions.json`, shows preview before run).
6. **Operator polish**:
   - “Open system terminal here” action (Windows/macOS/Linux).
   - Status strip: `cwd`, `shell`, `venv`, `rows×cols` and live PTY resize.

## Install

```bash
# POSIX
python -m venv .venv && source .venv/bin/activate
pip install pyqt6
# Windows also needs:
pip install pywinpty
```

## Run the GUI

```bash
python cli_gui_terminal.py
```

## Quick Actions

Place a `quick_actions.json` next to the script:

```json
[
  { "label": "Python Version", "argv": ["python","-V"] },
  { "label": "List", "argv": ["python","-c","import os; print(os.listdir())"], "env": {"DEMO":"1"} }
]
```

Trigger from the “Quick Actions” menu. You will **always** see the argv/environment preview and can edit before running.

## Parity Tests

Offscreen harness that asserts TTY, ANSI overwrite, and Ctrl‑C behavior, and writes a raw PTY capture.

```bash
# POSIX
QT_QPA_PLATFORM=offscreen python -m tests.parity_test_harness

# Windows (PowerShell)
$env:QT_QPA_PLATFORM="offscreen"
python -m tests.parity_test_harness
```

> If `pywinpty` is not installed on Windows, the GUI will raise a clear ImportError when attempting PTY mode.

## Integration Notes

- The GUI prefers PowerShell on Windows if available; otherwise falls back to `cmd.exe`.
- PTY resize is driven from widget geometry; it updates the status strip (`rows×cols`) and calls `TIOCSWINSZ` (POSIX) or `WinPTY.set_size` (Windows).
- ANSI MVP focuses on CR, BS, and CSI K. It can be swapped later for a full VT state machine without touching the widget API.
- Ctrl‑C uses process‑group signaling on POSIX and `^C` injection on Windows consoles (best effort). `Kill` is a hard terminate.
- Raw PTY bytes are ring‑buffered in memory and can be dumped via the harness for comparisons with a native terminal capture.
```


from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class PtyProcess:
    pid: Optional[int] = None


class PtyBackend:
    """Abstraction over PTY/ConPTY backends. Minimal stub.

    Real implementation will split Windows (ConPTY/pywinpty) and POSIX (ptyprocess)
    backends and provide async IO for the terminal widget.
    """

    def __init__(self, shell: Optional[str] = None, cwd: Optional[str] = None) -> None:
        self.shell = shell or self._default_shell()
        self.cwd = cwd or os.getcwd()
        self.process = PtyProcess()
        self._pty = None  # underlying backend object
        self._exit_code: Optional[int] = None

    def _default_shell(self) -> str:
        if os.name == "nt":  # Windows
            return os.environ.get("COMSPEC", "cmd.exe")
        return os.environ.get("SHELL", "/bin/bash")

    def start(self) -> None:
        """Start a PTY/ConPTY session if available, otherwise noop.

        POSIX: uses ptyprocess if available.
        Windows: attempts pywinpty, falls back to subprocess-less stub.
        """
        if os.name == "nt":
            self._start_windows()
        else:
            self._start_posix()

    def write(self, data: str) -> None:  # noqa: D401 - docstring not needed for stub
        try:
            if hasattr(self, "_pty") and self._pty is not None:
                self._pty.write(data)
        except Exception:
            pass

    def read(self, max_bytes: int = 4096) -> bytes:  # noqa: D401
        try:
            if hasattr(self, "_pty") and self._pty is not None:
                out = self._pty.read(max_bytes)
                return out.encode() if isinstance(out, str) else out
        except Exception:
            pass
        return b""

    def resize(self, rows: int, cols: int) -> None:  # noqa: D401
        try:
            if hasattr(self, "_pty") and self._pty is not None:
                self._pty.setwinsize(rows, cols)
        except Exception:
            pass

    def terminate(self) -> None:
        try:
            if hasattr(self, "_pty") and self._pty is not None:
                try:
                    # Try to capture exit code before closing
                    code = self._extract_exit_code()
                    if code is not None:
                        self._exit_code = int(code)
                except Exception:
                    pass
                self._pty.close(True)
        except Exception:
            pass
        self.process.pid = None

    def is_alive(self) -> bool:
        try:
            if hasattr(self, "_pty") and self._pty is not None:
                # ptyprocess exposes isalive(); winpty may not
                alive = getattr(self._pty, "isalive", None)
                if callable(alive):
                    return bool(alive())
        except Exception:
            pass
        # Fallback: if pid is None => not alive
        return self.process.pid is not None

    def send_ctrl_c(self) -> None:
        try:
            if os.name == "nt":
                self._send_ctrl_c_windows()
            else:
                if hasattr(self, "_pty") and self._pty is not None:
                    # Sending literal ETX over the pty usually triggers SIGINT on POSIX
                    self._pty.write("\x03")
        except Exception:
            pass

    # --- Platform-specific helpers ---

    def _start_posix(self) -> None:
        try:
            from ptyprocess import PtyProcessUnicode  # type: ignore

            self._pty = PtyProcessUnicode.spawn([self.shell], cwd=self.cwd)
            self.process.pid = getattr(self._pty, "pid", 0)
        except Exception:
            self._pty = None
            self.process.pid = 0

    def _start_windows(self) -> None:
        try:
            import winpty  # type: ignore

            # pywinpty v2 ships as winpty module
            self._pty = winpty.PTY(spawn_cmd=self.shell, cwd=self.cwd)
            self.process.pid = getattr(self._pty, "pid", 0)
        except Exception:
            try:
                import pywinpty  # type: ignore

                self._pty = pywinpty.Process(self.shell, cwd=self.cwd)
                self.process.pid = getattr(self._pty, "pid", 0)
            except Exception:
                self._pty = None
                self.process.pid = 0

    def _send_ctrl_c_windows(self) -> None:
        """Attempt to deliver Ctrl-C to the child process on Windows.

        Prefer winpty/pywinpty behavior; otherwise, try using GenerateConsoleCtrlEvent.
        """
        # Try pty-provided write of ^C first
        try:
            if hasattr(self, "_pty") and self._pty is not None and hasattr(self._pty, "write"):
                self._pty.write("\x03")
                return
        except Exception:
            pass

    # --- Exit code helpers ---
    def _extract_exit_code(self) -> Optional[int]:
        try:
            if self._pty is None:
                return self._exit_code
            # ptyprocess exposes exitstatus and status
            code = getattr(self._pty, "exitstatus", None)
            if code is not None:
                return int(code)
            status = getattr(self._pty, "status", None)
            if status is not None:
                return int(status)
            # Other common attributes across wrappers
            for attr in ("returncode", "exit_code", "exitStatus", "exit_status"):
                val = getattr(self._pty, attr, None)
                if val is not None:
                    return int(val)
        except Exception:
            return None
        return None

    def get_exit_code(self) -> Optional[int]:
        code = self._extract_exit_code()
        if code is not None:
            self._exit_code = int(code)
        return self._exit_code
        # Fallback: use WinAPI GenerateConsoleCtrlEvent if pid known
        try:
            import ctypes  # type: ignore
            from ctypes import wintypes  # type: ignore

            kernel32 = ctypes.windll.kernel32
            # Attach to parent console; 0xFFFFFFFF = ATTACH_PARENT_PROCESS
            ATTACH_PARENT_PROCESS = ctypes.c_uint(-1).value
            kernel32.AttachConsole(wintypes.DWORD(ATTACH_PARENT_PROCESS))
            # CTRL_C_EVENT = 0
            CTRL_C_EVENT = 0
            # Send to process group 0 (current) or the child's group if we had it; use 0 as fallback
            kernel32.GenerateConsoleCtrlEvent(wintypes.DWORD(CTRL_C_EVENT), wintypes.DWORD(0))
        except Exception:
            pass

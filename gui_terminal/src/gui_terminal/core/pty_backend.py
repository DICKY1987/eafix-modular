from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Tuple
import threading
import time


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
                self._pty.close(True)
        except Exception:
            pass
        self.process.pid = None

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

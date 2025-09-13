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

    def _default_shell(self) -> str:
        if os.name == "nt":  # Windows
            return os.environ.get("COMSPEC", "cmd.exe")
        return os.environ.get("SHELL", "/bin/bash")

    def start(self) -> None:
        # Placeholder: spawn logic to be implemented per platform.
        self.process.pid = 0

    def write(self, data: str) -> None:  # noqa: D401 - docstring not needed for stub
        # Placeholder for sending input to PTY.
        _ = data

    def read(self, max_bytes: int = 4096) -> bytes:  # noqa: D401
        # Placeholder for reading from PTY.
        _ = max_bytes
        return b""

    def resize(self, rows: int, cols: int) -> None:  # noqa: D401
        _ = (rows, cols)

    def terminate(self) -> None:
        self.process.pid = None


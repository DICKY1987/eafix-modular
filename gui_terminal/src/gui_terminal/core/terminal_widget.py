from __future__ import annotations

import threading
import time
from typing import Optional, Callable

from gui_terminal.core.pty_backend import PtyBackend


class TerminalWidget:
    """Headless-friendly terminal binder using PtyBackend.

    Provides a polling reader thread that invokes a callback when new bytes
    arrive. In a real GUI, this would integrate with the event loop.
    """

    def __init__(self, backend: Optional[PtyBackend] = None) -> None:
        self.backend = backend or PtyBackend()
        self._reader: Optional[threading.Thread] = None
        self._stop = False
        self.on_data: Optional[Callable[[bytes], None]] = None

    def start(self) -> None:
        self.backend.start()
        self._stop = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def send(self, data: str) -> None:
        self.backend.write(data)

    def _read_loop(self) -> None:
        while not self._stop:
            buf = self.backend.read(4096)
            if buf:
                if self.on_data:
                    try:
                        self.on_data(buf)
                    except Exception:
                        pass
            time.sleep(0.03)

    def close(self) -> None:
        self._stop = True
        try:
            if self._reader and self._reader.is_alive():
                self._reader.join(timeout=0.2)
        except Exception:
            pass
        self.backend.terminate()


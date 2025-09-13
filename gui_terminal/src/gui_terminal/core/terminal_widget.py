from __future__ import annotations

import threading
import time
from typing import Optional, Callable

from gui_terminal.core.pty_backend import PtyBackend
from gui_terminal.core.event_system import EventBus


class TerminalWidget:
    """Headless-friendly terminal binder using PtyBackend.

    Provides a polling reader thread that invokes a callback when new bytes
    arrive. In a real GUI, this would integrate with the event loop.
    """

    def __init__(self, backend: Optional[PtyBackend] = None) -> None:
        self.backend = backend or PtyBackend()
        self._reader: Optional[threading.Thread] = None
        self._watcher: Optional[threading.Thread] = None
        self._stop = False
        self.on_data: Optional[Callable[[bytes], None]] = None
        self.on_exit: Optional[Callable[[], None]] = None
        self.bus = EventBus()
        self._started_ts: float = 0.0

    def start(self) -> None:
        self.backend.start()
        self._stop = False
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._watcher = threading.Thread(target=self._watch_loop, daemon=True)
        self._watcher.start()
        try:
            self._started_ts = time.time()
            self.bus.publish("run.started", {"ts": self._started_ts})
        except Exception:
            pass

    def send(self, data: str) -> None:
        self.backend.write(data)
        try:
            self.bus.publish("input.sent", {"ts": time.time(), "chars": data})
        except Exception:
            pass

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

    def _watch_loop(self) -> None:
        # poll backend aliveness and fire exit callback once
        while not self._stop:
            try:
                if not self.backend.is_alive():
                    if self.on_exit:
                        try:
                            self.on_exit()
                        except Exception:
                            pass
                    try:
                        now = time.time()
                        code = self.backend.get_exit_code()
                        payload = {"ts": now, "elapsed": round(now - (self._started_ts or now), 3)}
                        if code is not None:
                            payload["exit_code"] = int(code)
                        self.bus.publish("run.exited", payload)
                    except Exception:
                        pass
                    break
            except Exception:
                break
            time.sleep(0.1)

    def close(self) -> None:
        self._stop = True
        try:
            if self._reader and self._reader.is_alive():
                self._reader.join(timeout=0.2)
        except Exception:
            pass
        try:
            if self._watcher and self._watcher.is_alive():
                self._watcher.join(timeout=0.2)
        except Exception:
            pass
        self.backend.terminate()

    # Convenience for sending SIGINT/ETX
    def send_ctrl_c(self) -> None:
        try:
            self.backend.send_ctrl_c()
        except Exception:
            pass
        try:
            self.bus.publish("signal.sent", {"ts": time.time(), "name": "SIGINT"})
        except Exception:
            pass


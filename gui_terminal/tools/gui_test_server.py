#!/usr/bin/env python3
"""
Headless GUI test server (offscreen) adapted for parity validation.
Notes:
- Requires PyQt6 and the gui_terminal package to be available on PYTHONPATH.
- Provided as a tool; not invoked by default tests.
"""
from __future__ import annotations

import os
import json
import socket
from typing import Optional

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication
except Exception:
    QApplication = None  # type: ignore

try:
    from gui_terminal.ui.main_window import MainWindow
except Exception:
    MainWindow = None  # type: ignore


HOST = "127.0.0.1"
PORT = 45454


def run_server() -> int:
    if QApplication is None or MainWindow is None:
        print(json.dumps({"ok": False, "error": "PyQt or gui_terminal not available"}))
        return 1

    app = QApplication([])
    win = MainWindow()
    # We intentionally do not show the window for headless operation
    term = getattr(win, "_term", None)
    if term is None:
        print(json.dumps({"ok": False, "error": "terminal backend unavailable"}))
        return 1
    # Track basic events to a simple buffer for parity checks
    buffer = []
    def _evt_sink(evt: dict):
        t = evt.get("type") or ""
        if not t:
            # Map by topic keys from EventBus usage
            if "input.sent" in evt.get("topic", ""):
                t = "input.sent"
        buffer.append(evt)
    try:
        term.bus.subscribe("input.sent", lambda e: _evt_sink({"type":"input.sent","chars": e.get("chars") if isinstance(e, dict) else None}))
        term.bus.subscribe("signal.sent", lambda e: _evt_sink({"type":"signal.sent","name":"SIGINT"}))
        term.bus.subscribe("run.exited", lambda e: _evt_sink({"type":"run.exited"}))
    except Exception:
        pass

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    try:
        while True:
            conn, _ = s.accept()
            with conn:
                data = conn.recv(65535)
                if not data:
                    continue
                try:
                    req = json.loads(data.decode("utf-8"))
                except Exception:
                    conn.sendall(b'{"ok":false,"error":"bad json"}')
                    continue
                op = req.get("op")
                if op == "start":
                    cmd = req.get("cmd") or []
                    if not cmd:
                        resp = {"ok": False, "error":"missing cmd"}
                    else:
                        # Send command as a single line to the shell
                        line = " ".join(cmd)
                        win._input.setText(line)
                        win._submit_line()
                        resp = {"ok": True}
                    conn.sendall(json.dumps(resp).encode("utf-8"))
                elif op == "read":
                    # Hacky: read last N chars from output widget
                    maxb = int(req.get("max", 4096))
                    text = win._output.toPlainText()
                    chunk = text[-maxb:]
                    conn.sendall(json.dumps({"ok": True, "data": chunk}).encode("utf-8"))
                elif op == "events":
                    # Return and clear buffered events
                    evs = list(buffer)
                    buffer.clear()
                    conn.sendall(json.dumps({"ok": True, "events": evs}).encode("utf-8"))
                elif op == "signal":
                    name = (req.get("name") or "SIGINT").upper()
                    if name == "SIGINT":
                        try:
                            term.send_ctrl_c()
                            conn.sendall(b'{"ok":true}')
                        except Exception:
                            conn.sendall(b'{"ok":false}')
                    else:
                        conn.sendall(b'{"ok":false,"error":"unsupported signal"}')
                elif op == "status":
                    try:
                        running = bool(term.backend.is_alive())
                    except Exception:
                        running = False
                    conn.sendall(json.dumps({"ok": True, "status": "running" if running else "idle"}).encode("utf-8"))
                elif op == "wait":
                    # Busy-wait small intervals until process exits or timeout
                    timeout = float(req.get("timeout", 5.0))
                    start = time.time()
                    exit_seen = False
                    while time.time() - start < timeout:
                        try:
                            if not term.backend.is_alive():
                                exit_seen = True
                                break
                        except Exception:
                            break
                        time.sleep(0.05)
                    conn.sendall(json.dumps({"ok": True, "exited": exit_seen}).encode("utf-8"))
                else:
                    conn.sendall(b'{"ok":false,"error":"unknown op"}')
    finally:
        s.close()


if __name__ == "__main__":
    raise SystemExit(run_server())


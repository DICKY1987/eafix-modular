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
                else:
                    conn.sendall(b'{"ok":false,"error":"unknown op"}')
    finally:
        s.close()


if __name__ == "__main__":
    raise SystemExit(run_server())


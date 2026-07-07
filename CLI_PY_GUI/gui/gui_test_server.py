#!/usr/bin/env python3
"""
Headless GUI test server:
- Launches a hidden PyQt6 app with a single TerminalTab.
- Exposes a tiny TCP JSON protocol for tests:
  * {"op":"start","cmd":["bash","-lc","echo hello"]}
  * {"op":"status"} -> returns {"status":"running|idle","cols":..,"rows":..}
  * {"op":"signal","name":"SIGINT"}
  * {"op":"read","max":4096} -> returns recent console text chunk
- Intended for CI parity tests; not for production.
"""

import os, sys, json, socket, threading, time
from typing import Optional
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from pty_terminal_runner import MainWindow, TerminalTab, CommandRequest

HOST = "127.0.0.1"
PORT = 45454

class ServerState:
    def __init__(self, tab: TerminalTab):
        self.tab = tab
        self.buffer = ""  # naive text buffer for reads
        self.last_exit = None
        tab.bus.published.connect(self._on_event)

    def _on_event(self, evt: dict):
        t = evt.get("type")
        if t == "run.started":
            self.buffer += f"[started] {evt.get('preview','')}\n"
        elif t == "run.exited":
            self.last_exit = int(evt.get('exit_code'))
            self.buffer += f"[exit] {self.last_exit} in {evt.get('elapsed'):.1f}s\n"
        elif t == "input.sent":
            self.buffer += f"$ {evt.get('chars','')}\n"
        elif t == "signal.sent":
            self.buffer += f"[signal] {evt.get('name')}\n"

def serve(sock: socket.socket, state: ServerState):
    sock.listen(1)
    while True:
        conn, _ = sock.accept()
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
                    state.tab.start_command(CommandRequest(tool=cmd[0], args=cmd[1:], cwd=os.getcwd()))
                    resp = {"ok": True}
                conn.sendall(json.dumps(resp).encode("utf-8"))

            elif op == "status":
                resp = {"ok": True, "status": "running" if state.tab.worker else "idle"}
                conn.sendall(json.dumps(resp).encode("utf-8"))

            elif op == "signal":
                name = req.get("name","SIGINT")
                if state.tab.worker and name.upper()=="SIGINT":
                    state.tab._send_sigint()
                    conn.sendall(b'{"ok":true}')
                else:
                    conn.sendall(b'{"ok":false}')

            elif op == "wait":
                # busy-wait small intervals until process exits or timeout
                timeout = float(req.get("timeout", 10.0))
                start = time.time()
                while time.time() - start < timeout:
                    if state.last_exit is not None:
                        break
                    time.sleep(0.05)
                conn.sendall(json.dumps({"ok": True, "exit": state.last_exit}).encode("utf-8"))

            elif op == "get_exit":
                conn.sendall(json.dumps({"ok": True, "exit": state.last_exit}).encode("utf-8"))

            elif op == "read":
                maxn = int(req.get("max", 4096))
                buf = state.buffer[-maxn:]
                conn.sendall(json.dumps({"ok": True, "data": buf}).encode("utf-8"))
            else:
                conn.sendall(b'{"ok":false,"error":"unknown op"}')

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    tab = win.tabs.widget(0)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    state = ServerState(tab)

    t = threading.Thread(target=serve, args=(s,state), daemon=True)
    t.start()
    # No window shown (offscreen), just run event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

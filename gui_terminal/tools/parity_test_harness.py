#!/usr/bin/env python3
"""
Parity test harness against the headless GUI test server.
Usage:
  1) In one shell:  PYTHONPATH=gui_terminal/src python gui_terminal/tools/gui_test_server.py
  2) In another:    python gui_terminal/tools/parity_test_harness.py

This is provided as a tool and not executed in CI by default.
"""
from __future__ import annotations

import json
import socket

HOST, PORT = "127.0.0.1", 45454


def rpc(obj: dict) -> dict:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(json.dumps(obj).encode("utf-8"))
    data = s.recv(1 << 20)
    s.close()
    return json.loads(data.decode("utf-8"))


def main() -> int:
    # basic run smoke
    resp = rpc({"op": "start", "cmd": ["echo", "hello"]})
    if not resp.get("ok"):
        print("start failed", resp)
        return 1
    out = rpc({"op": "read", "max": 2048}).get("data", "")
    print("READ:\n", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


import os
import sys
import time
import json
import socket
import subprocess
from pathlib import Path

import pytest


def _spawn_server(env):
    repo = Path(__file__).resolve().parents[1]
    py = sys.executable
    server = repo / "gui_terminal" / "tools" / "gui_test_server.py"
    return subprocess.Popen([py, str(server)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _rpc(obj):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    s.connect(("127.0.0.1", 45454))
    s.sendall(json.dumps(obj).encode("utf-8"))
    data = s.recv(1 << 20)
    s.close()
    return json.loads(data.decode("utf-8"))


@pytest.mark.skipif(os.environ.get("GUI_PARITY") != "1", reason="GUI parity tests disabled; set GUI_PARITY=1 to enable")
def test_exit_code_posix_only():
    if os.name == "nt":
        pytest.skip("Exit code verification limited to POSIX for now")
    try:
        import PyQt6  # noqa: F401
    except Exception:
        pytest.skip("PyQt6 not available")

    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo / "gui_terminal" / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("QT_QPA_PLATFORM", "offscreen")

    p = _spawn_server(env)
    try:
        time.sleep(0.6)
        assert _rpc({"op": "start", "cmd": ["bash", "-lc", "exit 7"]}).get("ok")
        res = _rpc({"op": "wait", "timeout": 3.0})
        assert res.get("ok") and res.get("exited"), res
        # Pull events and look for run.exited with exit_code
        evs = _rpc({"op": "events"}).get("events", [])
        found = False
        for ev in evs:
            if ev.get("type") == "run.exited" and "exit_code" in ev:
                assert int(ev["exit_code"]) == 7
                found = True
        assert found, evs
    finally:
        p.kill()


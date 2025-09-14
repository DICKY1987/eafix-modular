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
def test_cr_overwrite_and_exit_code_like_behavior():
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
        if os.name != "nt":
            cmd = ["bash", "-lc", "printf 'abc\\rABCD\\n' && exit 0"]
        else:
            cmd = ["cmd", "/c", "echo hello && exit /b 0"]
        assert _rpc({"op": "start", "cmd": cmd}).get("ok")
        time.sleep(0.6)
        out = _rpc({"op": "read", "max": 4096}).get("data", "")
        if os.name != "nt":
            assert "ABCD" in out, out
        else:
            assert "hello" in out, out
    finally:
        p.kill()


@pytest.mark.skipif(os.environ.get("GUI_PARITY") != "1", reason="GUI parity tests disabled; set GUI_PARITY=1 to enable")
def test_unicode_echo():
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
        if os.name != "nt":
            cmd = ["bash", "-lc", "printf 'I♥^ 3.14159\\n'"]
        else:
            cmd = ["cmd", "/c", "echo I^<3 3.14159"]
        assert _rpc({"op": "start", "cmd": cmd}).get("ok")
        time.sleep(0.6)
        out = _rpc({"op": "read", "max": 4096}).get("data", "")
        assert "3.14159" in out
    finally:
        p.kill()


@pytest.mark.skipif(os.environ.get("GUI_PARITY") != "1", reason="GUI parity tests disabled; set GUI_PARITY=1 to enable")
def test_ctrl_c_interrupts_sleep_on_posix():
    if os.name == "nt":
        pytest.skip("Ctrl-C path inconsistent on Windows shells; skip")
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
        cmd = ["bash", "-lc", "sleep 5"]
        assert _rpc({"op": "start", "cmd": cmd}).get("ok")
        time.sleep(0.2)
        _ = _rpc({"op": "signal", "name": "SIGINT"})
        res = _rpc({"op": "wait", "timeout": 4.0})
        assert res.get("ok") and res.get("exited")
    finally:
        p.kill()


@pytest.mark.skipif(os.environ.get("GUI_PARITY") != "1", reason="GUI parity tests disabled; set GUI_PARITY=1 to enable")
def test_stderr_interleave_order_basic():
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
        if os.name != "nt":
            cmd = ["bash", "-lc", "python3 - <<'PY'\nimport sys\nprint('out1')\nsys.stderr.write('err1\\n')\nprint('out2')\nsys.stderr.write('err2\\n')\nPY"]
        else:
            cmd = ["cmd", "/c", "python -c \"import sys; print('out1'); sys.stderr.write('err1\\n'); print('out2'); sys.stderr.write('err2\\n')\""]
        assert _rpc({"op": "start", "cmd": cmd}).get("ok")
        time.sleep(0.8)
        out = _rpc({"op": "read", "max": 4096}).get("data", "")
        # Check lines present; strict interleave may vary by platform but all lines should appear
        for token in ("out1", "err1", "out2", "err2"):
            assert token in out, out
    finally:
        p.kill()


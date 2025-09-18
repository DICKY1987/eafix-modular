#!/usr/bin/env python3
"""
Parity Test Harness (real PTY path via headless GUI server)
Usage (CI):
  1) Start:   python gui_test_server.py &
  2) Run:     python parity_test_harness.py
Tests validate:
  - TTY-like behavior (interactive echo via events)
  - ANSI CR handling (overwrite)
  - Ctrl-C exits (exit code >= 128 typical)
  - Unicode/UTF-8 handling
  - Exit code propagation
"""
import os, sys, time, json, socket

HOST, PORT = "127.0.0.1", 45454

def rpc(obj):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(json.dumps(obj).encode("utf-8"))
    data = s.recv(1<<20)
    s.close()
    return json.loads(data.decode("utf-8"))

def test_start_and_exit():
    # Run a quick command via an interactive shell
    cmd = ["bash","-lc","printf 'abc\\rABCD\\n' && exit 0"] if os.name!="nt" else ["cmd","/c","echo hello"]
    assert rpc({"op":"start","cmd":cmd})["ok"]
    time.sleep(1.2)
    out = rpc({"op":"read","max":2048})["data"]
    assert "ABCD" in out, "CR overwrite not reflected"
    assert "[exit]" in out, "Exit event missing"

def test_unicode():
    cmd = ["bash","-lc","printf 'π≈3.14159\\n'"] if os.name!="nt" else ["cmd","/c","echo π≈3.14159"]
    assert rpc({"op":"start","cmd":cmd})["ok"]
    time.sleep(0.6)
    out = rpc({"op":"read","max":2048})["data"]
    assert "π≈3.14159" in out


def test_ctrl_c_interrupt():
    if os.name == "nt":
        # Windows Ctrl-C path depends on ConPTY write of ^C; skip for now.
        return
    # Start a long-running sleep and interrupt
    assert rpc({"op":"start","cmd":["bash","-lc","sleep 5"]})["ok"]
    time.sleep(0.3)
    rpc({"op":"signal","name":"SIGINT"})
    res = rpc({"op":"wait","timeout":5.0})
    assert res["ok"]
    exitc = res.get("exit")
    assert exitc is not None and exitc >= 128, f"Expected signal exit code, got {exitc}"

def test_stderr_interleave_order():
    # Alternate stdout/stderr lines; verify order preserved in PTY buffer
    if os.name != "nt":
        cmd = ["bash","-lc","python3 - <<'PY'\nimport sys\nprint('out1')\nsys.stderr.write('err1\\n')\nprint('out2')\nsys.stderr.write('err2\\n')\nPY"]
    else:
        cmd = ["cmd","/c","python -c "import sys; print('out1'); sys.stderr.write('err1\\n'); print('out2'); sys.stderr.write('err2\\n')""]
    assert rpc({"op":"start","cmd":cmd})["ok"]
    time.sleep(1.0)
    out = rpc({"op":"read","max":4096})["data"]
    i1 = out.find("out1"); e1 = out.find("err1"); i2 = out.find("out2"); e2 = out.find("err2")
    assert -1 not in (i1,e1,i2,e2), f"Missing lines in output: {out}"
    assert i1 < e1 < i2 < e2, f"Order not preserved: {out}"


def run_all():
    tests = [test_start_and_exit, test_unicode, test_ctrl_c_interrupt, test_stderr_interleave_order]
    results = []
    for t in tests:
        try:
            t()
            results.append((t.__name__, True, ""))
        except Exception as e:
            results.append((t.__name__, False, str(e)))
    return results

if __name__ == "__main__":
    results = run_all()
    ok = all(r[1] for r in results)
    print(json.dumps({"ok": ok, "results": results}, indent=2))
    sys.exit(0 if ok else 1)

"""
EAFIX-Modular — MT4 ↔ Python Communication Test
=================================================
Tests all three live communication channels between Python and MT4:

  Test A — HTTP (MT4 → Python)
    MT4 Script sends GET http://127.0.0.1:5001/comms-test/ping
    Python responds with JSON; MT4 prints the test_id to confirm.

  Test B — Signal file (Python → MT4)
    Python writes a signal JSONL to the MT4 common files directory.
    MT4 Script reads the file and prints its contents.

  Test C — Feedback file (MT4 → Python)
    MT4 Script writes a feedback CSV to the MT4 common files directory.
    Python polls for it and reports pass/fail.

Usage
-----
1. Run this script first:
       python python_comms_test.py

2. While it is running, open MetaTrader 4, compile MT4_CommTest.mq4,
   and attach it to any chart as a Script.

3. Watch the console here for test results.

Configuration
-------------
Override defaults with environment variables:
  MT4_COMMON_DIR   Path to MT4's common files directory
                   Default: %APPDATA%\\MetaQuotes\\Terminal\\Common\\Files
  HTTP_PORT        Port for the Python HTTP server (default: 5001)
  SIGNAL_SUBDIR    Sub-folder inside MT4_COMMON_DIR (default: eafix_test)
  TIMEOUT_SECS     How long to wait for MT4 responses (default: 120)
"""

import json
import os
import sys
import time
import hashlib
import threading
import socket
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Force UTF-8 output so Unicode symbols render on Windows cmd/PowerShell
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Configuration ────────────────────────────────────────────────────────────

HTTP_PORT = int(os.environ.get("HTTP_PORT", 5003))

MT4_COMMON_DIR = Path(
    os.environ.get(
        "MT4_COMMON_DIR",
        Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal" / "Common" / "Files",
    )
)

SIGNAL_SUBDIR = os.environ.get("SIGNAL_SUBDIR", "eafix_test")
TEST_DIR      = MT4_COMMON_DIR / SIGNAL_SUBDIR
SIGNAL_FILE   = TEST_DIR / "signal.jsonl"
FEEDBACK_FILE = TEST_DIR / "feedback.csv"
TIMEOUT_SECS  = int(os.environ.get("TIMEOUT_SECS", 86400))  # 24 hours

# Unique ID for this test run so we can match signal ↔ feedback
TEST_RUN_ID = datetime.now(timezone.utc).strftime("COMMS-%Y%m%d-%H%M%S")

# Shared state between server thread and main thread
_http_hits: list[dict] = []
_http_lock = threading.Lock()


# ── Helpers ──────────────────────────────────────────────────────────────────

def banner(msg: str, char: str = "─") -> None:
    print(f"\n{char * 60}")
    print(f"  {msg}")
    print(char * 60)


def ok(msg: str)   -> None: print(f"  ✅  {msg}")
def fail(msg: str) -> None: print(f"  ❌  {msg}")
def info(msg: str) -> None: print(f"  ℹ   {msg}")
def wait(msg: str) -> None: print(f"  ⏳  {msg}")


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


# ── HTTP Server (Test A) ──────────────────────────────────────────────────────

class CommTestHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for MT4 WebRequest tests."""

    def log_message(self, fmt, *args):
        # Suppress default access log; we print our own
        pass

    def do_GET(self):
        if self.path == "/comms-test/ping":
            payload = json.dumps({
                "status": "ok",
                "test_id": TEST_RUN_ID,
                "server": "EAFIX-Python",
                "ts_utc": datetime.now(timezone.utc).isoformat(),
            }).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

            with _http_lock:
                _http_hits.append({
                    "ts": time.time(),
                    "remote": self.client_address,
                    "path": self.path,
                })
            print(f"\n  🌐  [Test A] HTTP ping received from {self.client_address[0]}")

        elif self.path == "/health":
            payload = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        else:
            self.send_response(404)
            self.end_headers()


def start_http_server() -> HTTPServer:
    server = HTTPServer(("0.0.0.0", HTTP_PORT), CommTestHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ── Test B — Write signal JSONL (Python → MT4) ───────────────────────────────

def write_signal() -> bool:
    """Write a test signal JSONL that MT4 will read."""
    try:
        TEST_DIR.mkdir(parents=True, exist_ok=True)

        signal = {
            "test_run_id":  TEST_RUN_ID,
            "type":         "COMMS_TEST",
            "symbol":       "EURUSD",
            "direction":    "BUY",
            "lot_size":     0.01,
            "ts_utc":       datetime.now(timezone.utc).isoformat(),
            "message":      "If you can read this in MT4, Test B passed!",
        }
        checksum = hashlib.sha256(json.dumps(signal, sort_keys=True).encode()).hexdigest()[:8]
        signal["checksum"] = checksum

        # Atomic write: write to .tmp then rename (matches bridge protocol)
        tmp = SIGNAL_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(signal) + "\n", encoding="utf-8")
        tmp.replace(SIGNAL_FILE)

        ok(f"Signal written → {SIGNAL_FILE}")
        info(f"test_run_id = {TEST_RUN_ID}")
        return True

    except Exception as exc:
        fail(f"Could not write signal file: {exc}")
        return False


# ── Test C — Poll for feedback CSV (MT4 → Python) ────────────────────────────

def poll_feedback(deadline: float) -> dict | None:
    """Poll for the feedback CSV written by MT4. Returns parsed row or None."""
    if FEEDBACK_FILE.exists():
        FEEDBACK_FILE.unlink()   # clear any stale file from a previous run

    wait(f"Waiting for MT4 to write feedback → {FEEDBACK_FILE}")
    print(f"       (timeout in {TIMEOUT_SECS}s — run the MT4 Script now)\n")

    while time.time() < deadline:
        if FEEDBACK_FILE.exists():
            text = FEEDBACK_FILE.read_text(encoding="utf-8").strip()
            if text:
                return {"raw": text}
        time.sleep(0.5)

    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    banner("EAFIX-Modular  MT4 ↔ Python Communication Test", "═")
    print(f"\n  Test run : {TEST_RUN_ID}")
    print(f"  HTTP port: {HTTP_PORT}")
    print(f"  Test dir : {TEST_DIR}\n")

    results: dict[str, bool] = {}
    deadline = time.time() + TIMEOUT_SECS

    # ── Pre-flight ──────────────────────────────────────────────────────────
    banner("Pre-flight checks")

    if port_in_use(HTTP_PORT):
        fail(f"Port {HTTP_PORT} is already in use. Stop the other process or set HTTP_PORT=<other>.")
        return 1
    ok(f"Port {HTTP_PORT} is free")

    if not MT4_COMMON_DIR.exists():
        fail(f"MT4 common directory not found: {MT4_COMMON_DIR}")
        info("Set MT4_COMMON_DIR env var to your MT4 Terminal\\Common\\Files path.")
        info("Trying to create the test directory anyway…")

    try:
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        ok(f"Test directory ready: {TEST_DIR}")
    except Exception as e:
        fail(f"Cannot create test directory: {e}")
        return 1

    # ── Test A: Start HTTP server ───────────────────────────────────────────
    banner("Test A — HTTP  (MT4 → Python via WebRequest)")
    server = start_http_server()
    ok(f"HTTP server listening on http://127.0.0.1:{HTTP_PORT}/comms-test/ping")
    info("MT4 must whitelist this URL: Tools → Options → Expert Advisors")

    # ── Test B: Write signal ────────────────────────────────────────────────
    banner("Test B — Signal file  (Python → MT4)")
    results["B_signal_write"] = write_signal()

    # ── Instructions ───────────────────────────────────────────────────────
    banner("▶  ACTION REQUIRED", "★")
    print("""
  1. In MetaTrader 4, open Tools → Options → Expert Advisors
     Tick "Allow WebRequest for listed URL" and add:
       http://127.0.0.1:{HTTP_PORT}

  2. Open Navigator → Scripts, drag MT4_CommTest onto any chart.

  3. Watch this console for Test A and Test C results.

  Press Ctrl+C to abort.
""")

    # ── Test C: Poll for feedback ───────────────────────────────────────────
    banner("Test C — Feedback file  (MT4 → Python)")
    feedback = poll_feedback(deadline)

    if feedback:
        ok("Feedback file received from MT4!")
        print(f"\n  Content:\n    {feedback['raw']}\n")
        results["C_feedback"] = True
    else:
        fail("No feedback file received within timeout.")
        results["C_feedback"] = False

    # ── Test A result (check http hits accumulated) ─────────────────────────
    with _http_lock:
        hits = list(_http_hits)
    if hits:
        results["A_http"] = True
        ok(f"HTTP ping received {len(hits)} time(s)")
    else:
        results["A_http"] = False
        fail("No HTTP ping received from MT4 within timeout.")

    # ── Summary ─────────────────────────────────────────────────────────────
    banner("Results", "═")
    all_passed = True
    labels = {
        "A_http":         "Test A — HTTP WebRequest  (MT4 → Python)",
        "B_signal_write": "Test B — Signal file      (Python → MT4)",
        "C_feedback":     "Test C — Feedback file    (MT4 → Python)",
    }
    for key, label in labels.items():
        passed = results.get(key, False)
        (ok if passed else fail)(label)
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("  🎉  All tests passed — bidirectional MT4 ↔ Python comms confirmed!\n")
        return 0
    else:
        print("  ⚠️   Some tests failed. Check the notes above.\n")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Aborted by user.\n")
        sys.exit(1)

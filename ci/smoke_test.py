# Simple smoke test: verify /healthz for expected services on known ports.
import time, sys
import urllib.request

services = {
    8081: "data-ingestor",
    8082: "indicator-engine",
    8083: "signal-generator",
    8084: "risk-manager",
    8085: "execution-engine",
    8086: "calendar-ingestor",
    8087: "reentry-matrix-svc",
    8088: "reporter",
    8080: "gui-gateway",
}

def check(port, retries=30, delay=2):
    url = f"http://localhost:{port}/healthz"
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(delay)
    return False

failed = []
for port, name in services.items():
    ok = check(port)
    print(f"{name} on {port}: {'OK' if ok else 'FAIL'}")
    if not ok:
        failed.append(name)

if failed:
    print("Smoke test failed for:", ", ".join(failed))
    sys.exit(1)
print("All services healthy.")

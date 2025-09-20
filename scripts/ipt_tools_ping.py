#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

import sys

try:
    import yaml  # type: ignore
except Exception:
    yaml = None


def run_cmd(cmd: List[str], timeout: float = 5.0) -> Dict[str, Any]:
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, text=True
        )
        out = proc.stdout.strip()
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "output": out,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except FileNotFoundError as e:
        return {"ok": False, "code": 127, "output": str(e), "latency_ms": int((time.time() - t0) * 1000)}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "code": 124, "output": f"timeout: {e}", "latency_ms": int((time.time() - t0) * 1000)}


def load_tools_cfg(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"tools config not found: {path}")
    if yaml is None:
        raise SystemExit("PyYAML is required. pip install pyyaml")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    root = Path.cwd()
    cfg_path = root / "config" / "tools.yaml"
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    out_path = state_dir / "tool_health.json"

    cfg = load_tools_cfg(cfg_path)
    tools = cfg.get("tools", [])
    results: List[Dict[str, Any]] = []
    for t in tools:
        name = t.get("name")
        version_cmd = t.get("version_cmd") or []
        health_cmd = t.get("health_cmd") or []
        caps = t.get("capabilities", [])
        cost_hint = t.get("cost_hint")

        vres = run_cmd(version_cmd) if version_cmd else {"ok": False, "output": "no version_cmd"}
        hres = run_cmd(health_cmd) if health_cmd else {"ok": False, "output": "no health_cmd"}
        status = "healthy" if hres.get("ok") else "unhealthy"
        results.append(
            {
                "name": name,
                "capabilities": caps,
                "status": status,
                "version": vres.get("output", ""),
                "latency_ms": hres.get("latency_ms"),
                "cost_hint": cost_hint,
                "checked_at": int(time.time()),
            }
        )

    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"tools": results}, f, indent=2)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())


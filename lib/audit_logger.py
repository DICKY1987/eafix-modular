from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict


AUDIT = Path("state/audit.jsonl")


def _ensure_dirs() -> None:
    AUDIT.parent.mkdir(parents=True, exist_ok=True)


def _sha256_of(obj: Any) -> str:
    try:
        data = json.dumps(obj, sort_keys=True).encode("utf-8")
    except Exception:
        data = str(obj).encode("utf-8", errors="replace")
    return hashlib.sha256(data).hexdigest()


def log_action(task_id: str, phase: str, action: str, details: Dict[str, Any] | None = None, cost_delta: float | None = None, tool: str | None = None) -> None:
    _ensure_dirs()
    details = details or {}
    entry = {
        "ts": int(time.time()),
        "task_id": task_id,
        "phase": phase,
        "action": action,
        "details": details,
        "cost_delta": cost_delta,
        "tool": tool,
        "sha": _sha256_of(details),
    }
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


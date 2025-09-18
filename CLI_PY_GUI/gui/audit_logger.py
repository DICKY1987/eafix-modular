# audit_logger.py
from __future__ import annotations
import os, json, time
from typing import Any

LOG_PATH = os.path.expanduser("~/.python_cockpit/audit.jsonl")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def write_event(evt: dict[str, Any]) -> None:
    try:
        evt = dict(evt)
        evt.setdefault("ts", time.time())
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")
    except Exception:
        pass

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict


LEDGER = Path("state/cost_ledger.jsonl")


def _ensure_dirs() -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)


def record_cost(task_id: str, tool: str, action: str, tokens: int | None, amount: float) -> None:
    _ensure_dirs()
    entry: Dict[str, Any] = {
        "ts": int(time.time()),
        "task_id": task_id,
        "tool": tool,
        "action": action,
        "tokens": tokens,
        "amount": amount,
    }
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_total_cost(task_id: str) -> float:
    if not LEDGER.exists():
        return 0.0
    total = 0.0
    with LEDGER.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("task_id") == task_id:
                try:
                    total += float(obj.get("amount", 0))
                except Exception:
                    pass
    return round(total, 4)


def record_gdw_cost(workflow_id: str, step_id: str | None, amount: float) -> None:
    """Convenience wrapper to record GDW execution costs.

    Uses a synthetic task_id namespace "gdw:<workflow_id>" and action "gdw_step".
    """
    tid = f"gdw:{workflow_id}"
    action = "gdw_step" if step_id else "gdw"
    record_cost(task_id=tid, tool="gdw_runner", action=f"{action}:{step_id or 'all'}", tokens=None, amount=amount)


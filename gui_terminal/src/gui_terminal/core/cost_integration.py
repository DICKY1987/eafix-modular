from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _import_cost_tracker():
    try:
        # Try relative import if repo root is on sys.path
        from lib import cost_tracker  # type: ignore
        return cost_tracker
    except Exception:
        # Attempt to add repo root next to this file (two levels up from gui_terminal/src)
        import sys

        root = Path(__file__).resolve().parents[4]
        if str(root) not in sys.path:
            sys.path.append(str(root))
        try:
            from lib import cost_tracker  # type: ignore
            return cost_tracker
        except Exception:
            return None


@dataclass
class CostEvent:
    task_id: str
    tool: str
    action: str
    tokens: Optional[int]
    amount: float


class CostTrackerBridge:
    """Thin adapter to the platform's lib.cost_tracker module."""

    def __init__(self) -> None:
        self._impl = _import_cost_tracker()

    def available(self) -> bool:
        return self._impl is not None

    def record(self, ev: CostEvent) -> None:
        if not self._impl:
            return
        try:
            self._impl.record_cost(ev.task_id, ev.tool, ev.action, ev.tokens, ev.amount)
        except Exception:
            pass

    def total_for(self, task_id: str) -> float:
        if not self._impl:
            return 0.0
        try:
            return float(self._impl.get_total_cost(task_id))
        except Exception:
            return 0.0


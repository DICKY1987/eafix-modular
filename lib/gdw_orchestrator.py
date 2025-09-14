from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .audit_logger import log_action


@dataclass
class DeferDecision:
    workflow_id: str
    reason: str
    inputs: Dict[str, Any]


def load_policies(repo_root: Path) -> Dict[str, Any]:
    path = repo_root / "config" / "gdw_policies.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def maybe_defer_to_gdw(task_description: str, repo_root: Path) -> Optional[DeferDecision]:
    """Very small heuristic to demonstrate GDW deferral decision.

    If policies contain a substring match to a known GDW, return a decision.
    """
    policies = load_policies(repo_root)
    rules = policies.get("rules", [])
    for r in rules:
        needle = str(r.get("match_substring", "")).lower()
        if needle and needle in task_description.lower():
            wf = str(r.get("workflow_id", "")).strip()
            if wf:
                log_action("gdw:decision", phase="route", action="defer", details={"workflow": wf, "reason": r.get("reason", "rule_match")})
                return DeferDecision(workflow_id=wf, reason=str(r.get("reason", "rule_match")), inputs=dict(r.get("inputs", {})))
    return None


from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import os

from .audit_logger import log_action
from .gdw_runner import execute_gdw
from .event_bus_client import publish_event


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


def get_deferral_mode(repo_root: Path) -> str:
    """Return deferral mode: off | prefer | only. Env overrides take precedence.

    GDW_ONLY => only, GDW_PREFER => prefer.
    """
    env = os.environ
    if env.get("GDW_ONLY") == "1":
        return "only"
    if env.get("GDW_PREFER") == "1":
        return "prefer"
    cfg = load_policies(repo_root)
    deferral = cfg.get("deferral", {})
    if not deferral or not deferral.get("enabled", False):
        return "off"
    mode = str(deferral.get("mode", "off")).lower()
    return mode if mode in ("off", "prefer", "only") else "off"


def should_fully_defer(decision: DeferDecision, repo_root: Path) -> bool:
    mode = get_deferral_mode(repo_root)
    if mode == "only":
        return True
    # Check rule hints (risk tier)
    # Load original rule for force_defer if present
    cfg = load_policies(repo_root)
    for r in cfg.get("rules", []):
        if str(r.get("workflow_id")) == decision.workflow_id:
            if bool(r.get("force_defer", False)):
                return True
    return False


def defer_and_capture(decision: DeferDecision, repo_root: Path, dry_run: bool = False) -> Dict[str, Any]:
    spec = (repo_root / "gdw" / decision.workflow_id / "v1.0.0" / "spec.json")
    result = {"error": "spec_not_found", "workflow": decision.workflow_id}
    if spec.exists():
        res = execute_gdw(spec, inputs=decision.inputs, dry_run=dry_run)
        result = {"workflow": decision.workflow_id, **res}
    log_action(
        task_id=f"gdw:{decision.workflow_id}",
        phase="defer",
        action="gdw_execute",
        details={"reason": decision.reason, "result": result},
        cost_delta=0.0,
        tool="gdw_runner",
    )
    publish_event({
        "type": "gdw.deferred",
        "workflow": decision.workflow_id,
        "reason": decision.reason,
        "rc": result.get("rc"),
        "steps": result.get("steps"),
    })
    return result

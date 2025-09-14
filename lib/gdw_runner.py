from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cost_tracker import record_gdw_cost
from .event_bus_client import publish_event
from .gdw_metrics import GDW_RUNS_TOTAL, GDW_RUN_DURATION


@dataclass
class GDWSpec:
    id: str
    version: str
    steps: List[Dict[str, Any]]
    observability: Dict[str, Any]


def load_spec(spec_path: Path) -> GDWSpec:
    with spec_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return GDWSpec(
        id=str(data.get("id")),
        version=str(data.get("version")),
        steps=list(data.get("steps", [])),
        observability=dict(data.get("observability", {})),
    )


def run_step(step: Dict[str, Any], env: Dict[str, str], dry_run: bool = True) -> int:
    runner = step.get("runner")
    cmd = step.get("cmd")
    timeout = int(step.get("timeout_sec", 120))
    if dry_run:
        print(f"[GDW] DRY step runner={runner} cmd={cmd}")
        return 0
    if not isinstance(cmd, str) or not cmd:
        print("[GDW] invalid step command", file=sys.stderr)
        return 2
    # Simplified: only support shell execution of command strings for bash/powershell/git
    shell = True
    try:
        proc = subprocess.run(cmd, shell=shell, env=env, timeout=timeout)
        return proc.returncode
    except subprocess.TimeoutExpired:
        return 124


def run_gdw(spec_path: Path, inputs: Optional[Dict[str, Any]] = None, dry_run: bool = True) -> int:
    spec = load_spec(spec_path)
    publish_event({"type": "gdw.start", "workflow": spec.id, "version": spec.version, "dry": dry_run})
    if GDW_RUNS_TOTAL:
        try:
            GDW_RUNS_TOTAL.labels(workflow=spec.id).inc()
        except Exception:
            pass
    print(f"[GDW] Executing {spec.id}@{spec.version} dry={dry_run}")
    env = os.environ.copy()
    env["GDW_SPEC"] = str(spec_path)
    env["GDW_INPUTS"] = json.dumps(inputs or {})
    env["GDW_DRY_RUN"] = "1" if dry_run else "0"
    import time
    t0 = time.time()
    rc = 0
    for step in spec.steps:
        step_id = str(step.get("id"))
        rc = run_step(step, env=env, dry_run=dry_run)
        record_gdw_cost(spec.id, step_id, amount=0.0)
        if rc != 0:
            print(f"[GDW] Step failed: {step_id} rc={rc}", file=sys.stderr)
            break
    if GDW_RUN_DURATION:
        try:
            GDW_RUN_DURATION.labels(workflow=spec.id).observe(max(0.0, time.time() - t0))
        except Exception:
            pass
    publish_event({"type": "gdw.end", "workflow": spec.id, "version": spec.version, "rc": rc})
    print(f"[GDW] Done rc={rc}")
    return rc


def execute_gdw(spec_path: Path, inputs: Optional[Dict[str, Any]] = None, dry_run: bool = True) -> Dict[str, Any]:
    """Execute a GDW and return a structured result without changing CLI compatibility.

    Returns a dict with keys: id, version, rc, steps (list of {id, rc}).
    """
    spec = load_spec(spec_path)
    env = os.environ.copy()
    env["GDW_SPEC"] = str(spec_path)
    env["GDW_INPUTS"] = json.dumps(inputs or {})
    env["GDW_DRY_RUN"] = "1" if dry_run else "0"
    step_results: List[Dict[str, Any]] = []
    rc = 0
    for step in spec.steps:
        step_id = str(step.get("id"))
        rc = run_step(step, env=env, dry_run=dry_run)
        publish_event({"type": "gdw.step", "workflow": spec.id, "step": step_id, "rc": rc})
        record_gdw_cost(spec.id, step_id, amount=0.0)
        step_results.append({"id": step_id, "rc": rc})
        if rc != 0:
            break
    artifacts = list(spec.observability.get("artifact_paths", [])) if isinstance(spec.observability, dict) else []
    return {"id": spec.id, "version": spec.version, "rc": rc, "steps": step_results, "artifacts": artifacts}

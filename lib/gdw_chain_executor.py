from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path

from .gdw_runner import run_gdw


@dataclass
class ChainStep:
    workflow: str
    inputs: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class ChainResult:
    success: bool
    step_results: List[Dict[str, Any]]


class GDWChainExecutor:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def execute(self, steps: List[ChainStep], dry_run: bool = True) -> ChainResult:
        results: List[Dict[str, Any]] = []
        for step in steps:
            spec = (self.repo_root / "gdw" / step.workflow / "v1.0.0" / "spec.json").resolve()
            t0 = time.time()
            rc = run_gdw(spec, inputs=step.inputs, dry_run=dry_run)
            results.append({
                "workflow": step.workflow,
                "inputs": step.inputs,
                "rc": rc,
                "duration": round(time.time() - t0, 3),
            })
            if rc != 0:
                return ChainResult(success=False, step_results=results)
        return ChainResult(success=True, step_results=results)


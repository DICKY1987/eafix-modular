#!/usr/bin/env python3
# doc_id: DOC-CI-ATOMIC-MANIFEST-0001
"""Read-only authority validation; the default route is full acceptance."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=["active", "progress"], default="active")
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    control = "governance/module_consolidation/"
    command = [sys.executable, control + "validate_consolidation.py", "--mode", "active"]
    if args.scope == "progress":
        command = [sys.executable, control + "progress_gate.py"]
    validation = subprocess.run(command, cwd=repo, check=False)
    if validation.returncode or args.scope == "progress":
        return validation.returncode
    # Check parity only. CI never writes roots or regenerates projections.
    return subprocess.run([sys.executable, control + "generate_projections.py", "--check"],
                          cwd=repo, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

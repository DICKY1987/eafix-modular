#!/usr/bin/env python3
"""Materialize and validate the staged EAFIX registry implementation.

Run from the repository root on branch copilot/eafix-registry-system-v1:
    python tools/registries/bootstrap_registry_system.py
"""
from __future__ import annotations

import base64
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "tools" / "registries" / "bootstrap-parts"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    part_files = sorted(PARTS.glob("part-*.b64"))
    if len(part_files) != 7:
        raise SystemExit(f"Expected 7 payload parts, found {len(part_files)}")

    encoded = "".join(path.read_text(encoding="utf-8").strip() for path in part_files)
    archive_bytes = base64.b64decode(encoded, validate=True)

    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "eafix-registry-source.tar.gz"
        archive.write_bytes(archive_bytes)
        with tarfile.open(archive, "r:gz") as bundle:
            bundle.extractall(ROOT)

    shutil.rmtree(PARTS)
    (ROOT / ".github" / "workflows" / "registry-bootstrap.yml").unlink(missing_ok=True)

    wrapper = ROOT / "tools" / "registries" / "build_registries.py"
    wrapper.write_text(
        "import argparse\n"
        "from registry_core import run\n"
        "if __name__ == '__main__':\n"
        "    p = argparse.ArgumentParser()\n"
        "    p.add_argument('--check', action='store_true')\n"
        "    p.add_argument('--report-only', action='store_true')\n"
        "    a = p.parse_args()\n"
        "    raise SystemExit(run(check=a.check, report_only=a.report_only))\n",
        encoding="utf-8",
        newline="\n",
    )

    for cache in ROOT.rglob("__pycache__"):
        if cache.is_dir():
            shutil.rmtree(cache)
    for pyc in ROOT.rglob("*.pyc"):
        pyc.unlink()

    run(sys.executable, "-m", "pip", "install", "jsonschema")
    run(sys.executable, "tools/registries/build_registries.py")
    run(sys.executable, "tools/registries/validate_record_schemas.py")
    run(sys.executable, "tools/registries/validate_registry_ids.py")
    run(sys.executable, "tools/registries/validate_registry_references.py")
    run(sys.executable, "tools/registries/validate_registry_authority.py")
    run(sys.executable, "tools/registries/build_registries.py", "--check")
    run(sys.executable, "-m", "unittest", "discover", "-s", "tests/registries", "-p", "test_*.py")

    print("Registry implementation materialized and validated.")
    print("Review changes, then commit them to copilot/eafix-registry-system-v1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

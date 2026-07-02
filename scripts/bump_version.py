#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


PYPROJECT = Path("pyproject.toml")


def bump(version: str, kind: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if kind == "major":
        major += 1
        minor = 0
        patch = 0
    elif kind == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def main(argv: list[str]) -> int:
    if not PYPROJECT.exists():
        print("pyproject.toml not found", file=sys.stderr)
        return 1
    kind = argv[1] if len(argv) > 1 else "patch"
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r"^version\s*=\s*\"(\d+\.\d+\.\d+)\"", text, flags=re.M)
    if not m:
        print("version not found in pyproject.toml", file=sys.stderr)
        return 1
    current = m.group(1)
    newv = bump(current, kind)
    text = re.sub(r"^version\s*=\s*\"(\d+\.\d+\.\d+)\"", f"version = \"{newv}\"", text, flags=re.M)
    PYPROJECT.write_text(text, encoding="utf-8")
    print(newv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


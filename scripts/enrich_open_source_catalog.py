from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Set

# Minimal, deterministic enrichment using awesome-selfhosted to set `self_hostable`.


def normalize(name: str) -> str:
    s = name.strip()
    # Drop any parenthetical qualifiers, e.g. "Z3 (SMT solver)" -> "Z3"
    s = re.sub(r"\s*\([^)]*\)\s*", " ", s)
    # Collapse whitespace and lowercase
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def fetch_awesome_selfhosted() -> Set[str]:
    import urllib.request

    url = (
        "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md"
    )
    with urllib.request.urlopen(url) as resp:
        content = resp.read().decode("utf-8", errors="ignore")

    names: Set[str] = set()
    # Lines typically look like: "- [AppName](https://...) - description"
    link_re = re.compile(r"^\s*[-*]\s*\[([^\]]+)]\(([^)]+)\)")
    for line in content.splitlines():
        m = link_re.match(line)
        if not m:
            continue
        app = m.group(1).strip()
        if app:
            names.add(normalize(app))
    return names


def main() -> None:
    ap = argparse.ArgumentParser(description="Enrich catalog JSON using awesome-selfhosted for self_hostable flag")
    ap.add_argument("--input", default=str(Path("P_tests/fixtures/open_source_apps_catalog.json")))
    ap.add_argument("--output", default=None, help="If omitted, updates in place")
    args = ap.parse_args()

    inp = Path(args.input)
    outp = Path(args.output) if args.output else inp

    data: List[Dict] = json.loads(inp.read_text(encoding="utf-8"))

    selfhosted_names = fetch_awesome_selfhosted()

    updated = 0
    for entry in data:
        name = entry.get("name", "")
        if not name:
            continue
        nm = normalize(name)
        if nm in selfhosted_names:
            if entry.get("self_hostable") is not True:
                entry["self_hostable"] = True
                updated += 1

    outp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {updated} entries with self_hostable=true. Output: {outp}")


if __name__ == "__main__":
    main()


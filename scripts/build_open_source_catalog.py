from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, Set, List


def normalize_name(raw: str) -> str:
    # Keep names as they appear; just trim whitespace and trailing punctuation
    return raw.strip().strip("\u200b").strip()


def parse_opensource_md(path: Path) -> Iterable[str]:
    names: List[str] = []
    if not path.exists():
        return names

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.rstrip("\n\r") for ln in f]

    # Collect all non-empty lines that look like names; exclude commentary markers
    collecting_after_list_header = False
    skip_until_chatgpt = False
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.lower().startswith("you said:"):
            skip_until_chatgpt = True
            continue
        if s.lower().startswith("chatgpt said:"):
            skip_until_chatgpt = False
            continue
        if skip_until_chatgpt:
            continue
        if s.lower().startswith("thought for"):
            continue
        if s.lower().startswith("here are 50"):
            collecting_after_list_header = True
            continue

        # Exclusions explicitly noted in the doc
        if "note: not open-source" in s.lower():
            continue
        if "initiative, not a single app" in s.lower():
            continue

        # Pre-header items are also valid names; include both pre and post sections
        if collecting_after_list_header or s:
            names.append(normalize_name(s))

    return names


def parse_opensource1_md(path: Path) -> Iterable[str]:
    names: List[str] = []
    if not path.exists():
        return names
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            low = s.lower()
            if low.startswith("compare to:"):
                # Skip proprietary/comparison references
                continue
            if " = " in s:
                try:
                    _, rhs = s.split("=", 1)
                except ValueError:
                    continue
                # Split common list separators (comma-separated). Keep items as-is otherwise.
                parts = [normalize_name(p) for p in rhs.split(",")]
                for p in parts:
                    if p:
                        names.append(p)
    return names


def parse_missing_csv(path: Path) -> Iterable[str]:
    names: List[str] = []
    if not path.exists():
        return names
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for idx, raw in enumerate(f):
            s = raw.strip()
            if idx == 0:
                # header/comment line
                continue
            if not s:
                continue
            names.append(normalize_name(s))
    return names


def unique_ordered(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for it in items:
        if it and it not in seen:
            seen.add(it)
            out.append(it)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Build open source apps catalog JSON from provided documents.")
    ap.add_argument(
        "--source-dir",
        default=str(Path.home() / "Downloads" / "OPEN_SOURCE_APPS_LIIB"),
        help="Directory containing opensource.md, opensource1.md, and Apps_Missing_From_Document.csv",
    )
    ap.add_argument(
        "--output",
        default=str(Path("P_tests/fixtures/open_source_apps_catalog.json")),
        help="Output JSON file path",
    )
    ap.add_argument(
        "--include-missing-csv",
        action="store_true",
        help="Also include names from Apps_Missing_From_Document.csv (may contain non-open-source entries)",
    )
    args = ap.parse_args()

    src = Path(args.source_dir)
    md1 = src / "opensource.md"
    md2 = src / "opensource1.md"
    csv = src / "Apps_Missing_From_Document.csv"

    names: List[str] = []
    names.extend(parse_opensource_md(md1))
    names.extend(parse_opensource1_md(md2))
    if args.include_missing_csv:
        names.extend(parse_missing_csv(csv))

    # De-duplicate while preserving order
    uniq = unique_ordered(names)

    # Build entries with name + deterministic fields from documents only
    # - open_source: true (since sources are explicitly open-source lists)
    # - other fields left as explicit null to make blanks clear
    entries = [
        {
            "name": nm,
            "open_source": True,
            "beginner_friendly": None,
            "cost": None,
            "usage_limitations": None,
            "pricing_model": None,
            "license_spdx_id": None,
            "license_allows_commercial_use": None,
            "self_hostable": None,
            "cloud_only": None,
            "requires_account": None,
            "requires_credit_card": None,
            "proprietary_dependency": None,
        }
        for nm in uniq
    ]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(entries)} entries to {out_path}")


if __name__ == "__main__":
    main()

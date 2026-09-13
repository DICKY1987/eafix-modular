#!/usr/bin/env python3
"""
validate_module_structure.py

Structural validator for the 34-module tree (m0001-*.. m0034-*).

This is the CI gate recommended by the module-governance audit
(step 4 of the "highest-leverage sequence" -- see DECISION_LOG.md at the repo
root for the full rationale). It enforces the invariants the audit found
broken or unenforced:

  1. Exactly one manifest.json per module folder, and it must parse as JSON.
  2. No filesystem path is claimed as `owned_files` by more than one module
     manifest (exclusive ownership -- Principle 3 / Principle 6).
  3. Every path listed in a manifest's owned_files / source_files / test_files
     / configuration_files / schema_files / shared_files actually exists in
     the repository (no phantom paths).
  4. `file_ownership.module_root` is set (not null) and is a directory that
     exists on disk (not a file, not missing).
  5. Every module folder has a README.md and an AGENTS.md at its root
     (Principle 7 -- AI-first design; see EAFIX_PROPOSED_34_MODULE_FILE_TREE.md).

What this deliberately does NOT check (out of scope by design, see
DECISION_LOG.md "Deferred / Not Done"):
  - Whether module_root physically *contains* every owned file (many modules
    legitimately still have code living in a shared, not-yet-split service
    directory pending physical migration -- that's tracked separately).
  - Full ownership coverage (i.e. that every .py file in the repo belongs to
    some module) -- only 24.9% of tracked source is currently mapped, and
    closing that gap is a large follow-up effort, not a CI gate.

Exit code 0 = pass, 1 = fail. Prints one line per violation.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FILE_LIST_KEYS = [
    "owned_files",
    "source_files",
    "test_files",
    "contract_files",
    "documentation_files",
    "configuration_files",
    "schema_files",
]


def find_module_dirs() -> list[Path]:
    return sorted(
        d for d in REPO_ROOT.iterdir()
        if d.is_dir() and d.name.startswith("m0") and d.name[1:5].isdigit()
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    module_dirs = find_module_dirs()
    if not module_dirs:
        print("ERROR: no module directories found (expected m00NN-* folders at repo root)")
        return 1

    manifests: dict[str, dict] = {}
    owned_by: dict[str, list[str]] = {}

    for d in module_dirs:
        modname = d.name
        manifest_path = d / "manifest.json"

        if not manifest_path.exists():
            errors.append(f"[{modname}] missing manifest.json")
            continue

        try:
            m = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"[{modname}] manifest.json is not valid JSON: {e}")
            continue

        manifests[modname] = m

        if not (d / "README.md").exists():
            errors.append(f"[{modname}] missing README.md")
        if not (d / "AGENTS.md").exists():
            errors.append(f"[{modname}] missing AGENTS.md")

        fo = m.get("file_ownership", {})

        module_root = fo.get("module_root")
        if module_root is None:
            errors.append(f"[{modname}] file_ownership.module_root is null")
        else:
            root_path = REPO_ROOT / module_root
            if not root_path.exists():
                errors.append(f"[{modname}] module_root '{module_root}' does not exist on disk")
            elif not root_path.is_dir():
                errors.append(f"[{modname}] module_root '{module_root}' is not a directory")

        # phantom-path + ownership-collision checks
        for key in FILE_LIST_KEYS:
            for p in fo.get(key) or []:
                if not (REPO_ROOT / p).exists():
                    errors.append(f"[{modname}] {key} references nonexistent path: {p}")
                if key == "owned_files":
                    owned_by.setdefault(p, []).append(modname)

        for entry in fo.get("shared_files") or []:
            p = entry.get("path")
            if p and not (REPO_ROOT / p).exists():
                errors.append(f"[{modname}] shared_files references nonexistent path: {p}")

    for path, mods in owned_by.items():
        if len(mods) > 1:
            errors.append(
                f"OWNERSHIP COLLISION: '{path}' is in owned_files of {len(mods)} modules: {', '.join(mods)}"
            )

    print(f"Checked {len(manifests)} module manifests under {len(module_dirs)} module directories.")
    print(f"Distinct owned_files paths tracked: {len(owned_by)}")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FAIL  {e}")

    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s). Structure validation FAILED.")
        return 1

    print(f"\n0 errors, {len(warnings)} warning(s). Structure validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

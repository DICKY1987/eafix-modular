#!/usr/bin/env python3
"""
Create the EAFIX consolidation project and its field set. Cross-platform
(Python port of the original bash version, for machines without Git Bash
on PATH). Idempotent: re-running skips fields/project that already exist.

Prereqs:
    gh auth login
    gh auth refresh -s project -s read:project

Usage:
    python project_bootstrap.py <owner> [--title "..."]
"""
import argparse, json, subprocess, sys

def gh(args, check=True):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout

FIELDS = [
    ("Item Type",       "SINGLE_SELECT", "Phase,Gate,Decision,Deliverable,Wave,Module"),
    ("Phase",           "SINGLE_SELECT", "P0,P1,P2,P3,P4,P5,P6,P7,P8"),
    ("Wave",            "SINGLE_SELECT", "W1,W2,W3,W4,W5,W6,W7,W8,Not Applicable"),
    ("Schema Valid",    "SINGLE_SELECT", "Unknown,Pass,Fail"),
    ("Spec Ready",      "SINGLE_SELECT", "Unknown,Pass,Fail"),
    ("Impl Verified",   "SINGLE_SELECT", "Unknown,Pass,Fail,Not Applicable"),
    ("Pilot",           "SINGLE_SELECT", "Yes,No"),
    ("SSOT ID",         "TEXT", None),
    ("Module Root",     "TEXT", None),
    ("Permanent ID",    "TEXT", None),
    ("Evidence Ref",    "TEXT", None),
    ("Approver",        "TEXT", None),
    ("Baseline Commit", "TEXT", None),
    ("Blocked Reason",  "TEXT", None),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("owner")
    ap.add_argument("--title", default="EAFIX 34-Module Documentation Consolidation")
    a = ap.parse_args()

    try:
        gh(["auth", "status"])
    except RuntimeError:
        print("Not authenticated. Run: gh auth login", file=sys.stderr)
        sys.exit(1)

    projects = json.loads(gh(["project", "list", "--owner", a.owner, "--format", "json", "--limit", "100"]))
    num = None
    for p in projects.get("projects", []):
        if p.get("title") == a.title:
            num = p["number"]
            break

    if num is None:
        print(f"Creating project: {a.title}")
        created = json.loads(gh(["project", "create", "--owner", a.owner, "--title", a.title, "--format", "json"]))
        num = created["number"]
        print(f"  created project #{num}")
    else:
        print(f"Project already exists: #{num}")

    existing = {f["name"] for f in json.loads(
        gh(["project", "field-list", str(num), "--owner", a.owner, "--format", "json", "--limit", "100"]))["fields"]}

    print("Fields:")
    for name, dtype, opts in FIELDS:
        if name in existing:
            print(f"  = {name} (exists)")
            continue
        args = ["project", "field-create", str(num), "--owner", a.owner,
                "--name", name, "--data-type", dtype]
        if opts:
            args += ["--single-select-options", opts]
        gh(args)
        print(f"  + {name} ({dtype})")

    print(f"\nProject #{num} ready.")
    print(f"Next: python project_sync.py --owner {a.owner} --project {num} "
          f"--repo DICKY1987/eafix-modular --dry-run")

if __name__ == "__main__":
    main()

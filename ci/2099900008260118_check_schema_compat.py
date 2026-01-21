# doc_id: DOC-DOC-0025
# DOC_ID: DOC-SERVICE-0004
# Simple backward-compatibility checker for JSON Schemas in contracts/events.
# Compares current working tree files vs a base git ref (default: origin/main).
#
# Rules (heuristics):
#   - Removing a property is BREAKING.
#   - Changing the type of a property is BREAKING.
#   - Adding to "required" is BREAKING.
#   - Removing from "required" is OK (more permissive).
#   - Adding a new property is OK.
#
# Usage:
#   BASE_REF=origin/main python ci/check_schema_compat.py

import json, os, subprocess, pathlib, sys

BASE = os.environ.get("BASE_REF", "origin/main")
CONTRACT_DIR = pathlib.Path("contracts/events")
changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "--", str(CONTRACT_DIR)]).decode().splitlines()
changed = [p for p in changed if p.endswith(".schema.json")]
if not changed:
    print("No changed schemas.")
    sys.exit(0)

def load_current(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

def load_base(path):
    content = subprocess.check_output(["git", "show", f"{BASE}:{path}"])
    return json.loads(content.decode())

def prop_types(schema):
    props = schema.get("properties", {})
    return {k: v.get("type") for k,v in props.items()}

def required_set(schema):
    return set(schema.get("required", []))

breaking = []
for p in changed:
    try:
        cur = load_current(p)
        old = load_base(p)
    except subprocess.CalledProcessError:
        # File is new; treat as non-breaking
        print(f"New schema (no base): {p}")
        continue
    except Exception as e:
        print(f"Error loading schemas for {p}: {e}", file=sys.stderr)
        sys.exit(2)

    cur_props = set(cur.get("properties", {}).keys())
    old_props = set(old.get("properties", {}).keys())

    # Removed property
    removed = old_props - cur_props
    for r in removed:
        breaking.append((p, f"Removed property '{r}'"))

    # Type changes
    old_types = prop_types(old)
    cur_types = prop_types(cur)
    for k in old_props & cur_props:
        if old_types.get(k) != cur_types.get(k):
            breaking.append((p, f"Type change for '{k}': {old_types.get(k)} -> {cur_types.get(k)}"))

    # Required changes
    old_req = required_set(old)
    cur_req = required_set(cur)
    added_required = cur_req - old_req
    for r in added_required:
        breaking.append((p, f"Added required property '{r}'"))

    if breaking:
        print(f"Checked {p}: BREAKING changes found.")
    else:
        print(f"Checked {p}: OK (no breaking changes).")

if breaking:
    print("\nBackward compatibility violations:")
    for f, msg in breaking:
        print(f"- {f}: {msg}")
    sys.exit(1)
else:
    sys.exit(0)

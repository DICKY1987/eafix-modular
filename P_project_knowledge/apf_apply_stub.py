"""
apf_apply_stub.py — Minimal skeleton to apply an APF Change Request (Edit Script)
NOTE: This is a stub for wiring and audit flow demonstration.
"""
import argparse, sys, hashlib, json, os, datetime
from typing import Any, Dict, List

try:
    import yaml  # PyYAML
except Exception:
    yaml = None

def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def load_yaml(path: str) -> Dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML not available. Install pyyaml to use this stub.")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path: str, data: Dict[str, Any]) -> None:
    if yaml is None:
        raise SystemExit("PyYAML not available. Install pyyaml to use this stub.")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)

def validate_cr_schema(cr: Dict[str, Any]) -> List[str]:
    errors = []
    for k in ["change_id", "title", "author", "created_utc", "target_file", "ops"]:
        if k not in cr:
            errors.append(f"missing required field: {k}")
    if not isinstance(cr.get("ops", []), list) or not cr["ops"]:
        errors.append("ops must be a non-empty list")
    return errors

def dry_run_apply(master: Dict[str, Any], cr: Dict[str, Any]) -> Dict[str, Any]:
    """Return a summary of what would change (no actual edits)."""
    summary = {"applies_to": cr["target_file"], "ops": []}
    for op in cr["ops"]:
        summary["ops"].append({"op_id": op["op_id"], "op": op["op"], "target": op.get("target_step"), "note": "dry-run only"})
    return summary

def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--apply", help="Path to CR yaml to apply")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--validate-only", help="Validate a master.yaml and exit")
    p.add_argument("--lint-cr", help="Glob for CR files to lint (very light stub)")
    args = p.parse_args(argv)

    if args.validate_only:
        if not os.path.exists(args.validate_only):
            print(f"ERROR: master not found: {args.validate_only}", file=sys.stderr)
            return 2
        # Placeholder: add schema + semantic validation here
        print(f"OK: validated {args.validate_only} (stub)")
        return 0

    if args.lint_cr:
        # Minimal demonstration: just check each CR loads and basic fields exist
        import glob
        rc = 0
        for path in glob.glob(args.lint_cr):
            try:
                cr = load_yaml(path)
                errs = validate_cr_schema(cr)
                if errs:
                    rc = 2
                    print(f"{path}: INVALID -> " + "; ".join(errs))
                else:
                    print(f"{path}: OK")
            except Exception as e:
                rc = 2
                print(f"{path}: ERROR -> {e}")
        return rc

    if args.apply:
        cr = load_yaml(args.apply)
        errs = validate_cr_schema(cr)
        if errs:
            print("CR schema errors: " + "; ".join(errs), file=sys.stderr)
            return 2

        master_path = cr["target_file"]
        if not os.path.exists(master_path):
            print(f"ERROR: master not found: {master_path}", file=sys.stderr)
            return 2

        computed_sha = sha256(master_path)
        exp_sha = cr.get("preconditions", {}).get("expected_master_sha256")
        if exp_sha and exp_sha.lower() != computed_sha.lower():
            print(f"ERROR: expected_master_sha256 mismatch. expected {exp_sha}, got {computed_sha}", file=sys.stderr)
            return 2

        master = load_yaml(master_path)

        if args.dry_run:
            summary = dry_run_apply(master, cr)
            print(json.dumps(summary, indent=2))
            return 0

        # IMPORTANT: Here you'd open a transaction, snapshot, apply each op with a sequencer,
        # run validators, produce a renumber map, and write updates atomically.
        # This stub only writes an audit record for demonstration.
        out_dir = os.path.join("audit", cr["change_id"])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "apply.log"), "w", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.utcnow().isoformat()}Z] APPLY (stub) -> {master_path}\n")
            for op in cr["ops"]:
                f.write(f" - {op['op_id']} {op['op']} target={op.get('target_step')}\n")
        print(f"Stub apply complete. See {out_dir}/apply.log")
        return 0

    p.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

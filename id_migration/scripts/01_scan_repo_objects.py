"""PH-01-STEP-001: Baseline Repository Scanner.

Walks the repository tree and produces physical_inventory_baseline.csv
with classification columns for downstream identity assignment.

Read-only: this script modifies NO repository files (only writes the output CSV).
"""

import csv
import fnmatch
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parent / "config"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"

# ---------------------------------------------------------------------------
# Path normalisation
# ---------------------------------------------------------------------------

def normalize_path(abs_path: str, repo_root: str) -> str:
    """Return a forward-slash relative path with no leading ./ or trailing /."""
    rel = os.path.relpath(abs_path, repo_root)
    # Convert to forward slashes
    rel = rel.replace("\\", "/")
    # Strip leading ./
    while rel.startswith("./"):
        rel = rel[2:]
    # Collapse duplicate separators
    rel = re.sub(r"/+", "/", rel)
    # Strip trailing separator
    rel = rel.rstrip("/")
    # Resolve . and .. (use PurePosixPath for clean resolution)
    parts = []
    for seg in rel.split("/"):
        if seg == ".":
            continue
        if seg == ".." and parts:
            parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts)

# ---------------------------------------------------------------------------
# Exclusion helpers
# ---------------------------------------------------------------------------

def is_excluded_dir(dir_name: str, excluded_dirs: list[str]) -> bool:
    return dir_name in excluded_dirs

def is_excluded_file(file_name: str, excluded_patterns: list[str]) -> bool:
    for pat in excluded_patterns:
        if fnmatch.fnmatch(file_name, pat):
            return True
    return False

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def load_classification_rules(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def classify_path(rel_path: str, object_type: str, rules_data: dict) -> dict:
    """Return classification dict for a given relative path."""
    default_class = rules_data.get("default_scope_class", "module_owned")
    classifications = rules_data.get("classifications", {})
    rules = rules_data.get("rules", [])

    scope_class = default_class

    # Ensure path uses forward slashes for matching
    match_path = rel_path.replace("\\", "/")
    # For directories, append trailing slash for prefix matching
    if object_type == "directory" and not match_path.endswith("/"):
        match_path_for_rules = match_path + "/"
    else:
        match_path_for_rules = match_path

    for rule in rules:
        match_type = rule["match_type"]
        values = rule["values"]
        matched = False

        if match_type == "path_prefix":
            for v in values:
                if match_path_for_rules.startswith(v) or match_path.startswith(v):
                    matched = True
                    break
        elif match_type == "path_contains":
            for v in values:
                if v in match_path_for_rules or v in match_path:
                    matched = True
                    break

        if matched:
            scope_class = rule["scope_class"]
            break  # first match wins

    class_info = classifications.get(scope_class, {})
    is_semantic = class_info.get("is_semantic_candidate", False)

    return {
        "object_scope_class": scope_class,
        "is_semantic_candidate": is_semantic,
    }

# ---------------------------------------------------------------------------
# Semantic role inference
# ---------------------------------------------------------------------------

# Common filename stems that map to roles
ROLE_PATTERNS = [
    (re.compile(r"config", re.I), "config"),
    (re.compile(r"plugin", re.I), "plugin"),
    (re.compile(r"processor", re.I), "processor"),
    (re.compile(r"orchestrat", re.I), "orchestrator"),
    (re.compile(r"validator", re.I), "validator"),
    (re.compile(r"health", re.I), "health"),
    (re.compile(r"metric", re.I), "metrics"),
    (re.compile(r"__init__", re.I), "init"),
    (re.compile(r"__main__", re.I), "main"),
    (re.compile(r"test_", re.I), "test"),
    (re.compile(r"_test$", re.I), "test"),
    (re.compile(r"model", re.I), "model"),
    (re.compile(r"schema", re.I), "schema"),
    (re.compile(r"cli", re.I), "cli"),
    (re.compile(r"resolver", re.I), "resolver"),
    (re.compile(r"adapter", re.I), "adapter"),
    (re.compile(r"handler", re.I), "handler"),
    (re.compile(r"scanner", re.I), "scanner"),
    (re.compile(r"generat", re.I), "generator"),
    (re.compile(r"migrat", re.I), "migration"),
    (re.compile(r"watcher", re.I), "watcher"),
    (re.compile(r"audit", re.I), "audit"),
    (re.compile(r"backup", re.I), "backup"),
    (re.compile(r"readme", re.I), "readme"),
    (re.compile(r"changelog", re.I), "changelog"),
]

def infer_semantic_role(name: str, object_type: str) -> str:
    """Infer a candidate semantic role from the filename stem."""
    if object_type == "directory":
        return ""
    stem = Path(name).stem
    # Strip leading numeric ID prefix (e.g. 2099900144260118_)
    stripped = re.sub(r"^\d+_", "", stem)
    for pattern, role in ROLE_PATTERNS:
        if pattern.search(stripped):
            return role
    return ""

def infer_module_hint(rel_path: str) -> str:
    """Extract service name from services/{name}/... paths."""
    parts = rel_path.split("/")
    if len(parts) >= 2 and parts[0] == "services":
        return parts[1]
    return ""

# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "object_type",
    "relative_path",
    "name",
    "parent_relative_path",
    "extension",
    "exists_on_disk",
    "is_excluded",
    "object_scope_class",
    "candidate_semantic_role",
    "path_normalized",
    "is_semantic_candidate",
    "inferred_module_hint",
]

def scan_repository(config: dict, classification_rules: dict) -> list[dict]:
    """Walk repo tree and return inventory rows."""
    repo_root = config["repository_root"]
    excluded_dirs = set(config.get("excluded_directories", []))
    excluded_files = config.get("excluded_files", [])

    rows = []

    for dirpath, dirnames, filenames in os.walk(repo_root, followlinks=False):
        # Normalise to forward-slash relative path
        rel_dir = normalize_path(dirpath, repo_root)

        # Determine if this directory itself is excluded
        dir_name = os.path.basename(dirpath)
        dir_excluded = is_excluded_dir(dir_name, excluded_dirs) if rel_dir != "." and rel_dir != "" else False

        # For the root directory, special handling
        if rel_dir == "." or rel_dir == "":
            parent_rel = ""
            rel_dir_clean = ""
        else:
            parent_rel = normalize_path(os.path.dirname(dirpath), repo_root)
            if parent_rel == ".":
                parent_rel = ""
            rel_dir_clean = rel_dir

        # Also check classification-based out_of_scope
        if rel_dir_clean:
            cls = classify_path(rel_dir_clean, "directory", classification_rules)
            dir_out_of_scope = cls["object_scope_class"] == "out_of_scope"
        else:
            dir_out_of_scope = False

        effective_excluded = dir_excluded or dir_out_of_scope

        # Emit directory row (skip root if assign_root_directory_id is false)
        if rel_dir_clean:
            cls = classify_path(rel_dir_clean, "directory", classification_rules)
            rows.append({
                "object_type": "directory",
                "relative_path": rel_dir_clean,
                "name": dir_name,
                "parent_relative_path": parent_rel,
                "extension": "",
                "exists_on_disk": True,
                "is_excluded": effective_excluded,
                "object_scope_class": cls["object_scope_class"],
                "candidate_semantic_role": "",
                "path_normalized": rel_dir_clean,
                "is_semantic_candidate": cls["is_semantic_candidate"],
                "inferred_module_hint": infer_module_hint(rel_dir_clean),
            })

        # Prune excluded directories from traversal
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs]

        # If this directory is excluded/out_of_scope, skip its files but we
        # already pruned subdirs above. Still emit file rows marked excluded.
        for fname in sorted(filenames):
            file_path = os.path.join(dirpath, fname)
            try:
                rel_file = normalize_path(file_path, repo_root)
            except ValueError:
                # Skip device files (e.g. NUL, CON on Windows)
                continue
            file_ext = os.path.splitext(fname)[1]  # includes leading dot
            file_excl = is_excluded_file(fname, excluded_files) or effective_excluded

            cls = classify_path(rel_file, "file", classification_rules)

            rows.append({
                "object_type": "file",
                "relative_path": rel_file,
                "name": fname,
                "parent_relative_path": rel_dir_clean,
                "extension": file_ext,
                "exists_on_disk": True,
                "is_excluded": file_excl,
                "object_scope_class": cls["object_scope_class"],
                "candidate_semantic_role": infer_semantic_role(fname, "file"),
                "path_normalized": rel_file,
                "is_semantic_candidate": cls["is_semantic_candidate"],
                "inferred_module_hint": infer_module_hint(rel_file),
            })

    return rows

def main():
    # Load configs
    config_path = CONFIG_DIR / "physical_id_config.json"
    rules_path = CONFIG_DIR / "file_classification_rules.json"

    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    if not rules_path.exists():
        print(f"ERROR: Classification rules not found: {rules_path}", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    classification_rules = load_classification_rules(rules_path)

    # Ensure output dir exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Scan
    print(f"Scanning repository: {config['repository_root']}")
    rows = scan_repository(config, classification_rules)

    # Write CSV
    output_path = OUTPUT_DIR / "physical_inventory_baseline.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    dirs = sum(1 for r in rows if r["object_type"] == "directory")
    files = sum(1 for r in rows if r["object_type"] == "file")
    excluded = sum(1 for r in rows if r["is_excluded"])
    print(f"Scan complete: {len(rows)} objects ({dirs} directories, {files} files)")
    print(f"Excluded: {excluded}")
    print(f"Output: {output_path}")

if __name__ == "__main__":
    main()

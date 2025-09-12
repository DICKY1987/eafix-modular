#!/usr/bin/env python3
import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


_line_comment_re = re.compile(r"//.*$")
_block_comment_re = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_json_comments(text: str) -> str:
    no_block = _block_comment_re.sub("", text)
    lines = [
        _line_comment_re.sub("", line) for line in no_block.splitlines(keepends=False)
    ]
    return "\n".join(lines)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = _strip_json_comments(raw)
        return json.loads(cleaned or "{}")


def dump_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def backup_dir(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.backup-{ts}")
    if path.exists():
        shutil.copytree(path, backup)
    return backup


def merge_list_by_key(dst_list: list, src_list: list, key: str) -> list:
    idx = {str(item.get(key)): i for i, item in enumerate(dst_list) if key in item}
    merged = list(dst_list)
    for item in src_list:
        k = item.get(key)
        if not k:
            # If no key, append if not exact duplicate
            if item not in merged:
                merged.append(item)
            continue
        sk = str(k)
        if sk in idx:
            # Keep destination version; skip source duplicate
            continue
        merged.append(item)
    return merged


def merge_tasks(src: dict, dst: dict) -> dict:
    out = dict(dst) if dst else {}
    out["version"] = dst.get("version") or src.get("version") or "2.0.0"
    # Merge top-level optional arrays
    for key in ("inputs", "problemMatcher", "options"):
        if key in src:
            if key not in out:
                out[key] = src[key]
            # If present in both, keep destination and ignore source
    # Merge tasks by label
    out["tasks"] = merge_list_by_key(dst.get("tasks", []), src.get("tasks", []), key="label")
    return out


def merge_launch(src: dict, dst: dict) -> dict:
    out = dict(dst) if dst else {}
    out["version"] = dst.get("version") or src.get("version") or "0.2.0"
    out["configurations"] = merge_list_by_key(
        dst.get("configurations", []), src.get("configurations", []), key="name"
    )
    # Optionally merge "compounds"
    if "compounds" in src:
        out["compounds"] = merge_list_by_key(
            dst.get("compounds", []), src.get("compounds", []), key="name"
        )
    return out


def merge_settings(src: dict, dst: dict) -> dict:
    # Destination wins; add missing keys from source
    out = dict(src)
    out.update(dst or {})
    return out


def copy_mode(src_path: Path, dst_path: Path):
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)


def main():
    parser = argparse.ArgumentParser(description="Merge or install VS Code configs from CODEX package")
    parser.add_argument(
        "--source",
        default=str(Path("CODEX_IMPLEMENTATION") / "vscode_configuration"),
        help="Source directory containing tasks.json, launch.json, settings.json",
    )
    parser.add_argument(
        "--dest",
        default=str(Path(".vscode")),
        help="Destination .vscode directory",
    )
    parser.add_argument(
        "--mode",
        choices=["merge", "copy"],
        default="merge",
        help="Merge into existing files (default) or overwrite by copy",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup destination .vscode directory before changes",
    )
    args = parser.parse_args()

    src_dir = Path(args.source)
    dst_dir = Path(args.dest)

    if args.backup:
        backup_dir(dst_dir)

    mapping = {
        "tasks.json": (merge_tasks if args.mode == "merge" else None),
        "launch.json": (merge_launch if args.mode == "merge" else None),
        "settings.json": (merge_settings if args.mode == "merge" else None),
    }

    for filename, merge_fn in mapping.items():
        src_path = src_dir / filename
        if not src_path.exists():
            continue
        dst_path = dst_dir / filename
        if args.mode == "copy" or not dst_path.exists():
            copy_mode(src_path, dst_path)
        else:
            src_data = load_json(src_path)
            dst_data = load_json(dst_path)
            if filename == "settings.json":
                merged = merge_settings(src_data, dst_data)
            elif filename == "tasks.json":
                merged = merge_tasks(src_data, dst_data)
            elif filename == "launch.json":
                merged = merge_launch(src_data, dst_data)
            else:
                merged = dst_data
            dump_json(dst_path, merged)

    print(f"VS Code configs processed in mode={args.mode}. Destination: {dst_dir}")


if __name__ == "__main__":
    main()

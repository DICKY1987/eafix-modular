from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "id_migration" / "config" / "physical_id_config.json"
DEFAULT_BASELINE_PATH = REPO_ROOT / "id_migration" / "output" / "physical_inventory_baseline.csv"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "id_migration" / "output" / "migration_manifest.jsonl"
DEFAULT_REGISTRY_PATH = REPO_ROOT / "id_migration" / "output" / "physical_id_registry.csv"
DEFAULT_COUNTER_STORE_PATH = REPO_ROOT / "COUNTER_STORE.json"

FILE_ID_PREFIX = "1"
DIRECTORY_ID_PREFIX = "2"
ID_WIDTH = 20
ALLOCATOR_VERSION = "ph02-allocator/1.0"
FILE_EVENT_TYPES = {"plan": "plan_file_rename", "apply": "apply_file_rename"}
DIRECTORY_EVENT_TYPES = {"plan": "plan_dir_id_create", "apply": "apply_dir_id_create"}
REGISTRY_COLUMNS = [
    "object_type",
    "file_id",
    "directory_id",
    "relative_path",
    "name",
    "parent_relative_path",
    "parent_directory_id",
    "extension",
    "id_source",
    "is_excluded",
    "exists_on_disk",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    temp_path.replace(path)


def repo_relative_to_path(relative_path: str) -> Path:
    if not relative_path:
        return REPO_ROOT
    return REPO_ROOT.joinpath(*relative_path.split("/"))


def load_baseline_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def validate_id_string(value: str, prefix: str) -> None:
    if len(value) != ID_WIDTH or not value.isdigit() or not value.startswith(prefix):
        raise ValueError(f"invalid {prefix}-prefixed ID: {value}")


def increment_id(value: str) -> str:
    validate_id_string(value, value[0])
    return str(int(value) + 1).zfill(ID_WIDTH)


def load_counter_store(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("COUNTER_STORE.json must contain a JSON object")
    counters = payload.get("counters")
    if not isinstance(counters, dict):
        raise ValueError("COUNTER_STORE.json missing counters object")
    for key, prefix in (("file_id", FILE_ID_PREFIX), ("directory_id", DIRECTORY_ID_PREFIX)):
        value = counters.get(key)
        if not isinstance(value, str):
            raise ValueError(f"COUNTER_STORE.json missing string counter for {key}")
        validate_id_string(value, prefix)
    return payload


def allocate_next_id(counter_store: dict[str, Any], counter_key: str, prefix: str) -> str:
    current = counter_store["counters"][counter_key]
    validate_id_string(current, prefix)
    next_value = increment_id(current)
    if not next_value.startswith(prefix):
        raise ValueError(f"{counter_key} exceeded available {prefix}-prefixed range")
    counter_store["counters"][counter_key] = next_value
    return current


def read_dir_id(anchor_path: Path) -> dict[str, Any]:
    payload = load_json(anchor_path)
    if not isinstance(payload, dict):
        raise ValueError(f"{anchor_path} must contain a JSON object")
    dir_id = payload.get("dir_id")
    if not isinstance(dir_id, str):
        raise ValueError(f"{anchor_path} missing dir_id")
    validate_id_string(dir_id, DIRECTORY_ID_PREFIX)
    return payload


def load_existing_file_assignments(manifest_path: Path, registry_path: Path) -> dict[str, dict[str, str]]:
    assignments: dict[str, dict[str, str]] = {}

    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("event_type") != "apply_file_rename":
                    continue
                relative_path = record.get("relative_path")
                file_id = record.get("file_id")
                if isinstance(relative_path, str) and isinstance(file_id, str) and file_id:
                    assignments[relative_path] = {
                        "file_id": file_id,
                        "status": str(record.get("status", "preserved")),
                    }

    if registry_path.is_file():
        with registry_path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                relative_path = row.get("relative_path", "")
                file_id = row.get("file_id", "")
                if relative_path and file_id and relative_path not in assignments:
                    assignments[relative_path] = {"file_id": file_id, "status": "preserved"}

    return assignments


def load_directory_event_statuses(manifest_path: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    if not manifest_path.is_file():
        return statuses

    with manifest_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("event_type") != "apply_dir_id_create":
                continue
            relative_path = record.get("relative_path")
            status = record.get("status")
            if isinstance(relative_path, str) and isinstance(status, str):
                statuses[relative_path] = status

    return statuses


def scan_existing_directory_ids(rows: list[dict[str, str]], anchor_name: str) -> dict[str, dict[str, str]]:
    existing: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["object_type"] != "directory" or as_bool(row["is_excluded"]):
            continue
        anchor_path = repo_relative_to_path(row["relative_path"]) / anchor_name
        if not anchor_path.is_file():
            continue
        payload = read_dir_id(anchor_path)
        existing[row["relative_path"]] = {"directory_id": payload["dir_id"], "status": "preserved"}
    return existing


def synchronize_counter_store(
    counter_store: dict[str, Any],
    existing_file_assignments: dict[str, dict[str, str]],
    existing_directory_ids: dict[str, dict[str, str]],
) -> None:
    max_file_id = max((info["file_id"] for info in existing_file_assignments.values()), default=None)
    max_directory_id = max((info["directory_id"] for info in existing_directory_ids.values()), default=None)

    if max_file_id is not None:
        required_next = increment_id(max_file_id)
        if counter_store["counters"]["file_id"] < required_next:
            counter_store["counters"]["file_id"] = required_next

    if max_directory_id is not None:
        required_next = increment_id(max_directory_id)
        if counter_store["counters"]["directory_id"] < required_next:
            counter_store["counters"]["directory_id"] = required_next


def build_assignment_plan(
    rows: list[dict[str, str]],
    config: dict[str, Any],
    counter_store: dict[str, Any],
    existing_file_assignments: dict[str, dict[str, str]],
    existing_directory_ids: dict[str, dict[str, str]],
) -> dict[str, Any]:
    anchor_name = config["directory_identity_mechanism"]["anchor_filename"]
    plan_counter_store = deepcopy(counter_store)
    synchronize_counter_store(plan_counter_store, existing_file_assignments, existing_directory_ids)

    directory_actions: list[dict[str, Any]] = []
    file_actions: list[dict[str, Any]] = []
    new_allocations = 0
    preserved_ids = 0

    directory_rows = sorted(
        (row for row in rows if row["object_type"] == "directory"),
        key=lambda row: row["relative_path"].casefold(),
    )
    file_rows = sorted(
        (row for row in rows if row["object_type"] == "file"),
        key=lambda row: row["relative_path"].casefold(),
    )

    for row in directory_rows:
        if as_bool(row["is_excluded"]):
            continue
        relative_path = row["relative_path"]
        anchor_path = repo_relative_to_path(relative_path) / anchor_name
        existing = existing_directory_ids.get(relative_path)
        if existing:
            directory_id = existing["directory_id"]
            status = "preserved"
            preserved_ids += 1
        else:
            directory_id = allocate_next_id(plan_counter_store, "directory_id", DIRECTORY_ID_PREFIX)
            status = "assigned"
            new_allocations += 1

        directory_actions.append(
            {
                "relative_path": relative_path,
                "anchor_path": anchor_path,
                "directory_id": directory_id,
                "status": status,
            }
        )

    for row in file_rows:
        if as_bool(row["is_excluded"]):
            continue
        relative_path = row["relative_path"]
        existing = existing_file_assignments.get(relative_path)
        if existing:
            file_id = existing["file_id"]
            status = "preserved"
            preserved_ids += 1
        else:
            file_id = allocate_next_id(plan_counter_store, "file_id", FILE_ID_PREFIX)
            status = "assigned"
            new_allocations += 1

        file_actions.append(
            {
                "relative_path": relative_path,
                "file_id": file_id,
                "status": status,
            }
        )

    return {
        "counter_store_after": plan_counter_store,
        "directories": directory_actions,
        "files": file_actions,
        "counts": {
            "directories_with_directory_id": len(directory_actions),
            "files_with_file_id": len(file_actions),
            "new_allocations": new_allocations,
            "preserved_ids": preserved_ids,
        },
    }


def make_manifest_events(
    mode: str,
    run_id: str,
    directory_actions: list[dict[str, Any]],
    file_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    emitted_at = utc_now()
    events: list[dict[str, Any]] = []

    for index, action in enumerate(directory_actions, start=1):
        events.append(
            {
                "run_id": run_id,
                "emitted_at_utc": emitted_at,
                "mode": mode,
                "sequence": index,
                "event_type": DIRECTORY_EVENT_TYPES[mode],
                "object_type": "directory",
                "relative_path": action["relative_path"],
                "directory_id": action["directory_id"],
                "status": action["status"],
                "anchor_filename": ".dir_id",
                "anchor_path": str(action["anchor_path"].relative_to(REPO_ROOT)).replace("\\", "/"),
            }
        )

    base_sequence = len(events)
    for index, action in enumerate(file_actions, start=1):
        events.append(
            {
                "run_id": run_id,
                "emitted_at_utc": emitted_at,
                "mode": mode,
                "sequence": base_sequence + index,
                "event_type": FILE_EVENT_TYPES[mode],
                "object_type": "file",
                "relative_path": action["relative_path"],
                "new_relative_path": action["relative_path"],
                "file_id": action["file_id"],
                "status": action["status"],
                "rename_required": False,
                "note": "registry_assigned_no_filename_change",
            }
        )

    return events


def write_dir_anchor(anchor_path: Path, directory_id: str, relative_path: str, project_root_id: str | None) -> None:
    payload = {
        "dir_id": directory_id,
        "allocated_at_utc": utc_now(),
        "allocator_version": ALLOCATOR_VERSION,
        "project_root_id": project_root_id,
        "relative_path": relative_path,
    }
    anchor_path.parent.mkdir(parents=True, exist_ok=True)
    with anchor_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def run_plan(
    plan: dict[str, Any],
    manifest_path: Path,
) -> None:
    run_id = f"plan_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    events = make_manifest_events("plan", run_id, plan["directories"], plan["files"])
    append_jsonl(manifest_path, events)
    print(json.dumps(plan["counts"], indent=2))
    print(f"Manifest appended: {manifest_path}")


def run_apply(
    plan: dict[str, Any],
    counter_store_path: Path,
    manifest_path: Path,
    assign_root_directory_id: bool,
) -> None:
    counter_store_after = plan["counter_store_after"]
    counters_changed = plan["counts"]["new_allocations"] > 0
    if counters_changed:
        counter_store_after["last_updated_utc"] = utc_now()
        write_json_atomic(counter_store_path, counter_store_after)

    project_root_id = None if not assign_root_directory_id else counter_store_after["counters"]["directory_id"]
    for action in plan["directories"]:
        if action["status"] != "assigned":
            continue
        write_dir_anchor(action["anchor_path"], action["directory_id"], action["relative_path"], project_root_id)

    run_id = f"apply_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    events = make_manifest_events("apply", run_id, plan["directories"], plan["files"])
    append_jsonl(manifest_path, events)

    print(json.dumps(plan["counts"], indent=2))
    if counters_changed:
        print(f"Updated counter store: {counter_store_path}")
    print(f"Manifest appended: {manifest_path}")


def derive_registry(
    rows: list[dict[str, str]],
    config: dict[str, Any],
    manifest_path: Path,
    registry_path: Path,
) -> dict[str, int]:
    anchor_name = config["directory_identity_mechanism"]["anchor_filename"]
    existing_file_assignments = load_existing_file_assignments(manifest_path, registry_path)
    directory_state = scan_existing_directory_ids(rows, anchor_name)
    directory_statuses = load_directory_event_statuses(manifest_path)

    registry_rows: list[dict[str, Any]] = []
    missing_paths: list[str] = []

    for row in rows:
        is_excluded = as_bool(row["is_excluded"])
        exists_on_disk = as_bool(row["exists_on_disk"])
        relative_path = row["relative_path"]
        parent_relative_path = row["parent_relative_path"]
        parent_directory_id = ""
        if parent_relative_path:
            parent_directory_id = directory_state.get(parent_relative_path, {}).get("directory_id", "")

        record = {
            "object_type": row["object_type"],
            "file_id": "",
            "directory_id": "",
            "relative_path": relative_path,
            "name": row["name"],
            "parent_relative_path": parent_relative_path,
            "parent_directory_id": parent_directory_id,
            "extension": row["extension"] if row["object_type"] == "file" else "",
            "id_source": "preserved",
            "is_excluded": is_excluded,
            "exists_on_disk": exists_on_disk,
        }

        if row["object_type"] == "directory":
            if not is_excluded:
                directory_id = directory_state.get(relative_path, {}).get("directory_id", "")
                if not directory_id:
                    missing_paths.append(relative_path)
                record["directory_id"] = directory_id
                status = directory_statuses.get(relative_path, "preserved")
                record["id_source"] = "COUNTER_STORE" if status == "assigned" else "preserved"
        else:
            if not is_excluded:
                file_assignment = existing_file_assignments.get(relative_path)
                if not file_assignment:
                    missing_paths.append(relative_path)
                else:
                    record["file_id"] = file_assignment["file_id"]
                    record["id_source"] = "COUNTER_STORE" if file_assignment["status"] == "assigned" else "preserved"

        registry_rows.append(record)

    if missing_paths:
        sample = ", ".join(missing_paths[:10])
        raise RuntimeError(f"missing physical IDs for {len(missing_paths)} baseline rows: {sample}")

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_COLUMNS)
        writer.writeheader()
        writer.writerows(registry_rows)

    counts = {
        "files_with_file_id": sum(1 for row in registry_rows if row["object_type"] == "file" and row["file_id"]),
        "directories_with_directory_id": sum(
            1 for row in registry_rows if row["object_type"] == "directory" and row["directory_id"]
        ),
        "total_rows": len(registry_rows),
    }
    print(json.dumps(counts, indent=2))
    print(f"Registry written: {registry_path}")
    return counts


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PH-02 physical ID assignment and registry derivation")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to physical_id_config.json")
    parser.add_argument("--mode", choices=["plan", "apply", "derive-registry"], help="Execution mode")
    parser.add_argument(
        "--derive-registry",
        action="store_true",
        help="Alias for --mode derive-registry",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    mode = "derive-registry" if args.derive_registry else args.mode
    if mode is None:
        print("ERROR: specify --mode {plan,apply,derive-registry} or --derive-registry", file=sys.stderr)
        return 2

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (REPO_ROOT / config_path).resolve()

    if not config_path.is_file():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        return 2
    if not DEFAULT_BASELINE_PATH.is_file():
        print(f"ERROR: baseline CSV not found: {DEFAULT_BASELINE_PATH}", file=sys.stderr)
        return 2
    if not DEFAULT_COUNTER_STORE_PATH.is_file():
        print(f"ERROR: counter store not found: {DEFAULT_COUNTER_STORE_PATH}", file=sys.stderr)
        return 2

    config = load_json(config_path)
    rows = load_baseline_rows(DEFAULT_BASELINE_PATH)

    if mode == "derive-registry":
        try:
            derive_registry(rows, config, DEFAULT_MANIFEST_PATH, DEFAULT_REGISTRY_PATH)
        except Exception as exc:  # pragma: no cover - command-line path
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        return 0

    try:
        counter_store = load_counter_store(DEFAULT_COUNTER_STORE_PATH)
        existing_file_assignments = load_existing_file_assignments(DEFAULT_MANIFEST_PATH, DEFAULT_REGISTRY_PATH)
        existing_directory_ids = scan_existing_directory_ids(
            rows,
            config["directory_identity_mechanism"]["anchor_filename"],
        )
        plan = build_assignment_plan(rows, config, counter_store, existing_file_assignments, existing_directory_ids)
        if mode == "plan":
            run_plan(plan, DEFAULT_MANIFEST_PATH)
        else:
            run_apply(plan, DEFAULT_COUNTER_STORE_PATH, DEFAULT_MANIFEST_PATH, config["assign_root_directory_id"])
    except Exception as exc:  # pragma: no cover - command-line path
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

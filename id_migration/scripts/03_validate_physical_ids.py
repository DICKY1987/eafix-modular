from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "id_migration" / "config" / "physical_id_config.json"
DEFAULT_REGISTRY_PATH = REPO_ROOT / "id_migration" / "output" / "physical_id_registry.csv"
DEFAULT_REPORT_PATH = REPO_ROOT / "id_migration" / "output" / "physical_validation_report.json"
DEFAULT_DIR_SCHEMA_PATH = REPO_ROOT / "id_migration" / "schemas" / "dir_id.schema.json"
DEFAULT_CLASSIFICATION_RULES_PATH = REPO_ROOT / "id_migration" / "config" / "file_classification_rules.json"

EXPECTED_REGISTRY_COLUMNS = [
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
VALID_OBJECT_TYPES = {"file", "directory"}
VALID_ID_SOURCES = {"COUNTER_STORE", "preserved"}
FILE_ID_PATTERN = re.compile(r"^1\d{19}$")
DIRECTORY_ID_PATTERN = re.compile(r"^2\d{19}$")
PATH_PATTERN = re.compile(r"^(?![\\/])(?!.*\\)(?!.*//).+[^/]$")
NAME_PATTERN = re.compile(r"^[^\\/]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def normalize_relative_path(path_value: str) -> str:
    value = str(path_value).replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    value = re.sub(r"/+", "/", value)
    value = value.rstrip("/")
    if value in {"", "."}:
        return ""

    parts: list[str] = []
    for segment in value.split("/"):
        if segment in {"", "."}:
            continue
        if segment == "..":
            if parts:
                parts.pop()
            continue
        parts.append(segment)
    return "/".join(parts)


def normalize_absolute_path(path: Path, repo_root: Path) -> str:
    return normalize_relative_path(os.path.relpath(path, repo_root))


def path_key(path_value: str) -> str:
    normalized = normalize_relative_path(path_value)
    return normalized.casefold() if os.name == "nt" else normalized


def parse_bool(value: str, *, field: str, line_number: int, errors: list[dict[str, Any]]) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    errors.append(
        issue(
            "INVALID_BOOLEAN",
            f"{field} must be True or False, got {value!r}",
            line_number=line_number,
            field=field,
        )
    )
    return False


def parse_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def issue(
    code: str,
    message: str,
    *,
    line_number: int | None = None,
    relative_path: str | None = None,
    field: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if line_number is not None:
        payload["line_number"] = line_number
    if relative_path is not None:
        payload["relative_path"] = relative_path
    if field is not None:
        payload["field"] = field
    return payload


def load_classification_rules(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"classification rules must be a JSON object: {path}")
    return payload


def classify_path(rel_path: str, object_type: str, rules_data: dict[str, Any]) -> dict[str, Any]:
    default_class = rules_data.get("default_scope_class", "module_owned")
    classifications = rules_data.get("classifications", {})
    rules = rules_data.get("rules", [])

    scope_class = default_class
    match_path = rel_path.replace("\\", "/")
    match_path_for_rules = f"{match_path}/" if object_type == "directory" and not match_path.endswith("/") else match_path

    for rule in rules:
        match_type = rule.get("match_type")
        values = rule.get("values", [])
        matched = False
        if match_type == "path_prefix":
            matched = any(match_path_for_rules.startswith(value) or match_path.startswith(value) for value in values)
        elif match_type == "path_contains":
            matched = any(value in match_path_for_rules or value in match_path for value in values)
        if matched:
            scope_class = str(rule.get("scope_class", scope_class))
            break

    return classifications.get(scope_class, {"object_scope_class": scope_class}) | {"object_scope_class": scope_class}


def discover_governed_directories(
    repo_root: Path,
    config: dict[str, Any],
    classification_rules: dict[str, Any],
) -> set[str]:
    excluded_dirs = set(config.get("excluded_directories", []))
    governed_dirs: set[str] = set()

    for dirpath, dirnames, _filenames in os.walk(repo_root, followlinks=False):
        dir_path = Path(dirpath)
        rel_dir = normalize_absolute_path(dir_path, repo_root)
        dir_name = dir_path.name

        if rel_dir:
            dir_excluded = dir_name in excluded_dirs
            dir_scope = classify_path(rel_dir, "directory", classification_rules).get("object_scope_class")
            if not dir_excluded and dir_scope != "out_of_scope":
                governed_dirs.add(rel_dir)

        dirnames[:] = [name for name in dirnames if name not in excluded_dirs]

    return governed_dirs


def validate_dir_anchor_payload(
    payload: Any,
    *,
    expected_relative_path: str,
    schema: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []

    if schema is not None:
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            schema = None
        else:
            validator = Draft202012Validator(schema)
            errors.extend(error.message for error in validator.iter_errors(payload))

    if not isinstance(payload, dict):
        return errors + ["anchor payload must be a JSON object"]

    required_keys = {
        "dir_id",
        "allocated_at_utc",
        "allocator_version",
        "project_root_id",
        "relative_path",
    }
    if set(payload) != required_keys:
        missing = sorted(required_keys - set(payload))
        extra = sorted(set(payload) - required_keys)
        if missing:
            errors.append(f"missing keys: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected keys: {', '.join(extra)}")

    dir_id = payload.get("dir_id")
    if not isinstance(dir_id, str) or not DIRECTORY_ID_PATTERN.fullmatch(dir_id):
        errors.append("dir_id must match ^2\\d{19}$")

    allocated_at = payload.get("allocated_at_utc")
    if not parse_datetime(allocated_at):
        errors.append("allocated_at_utc must be an ISO-8601 datetime")

    allocator_version = payload.get("allocator_version")
    if not isinstance(allocator_version, str) or not allocator_version.strip():
        errors.append("allocator_version must be a non-empty string")

    project_root_id = payload.get("project_root_id")
    if project_root_id is not None and (
        not isinstance(project_root_id, str) or not DIRECTORY_ID_PATTERN.fullmatch(project_root_id)
    ):
        errors.append("project_root_id must be null or match ^2\\d{19}$")

    relative_path = payload.get("relative_path")
    if not isinstance(relative_path, str) or not relative_path:
        errors.append("relative_path must be a non-empty string")
    else:
        normalized = normalize_relative_path(relative_path)
        if normalized != relative_path:
            errors.append("relative_path must already be normalized")
        if not PATH_PATTERN.fullmatch(relative_path):
            errors.append("relative_path does not satisfy the path normalization contract")
        if relative_path != expected_relative_path:
            errors.append(
                f"relative_path {relative_path!r} does not match anchor location {expected_relative_path!r}"
            )

    return errors


def load_registry_rows(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    typed_rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if fieldnames != EXPECTED_REGISTRY_COLUMNS:
            errors.append(
                issue(
                    "INVALID_HEADER",
                    f"registry header must be exactly {EXPECTED_REGISTRY_COLUMNS}, got {fieldnames}",
                )
            )

        for line_number, raw_row in enumerate(reader, start=2):
            if None in raw_row:
                errors.append(issue("ROW_SHAPE_ERROR", "row has extra columns", line_number=line_number))
                continue

            row = {column: raw_row.get(column, "") for column in EXPECTED_REGISTRY_COLUMNS}
            object_type = row["object_type"]
            relative_path = row["relative_path"]
            parent_relative_path = row["parent_relative_path"]
            file_id = row["file_id"]
            directory_id = row["directory_id"]
            parent_directory_id = row["parent_directory_id"]

            is_excluded = parse_bool(row["is_excluded"], field="is_excluded", line_number=line_number, errors=errors)
            exists_on_disk = parse_bool(
                row["exists_on_disk"],
                field="exists_on_disk",
                line_number=line_number,
                errors=errors,
            )

            if object_type not in VALID_OBJECT_TYPES:
                errors.append(
                    issue(
                        "INVALID_OBJECT_TYPE",
                        f"object_type must be one of {sorted(VALID_OBJECT_TYPES)}, got {object_type!r}",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="object_type",
                    )
                )

            normalized_relative_path = normalize_relative_path(relative_path)
            if normalized_relative_path != relative_path:
                errors.append(
                    issue(
                        "NON_NORMALIZED_PATH",
                        "relative_path must already be normalized",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="relative_path",
                    )
                )
            elif relative_path and not PATH_PATTERN.fullmatch(relative_path):
                errors.append(
                    issue(
                        "INVALID_RELATIVE_PATH",
                        "relative_path does not satisfy the path normalization contract",
                        line_number=line_number,
                        relative_path=relative_path,
                        field="relative_path",
                    )
                )

            normalized_parent_path = normalize_relative_path(parent_relative_path)
            if normalized_parent_path != parent_relative_path:
                errors.append(
                    issue(
                        "NON_NORMALIZED_PARENT_PATH",
                        "parent_relative_path must already be normalized",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="parent_relative_path",
                    )
                )
            elif parent_relative_path and not PATH_PATTERN.fullmatch(parent_relative_path):
                errors.append(
                    issue(
                        "INVALID_PARENT_PATH",
                        "parent_relative_path does not satisfy the path normalization contract",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="parent_relative_path",
                    )
                )

            if not relative_path:
                errors.append(issue("MISSING_RELATIVE_PATH", "relative_path must be non-empty", line_number=line_number))

            name = row["name"]
            expected_name = PurePosixPath(relative_path).name if relative_path else ""
            if not name:
                errors.append(issue("MISSING_NAME", "name must be non-empty", line_number=line_number))
            elif not NAME_PATTERN.fullmatch(name):
                errors.append(
                    issue(
                        "INVALID_NAME",
                        "name must be a basename with no path separators",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="name",
                    )
                )
            elif expected_name and name != expected_name:
                errors.append(
                    issue(
                        "NAME_PATH_MISMATCH",
                        f"name {name!r} does not match basename {expected_name!r}",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="name",
                    )
                )

            expected_parent = str(PurePosixPath(relative_path).parent) if relative_path else ""
            if expected_parent == ".":
                expected_parent = ""
            if relative_path and parent_relative_path != expected_parent:
                errors.append(
                    issue(
                        "PARENT_PATH_MISMATCH",
                        f"parent_relative_path {parent_relative_path!r} does not match derived parent {expected_parent!r}",
                        line_number=line_number,
                        relative_path=relative_path,
                        field="parent_relative_path",
                    )
                )

            if parent_directory_id and not DIRECTORY_ID_PATTERN.fullmatch(parent_directory_id):
                errors.append(
                    issue(
                        "INVALID_PARENT_DIRECTORY_ID",
                        "parent_directory_id must be empty or match ^2\\d{19}$",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="parent_directory_id",
                    )
                )

            if file_id and not FILE_ID_PATTERN.fullmatch(file_id):
                errors.append(
                    issue(
                        "INVALID_FILE_ID",
                        "file_id must be empty or match ^1\\d{19}$",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="file_id",
                    )
                )

            if directory_id and not DIRECTORY_ID_PATTERN.fullmatch(directory_id):
                errors.append(
                    issue(
                        "INVALID_DIRECTORY_ID",
                        "directory_id must be empty or match ^2\\d{19}$",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="directory_id",
                    )
                )

            if row["id_source"] not in VALID_ID_SOURCES:
                errors.append(
                    issue(
                        "INVALID_ID_SOURCE",
                        f"id_source must be one of {sorted(VALID_ID_SOURCES)}, got {row['id_source']!r}",
                        line_number=line_number,
                        relative_path=relative_path or None,
                        field="id_source",
                    )
                )

            has_file_id = bool(file_id)
            has_directory_id = bool(directory_id)
            if has_file_id and has_directory_id:
                errors.append(
                    issue(
                        "AMBIGUOUS_ROW_ID",
                        "row may not contain both file_id and directory_id",
                        line_number=line_number,
                        relative_path=relative_path or None,
                    )
                )

            expected_extension = PurePosixPath(name).suffix if name else ""
            if object_type == "file":
                if has_directory_id:
                    errors.append(
                        issue(
                            "FILE_ROW_HAS_DIRECTORY_ID",
                            "file rows must leave directory_id empty",
                            line_number=line_number,
                            relative_path=relative_path or None,
                        )
                    )
                if not is_excluded and not has_file_id:
                    errors.append(
                        issue(
                            "NON_EXCLUDED_FILE_MISSING_ID",
                            "non-excluded file row must have a file_id",
                            line_number=line_number,
                            relative_path=relative_path or None,
                        )
                    )
                if row["extension"] != expected_extension:
                    errors.append(
                        issue(
                            "EXTENSION_MISMATCH",
                            f"extension {row['extension']!r} does not match derived extension {expected_extension!r}",
                            line_number=line_number,
                            relative_path=relative_path or None,
                            field="extension",
                        )
                    )
            elif object_type == "directory":
                if has_file_id:
                    errors.append(
                        issue(
                            "DIRECTORY_ROW_HAS_FILE_ID",
                            "directory rows must leave file_id empty",
                            line_number=line_number,
                            relative_path=relative_path or None,
                        )
                    )
                if not is_excluded and not has_directory_id:
                    errors.append(
                        issue(
                            "NON_EXCLUDED_DIRECTORY_MISSING_ID",
                            "non-excluded directory row must have a directory_id",
                            line_number=line_number,
                            relative_path=relative_path or None,
                        )
                    )
                if row["extension"]:
                    errors.append(
                        issue(
                            "DIRECTORY_EXTENSION_NOT_EMPTY",
                            "directory rows must leave extension empty",
                            line_number=line_number,
                            relative_path=relative_path or None,
                            field="extension",
                        )
                    )

            if not is_excluded and not (has_file_id ^ has_directory_id):
                errors.append(
                    issue(
                        "NON_EXCLUDED_ROW_ID_CARDINALITY",
                        "non-excluded rows must have exactly one non-empty ID field",
                        line_number=line_number,
                        relative_path=relative_path or None,
                    )
                )

            if is_excluded and not (has_file_id or has_directory_id):
                warnings.append(
                    issue(
                        "EXCLUDED_ROW_WITHOUT_ID",
                        "excluded row carries no physical ID",
                        line_number=line_number,
                        relative_path=relative_path or None,
                    )
                )

            typed_rows.append(
                {
                    **row,
                    "line_number": line_number,
                    "is_excluded": is_excluded,
                    "exists_on_disk": exists_on_disk,
                }
            )

    return typed_rows, errors, warnings


def validate_registry_integrity(rows: list[dict[str, Any]], repo_root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    rows_by_path: dict[str, dict[str, Any]] = {}
    directory_rows_by_path: dict[str, dict[str, Any]] = {}
    file_ids: dict[str, dict[str, Any]] = {}
    directory_ids: dict[str, dict[str, Any]] = {}

    for row in rows:
        relative_path = str(row["relative_path"])
        key = path_key(relative_path)
        existing_path_row = rows_by_path.get(key)
        if existing_path_row is not None:
            errors.append(
                issue(
                    "DUPLICATE_RELATIVE_PATH",
                    f"relative_path duplicates line {existing_path_row['line_number']}",
                    line_number=row["line_number"],
                    relative_path=relative_path,
                )
            )
        else:
            rows_by_path[key] = row

        if row["object_type"] == "directory":
            directory_rows_by_path[key] = row

        file_id = str(row["file_id"])
        if file_id:
            existing = file_ids.get(file_id)
            if existing is not None:
                errors.append(
                    issue(
                        "DUPLICATE_FILE_ID",
                        f"file_id duplicates line {existing['line_number']}",
                        line_number=row["line_number"],
                        relative_path=relative_path,
                        field="file_id",
                    )
                )
            else:
                file_ids[file_id] = row

        directory_id = str(row["directory_id"])
        if directory_id:
            existing = directory_ids.get(directory_id)
            if existing is not None:
                errors.append(
                    issue(
                        "DUPLICATE_DIRECTORY_ID",
                        f"directory_id duplicates line {existing['line_number']}",
                        line_number=row["line_number"],
                        relative_path=relative_path,
                        field="directory_id",
                    )
                )
            else:
                directory_ids[directory_id] = row

        path_on_disk = repo_root.joinpath(*relative_path.split("/"))
        exists_on_disk = bool(row["exists_on_disk"])
        if exists_on_disk:
            if row["object_type"] == "file" and not path_on_disk.is_file():
                errors.append(
                    issue(
                        "FILE_MISSING_ON_DISK",
                        "row declares exists_on_disk=True but file is missing",
                        line_number=row["line_number"],
                        relative_path=relative_path,
                    )
                )
            if row["object_type"] == "directory" and not path_on_disk.is_dir():
                errors.append(
                    issue(
                        "DIRECTORY_MISSING_ON_DISK",
                        "row declares exists_on_disk=True but directory is missing",
                        line_number=row["line_number"],
                        relative_path=relative_path,
                    )
                )
        elif path_on_disk.exists():
            errors.append(
                issue(
                    "EXISTS_ON_DISK_MISMATCH",
                    "row declares exists_on_disk=False but path exists",
                    line_number=row["line_number"],
                    relative_path=relative_path,
                )
            )

    for row in rows:
        relative_path = str(row["relative_path"])
        parent_relative_path = str(row["parent_relative_path"])
        parent_directory_id = str(row["parent_directory_id"])
        if not parent_relative_path:
            if parent_directory_id:
                errors.append(
                    issue(
                        "ROOT_ROW_HAS_PARENT_ID",
                        "root-level rows must leave parent_directory_id empty",
                        line_number=row["line_number"],
                        relative_path=relative_path,
                        field="parent_directory_id",
                    )
                )
            continue

        parent_row = directory_rows_by_path.get(path_key(parent_relative_path))
        if parent_row is None:
            errors.append(
                issue(
                    "MISSING_PARENT_ROW",
                    "parent_relative_path does not resolve to a directory row",
                    line_number=row["line_number"],
                    relative_path=relative_path,
                    field="parent_relative_path",
                )
            )
            continue

        expected_parent_id = str(parent_row["directory_id"])
        if not expected_parent_id:
            errors.append(
                issue(
                    "PARENT_ROW_MISSING_DIRECTORY_ID",
                    "parent directory row has no directory_id",
                    line_number=row["line_number"],
                    relative_path=relative_path,
                    field="parent_directory_id",
                )
            )
        elif parent_directory_id != expected_parent_id:
            errors.append(
                issue(
                    "PARENT_DIRECTORY_ID_MISMATCH",
                    f"parent_directory_id {parent_directory_id!r} does not match parent row directory_id {expected_parent_id!r}",
                    line_number=row["line_number"],
                    relative_path=relative_path,
                    field="parent_directory_id",
                )
            )

    return errors


def validate_anchors_and_directories(
    *,
    repo_root: Path,
    config: dict[str, Any],
    classification_rules: dict[str, Any],
    dir_schema: dict[str, Any] | None,
    registry_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    errors: list[dict[str, Any]] = []
    anchor_name = str(config["directory_identity_mechanism"]["anchor_filename"])
    governed_dirs = discover_governed_directories(repo_root, config, classification_rules)

    registry_directory_rows = {
        path_key(str(row["relative_path"])): row
        for row in registry_rows
        if row["object_type"] == "directory"
    }
    anchors_seen: dict[str, Path] = {}
    anchor_count = 0

    for anchor_path in repo_root.rglob(anchor_name):
        if not anchor_path.is_file():
            continue
        anchor_count += 1
        relative_dir = normalize_absolute_path(anchor_path.parent, repo_root)
        relative_dir_key = path_key(relative_dir)

        previous_anchor = anchors_seen.get(relative_dir_key)
        if previous_anchor is not None:
            errors.append(
                issue(
                    "MULTIPLE_ANCHORS_FOR_DIRECTORY",
                    f"directory already had anchor at {previous_anchor}",
                    relative_path=relative_dir or None,
                )
            )
            continue
        anchors_seen[relative_dir_key] = anchor_path

        try:
            payload = load_json(anchor_path)
        except json.JSONDecodeError as exc:
            errors.append(
                issue(
                    "INVALID_ANCHOR_JSON",
                    f"anchor is not valid JSON: {exc}",
                    relative_path=relative_dir or None,
                )
            )
            continue

        anchor_errors = validate_dir_anchor_payload(
            payload,
            expected_relative_path=relative_dir,
            schema=dir_schema,
        )
        for message in anchor_errors:
            errors.append(
                issue(
                    "INVALID_DIR_ANCHOR",
                    message,
                    relative_path=relative_dir or None,
                )
            )

        registry_row = registry_directory_rows.get(relative_dir_key)
        if registry_row is None:
            errors.append(
                issue(
                    "ORPHAN_DIR_ANCHOR",
                    "anchor exists on disk but no directory row exists in physical_id_registry.csv",
                    relative_path=relative_dir or None,
                )
            )
            continue

        payload_dir_id = payload.get("dir_id") if isinstance(payload, dict) else None
        registry_dir_id = str(registry_row["directory_id"])
        if payload_dir_id != registry_dir_id:
            errors.append(
                issue(
                    "ANCHOR_DIRECTORY_ID_MISMATCH",
                    f"anchor dir_id {payload_dir_id!r} does not match registry directory_id {registry_dir_id!r}",
                    line_number=registry_row["line_number"],
                    relative_path=relative_dir or None,
                )
            )

    for relative_dir in sorted(governed_dirs, key=str.casefold):
        directory_path = repo_root.joinpath(*relative_dir.split("/"))
        anchor_path = directory_path / anchor_name
        if not anchor_path.is_file():
            errors.append(
                issue(
                    "MISSING_DIR_ANCHOR",
                    "governed directory is missing .dir_id anchor",
                    relative_path=relative_dir,
                )
            )

        registry_row = registry_directory_rows.get(path_key(relative_dir))
        if registry_row is None:
            errors.append(
                issue(
                    "MISSING_DIRECTORY_REGISTRY_ROW",
                    "governed directory is missing from physical_id_registry.csv",
                    relative_path=relative_dir,
                )
            )
        elif registry_row["is_excluded"]:
            errors.append(
                issue(
                    "GOVERNED_DIRECTORY_MARKED_EXCLUDED",
                    "governed directory row is unexpectedly marked excluded",
                    line_number=registry_row["line_number"],
                    relative_path=relative_dir,
                )
            )

    for registry_row in registry_directory_rows.values():
        relative_dir = str(registry_row["relative_path"])
        if not registry_row["is_excluded"] and registry_row["exists_on_disk"] and relative_dir not in governed_dirs:
            errors.append(
                issue(
                    "REGISTRY_DIRECTORY_NOT_GOVERNED",
                    "directory row exists on disk but was not discovered as a governed directory",
                    line_number=registry_row["line_number"],
                    relative_path=relative_dir,
                )
            )

    return errors, {
        "governed_directories_on_disk": len(governed_dirs),
        "anchors_on_disk": anchor_count,
    }


def build_report(
    *,
    errors: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    registry_rows: list[dict[str, Any]],
    directory_metrics: dict[str, int],
    config_path: Path,
    registry_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    non_excluded_rows = sum(1 for row in registry_rows if not row["is_excluded"])
    file_rows = sum(1 for row in registry_rows if row["object_type"] == "file")
    directory_rows = sum(1 for row in registry_rows if row["object_type"] == "directory")
    physical_status = "PASS" if not errors else "FAIL"

    return {
        "gate": "G-02",
        "validated_at_utc": utc_now(),
        "physical_status": physical_status,
        "inputs": {
            "config": str(config_path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "registry": str(registry_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        },
        "output": str(report_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "summary": {
            "registry_rows": len(registry_rows),
            "registry_file_rows": file_rows,
            "registry_directory_rows": directory_rows,
            "non_excluded_rows": non_excluded_rows,
            "excluded_rows": len(registry_rows) - non_excluded_rows,
            **directory_metrics,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "checks": {
            "registry_has_exact_11_columns": not any(error["code"] == "INVALID_HEADER" for error in errors),
            "non_excluded_rows_have_physical_ids": not any(
                error["code"]
                in {
                    "NON_EXCLUDED_FILE_MISSING_ID",
                    "NON_EXCLUDED_DIRECTORY_MISSING_ID",
                    "NON_EXCLUDED_ROW_ID_CARDINALITY",
                }
                for error in errors
            ),
            "parent_linkage_valid": not any(
                error["code"]
                in {
                    "MISSING_PARENT_ROW",
                    "PARENT_ROW_MISSING_DIRECTORY_ID",
                    "PARENT_DIRECTORY_ID_MISMATCH",
                    "ROOT_ROW_HAS_PARENT_ID",
                }
                for error in errors
            ),
            "no_duplicate_ids": not any(
                error["code"] in {"DUPLICATE_FILE_ID", "DUPLICATE_DIRECTORY_ID"} for error in errors
            ),
            "no_orphan_dir_anchors": not any(
                error["code"] in {"ORPHAN_DIR_ANCHOR", "MISSING_DIR_ANCHOR"} for error in errors
            ),
            "registry_paths_match_filesystem": not any(
                error["code"]
                in {
                    "FILE_MISSING_ON_DISK",
                    "DIRECTORY_MISSING_ON_DISK",
                    "EXISTS_ON_DISK_MISMATCH",
                    "REGISTRY_DIRECTORY_NOT_GOVERNED",
                }
                for error in errors
            ),
        },
        "errors": errors,
        "warnings": warnings,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PH-03 physical identity validator")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to physical_id_config.json")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (REPO_ROOT / config_path).resolve()

    if not config_path.is_file():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        return 2
    if not DEFAULT_REGISTRY_PATH.is_file():
        print(f"ERROR: registry not found: {DEFAULT_REGISTRY_PATH}", file=sys.stderr)
        return 2
    if not DEFAULT_DIR_SCHEMA_PATH.is_file():
        print(f"ERROR: dir_id schema not found: {DEFAULT_DIR_SCHEMA_PATH}", file=sys.stderr)
        return 2
    if not DEFAULT_CLASSIFICATION_RULES_PATH.is_file():
        print(f"ERROR: classification rules not found: {DEFAULT_CLASSIFICATION_RULES_PATH}", file=sys.stderr)
        return 2

    try:
        config = load_json(config_path)
        if not isinstance(config, dict):
            raise ValueError("config root must be a JSON object")
        dir_schema = load_json(DEFAULT_DIR_SCHEMA_PATH)
        classification_rules = load_classification_rules(DEFAULT_CLASSIFICATION_RULES_PATH)
        registry_rows, registry_errors, registry_warnings = load_registry_rows(DEFAULT_REGISTRY_PATH)
        integrity_errors = validate_registry_integrity(registry_rows, REPO_ROOT)
        anchor_errors, directory_metrics = validate_anchors_and_directories(
            repo_root=REPO_ROOT,
            config=config,
            classification_rules=classification_rules,
            dir_schema=dir_schema if isinstance(dir_schema, dict) else None,
            registry_rows=registry_rows,
        )
    except Exception as exc:  # pragma: no cover - command-line path
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors = [*registry_errors, *integrity_errors, *anchor_errors]
    warnings = registry_warnings
    report = build_report(
        errors=errors,
        warnings=warnings,
        registry_rows=registry_rows,
        directory_metrics=directory_metrics,
        config_path=config_path,
        registry_path=DEFAULT_REGISTRY_PATH,
        report_path=DEFAULT_REPORT_PATH,
    )
    write_json(DEFAULT_REPORT_PATH, report)

    print("=" * 60)
    print("G-02 Gate: Physical Identity Validation")
    print("=" * 60)
    print(f"Registry rows:        {report['summary']['registry_rows']}")
    print(f"Directory rows:       {report['summary']['registry_directory_rows']}")
    print(f"File rows:            {report['summary']['registry_file_rows']}")
    print(f"Governed directories: {report['summary']['governed_directories_on_disk']}")
    print(f"Anchors on disk:      {report['summary']['anchors_on_disk']}")
    print(f"Warnings:             {report['summary']['warning_count']}")
    print(f"Errors:               {report['summary']['error_count']}")
    print(f"Report:               {DEFAULT_REPORT_PATH}")
    print("=" * 60)

    if errors:
        print("\nRESULT: FAIL")
        for item in errors[:10]:
            location = ""
            if "line_number" in item:
                location += f" line {item['line_number']}"
            if "relative_path" in item:
                location += f" [{item['relative_path']}]"
            print(f"- {item['code']}{location}: {item['message']}")
        if len(errors) > 10:
            print(f"... {len(errors) - 10} additional errors in report")
        return 1

    print("\nRESULT: PASS")
    if warnings:
        print("Warnings:")
        for item in warnings[:10]:
            location = ""
            if "line_number" in item:
                location += f" line {item['line_number']}"
            if "relative_path" in item:
                location += f" [{item['relative_path']}]"
            print(f"- {item['code']}{location}: {item['message']}")
        if len(warnings) > 10:
            print(f"... {len(warnings) - 10} additional warnings in report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_FILE_PATTERN = r"^1\d{19}$"
EXPECTED_DIRECTORY_PATTERN = r"^2\d{19}$"
REQUIRED_BOOTSTRAP_FILES = (
    "COUNTER_STORE.json",
    "id_migration/config/path_normalization_rules.json",
    "id_migration/config/file_classification_rules.json",
    "id_migration/schemas/dir_id.schema.json",
    "id_migration/schemas/physical_id_registry.schema.json",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def validate_manual(config: dict[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    required_keys = {
        "repository_root",
        "excluded_directories",
        "excluded_files",
        "assign_root_directory_id",
        "directory_identity_mechanism",
        "file_identity_mechanism",
        "physical_id_patterns",
    }

    if set(config) != required_keys:
        missing = sorted(required_keys - set(config))
        extra = sorted(set(config) - required_keys)
        if missing:
            errors.append(f"missing required keys: {', '.join(missing)}")
        if extra:
            errors.append(f"unexpected keys: {', '.join(extra)}")

    repository_root = Path(str(config.get("repository_root", "")))
    if not repository_root.is_absolute():
        errors.append("repository_root must be an absolute path")
    elif repository_root.resolve() != repo_root.resolve():
        errors.append(
            f"repository_root must resolve to {repo_root}, got {repository_root.resolve()}"
        )

    for key in ("excluded_directories", "excluded_files"):
        value = config.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"{key} must be a list of strings")
        elif len(value) != len(set(value)):
            errors.append(f"{key} contains duplicate entries")

    if not isinstance(config.get("assign_root_directory_id"), bool):
        errors.append("assign_root_directory_id must be boolean")

    directory_mechanism = config.get("directory_identity_mechanism")
    if not isinstance(directory_mechanism, dict):
        errors.append("directory_identity_mechanism must be an object")
    else:
        if directory_mechanism.get("mechanism") != "sidecar_anchor_file":
            errors.append("directory_identity_mechanism.mechanism must be sidecar_anchor_file")
        if directory_mechanism.get("anchor_filename") != ".dir_id":
            errors.append("directory_identity_mechanism.anchor_filename must be .dir_id")
        if not isinstance(directory_mechanism.get("anchor_required"), bool):
            errors.append("directory_identity_mechanism.anchor_required must be boolean")

    file_mechanism = config.get("file_identity_mechanism")
    if not isinstance(file_mechanism, dict):
        errors.append("file_identity_mechanism must be an object")
    else:
        if file_mechanism.get("mechanism") != "registry_assigned":
            errors.append("file_identity_mechanism.mechanism must be registry_assigned")
        if file_mechanism.get("rename_required") is not False:
            errors.append("file_identity_mechanism.rename_required must be false")

    patterns = config.get("physical_id_patterns")
    if not isinstance(patterns, dict):
        errors.append("physical_id_patterns must be an object")
    else:
        if patterns.get("id_length") != 20:
            errors.append("physical_id_patterns.id_length must be 20")
        if patterns.get("file_id_pattern") != EXPECTED_FILE_PATTERN:
            errors.append(
                "physical_id_patterns.file_id_pattern must be the literal regex ^1\\d{19}$"
            )
        if patterns.get("directory_id_pattern") != EXPECTED_DIRECTORY_PATTERN:
            errors.append(
                "physical_id_patterns.directory_id_pattern must be the literal regex ^2\\d{19}$"
            )

    return errors


def validate_schema(config: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return []

    validator = Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(config)]


def validate_bootstrap_files(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_BOOTSTRAP_FILES:
        full_path = repo_root / relative_path
        if not full_path.is_file():
            errors.append(f"required bootstrap file missing: {relative_path}")
            continue
        try:
            load_json(full_path)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON in {relative_path}: {exc}")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return fail(
            "usage: python id_migration/scripts/validate_physical_id_config.py "
            "id_migration/config/physical_id_config.json"
        )

    repo_root = Path(__file__).resolve().parents[2]
    schema_path = repo_root / "EA-REG" / "physical_id_config_schema.json"
    config_path = (repo_root / argv[1]).resolve()

    if not schema_path.is_file():
        return fail(f"schema not found: {schema_path}")
    if not config_path.is_file():
        return fail(f"config not found: {config_path}")

    try:
        schema = load_json(schema_path)
        config = load_json(config_path)
    except json.JSONDecodeError as exc:
        return fail(f"invalid JSON: {exc}")

    if not isinstance(config, dict):
        return fail("config root must be a JSON object")

    errors = []
    errors.extend(validate_schema(config, schema))
    errors.extend(validate_manual(config, repo_root))
    errors.extend(validate_bootstrap_files(repo_root))

    if errors:
        print("physical_id_config validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("physical_id_config.json validated successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

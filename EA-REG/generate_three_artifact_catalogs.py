#!/usr/bin/env python3
"""
Generate the canonical three-artifact starter set:
1. module_catalog.json
2. process_step_catalog.json
3. file_registry.csv

Inputs are grounded in the current repository state:
- 2026012201113002_updated_trading_process_v2.yaml
- file_module_mapping.csv
- identifier_map.json
- ../id_migration/output/physical_id_registry.csv
"""

from __future__ import annotations

import csv
import json
import os
import re
from collections import defaultdict
from io import StringIO
from pathlib import Path, PurePosixPath
from typing import Iterable

import yaml


REPO_ROOT = Path(__file__).resolve().parent
REPO_PARENT = REPO_ROOT.parent  # repository root (one level above EA-REG)
PROCESS_CANDIDATES = [
    REPO_PARENT / "2026012201113002_updated_trading_process_v2.yaml",
    REPO_ROOT / "2026012201113002_updated_trading_process_v2.yaml",
    REPO_PARENT / "updated_trading_process_aligned.yaml",
    REPO_ROOT / "updated_trading_process_aligned.yaml",
]
LEGACY_MAPPING_PATH = REPO_ROOT / "file_module_mapping.csv"
LEGACY_FILE_REGISTRY_PATH = (
    REPO_PARENT
    / "Directory management system"
    / "02_DOCUMENTATION"
    / "id_16_digit"
    / "registry"
    / "2026012201111008_FILE_REGISTRY.json"
)
IDENTIFIER_MAP_PATH = REPO_ROOT / "identifier_map.json"
PHYSICAL_REGISTRY_PATH = REPO_PARENT / "id_migration" / "output" / "physical_id_registry.csv"
CLASSIFICATION_RULES_PATH = REPO_PARENT / "id_migration" / "config" / "file_classification_rules.json"
MODULE_CATALOG_PATH = REPO_ROOT / "module_catalog.json"
PROCESS_STEP_CATALOG_PATH = REPO_ROOT / "process_step_catalog.json"
FILE_REGISTRY_PATH = REPO_ROOT / "file_registry.csv"

LOOP_SENTINEL_REMAP = {"(loop)": "F1_FLOW_ORCHESTRATOR"}

MODULE_KIND_MAP = {
    "B": "INTEGRATION_BRIDGE_MODULE",
    "D": "INTEGRATION_BRIDGE_MODULE",
    "F": "INFRA_PLATFORM_MODULE",
    "P": "OBSERVABILITY_REPORTING_MODULE",
}
LEGACY_ALIAS_NOTES = {
    "O2_OMS": "Legacy alias observed in file_module_mapping.csv; superseded by O2_OMS_STATE_MACHINE.",
    "O3_PNL_CLASSIFIER": (
        "Legacy alias observed in file_module_mapping.csv; superseded by "
        "O3_TRADE_CLOSE_CLASSIFIER."
    ),
}
CSV_HEADER = [
    "file_id",
    "relative_path",
    "directory_id",
    "file_name",
    "extension",
    "module_id",
    "assigned_module_name",
    "process_steps",
    "component_ids",
    "last_verified_utc",
    "file_scope_class",
]
BLANK_MODULE_SCOPE_CLASSES = {"test", "tooling", "legacy", "out_of_scope"}


def unique_ordered(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def select_process_source() -> tuple[Path, dict]:
    for candidate in PROCESS_CANDIDATES:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as handle:
                return candidate, yaml.safe_load(handle)
    raise FileNotFoundError("No process YAML source was found.")


def normalize_repo_relative(path_text: str) -> str:
    if not path_text:
        return ""

    raw = path_text.strip().replace("\\", "/")
    if not raw:
        return ""

    path_obj = Path(raw)
    if path_obj.is_absolute():
        absolute = path_obj.resolve(strict=False).as_posix()
        repo_root = REPO_PARENT.resolve().as_posix()
        prefix = repo_root + "/"
        if absolute.lower().startswith(prefix.lower()):
            raw = absolute[len(prefix) :]
        elif absolute.lower() == repo_root.lower():
            raw = ""
        else:
            raw = absolute

    return PurePosixPath(raw.lstrip("./")).as_posix()


def to_windows_path(posix_path: str) -> str:
    return posix_path.replace("/", "\\")


def path_exists_in_repo(posix_path: str) -> bool:
    if not posix_path:
        return False
    return (REPO_PARENT / Path(posix_path)).exists()


def extract_file_id(path_text: str) -> str:
    basename = PurePosixPath(path_text).name
    match = re.match(r"^(\d{16,20})(?:[_-]|$)", basename)
    return match.group(1) if match else ""


def humanize_module_id(module_id: str) -> str:
    if module_id == "(loop)":
        return "Loop Controller"

    words: list[str]
    if module_id.islower() and "-" in module_id:
        words = module_id.split("-")
    elif "_" in module_id:
        prefix, _, remainder = module_id.partition("_")
        if re.match(r"^[A-Z]\d+$", prefix):
            words = remainder.split("_")
        else:
            words = module_id.split("_")
    else:
        words = [module_id]

    special = {"mt4": "MT4", "oms": "OMS", "ea": "EA", "pnl": "PnL"}
    return " ".join(special.get(word.lower(), word.title()) for word in words if word)


def infer_module_kind(module_id: str) -> str:
    if module_id == "(loop)":
        return "PIPELINE_STAGE_MODULE"
    return MODULE_KIND_MAP.get(module_id[0], "PIPELINE_STAGE_MODULE")


def extract_contract_tokens(text: str) -> list[str]:
    if not text:
        return []

    cleaned = re.sub(r"\([^)]*\)", " ", text)
    cleaned = re.sub(r"\bfrom Step \d+\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("->", " ")
    cleaned = cleaned.replace("+", " ")
    cleaned = cleaned.replace(",", " ")
    cleaned = re.sub(r"\bOR\b", " ", cleaned)

    return unique_ordered(re.findall(r"\b[A-Z][A-Za-z0-9_]*\b", cleaned))


def extract_key_functions(responsible: str) -> list[str]:
    if not responsible:
        return []

    if "::" in responsible:
        return unique_ordered(part for part in responsible.split("::")[1:] if part)

    path_like = responsible.split("::")[0]
    if re.search(r"\.(py|mq4|mql4|js|ts)$", path_like, flags=re.IGNORECASE):
        stem = Path(path_like).stem
        return [stem] if stem else []

    return [responsible.strip()] if responsible.strip() else []


def make_directory_id(path_text: str) -> str:
    parent = PurePosixPath(path_text).parent.as_posix()
    if parent in ("", "."):
        return "DIR_ROOT"

    slug = re.sub(r"[^A-Za-z0-9]+", "_", parent).strip("_").upper()
    return f"DIR_{slug}" if slug else "DIR_ROOT"


def load_legacy_mapping_rows() -> list[dict[str, str]]:
    if not LEGACY_MAPPING_PATH.exists():
        return []

    content = LEGACY_MAPPING_PATH.read_text(encoding="utf-8-sig")
    content = content.lstrip("\ufeff").lstrip("\r\n")
    reader = csv.DictReader(StringIO(content))
    return [row for row in reader if row and any((value or "").strip() for value in row.values())]


def load_doc_id_lookup() -> dict[str, str]:
    if not LEGACY_FILE_REGISTRY_PATH.exists():
        return {}

    with LEGACY_FILE_REGISTRY_PATH.open("r", encoding="utf-8") as handle:
        registry = json.load(handle)

    lookup: dict[str, str] = {}
    for file_record in registry.get("files", []):
        relative_path = normalize_repo_relative(file_record.get("relative_path", ""))
        doc_id = file_record.get("doc_id", "")
        if relative_path and doc_id:
            lookup[relative_path] = doc_id
    return lookup


def load_identifier_context() -> dict[str, object]:
    if not IDENTIFIER_MAP_PATH.exists():
        raise FileNotFoundError(f"identifier map not found: {IDENTIFIER_MAP_PATH}")

    with IDENTIFIER_MAP_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    modules = payload.get("modules", {})
    aliases = payload.get("aliases", {})
    process_steps = payload.get("process_steps", {})
    if not isinstance(modules, dict) or not isinstance(aliases, dict) or not isinstance(process_steps, dict):
        raise ValueError("identifier_map.json must contain modules, aliases, and process_steps objects")

    steps_by_number: dict[int, dict[str, str]] = {}
    for step_key, step_payload in process_steps.items():
        if not isinstance(step_payload, dict):
            raise ValueError(f"identifier_map process step {step_key!r} is not an object")
        step_number = int(step_payload["step_number"])
        steps_by_number[step_number] = step_payload

    aliases_by_target: dict[str, list[str]] = defaultdict(list)
    for alias_symbol, alias_payload in aliases.items():
        target_symbol = alias_payload.get("resolves_to", "")
        if target_symbol:
            aliases_by_target[target_symbol].append(alias_symbol)

    return {
        "payload": payload,
        "modules": modules,
        "aliases": aliases,
        "steps_by_number": steps_by_number,
        "aliases_by_target": {
            target: sorted(values)
            for target, values in aliases_by_target.items()
        },
    }


def load_physical_registry_rows() -> dict[str, dict[str, str]]:
    if not PHYSICAL_REGISTRY_PATH.exists():
        raise FileNotFoundError(f"physical registry not found: {PHYSICAL_REGISTRY_PATH}")

    with PHYSICAL_REGISTRY_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [
            row
            for row in reader
            if row and any((value or "").strip() for value in row.values())
        ]

    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        relative_path = normalize_repo_relative(row.get("relative_path", ""))
        if not relative_path:
            continue
        lookup[relative_path] = {
            **row,
            "relative_path": relative_path,
        }
    return lookup


def load_classification_rules() -> dict[str, object]:
    if not CLASSIFICATION_RULES_PATH.exists():
        raise FileNotFoundError(f"classification rules not found: {CLASSIFICATION_RULES_PATH}")

    with CLASSIFICATION_RULES_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("file_classification_rules.json must contain a JSON object")
    return payload


def classify_scope(relative_path: str, object_type: str, rules_data: dict[str, object]) -> str:
    default_class = str(rules_data.get("default_scope_class", "module_owned"))
    scope_class = default_class
    match_path = relative_path.replace("\\", "/")
    match_path_for_rules = f"{match_path}/" if object_type == "directory" and not match_path.endswith("/") else match_path

    for rule in rules_data.get("rules", []):
        if not isinstance(rule, dict):
            continue
        values = [str(value) for value in rule.get("values", [])]
        matched = False
        if rule.get("match_type") == "path_prefix":
            matched = any(match_path_for_rules.startswith(value) or match_path.startswith(value) for value in values)
        elif rule.get("match_type") == "path_contains":
            matched = any(value in match_path_for_rules or value in match_path for value in values)
        if matched:
            scope_class = str(rule.get("scope_class", scope_class))
            break

    return scope_class


def resolve_module_symbol(module_symbol: str, identifier_context: dict[str, object]) -> str:
    if not module_symbol:
        return ""

    modules = identifier_context["modules"]
    aliases = identifier_context["aliases"]
    if module_symbol in modules:
        return module_symbol
    if module_symbol in aliases:
        return str(aliases[module_symbol]["resolves_to"])
    raise KeyError(f"Unknown module symbol: {module_symbol}")


def module_numeric_id(module_symbol: str, identifier_context: dict[str, object]) -> str:
    if not module_symbol:
        return ""
    canonical_symbol = resolve_module_symbol(module_symbol, identifier_context)
    return str(identifier_context["modules"][canonical_symbol]["numeric_id"])


def module_name(module_symbol: str, identifier_context: dict[str, object]) -> str:
    if not module_symbol:
        return ""
    canonical_symbol = resolve_module_symbol(module_symbol, identifier_context)
    return str(identifier_context["modules"][canonical_symbol].get("module_name", humanize_module_id(canonical_symbol)))


def load_existing_module_catalog() -> dict | None:
    if not MODULE_CATALOG_PATH.exists():
        return None

    with MODULE_CATALOG_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        return None
    if not isinstance(payload.get("modules"), list):
        return None
    return payload


def derive_step_dependencies(
    step: dict,
    output_producers: dict[str, list[dict]],
    step_by_number: dict[int, dict],
) -> list[dict[str, str]]:
    dependency_details: dict[str, set[str]] = defaultdict(set)
    input_text = step.get("input_contract", step.get("input", ""))

    for step_number_text in re.findall(r"\bfrom Step (\d+)\b", input_text, flags=re.IGNORECASE):
        explicit_step = step_by_number.get(int(step_number_text))
        if explicit_step and explicit_step["module_symbol"] != step["module_symbol"]:
            dependency_details[explicit_step["module_id"]].add(
                f"Explicitly references step {explicit_step['step_number']}."
            )

    for contract in extract_contract_tokens(input_text):
        for producer in output_producers.get(contract, []):
            if producer["step_number"] >= step["step_number"]:
                continue
            if producer["module_symbol"] == step["module_symbol"]:
                continue
            dependency_details[producer["module_id"]].add(f"Produces {contract}.")

    dependencies: list[dict[str, str]] = []
    for target_id in sorted(dependency_details):
        reasons = sorted(dependency_details[target_id])
        dependencies.append(
            {
                "target_type": "module",
                "target_id": target_id,
                "relationship": "requires",
                "reason": " ".join(reasons),
            }
        )
    return dependencies


def build_process_step_catalog(
    process_doc: dict,
    process_source: Path,
    identifier_context: dict[str, object],
) -> tuple[dict, dict[str, list[dict]]]:
    steps = process_doc.get("steps", [])
    step_by_number: dict[int, dict] = {}
    output_producers: dict[str, list[dict]] = defaultdict(list)
    identifier_steps = identifier_context["steps_by_number"]

    normalized_steps: list[dict] = []
    for step in steps:
        step_number = int(step["number"])
        normalized_entrypoints = unique_ordered(
            normalize_repo_relative(path_text) for path_text in step.get("entrypoint_files", [])
        )
        raw_module_symbol = LOOP_SENTINEL_REMAP.get(step["module_id"], step["module_id"])
        canonical_symbol = resolve_module_symbol(raw_module_symbol, identifier_context)
        step_identity = identifier_steps.get(step_number)
        if step_identity is None:
            raise KeyError(f"identifier_map.json missing process step mapping for step {step_number}")
        normalized_step = {
            "step_number": step_number,
            "step_code": f"S{step_number:02d}",
            "process_step_id": str(step_identity["numeric_id"]),
            "step_name": step["name"],
            "module_id": module_numeric_id(canonical_symbol, identifier_context),
            "module_symbol": canonical_symbol,
            "responsible": step.get("responsible", ""),
            "input_contract": step.get("input", ""),
            "output_contract": step.get("output", ""),
            "input_contracts": extract_contract_tokens(step.get("input", "")),
            "output_contracts": extract_contract_tokens(step.get("output", "")),
            "validation": step.get("validation", ""),
            "failure": step.get("failure", ""),
            "entrypoint_files_internal": normalized_entrypoints,
        }
        normalized_steps.append(normalized_step)
        step_by_number[step_number] = normalized_step
        for output_contract in normalized_step["output_contracts"]:
            output_producers[output_contract].append(normalized_step)

    module_to_steps: dict[str, list[dict]] = defaultdict(list)
    exported_steps: list[dict] = []
    for step in normalized_steps:
        step["dependency_step_ids"] = unique_ordered(
            step_by_number[int(step_number_text)]["process_step_id"]
            for step_number_text in re.findall(
                r"\bfrom Step (\d+)\b", step.get("input_contract", ""), flags=re.IGNORECASE
            )
            if int(step_number_text) in step_by_number
        )
        for contract in step["input_contracts"]:
            for producer in output_producers.get(contract, []):
                if producer["step_number"] >= step["step_number"]:
                    continue
                step["dependency_step_ids"].append(producer["process_step_id"])
        step["dependency_step_ids"] = sorted(set(step["dependency_step_ids"]))

        exported_step = {
            "process_step_id": step["process_step_id"],
            "step_code": step["step_code"],
            "step_number": step["step_number"],
            "step_name": step["step_name"],
            "module_id": step["module_id"],
            "module_symbol": step["module_symbol"],
            "responsible": step["responsible"],
            "input_contract": step["input_contract"],
            "output_contract": step["output_contract"],
            "input_contracts": step["input_contracts"],
            "output_contracts": step["output_contracts"],
            "dependency_step_ids": step["dependency_step_ids"],
            "validation": step["validation"],
            "failure": step["failure"],
            "entrypoint_files": [to_windows_path(path_text) for path_text in step["entrypoint_files_internal"]],
        }
        exported_steps.append(exported_step)
        module_to_steps[step["module_symbol"]].append(step)

    catalog = {
        "schema_version": "1.0.0",
        "document_type": "process_step_catalog",
        "catalog_id": "HUEY_P_EAFIX_PROCESS_STEP_CATALOG",
        "catalog_name": "HUEY P EAFIX Process Step Catalog",
        "process_context": {
            "process_id": process_doc.get("process_id", ""),
            "process_version": process_doc.get("process_version", ""),
            "source_file": process_source.name,
        },
        "steps": exported_steps,
    }
    return catalog, module_to_steps


def build_module_catalog(
    process_doc: dict,
    process_source: Path,
    module_to_steps: dict[str, list[dict]],
    legacy_module_ids: set[str],
    existing_catalog: dict | None,
    identifier_context: dict[str, object],
) -> dict:
    process_id = process_doc.get("process_id", "")
    process_version = process_doc.get("process_version", "")
    all_steps = [step for steps in module_to_steps.values() for step in steps]
    global_output_producers: dict[str, list[dict]] = defaultdict(list)
    global_step_by_number = {step["step_number"]: step for step in all_steps}
    for step in all_steps:
        for output_contract in step["output_contracts"]:
            global_output_producers[output_contract].append(step)

    process_module_order = [
        resolve_module_symbol(LOOP_SENTINEL_REMAP.get(step["module_id"], step["module_id"]), identifier_context)
        for step in process_doc.get("steps", [])
    ]
    process_module_symbols = unique_ordered(
        process_module_order + list(identifier_context["modules"].keys())
    )
    existing_modules = {
        module.get("canonical_symbol", module.get("module_id")): module
        for module in (existing_catalog or {}).get("modules", [])
        if isinstance(module, dict) and (module.get("canonical_symbol") or module.get("module_id"))
    }
    aliases_by_target: dict[str, list[str]] = identifier_context["aliases_by_target"]

    modules: list[dict] = []
    for module_symbol in process_module_symbols:
        steps = module_to_steps.get(module_symbol, [])
        existing_module = existing_modules.get(module_symbol, {})
        module_entry = identifier_context["modules"][module_symbol]
        aggregated_dependencies: dict[str, set[str]] = defaultdict(set)
        for step in steps:
            for dependency in derive_step_dependencies(
                step,
                global_output_producers,
                global_step_by_number,
            ):
                aggregated_dependencies[dependency["target_id"]].add(dependency["reason"])

        dependencies = [
            {
                "target_type": "module",
                "target_id": target_id,
                "relationship": "requires",
                "reason": " ".join(sorted(reasons)),
            }
            for target_id, reasons in sorted(aggregated_dependencies.items())
        ]

        scope_in = unique_ordered(
            contract
            for step in steps
            for contract in step.get("input_contracts", [])
        )
        scope_out = unique_ordered(
            contract
            for step in steps
            for contract in step.get("output_contracts", [])
        )
        responsibilities = unique_ordered(step["step_name"] for step in steps)
        key_functions = unique_ordered(
            function_name
            for step in steps
            for function_name in extract_key_functions(step["responsible"])
        )

        interfaces = [
            {"name": contract, "kind": "input", "contract_type": contract}
            for contract in scope_in
        ] + [
            {"name": contract, "kind": "output", "contract_type": contract}
            for contract in scope_out
        ]

        process_bindings = [
            {
                "process_id": process_id,
                "process_version": process_version,
                "step_number": step["step_number"],
                "step_name": step["step_name"],
                "responsible": step["responsible"],
                "input_contract": step["input_contract"],
                "output_contract": step["output_contract"],
                "validation": step["validation"],
                "failure": step["failure"],
                "entrypoint_files": [
                    to_windows_path(path_text) for path_text in step["entrypoint_files_internal"]
                ],
            }
            for step in sorted(steps, key=lambda item: item["step_number"])
        ]

        entrypoint_files = unique_ordered(
            path_text
            for step in steps
            for path_text in step["entrypoint_files_internal"]
        )
        filesystem_hints = {
            "entrypoint_files": [to_windows_path(path_text) for path_text in entrypoint_files]
        }
        if entrypoint_files:
            filesystem_hints["module_root"] = to_windows_path(
                os.path.commonpath(entrypoint_files).replace("\\", "/")
            )

        notes = unique_ordered(
            step["failure"]
            for step in steps
            if step.get("failure")
        )

        if module_symbol == "SHARED_LIBS" and not steps:
            purpose = "Owns cross-cutting shared libraries used across canonical modules."
            responsibilities = ["Provide reusable shared utilities and middleware."]
            filesystem_hints = {"module_root": "shared"}
        else:
            purpose = (
                f"Owns process step {steps[0]['step_number']}: {steps[0]['step_name']}."
                if len(steps) == 1
                else "Owns multiple process steps in the canonical trading workflow."
            )

        module_record = {
            "module_id": str(module_entry["numeric_id"]),
            "canonical_symbol": module_symbol,
            "module_name": str(module_entry.get("module_name", humanize_module_id(module_symbol))),
            "module_kind": infer_module_kind(module_symbol),
            "version": str(existing_module.get("version", "1.0.0")),
            "status": "canonical",
            "layer": existing_module.get("layer", "unassigned"),
            "purpose": purpose,
            "scope_in": scope_in,
            "scope_out": scope_out,
            "responsibilities": responsibilities,
            "dependencies": dependencies,
            "key_functions": key_functions,
            "interfaces": interfaces,
            "process_bindings": process_bindings,
            "filesystem_hints": filesystem_hints,
        }
        invariants = unique_ordered(
            step["validation"]
            for step in steps
            if step.get("validation")
        )
        if invariants:
            module_record["quality_gates"] = {"invariants": invariants}
        if notes:
            module_record["notes"] = notes
        if aliases_by_target.get(module_symbol):
            module_record["legacy_aliases"] = aliases_by_target[module_symbol]

        modules.append(module_record)

    catalog = {
        "schema_version": "1.0.0",
        "document_type": "module_catalog",
        "catalog_id": "HUEY_P_EAFIX_MODULE_CATALOG",
        "catalog_name": "HUEY P EAFIX Module Catalog",
        "version": "1.0.0",
        "process_context": {
            "process_id": process_id,
            "process_version": process_version,
            "module_registry_file": process_source.name,
        },
        "modules": modules,
    }
    if existing_catalog:
        catalog.update(
            {
                key: value
                for key, value in existing_catalog.items()
                if key != "modules"
            }
        )
        catalog["process_context"] = {
            **catalog.get("process_context", {}),
            "process_id": process_id,
            "process_version": process_version,
            "module_registry_file": process_source.name,
        }

    return catalog


def build_file_registry(
    module_to_steps: dict[str, list[dict]],
    legacy_rows: list[dict[str, str]],
    physical_registry_rows: dict[str, dict[str, str]],
    classification_rules: dict[str, object],
    identifier_context: dict[str, object],
    last_verified_utc: str,
) -> list[dict[str, str]]:
    file_records: dict[str, dict] = {}

    for row in legacy_rows:
        relative_path = normalize_repo_relative(row.get("FullName", ""))
        physical_row = physical_registry_rows.get(relative_path)
        if (
            not relative_path
            or physical_row is None
            or physical_row.get("object_type") != "file"
            or physical_row.get("is_excluded") == "True"
        ):
            continue

        record = file_records.setdefault(
            relative_path,
            {
                "module_symbols": [],
                "entrypoint_steps": [],
                "physical_row": physical_row,
            },
        )
        for module_symbol in unique_ordered((row.get("CanonicalModules", "") or "").split(",")):
            record["module_symbols"].append(resolve_module_symbol(module_symbol, identifier_context))

    for steps in module_to_steps.values():
        for step in steps:
            for entrypoint_path in step.get("entrypoint_files_internal", []):
                physical_row = physical_registry_rows.get(entrypoint_path)
                if (
                    not path_exists_in_repo(entrypoint_path)
                    or physical_row is None
                    or physical_row.get("object_type") != "file"
                    or physical_row.get("is_excluded") == "True"
                ):
                    continue
                record = file_records.setdefault(
                    entrypoint_path,
                    {
                        "module_symbols": [],
                        "entrypoint_steps": [],
                        "physical_row": physical_row,
                    },
                )
                record["module_symbols"].append(step["module_symbol"])
                record["entrypoint_steps"].append(step)

    rows: list[dict[str, str]] = []
    for relative_path in sorted(file_records, key=str.casefold):
        file_record = file_records[relative_path]
        physical_row = file_record["physical_row"]
        scope_class = classify_scope(relative_path, "file", classification_rules)
        candidate_symbols = unique_ordered(
            [*file_record["module_symbols"], *(step["module_symbol"] for step in file_record["entrypoint_steps"])]
        )
        if scope_class == "tooling" and candidate_symbols:
            scope_class = "module_owned"

        if scope_class == "shared":
            assigned_symbol = "SHARED_LIBS"
        elif scope_class == "config_data":
            assigned_symbol = "F1_CONFIG_PREFERENCES"
        elif scope_class in BLANK_MODULE_SCOPE_CLASSES:
            assigned_symbol = ""
        else:
            assigned_symbol = candidate_symbols[0] if candidate_symbols else ""

        if not assigned_symbol:
            continue

        step_ids = unique_ordered(
            step["process_step_id"]
            for step in sorted(file_record["entrypoint_steps"], key=lambda item: item["step_number"])
            if step["module_symbol"] == assigned_symbol
        )
        rows.append(
            {
                "file_id": physical_row.get("file_id", ""),
                "relative_path": relative_path,
                "directory_id": physical_row.get("parent_directory_id", ""),
                "file_name": physical_row.get("name", PurePosixPath(relative_path).name),
                "extension": physical_row.get("extension", PurePosixPath(relative_path).suffix),
                "module_id": module_numeric_id(assigned_symbol, identifier_context) if assigned_symbol else "",
                "assigned_module_name": module_name(assigned_symbol, identifier_context) if assigned_symbol else "",
                "process_steps": ";".join(step_ids),
                "component_ids": "",
                "last_verified_utc": last_verified_utc,
                "file_scope_class": scope_class,
            }
        )

    return rows


def write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def write_file_registry(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    process_source, process_doc = select_process_source()
    legacy_rows = load_legacy_mapping_rows()
    existing_catalog = load_existing_module_catalog()
    identifier_context = load_identifier_context()
    physical_registry_rows = load_physical_registry_rows()
    classification_rules = load_classification_rules()
    last_verified_utc = str(identifier_context["payload"].get("generated_at", ""))
    legacy_module_ids = {
        module_id
        for row in legacy_rows
        for module_id in unique_ordered((row.get("CanonicalModules", "") or "").split(","))
        if module_id
    }

    process_step_catalog, module_to_steps = build_process_step_catalog(
        process_doc,
        process_source,
        identifier_context,
    )
    module_catalog = build_module_catalog(
        process_doc=process_doc,
        process_source=process_source,
        module_to_steps=module_to_steps,
        legacy_module_ids=legacy_module_ids,
        existing_catalog=existing_catalog,
        identifier_context=identifier_context,
    )
    file_registry_rows = build_file_registry(
        module_to_steps=module_to_steps,
        legacy_rows=legacy_rows,
        physical_registry_rows=physical_registry_rows,
        classification_rules=classification_rules,
        identifier_context=identifier_context,
        last_verified_utc=last_verified_utc,
    )

    write_json(PROCESS_STEP_CATALOG_PATH, process_step_catalog)
    write_json(MODULE_CATALOG_PATH, module_catalog)
    write_file_registry(FILE_REGISTRY_PATH, file_registry_rows)

    mapped_rows = sum(1 for row in file_registry_rows if row["module_id"])
    step_bound_rows = sum(1 for row in file_registry_rows if row["process_steps"])
    print(f"Process source: {process_source.name}")
    print(f"Process steps written: {len(process_step_catalog['steps'])}")
    print(f"Modules written: {len(module_catalog['modules'])}")
    print(f"File registry rows written: {len(file_registry_rows)}")
    print(f"Rows with module binding: {mapped_rows}")
    print(f"Rows with process-step binding: {step_bound_rows}")
    if existing_catalog:
        print(f"Seed catalog preserved: {len(existing_catalog.get('modules', []))} existing modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

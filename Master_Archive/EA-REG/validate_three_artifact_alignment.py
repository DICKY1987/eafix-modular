from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


FILE_REGISTRY_COLUMNS = [
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
PHYSICAL_REGISTRY_COLUMNS = [
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
ALLOWED_SCOPE_CLASSES = {
    "module_owned",
    "shared",
    "test",
    "tooling",
    "legacy",
    "config_data",
    "out_of_scope",
}
BLANK_ALLOWED_SCOPE_CLASSES = {"test", "tooling", "legacy", "out_of_scope"}
MODULE_ID_PATTERN = re.compile(r"^5\d{19}$")
PROCESS_STEP_ID_PATTERN = re.compile(r"^6\d{19}$")
FILE_ID_PATTERN = re.compile(r"^1\d{19}$")
DIRECTORY_ID_PATTERN = re.compile(r"^2\d{19}$")
UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T")
LOOP_SENTINEL_REMAP = {"(loop)": "F1_FLOW_ORCHESTRATOR"}


class ArtifactValidator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.parent_root = repo_root.parent
        self.file_registry_path = repo_root / "file_registry.csv"
        self.module_catalog_path = repo_root / "module_catalog.json"
        self.process_step_catalog_path = repo_root / "process_step_catalog.json"
        self.module_schema_path = repo_root / "schemas" / "module_catalog.schema.json"
        self.identifier_map_path = repo_root / "identifier_map.json"
        self.physical_registry_path = self.parent_root / "id_migration" / "output" / "physical_id_registry.csv"
        self.physical_report_path = self.parent_root / "id_migration" / "output" / "physical_validation_report.json"
        self.process_source_candidates = [
            self.parent_root / "2026012201113002_updated_trading_process_v2.yaml",
            repo_root / "2026012201113002_updated_trading_process_v2.yaml",
            self.parent_root / "updated_trading_process_aligned.yaml",
            repo_root / "updated_trading_process_aligned.yaml",
        ]
        self.markdown_report_path = repo_root / "ALIGNMENT_VALIDATION_REPORT.md"

        self.info: list[str] = []
        self.warnings: list[str] = []
        self.alignment_errors: list[str] = []
        self.readiness_errors: list[str] = []
        self.physical_errors: list[str] = []

    def validate_all(self) -> tuple[bool, dict[str, Any]]:
        print("=" * 80)
        print("THREE-ARTIFACT ALIGNMENT VALIDATION")
        print("=" * 80)

        self._check_artifact_existence()

        file_registry_rows, file_registry_columns = self._load_csv_rows(self.file_registry_path, "file registry")
        physical_registry_rows, physical_registry_columns = self._load_csv_rows(
            self.physical_registry_path,
            "physical registry",
        )
        module_catalog = self._load_json(self.module_catalog_path, "module catalog")
        process_catalog = self._load_json(self.process_step_catalog_path, "process step catalog")
        identifier_map = self._load_json(self.identifier_map_path, "identifier map")
        physical_report = self._load_json(self.physical_report_path, "physical validation report", required=False)
        process_source_path, process_yaml = self._load_process_yaml()

        physical_status = self._validate_physical_status(physical_report, physical_registry_columns, physical_registry_rows)
        if module_catalog:
            self._validate_module_catalog_schema(module_catalog)
            self._validate_module_catalog(module_catalog, identifier_map)
        if process_catalog and process_yaml and identifier_map:
            self._validate_process_catalog(process_catalog, process_yaml, identifier_map, process_source_path)
        if file_registry_rows and module_catalog and process_catalog and physical_registry_rows:
            self._validate_file_registry(
                file_registry_columns,
                file_registry_rows,
                module_catalog,
                process_catalog,
                physical_registry_rows,
            )

        semantic_coverage_pct = self._compute_semantic_coverage(file_registry_rows)
        alignment_status = "PASS" if not self.alignment_errors else "FAIL"
        readiness_status = (
            "PASS"
            if not self.readiness_errors and semantic_coverage_pct >= 85.0 and physical_status == "PASS"
            else "FAIL"
        )
        success = physical_status == "PASS" and alignment_status == "PASS" and readiness_status == "PASS"

        report = self._build_report(
            physical_status=physical_status,
            alignment_status=alignment_status,
            readiness_status=readiness_status,
            semantic_coverage_pct=semantic_coverage_pct,
            file_registry_rows=file_registry_rows,
            module_catalog=module_catalog,
            process_catalog=process_catalog,
            process_source_path=process_source_path,
        )
        self._write_markdown_report(report)
        self._print_summary(report)
        return success, report

    def _check_artifact_existence(self) -> None:
        print("\n1. CHECKING ARTIFACT EXISTENCE")
        print("-" * 80)
        required_paths = [
            ("file registry", self.file_registry_path, True),
            ("module catalog", self.module_catalog_path, True),
            ("process step catalog", self.process_step_catalog_path, True),
            ("module schema", self.module_schema_path, True),
            ("identifier map", self.identifier_map_path, True),
            ("physical registry", self.physical_registry_path, True),
            ("physical validation report", self.physical_report_path, False),
        ]

        for label, path, required in required_paths:
            if path.exists():
                print(f"✓ {label}: {path.name}")
                self.info.append(f"{label.title()} present: {path.name}")
                continue
            message = f"Missing {label}: {path}"
            if required:
                print(f"✗ {message}")
                self.alignment_errors.append(message)
            else:
                print(f"⚠ {message}")
                self.warnings.append(message)

    def _load_csv_rows(self, path: Path, label: str) -> tuple[list[dict[str, str]], list[str]]:
        if not path.exists():
            return [], []

        try:
            content = path.read_text(encoding="utf-8-sig")
            reader = csv.DictReader(StringIO(content))
            rows = [
                row
                for row in reader
                if row and any((value or "").strip() for value in row.values())
            ]
            return rows, reader.fieldnames or []
        except Exception as exc:
            self.alignment_errors.append(f"Error loading {label}: {exc}")
            return [], []

    def _load_json(self, path: Path, label: str, *, required: bool = True) -> dict[str, Any]:
        if not path.exists():
            if required:
                self.alignment_errors.append(f"Missing {label}: {path}")
            return {}

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception as exc:
            self.alignment_errors.append(f"Error loading {label}: {exc}")
            return {}

        if not isinstance(payload, dict):
            self.alignment_errors.append(f"{label.title()} is not a JSON object: {path}")
            return {}
        return payload

    def _load_process_yaml(self) -> tuple[Path | None, dict[str, Any]]:
        for candidate in self.process_source_candidates:
            if not candidate.exists():
                continue
            try:
                with candidate.open("r", encoding="utf-8") as handle:
                    payload = yaml.safe_load(handle)
            except Exception as exc:
                self.alignment_errors.append(f"Error loading process YAML {candidate}: {exc}")
                return candidate, {}
            if isinstance(payload, dict):
                return candidate, payload
            self.alignment_errors.append(f"Process YAML is not a mapping: {candidate}")
            return candidate, {}
        self.alignment_errors.append("No process YAML source was found for comparison.")
        return None, {}

    def _normalize_path(self, path_text: str) -> str:
        raw = (path_text or "").strip().replace("\\", "/")
        return PurePosixPath(raw.lstrip("./")).as_posix() if raw else ""

    def _parse_utc(self, value: str) -> bool:
        if not value or not UTC_PATTERN.search(value):
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return True

    def _validate_physical_status(
        self,
        physical_report: dict[str, Any],
        physical_columns: list[str],
        physical_rows: list[dict[str, str]],
    ) -> str:
        print("\n2. VALIDATING PHYSICAL LAYER STATUS")
        print("-" * 80)

        if physical_columns != PHYSICAL_REGISTRY_COLUMNS:
            self.physical_errors.append(
                "physical_id_registry.csv does not match the expected 11-column schema"
            )
        if not physical_rows:
            self.physical_errors.append("physical_id_registry.csv is empty")

        if physical_report:
            report_status = str(physical_report.get("physical_status", "FAIL"))
            if report_status != "PASS":
                self.physical_errors.append(
                    f"physical_validation_report.json reports physical_status={report_status}"
                )
        else:
            self.warnings.append("physical_validation_report.json not available; using registry-only physical checks")

        status = "PASS" if not self.physical_errors else "FAIL"
        print(f"Physical status: {status}")
        return status

    def _validate_module_catalog_schema(self, module_catalog: dict[str, Any]) -> None:
        print("\n3. VALIDATING MODULE CATALOG SCHEMA")
        print("-" * 80)
        try:
            import jsonschema
        except ImportError:
            self.warnings.append("jsonschema not installed; module catalog schema validation skipped.")
            return

        try:
            schema = json.loads(self.module_schema_path.read_text(encoding="utf-8"))
            validator = jsonschema.Draft202012Validator(schema)
            errors = sorted(validator.iter_errors(module_catalog), key=lambda err: list(err.path))
        except Exception as exc:
            self.alignment_errors.append(f"Error validating module catalog schema: {exc}")
            return

        for error in errors[:20]:
            path = ".".join(str(part) for part in error.path) or "<root>"
            self.alignment_errors.append(f"Module catalog schema violation at {path}: {error.message}")
        if not errors:
            self.info.append("Module catalog passes schema validation.")

    def _validate_module_catalog(self, module_catalog: dict[str, Any], identifier_map: dict[str, Any]) -> None:
        modules = module_catalog.get("modules", [])
        if not isinstance(modules, list):
            self.alignment_errors.append("module_catalog.json must contain a modules array")
            return

        seen_module_ids: set[str] = set()
        seen_symbols: set[str] = set()
        alias_symbols = set((identifier_map.get("aliases") or {}).keys())

        for module in modules:
            module_id = str(module.get("module_id", ""))
            canonical_symbol = str(module.get("canonical_symbol", ""))
            module_name = str(module.get("module_name", ""))
            if not MODULE_ID_PATTERN.fullmatch(module_id):
                self.alignment_errors.append(f"Invalid module_catalog.module_id: {module_id!r}")
            if module_id in seen_module_ids:
                self.alignment_errors.append(f"Duplicate module_catalog.module_id: {module_id}")
            seen_module_ids.add(module_id)

            if not canonical_symbol:
                self.alignment_errors.append("module_catalog canonical_symbol may not be blank")
            if canonical_symbol in seen_symbols:
                self.alignment_errors.append(f"Duplicate module_catalog canonical_symbol: {canonical_symbol}")
            seen_symbols.add(canonical_symbol)

            if canonical_symbol in alias_symbols:
                self.alignment_errors.append(
                    f"Alias symbol {canonical_symbol} must not appear as a module_catalog row"
                )
            if not module_name:
                self.alignment_errors.append(f"module_catalog row {canonical_symbol!r} has blank module_name")

        self.info.append(f"Module catalog rows checked: {len(modules)}")

    def _validate_process_catalog(
        self,
        process_catalog: dict[str, Any],
        process_yaml: dict[str, Any],
        identifier_map: dict[str, Any],
        process_source_path: Path | None,
    ) -> None:
        print("\n4. VALIDATING PROCESS STEP CATALOG")
        print("-" * 80)
        steps = process_catalog.get("steps", [])
        yaml_steps = {
            int(step["number"]): step
            for step in process_yaml.get("steps", [])
            if step.get("number") is not None
        }
        id_steps = identifier_map.get("process_steps", {})
        id_steps_by_number = {
            int(step_payload["step_number"]): step_payload
            for step_payload in id_steps.values()
            if isinstance(step_payload, dict) and step_payload.get("step_number") is not None
        }
        seen_step_ids: set[str] = set()

        for step in steps:
            step_number = int(step.get("step_number", 0))
            process_step_id = str(step.get("process_step_id", ""))
            module_id = str(step.get("module_id", ""))
            module_symbol = str(step.get("module_symbol", ""))

            if not PROCESS_STEP_ID_PATTERN.fullmatch(process_step_id):
                self.alignment_errors.append(f"Invalid process_step_id: {process_step_id!r}")
            if process_step_id in seen_step_ids:
                self.alignment_errors.append(f"Duplicate process_step_id: {process_step_id}")
            seen_step_ids.add(process_step_id)
            if not MODULE_ID_PATTERN.fullmatch(module_id):
                self.alignment_errors.append(f"Invalid process_step_catalog.module_id: {module_id!r}")
            if not module_symbol:
                self.alignment_errors.append(f"Process step {process_step_id} has blank module_symbol")

            yaml_step = yaml_steps.get(step_number)
            id_step = id_steps_by_number.get(step_number)
            if yaml_step is None or id_step is None:
                self.alignment_errors.append(f"Step {step_number} missing from YAML or identifier_map")
                continue

            expected_symbol = LOOP_SENTINEL_REMAP.get(str(yaml_step.get("module_id", "")), str(yaml_step.get("module_id", "")))
            expected_id = str(id_step.get("module_id", ""))
            if step.get("step_name") != yaml_step.get("name"):
                self.alignment_errors.append(
                    f"Step {step_number} name mismatch: catalog={step.get('step_name')!r} yaml={yaml_step.get('name')!r}"
                )
            if module_symbol != expected_symbol:
                self.alignment_errors.append(
                    f"Step {step_number} module_symbol mismatch: catalog={module_symbol!r} yaml={expected_symbol!r}"
                )
            if module_id != expected_id:
                self.alignment_errors.append(
                    f"Step {step_number} module_id mismatch: catalog={module_id!r} identifier_map={expected_id!r}"
                )

        if process_source_path:
            self.info.append(f"Process catalog matches YAML source {process_source_path.name}")

    def _validate_file_registry(
        self,
        actual_columns: list[str],
        file_registry_rows: list[dict[str, str]],
        module_catalog: dict[str, Any],
        process_catalog: dict[str, Any],
        physical_registry_rows: list[dict[str, str]],
    ) -> None:
        print("\n5. VALIDATING FILE REGISTRY AND CROSS-LAYER LINKS")
        print("-" * 80)

        if actual_columns != FILE_REGISTRY_COLUMNS:
            self.alignment_errors.append(
                "file_registry.csv does not match the expected 11-column order: "
                + ", ".join(FILE_REGISTRY_COLUMNS)
            )

        module_ids = {str(module.get("module_id", "")) for module in module_catalog.get("modules", []) if module.get("module_id")}
        process_steps = process_catalog.get("steps", [])
        process_step_ids = {
            str(step.get("process_step_id", ""))
            for step in process_steps
            if step.get("process_step_id")
        }
        module_bindings = {
            str(module.get("module_id", "")): {
                int(binding.get("step_number"))
                for binding in module.get("process_bindings", [])
                if binding.get("step_number") is not None
            }
            for module in module_catalog.get("modules", [])
        }
        physical_file_rows = {
            self._normalize_path(row.get("relative_path", "")): row
            for row in physical_registry_rows
            if row.get("object_type") == "file"
        }
        physical_file_ids = {
            row.get("file_id", "")
            for row in physical_registry_rows
            if row.get("object_type") == "file" and row.get("file_id")
        }
        physical_directory_ids = {
            row.get("directory_id", "")
            for row in physical_registry_rows
            if row.get("object_type") == "directory" and row.get("directory_id")
        }

        for row in file_registry_rows:
            file_id = row.get("file_id", "")
            relative_path = self._normalize_path(row.get("relative_path", ""))
            directory_id = row.get("directory_id", "")
            file_name = row.get("file_name", "")
            extension = row.get("extension", "")
            module_id = row.get("module_id", "")
            assigned_module_name = row.get("assigned_module_name", "")
            process_steps_value = row.get("process_steps", "")
            last_verified_utc = row.get("last_verified_utc", "")
            file_scope_class = row.get("file_scope_class", "")

            if not FILE_ID_PATTERN.fullmatch(file_id):
                self.alignment_errors.append(f"Invalid file_registry.file_id for {relative_path}: {file_id!r}")
                self.readiness_errors.append(f"Blank or invalid file_id for {relative_path}")
            if not directory_id:
                self.readiness_errors.append(f"Blank directory_id for {relative_path}")
            elif not DIRECTORY_ID_PATTERN.fullmatch(directory_id):
                self.alignment_errors.append(f"Invalid file_registry.directory_id for {relative_path}: {directory_id!r}")
            if not relative_path or relative_path != self._normalize_path(relative_path):
                self.alignment_errors.append(f"file_registry relative_path is not normalized: {relative_path!r}")
            if file_name != PurePosixPath(relative_path).name:
                self.alignment_errors.append(
                    f"file_registry file_name mismatch for {relative_path}: {file_name!r}"
                )
            if extension != PurePosixPath(file_name).suffix:
                self.alignment_errors.append(f"file_registry extension mismatch for {relative_path}: {extension!r}")
            if file_scope_class not in ALLOWED_SCOPE_CLASSES:
                self.alignment_errors.append(
                    f"Invalid file_scope_class for {relative_path}: {file_scope_class!r}"
                )
            if not self._parse_utc(last_verified_utc):
                self.alignment_errors.append(f"Invalid last_verified_utc for {relative_path}: {last_verified_utc!r}")

            if module_id:
                if not MODULE_ID_PATTERN.fullmatch(module_id):
                    self.alignment_errors.append(f"Invalid file_registry.module_id for {relative_path}: {module_id!r}")
                if module_id not in module_ids:
                    self.alignment_errors.append(f"file_registry.module_id not in module catalog for {relative_path}: {module_id}")
                if not assigned_module_name:
                    self.alignment_errors.append(f"assigned_module_name is blank for mapped row {relative_path}")
            else:
                self.readiness_errors.append(f"Blank module_id for {relative_path}")
                if file_scope_class not in BLANK_ALLOWED_SCOPE_CLASSES:
                    self.alignment_errors.append(
                        f"Blank module_id is not allowed for file_scope_class={file_scope_class!r} at {relative_path}"
                    )

            physical_row = physical_file_rows.get(relative_path)
            if physical_row is None:
                self.alignment_errors.append(f"file_registry row missing from physical registry: {relative_path}")
            else:
                if file_id not in physical_file_ids or file_id != physical_row.get("file_id", ""):
                    self.alignment_errors.append(
                        f"file_registry.file_id mismatch against physical registry for {relative_path}"
                    )
                if directory_id not in physical_directory_ids or directory_id != physical_row.get("parent_directory_id", ""):
                    self.alignment_errors.append(
                        f"file_registry.directory_id mismatch against physical registry for {relative_path}"
                    )

            parsed_step_ids = [step_id for step_id in process_steps_value.split(";") if step_id]
            for step_id in parsed_step_ids:
                if not PROCESS_STEP_ID_PATTERN.fullmatch(step_id):
                    self.alignment_errors.append(f"Invalid process_steps entry for {relative_path}: {step_id!r}")
                if step_id not in process_step_ids:
                    self.alignment_errors.append(
                        f"file_registry.process_steps entry not found in process_step_catalog for {relative_path}: {step_id}"
                    )
            if parsed_step_ids and module_id:
                bound_step_numbers = {
                    int(step.get("step_number"))
                    for step in process_steps
                    if str(step.get("process_step_id", "")) in parsed_step_ids
                }
                if not bound_step_numbers.issubset(module_bindings.get(module_id, set())):
                    self.alignment_errors.append(
                        f"module_catalog.process_bindings missing step linkage for {relative_path}"
                    )

    def _compute_semantic_coverage(self, file_registry_rows: list[dict[str, str]]) -> float:
        relevant_rows = [
            row
            for row in file_registry_rows
            if row.get("file_scope_class") != "out_of_scope"
        ]
        if not relevant_rows:
            return 0.0
        covered_rows = [
            row
            for row in relevant_rows
            if (row.get("module_id") or "").strip()
        ]
        return round((len(covered_rows) / len(relevant_rows)) * 100, 2)

    def _build_report(
        self,
        *,
        physical_status: str,
        alignment_status: str,
        readiness_status: str,
        semantic_coverage_pct: float,
        file_registry_rows: list[dict[str, str]],
        module_catalog: dict[str, Any],
        process_catalog: dict[str, Any],
        process_source_path: Path | None,
    ) -> dict[str, Any]:
        return {
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "physical_status": physical_status,
            "alignment_status": alignment_status,
            "readiness_status": readiness_status,
            "semantic_coverage_pct": semantic_coverage_pct,
            "counts": {
                "file_registry_rows": len(file_registry_rows),
                "module_count": len(module_catalog.get("modules", [])),
                "process_step_count": len(process_catalog.get("steps", [])),
            },
            "paths": {
                "file_registry": str(self.file_registry_path),
                "module_catalog": str(self.module_catalog_path),
                "process_step_catalog": str(self.process_step_catalog_path),
                "module_schema": str(self.module_schema_path),
                "identifier_map": str(self.identifier_map_path),
                "physical_registry": str(self.physical_registry_path),
                "process_source": str(process_source_path) if process_source_path else "",
            },
            "info": self.info,
            "warnings": self.warnings,
            "physical_errors": self.physical_errors,
            "alignment_errors": self.alignment_errors,
            "readiness_errors": self.readiness_errors,
        }

    def _write_markdown_report(self, report: dict[str, Any]) -> None:
        lines = [
            "# Three-Artifact Alignment Validation Report",
            "",
            f"Generated: {report['generated_at_utc']}",
            "",
            "## Status",
            "",
            f"- physical_status: {report['physical_status']}",
            f"- alignment_status: {report['alignment_status']}",
            f"- readiness_status: {report['readiness_status']}",
            f"- semantic_coverage_pct: {report['semantic_coverage_pct']}",
            "",
            "## Counts",
            "",
            f"- file_registry_rows: {report['counts']['file_registry_rows']}",
            f"- module_count: {report['counts']['module_count']}",
            f"- process_step_count: {report['counts']['process_step_count']}",
            "",
            "## Paths",
            "",
        ]
        lines.extend(f"- {key}: `{value}`" for key, value in report["paths"].items() if value)
        for title, items in [
            ("Info", report["info"]),
            ("Warnings", report["warnings"]),
            ("Physical Errors", report["physical_errors"]),
            ("Alignment Errors", report["alignment_errors"]),
            ("Readiness Errors", report["readiness_errors"]),
        ]:
            lines.extend(["", f"## {title}", ""])
            if items:
                lines.extend(f"- {item}" for item in items)
            else:
                lines.append("- None")
        lines.append("")
        self.markdown_report_path.write_text("\n".join(lines), encoding="utf-8")

    def _print_summary(self, report: dict[str, Any]) -> None:
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"physical_status: {report['physical_status']}")
        print(f"alignment_status: {report['alignment_status']}")
        print(f"readiness_status: {report['readiness_status']}")
        print(f"semantic_coverage_pct: {report['semantic_coverage_pct']}")
        print(f"warnings: {len(report['warnings'])}")
        print(
            "errors: "
            f"{len(report['physical_errors']) + len(report['alignment_errors']) + len(report['readiness_errors'])}"
        )
        print(f"report: {self.markdown_report_path}")


if __name__ == "__main__":
    validator = ArtifactValidator(Path(__file__).resolve().parent)
    success, _report = validator.validate_all()
    raise SystemExit(0 if success else 1)

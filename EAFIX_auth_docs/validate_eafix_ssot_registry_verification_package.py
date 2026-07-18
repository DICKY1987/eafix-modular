#!/usr/bin/env python3
"""
Validate the EAFIX SSOT registry delivery verification package or a run bundle.

Python: 3.9+
Dependency: jsonschema >= 4.18

JSON Schema validates individual document shape. This validator adds the
cross-file semantic checks that JSON Schema cannot express: target bindings,
counts, unique IDs, JSON Pointer resolution, graph order, obligation/check
coverage, evidence reference integrity, file hashes, freshness, sealing, and
final-status consistency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "jsonschema is required. Install with: python -m pip install 'jsonschema>=4.18'"
    ) from exc


PLAN_NAME = "EAFIX_SSOT_REGISTRY_SYSTEM_FINAL_MERGED_IMPLEMENTATION_PLAN_v2_0_0.json"
SPEC_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_SPEC_v1_0_0.json"
SPEC_SCHEMA_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_SPEC.schema.json"
MATRIX_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_OBLIGATION_MATRIX.generated.json"
CHECKLIST_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_CHECKLIST.generated.md"
EVIDENCE_TEMPLATE_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_EVIDENCE_MANIFEST.json"
REPORT_TEMPLATE_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_REPORT.json"
EVIDENCE_SCHEMA_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_EVIDENCE_MANIFEST.schema.json"
REPORT_SCHEMA_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_REPORT.schema.json"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass
class Finding:
    code: str
    message: str
    path: Optional[str] = None
    severity: str = "error"

    def as_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.path is not None:
            result["path"] = self.path
        return result


@dataclass
class ValidationResult:
    findings: List[Finding] = field(default_factory=list)
    checks_run: int = 0

    def add(
        self,
        code: str,
        message: str,
        path: Optional[str] = None,
        severity: str = "error",
    ) -> None:
        self.findings.append(Finding(code, message, path, severity))

    def check(self, condition: bool, code: str, message: str, path: Optional[str] = None) -> None:
        self.checks_run += 1
        if not condition:
            self.add(code, message, path)

    @property
    def errors(self) -> List[Finding]:
        return [item for item in self.findings if item.severity == "error"]

    @property
    def warnings(self) -> List[Finding]:
        return [item for item in self.findings if item.severity == "warning"]


def load_json(path: Path, result: ValidationResult) -> Optional[Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result.add("FILE_MISSING", "Required file is missing.", str(path))
    except json.JSONDecodeError as exc:
        result.add(
            "JSON_INVALID",
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            str(path),
        )
    except OSError as exc:
        result.add("FILE_READ_ERROR", str(exc), str(path))
    return None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise KeyError(pointer)
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(pointer)
    return current


def validate_json_schema(
    instance: Any,
    schema: Any,
    instance_path: Path,
    schema_path: Path,
    result: ValidationResult,
) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        result.add("SCHEMA_INVALID", str(exc), str(schema_path))
        return
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )
    result.checks_run += 1
    for error in errors:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        result.add(
            "SCHEMA_INSTANCE_INVALID",
            error.message,
            f"{instance_path}{pointer}",
        )


def collect_spec_ids(spec: Mapping[str, Any]) -> Tuple[List[str], List[str], List[str]]:
    gate_ids: List[str] = []
    check_ids: List[str] = []
    phase_refs: List[str] = []
    for gate in spec["verification_gates"]:
        gate_ids.append(gate["gate_id"])
        phase_refs.extend(gate.get("phase_refs", []))
        for check in gate["checks"]:
            check_ids.append(check["check_id"])
            phase_refs.extend(check.get("phase_refs", []))
    return gate_ids, check_ids, phase_refs


def validate_spec_semantics(
    *,
    root: Path,
    plan: Mapping[str, Any],
    spec: Mapping[str, Any],
    result: ValidationResult,
) -> None:
    plan_path = root / PLAN_NAME
    gate_ids, check_ids, phase_refs = collect_spec_ids(spec)
    rule_ids = [rule["rule_id"] for rule in spec["semantic_validation_rules"]]
    control_ids = [
        control["control_id"] for control in spec["anti_false_completion_controls"]
    ]
    obligation_rule_ids = [
        rule["rule_id"]
        for rule in spec["plan_obligation_inventory"]["obligation_generation_rules"]
    ]

    for name, values in [
        ("gate_id", gate_ids),
        ("check_id", check_ids),
        ("semantic rule ID", rule_ids),
        ("anti-false-completion control ID", control_ids),
        ("obligation-generation rule ID", obligation_rule_ids),
    ]:
        result.check(
            len(values) == len(set(values)),
            "SEM_001_DUPLICATE_ID",
            f"{name} values must be unique.",
            SPEC_NAME,
        )

    gate_order = {gate["gate_id"]: gate["order"] for gate in spec["verification_gates"]}
    orders = list(gate_order.values())
    result.check(
        sorted(orders) == list(range(len(orders))),
        "SEM_003_GATE_ORDER",
        "Gate order must be unique and contiguous from 0.",
        SPEC_NAME,
    )
    for gate in spec["verification_gates"]:
        for dependency in gate["depends_on"]:
            result.check(
                dependency in gate_order and gate_order[dependency] < gate["order"],
                "SEM_002_GATE_DEPENDENCY",
                f"{gate['gate_id']} dependency {dependency} must resolve to an earlier gate.",
                SPEC_NAME,
            )

    phase_ids = {phase["phase_id"] for phase in plan["phases"]}
    for phase_ref in phase_refs:
        result.check(
            phase_ref in phase_ids,
            "SEM_004_PHASE_REF",
            f"Unknown phase reference: {phase_ref}",
            SPEC_NAME,
        )

    expected_counts = spec["plan_obligation_inventory"]["expected_counts"]
    result.check(
        sum(expected_counts.values())
        == spec["plan_obligation_inventory"]["expected_total_obligations"],
        "SEM_006_COUNT_SUM",
        "Expected obligation counts do not sum to expected_total_obligations.",
        SPEC_NAME,
    )

    extracted_counts = {
        "source_entries": len(plan["source_plan_consolidation"]["sources"]),
        "phases": len(plan["phases"]),
        "tasks": sum(len(phase["tasks"]) for phase in plan["phases"]),
        "task_acceptance_clauses": sum(
            len(task.get("acceptance", []))
            for phase in plan["phases"]
            for task in phase["tasks"]
        ),
        "task_outputs": sum(
            len(task.get("outputs", []))
            for phase in plan["phases"]
            for task in phase["tasks"]
        ),
        "task_evidence_requirements": sum(
            len(task.get("evidence_required", []))
            for phase in plan["phases"]
            for task in phase["tasks"]
        ),
        "phase_exit_gates": len(plan["phases"]),
        "phase_exit_gate_conditions": sum(
            len(phase["exit_gate"]["pass_condition"]) for phase in plan["phases"]
        ),
        "validation_rules": len(plan["validation_catalog"]),
        "human_decisions": len(plan["human_decision_register"]),
        "write_scopes": len(plan["write_scopes"]),
        "definition_of_done_criteria": len(plan["definition_of_done"]),
        "global_constraints": len(plan["global_constraints"]),
        "failure_conditions": len(
            plan["failure_handling"]["global_fail_closed_conditions"]
        ),
        "agent_execution_rules": sum(
            len(plan["agent_execution_contract"][key])
            for key in ["before_each_task", "during_each_task", "after_each_task"]
        ),
    }
    result.check(
        extracted_counts == expected_counts,
        "SEM_007_EXTRACTED_COUNTS",
        "Counts extracted from the target plan do not equal specification expected_counts.",
        SPEC_NAME,
    )

    verdicts = [
        item["verdict"]
        for item in spec["verdict_taxonomy"]["allowed_verdicts"]
    ]
    evidence_types = set(spec["evidence_contract"]["evidence_types"])
    for gate in spec["verification_gates"]:
        for check in gate["checks"]:
            check_path = f"{SPEC_NAME}:{check['check_id']}"
            if check["severity"] in {"blocker", "high"}:
                result.check(
                    check["fail_closed"] is True,
                    "SEM_008_FAIL_CLOSED",
                    "Blocker/high checks must be fail_closed.",
                    check_path,
                )
                result.check(
                    len(check["required_evidence"]) > 0,
                    "SEM_008_EVIDENCE_REQUIRED",
                    "Blocker/high checks require evidence.",
                    check_path,
                )
            result.check(
                len(check["requirement_sources"]) > 0
                and len(check["procedure"]) > 0
                and len(check["expected_results"]) > 0
                and bool(check["remediation_on_fail"]),
                "SEM_009_CHECK_COMPLETENESS",
                "Each check needs sources, procedure, expected results, and remediation.",
                check_path,
            )
            result.check(
                check["allowed_verdicts"] == verdicts,
                "SEM_014_VERDICT_TAXONOMY",
                "Check verdicts differ from the closed verdict taxonomy.",
                check_path,
            )
            for evidence in check["required_evidence"]:
                result.check(
                    evidence["evidence_type"] in evidence_types,
                    "SEM_013_EVIDENCE_TYPE",
                    f"Unknown evidence type: {evidence['evidence_type']}",
                    check_path,
                )
            if check["control_type"] == "enforcement":
                negative = check.get("negative_test")
                result.check(
                    isinstance(negative, dict) and negative.get("required") is True,
                    "SEM_015_NEGATIVE_TEST",
                    "Enforcement controls require a negative test.",
                    check_path,
                )

    package_orders = [
        item["package_order"] for item in spec["required_package_artifacts"]
    ]
    package_paths = [item["path"] for item in spec["required_package_artifacts"]]
    result.check(
        len(package_orders) == len(set(package_orders))
        and len(package_paths) == len(set(package_paths)),
        "SEM_010_PACKAGE_UNIQUENESS",
        "Required package artifact paths/orders must be unique.",
        SPEC_NAME,
    )

    target = spec["target_plan"]
    observed = {
        "plan_id": plan.get("plan_id"),
        "plan_version": plan.get("plan_version"),
        "filename": plan_path.name,
        "sha256": sha256_file(plan_path),
        "byte_size": plan_path.stat().st_size,
    }
    expected = {
        "plan_id": target["plan_id"],
        "plan_version": target["plan_version"],
        "filename": target["filename"],
        "sha256": target["sha256"],
        "byte_size": target["byte_size"],
    }
    result.check(
        observed == expected,
        "SEM_012_TARGET_BINDING",
        f"Target binding mismatch: expected {expected}, observed {observed}",
        PLAN_NAME,
    )


def validate_matrix(
    *,
    root: Path,
    plan: Mapping[str, Any],
    spec: Mapping[str, Any],
    matrix: Mapping[str, Any],
    result: ValidationResult,
) -> Tuple[Set[str], Set[str]]:
    gate_ids, check_ids_list, _ = collect_spec_ids(spec)
    check_ids = set(check_ids_list)
    obligation_records = matrix.get("obligations", [])
    expected_total = spec["plan_obligation_inventory"]["expected_total_obligations"]

    result.check(
        len(obligation_records) == expected_total,
        "MATRIX_COUNT",
        f"Matrix has {len(obligation_records)} obligations; expected {expected_total}.",
        MATRIX_NAME,
    )
    obligation_ids_list = [record.get("obligation_id") for record in obligation_records]
    result.check(
        len(obligation_ids_list) == len(set(obligation_ids_list)),
        "MATRIX_DUPLICATE_OBLIGATION_ID",
        "Obligation IDs must be unique.",
        MATRIX_NAME,
    )
    obligation_ids = set(obligation_ids_list)

    invalid_pointers = 0
    unmapped = 0
    unknown_check_refs: Set[str] = set()
    category_counts: Counter[str] = Counter()
    calculated_check_coverage: Dict[str, List[str]] = defaultdict(list)

    for record in obligation_records:
        obligation_id = record.get("obligation_id", "<missing>")
        category_counts[record.get("source_class")] += 1
        pointer = record.get("source_pointer")
        try:
            resolved = resolve_json_pointer(plan, pointer)
            if resolved != record.get("source_value_snapshot"):
                result.add(
                    "MATRIX_SOURCE_SNAPSHOT",
                    "Source snapshot differs from target plan.",
                    f"{MATRIX_NAME}:{obligation_id}",
                )
        except Exception:
            invalid_pointers += 1
            result.add(
                "MATRIX_POINTER",
                f"Source pointer does not resolve: {pointer}",
                f"{MATRIX_NAME}:{obligation_id}",
            )
        mapped = record.get("mapped_check_ids", [])
        if not mapped:
            unmapped += 1
        for check_id in mapped:
            if check_id not in check_ids:
                unknown_check_refs.add(check_id)
            else:
                calculated_check_coverage[check_id].append(obligation_id)

    result.check(
        invalid_pointers == 0,
        "MATRIX_POINTER_TOTAL",
        f"Matrix contains {invalid_pointers} invalid source pointers.",
        MATRIX_NAME,
    )
    result.check(
        unmapped == 0,
        "MATRIX_UNMAPPED_TOTAL",
        f"Matrix contains {unmapped} unmapped obligations.",
        MATRIX_NAME,
    )
    result.check(
        not unknown_check_refs,
        "MATRIX_UNKNOWN_CHECKS",
        f"Matrix references unknown checks: {sorted(unknown_check_refs)}",
        MATRIX_NAME,
    )

    expected_counts = spec["plan_obligation_inventory"]["expected_counts"]
    expected_by_class = {
        "source_entry": expected_counts["source_entries"],
        "phase": expected_counts["phases"],
        "task": expected_counts["tasks"],
        "task_acceptance_clause": expected_counts["task_acceptance_clauses"],
        "task_output": expected_counts["task_outputs"],
        "task_evidence_requirement": expected_counts["task_evidence_requirements"],
        "phase_exit_gate": expected_counts["phase_exit_gates"],
        "phase_exit_gate_condition": expected_counts["phase_exit_gate_conditions"],
        "validation_rule": expected_counts["validation_rules"],
        "human_decision": expected_counts["human_decisions"],
        "write_scope": expected_counts["write_scopes"],
        "definition_of_done": expected_counts["definition_of_done_criteria"],
        "global_constraint": expected_counts["global_constraints"],
        "failure_condition": expected_counts["failure_conditions"],
        "agent_execution_rule": expected_counts["agent_execution_rules"],
    }
    result.check(
        dict(category_counts) == expected_by_class,
        "MATRIX_CATEGORY_COUNTS",
        f"Matrix category counts differ: {dict(category_counts)}",
        MATRIX_NAME,
    )

    index_rows = matrix.get("check_coverage_index", [])
    index_ids = [row.get("check_id") for row in index_rows]
    result.check(
        len(index_ids) == len(check_ids) and set(index_ids) == check_ids,
        "MATRIX_CHECK_INDEX",
        "Check coverage index must contain every check exactly once.",
        MATRIX_NAME,
    )
    for row in index_rows:
        check_id = row["check_id"]
        observed_ids = row.get("mapped_obligation_ids", [])
        expected_ids = calculated_check_coverage.get(check_id, [])
        result.check(
            observed_ids == expected_ids
            and row.get("mapped_obligation_count") == len(expected_ids),
            "MATRIX_CHECK_INDEX_CONTENT",
            f"Check coverage index differs for {check_id}.",
            f"{MATRIX_NAME}:{check_id}",
        )

    summary = matrix.get("coverage_summary", {})
    result.check(
        summary.get("coverage_percent") == 100.0
        and summary.get("unmapped_obligations") == 0
        and summary.get("invalid_source_pointers") == 0
        and summary.get("duplicate_obligation_ids") == 0,
        "MATRIX_COVERAGE_SUMMARY",
        "Matrix coverage summary is not a clean 100% result.",
        MATRIX_NAME,
    )
    return obligation_ids, check_ids


def validate_checklist(
    *,
    root: Path,
    spec: Mapping[str, Any],
    result: ValidationResult,
) -> None:
    path = root / CHECKLIST_NAME
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        result.add("CHECKLIST_READ", str(exc), str(path))
        return
    gate_ids, check_ids, _ = collect_spec_ids(spec)
    for identifier in gate_ids + check_ids:
        result.check(
            identifier in text,
            "CHECKLIST_ID_MISSING",
            f"Checklist does not contain {identifier}.",
            CHECKLIST_NAME,
        )
    for expected_hash in [
        spec["target_plan"]["sha256"],
        sha256_file(root / SPEC_NAME),
    ]:
        result.check(
            expected_hash in text,
            "CHECKLIST_BINDING_HASH",
            f"Checklist does not contain binding hash {expected_hash}.",
            CHECKLIST_NAME,
        )


def validate_package(root: Path, result: ValidationResult) -> Optional[Dict[str, Any]]:
    paths = {
        "plan": root / PLAN_NAME,
        "spec": root / SPEC_NAME,
        "spec_schema": root / SPEC_SCHEMA_NAME,
        "matrix": root / MATRIX_NAME,
        "evidence": root / EVIDENCE_TEMPLATE_NAME,
        "report": root / REPORT_TEMPLATE_NAME,
        "evidence_schema": root / EVIDENCE_SCHEMA_NAME,
        "report_schema": root / REPORT_SCHEMA_NAME,
    }
    docs = {name: load_json(path, result) for name, path in paths.items()}
    if any(value is None for value in docs.values()):
        return None

    validate_json_schema(
        docs["spec"], docs["spec_schema"], paths["spec"], paths["spec_schema"], result
    )
    validate_spec_semantics(root=root, plan=docs["plan"], spec=docs["spec"], result=result)
    obligation_ids, check_ids = validate_matrix(
        root=root,
        plan=docs["plan"],
        spec=docs["spec"],
        matrix=docs["matrix"],
        result=result,
    )
    validate_checklist(root=root, spec=docs["spec"], result=result)
    validate_json_schema(
        docs["evidence"],
        docs["evidence_schema"],
        paths["evidence"],
        paths["evidence_schema"],
        result,
    )
    validate_json_schema(
        docs["report"],
        docs["report_schema"],
        paths["report"],
        paths["report_schema"],
        result,
    )

    # Template false-completion safety.
    result.check(
        docs["evidence"]["document_state"] == "unexecuted_template"
        and docs["evidence"]["seal"]["seal_state"] == "unsealed"
        and not docs["evidence"]["evidence_records"],
        "EVIDENCE_TEMPLATE_STATE",
        "Evidence template must be unexecuted, unsealed, and empty.",
        EVIDENCE_TEMPLATE_NAME,
    )
    check_verdicts = [
        check["verdict"]
        for gate in docs["report"]["gate_results"]
        for check in gate["check_results"]
    ]
    result.check(
        docs["report"]["document_state"] == "unexecuted_template"
        and docs["report"]["report_status"] == "not_run"
        and docs["report"]["final_status"] is None
        and all(value is None for value in check_verdicts)
        and all(
            row["resolution_status"] == "not_run"
            for row in docs["report"]["obligation_results"]
        ),
        "REPORT_TEMPLATE_STATE",
        "Report template contains an execution result or completion claim.",
        REPORT_TEMPLATE_NAME,
    )

    # Exact immutable package bindings in both templates.
    expected_bindings = {
        binding["artifact_role"]: (
            binding["path"],
            binding["sha256"],
            binding["byte_size"],
        )
        for binding in docs["evidence"]["immutable_package_bindings"]
    }
    report_bindings = {
        binding["artifact_role"]: (
            binding["path"],
            binding["sha256"],
            binding["byte_size"],
        )
        for binding in docs["report"]["immutable_package_bindings"]
    }
    result.check(
        expected_bindings == report_bindings,
        "TEMPLATE_BINDINGS_DIFFER",
        "Evidence/report immutable bindings differ.",
    )
    for role, (filename, expected_hash, expected_size) in expected_bindings.items():
        artifact_path = root / filename
        result.check(
            artifact_path.exists(),
            "BOUND_ARTIFACT_MISSING",
            f"Bound artifact is missing for role {role}: {filename}",
            filename,
        )
        if artifact_path.exists():
            result.check(
                sha256_file(artifact_path) == expected_hash
                and artifact_path.stat().st_size == expected_size,
                "BOUND_ARTIFACT_HASH",
                f"Bound artifact hash/size differs for role {role}.",
                filename,
            )

    return {
        "plan": docs["plan"],
        "spec": docs["spec"],
        "matrix": docs["matrix"],
        "obligation_ids": obligation_ids,
        "check_ids": check_ids,
        "evidence_schema": docs["evidence_schema"],
        "report_schema": docs["report_schema"],
    }


def resolve_evidence_path(run_root: Path, path_or_uri: str) -> Optional[Path]:
    parsed = urlparse(path_or_uri)
    if parsed.scheme and parsed.scheme not in {"file"}:
        return None
    path = Path(parsed.path if parsed.scheme == "file" else path_or_uri)
    if not path.is_absolute():
        path = run_root / path
    try:
        resolved = path.resolve()
        run_resolved = run_root.resolve()
        resolved.relative_to(run_resolved)
    except (ValueError, OSError):
        return None
    return resolved


def validate_run(
    *,
    package_root: Path,
    run_root: Path,
    package: Mapping[str, Any],
    result: ValidationResult,
) -> None:
    evidence_path = run_root / "verification_evidence_manifest.json"
    report_path = run_root / "verification_report.json"
    evidence = load_json(evidence_path, result)
    report = load_json(report_path, result)
    if evidence is None or report is None:
        return

    validate_json_schema(
        evidence,
        package["evidence_schema"],
        evidence_path,
        package_root / EVIDENCE_SCHEMA_NAME,
        result,
    )
    validate_json_schema(
        report,
        package["report_schema"],
        report_path,
        package_root / REPORT_SCHEMA_NAME,
        result,
    )

    obligation_ids: Set[str] = set(package["obligation_ids"])
    check_ids: Set[str] = set(package["check_ids"])
    evidence_records = evidence.get("evidence_records", [])
    evidence_ids_list = [record.get("evidence_id") for record in evidence_records]
    result.check(
        len(evidence_ids_list) == len(set(evidence_ids_list)),
        "RUN_DUPLICATE_EVIDENCE_ID",
        "Evidence IDs must be unique.",
        str(evidence_path),
    )
    evidence_by_id = {
        record["evidence_id"]: record
        for record in evidence_records
        if isinstance(record.get("evidence_id"), str)
    }
    requirement_ids = {
        row["requirement_id"] for row in evidence["evidence_requirements"]
    }

    run_context = evidence["run_context"]
    report_context = report["run_context"]
    for field in ["run_id", "target_branch", "target_commit_sha", "verifier_identity"]:
        result.check(
            run_context.get(field) == report_context.get(field),
            "RUN_CONTEXT_MISMATCH",
            f"Evidence/report run_context differs for {field}.",
        )
    result.check(
        run_context.get("run_context_status") == "frozen"
        and report_context.get("run_context_status") == "frozen",
        "RUN_CONTEXT_NOT_FROZEN",
        "Run context must be frozen.",
    )

    fresh_count = stale_count = unverifiable_count = hash_failures = 0
    for record in evidence_records:
        evidence_id = record.get("evidence_id", "<missing>")
        result.check(
            record.get("check_id") in check_ids,
            "RUN_UNKNOWN_CHECK_REF",
            f"{evidence_id} references unknown check {record.get('check_id')}.",
        )
        unknown_obligations = set(record.get("obligation_ids", [])) - obligation_ids
        result.check(
            not unknown_obligations,
            "RUN_UNKNOWN_OBLIGATION_REF",
            f"{evidence_id} references unknown obligations {sorted(unknown_obligations)}.",
        )
        unknown_requirements = set(record.get("requirement_ids", [])) - requirement_ids
        result.check(
            not unknown_requirements,
            "RUN_UNKNOWN_REQUIREMENT_REF",
            f"{evidence_id} references unknown requirements {sorted(unknown_requirements)}.",
        )
        result.check(
            record.get("target_commit_sha") == run_context.get("target_commit_sha"),
            "RUN_EVIDENCE_COMMIT",
            f"{evidence_id} is not bound to the frozen target commit.",
        )
        result.check(
            record.get("target_plan_sha256") == package["spec"]["target_plan"]["sha256"],
            "RUN_EVIDENCE_PLAN_HASH",
            f"{evidence_id} target-plan hash differs.",
        )
        result.check(
            record.get("verification_spec_sha256")
            == sha256_file(package_root / SPEC_NAME),
            "RUN_EVIDENCE_SPEC_HASH",
            f"{evidence_id} verification-spec hash differs.",
        )
        result.check(
            record.get("obligation_matrix_sha256")
            == sha256_file(package_root / MATRIX_NAME),
            "RUN_EVIDENCE_MATRIX_HASH",
            f"{evidence_id} matrix hash differs.",
        )

        freshness = record.get("freshness_status")
        if freshness == "fresh":
            fresh_count += 1
        elif freshness == "stale":
            stale_count += 1
        else:
            unverifiable_count += 1

        resolved_path = resolve_evidence_path(run_root, record.get("path_or_uri", ""))
        if resolved_path is not None:
            if not resolved_path.exists() or not resolved_path.is_file():
                result.add(
                    "RUN_EVIDENCE_FILE_MISSING",
                    "Evidence file is missing.",
                    f"{evidence_id}:{resolved_path}",
                )
                hash_failures += 1
            else:
                observed_hash = sha256_file(resolved_path)
                if observed_hash != record.get("sha256"):
                    result.add(
                        "RUN_EVIDENCE_HASH",
                        f"Evidence hash differs: observed {observed_hash}.",
                        evidence_id,
                    )
                    hash_failures += 1
                if record.get("byte_size") is not None:
                    result.check(
                        resolved_path.stat().st_size == record["byte_size"],
                        "RUN_EVIDENCE_SIZE",
                        f"{evidence_id} byte_size differs.",
                    )
        elif record.get("integrity_status") != "verified":
            result.add(
                "RUN_EXTERNAL_EVIDENCE_UNVERIFIED",
                "External evidence URI must have verified integrity.",
                evidence_id,
            )

    # Requirement and index reference resolution.
    for requirement in evidence["evidence_requirements"]:
        unknown = set(requirement.get("satisfying_evidence_ids", [])) - set(evidence_by_id)
        result.check(
            not unknown,
            "RUN_REQUIREMENT_EVIDENCE_REF",
            f"{requirement['requirement_id']} references missing evidence {sorted(unknown)}.",
        )
        if requirement["satisfaction_status"] == "satisfied":
            records = [
                evidence_by_id[evidence_id]
                for evidence_id in requirement["satisfying_evidence_ids"]
                if evidence_id in evidence_by_id
            ]
            result.check(
                len(records) >= requirement["minimum_count"],
                "RUN_REQUIREMENT_MINIMUM",
                f"{requirement['requirement_id']} does not meet minimum_count.",
            )
            if requirement["freshness_required"]:
                result.check(
                    all(record["freshness_status"] == "fresh" for record in records),
                    "RUN_REQUIREMENT_FRESHNESS",
                    f"{requirement['requirement_id']} uses non-fresh evidence.",
                )

    # Report IDs and reference resolution.
    report_gate_ids = [gate["gate_id"] for gate in report["gate_results"]]
    spec_gate_ids = [
        gate["gate_id"] for gate in package["spec"]["verification_gates"]
    ]
    result.check(
        report_gate_ids == spec_gate_ids,
        "RUN_REPORT_GATE_IDS",
        "Report gate IDs/order differ from specification.",
    )
    report_check_ids = [
        check["check_id"]
        for gate in report["gate_results"]
        for check in gate["check_results"]
    ]
    result.check(
        report_check_ids
        == [
            check["check_id"]
            for gate in package["spec"]["verification_gates"]
            for check in gate["checks"]
        ],
        "RUN_REPORT_CHECK_IDS",
        "Report check IDs/order differ from specification.",
    )
    report_obligation_ids = [
        row["obligation_id"] for row in report["obligation_results"]
    ]
    result.check(
        report_obligation_ids
        == [row["obligation_id"] for row in package["matrix"]["obligations"]],
        "RUN_REPORT_OBLIGATION_IDS",
        "Report obligation IDs/order differ from matrix.",
    )

    all_report_evidence_refs: Set[str] = set()
    for gate in report["gate_results"]:
        all_report_evidence_refs.update(gate.get("gate_evidence_ids", []))
        decision_id = gate.get("gate_decision_evidence_id")
        if decision_id:
            all_report_evidence_refs.add(decision_id)
        for check in gate["check_results"]:
            all_report_evidence_refs.update(check.get("evidence_ids", []))
            all_report_evidence_refs.update(check.get("fresh_evidence_ids", []))
            all_report_evidence_refs.update(
                check.get("stale_or_unverifiable_evidence_ids", [])
            )
            all_report_evidence_refs.update(
                check.get("negative_test", {}).get("evidence_ids", [])
            )
            approval_id = check.get("not_applicable_approval_evidence_id")
            if approval_id:
                all_report_evidence_refs.add(approval_id)
            if check.get("verdict") == "pass":
                result.check(
                    bool(check.get("fresh_evidence_ids"))
                    and not check.get("stale_or_unverifiable_evidence_ids"),
                    "RUN_PASS_EVIDENCE",
                    f"{check['check_id']} pass lacks clean fresh evidence.",
                )
    for row in report["obligation_results"]:
        all_report_evidence_refs.update(row.get("evidence_ids", []))
        approval_id = row.get("not_applicable_approval_evidence_id")
        if approval_id:
            all_report_evidence_refs.add(approval_id)
    unknown_report_refs = all_report_evidence_refs - set(evidence_by_id)
    result.check(
        not unknown_report_refs,
        "RUN_REPORT_EVIDENCE_REFS",
        f"Report references missing evidence IDs: {sorted(unknown_report_refs)}",
    )

    # Count arithmetic.
    gate_verdicts = Counter(
        gate["gate_verdict"] if gate["gate_verdict"] is not None else "not_run"
        for gate in report["gate_results"]
    )
    check_verdicts = Counter(
        check["verdict"] if check["verdict"] is not None else "not_run"
        for gate in report["gate_results"]
        for check in gate["check_results"]
    )
    obligation_statuses = Counter(
        row["resolution_status"] for row in report["obligation_results"]
    )
    summary = report["coverage_summary"]
    arithmetic = {
        "gates_passed": gate_verdicts["pass"],
        "gates_failed": gate_verdicts["fail"],
        "gates_blocked": gate_verdicts["blocked"],
        "gates_not_run": gate_verdicts["not_run"],
        "checks_passed": check_verdicts["pass"],
        "checks_failed": check_verdicts["fail"],
        "checks_blocked": check_verdicts["blocked"],
        "checks_not_applicable": check_verdicts["not_applicable"],
        "checks_not_run": check_verdicts["not_run"],
        "obligations_satisfied": obligation_statuses["satisfied"],
        "obligations_failed": obligation_statuses["failed"],
        "obligations_blocked": obligation_statuses["blocked"],
        "obligations_not_applicable": obligation_statuses["not_applicable"],
        "obligations_not_run": obligation_statuses["not_run"],
    }
    for field, expected in arithmetic.items():
        result.check(
            summary.get(field) == expected,
            "RUN_SUMMARY_ARITHMETIC",
            f"coverage_summary.{field} is {summary.get(field)}, expected {expected}.",
        )

    # Completion and sealing.
    final_status = report.get("final_status")
    if final_status == "verified_complete":
        result.check(
            report["evidence_manifest_binding"]["seal_state"] == "sealed"
            and evidence["seal"]["seal_state"] == "sealed",
            "RUN_COMPLETE_UNSEALED",
            "verified_complete requires a sealed evidence manifest.",
        )
        result.check(
            gate_verdicts["pass"] == len(report["gate_results"])
            and check_verdicts["fail"] == 0
            and check_verdicts["blocked"] == 0
            and check_verdicts["not_run"] == 0
            and obligation_statuses["failed"] == 0
            and obligation_statuses["blocked"] == 0
            and obligation_statuses["not_run"] == 0,
            "RUN_COMPLETE_COUNTS",
            "verified_complete has unresolved gate/check/obligation results.",
        )
        result.check(
            report["executive_summary"]["completion_claim_supported"] is True,
            "RUN_COMPLETE_CLAIM",
            "verified_complete must explicitly support the completion claim.",
        )
        result.check(
            report["approvals"]["owner_completion_decision"]["decision"] == "approve",
            "RUN_COMPLETE_APPROVAL",
            "verified_complete requires owner approval.",
        )
        result.check(
            hash_failures == 0 and stale_count == 0 and unverifiable_count == 0,
            "RUN_COMPLETE_EVIDENCE_INTEGRITY",
            "verified_complete requires clean evidence integrity/freshness.",
        )

    # Sealed manifest consistency.
    if evidence["seal"]["seal_state"] == "sealed":
        result.check(
            evidence["seal"]["sealed_target_commit_sha"]
            == run_context["target_commit_sha"],
            "RUN_SEAL_COMMIT",
            "Seal target commit differs from frozen run commit.",
        )
        result.check(
            evidence["seal"]["record_count_at_seal"] == len(evidence_records),
            "RUN_SEAL_RECORD_COUNT",
            "Seal record count differs from evidence record count.",
        )

    # Collection summary basic arithmetic.
    collection = evidence["collection_summary"]
    result.check(
        collection["evidence_records_collected"] == len(evidence_records),
        "RUN_COLLECTION_COUNT",
        "Evidence collection count differs from evidence_records length.",
    )
    result.check(
        collection["fresh_evidence_records"] == fresh_count
        and collection["stale_evidence_records"] == stale_count
        and collection["unverifiable_evidence_records"] == unverifiable_count,
        "RUN_COLLECTION_FRESHNESS_COUNTS",
        "Evidence freshness summary differs from evidence records.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Directory containing the verification package.",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Optional run bundle directory. When present, package and run are validated.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional path for a machine-readable validation result.",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Return failure when warnings exist.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    result = ValidationResult()

    package = validate_package(root, result)
    if package is not None and args.run_root is not None:
        validate_run(
            package_root=root,
            run_root=args.run_root.resolve(),
            package=package,
            result=result,
        )

    output = {
        "status": "PASS" if not result.errors else "FAIL",
        "checks_run": result.checks_run,
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "findings": [finding.as_dict() for finding in result.findings],
        "package_root": str(root),
        "run_root": str(args.run_root.resolve()) if args.run_root else None,
    }
    rendered = json.dumps(output, indent=2)
    print(rendered)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered + "\n", encoding="utf-8", newline="\n")

    if result.errors:
        return 1
    if args.warnings_as_errors and result.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

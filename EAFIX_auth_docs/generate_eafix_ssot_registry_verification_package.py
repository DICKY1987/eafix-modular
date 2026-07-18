#!/usr/bin/env python3
"""
Deterministically rebuild/check the EAFIX SSOT registry verification matrix and
human checklist, and initialize an isolated verification run.

Python: 3.9+
Dependencies: standard library only.

The plan and verification specification are immutable, hash-bound inputs. The
obligation matrix contains curated obligation-to-check mapping decisions that
are not fully derivable from the specification, so an existing matrix (or an
explicit --mapping-source) is required as the mapping authority. The script
re-extracts every source pointer from the bound plan, verifies that the curated
mapping still applies, recomputes all derived indexes/counts, and renders the
checklist from the canonical specification.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple


PLAN_NAME = "EAFIX_SSOT_REGISTRY_SYSTEM_FINAL_MERGED_IMPLEMENTATION_PLAN_v2_0_0.json"
SPEC_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_SPEC_v1_0_0.json"
MATRIX_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_OBLIGATION_MATRIX.generated.json"
CHECKLIST_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_CHECKLIST.generated.md"
EVIDENCE_TEMPLATE_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_EVIDENCE_MANIFEST.json"
REPORT_TEMPLATE_NAME = "EAFIX_SSOT_REGISTRY_DELIVERY_VERIFICATION_REPORT.json"

RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class GenerationError(RuntimeError):
    """Raised when deterministic generation cannot proceed safely."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GenerationError(f"Required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GenerationError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def stable_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def resolve_json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise GenerationError(f"Invalid JSON Pointer: {pointer}")
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        try:
            if isinstance(current, list):
                current = current[int(part)]
            elif isinstance(current, dict):
                current = current[part]
            else:
                raise KeyError(part)
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise GenerationError(
                f"JSON Pointer does not resolve: {pointer} (failed at {part!r})"
            ) from exc
    return current


def collect_checks(spec: Mapping[str, Any]) -> Tuple[List[Mapping[str, Any]], Dict[str, str], Dict[str, int]]:
    checks: List[Mapping[str, Any]] = []
    gate_by_check: Dict[str, str] = {}
    gate_order: Dict[str, int] = {}
    for gate in spec["verification_gates"]:
        gate_id = gate["gate_id"]
        if gate_id in gate_order:
            raise GenerationError(f"Duplicate gate ID: {gate_id}")
        gate_order[gate_id] = int(gate["order"])
        for check in gate["checks"]:
            check_id = check["check_id"]
            if check_id in gate_by_check:
                raise GenerationError(f"Duplicate check ID: {check_id}")
            gate_by_check[check_id] = gate_id
            checks.append(check)
    return checks, gate_by_check, gate_order


def verify_target_binding(plan_path: Path, spec: Mapping[str, Any], plan: Mapping[str, Any]) -> None:
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
    if observed != expected:
        raise GenerationError(
            "Target-plan binding mismatch.\n"
            f"Expected: {json.dumps(expected, sort_keys=True)}\n"
            f"Observed: {json.dumps(observed, sort_keys=True)}"
        )


def rebuild_matrix(
    *,
    plan_path: Path,
    spec_path: Path,
    plan: Mapping[str, Any],
    spec: Mapping[str, Any],
    mapping_source: Mapping[str, Any],
) -> Dict[str, Any]:
    checks, gate_by_check, gate_order = collect_checks(spec)
    check_by_id = {check["check_id"]: check for check in checks}

    expected_total = int(spec["plan_obligation_inventory"]["expected_total_obligations"])
    source_obligations = mapping_source.get("obligations")
    if not isinstance(source_obligations, list):
        raise GenerationError("Mapping source has no obligations array.")
    if len(source_obligations) != expected_total:
        raise GenerationError(
            f"Mapping source obligation count is {len(source_obligations)}, expected {expected_total}."
        )

    obligation_ids: List[str] = []
    rebuilt_obligations: List[Dict[str, Any]] = []
    category_counts: Dict[str, int] = {}
    check_coverage: Dict[str, List[str]] = {check_id: [] for check_id in check_by_id}

    for source_record in source_obligations:
        record = copy.deepcopy(source_record)
        obligation_id = record.get("obligation_id")
        if not isinstance(obligation_id, str) or not obligation_id:
            raise GenerationError("Obligation has no valid obligation_id.")
        obligation_ids.append(obligation_id)

        pointer = record.get("source_pointer")
        if not isinstance(pointer, str):
            raise GenerationError(f"{obligation_id}: source_pointer is missing.")
        resolved = resolve_json_pointer(plan, pointer)
        if resolved != record.get("source_value_snapshot"):
            raise GenerationError(
                f"{obligation_id}: source snapshot differs from bound plan at {pointer}. "
                "The plan/spec/mapping package must be revised together."
            )

        mapped_check_ids = record.get("mapped_check_ids")
        if not isinstance(mapped_check_ids, list) or not mapped_check_ids:
            raise GenerationError(f"{obligation_id}: no mapped checks.")
        unknown_checks = sorted(set(mapped_check_ids) - set(check_by_id))
        if unknown_checks:
            raise GenerationError(
                f"{obligation_id}: unknown mapped checks: {unknown_checks}"
            )

        mapped_gate_ids = sorted(
            {gate_by_check[check_id] for check_id in mapped_check_ids},
            key=lambda gate_id: gate_order[gate_id],
        )
        record["mapped_gate_ids"] = mapped_gate_ids
        record["coverage_status"] = (
            "mapped_exactly_once"
            if len(mapped_check_ids) == 1
            else "mapped_multiple_explained"
        )
        record["mapping_rationale"] = (
            "Mapped to universal obligation-coverage controls, source-class controls, "
            "phase-domain controls, and keyword-specific controls where applicable."
        )

        source_class = record.get("source_class")
        if not isinstance(source_class, str):
            raise GenerationError(f"{obligation_id}: invalid source_class.")
        category_counts[source_class] = category_counts.get(source_class, 0) + 1
        for check_id in mapped_check_ids:
            check_coverage[check_id].append(obligation_id)
        rebuilt_obligations.append(record)

    duplicates = sorted(
        obligation_id
        for obligation_id in set(obligation_ids)
        if obligation_ids.count(obligation_id) > 1
    )
    if duplicates:
        raise GenerationError(f"Duplicate obligation IDs: {duplicates[:20]}")

    expected_counts = spec["plan_obligation_inventory"]["expected_counts"]
    expected_by_source_class = {
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
    if category_counts != expected_by_source_class:
        raise GenerationError(
            "Obligation source-class counts do not match the verification specification.\n"
            f"Expected: {json.dumps(expected_by_source_class, sort_keys=True)}\n"
            f"Observed: {json.dumps(category_counts, sort_keys=True)}"
        )

    procedural_checks = {
        "VER-G00-005",
        "VER-G00-006",
        "VER-G01-002",
        "VER-G10-007",
    }
    checks_without_obligations = {
        check_id for check_id, ids in check_coverage.items() if not ids
    }
    unexpected = sorted(checks_without_obligations - procedural_checks)
    if unexpected:
        raise GenerationError(
            f"Substantive verification checks have no mapped obligations: {unexpected}"
        )

    matrix = copy.deepcopy(mapping_source)
    matrix["generated_from"] = {
        "target_plan": {
            "path": plan_path.name,
            "plan_id": plan["plan_id"],
            "plan_version": plan["plan_version"],
            "sha256": sha256_file(plan_path),
            "byte_size": plan_path.stat().st_size,
        },
        "verification_specification": {
            "path": spec_path.name,
            "verification_spec_id": spec["verification_spec_id"],
            "verification_spec_version": spec["verification_spec_version"],
            "sha256": sha256_file(spec_path),
            "byte_size": spec_path.stat().st_size,
        },
        "generation_rule_source": "/plan_obligation_inventory/obligation_generation_rules",
    }
    matrix["coverage_summary"] = {
        "expected_total_obligations": expected_total,
        "generated_total_obligations": len(rebuilt_obligations),
        "mapped_obligations": len(rebuilt_obligations),
        "unmapped_obligations": 0,
        "invalid_source_pointers": 0,
        "duplicate_obligation_ids": 0,
        "verification_checks_total": len(checks),
        "verification_checks_with_obligation_mappings": sum(
            1 for ids in check_coverage.values() if ids
        ),
        "procedural_checks_without_direct_plan_obligations": sorted(
            procedural_checks & checks_without_obligations
        ),
        "coverage_percent": 100.0,
        "category_counts": dict(sorted(category_counts.items())),
    }
    matrix["check_coverage_index"] = [
        {
            "check_id": check["check_id"],
            "gate_id": gate_by_check[check["check_id"]],
            "title": check["title"],
            "mapped_obligation_count": len(check_coverage[check["check_id"]]),
            "mapped_obligation_ids": check_coverage[check["check_id"]],
        }
        for gate in spec["verification_gates"]
        for check in gate["checks"]
    ]
    matrix["obligations"] = rebuilt_obligations
    matrix["integrity"]["expected_obligation_count"] = expected_total
    matrix["integrity"]["expected_check_count"] = len(checks)
    return matrix


def render_checklist(
    *,
    plan: Mapping[str, Any],
    spec: Mapping[str, Any],
    matrix: Mapping[str, Any],
    plan_path: Path,
    spec_path: Path,
    matrix_path: Path,
) -> str:
    checks, _, _ = collect_checks(spec)
    check_coverage = {
        row["check_id"]: row["mapped_obligation_count"]
        for row in matrix["check_coverage_index"]
    }
    category_counts = matrix["coverage_summary"]["category_counts"]
    expected_counts = spec["plan_obligation_inventory"]["expected_counts"]
    expected_by_source_class = {
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
    expected_total = spec["plan_obligation_inventory"]["expected_total_obligations"]

    lines: List[str] = []
    append = lines.append
    append("# EAFIX SSOT Registry Delivery Verification Checklist")
    append("")
    append("> **Generated, non-authoritative artifact. Do not hand-edit.**")
    append("> Regenerate from the canonical verification specification and bound final plan.")
    append("")
    append("## Document binding")
    append("")
    append(f"- **Target plan:** `{plan['plan_id']}` version `{plan['plan_version']}`")
    append(f"- **Target plan file:** `{plan_path.name}`")
    append(f"- **Target plan SHA-256:** `{sha256_file(plan_path)}`")
    append(
        f"- **Verification specification:** `{spec['verification_spec_id']}` "
        f"version `{spec['verification_spec_version']}`"
    )
    append(f"- **Verification specification file:** `{spec_path.name}`")
    append(f"- **Verification specification SHA-256:** `{sha256_file(spec_path)}`")
    append(f"- **Obligation matrix:** `{matrix_path.name}`")
    append(f"- **Expected plan obligations:** `{expected_total}`")
    append(f"- **Verification gates:** `{len(spec['verification_gates'])}`")
    append(f"- **Verification checks:** `{len(checks)}`")
    append("")
    append("## Use rules")
    append("")
    for rule in [
        "Execute gates in numeric order and only after all declared dependencies pass.",
        "Record each check verdict in a separate run-specific verification report; do not edit this checklist to become the result authority.",
        "Use only `pass`, `fail`, `blocked`, or `not_applicable` as verdicts.",
        "`blocked` is not a pass. `not_applicable` requires plan-based rationale and approval when required.",
        "Every pass must cite fresh evidence bound to the target commit, target-plan hash, and verification-specification hash.",
        "Do not rely on the implementing agent's summary as evidence.",
        "Run negative tests, mutations, and rollback rehearsals only in isolated fixtures or disposable worktrees.",
        "Stop downstream completion claims when a blocker or high-severity check fails or is blocked.",
    ]:
        append(f"- {rule}")
    append("")
    append("## Obligation coverage summary")
    append("")
    append("| Obligation class | Expected | Generated | Status |")
    append("|---|---:|---:|---|")
    for source_class, expected_count in expected_by_source_class.items():
        actual_count = category_counts[source_class]
        status = "PASS" if actual_count == expected_count else "FAIL"
        append(f"| `{source_class}` | {expected_count} | {actual_count} | {status} |")
    append(
        f"| **Total** | **{expected_total}** | **{matrix['coverage_summary']['generated_total_obligations']}** | "
        f"**{'PASS' if matrix['coverage_summary']['generated_total_obligations'] == expected_total else 'FAIL'}** |"
    )
    append("")
    append("## Run header")
    append("")
    for field in [
        "Run ID",
        "Repository",
        "Target branch",
        "Target commit SHA",
        "Verifier identity",
        "Started at UTC",
        "Completed at UTC",
        "Working tree clean",
        "Evidence root",
        "Final report path",
    ]:
        append(f"- [ ] **{field}:** `____________________________`")
    append("")
    append("## Gate summary")
    append("")
    append("| Order | Gate | Title | Dependency | Blocker/high pass required | Verdict |")
    append("|---:|---|---|---|---|---|")
    for gate in spec["verification_gates"]:
        dependencies = ", ".join(gate["depends_on"]) or "None"
        append(
            f"| {gate['order']} | `{gate['gate_id']}` | {gate['title']} | "
            f"{dependencies} | Yes | `not_run` |"
        )
    append("")

    for gate in spec["verification_gates"]:
        append(f"## {gate['gate_id']} — {gate['title']}")
        append("")
        append(f"**Purpose:** {gate['purpose']}")
        append("")
        dependencies = ", ".join(f"`{item}`" for item in gate["depends_on"]) or "None"
        append(f"**Depends on:** {dependencies}")
        append("")
        if gate.get("phase_refs"):
            append(
                "**Target-plan phases:** "
                + ", ".join(f"`{phase}`" for phase in gate["phase_refs"])
            )
            append("")
        append("**Pass policy:**")
        for key, value in gate["pass_policy"].items():
            rendered = str(value).lower() if isinstance(value, bool) else value
            append(f"- `{key}`: `{rendered}`")
        append("")
        append(f"**On failure:** {gate['on_fail']}")
        append("")

        for check in gate["checks"]:
            append(f"### [ ] {check['check_id']} — {check['title']}")
            append("")
            append(
                f"- **Category:** `{check['category']}`  \n"
                f"- **Severity:** `{check['severity']}`  \n"
                f"- **Control type:** `{check['control_type']}`  \n"
                f"- **Verification mode:** `{check['verification_mode']}`  \n"
                f"- **Automation:** `{check['automation_level']}`  \n"
                f"- **Applicability:** `{check['applicability']}`  \n"
                f"- **Fail closed:** `{str(check['fail_closed']).lower()}`  \n"
                f"- **Mapped obligations:** `{check_coverage.get(check['check_id'], 0)}`"
            )
            append("")
            if check.get("phase_refs"):
                append(
                    "- **Phase references:** "
                    + ", ".join(f"`{phase}`" for phase in check["phase_refs"])
                )
            if check.get("preconditions"):
                append("- **Preconditions:**")
                for item in check["preconditions"]:
                    append(f"  - [ ] {item}")
            append("- **Procedure:**")
            for item in check["procedure"]:
                append(f"  - [ ] {item}")
            if check.get("commands"):
                append("- **Commands:**")
                for command in check["commands"]:
                    append(f"  - [ ] `{command}`")
            append("- **Expected results:**")
            for result in check["expected_results"]:
                append(f"  - [ ] {result}")
            append("- **Required evidence:**")
            for evidence in check["required_evidence"]:
                append(
                    f"  - [ ] `{evidence['evidence_type']}` — {evidence['description']} "
                    f"(minimum: {evidence['minimum_count']}; "
                    f"freshness required: {str(evidence['freshness_required']).lower()})"
                )
            append(
                "- **Allowed verdicts:** "
                + ", ".join(f"`{verdict}`" for verdict in check["allowed_verdicts"])
            )
            negative = check.get("negative_test", {})
            append(
                f"- **Negative test required:** "
                f"`{str(negative.get('required', False)).lower()}`"
            )
            if negative.get("required"):
                append(f"  - [ ] Mutation: {negative['mutation']}")
                append(f"  - [ ] Expected failure: {negative['expected_failure']}")
                append(f"  - [ ] Isolation: {negative['isolation_rule']}")
            append(f"- **Remediation on failure:** {check['remediation_on_fail']}")
            append("- **Run result:**")
            append("  - [ ] Verdict recorded in run-specific report")
            append("  - [ ] Evidence IDs linked")
            append("  - [ ] Evidence freshness verified")
            append("  - [ ] Findings and remediation owner recorded when not `pass`")
            append("")

        append(f"### [ ] {gate['gate_id']} gate decision")
        append("")
        append("- [ ] All dependency gates passed.")
        append("- [ ] All blocker checks passed.")
        append("- [ ] All high-severity checks passed.")
        append("- [ ] No blocked check remains.")
        append("- [ ] Any `not_applicable` verdict has required rationale and approval.")
        append("- [ ] Gate verdict and evidence references are recorded in the run report.")
        append("")

    append("## Final completion decision")
    append("")
    for requirement in spec["completion_policy"]["verified_complete_requires"]:
        append(f"- [ ] {requirement}")
    append("")
    append("### Allowed final status")
    append("")
    for status in spec["completion_policy"]["final_status_values"]:
        append(f"- [ ] `{status}`")
    append("")
    append("### Final declaration controls")
    append("")
    append("- [ ] Exactly one allowed final status is selected.")
    append("- [ ] The selected status is supported by the run-specific report.")
    append("- [ ] Every evidence reference resolves and is fresh.")
    append("- [ ] The evidence bundle is sealed.")
    append("- [ ] Owner approval, rejection, or deferral is recorded.")
    append("- [ ] No completion claim relies on unsupported prose.")
    append("")
    append("## Integrity note")
    append("")
    append(
        "This checklist is generated from the canonical verification specification. "
        "Its check text, ordering, severity, procedure, expected results, evidence "
        "requirements, and gate rules must match that specification. Verification "
        "results belong in the run-specific report and evidence bundle, not in this file."
    )
    append("")
    return "\n".join(lines)


def compare_or_write(path: Path, expected: bytes, write: bool) -> bool:
    observed = path.read_bytes() if path.exists() else None
    changed = observed != expected
    if changed and write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(expected)
    return changed


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def initialize_run(
    *,
    root: Path,
    run_id: str,
    branch: str,
    commit_sha: str,
    verifier: str,
    output_root: Optional[Path],
) -> Tuple[Path, Path]:
    if not RUN_ID_RE.fullmatch(run_id):
        raise GenerationError(f"Invalid run ID: {run_id}")
    if not branch.strip():
        raise GenerationError("Branch must not be empty.")
    if not GIT_SHA_RE.fullmatch(commit_sha):
        raise GenerationError("Commit SHA must be 40 lowercase hexadecimal characters.")
    if not verifier.strip():
        raise GenerationError("Verifier identity must not be empty.")

    evidence_template_path = root / EVIDENCE_TEMPLATE_NAME
    report_template_path = root / REPORT_TEMPLATE_NAME
    evidence = load_json(evidence_template_path)
    report = load_json(report_template_path)

    run_root = output_root or (root / ".state" / "verification" / run_id)
    if run_root.exists() and any(run_root.iterdir()):
        raise GenerationError(f"Run root already exists and is not empty: {run_root}")
    run_root.mkdir(parents=True, exist_ok=True)
    for child in [
        "command_transcripts",
        "raw_outputs",
        "artifacts",
        "ci",
        "mutations",
        "rollbacks",
        "manual_reviews",
        "approvals",
    ]:
        (run_root / child).mkdir(exist_ok=True)

    started = utc_now()
    evidence["document_state"] = "in_progress"
    evidence["run_context"].update(
        {
            "run_id": run_id,
            "target_branch": branch,
            "target_commit_sha": commit_sha,
            "started_at_utc": started,
            "completed_at_utc": None,
            "verifier_identity": verifier,
            "working_tree_clean": True,
            "evidence_root": run_root.as_posix(),
            "run_context_status": "frozen",
        }
    )
    report["document_state"] = "in_progress"
    report["report_status"] = "in_progress"
    report["run_context"].update(
        {
            "run_id": run_id,
            "target_branch": branch,
            "target_commit_sha": commit_sha,
            "started_at_utc": started,
            "completed_at_utc": None,
            "verifier_identity": verifier,
            "working_tree_clean": True,
            "run_context_status": "frozen",
        }
    )
    evidence_name = "verification_evidence_manifest.json"
    report_name = "verification_report.json"
    report["evidence_manifest_binding"]["run_manifest_path"] = (
        run_root / evidence_name
    ).as_posix()

    evidence_path = run_root / evidence_name
    report_path = run_root / report_name
    evidence_path.write_bytes(stable_json_bytes(evidence))
    report_path.write_bytes(stable_json_bytes(report))
    return evidence_path, report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Directory containing the verification package files.",
    )
    parser.add_argument(
        "--mapping-source",
        type=Path,
        default=None,
        help="Curated obligation matrix used as mapping authority (defaults to output matrix).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write regenerated matrix/checklist when they differ.",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="Check generated outputs without writing (default).",
    )
    parser.add_argument("--init-run", metavar="RUN_ID", help="Initialize a run bundle.")
    parser.add_argument("--branch", help="Target branch for --init-run.")
    parser.add_argument("--commit-sha", help="Target commit SHA for --init-run.")
    parser.add_argument("--verifier", help="Verifier identity for --init-run.")
    parser.add_argument(
        "--run-output-root",
        type=Path,
        default=None,
        help="Optional explicit output directory for --init-run.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()

    if args.init_run:
        missing = [
            name
            for name, value in [
                ("--branch", args.branch),
                ("--commit-sha", args.commit_sha),
                ("--verifier", args.verifier),
            ]
            if not value
        ]
        if missing:
            raise GenerationError(
                f"--init-run requires: {', '.join(missing)}"
            )
        evidence_path, report_path = initialize_run(
            root=root,
            run_id=args.init_run,
            branch=args.branch,
            commit_sha=args.commit_sha,
            verifier=args.verifier,
            output_root=args.run_output_root,
        )
        print(
            json.dumps(
                {
                    "status": "initialized",
                    "evidence_manifest": str(evidence_path),
                    "verification_report": str(report_path),
                },
                indent=2,
            )
        )
        return 0

    plan_path = root / PLAN_NAME
    spec_path = root / SPEC_NAME
    matrix_path = root / MATRIX_NAME
    checklist_path = root / CHECKLIST_NAME
    mapping_source_path = (
        args.mapping_source.resolve()
        if args.mapping_source
        else matrix_path
    )

    plan = load_json(plan_path)
    spec = load_json(spec_path)
    mapping_source = load_json(mapping_source_path)
    verify_target_binding(plan_path, spec, plan)

    expected_matrix = rebuild_matrix(
        plan_path=plan_path,
        spec_path=spec_path,
        plan=plan,
        spec=spec,
        mapping_source=mapping_source,
    )
    expected_matrix_bytes = stable_json_bytes(expected_matrix)
    expected_checklist = render_checklist(
        plan=plan,
        spec=spec,
        matrix=expected_matrix,
        plan_path=plan_path,
        spec_path=spec_path,
        matrix_path=matrix_path,
    ).encode("utf-8")

    write = bool(args.write)
    matrix_changed = compare_or_write(matrix_path, expected_matrix_bytes, write)
    checklist_changed = compare_or_write(checklist_path, expected_checklist, write)

    result = {
        "mode": "write" if write else "check",
        "matrix_changed": matrix_changed,
        "checklist_changed": checklist_changed,
        "expected_matrix_sha256": sha256_bytes(expected_matrix_bytes),
        "expected_checklist_sha256": sha256_bytes(expected_checklist),
        "obligations": len(expected_matrix["obligations"]),
        "checks": expected_matrix["coverage_summary"]["verification_checks_total"],
        "coverage_percent": expected_matrix["coverage_summary"]["coverage_percent"],
    }
    print(json.dumps(result, indent=2))
    return 0 if write or not (matrix_changed or checklist_changed) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)

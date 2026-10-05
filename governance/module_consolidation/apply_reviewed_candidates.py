"""Apply explicitly reviewed candidate proposals; never write active roots."""
from __future__ import annotations

import argparse
from pathlib import Path

from authority_core import REPO, file_sha, guarded_replace, jsonl, load, pointer
from progress_gate import validate_progress
from validate_consolidation import validate_manifests


def verify_reviewed_source(change: dict, repo: Path) -> None:
    """Check frozen JSON values or exact line ranges in reviewed text/code."""
    source = repo / change["source_path"]
    if file_sha(source) != change["source_sha256"]:
        raise ValueError("Stale reviewed source")
    if "source_json_pointer" in change:
        value = jsonl(source) if source.suffix == ".jsonl" else load(source)
        if pointer(value, change["source_json_pointer"]) != change["reviewed_source_value"]:
            raise ValueError("Source locator/value changed")
    else:
        start, end = change["source_line_start"], change["source_line_end"]
        lines = source.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        if not (isinstance(start, int) and isinstance(end, int) and 1 <= start <= end <= len(lines)):
            raise ValueError("Invalid reviewed source line range")
        if "".join(lines[start - 1:end]) != change["reviewed_source_text"]:
            raise ValueError("Source locator/text changed")


def apply_proposals(path: Path, repo: Path = REPO) -> int:
    proposals = load(path)
    control = repo / "governance/module_consolidation"
    baseline = load(control / "run/baseline.json")["baseline_commit"]
    if proposals["baseline_commit"] != baseline or not proposals["review_approved"]:
        raise ValueError("Proposal is unapproved or based on a different baseline")
    decisions = {d["decision_id"]: d for d in load(control / "resolution_decisions.json")["decisions"]}
    if decisions[proposals["decision_id"]]["status"] != "approved_for_execution":
        raise ValueError("Semantic decision not approved for execution")
    if validate_progress(repo, "evidence_backed_candidate_patches")["status"] != "PASS":
        raise ValueError("Independent candidate integrity gate blocked")
    prepared = []
    for item in proposals["proposals"]:
        target = repo / item["candidate_path"]
        if target.parent.parent.resolve() != (control / "staging").resolve() or target.name != "manifest.v2.candidate.json":
            raise ValueError("Only staged module candidates may be patched")
        old = load(target)
        new = item["reviewed_candidate"]
        # An exact already-applied candidate is an idempotent no-op.
        if old == new:
            continue
        if file_sha(target) != item["expected_candidate_sha256"] or old != item["reviewed_old_candidate"]:
            raise ValueError("Stale candidate: reconcile before applying")
        for change in item["reviewed_changes"]:
            verify_reviewed_source(change, repo)
        prepared.append((target, item, old, new))
    replacements = {target.resolve(): new for target, _, _, new in prepared}
    universe = load(control / "module_universe.json")
    manifests = []
    for module in universe:
        candidate = control / "staging" / module["short_id"] / "manifest.v2.candidate.json"
        manifests.append(replacements.get(candidate.resolve(), load(candidate)))
    integrity = validate_manifests(manifests, universe, repo,
        load(control / "staging/shared_file_registry.candidate.json"), check_readiness=False)
    if integrity["status"] != "PASS":
        raise ValueError("Reviewed candidate result fails structural/reference/evidence integrity")
    # Preflight every proposal before the first write.
    for target, item, old, new in prepared:
        guarded_replace(target, item["expected_candidate_sha256"], old, new, baseline, repo=repo)
    return len(prepared)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal_path", type=Path)
    args = parser.parse_args()
    print({"candidates_changed": apply_proposals(args.proposal_path), "active_roots_changed": 0})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

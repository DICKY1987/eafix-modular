"""One-way, deterministic projections; active generation requires a passing cutover gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from authority_core import (BUNDLE, CONTROL, PROCESS, REPO, SHARED, file_sha, load, write)
from validate_consolidation import validate_repository


def projection_outputs(repo: Path, *, candidate: bool = False) -> dict[str, dict | str]:
    control = repo / "governance/module_consolidation"
    universe = load(control / "module_universe.json")
    baseline = load(control / "run/baseline.json")
    manifests = []
    inputs = []
    for u in universe:
        path = control / "staging" / u["short_id"] / "manifest.v2.candidate.json" if candidate else repo / u["root"] / "manifest.json"
        m = load(path)
        if m.get("schema_version") != "2.0.0":
            raise ValueError("Projection generation requires v2 inputs")
        manifests.append(m)
        inputs.append({"path": path.relative_to(repo).as_posix(), "sha256": file_sha(path),
                       "version": m["manifest_version"]})
    shared = control / "staging/shared_file_registry.candidate.json" if candidate else repo / SHARED
    global_inputs = [{"path": str(p.relative_to(repo)), "sha256": file_sha(p)} for p in [repo / PROCESS, shared]]
    metadata = {"generator": "governance/module_consolidation/generate_projections.py", "generator_version": "1.0.0",
                "generated_at_utc": baseline["pinned_at_utc"], "source_commit": baseline["baseline_commit"],
                "authority_policy": "generated_from_module_manifests", "source_manifests": inputs, "global_sources": global_inputs,
                "projection_status": "candidate_preview" if candidate else "active_derived"}
    outputs: dict[str, dict | str] = {BUNDLE: {"schema_version": "2.0.0", "document_type": "generated_module_manifest_bundle",
        "module_count": 34, **metadata, "manifests": manifests}}
    index = {"schema_version": "2.0.0", "document_type": "generated_module_index", **metadata,
             "modules": [{"module_id": m["module_identity"]["module_id"], "short_id": m["module_identity"]["short_id"],
                          "canonical_symbol": m["module_identity"]["canonical_symbol"], "manifest_path": u["root"] + "/manifest.json",
                          "process_step_ids": [s["step_id"] for s in m["process_steps"]],
                          "specification_ready": m["reconciliation"]["specification_ready"]} for u, m in zip(universe, manifests)]}
    outputs["EAFIX_auth_docs/generated/modules/module_index.json"] = index
    for u, m, src in zip(universe, manifests, inputs):
        mid = u["module_id"]
        prefix = "context_packets/" + mid
        outputs[prefix + "/context_packet.json"] = {"schema_version": "2.0.0", "document_type": "generated_module_context_packet",
            **metadata, "source_manifest": src, "module_identity": m["module_identity"], "module_context": m,
            "global_authority_refs": [PROCESS, SHARED], "use_policy": "Load the module manifest for editable facts; this packet is read-only derived context."}
        outputs[prefix + "/ai_readme.md"] = (
            f"# {m['module_identity']['module_name']}\n\n"
            f"Generated from `{u['root']}/manifest.json`. Authority policy: generated_from_module_manifests.\n\n"
            f"Canonical symbol: `{u['canonical_symbol']}`. Source SHA-256: `{src['sha256']}`.\n\n"
            f"Source commit: `{baseline['baseline_commit']}`. Specification ready: `{m['reconciliation']['specification_ready']}`.\n"
        )
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--candidate-preview", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    if not args.candidate_preview:
        report = validate_repository(repo, mode="active", check_projection_parity=False)
        if report["status"] != "PASS":
            print("BLOCKED: active authority validation failed; no projection or authority was changed")
            return 1
    outputs = projection_outputs(repo, candidate=args.candidate_preview)
    base = repo / "governance/module_consolidation/projection_preview" if args.candidate_preview else repo
    stale = []
    for relative, content in outputs.items():
        path = base / relative
        rendered = content if isinstance(content, str) else json.dumps(content, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
    print(json.dumps({"output_count": len(outputs), "stale_outputs": stale, "candidate_preview": args.candidate_preview,
                      "root_manifest_writes": 0}, sort_keys=True))
    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())

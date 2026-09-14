# Agent instructions -- OMS State Machine (O2_OMS_STATE_MACHINE)

> Auto-generated from `manifest.json` by the governance remediation pass on 2026-09-09T07:12:15+00:00.

Read `README.md` in this folder first for what this module does. This file is specifically for an AI coding agent
about to make changes here.

## Boundary rules (from `contracts.module_io_policy`)

- May ingest only declared upstream outputs: `True`
- Private cross-module access allowed: `False`
- Shared-kernel access policy: `stable_domain_neutral_primitives_only`

**Do not** implement any of this module's `forbidden_responsibilities` (see README) inside this folder, and do not
reach into a sibling module's `m00NN-src/` directly -- consume its declared output contract instead.

## Where code goes

- Primary module root: `m0019-o2-oms-state-machine`
- If `module_root` is this module's own scaffold folder (not yet a real service directory), this module's canonical
  implementation is still physically located in the shared service path(s) listed under "Shared / not-yet-refactored
  files" in README.md, pending the repository's Phase-5 physical migration. Do not assume the scaffold subfolders
  (`m0019-o2-oms-state-machine-src/`, `m0019-o2-oms-state-machine-tests/`, etc.) already contain the real implementation -- check `file_ownership.owned_files`
  in `manifest.json` first.

## Validation

- Applicable gates: GATE-O2_OMS_STATE_MACHINE
- Applicable rules: VAL-S19-001
- Required validators: jsonschema

Run `python tools/validate_module_structure.py` from the repo root before committing structural changes (new files,
moved files, or manifest edits) -- it enforces exclusive file ownership and manifest/disk consistency across all 34
modules, not just this one.

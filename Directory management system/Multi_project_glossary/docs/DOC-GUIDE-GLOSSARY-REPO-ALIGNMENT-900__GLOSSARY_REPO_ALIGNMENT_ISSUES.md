<!-- DOC_LINK: DOC-GUIDE-GLOSSARY-REPO-ALIGNMENT-900 -->
---
doc_id: DOC-GUIDE-GLOSSARY-REPO-ALIGNMENT-900
status: draft
doc_type: guide
---

# Glossary Repo Alignment Issues

## Purpose

Document the current mismatch between the repository layout and the paths,
links, and tool expectations referenced by glossary documentation and scripts.
This is intended to clarify scope and next steps.

## Status

Most path mismatches are now addressed by aligning docs and scripts to the SSOT plan in
`docs\DOC-GUIDE-GLOSSARY-SYSTEM-PLAN-910__GLOSSARY_SYSTEM_PLAN.md`.

## Observed mismatches

1. Referenced files that do not exist in this repo (resolved)
   - Docs previously pointed to `glossary.md`, `.glossary-metadata.yaml`, and
     `scripts\glossary\*.py`, but have been updated to `DOC-*__` paths.
     Examples:
     - `docs\DOC-GUIDE-GLOSSARY-SYSTEM-OVERVIEW-423__GLOSSARY_SYSTEM_OVERVIEW.md`
     - `docs\DOC-GUIDE-GLOSSARY-PROCESS-DOCS-README-292__GLOSSARY_PROCESS_DOCS_README.md`
     - `schemas\DOC-CONFIG-GLOSSARY-PROCESS-STEPS-SCHEMA-302__GLOSSARY_PROCESS_STEPS_SCHEMA.yaml`

2. Policy paths reference missing metadata location (resolved)
   - `config\DOC-CONFIG-GLOSSARY-SSOT-POLICY-266__glossary_ssot_policy.yaml`
     now points to `DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml`.

3. Validator scripts use legacy paths (resolved)
   - `scripts\DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py`
     now targets `docs\DOC-GUIDE-GLOSSARY-665__glossary.md` and
     `DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml`.
   - `scripts\DOC-CORE-SUB-GLOSSARY-VALIDATE-GLOSSARY-SCHEMA-770__validate_glossary_schema.py`
     looks for `GLOSSARY_PROCESS_STEPS_SCHEMA.yaml` in the script directory, but
     the actual schema is
     `schemas\DOC-CONFIG-GLOSSARY-PROCESS-STEPS-SCHEMA-302__GLOSSARY_PROCESS_STEPS_SCHEMA.yaml`.

4. Directory manifest references missing registry files (resolved)
   - `DOC-CONFIG-DIR-MANIFEST-CONTEXT-GLOSSARY-1003__DIR_MANIFEST.yaml`
     now references `DOC-REGISTRY-TERM-ID-001__GLOSSARY_REGISTRY.yaml`.

5. Example JSONs reference an external project root
   - Files under `examples\*.json` use
     `C:\Users\richg\ALL_AI\Complete AI Development Pipeline - Canonical Phase Plan`
     rather than this repo root.

## Impact

- Most path mismatches are resolved, so validation and SSOT tooling now point to
  current artifacts.
- Cross references and "how to use" instructions have been updated to match the
  SSOT plan.
- Remaining risk: example JSONs still point to an external project root.

## Open questions

1. Is this repo meant to mirror a different canonical layout (for example,
   `DOC-GUIDE-GLOSSARY-665__glossary.md`, `DOC-CONFIG-GLOSSARY-METADATA-032__.glossary-metadata.yaml`,
   `scripts\DOC-*__*.py`), or should the docs and scripts be updated to the current `DOC-*__` naming?
2. Should missing files (glossary metadata, glossary scripts, registry entries)
   be added here, or do you want the references rewritten to point to another
   repo?

# Authority & Supersession Checklist (Required Entry Gate)

1. Confirm control files are present and readable:
   - `/home/runner/work/eafix-modular/eafix-modular/EAFIX_auth_docs/doc_authority.json`
   - `/home/runner/work/eafix-modular/eafix-modular/EAFIX_auth_docs/module_catalog.json`
   - `/home/runner/work/eafix-modular/eafix-modular/EAFIX_auth_docs/process_step_catalog.json`
   - `/home/runner/work/eafix-modular/eafix-modular/EAFIX_auth_docs/module_checklist.json`
   - `/home/runner/work/eafix-modular/eafix-modular/eafix_project_knowledge_reference_routing_instructions.json`
2. Apply decision rule exactly: `canonical > supporting_reference > legacy_reference > generated > superseded`.
3. Regenerate `/home/runner/work/eafix-modular/eafix-modular/EAFIX_auth_docs/documentation_triage_matrix.json` with SHA256-based duplicate detection.
4. For each overlap group, select one active authority document and mark the rest as supporting or superseded.
5. Move superseded files into `/home/runner/work/eafix-modular/eafix-modular/EAFIX_auth_docs/superseded/` only after the authority decision is recorded.
6. Add machine-readable supersession metadata to each moved file (`status`, `superseded_by`, `reason`, `active_authority=false`).
7. Update `/home/runner/work/eafix-modular/eafix-modular/EAFIX_auth_docs/doc_authority.json` and `/home/runner/work/eafix-modular/eafix-modular/EAFIX_auth_docs/documentation_cleanup_report.json`.
8. Validate no active references point to superseded/deleted files.
9. Confirm module symbol coverage and alignment across catalog/checklist/worksheet before closing.
10. Do not add new docs until this checklist has been completed for the current pass.

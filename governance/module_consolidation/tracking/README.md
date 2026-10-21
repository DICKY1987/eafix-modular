# EAFIX consolidation tracking

Baseline: `f37f8ca8bd966031fb243a9cd9401b065c29135a`.
Execution status: **ACTIVE_WITH_SCOPED_HOLDS** under DEC-031.
Independent review is in progress; phase acceptance gates and cutover remain
BLOCKED where evidence is incomplete. Candidate fact updates do not mean a
module, wave, or source is fully reconciled.

This directory holds a derived work-tracking view. The governed decisions,
source ledger, blocker queue and phase report determine its content. Module
specifications remain in the existing active roots until P6 passes.

Run `python governance/module_consolidation/tracking/build_ssot.py` from any
directory. It writes beside its own script and preserves the 76 existing item
IDs. D1-D7 are derived from the owner's DEC policy, not treated as unanswered
questions. The module schema field describes the candidate; the active root
remains v1. The three readiness fields remain independent.

No GitHub Projects or issue statuses were changed by this execution. Existing
`project_sync.py` and `project_bootstrap.py` remain optional projection tools;
their external state is not the execution authority.

See `../CLOSEOUT_REPORT.md`, `../run/phase_status.json`,
`../resolution_decisions.json` and `../run/critical_blockers.json`.

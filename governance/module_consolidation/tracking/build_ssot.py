#!/usr/bin/env python3
"""
Build the SSOT work plan for the EAFIX 34-module documentation consolidation.

The SSOT is the authority. GitHub Projects is a *projection* of it.
Nothing in this file is a status the UI may overwrite: sync is one-way
(repo -> GitHub) and project_sync.py reports drift rather than absorbing it.
"""
import json
from pathlib import Path

PLAN_VERSION = "2.0.0"
BASELINE_COMMIT = "f37f8ca8bd966031fb243a9cd9401b065c29135a"
CONTROL = Path(__file__).resolve().parents[1]


def read_governance(name):
    return json.loads((CONTROL / name).read_text(encoding="utf-8-sig"))

MODULES = [
    ("m0001", "m0001-f1-config-preferences",       "F1_CONFIG_PREFERENCES",      "W1"),
    ("m0002", "m0002-f3-clock-scheduler",          "F3_CLOCK_SCHEDULER",         "W1"),
    ("m0003", "m0003-d2-calendar-source-adapter",  "D2_CALENDAR_SOURCE_ADAPTER", "W2"),
    ("m0004", "m0004-d3-calendar-normalizer",      "D3_CALENDAR_NORMALIZER",     "W2"),
    ("m0005", "m0005-f2-event-log",                "F2_EVENT_LOG",               "W1"),
    ("m0006", "m0006-d4-calendar-trigger-builder", "D4_CALENDAR_TRIGGER_BUILDER","W2"),
    ("m0007", "m0007-d1-market-feed-adapter",      "D1_MARKET_FEED_ADAPTER",     "W2"),
    ("m0008", "m0008-c1-bar-builder",              "C1_BAR_BUILDER",             "W3"),
    ("m0009", "m0009-c2-indicator-engine",         "C2_INDICATOR_ENGINE",        "W3"),
    ("m0010", "m0010-c3-feature-packager",         "C3_FEATURE_PACKAGER",        "W3"),
    ("m0011", "m0011-s1-signal-engine",            "S1_SIGNAL_ENGINE",           "W4"),
    ("m0012", "m0012-s2-intent-builder",           "S2_INTENT_BUILDER",          "W4"),
    ("m0013", "m0013-r1-risk-evaluator",           "R1_RISK_EVALUATOR",          "W4"),
    ("m0014", "m0014-r2-order-intent-compiler",    "R2_ORDER_INTENT_COMPILER",   "W4"),
    ("m0015", "m0015-o1-order-router",             "O1_ORDER_ROUTER",            "W5"),
    ("m0016", "m0016-b1-mt4-adapter-transport",    "B1_MT4_ADAPTER_TRANSPORT",   "W5"),
    ("m0017", "m0017-b2-mt4-ea-executor",          "B2_MT4_EA_EXECUTOR",         "W5"),
    ("m0018", "m0018-b3-exec-event-normalizer",    "B3_EXEC_EVENT_NORMALIZER",   "W5"),
    ("m0019", "m0019-o2-oms-state-machine",        "O2_OMS_STATE_MACHINE",       "W5"),
    ("m0020", "m0020-o3-trade-close-classifier",   "O3_TRADE_CLOSE_CLASSIFIER",  "W5"),
    ("m0021", "m0021-e1-outcome-bucketizer",       "E1_OUTCOME_BUCKETIZER",      "W6"),
    ("m0022", "m0022-e2-proximity-evaluator",      "E2_PROXIMITY_EVALUATOR",     "W6"),
    ("m0023", "m0023-e3-matrix-lookup",            "E3_MATRIX_LOOKUP",           "W6"),
    ("m0024", "m0024-e4-reentry-intent-builder",   "E4_REENTRY_INTENT_BUILDER",  "W6"),
    ("m0025", "m0025-f4-flow-orchestrator",        "F4_FLOW_ORCHESTRATOR",       "W1"),
    ("m0026", "m0026-p1-health-aggregator",        "P1_HEALTH_AGGREGATOR",       "W7"),
    ("m0027", "m0027-r3-correlation-guard",        "R3_CORRELATION_GUARD",       "W4"),
    ("m0028", "m0028-u1-dashboard-backend",        "U1_DASHBOARD_BACKEND",       "W7"),
    ("m0029", "m0029-u2-gui-gateway",              "U2_GUI_GATEWAY",             "W7"),
    ("m0030", "m0030-u3-mt4-expiry-overlay",       "U3_MT4_EXPIRY_OVERLAY",      "W7"),
    ("m0031", "m0031-u4-desktop-operator",         "U4_DESKTOP_OPERATOR",        "W7"),
    ("m0032", "m0032-p2-reporter",                 "P2_REPORTER",                "W7"),
    ("m0033", "m0033-sk1-plugin-interface",        "SK1_PLUGIN_INTERFACE",       "W8"),
    ("m0034", "m0034-sk2-idempotency",             "SK2_IDEMPOTENCY",            "W8"),
]

PILOT = {"m0009", "m0016", "m0029", "m0034"}

WAVES = [
    ("W1", "Foundation"), ("W2", "Data acquisition"), ("W3", "Computation"),
    ("W4", "Signals and risk"), ("W5", "Orders and execution"), ("W6", "Re-entry"),
    ("W7", "Operator and observability"), ("W8", "Shared kernels"),
]

PHASES = [
    ("P0", "Baseline",
     "Pin commit; inspect local changes; inventory sources, roots, authorities, references, and all generators/writers.",
     "Reproducible inventory and agreed scope; unresolved identity/authority conflicts explicitly listed."),
    ("P1", "Policy and schema",
     "Approve Section 2 decisions; build field-authority matrix, new schema, migration map, and validation fixtures.",
     "Owner approval; representative positive/negative schema tests pass."),
    ("P2", "Seed all 34 candidates",
     "Copy existing module information into staging through the migration map; retain lineage and unknowns.",
     "Exactly 34 correctly identified candidates; no unaccounted v1 field loss."),
    ("P3", "Pilot",
     "Run full reconciliation on representative modules and document formats; exercise archival in a disposable copy only.",
     "End-to-end evidence, conflict handling, repeatability, and restoration checks pass."),
    ("P4", "Controlled batches",
     "Process pinned source batches and complete module coverage waves; stage only approved changes.",
     "Every batch passes its own gates; unresolved matters remain visible."),
    ("P5", "System validation",
     "Validate all 34 together, references, contracts, process bindings, ownership, behavior completeness, and coverage.",
     "Approved specifications ready for cutover; no unresolved mandatory specification blockers."),
    ("P6", "Authority cutover",
     "Publish the 34 manifests and authority routing together; redirect legacy writers; regenerate designated projections.",
     "One active authority per fact class; CI and regenerated projections agree."),
    ("P7", "Retire eligible documents",
     "Verify committed target values; mark fully scraped; check retention/references; archive approved sources.",
     "Each source independently meets reconciliation and archive gates."),
    ("P8", "Closeout and maintenance",
     "Deliver verification summary, remaining live references, archive index, gaps, and future-change rules.",
     "Owner accepts results against Section 13, not merely a file-count target."),
]

DECISIONS = [
    ("D1", "Module authority location",
     "One `<existing-module-root>/manifest.json` per module; retain the currently approved filename if different.",
     "Avoid introducing a second module authority or coupling this work to folder migration."),
    ("D2", "Meaning of single authority",
     "Module JSON owns module-specific specs; shared contracts and global process definitions retain their own authorities.",
     "Prevent conflicting copies of shared facts inside 34 files."),
    ("D3", "Schema evolution",
     "Publish a new major schema version for breaking changes; keep the supplied v1 schema immutable.",
     "Changing process cardinality and provenance requires an explicit migration."),
    ("D4", "Decision authority",
     "Repository owner, or explicitly delegated reviewer, approves semantic resolutions; automation may propose.",
     "A confidence score or historical document label is not approval."),
    ("D5", "Automation boundary",
     "Pilot requires review of every change; later permit only expressly approved low-risk rules.",
     "Blank fields can still receive wrong information."),
    ("D6", "Header and archive policy",
     "Preserve original bytes; annotate an archived prose copy; use a standard sidecar and notice for every format.",
     "Meet the notice requirement without corrupting JSON, CSV, PDFs, or evidence."),
    ("D7", "Disposition of the competing manifest bundle",
     "Decide the fate of EAFIX_auth_docs/manifests/eafix_module_manifests_bundle.vNext.schema_valid.json: "
     "regenerate-from-roots, or archive. VERIFIED 2026-09-22: it holds all 34 manifests in the identical v1 shape "
     "and already disagrees with the module roots on 28 of 34 (file_ownership, reconciliation_status, "
     "last_updated_utc, notes).",
     "A live second authority can silently reverse the P6 cutover. Not in the original Section 2 list; added from "
     "baseline verification."),
]

DELIVERABLES = [
    ("DL1", "P1", "Consolidation policy",
     "Field ownership, approval rules, profiles, migration map, and completeness rules."),
    ("DL2", "P1", "Atomic module schema v2",
     "Adds behavior, applicability, field evidence, conflicts, verification, and source-extraction sections. "
     "VERIFIED: 0 of 34 current manifests carry any of these; all are schema_version 1.0.0."),
    ("DL3", "P1", "v1 to v2 migration map",
     "Every old field retained, transformed, or retired with a recorded reason. No silent field loss."),
    ("DL4", "P1", "Validation fixtures",
     "Representative positive and negative schema tests."),
    ("DL5", "P0", "Source-processing ledger",
     "Inventory, source versions, coverage, state transitions, retention, archive locations. "
     "VERIFIED: 269 files in EAFIX_auth_docs; only 37 match on filename."),
    ("DL6", "P0", "Writer and generator inventory",
     "Every script, CI job, editor and importer that can rewrite manifests, registries, bundles or context packets."),
    ("DL7", "P4", "Batch reconciliation record set",
     "Extracted claims, proposed mappings, baseline values, decisions, candidate patches."),
    ("DL8", "P7", "Archive tree and receipts",
     "archive/module-supporting-docs/<source-id>/<hash-prefix>/ with original, receipt.json, README notice. "
     "VERIFIED: no top-level archive/ exists yet."),
    ("DL9", "P8", "Closeout report",
     "Explicit denominators; files, source versions, claims and module relationships counted separately."),
]

def issue_body(lines):
    return "\n".join(lines).strip()

def build():
    items = []

    for pid, name, work, gate in PHASES:
        items.append({
            "ssot_id": f"PHASE-{pid}",
            "item_type": "Phase",
            "title": f"{pid} - {name}",
            "body": issue_body([
                f"**Phase {pid}: {name}**", "",
                "### Work", work, "",
                "### Gate to proceed", gate, "",
                "---",
                "Projected from the consolidation SSOT. Status is owned by the repo ledger, not this issue.",
            ]),
            "fields": {"Status": "Todo", "Item Type": "Phase", "Phase": pid,
                       "Wave": "Not Applicable", "Baseline Commit": BASELINE_COMMIT},
            "parent": None,
            "labels": ["consolidation", "phase"],
        })
        items.append({
            "ssot_id": f"GATE-{pid}",
            "item_type": "Gate",
            "title": f"GATE {pid} - {name}",
            "body": issue_body([
                f"**Gate for phase {pid}.** Close only when the criterion below is met and evidence is recorded.", "",
                "### Criterion", gate, "",
                "### Required before close",
                "- [ ] Evidence recorded in the ledger (not in this issue)",
                "- [ ] Named approver recorded",
                "- [ ] No unresolved blocking items in this phase", "",
                "---",
                "A gate is an approval record. GitHub is not the authority for it; the repo ledger is.",
            ]),
            "fields": {"Status": "Todo", "Item Type": "Gate", "Phase": pid,
                       "Wave": "Not Applicable", "Baseline Commit": BASELINE_COMMIT},
            "parent": f"PHASE-{pid}",
            "labels": ["consolidation", "gate"],
        })

    for did, title, default, why in DECISIONS:
        items.append({
            "ssot_id": f"DEC-{did}",
            "item_type": "Decision",
            "title": f"DECISION {did} - {title}",
            "body": issue_body([
                f"**{title}**", "",
                "### Recommended default", default, "",
                "### Why it matters", why, "",
                "### Close criteria",
                "- [ ] Owner decision recorded in the consolidation policy",
                "- [ ] Who may approve exceptions is named", "",
                "---",
                "Blocks P1. Execution must not begin while this is open.",
            ]),
            "fields": {"Status": "Todo", "Item Type": "Decision", "Phase": "P1",
                       "Wave": "Not Applicable", "Baseline Commit": BASELINE_COMMIT},
            "parent": "PHASE-P1",
            "labels": ["consolidation", "decision", "blocking"],
        })

    for dl_id, phase, title, desc in DELIVERABLES:
        items.append({
            "ssot_id": f"DELIV-{dl_id}",
            "item_type": "Deliverable",
            "title": f"{dl_id} - {title}",
            "body": issue_body([f"**{title}**", "", desc, "", "---", f"Deliverable of phase {phase}."]),
            "fields": {"Status": "Todo", "Item Type": "Deliverable", "Phase": phase,
                       "Wave": "Not Applicable", "Baseline Commit": BASELINE_COMMIT},
            "parent": f"PHASE-{phase}",
            "labels": ["consolidation", "deliverable"],
        })

    wave_counts = {}
    for _, _, _, w in MODULES:
        wave_counts[w] = wave_counts.get(w, 0) + 1

    for wid, wname in WAVES:
        items.append({
            "ssot_id": f"WAVE-{wid}",
            "item_type": "Wave",
            "title": f"{wid} {wname} - {wave_counts[wid]} modules",
            "body": issue_body([
                f"**Coverage wave {wid}: {wname}**", "",
                f"{wave_counts[wid]} modules.", "",
                "Waves are work organization, not runtime execution order. Source dependencies and conflicts "
                "may require reviewing several waves together.", "",
                "A shared source document must not be skimmed for one module and then declared complete.",
            ]),
            "fields": {"Status": "Todo", "Item Type": "Wave", "Phase": "P4",
                       "Wave": wid, "Baseline Commit": BASELINE_COMMIT},
            "parent": "PHASE-P4",
            "labels": ["consolidation", "wave"],
        })

    for locator, root, symbol, wave in MODULES:
        is_pilot = locator in PILOT
        items.append({
            "ssot_id": f"MOD-{locator}",
            "item_type": "Module",
            "title": f"{locator} {symbol}" + ("  [PILOT]" if is_pilot else ""),
            "body": issue_body([
                f"**Module root:** `{root}`",
                f"**Canonical symbol:** `{symbol}`",
                f"**Target authority:** `{root}/manifest.json` (subject to Decision D1)",
                f"**Coverage wave:** {wave}",
                "**Pilot module:** " + ("yes" if is_pilot else "no"), "",
                "### Readiness (tracked as independent fields - never collapse them)",
                "- `Schema Valid` - parses and validates against schema v2",
                "- `Spec Ready` - all applicable mandatory fields confirmed; no unknowns blocking",
                "- `Impl Verified` - observed conformance at a recorded commit", "",
                "### Close criteria",
                "- [ ] One designated active JSON authority, approved identity",
                "- [ ] Passes schema and applicable profile completeness rules",
                "- [ ] Every accepted claim traces to evidence and a decision",
                "- [ ] Contracts, process bindings and ownership consistent with the full set", "",
                "---",
                "VERIFIED 2026-09-22: manifest exists at schema_version 1.0.0 with no behavior, applicability or "
                "field_evidence sections, and null contract schema_refs.",
            ]),
            "fields": {
                "Status": "Todo", "Item Type": "Module", "Phase": "P4", "Wave": wave,
                "Schema Valid": "Unknown", "Spec Ready": "Unknown", "Impl Verified": "Unknown",
                "Pilot": "Yes" if is_pilot else "No",
                "Module Root": root, "Baseline Commit": BASELINE_COMMIT,
            },
            "parent": f"WAVE-{wave}",
            "labels": ["consolidation", "module"] + (["pilot"] if is_pilot else []),
        })

    baseline = read_governance("run/baseline.json")
    if baseline["baseline_commit"] != BASELINE_COMMIT:
        raise ValueError("Tracking baseline must match the frozen execution baseline")
    governed = {d["decision_id"]: d for d in read_governance("resolution_decisions.json")["decisions"]}
    phase_status = read_governance("run/phase_status.json")
    execution_policy = read_governance("execution_policy.json")
    independent_work = execution_policy["status"] == "approved_scoped_suspension"
    legacy_mapping = {"D1": "DEC-001", "D2": "DEC-002", "D3": "DEC-006", "D4": "DEC-010",
                      "D5": "DEC-012", "D6": "DEC-015", "D7": "DEC-005"}
    for item in items:
        fields = item["fields"]
        if item["item_type"] in {"Phase", "Gate"}:
            result = phase_status[fields["Phase"]]
            fields["Status"] = "Done" if result["status"] == "PASS" else "Blocked"
            if independent_work and item["item_type"] == "Phase" and fields["Phase"] in {"P0", "P1", "P3", "P4", "P5"}:
                fields["Status"] = "In Progress"
            fields["Blocked Reason"] = result["reason"]
            item["body"] = result["reason"] + "\n\nEvidence: governance/module_consolidation/run/phase_status.json"
        elif item["item_type"] == "Decision":
            decision = governed[legacy_mapping[item["ssot_id"].removeprefix("DEC-")]]
            fields["Status"] = "Done"
            fields["Evidence Ref"] = decision["decision_id"]
            fields["Approver"] = decision["approved_by"]
            item["body"] = decision["decision"] + "\n\nPolicy approved; authority cutover remains blocked. See resolution_decisions.json."
        elif item["item_type"] == "Module":
            short = item["ssot_id"].removeprefix("MOD-")
            candidate = read_governance(f"staging/{short}/manifest.v2.candidate.json")
            fields.update({"Status": "In Progress" if independent_work else "Blocked", "Schema Valid": "Yes" if candidate["reconciliation"]["schema_valid"] else "No",
                           "Spec Ready": "No", "Impl Verified": "No", "Evidence Ref": f"staging/{short}/manifest.v2.candidate.json",
                           "Blocked Reason": "Candidate only; mandatory reconciliation remains; active root is v1."})
            item["body"] = f"Root: {fields['Module Root']}/manifest.json\n\nSchema status describes the v2 candidate. The active root remains v1. Specification readiness and implementation verification are independent."
        elif item["item_type"] in {"Wave", "Deliverable"}:
            fields["Status"] = "In Progress" if independent_work and item["item_type"] == "Wave" else "Blocked"
            fields["Blocked Reason"] = "Consult execution reports for partial artifacts; final authority state has not passed."
    source_count = sum(1 for line in (CONTROL / "run/source_processing_ledger.jsonl").read_text().splitlines() if line.strip())
    return {
        "ssot_version": PLAN_VERSION,
        "generated_on": baseline["pinned_at_utc"].split("T")[0],
        "baseline_commit": BASELINE_COMMIT,
        "execution_status": execution_policy["execution_status"],
        "cutover_status": "BLOCKED",
        "repository": "DICKY1987/eafix-modular",
        "authority_note": (
            "This file is the SSOT for consolidation WORK TRACKING only. It is not a module authority and not "
            f"a claim ledger. Source versions ({source_count}) and claims are tracked in the repo ledger, never as "
            "project items."
        ),
        "not_tracked_in_github": [
            f"Individual source versions ({source_count}) - source-processing ledger owns their state",
            "Extracted claims and dispositions - claim ledger owns these",
            "Field-level evidence - module manifests own this",
            "Gate approval evidence - consolidation policy and ledger own this",
        ],
        "items": build_items_sorted(items),
    }

def build_items_sorted(items):
    order = {"Phase": 0, "Gate": 1, "Decision": 2, "Deliverable": 3, "Wave": 4, "Module": 5}
    return sorted(items, key=lambda i: (order[i["item_type"]], i["ssot_id"]))

if __name__ == "__main__":
    doc = build()
    with (Path(__file__).resolve().parent / "eafix_consolidation_ssot.json").open("w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    counts = {}
    for i in doc["items"]:
        counts[i["item_type"]] = counts.get(i["item_type"], 0) + 1
    print("Wrote eafix_consolidation_ssot.json")
    print("Total items:", len(doc["items"]))
    for k in ("Phase", "Gate", "Decision", "Deliverable", "Wave", "Module"):
        print(f"  {k:12s} {counts.get(k,0)}")

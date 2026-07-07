## **Core idea**

Treat the new module system as a **versioned governance system**, not a one-time cleanup.

The current `atomic_module_catalog_vNext` is only `LOCKED_PASS_1`; it locks 34 well-supported module identities, while explicitly deferring EA-side systems, position sizing, CAL8 registry, event-gateway, stub services, and Grafana classification to Pass 2\. It also states that file/service binding is still resolved later during individual manifest generation.

So the project needs a controlled modification process that assumes:

Modules will be added.  
Some modules will split.  
Some will merge.  
Some will be renamed.  
Some will be retired.  
Contracts will change.  
File ownership will move.

The mistake would be treating the Pass 1 catalog as final architecture.

---

# **1\. Use three layers of module records**

Do not put every type of module change directly into the main catalog. Use three different records.

| Layer | File / artifact | Purpose |
| ----- | ----- | ----- |
| **Current state** | `atomic_module_catalog_vNext.json` | The currently approved flat module list |
| **Decision history** | `atomic_module_decomposition_decisions.json` | Why something was kept, split, promoted, deferred, merged, or rejected |
| **Change proposals** | new `module_change_requests/` folder | Proposed future changes before they are accepted |

The decomposition file already performs the decision-history role: it records candidates, origin type, disposition, score, rationale, evidence, and review flags.

The missing piece is a formal **Module Change Request** layer.

---

# **2\. Add a Module Change Request system**

Create one file per proposed architecture modification:

/module\_change\_requests/  
  MCR-2026-0001-split-r1-position-sizing.json  
  MCR-2026-0002-promote-cal8-registry.json  
  MCR-2026-0003-ea-reentry-gate-boundary.json

Use `MCR` for **Module Change Request**.

Each MCR should answer:

{  
  "mcr\_id": "MCR-2026-0001",  
  "title": "Split position sizing from R1\_RISK\_EVALUATOR",  
  "change\_type": "SPLIT\_MODULE",  
  "status": "proposed",  
  "affected\_modules": \["R1\_RISK\_EVALUATOR"\],  
  "proposed\_modules\_added": \["R4\_POSITION\_SIZER"\],  
  "proposed\_modules\_removed": \[\],  
  "proposed\_aliases": \[\],  
  "reason": "Position sizing has distinct rules, evidence, tests, and output contract.",  
  "source\_evidence": \[  
    "atomic\_module\_decomposition\_decisions.json",  
    "Claude\_gen\_atomic module catalog vNext.json",  
    "module\_catalog.json",  
    "process\_step\_catalog.json"  
  \],  
  "contract\_changes": {  
    "new\_contracts": \["PositionSizeDecision"\],  
    "changed\_contracts": \["RiskDecision"\],  
    "removed\_contracts": \[\]  
  },  
  "file\_mapping\_impact": "needs\_review",  
  "process\_impact": "R1 remains approval gate; new R4 feeds R1",  
  "risk\_level": "high",  
  "decision": "pending",  
  "decision\_notes": \[\]  
}

This prevents casual edits to the module list. Every architecture change becomes reviewable and traceable.

---

# **3\. Define allowed module change types**

Use a fixed enum. Do not allow free-form change types.

| Change type | Meaning |
| ----- | ----- |
| `ADD_MODULE` | Add a new atomic module |
| `SPLIT_MODULE` | One module becomes two or more modules |
| `MERGE_MODULES` | Multiple modules collapse into one |
| `NARROW_SCOPE` | Existing module keeps identity but loses responsibilities |
| `EXPAND_SCOPE` | Existing module gains responsibility |
| `RENAME_SYMBOL` | Symbol changes, numeric ID remains |
| `RETIRE_MODULE` | Module stops being active but ID remains historical |
| `PROMOTE_WORK_CELL` | Former work cell becomes module |
| `PROMOTE_SUBMODULE` | Former submodule becomes module |
| `DEMOTE_TO_INTERNAL` | Former module/submodule becomes internal function |
| `MOVE_TO_SHARED_KERNEL` | Logic becomes shared-kernel module |
| `CHANGE_CONTRACT` | Input/output contracts change |
| `CHANGE_OWNER_FILES` | Source files move between modules |
| `CHANGE_RUNTIME_BOUNDARY` | Runtime/service/channel ownership changes |

This matches the current schema direction. The manifest schema already supports migration states like `promoted_from_work_cell`, `promoted_from_submodule`, `merged_from_multiple_work_cells`, `renamed_from_legacy_alias`, `shared_kernel_extraction`, and `deprecated_alias`.

---

# **4\. Never reuse module IDs**

This should be a hard rule.

Numeric module IDs are permanent.  
Canonical symbols may change.  
Names may change.  
Purpose may change within limits.  
IDs are never reused.

If a module is retired:

{  
  "module\_id": "50000000000000000013",  
  "canonical\_symbol": "R1\_RISK\_EVALUATOR",  
  "identity\_status": "retired",  
  "superseded\_by": \["50000000000000000035"\],  
  "legacy\_aliases": \["R1\_RISK\_EVALUATOR"\]  
}

The schema already treats canonical module identity as a first-class object with `module_id`, `numeric_module_id`, `canonical_symbol`, `legacy_aliases`, `supersedes`, `superseded_by`, `identity_status`, and `identity_model`.

This prevents future AI confusion.

---

# **5\. Separate numeric ID from semantic meaning**

Use the numeric ID as an **opaque permanent handle**.

Use the symbol for human meaning.

Good:

50000000000000000027 \= permanent ID  
R3\_CORRELATION\_GUARD \= human-readable symbol

Bad:

Trying to make the numeric ID encode layer, phase, group, runtime, and order.

Why: the architecture will keep changing. If numeric IDs encode too much meaning, every refactor creates pressure to renumber. Renumbering breaks history.

The current catalog already assigned new IDs `...027` through `...034` after Pass 1 additions, while the domain meaning lives in symbols like `R3_CORRELATION_GUARD`, `U1_DASHBOARD_BACKEND`, and `SK2_IDEMPOTENCY`.

That is the right direction.

---

# **6\. Recommended module symbol pattern**

Use this pattern:

\<DOMAIN\_PREFIX\>\<ORDINAL\>\_\<CAPABILITY\_NAME\>

Examples:

F1\_CONFIG\_PREFERENCES  
D2\_CALENDAR\_SOURCE\_ADAPTER  
C2\_INDICATOR\_ENGINE  
S1\_SIGNAL\_ENGINE  
R3\_CORRELATION\_GUARD  
U2\_GUI\_GATEWAY  
SK2\_IDEMPOTENCY

## **Prefix meanings**

| Prefix | Domain |
| ----- | ----- |
| `F` | Foundation / infrastructure / orchestration |
| `D` | Data ingest / external data normalization |
| `C` | Compute / bars / indicators / feature packaging |
| `S` | Signal and intent |
| `R` | Risk and order-intent compilation |
| `O` | Order management / OMS state |
| `B` | Broker / MT4 bridge |
| `E` | Reentry engine |
| `P` | Platform observability / health / reporting |
| `U` | UI / gateway / operator-facing surfaces |
| `SK` | Shared kernel |
| `EA` | EA-side MQL4 internal modules, if promoted in Pass 2 |
| `GOV` | Governance/documentation tooling, if later treated as modules |

## **Capability-name rules**

Use nouns, not verbs:

Good:

R3\_CORRELATION\_GUARD  
D5\_CAL8\_REGISTRY  
EA2\_REENTRY\_GATE  
SK3\_POSITION\_SIZING  
U3\_MT4\_EXPIRY\_OVERLAY

Avoid vague names:

R3\_RISK\_HELPER  
D5\_CALENDAR\_THING  
EA2\_MANAGER  
SK3\_UTILS

---

# **7\. Ordinal rules**

The ordinal should be **stable inside the prefix**, not necessarily process order.

Recommended policy:

| Case | Rule |
| ----- | ----- |
| Existing module keeps same meaning | Keep ordinal |
| Existing module renamed for collision | New symbol, old symbol becomes alias |
| New module split from existing module | Use next open ordinal in same prefix |
| Module retired | Do not reuse ordinal |
| Module merged | Keep surviving module’s ordinal; retired module becomes alias/superseded |
| Candidate not approved yet | Use `CANDIDATE-...`, not a real ordinal |

Example:

R1\_RISK\_EVALUATOR        // existing approval decision  
R2\_ORDER\_INTENT\_COMPILER // existing order-intent compiler  
R3\_CORRELATION\_GUARD     // promoted work cell  
R4\_POSITION\_SIZER        // possible future split

For Pass 2 EA-side modules:

EA1\_BRIDGE\_RECEIVER  
EA2\_REENTRY\_GATE  
EA3\_EXECUTION\_FEEDBACK  
EA4\_PROFILE\_ROTATOR  
EA5\_FREEZE\_MONITOR

But do not create these until the MT4/Python authority boundary is resolved.

---

# **8\. Use status levels, not deletion**

Every module should have a lifecycle status.

| Status | Meaning |
| ----- | ----- |
| `proposed` | Mentioned in MCR, not accepted |
| `candidate` | Has enough evidence to evaluate |
| `approved` | Accepted into next catalog pass |
| `canonical` | Locked in current catalog |
| `implemented` | Has source/runtime/files bound |
| `manifest_ready` | Has valid atomic manifest |
| `deprecated_alias` | Old symbol retained for traceability |
| `retired` | No longer active, but ID remains reserved |
| `superseded` | Replaced by another module |

Important distinction:

canonical ≠ implemented  
approved ≠ fully documented  
locked identity ≠ complete file binding

Your current catalog explicitly says reconciliation flags are carried forward and that file/service binding is resolved during manifest generation, not by the identity lock itself.

---

# **9\. Add a module change impact checklist**

Every MCR should force a checklist.

| Impact area | Required question |
| ----- | ----- |
| Identity | Does this add, rename, retire, or supersede a module? |
| Contracts | Are input/output contracts added, changed, removed, or versioned? |
| Process | Does this change a process step, phase, dependency, or handoff? |
| Runtime | Does a service, port, MQL4 component, UI product, or channel owner change? |
| Files | Does file ownership change? |
| Tests | Are validators, schemas, or evidence paths affected? |
| Docs | Which manifests, catalogs, crosswalks, and references must update? |
| UI | Does the operator see new controls, fields, alerts, or disabled states? |
| MT4 | Does this change EA behavior, WebRequest, DDE, CSV, socket, DLL, or OrderSend boundaries? |
| Risk | Does this affect sizing, exposure, circuit breakers, order routing, execution, or emergency stop? |

This is where the routing file matters: module architecture work should consult module catalog, process catalog, module map, file mapping, and service references; UI work adds the UI catalog; MT4 work adds the MT4 authority reference and communication channels.

---

# **10\. Add a catalog pass system**

Keep using “Pass” terminology. It is useful.

Recommended structure:

Pass 1: Python pipeline \+ UI/gateway \+ shared kernel identity lock  
Pass 2: EA-side MQL4 decomposition and MT4/Python authority boundary  
Pass 3: Risk sizing / position sizing / correlation refinement  
Pass 4: Calendar identity layer: CAL8 registry decision  
Pass 5: Service inventory reconciliation: event-gateway, data-validator, compliance-monitor  
Pass 6: File ownership lock and manifest generation  
Pass 7: Validator/generator enforcement

Each pass produces:

atomic\_module\_catalog\_vNext\_pass\<N\>.json  
atomic\_module\_decomposition\_decisions\_pass\<N\>.json  
module\_change\_log\_pass\<N\>.json  
module\_crosswalk\_pass\<N\>.json

Only one file should be marked current:

atomic\_module\_catalog.current.json

This avoids “which version should AI use?” problems.

---

# **11\. Add a current-state index**

Create:

module\_system\_index.json

Purpose: tell AI which files are current and which are historical.

Example:

{  
  "current\_catalog": "atomic\_module\_catalog\_vNext\_pass1.json",  
  "current\_schema": "eafix\_unified\_atomic\_module\_schema\_v1\_0\_0.json",  
  "current\_decomposition\_decisions": "atomic\_module\_decomposition\_decisions\_pass1.json",  
  "current\_manifest\_directory": "atomic\_module\_manifests/",  
  "current\_change\_request\_directory": "module\_change\_requests/",  
  "historical\_catalogs": \[\],  
  "deprecated\_files": \[\],  
  "active\_pass": "PASS\_1",  
  "next\_pass\_focus": \[  
    "EA Systems A-G",  
    "position sizing split",  
    "CAL8 registry decision",  
    "event-gateway classification"  
  \]  
}

This would reduce AI context confusion more than almost any other file.

---

# **12\. Maintain a module crosswalk**

Every rename, split, merge, and retirement needs a crosswalk.

{  
  "from": {  
    "symbol": "F1\_FLOW\_ORCHESTRATOR",  
    "status": "legacy\_alias"  
  },  
  "to": {  
    "symbol": "F4\_FLOW\_ORCHESTRATOR",  
    "module\_id": "50000000000000000025"  
  },  
  "change\_type": "RENAME\_SYMBOL",  
  "reason": "Cleared PREFIX\_COLLISION\_F1",  
  "effective\_pass": "PASS\_1"  
}

The Pass 1 catalog already handles this pattern by recording `F1_FLOW_ORCHESTRATOR` as a legacy alias of `F4_FLOW_ORCHESTRATOR` and by recording stale symbols such as `O2_OMS` and `O3_PNL_CLASSIFIER` as legacy aliases.

---

# **13\. Keep manifests downstream of catalog decisions**

Do not hand-edit manifests as architecture changes happen.

The flow should be:

MCR accepted  
  → decomposition decisions updated  
  → flat module catalog updated  
  → crosswalk updated  
  → affected manifests regenerated or patched  
  → validators run  
  → stale manifests marked

The manifest schema already requires sections for authority, identity, classification, process binding, contracts, file ownership, runtime, channels, gates, failure behavior, documentation, migration traceability, reconciliation status, AI context, platform constraints, and staleness policy.

That means manifests should be generated from approved sources, not used as the place where architecture arguments happen.

---

# **14\. Use reconciliation flags as work queues**

The current catalog carries flags like:

NO\_FILES  
SERVICE\_UNBOUND  
SUBMODULE\_UNDOC  
SCOPE\_NARROWED  
EA\_SECOND\_PASS  
NEW\_MODULE  
SAFETY\_CONTROLS  
OWNS\_CHANNEL\_HTTP5001

Do not treat these as defects only. Treat them as **migration work queues**.

Example queues:

| Queue | Meaning |
| ----- | ----- |
| `NO_FILES` | Needs source ownership discovery |
| `SERVICE_UNBOUND` | Needs service/runtime binding |
| `SUBMODULE_UNDOC` | Old submodule docs need disposition |
| `EA_SECOND_PASS` | Needs MT4/Python boundary review |
| `NEW_MODULE` | Needs first manifest and validation evidence |
| `SCOPE_NARROWED` | Needs contract/process update check |
| `SAFETY_CONTROLS` | Needs safety/disabled-state validation |
| `OWNS_CHANNEL_HTTP5001` | Needs communication-channel binding |

This lets you manage migration as a backlog, not as an unstructured cleanup.

---

# **15\. Naming convention for files**

Recommended file names:

## **Catalogs**

atomic\_module\_catalog.pass\_001.json  
atomic\_module\_catalog.pass\_002.json  
atomic\_module\_catalog.current.json

## **Decision logs**

atomic\_module\_decomposition\_decisions.pass\_001.json  
atomic\_module\_decomposition\_decisions.pass\_002.json

## **Change requests**

MCR-2026-0001-split-r1-position-sizing.json  
MCR-2026-0002-promote-d5-cal8-registry.json

## **Crosswalks**

atomic\_module\_crosswalk.pass\_001.json  
atomic\_module\_crosswalk.current.json

## **Manifests**

atomic\_module\_manifests/  
  50000000000000000013\_\_R1\_RISK\_EVALUATOR.manifest.json  
  50000000000000000027\_\_R3\_CORRELATION\_GUARD.manifest.json

Use double underscore between ID and symbol. It makes parsing easier:

\<module\_id\>\_\_\<canonical\_symbol\>.manifest.json

---

# **16\. Naming convention for contracts**

Use contract names that describe data, not actions.

Good:

RiskDecision  
RiskGuardResult  
BrokerOrderEnvelope  
ExecutionReport  
CalendarTrigger  
FeatureFrame  
OperatorCommand

Bad:

RunRisk  
DoTrade  
SendThing  
HandleSignal

If versioning is needed:

RiskDecision\_v1  
RiskDecision\_v2  
OrderIntent\_v1\_2  
ExecutionReport\_v1

Use versioned names only when the schema actually changes incompatibly.

---

# **17\. Naming convention for phases and groups**

Keep phases process-oriented:

PHASE\_A\_CONFIG\_SCHEDULING  
PHASE\_B\_CALENDAR\_INTAKE\_TRIGGERS  
PHASE\_C\_MARKET\_DATA\_INDICATORS  
PHASE\_E\_SIGNAL\_INTENT\_RISK  
PHASE\_G\_ORDER\_ROUTING\_MT4\_EXECUTION  
PHASE\_OBS\_UI\_REPORTING  
PHASE\_XCUT\_SHARED\_KERNEL

Keep groups domain-oriented:

G0\_INFRASTRUCTURE\_PLATFORM  
G1\_DATA\_INGEST  
G2\_COMPUTE\_FEATURE  
G3\_SIGNAL\_INTENT  
G4\_RISK  
G5\_OMS  
G6\_MT4\_BRIDGE  
G7\_REENTRY  
G8\_UI\_GATEWAY  
G10\_SHARED\_KERNEL

The catalog already uses domain group IDs/names, phases, layers, process steps, purposes, input contracts, output contracts, aliases, migration status, review status, and reconciliation flags per module.

---

# **18\. My recommended operating model**

Use this workflow:

1\. Identify issue or architecture refinement  
2\. Create Module Change Request  
3\. Score atomicity / impact  
4\. Decide: add, split, merge, rename, retire, defer  
5\. Update decomposition decisions  
6\. Update flat module catalog  
7\. Update crosswalk  
8\. Regenerate affected manifests  
9\. Run validators  
10\. Update current-state index  
11\. Preserve old IDs and aliases

This gives you controlled evolution without freezing the project too early.

---

## **The main principle**

Do not try to prevent change. **Make change traceable.**

The correct system is not:

final module catalog forever

It is:

current locked catalog  
\+ proposed changes  
\+ decision log  
\+ crosswalk  
\+ generated manifests  
\+ validators  
\+ stale-status tracking

That structure lets the architecture keep evolving while still giving AI a stable, deterministic source of truth.


# EAFIX Unified Atomic Module Manifest — AI Fill Instructions

**Version:** 1.0.0  
**Target schema:** `eafix_unified_atomic_module_schema_v1_0_0.json`  
**Document type:** AI schema interpretation and field-population guide  
**Project:** EA_MOD / HUEY_P / EAFIX Modular Trading System

---

## 1. Purpose of this guide

This guide explains how an AI system must interpret and populate the **EAFIX Unified Atomic Module Manifest**.

The JSON Schema defines which fields are allowed and required. This guide defines what those fields **mean**, what information belongs in each section, what information does **not** belong there, and how AI should handle uncertainty, conflicts, migration history, and source authority.

The goal is to prevent the AI from technically producing valid JSON while placing the wrong information in the wrong location.

---

## 2. Core doctrine

The unified manifest is based on one module-centric rule:

> **The atomic module is the architecture unit, documentation unit, contract owner, file ownership boundary, validation unit, and AI work boundary.**

The manifest must describe **one atomic module only**.

Do not recreate the old layered architecture inside the manifest:

```text
Large module
  -> submodule
      -> work cell
```

The target architecture is:

```text
System / process phase
  -> atomic canonical module
```

Durable responsibilities belong in atomic modules. Temporary implementation tasks belong in task/evidence artifacts. Historical work-cell or submodule origins belong only in `migration_traceability`.

---

## 3. Definition of an atomic module

A module qualifies as atomic when it meets most or all of these conditions:

1. It has one primary responsibility.
2. It accepts declared input contracts.
3. It emits declared output contracts.
4. It owns its implementation files or has a clearly declared file ownership boundary.
5. It has explicit dependencies.
6. It has explicit validation and failure behavior.
7. It can be tested independently.
8. Another module can consume its output without knowing its internals.
9. It does not require another module's private files, private state, helper functions, or internal objects.

A module is probably **not** atomic if its purpose contains multiple unrelated responsibilities joined by phrases like:

```text
and then
also handles
plus manages
responsible for everything related to
```

If a unit is too broad, split it before writing the manifest.

---

## 4. Forbidden architecture patterns

The manifest must not contain permanent nested architecture layers.

Do **not** add these fields to a manifest:

```text
work_cells
work_cell_context
submodules
child_modules
nested_modules
implementation_cells
```

If a former work cell or submodule represents a durable system responsibility, promote it into its own atomic module.

If a former work cell or submodule is only historical context, record it in `migration_traceability`.

If it is only a temporary task, record it in a task packet or evidence file, not in the module manifest.

---

## 5. Global module-to-module boundary rule

A module may ingest only:

1. declared output contracts from upstream modules;
2. approved shared-kernel primitives;
3. explicitly declared external inputs;
4. declared configuration contracts.

A module may **not** ingest another module's:

```text
private files
private state
helper functions
implementation objects
internal database tables
undocumented cache contents
runtime locals
```

If a downstream module needs something, the upstream module must emit it as a declared output contract.

---

## 6. Source authority and conflict handling

When populating a manifest, use the project routing instructions first. The routing instructions determine which project-knowledge files must be consulted for the module, process, communication channel, UI screen, MT4 capability, or validation concern.

Use this authority order unless a more specific route overrides it:

1. Project routing instructions.
2. Canonical module catalog for module identity, responsibility, dependencies, interfaces, and quality gates.
3. Process step catalog / aligned process for process steps, contracts, validation behavior, failure behavior, and phase order.
4. Communication channel catalog for channel IDs, protocol, direction, ports, topics, owners, and data contracts.
5. File-to-module mapping for observed source/test/config/plugin file ownership.
6. Standards registry for active rules, gates, evidence requirements, and enforcement criteria.
7. MT4 authoritative reference for MT4 platform capabilities, limits, WebRequest, DDE, DLL, EA, broker, and terminal behavior.
8. Module map for high-level grouping, service home hints, numeric ID clues, bridge protocol, EA-side systems, and shared libraries.
9. Narrative summaries and simple explanations for orientation only.

If sources conflict:

- Prefer machine-readable canonical JSON over narrative Markdown or prose.
- Prefer active/current documents over legacy documents.
- Prefer explicit source authority over inferred behavior.
- If no source supports a value, mark the value as `unknown`, `needs_review`, `candidate`, or `partial` according to the schema.
- Do not invent values to make the manifest look complete.

---

## 7. Required handling of unknowns

When evidence is incomplete:

```text
Do not guess.
Do not silently omit uncertainty.
Do not fill fields from memory.
Do not turn assumptions into facts.
```

Use explicit uncertainty markers:

```text
unknown
needs_review
candidate
partial
unassigned
conflicted
not_applicable
```

Use `reconciliation_status.known_flags` or `reconciliation_status.reconciliation_notes` to record why the field is uncertain.

---

# 8. Section-by-section fill instructions

---

## 8.1 `schema_version`

### Purpose
Identifies the version of the schema format used by this manifest.

### Put here
- The schema version expected by the validator.
- Example: `1.0.0`.

### Do not put here
- Process version.
- Module implementation version.
- Manifest change history.

---

## 8.2 `document_type`

### Purpose
Identifies the document as a module manifest.

### Put here
A stable document-type value, such as:

```json
"unified_atomic_module_manifest"
```

### Do not put here
- Module kind.
- Runtime type.
- Process phase.

---

## 8.3 `packet_type`

### Purpose
Identifies the manifest as the replacement for old module/work-cell context packets.

### Put here
Exactly:

```json
"atomic_module_manifest"
```

### Do not put here
- `module_context_packet`
- `work_cell_context`
- `submodule_context`

---

## 8.4 `manifest_version`

### Purpose
Tracks the version of this specific module manifest.

### Put here
- Semantic version of the manifest itself.
- Increment when the manifest content changes materially.

### Do not put here
- Schema version.
- Process version.
- Module software release version unless the schema explicitly equates them.

---

## 8.5 `generated_at_utc` and `last_updated_utc`

### Purpose
Record when the manifest was generated or updated.

### Put here
- UTC timestamp.
- ISO 8601 format.

### Do not put here
- Local time without timezone.
- Ambiguous relative dates.

---

## 8.6 `source_authority`

### Purpose
Identifies which project-knowledge files were used and which source wins when conflicts exist.

### Put here
- Required reference documents used to populate the manifest.
- Companion documents used for context.
- Authority priority.
- Conflict-resolution notes.
- Source hashes if available.
- Generated-from file list.

### Do not put here
- Module purpose.
- Runtime configuration.
- Source code files owned by the module.
- Implementation details.

### AI instruction
This section is about **evidence and authority**, not behavior.

If a module involves MT4, communication channels, UI, risk, reentry, calendar, or process contracts, list the route-required documents that govern that area.

---

## 8.7 `module_identity`

### Purpose
Defines exactly which module this manifest describes.

### Put here
- Numeric module ID.
- Canonical symbol.
- Module name.
- Legacy aliases.
- Deprecated identifiers.
- Superseded identifiers.
- Replacement identifiers.
- Identity model.
- Identity status.
- Module status.

### Do not put here
- Purpose.
- File list.
- Process step.
- Service port.
- Communication channel details.

### Good example

```json
{
  "numeric_module_id": "50000000000000010004",
  "canonical_symbol": "RISK_CORRELATION_GUARD",
  "module_name": "Risk Correlation Guard",
  "legacy_aliases": ["R1_4_CORRELATION_GUARDS"],
  "supersedes": ["R1_RISK_EVALUATOR"],
  "identity_status": "canonical",
  "identity_model": "numeric_plus_symbol",
  "status": "active"
}
```

### Bad example

```json
{
  "module_name": "Risk module that does all safety checks and sizing"
}
```

That is not enough identity, and the name implies the module may be too broad.

---

## 8.8 `module_classification`

### Purpose
Classifies the module architecturally.

### Put here
- Module kind.
- Domain group.
- Layer.
- Deployable scope.
- Runtime category.
- MVP classification.
- Tags.

### Do not put here
- Detailed responsibilities.
- Contracts.
- File ownership.
- Process validation rules.

### Examples of module kinds

```text
PIPELINE_STAGE_MODULE
INTEGRATION_BRIDGE_MODULE
INFRA_PLATFORM_MODULE
OBSERVABILITY_REPORTING_MODULE
SHARED_KERNEL_MODULE
UI_MODULE
MQL4_EA_MODULE
DOCUMENTATION_ONLY_MODULE
```

### AI instruction
Classification tells what kind of module this is. It does not define what the module does. Put behavior in `purpose`, `module_scope`, and `contracts`.

---

## 8.9 `purpose`

### Purpose
States why the module exists.

### Put here
- One concise responsibility statement.
- One primary outcome.
- No multiple unrelated responsibilities.

### Do not put here
- A list of tasks.
- General system explanation.
- Historical migration notes.
- Process step details.

### Good example

```text
Evaluate whether a proposed trade violates configured portfolio correlation limits.
```

### Bad example

```text
Evaluate risk, size positions, check margin, manage exposure, assemble the final decision, and prepare order routing.
```

The bad example indicates this should be split into smaller atomic modules.

---

## 8.10 `plain_language_summary`

### Purpose
Explains the module in simple language for AI and human comprehension.

### Put here
- A short non-authoritative explanation.
- Simple analogy only if it clarifies the module.
- No new requirements.

### Do not put here
- Binding requirements.
- Validation gates.
- Contracts.
- Runtime settings.

### Rule
If `plain_language_summary` conflicts with structured fields, the structured fields win.

---

## 8.11 `process_binding`

### Purpose
Places the module in the end-to-end trading lifecycle.

### Put here
- Process ID.
- Process version.
- Phase ID.
- Phase name.
- Step ID.
- Step number.
- Step code.
- Step name.
- Process order.
- Dependency step IDs.
- Upstream modules.
- Downstream modules.
- Responsible entrypoint or component.
- Entrypoint files.
- Output description.
- Loop behavior if applicable.

### Do not put here
- Full source file ownership.
- Communication channel catalog.
- Standards rules.
- Plain-language explanation.

### AI instruction
This section must describe the atomic module's real process position. If the module was split from a larger module, do not blindly copy the old broad step if it no longer matches the new module.

---

## 8.12 `contracts`

### Purpose
Defines what the module accepts and emits.

This is the primary module-to-module boundary.

### Put here
- Input contracts.
- Output contracts.
- Contract schema references.
- Contract files.
- Output description.
- Contract version policy.
- Idempotency key policy.
- Hash/checksum policy.
- Schema validation requirement.
- Rule that only declared outputs may be consumed by other modules.

### Do not put here
- Internal helper objects.
- Private database tables.
- Unversioned vague data names.
- File paths unless they are formal contract files.
- Another module's private implementation object.

### Good example

```json
{
  "input_contracts": ["TradeIntent", "PortfolioState", "CorrelationPolicy"],
  "output_contracts": ["RiskGuardResult"],
  "schema_validation_required": true,
  "consumes_only_declared_outputs": true
}
```

### Bad example

```json
{
  "input_contracts": ["risk_manager.py", "account stuff", "data"]
}
```

### Hard rule
A downstream module may ingest only the output contracts declared here.

---

## 8.13 `module_scope`

### Purpose
Defines what the module owns, what it does not own, and what public behavior it exposes.

### Put here
- Scope in.
- Scope out.
- Responsibilities.
- Forbidden responsibilities.
- Key functions.
- Public API surface.
- Internal-only objects.
- Shared-kernel usage.
- Atomicity statement.

### Do not put here
- File ownership lists.
- Process step metadata.
- Migration history.

### AI instruction
Scope-out is as important as scope-in. If the AI cannot identify what the module is forbidden from doing, the module is not sufficiently bounded.

### Example forbidden responsibilities for a correlation guard

```text
- calculate position size
- route orders
- call MT4
- assemble final RiskDecision
- mutate portfolio state
```

---

## 8.14 `file_ownership`

### Purpose
Defines which files belong to this module and which files AI may or may not edit.

### Put here
- Module root.
- Manifest path.
- Owned files.
- Source files.
- Test files.
- Contract files.
- Documentation files.
- Configuration files.
- Schema files.
- Generated files.
- Evidence files.
- Allowed files.
- Forbidden files.
- Shared files.
- File role index.
- Unassigned candidate files.
- File assignment status.
- File assignment policy reference.
- Ownership derivation notes.

### Do not put here
- Every imported dependency.
- Files owned by upstream/downstream modules.
- External system files.
- Historical file names unless needed for migration traceability.

### Definitions

```text
owned_files = files that are part of this module.
allowed_files = files AI may edit for this module task.
forbidden_files = files AI must not edit while working on this module.
shared_files = files the module may use but does not own.
```

### AI instruction
Do not mark shared infrastructure as owned just because the module imports it.

---

## 8.15 `service_runtime`

### Purpose
Describes how and where the module runs.

### Put here
- Service home.
- Candidate service home.
- Runtime kind.
- Language.
- Microservice port.
- Host.
- Deployment unit.
- Runtime status.
- Startup entrypoints.
- Health endpoint.
- Metrics endpoint.
- External systems.
- Required operator settings.

### Do not put here
- Module purpose.
- Business logic.
- Full communication-channel details.

### Runtime kind examples

```text
python_service
mql4_ea
desktop_ui
dashboard_backend
shared_kernel
external_infrastructure
database
redis_bus
documentation_only
```

---

## 8.16 `communication_channels`

### Purpose
Defines channels this module owns, consumes, publishes to, or subscribes to.

### Put here
- Owned channels.
- Consumed channels.
- Published topics.
- Subscribed topics.
- Fallback hierarchy.
- Channel notes.

For each channel, capture relevant details such as:

```text
channel_id
channel_name
status
direction
protocol
port
host
routes
redis_topics
dde_topic
poll_interval_ms
outbox_pattern
data_contracts
python_files
mt4_files
enabled_by_default
fallback behavior
```

### Do not put here
- The entire project-wide communication catalog.
- Channels unrelated to this module.
- Generic implementation notes that belong in service runtime.

### AI instruction
If a module owns a channel, include it in `owned_channels`. If it only consumes from a channel, include it in `consumed_channels`.

---

## 8.17 `dependencies`

### Purpose
Defines what this module depends on.

### Put here
For each dependency:

```text
target_type
target_id
target_symbol
relationship
reason
optional
version_constraint
consumed_contracts
```

Dependency types may include:

```text
module
external_system
shared_kernel
configuration
communication_channel
database
operator_setting
```

### Do not put here
- Private implementation imports unless they are approved shared-kernel dependencies.
- Historical dependencies no longer active.
- Broad vague dependencies like `system` or `all services`.

### AI instruction
A dependency on another module must be through that module's output contract, not through its private implementation.

---

## 8.18 `standards_and_gates`

### Purpose
Defines the standards, gates, validators, and evidence needed to consider the module valid.

### Put here
- Applicable rule IDs.
- Applicable gate IDs.
- Required gate commands.
- Required validators.
- Standards domains.
- Evidence requirement.
- Evidence paths.
- Blocking gate policy.
- Test coverage minimum.
- Invariants.
- Security scan requirement.
- Contract validation requirement.
- Source traceability requirement.

### Do not put here
- Full text of every standard rule.
- General quality advice.
- Non-enforceable preferences unless marked as guidance.

### AI instruction
Reference rule IDs and gate IDs from the standards registry. Do not duplicate the whole standards registry in every manifest.

A rule becomes blocking only when an enforcement gate exists, has pass/fail criteria, and writes evidence.

---

## 8.19 `state_and_failure_behavior`

### Purpose
Defines how the module validates, fails, retries, falls back, quarantines, and defaults safely.

### Put here
- Validation contract.
- Failure contract.
- State machine reference.
- State machine states.
- Retry policy.
- Fallback policy.
- Quarantine policy.
- Idempotency policy.
- Timeout policy.
- Time standard policy.
- Fail-closed default.
- Risk-off default.

### Do not put here
- Vague error handling statements.
- Implementation code.
- Logging-only behavior unless it is the formal failure output.

### Good example

```text
If the correlation matrix is missing or stale, reject the trade with reason CORRELATION_DATA_UNAVAILABLE and emit RiskGuardResult(REJECT).
```

### Bad example

```text
Handle missing correlation data appropriately.
```

### Default behavior vocabulary

```text
REJECT
CONTINUE
RETRY
HALT
SUPPRESS
QUARANTINE
USE_LAST_KNOWN_GOOD
RISK_OFF
```

---

## 8.20 `documentation_set`

### Purpose
Defines the documentation that belongs to this module and whether that documentation is complete.

### Put here
- Required documents.
- Document status.
- Documentation completeness.
- Missing documents.
- Deprecated submodule documents.
- Plain-language summary reference.
- Generated README reference.
- Verification matrix reference.
- Implementation map reference.
- API interfaces reference.
- Contracts reference.
- State machine reference.

### Expected document examples

```text
module_context.json
contracts.json
state_machine.json
api_interfaces.json
verification_matrix.json
implementation_map.json
README.md
failure_modes.md
acceptance.md
```

### Do not put here
- Permanent submodule definitions.
- Work-cell definitions.
- Full source file ownership list.

### AI instruction
Deprecated submodule documentation may be referenced only for migration traceability. It must not recreate a submodule architecture layer.

---

## 8.21 `migration_traceability`

### Purpose
Records where the atomic module came from.

### Put here
- Migration status.
- Source parent modules.
- Promoted work cells.
- Promoted submodules.
- Source ATONIC steps.
- Source canonical steps.
- Deprecated identifiers.
- Replacement modules.
- Crosswalk references.
- Migration notes.

### Do not put here
- Current responsibilities unless needed to explain migration.
- Current contract authority.
- Permanent child module structures.

### AI instruction
This section is historical. It does not define current architecture ownership.

### Valid examples

```text
Promoted from work cell R1_4_CORRELATION_GUARDS.
Split from old parent module R1_RISK_EVALUATOR.
Maps to canonical step S13.
Maps to ATONIC steps related to risk guard evaluation.
```

---

## 8.22 `reconciliation_status`

### Purpose
Records whether the module manifest is aligned with current project knowledge and source files.

### Put here
- Service binding status.
- Submodule documentation status.
- Mapped file count.
- Owned channel IDs.
- Known flags.
- Stale symbol tokens.
- Kind mismatch flag.
- Layer unassigned flag.
- Prefix collision flag.
- Reconciliation notes.
- Last reconciled timestamp.

### Do not put here
- Manually invented audit results.
- Requirements.
- Contracts.
- Runtime behavior.

### AI instruction
This section should be generated from evidence where possible. If evidence is unavailable, mark it `needs_review`.

### Common flags

```text
SERVICE_UNBOUND
SUBMODULE_UNDOC
KIND_MISMATCH
NO_FILES
STALE_CSV_SYMBOL
LAYER_UNASSIGNED
PREFIX_COLLISION
CHECKLIST_KEY_FMT
```

---

## 8.23 `ai_context`

### Purpose
Gives AI practical guidance for safely using or editing this module.

### Put here
- AI usage guidance.
- Use-when guidance.
- Do-not-use-when guidance.
- Must-remember guidance.
- Safe edit boundary.
- Forbidden assumptions.
- Common failure patterns.
- Context priority.

### Do not put here
- Binding requirements that belong in contracts or gates.
- Source authority that belongs in `source_authority`.
- Runtime settings that belong in `service_runtime`.

### AI instruction
AI context is guidance. It never overrides canonical contracts, authority files, gates, or failure policy.

### Example forbidden assumptions

```text
Do not assume socket transport is enabled.
Do not assume MT4 can run without the desktop terminal open.
Do not assume risk approval implies order routing.
Do not assume a module can read another module's database table directly.
```

---

## 8.24 `platform_constraints`

### Purpose
Captures platform-specific rules that affect implementation.

### Put here
- Platform name.
- Native capability references.
- Known limitation references.
- Required operator settings.
- Broker variability.
- Custom vs native policy.
- MT4 terminal requirements.
- WebRequest settings.
- DDE requirements.
- DLL import requirements.
- Filesystem constraints.
- OS constraints.

### Do not put here
- General design preferences.
- Generic module responsibilities.
- Business logic.

### MT4 example facts

```text
MT4 desktop terminal must remain open for EAs to run.
MT4 web terminal cannot run Expert Advisors.
WebRequest must be enabled for HTTP calls.
DLL imports may be required for socket bridge behavior.
Broker execution behavior can vary.
```

---

## 8.25 `observability`

### Purpose
Defines how the module is monitored, audited, and diagnosed.

### Put here
- Health signals emitted.
- Metrics emitted.
- Log events.
- SLO references.
- Audit events required.
- Alert conditions.

### Do not put here
- General logging advice.
- Standards rule text.
- Failure behavior that belongs in `state_and_failure_behavior`.

### AI instruction
Runtime modules should not fail silently. If a failure can affect trading safety, transport reliability, or process correctness, the module needs an observable event, metric, alert, or health signal.

---

## 8.26 `security_and_safety`

### Purpose
Captures both software security and trading safety constraints.

### Put here
- Trading safety level.
- Admin gate requirement.
- Secrets policy.
- Risk-off behavior on unknown health.
- Manual operator confirmation requirement.
- Forbidden side effects.
- Sensitive operations.
- Least privilege notes.

### Do not put here
- Generic security advice not tied to the module.
- Standards rule text that belongs in the standards registry.
- Failure policy that belongs in `state_and_failure_behavior`.

### Security examples

```text
no hardcoded secrets
no logging credentials
path validation required
least privilege required
```

### Trading safety examples

```text
risk-off on unknown health
no order execution from non-approved module
no bypassing risk evaluation
manual confirmation required for dangerous operations
```

---

## 8.27 `staleness_policy`

### Purpose
Defines when the manifest must be regenerated or reviewed.

### Put here
- Regenerate-if-changed list.
- Last generated from source list.
- Source hashes.
- Staleness check command.
- Staleness status.

### Do not put here
- General maintenance notes.
- Requirements.
- Current module status.

### Common regenerate triggers

```text
routing instructions change
module catalog changes
process catalog changes
aligned process changes
file-module mapping changes
communication channel catalog changes
standards registry changes
owned source files change
contract schemas change
MT4 authoritative reference changes for MT4-facing modules
UI catalog changes for UI-facing modules
```

---

## 8.28 `notes`

### Purpose
Stores limited non-authoritative clarifications.

### Put here
- Human notes that do not fit elsewhere.
- Clarifying comments.
- Temporary observations marked as non-authoritative.

### Do not put here
- Requirements.
- Contracts.
- Gates.
- Dependencies.
- Failure behavior.
- File ownership.
- Source authority.

### AI instruction
If a note is required for implementation correctness, move it to the correct structured section.

---

# 9. Field population workflow for AI

When creating or updating an atomic module manifest, AI must follow this workflow:

1. Identify the module or candidate atomic module.
2. Apply the project routing instructions to determine required references.
3. Load required reference documents.
4. Resolve identity: numeric ID, canonical symbol, legacy aliases, status.
5. Determine whether the unit is truly atomic.
6. If not atomic, recommend decomposition before completing the manifest.
7. Populate process binding from process catalogs/aligned process documents.
8. Populate contracts from process and module authority documents.
9. Populate file ownership from file-module mapping and module-owned folders.
10. Populate communication channels from communication channel catalog.
11. Populate standards and gates from active standards registry.
12. Populate state/failure behavior from process contracts and module docs.
13. Populate migration traceability from work-cell, submodule, crosswalk, or reconciliation sources.
14. Populate reconciliation status from audit/evidence sources.
15. Mark unknowns explicitly.
16. Validate the manifest against the schema.
17. Record staleness triggers and source files used.

---

# 10. Good vs bad manifest behavior

## Good behavior

```text
The AI says: “This module consumes TradeIntent and emits RiskGuardResult. It must not size orders or assemble RiskDecision. Those are separate modules.”
```

## Bad behavior

```text
The AI says: “This risk module handles all risk behavior, sizing, account checks, and final approval because those were all under R1_RISK_EVALUATOR.”
```

The bad behavior preserves the old oversized module structure.

---

# 11. Migration rules from old model

## Old model

```text
canonical module
  -> submodule
      -> work cell
```

## New model

```text
atomic canonical module
```

## Migration decision table

| Old item type | If durable responsibility | If temporary task | If historical only |
|---|---|---|---|
| Large module | Convert to domain group or split into atomic modules | Not applicable | Record in migration traceability |
| Submodule | Promote to atomic module | Not applicable | Record in migration traceability |
| Work cell | Promote to atomic module | Convert to task/evidence artifact | Record in migration traceability |
| UI screen | Promote only if it owns durable contract/API behavior | Keep as UI task/evidence | Record as UI binding |
| Helper function | Keep internal or move to shared kernel if stable/reusable | Not applicable | Do not promote |

---

# 12. Validation expectations

A completed manifest should pass these checks:

1. It validates against the JSON Schema.
2. It describes exactly one atomic module.
3. It contains no permanent `work_cells` or `submodules` layer.
4. It has explicit input and output contracts.
5. It has explicit scope-in and scope-out.
6. It has clear file ownership.
7. It lists required authority sources.
8. It states validation and failure behavior.
9. It includes applicable standards and gates.
10. It identifies communication channels if relevant.
11. It records migration traceability if derived from prior modules, submodules, or work cells.
12. It marks unresolved items as `needs_review`, `candidate`, `partial`, or `unknown`.
13. It includes a staleness policy.

---

# 13. Final instruction to AI

When filling the unified module manifest, do not optimize for making the file look complete. Optimize for **correct boundaries**.

The manifest is valid only when it makes the following clear:

```text
what this module is
what it owns
what it accepts
what it emits
what it must not do
what files it controls
what contracts it obeys
what channels it uses
what gates prove it is correct
what failures it must handle
what historical structures it replaced
what source files justify the manifest
```

If those answers are unclear, the module is not ready to be treated as an atomic canonical module.

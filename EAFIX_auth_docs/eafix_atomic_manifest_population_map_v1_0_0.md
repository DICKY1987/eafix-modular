# EAFIX Atomic Manifest Population Map v1.0.0

This document describes a fully deterministic mapping from authoritative sources to every field in the unified atomic module manifest used in the EAFIX system.  It is intended to be machine‑readable as well as human‑comprehensible, and it forms the basis for automated manifest generation and validation.

## Introduction

Each atomic module manifest serves as the single point of truth for a module’s identity, classification, process placement, contracts, responsibilities, file ownership, runtime environment, dependencies, gates, behaviours, documentation, migration history and reconciliation status.  To make manifest generation reproducible, every field must be populated from a well defined source using an explicit rule, with fallbacks, validation and provenance.  No field may be invented.  When information is missing, the manifest must clearly say so using the status markers defined below.

### Authority order

When multiple sources can provide a value, the following authority order MUST be respected.  Earlier sources override later ones; if they disagree the field is marked `conflicted` and requires manual review.

1. **Project routing file** – defines excluded paths, root directories and high level instructions for documentation control.
2. **Canonical module catalog** – the authoritative list of modules (numeric IDs, symbols, names, statuses, domain group, phase, layer, etc.).
3. **Process step catalog and canonical process** – the 26‑step process definition with phase and step metadata.
4. **Communication channel catalog** – definitions of messaging channels, topics, protocols and routes.
5. **File‑to‑module mapping** – explicit assignment of files to modules, shared kernel or UI products.
6. **Standards registry** – defines compliance rules, gates and invariants.
7. **MT4 authority reference** – authoritative reference for MT4 broker integration modules.
8. **Module map** – mapping of modules to micro‑services, UI surfaces, shared kernel packages or other deployable scopes.
9. **Narrative documentation** – explanatory documents and summaries; they provide orientation only and must never override structured sources.

### Status markers

If a field cannot be populated, the manifest must use one of the following markers:

- `unknown` – no information is currently available.
- `needs_review` – information exists but is incomplete or ambiguous and needs human intervention.
- `candidate` – a value was inferred using heuristics and requires verification.
- `partial` – some information has been found but it does not satisfy completeness criteria.
- `unassigned` – the field intentionally has no value (e.g. module has no output contract).
- `conflicted` – conflicting values have been found across authoritative sources.
- `not_applicable` – the field is not relevant for this module (e.g. a UI module will have no broker port).

### General rule structure

For each field, the population map specifies:

- **field_path** – dotted path within the manifest (e.g. `module_identity.canonical_symbol`).
- **primary_source** – the authoritative document or dataset used first.
- **fallback_sources** – ordered list of alternative sources.
- **join_key** – the key used to match records across sources (usually `numeric_module_id` or `canonical_symbol`).
- **extraction_rule** – how to obtain the value from the source.
- **transform** – any transformation applied (e.g. normalisation, case, trim).
- **validation_rule** – requirements the value must satisfy (format, enumeration, uniqueness).
- **conflict_rule** – how to resolve conflicting values.
- **missing_behavior** – what to do when no source can provide a value.
- **provenance_writeback** – what provenance information to record alongside the value.
- **regeneration_policy** – when to update the field.
- **manual_review_triggers** – conditions that require human intervention.

## Field mappings by manifest section

The following sections describe population rules by manifest section.  For brevity, similar fields are grouped together.  The examples following each section illustrate how the rules apply to selected modules.

### 1 – source_authority

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `source_authority.references` | project routing file (`routing.yaml` or similar) | doc control file `module system as a versioned governance system.txt` | List every authoritative document referenced in the routing file.  For each reference record the relative path, last commit hash and revision tag.  Validate that each file exists.  Mark `needs_review` if any referenced file is missing. |
| `source_authority.authority_priority` | fill‑instructions document | governance glossary | Populate with the ordered list of authority sources as defined above.  This is a constant across all modules. |
| `source_authority.hashes` | compute | none | For each referenced source file, compute its SHA‑256 hash and record it. |
| `source_authority.generated_from_files` | compute | none | Record the list of source files used during manifest generation, along with their line ranges and commit hashes. |

### 2 – module_identity

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `module_identity.numeric_module_id` | canonical module catalog (`module_catalog.json`) | decomposition decisions | Read the `module_id` field and convert to an integer.  Validate uniqueness across modules and ensure it is positive.  If missing, mark `needs_review`. |
| `module_identity.canonical_symbol` | canonical module catalog | process step catalog, module map | Read the `symbol` field.  Normalise to uppercase letters with underscores.  Validate that the prefix matches the domain group (see classification).  Mark `conflicted` if multiple symbols exist. |
| `module_identity.module_name` | canonical module catalog | process step catalog, module map | Read the `name` field.  Normalise to title case.  Validate non‑empty and ≤ 64 characters. |
| `module_identity.aliases` | decomposition decisions | module map | List any previous symbols or names for this module.  Remove duplicates and exclude the canonical symbol. |
| `module_identity.superseded_ids` | decomposition decisions | none | List numeric IDs of modules that are superseded by this module. |
| `module_identity.module_status` | canonical module catalog | reconciliation worksheet | Read the `status` field (`active`, `retired`, `needs_review`).  If the module appears in reconciliation with flag `STALE_CSV_SYMBOL` or `RETIRE`, set status accordingly. |
| `module_identity.identity_model` | canonical module catalog | governance glossary | Record the identity model version (e.g. `vNext` or `v1`). |

#### Example: identity mapping for `F1_CONFIG_PREFERENCES`

- `numeric_module_id`: 1 (from module catalog).
- `canonical_symbol`: `F1_CONFIG_PREFERENCES`.
- `module_name`: `Configuration Service`.
- `aliases`: none.
- `superseded_ids`: empty.
- `module_status`: `active`.
- `identity_model`: `vNext`.

### 3 – module_classification

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `module_classification.module_kind` | canonical module catalog | decomposition decisions | Extract the enumerated kind such as `INFRA_PLATFORM_MODULE`, `DATA_INGEST_MODULE`, `COMPUTE_MODULE`, `SIGNAL_MODULE`, `RISK_MODULE`, `ORDER_MODULE`, `BROKER_MODULE`, `REENTRY_MODULE`, `PLATFORM_OBSERVABILITY_MODULE`, `UI_MODULE`, `SHARED_KERNEL_MODULE`, `GATEWAY_MODULE`.  Validate that the value belongs to the allowed list. |
| `module_classification.module_role` | canonical module catalog | process step catalog | Extract the high level role, e.g. `atomic_canonical_module`, `ui_module`, `gateway_module`, `shared_kernel_module`. |
| `module_classification.domain_group_id`, `module_classification.domain_group_name` | canonical module catalog | module map | Read the domain group (e.g. `G0`, `G1`, …).  Cross‑reference with the domain group registry to populate the human‑readable name (e.g. `Infrastructure Platform`, `Data Ingest`, etc.).  Validate that the prefix of `canonical_symbol` matches the group: `F*` → `G0`, `D*` → `G1`, `C*` → `G2`, `S*` → `G3`, `R*` → `G4`, `O*` → `G5`, `B*` → `G6`, `E*` → `G7`, `P*` → `G9`, `U*` → `G8`, `SK*` → `G10`.  If mismatch, flag with `PREFIX_COLLISION`. |
| `module_classification.phase_id` | canonical module catalog | process step catalog | Populate with the phase (e.g. `PHASE_A`, `PHASE_B`, …).  Validate that the phase is consistent with the domain group.  If phase is undefined, leave `unknown`. |
| `module_classification.layer` | canonical module catalog | module map | Populate with layer number (1–6).  Validate that layers increase with domain complexity (foundation = lower layers). |
| `module_classification.deployable_scope` | canonical module catalog | reconciliation worksheet | Read the `deployable_scope` (e.g. `python_service`, `mt4_plugin`, `dashboard_backend`).  Ensure that it corresponds to a service or product and cross‑validate with the file ownership map. |
| `module_classification.runtime_category` | canonical module catalog | service inventory | Populate with the runtime (e.g. `python_service`, `rust_service`, `mt4_plugin`, `dashboard_backend`, `ui_gateway`, `shared_kernel`). |
| `module_classification.mvp_classification` | canonical module catalog | none | Populate with `mvp`, `non_mvp` or `experimental`.  If missing, set to `unknown`. |
| `module_classification.tags` | canonical module catalog | module map | Populate with a list of tags.  Normalise to lowercase, remove duplicates, sort alphabetically. |

### 4 – process_binding

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `process_binding.phase_id` | process step catalog | canonical module catalog | Copy the phase ID from the process definition. |
| `process_binding.phase_name` | process step catalog | none | Copy the human‑readable phase name. |
| `process_binding.step_id` | process step catalog | atonic to canonical crosswalk | Copy the canonical step ID (e.g. `S01`).  If the atonic crosswalk maps the module to multiple steps, choose the step that emits the module’s primary output contract; record others in migration traceability. |
| `process_binding.step_name` | process step catalog | none | Copy the step name.  Validate that it matches the module name. |
| `process_binding.step_order` | process step catalog | canonical module catalog | Copy the numeric order of the step within its phase. |
| `process_binding.dependencies` | process step catalog | communication channel catalog, contract registry | List modules that this module depends on upstream.  Use canonical symbols. |
| `process_binding.upstream_modules` | communication channel catalog | contract registry | List modules that emit contracts consumed by this module. |
| `process_binding.downstream_modules` | communication channel catalog | contract registry | List modules that consume this module’s outputs. |
| `process_binding.responsible_entrypoint` | service inventory | file ownership mapping | Record the function or script that is responsible for invoking this process step (e.g. `src/config/preferences/main.py`). |
| `process_binding.output_description` | contract documentation | canonical process documentation | Summarise the output produced by the module. |

### 5 – contracts

Contracts consist of two lists: `input_contracts` and `output_contracts`.  Each contract entry has the following fields: `contract_name`, `description`, `schema_ref`, `version`, `producer_module`, `consumer_modules`, `idempotency_policy`.

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `contracts.input_contracts`, `contracts.output_contracts` | contract registry (to be created) | contract documentation within service repositories | Because a central contract registry does not yet exist, this section is sparsely populated.  Look inside the service repository under `contracts/` or `schemas/` for JSON schema or YAML definitions.  Parse the file names to derive contract names.  If a contract file contains a `$id` or `title` field, use that as the `contract_name`.  Record the relative path as `schema_ref` and extract the version from file metadata if present.  If no contract information is found, leave the lists empty and mark `needs_review`. |

### 6 – module_scope

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `module_scope.scope_in`, `module_scope.responsibilities` | canonical module catalog (key functions) | decomposition decisions, module map | Populate with a concise list of responsibilities and key functions defined for the module.  Use bullet points. |
| `module_scope.scope_out`, `module_scope.forbidden_responsibilities` | governance docs | none | List responsibilities that must not be performed by this module.  For example, ingest modules must not compile orders. |
| `module_scope.key_functions` | canonical module catalog | service code annotations | List the names of core functions or classes. |
| `module_scope.shared_kernel_use` | canonical module catalog | none | Indicate whether the module is permitted to call shared kernel functions and list them if applicable. |

### 7 – file_ownership

The `file_ownership` section is derived entirely from the file ownership resolution policy (see separate document).  The population map defers to that policy for extraction rules.  For completeness, the fields are as follows:

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `file_ownership.owned_files` | module_file_mapping | service_home, heuristics | List all files exclusively owned by this module. |
| `file_ownership.shared_files` | module_file_mapping | none | List files used by multiple modules. |
| `file_ownership.allowed_files` | module_file_mapping | service_home, governance docs | List files that the module may read or import but must not modify. |
| `file_ownership.forbidden_files` | governance docs | none | List files that the module must not use or modify. |
| `file_ownership.assignment_status` | derived | none | Set to `owned`, `partial`, or `unassigned` based on the presence of owned files. |

### 8 – service_runtime

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `service_runtime.service_home` | service inventory (micro‑service catalog) | file ownership mapping | The root directory of the service implementing the module.  Validate that it exists. |
| `service_runtime.runtime_kind` | service configuration (e.g. Dockerfile) | heuristics based on file extensions | Populate with `python_service`, `rust_service`, `mt4_plugin`, `ui_gateway`, `dashboard_backend`, `shared_kernel`, etc. |
| `service_runtime.language` | service configuration | file extensions | Record the primary programming language (Python, Rust, JavaScript, etc.). |
| `service_runtime.port` | service configuration | heuristics | If the service exposes HTTP or gRPC, record the port number. |
| `service_runtime.host` | service configuration | none | Typically `localhost` or internal service name. |
| `service_runtime.entrypoints` | service configuration | file ownership mapping | List of entrypoint scripts or functions. |
| `service_runtime.health_endpoint`, `service_runtime.metrics_endpoint` | service configuration | defaults | If specified, record the paths.  Otherwise default to `/health` and `/metrics`. |
| additional runtime fields | service configuration | none | Populate as per configuration (e.g. environment variables). |

### 9 – communication_channels

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `communication_channels.owned_channels` | communication channel catalog | service configuration | List the names of channels (e.g. Kafka topics, Redis streams) produced by this module. |
| `communication_channels.consumed_channels` | communication channel catalog | service configuration | List channels consumed by this module. |
| `communication_channels.topics`, `protocols`, `routes`, `ports`, `redis`, `dde`, `files` | channel catalog | service configuration | Populate detailed channel metadata such as message topic names, transport protocols (kafka, redis, http), route URIs, port numbers, file paths, etc.  If no channels exist, leave empty and mark `unassigned`. |
| `communication_channels.fallback_behavior` | governance docs | none | Define fallback behaviour if channel subscription fails (e.g. retry, circuit breaker). |

### 10 – dependencies

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `dependencies[]` | canonical module catalog (dependency list) | service configuration (requirements files), process step catalog | Each dependency record must include: `target_type` (`module`, `service`, `contract`, `external_service`, etc.); `target_id` (numeric module ID or external identifier); `target_symbol` (canonical symbol or service name); `relationship` (`calls`, `imports`, `uses`, `produces_for`, etc.); `reason` (concise justification); `optionality` (`required` or `optional`); `version` (if applicable, e.g. dependency version); `consumed_contracts` (list of contract names).  Validate that all referenced modules or services exist. |

### 11 – standards_and_gates

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `standards_and_gates.rule_ids` | standards registry | gating scripts | List the compliance rules relevant to the module (e.g. `CSG001`, `SEC_CHECK_01`). |
| `standards_and_gates.gate_ids` | standards registry | none | List gate identifiers that must run for this module (e.g. `quality_gate`, `security_gate`). |
| `standards_and_gates.commands` | gating scripts | none | List shell commands or scripts used to run the gates. |
| `standards_and_gates.validators` | gating scripts | none | List validator classes or functions. |
| `standards_and_gates.evidence_paths` | gating scripts | none | List file paths where evidence of compliance is stored (e.g. test reports, coverage reports). |
| `standards_and_gates.blocking_policy` | governance docs | none | Indicate whether failing this gate blocks deployment. |
| `standards_and_gates.invariants` | governance docs | none | List invariants that must always hold (e.g. “no external network access”, “idempotent on retry”). |
| `standards_and_gates.security_contracts` | security docs | none | List security contracts applicable. |
| `standards_and_gates.source_traceability_checks` | gating scripts | none | Indicate whether the module’s code references are traceable back to the manifest sources. |

### 12 – state_and_failure_behavior

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `state_and_failure_behavior.validation_contracts` | contract registry | service configuration | List the validation contracts run on input data. |
| `state_and_failure_behavior.failure_contracts` | contract registry | service configuration | List the failure mode contracts emitted on error. |
| `state_and_failure_behavior.retry_policy` | service configuration | governance docs | Populate with a structured description (e.g. maximum retries, back‑off strategy). |
| `state_and_failure_behavior.fallback_policy` | service configuration | governance docs | Describe fallback actions (e.g. call a default service, return default value). |
| `state_and_failure_behavior.quarantine_policy` | service configuration | governance docs | Describe how malformed inputs or failures are quarantined. |
| `state_and_failure_behavior.idempotency_policy` | service configuration | governance docs | Describe how duplicate requests are handled (e.g. by using idempotency keys). |
| `state_and_failure_behavior.timeout_policy` | service configuration | governance docs | Populate with request and execution timeout settings. |
| `state_and_failure_behavior.fail_closed_default` | governance docs | none | Boolean indicating whether the module should fail closed in case of error. |
| `state_and_failure_behavior.risk_off_default` | governance docs | none | Boolean indicating whether the module should automatically reduce risk exposure on failure. |

### 13 – documentation_set

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `documentation_set.required_docs` | canonical module catalog | governance docs | List of required documentation types (e.g. `README.md`, `CONTRACTS.md`, `STATE.md`, `API.md`, `VERIFICATION.md`). |
| `documentation_set.doc_status` | repository contents | none | For each required document, mark `present`, `missing` or `partial`. |
| `documentation_set.missing_docs` | derived | none | Compute the list of missing documents by comparing `required_docs` and repository contents. |

### 14 – migration_traceability

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `migration_traceability.source_parent_modules` | decomposition decisions | canonical module catalog | List IDs or symbols of modules that this module originated from.  For example, if `F2_EVENT_LOG` replaced part of a larger “Infrastructure Orchestrator” module, list that module. |
| `migration_traceability.promoted_work_cells` | decomposition decisions | module map | List submodules or work cells that have been promoted to first‑class modules. |
| `migration_traceability.atonic_to_canonical_mappings` | atonic to canonical crosswalk | narrative explanation | For each canonical process step, list the ATONIC step IDs that map to it along with the relationship classification (`CANONICAL_ONLY`, `ONE_TO_MANY`, `PARTIAL`, `ATONIC_ONLY`). |
| `migration_traceability.deprecated_ids` | decomposition decisions | none | List IDs of modules that have been deprecated and superseded by this module. |
| `migration_traceability.crosswalk_references` | atonic crosswalk files | none | List file paths of crosswalks used to populate this section. |

### 15 – reconciliation_status

| field_path | primary_source | fallback_sources | extraction_rule & notes |
| --- | --- | --- | --- |
| `reconciliation_status.service_binding` | reconciliation worksheet | none | Indicate whether the module has a bound micro‑service or is still unbound.  Values: `bound`, `unbound`. |
| `reconciliation_status.mapped_file_count` | file_ownership map | none | The number of files owned by this module. |
| `reconciliation_status.owned_channels_count` | communication channel catalog | none | The number of communication channels owned by this module. |
| `reconciliation_status.known_flags` | reconciliation worksheet | none | Copy the list of flags assigned to this module. |
| `reconciliation_status.stale_symbols` | reconciliation worksheet | none | List any stale or mismatched symbols encountered during reconciliation. |
| `reconciliation_status.mismatches` | reconciliation worksheet | none | List mismatches between catalogs (e.g. classification mismatch, service binding mismatch). |
| `reconciliation_status.reconciliation_notes` | reconciliation worksheet | none | Copy any free‑form notes on reconciliation. |

### 16 – AI_context, platform_constraints, observability, safety, staleness_policy

These sections are reserved for future use.  Populate them only when authoritative sources are added.  Until then they should be set to `unknown` or `not_applicable`.

## Manual review triggers

Manual review is required when:

- Any field is marked `conflicted`.
- A mandatory field is `unknown`.
- A field uses `candidate` or `needs_review`.
- The module has no owned files (`assignment_status = unassigned`).
- The prefix of `canonical_symbol` does not match its domain group.
- The module has mismatched phase or layer information.
- The module’s contracts cannot be located.
- The module’s responsible entrypoint cannot be determined.
- A channel or dependency references a non‑existent module.

## Regeneration policy

The population map should be re‑executed whenever:

- The project routing file, canonical module catalog, process step catalog, communication channel catalog, file mapping, standards registry, MT4 reference, module map or narrative documents change.
- A new module is added, split, merged or retired.
- The file ownership resolution policy is updated.
- A contract registry is introduced or modified.
- The standards registry adds, removes or updates rules or gates.

## Examples for selected modules

### F1_CONFIG_PREFERENCES

- **Identity:** ID `1`, symbol `F1_CONFIG_PREFERENCES`, name `Configuration Service`, status `active`.
- **Classification:** `module_kind=INFRA_PLATFORM_MODULE`, `module_role=atomic_canonical_module`, domain group `G0` / `Infrastructure Platform`, `phase_id=PHASE_A`, `layer=1`, `deployable_scope=python_service`, `runtime_category=python_service`.
- **Process binding:** Phase A, step `S01` / `Configuration Service`, no upstream modules, downstream modules include `F3_CLOCK_SCHEDULER`; dependencies list empty.
- **Contracts:** none defined yet; mark `needs_review`.
- **Scope:** Provide configuration preferences and defaults; must not ingest data or generate orders.
- **File ownership:** Owned files `src/config/preferences/` and tests; no shared files.
- **Service runtime:** service home `services/configuration_service`; runtime kind `python_service`; entrypoint `src/config/preferences/main.py`.
- **Reconciliation status:** `service_binding=bound`, `mapped_file_count > 0`, flags `NO_FILES` removed once files are assigned.

### F3_CLOCK_SCHEDULER

Similar to F1 but with module kind `INFRA_PLATFORM_MODULE`, responsibilities include scheduling process steps; file ownership is currently empty (status `unassigned`) and requires completion; runtime unknown; this triggers `needs_review`.

### D2_CALENDAR_SOURCE_ADAPTER

- **Identity:** ID `3`, symbol `D2_CALENDAR_SOURCE_ADAPTER`, name `Calendar Source Adapter`.
- **Classification:** `module_kind=DATA_INGEST_MODULE`, role `atomic_canonical_module`, domain `G1` / `Data Ingest`, phase `PHASE_B`, layer `2`, deployable scope `python_service`.
- **Process binding:** Phase B, step `S03` / `Calendar Source Adapter`; upstream modules none; downstream includes `D3_CALENDAR_NORMALIZER`.  Dependencies may include market feed modules if used.
- **Contracts:** Input contract `MarketDataFeed` if present; output contract `RawCalendarStream`.  If contract files exist in `contracts/` folder record them; else mark `needs_review`.
- **File ownership:** Owned files in `src/calendar/adapter/` and `src/calendar/ingestor/`; shared file `shared/calendar_ingestor.py` with D3; assignment status `partial`.
- **Service runtime:** service home `services/calendar_ingestor`; runtime `python_service`; port `8084` as recorded in service config; entrypoint `src/calendar/adapter/main.py`; health/metrics endpoints at `/health` and `/metrics`.
- **Reconciliation status:** `service_binding=service_unbound` until service binding is assigned; flags include `SERVICE_UNBOUND`, `KIND_MISMATCH` if classification disagrees with module catalog.

### D3_CALENDAR_NORMALIZER

Similar to D2 but module kind `DATA_INGEST_MODULE` and responsibilities include normalising raw calendar events; shares `shared/calendar_ingestor.py`.

### F2_EVENT_LOG

- **Identity:** ID `5`, symbol `F2_EVENT_LOG`, name `Event Log`.
- **Classification:** `module_kind=INFRA_PLATFORM_MODULE`, domain `G0`, phase `PHASE_A`, layer `1`, deployable scope `python_service`.
- **Process binding:** Step `S05` if defined; output contract `EventAuditLog`.
- **File ownership:** Owned files in `src/event_log/`; shared `shared/logging_utils.py` if used.
- **Service runtime:** service home `services/event_log`; runtime `python_service`; port from config.

These examples illustrate how the rules above result in deterministic population.

## Conclusion

This population map defines deterministic rules for each field in the atomic module manifest.  Automated tools must implement these rules exactly to ensure that manifest generation is reproducible and auditable.  Any deviations, conflicts or missing data must be surfaced using the prescribed status markers to prompt manual intervention and continuous improvement of the underlying authoritative sources.

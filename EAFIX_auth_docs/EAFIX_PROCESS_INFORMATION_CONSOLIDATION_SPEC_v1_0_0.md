# EAFIX Process Information Consolidation and Canonical Operational Document Specification

**Document ID:** `EAFIX-PROCESS-CONSOLIDATION-SPEC`  
**Version:** `1.0.0`  
**Status:** Working consolidation baseline  
**Repository:** `DICKY1987/eafix-modular`  
**Purpose:** Identify every beneficial information type found across EAFIX process documents and define one canonical operational document capable of preserving that information without parallel process authorities.

---

## 1. Problem Statement

The repository contains process information at several levels:

1. End-to-end system lifecycle
2. Phase-level process descriptions
3. Canonical process steps
4. Module-level responsibilities and handoffs
5. Work-cell and single-task procedures
6. Subsystem flows such as calendar, transport, execution, risk, OMS, and reentry
7. Runtime implementation evidence
8. Validation, failure, retry, fallback, and recovery behavior
9. Operator procedures and runbooks
10. Governance and documentation-control procedures

The information is fragmented across JSON, YAML, Markdown, text, CSV, manifests, context packets, work-cell records, source files, tests, contracts, runbooks, and generated reports.

The consolidation must not be performed by copying all prose into one larger narrative. That would preserve duplication and contradictions. The correct approach is to:

- inventory every information type;
- normalize equivalent fields;
- preserve unique beneficial fields;
- distinguish required behavior from observed implementation;
- record conflicts rather than silently resolving them;
- create one canonical structured operational-process record;
- generate human-readable process documentation from that record.

---

## 2. Governing Authority Model

### 2.1 Mandatory routing authority

The repository routing document determines which sources must be consulted and which source wins for each subject:

```text
eafix_project_knowledge_reference_routing_instructions.json
```

Current routing rules establish that:

- module identity and responsibilities come from the canonical module catalog;
- process step IDs, step codes, basic handoffs, and dependencies come from the process-step catalog;
- phase grouping and validation/failure contract IDs come from the aligned process;
- communication channel IDs, ports, protocols, directions, and contracts come from the communication-channel catalog;
- physical file-to-module assignments come from the file mapping;
- MT4 platform behavior comes from the MT4 authority;
- calendar deterministic decisions come from the calendar design authority;
- current implementation claims must be verified against source.

### 2.2 Current document authority

The current document-control registry identifies these as canonical process authorities:

```text
EAFIX_auth_docs/01_canonical_registries/updated_trading_process_aligned.json
EAFIX_auth_docs/01_canonical_registries/process_step_catalog.json
EAFIX_auth_docs/01_canonical_registries/module_catalog.json
EAFIX_auth_docs/01_canonical_registries/communication_channels.json
```

These authorities are necessary but not sufficient. They do not contain all beneficial process information found in lower-authority documents.

### 2.3 Conflict rule

The consolidated document must use this general priority:

```text
subject-specific canonical structured source
    >
active governance baseline
    >
verified current source and tests
    >
structured supporting source
    >
source-grounded analysis
    >
subsystem technical specification
    >
historical narrative
    >
implementation sample
```

A lower-authority source may add a field that is absent from higher-authority sources, but it may not silently override an existing canonical value.

---

## 3. Process Document Universe

The following groups contain process information that must be mined.

## 3.1 Canonical end-to-end process records

| Source | Primary information |
|---|---|
| `updated_trading_process_aligned.json` | Process ID/version, phases, phase sequence, step sequence, module sequence, validation IDs, failure IDs, default behavior |
| `process_step_catalog.json` | Stable step IDs, codes, names, owners, inputs, outputs, dependencies, responsible artifacts, entrypoints, validation and failure summaries |
| `module_catalog.json` | Module identities, responsibilities, interfaces, dependencies, process bindings, quality gates, service/runtime hints |
| `communication_channels.json` | Channel identity, direction, protocol, ports, routes, topics, contracts, owners, files, fallback status |
| `ui_catalog.json` | Operator screens, controls, API/WebSocket surfaces, safety states, disabled-state behavior |
| MT4 authority reference | Native MT4 capabilities, constraints, broker variability, platform behavior |
| Calendar deterministic design authority | Calendar identity, normalization, timing, single-writer behavior, blocking and suppression rules |

## 3.2 End-to-end narrative and evidence-grounded specifications

| Source | Unique beneficial information |
|---|---|
| `PROCESS_SPEC_SOURCE_GROUNDED_v1.0.md` | Separation of canonical, microservice, and MT4 realities; implementation evidence; conflicts; planned versus implemented status |
| `source_grounded_trading_process_spec.md` | Granular implemented/planned substeps, runtime artifacts, identifiers, stores, topic mismatches, actual source behavior |
| `EAFIX_ATONIC_ End-to-End Trading Lifecycle Process.md` | Atomic tasks, validation details, failure branches, database and artifact operations |
| `0110000081260118_HUEY_P_UNIFIED_SPECIFICATION.md` | Broad system behavior, architecture, risk, calendar, reentry, execution, and operational details |
| `EAFIX-Modular — End-to-End Module Map.txt` | Module groups, service homes, ports, key functions, subsystem relationships, EA-side systems |

## 3.3 Subsystem process specifications

| Subsystem | Sources and information |
|---|---|
| Trade placement | `0199900080260118_TRADE_PLACEMENT_FLOW.md`: Python-to-MT4 flow, transport selection, atomic writes, heartbeats, execution feedback, timing, failover |
| Reentry | `0199900016260118_The Complete Reentry Trading System- Technical Specification & Process Flow.md`: initialization, matrix loading, signal detection, chain states, decisions, failure branches |
| Calendar | `ECONOMIC_CALENDAR_MVP_SPEC.yaml`, calendar manifests and consolidation files: scope, configuration, timezone, cadence, contracts, blocking windows, fail-safe behavior, tests |
| MT4 bridge | Communication-channel documents, MQL4 references, EA execution documents: transport, polling, socket, file locations, execution behavior |
| Risk | Risk-manager work cells and context packets: position limits, exposure, circuit breakers, correlation, allowed and forbidden dependencies |
| OMS | OMS manifests and context packets: states, transitions, position ownership, close classification |
| Operations | Deployment, monitoring, incident response, service health, backup/recovery, trading incidents, escalation procedures |

## 3.4 Module and single-task records

These must be mined because they contain details often absent from the global process:

```text
manifests/module_manifests/*.manifest.json
context_packets/<module_id>/context_packet.json
context_packets/<module_id>/**/work_cell_context.json
services/*/work_cells/*.json
```

They contribute:

- module and work-cell purpose;
- process-step bindings;
- inputs and outputs;
- allowed and forbidden dependencies;
- source and test files;
- acceptance and validation gates;
- required references;
- file-scope constraints;
- implementation notes.

## 3.5 Supporting operational evidence

```text
file_module_mapping.csv
eafix_services_ai_reference_20260510.json
contract and schema files
tests
observability rules
service configuration
source entrypoints
runtime implementation
runbook indexes
validation reports
```

These sources confirm whether claimed behavior is implemented and identify executable paths, evidence, metrics, limits, and gaps.

## 3.6 Governance processes retained separately

The following define how the operational process is changed, not how trading executes:

```text
module_lifecycle_governance.json
versioned governance system documents
eafix_file_ownership_resolution_policy_v1_0_0.md
eafix_atomic_manifest_population_map_v1_0_0.md
doc_authority.json
module_naming_governance.json
```

The canonical operational document must reference these in its change-control section but must not merge their procedures into the trading execution sequence.

---

## 4. Complete Superset of Relevant Process Fields

The final document must support every field group below.

# 4.1 Document identity and governance

| Field | Purpose |
|---|---|
| `document_id` | Permanent document identity |
| `document_type` | Canonical operational-process authority |
| `schema_version` | Governing schema version |
| `process_id` | Stable process identity |
| `process_name` | Human-readable name |
| `process_version` | Semantic process version |
| `status` | Draft, candidate, canonical, deprecated, superseded |
| `effective_from_utc` | Date version becomes operational |
| `supersedes` | Prior process versions |
| `superseded_by` | Later process version |
| `change_request_refs` | MCR or governance decisions authorizing changes |
| `authority_policy` | Conflict-resolution policy |
| `required_reference_documents` | Mandatory governing references |
| `generated_from_documents` | Source inventory |
| `source_hashes` | Source integrity |
| `last_reconciled_commit` | Repository snapshot used |
| `last_reconciled_utc` | Reconciliation time |
| `document_owner` | Governance owner |
| `approval_status` | Ratification status |
| `known_authority_conflicts` | Unresolved source conflicts |

# 4.2 System purpose and boundaries

| Field | Purpose |
|---|---|
| `primary_business_objective` | What the system accomplishes |
| `operational_outcome` | Final observable outcome |
| `scope_in` | Included behavior |
| `scope_out` | Explicit exclusions |
| `non_goals` | Features intentionally not provided |
| `system_assumptions` | Required environmental assumptions |
| `external_actors` | Broker, operator, calendar provider, MT4 |
| `external_systems` | Redis, file system, databases, APIs |
| `safety_objectives` | Capital and execution safety goals |
| `determinism_objectives` | Repeatability guarantees |
| `availability_objectives` | Operational uptime behavior |
| `mvp_boundary` | Current minimum operational scope |
| `planned_extensions` | Approved future scope |

# 4.3 Process realities

The document must preserve separate views:

```text
required_operational_behavior
current_implementation_behavior
target_future_behavior
```

Each view needs:

| Field | Purpose |
|---|---|
| `behavior_status` | Required, implemented, partial, planned, stub, missing, conflicted, deprecated |
| `evidence_refs` | Proof for the status |
| `implementation_notes` | Difference from required behavior |
| `gap_ids` | Linked gaps |
| `remediation_refs` | Work addressing the gap |

# 4.4 Phase fields

| Field | Purpose |
|---|---|
| `phase_id` | Stable phase identity |
| `phase_code` | Short code |
| `phase_name` | Human-readable name |
| `phase_order` | Deterministic ordering |
| `phase_purpose` | Reason phase exists |
| `entry_conditions` | Conditions required to enter |
| `exit_conditions` | Conditions required to leave |
| `owned_step_ids` | Steps in phase |
| `module_sequence` | Module order |
| `parallelizable_steps` | Parallel work |
| `phase_inputs` | Inputs entering phase |
| `phase_outputs` | Outputs leaving phase |
| `phase_state` | State represented |
| `phase_timeout` | Maximum phase duration |
| `phase_failure_behavior` | Failure result |
| `phase_acceptance_gates` | Required gates |
| `phase_observability` | Metrics and events |
| `phase_runbook_refs` | Operator response |
| `phase_diagram_refs` | Generated visual |

# 4.5 Canonical step identity

| Field | Purpose |
|---|---|
| `step_id` | Permanent numeric step ID |
| `step_code` | Stable readable code |
| `step_number` | Display order |
| `step_name` | Canonical name |
| `step_type` | Transformation, gate, persistence, routing, execution, observation |
| `phase_id` | Parent phase |
| `owner_module_id` | Canonical owner |
| `owner_module_symbol` | Readable owner |
| `supporting_module_ids` | Shared participants |
| `work_cell_ids` | Atomic activities |
| `process_order` | Deterministic order |
| `dependency_step_ids` | Required predecessors |
| `optional_dependency_step_ids` | Optional predecessors |
| `upstream_module_ids` | Upstream modules |
| `downstream_module_ids` | Downstream modules |
| `loop_behavior` | Repetition, cadence, terminal behavior |
| `reentry_point` | Whether process can re-enter here |
| `terminal_step` | Whether step ends a branch |

# 4.6 Trigger and scheduling fields

| Field | Purpose |
|---|---|
| `trigger_id` | Stable trigger identity |
| `trigger_type` | Event, schedule, file, API, operator, state change |
| `trigger_source` | Source system |
| `trigger_condition` | Exact condition |
| `schedule` | Frequency or cron semantics |
| `cadence_seconds` | Poll or execution cadence |
| `debounce_policy` | Duplicate trigger suppression |
| `freshness_window` | Valid trigger age |
| `activation_window` | Time interval where trigger applies |
| `timezone` | Governing timezone |
| `clock_source` | System, broker, UTC, source timezone |
| `startup_trigger` | Startup behavior |
| `manual_trigger_allowed` | Operator initiation |
| `trigger_evidence` | Proof of activation |

# 4.7 Preconditions and guards

| Field | Purpose |
|---|---|
| `precondition_id` | Stable condition identity |
| `condition` | Boolean requirement |
| `source_field` | Input or state inspected |
| `comparison` | Exact comparison |
| `failure_behavior` | Result when false |
| `fail_closed` | Safety posture |
| `risk_off_on_failure` | Whether trading is disabled |
| `operator_override_allowed` | Override policy |
| `override_authority` | Required permission |
| `evidence_required` | Gate evidence |
| `guard_order` | Evaluation sequence |

# 4.8 Input contracts

Each input must include:

```text
contract_name
contract_id
version
schema_ref
producer_module_id
producer_step_id
channel_id
required
cardinality
delivery_semantics
ordering_semantics
freshness_requirement
validation_rules
default_behavior_if_missing
example_ref
sensitive_fields
idempotency_fields
checksum_fields
```

# 4.9 Output contracts

Each output must include:

```text
contract_name
contract_id
version
schema_ref
consumer_module_ids
consumer_step_ids
channel_ids
cardinality
creation_condition
persistence_requirement
retention_policy
ordering_guarantee
idempotency_fields
checksum_fields
example_ref
success_status
partial_output_allowed
```

# 4.10 Atomic activities and transformations

Every step may contain ordered atomic activities:

| Field | Purpose |
|---|---|
| `activity_id` | Stable substep identity |
| `activity_order` | Sequence |
| `activity_name` | Human-readable name |
| `activity_type` | Read, validate, transform, classify, persist, publish, execute |
| `responsible_function` | Function/class |
| `source_files` | Implementation |
| `inputs` | Activity inputs |
| `operation` | Exact action |
| `transformation_rules` | Field-level transformations |
| `calculation_formula` | Mathematical logic |
| `configuration_refs` | Parameters |
| `outputs` | Activity outputs |
| `side_effects` | Writes, messages, orders |
| `branch_refs` | Branches created |
| `validation_refs` | Validation after activity |
| `failure_refs` | Failures possible |
| `test_refs` | Tests |
| `implementation_status` | Actual state |
| `evidence_refs` | Proof |

# 4.11 Branches and decisions

| Field | Purpose |
|---|---|
| `branch_id` | Stable branch identity |
| `decision_name` | Decision being made |
| `evaluation_order` | Priority |
| `condition_expression` | Machine-readable condition |
| `condition_description` | Human explanation |
| `true_target_step_id` | True path |
| `false_target_step_id` | False path |
| `outcome_code` | Result code |
| `default_branch` | Fallback |
| `fail_closed_branch` | Safety branch |
| `reason_code` | Audit explanation |
| `mutually_exclusive` | Branch relationship |
| `exhaustive` | Whether all inputs resolve |
| `decision_evidence` | Logged proof |

# 4.12 State machines and lifecycle

| Field | Purpose |
|---|---|
| `state_machine_id` | Stable state machine |
| `state_id` | Stable state |
| `state_name` | Human state |
| `initial_state` | Starting state |
| `terminal_states` | End states |
| `allowed_transitions` | Transition graph |
| `transition_trigger` | Trigger |
| `transition_guard` | Required condition |
| `transition_action` | Side effect |
| `invalid_transition_behavior` | Failure |
| `state_persistence` | Store |
| `recovery_state` | Restart behavior |
| `state_timeout` | Timeout |
| `state_event` | Emitted event |
| `state_owner_module_id` | Owner |

# 4.13 Validation and acceptance

| Field | Purpose |
|---|---|
| `validation_id` | Stable validation identity |
| `validation_type` | Schema, business, integrity, freshness, safety |
| `rule` | Human rule |
| `machine_rule` | Executable expression |
| `pass_criteria` | Exact pass condition |
| `fail_criteria` | Exact fail condition |
| `validator_ref` | Validator implementation |
| `gate_id` | Blocking gate |
| `blocking` | Whether process stops |
| `evidence_required` | Evidence |
| `evidence_path` | Output |
| `test_refs` | Tests |
| `acceptance_criteria` | Definition of done |
| `coverage_requirement` | Coverage threshold |
| `contract_validation_required` | Contract gate |
| `security_scan_required` | Security gate |

# 4.14 Failure behavior

| Field | Purpose |
|---|---|
| `failure_mode_id` | Stable failure identity |
| `failure_name` | Name |
| `trigger_condition` | Failure condition |
| `affected_step_id` | Step |
| `severity` | Informational, warning, error, critical |
| `default_behavior` | Reject, continue, retry, halt, suppress, quarantine, LKG, risk-off, skip, rollback |
| `fail_closed` | Safety behavior |
| `retry_policy_id` | Retry |
| `fallback_policy_id` | Fallback |
| `quarantine_policy_id` | Quarantine |
| `rollback_policy_id` | Rollback |
| `operator_alert_required` | Alert |
| `alert_id` | Alert definition |
| `incident_class` | Incident category |
| `recovery_step_id` | Resume point |
| `runbook_ref` | Operator procedure |
| `evidence_required` | Proof |
| `error_code` | Stable code |
| `reason_code` | Business reason |

# 4.15 Retry, timeout, fallback, and recovery

Retry:

```text
max_attempts
initial_delay
backoff_type
backoff_multiplier
maximum_delay
jitter_policy
retryable_errors
non_retryable_errors
exhausted_behavior
```

Timeout:

```text
timeout_seconds
clock_source
timeout_start_event
timeout_end_event
timeout_behavior
late_result_behavior
```

Fallback:

```text
primary_path
fallback_path
activation_condition
promotion_condition
demotion_condition
health_requirement
fail_closed
```

Recovery:

```text
restart_behavior
resume_checkpoint
last_known_good_policy
replay_policy
deduplication_after_recovery
rollback_steps
operator_approval
```

# 4.16 Determinism and idempotency

| Field | Purpose |
|---|---|
| `determinism_policy_id` | Stable policy |
| `same_input_same_output_required` | Determinism |
| `ordering_rule` | Stable ordering |
| `tie_breaker_rule` | Equal-time ordering |
| `rounding_rule` | Numeric consistency |
| `timezone_rule` | Time consistency |
| `randomness_policy` | Random seed or prohibition |
| `idempotency_required` | Duplicate safety |
| `idempotency_key_fields` | Key |
| `duplicate_behavior` | Skip, return prior, reject |
| `deduplication_window` | Window |
| `sequence_field` | Sequence |
| `checksum_required` | Integrity |
| `checksum_algorithm` | SHA-256 etc. |
| `checksum_fields` | Covered data |
| `atomic_write_required` | Temp/flush/rename |
| `replay_behavior` | Replay |

# 4.17 Communication channels and transport

| Field | Purpose |
|---|---|
| `channel_id` | Stable channel |
| `channel_name` | Name |
| `status` | Active, disabled, planned |
| `direction` | Producer/consumer |
| `protocol` | HTTP, DDE, file, Redis, socket, REST, WebSocket |
| `host` | Host |
| `port` | Port |
| `routes` | API routes |
| `topics` | Pub/sub topics |
| `file_pattern` | File transport |
| `poll_interval_ms` | Polling |
| `heartbeat_interval` | Heartbeat |
| `heartbeat_timeout` | Timeout |
| `delivery_semantics` | At-most/at-least/exactly once |
| `ordering_semantics` | Ordering |
| `ack_required` | ACK |
| `ack_contract` | ACK data |
| `owning_module_id` | Owner |
| `producer_module_ids` | Producers |
| `consumer_module_ids` | Consumers |
| `contract_refs` | Data |
| `fallback_channel_id` | Fallback |
| `enabled_by_default` | Default |
| `health_check` | Health |

# 4.18 Persistence and artifacts

| Field | Purpose |
|---|---|
| `store_id` | Stable store |
| `store_type` | File, Redis, SQLite, Postgres, memory |
| `path_or_connection_ref` | Location |
| `owner_module_id` | Owner |
| `write_step_ids` | Writers |
| `read_step_ids` | Readers |
| `single_writer_required` | Governance |
| `transaction_policy` | Transaction |
| `append_only` | Append-only |
| `retention` | Retention |
| `archive_policy` | Archive |
| `backup_policy` | Backup |
| `restore_policy` | Restore |
| `schema_ref` | Schema |
| `atomic_write_policy` | Atomic write |
| `file_name_pattern` | Artifacts |
| `generated_at_field` | Freshness |
| `staleness_threshold` | Stale behavior |
| `corruption_behavior` | Corruption |
| `lock_behavior` | File locks |

# 4.19 Configuration and operator settings

| Field | Purpose |
|---|---|
| `config_id` | Configuration identity |
| `config_source` | File/env/UI |
| `schema_ref` | Schema |
| `required_fields` | Required |
| `default_values` | Defaults |
| `allowed_values` | Enums |
| `minimum` / `maximum` | Limits |
| `formula` | Derived value |
| `reload_behavior` | Reload |
| `immutable_after_start` | Snapshot |
| `last_known_good` | LKG |
| `operator_setting` | UI/operator setting |
| `permission_required` | Permission |
| `safety_class` | Safety |
| `change_requires_restart` | Restart |
| `validation_ref` | Validation |

# 4.20 Timing, performance, and service levels

| Field | Purpose |
|---|---|
| `cadence` | Frequency |
| `poll_interval` | Poll |
| `latency_target_ms` | Target |
| `latency_warning_ms` | Warning |
| `latency_critical_ms` | Critical |
| `throughput_target` | Throughput |
| `freshness_requirement` | Freshness |
| `staleness_threshold` | Stale |
| `heartbeat_interval` | Heartbeat |
| `heartbeat_timeout` | Failure |
| `processing_deadline` | Deadline |
| `market_session_constraint` | Session |
| `calendar_window` | Calendar timing |
| `performance_budget_ref` | Budget |
| `slo_id` | SLO |
| `sla_id` | SLA |

# 4.21 Risk, security, and safety

| Field | Purpose |
|---|---|
| `risk_rule_id` | Risk rule |
| `risk_limit` | Limit |
| `risk_unit` | Percent, dollars, lots |
| `aggregation_scope` | Trade, symbol, account, portfolio |
| `block_behavior` | Block |
| `risk_off_behavior` | Risk off |
| `emergency_stop` | Stop |
| `operator_override_policy` | Override |
| `authorization_role` | Authorization |
| `audit_required` | Audit |
| `sensitive_data_fields` | Sensitive data |
| `secrets_policy_ref` | Secrets |
| `security_gate_ids` | Security |
| `broker_constraint_ref` | Broker |
| `safe_default` | Safe default |

# 4.22 Observability

| Field | Purpose |
|---|---|
| `event_id` | Event identity |
| `event_name` | Event |
| `event_contract` | Contract |
| `metric_id` | Metric |
| `metric_name` | Metric |
| `metric_type` | Counter/gauge/histogram |
| `metric_target` | Target |
| `metric_warning` | Warning |
| `metric_critical` | Critical |
| `log_event` | Log |
| `log_level` | Level |
| `trace_id_fields` | Trace |
| `correlation_id_fields` | Correlation |
| `health_endpoint` | Health |
| `metrics_endpoint` | Metrics |
| `alert_id` | Alert |
| `alert_condition` | Condition |
| `alert_duration` | Duration |
| `alert_severity` | Severity |
| `dashboard_refs` | Dashboard |

# 4.23 Runtime binding and implementation evidence

| Field | Purpose |
|---|---|
| `implementation_status` | Implemented, partial, planned, stub, missing, conflicted |
| `service_home` | Service root |
| `runtime_kind` | Python, MQL4, UI, DB |
| `language` | Language |
| `entrypoint_files` | Entrypoints |
| `responsible_functions` | Functions/classes |
| `source_files` | Source |
| `test_files` | Tests |
| `configuration_files` | Config |
| `contract_files` | Contracts |
| `schema_files` | Schemas |
| `documentation_files` | Docs |
| `evidence_files` | Evidence |
| `commit_sha` | Snapshot |
| `source_line_refs` | Exact evidence |
| `test_status` | Test status |
| `runtime_status` | Active, disabled, planned, stub |
| `deployment_unit` | Container, service, EA |
| `microservice_port` | Port |
| `known_runtime_differences` | Variance |

# 4.24 Operator and runbook linkage

| Field | Purpose |
|---|---|
| `operator_action_id` | Stable operator action |
| `action_trigger` | When used |
| `prerequisites` | Prerequisites |
| `commands` | Commands |
| `expected_result` | Result |
| `verification` | Verify |
| `rollback` | Rollback |
| `escalation` | Escalation |
| `required_role` | Role |
| `maintenance_mode_required` | Maintenance |
| `trading_stop_required` | Trading stop |
| `incident_creation_required` | Incident |
| `runbook_ref` | Runbook |
| `automation_status` | Manual/automated |
| `operator_confirmation_required` | Confirmation |

# 4.25 UI bindings

| Field | Purpose |
|---|---|
| `ui_product_id` | UI product |
| `screen_id` | Screen |
| `control_id` | Control |
| `displayed_fields` | Fields |
| `operator_actions` | Actions |
| `disabled_state_rules` | Disabled state |
| `safety_level` | Safety |
| `admin_gate` | Admin |
| `rest_endpoint_refs` | REST |
| `websocket_channel_refs` | WS |
| `refresh_interval` | Refresh |
| `alert_presentation` | Alert |
| `acceptance_criteria` | UI acceptance |

# 4.26 Traceability, conflicts, and gaps

| Field | Purpose |
|---|---|
| `source_refs` | Every source |
| `provenance` | Origin |
| `authority_rank` | Rank |
| `confidence` | Confidence |
| `conflict_id` | Conflict |
| `conflicting_values` | Values |
| `resolution_status` | Resolved/open |
| `resolution_rule` | Rule |
| `decision_ref` | Decision |
| `gap_id` | Gap |
| `gap_type` | Missing implementation, contract, evidence |
| `gap_severity` | Severity |
| `remediation_owner` | Owner |
| `remediation_ref` | Issue/plan |
| `target_version` | Target |
| `staleness_status` | Fresh/stale |
| `regeneration_trigger` | Trigger |

---

## 5. Canonical Document Structure

The final single operational source must be a structured document with this shape:

```json
{
  "document_control": {},
  "authority_and_provenance": {},
  "system_definition": {},
  "operational_realities": {
    "required_behavior": {},
    "current_implementation": {},
    "target_behavior": {}
  },
  "global_policies": {
    "determinism": {},
    "idempotency": {},
    "time": {},
    "safety": {},
    "risk": {},
    "security": {},
    "observability": {}
  },
  "configuration_registry": [],
  "contract_bindings": [],
  "channel_bindings": [],
  "storage_bindings": [],
  "state_machines": [],
  "phases": [
    {
      "phase_identity": {},
      "entry_exit_contract": {},
      "steps": [
        {
          "step_identity": {},
          "ownership": {},
          "runtime_status": {},
          "triggers": [],
          "preconditions": [],
          "inputs": [],
          "atomic_activities": [],
          "branches": [],
          "state_transitions": [],
          "outputs": [],
          "side_effects": [],
          "validations": [],
          "failures": [],
          "retry_timeout_fallback": {},
          "communication": [],
          "persistence": [],
          "configuration": [],
          "timing_and_performance": {},
          "risk_security_safety": {},
          "observability": {},
          "operator_procedures": [],
          "ui_bindings": [],
          "tests_and_evidence": {},
          "implementation_gaps": [],
          "source_traceability": []
        }
      ]
    }
  ],
  "cross_cutting_modules": [],
  "end_to_end_failure_matrix": [],
  "end_to_end_contract_matrix": [],
  "end_to_end_traceability": [],
  "known_conflicts": [],
  "open_gaps": [],
  "change_control": {}
}
```

---

## 6. Per-Step Canonical Record

Every operational step must be populated using the following full record.

```yaml
step_identity:
  step_id:
  step_code:
  step_number:
  step_name:
  step_type:
  phase_id:
  process_order:
  terminal_step:
  loop_behavior:

ownership:
  owner_module_id:
  owner_module_symbol:
  supporting_module_ids:
  work_cell_ids:
  upstream_module_ids:
  downstream_module_ids:
  dependency_step_ids:

required_behavior:
  purpose:
  trigger:
  preconditions:
  input_contracts:
  ordered_activities:
  branch_logic:
  state_transitions:
  output_contracts:
  side_effects:
  success_condition:

current_implementation:
  implementation_status:
  service_home:
  runtime_kind:
  entrypoints:
  responsible_functions:
  source_files:
  test_files:
  evidence_refs:
  differences_from_required:

controls:
  validation_rules:
  acceptance_gates:
  invariants:
  failure_modes:
  retry_policy:
  timeout_policy:
  fallback_policy:
  rollback_policy:
  idempotency_policy:
  determinism_policy:
  fail_closed:
  risk_off_default:

integration:
  channel_refs:
  topic_refs:
  route_refs:
  file_patterns:
  store_refs:
  contract_schema_refs:

configuration:
  setting_refs:
  defaults:
  limits:
  allowed_values:
  formulas:
  reload_behavior:

timing_and_performance:
  cadence:
  freshness:
  latency_target:
  latency_warning:
  latency_critical:
  heartbeat:
  staleness_threshold:

observability:
  events:
  metrics:
  logs:
  alerts:
  dashboards:
  health_checks:

operations:
  operator_actions:
  runbook_refs:
  escalation_refs:
  recovery_checkpoint:
  maintenance_requirements:

traceability:
  source_refs:
  source_line_refs:
  authority_rank:
  conflicts:
  gap_ids:
  remediation_refs:
  last_verified_commit:
```

---

## 7. Source-to-Field Mining Matrix

| Source class | Fields to mine |
|---|---|
| Aligned process | Process/version, phases, step IDs, validation IDs, failure IDs, default behavior |
| Process-step catalog | Step names, owners, inputs, outputs, dependencies, responsible components, entrypoints |
| Module catalog | Module identity, purpose, scope, interfaces, dependencies, quality gates |
| Communication-channel catalog | Channel fields, protocols, ports, topics, routes, owners, contracts, fallback |
| Calendar authority/spec | Timezones, cadence, windows, configuration, normalization, blocking, stale behavior |
| MT4 authority | Platform constraints, execution capabilities, broker variability, native paths, order behavior |
| UI catalog | Screens, controls, REST, WebSocket, disabled states, safety |
| Source-grounded process specs | Actual implementation status, verified files, conflicts, gaps, stores, identifiers |
| ATONIC lifecycle | Atomic actions, detailed validation, failure branches, retries, task ordering |
| Trade-placement flow | Transport sequence, atomic writes, ACK, heartbeat, execution flow, timing |
| Reentry specification | State machine, matrix lookup, generation chain, debouncing, failure branches |
| Module manifests | Process binding, contracts, module scope, files, runtime, gates, failure behavior |
| Work-cell contexts | Atomic purpose, work-cell IDs, source/test files, dependencies, gates |
| Service source | Actual functions, side effects, topics, stores, error behavior |
| Tests | Executable acceptance criteria, edge cases, expected outcomes |
| Runbooks | Operator actions, recovery, rollback, escalation, deployment, incident response |
| Observability rules | Metrics, thresholds, alerts, severity, duration |
| File mapping | Physical implementation ownership and target module |
| Service inventory | Service homes, runtime kind, ports, entrypoints |

---

## 8. Merge Rules

## 8.1 Equivalent fields must be normalized

Examples:

```text
Responsible
responsible
owner
confirmed owner
service owner
```

become:

```text
owner_module_id
responsible_component
responsible_function
```

Examples:

```text
Failure
failure behavior
default failure behavior
failure contract
```

become:

```text
failure_modes[]
```

Examples:

```text
entrypoint_files
responsible file
source file
service main
```

remain distinct:

```text
entrypoint_files
responsible_functions
source_files
```

## 8.2 Do not collapse required and current behavior

A canonical requirement may say:

```text
CalendarEvent is published to eafix.calendar.events
```

Current source may publish:

```text
calendar_events
```

The consolidated record must retain both:

```yaml
required_behavior:
  topic: eafix.calendar.events

current_implementation:
  topic: calendar_events
  implementation_status: conflicted

known_conflicts:
  - conflict_id: ...
```

## 8.3 Do not copy duplicate prose

One normalized record must replace repeated descriptions.

Narratives become generated summaries from the normalized record.

## 8.4 Preserve unique lower-authority detail

A lower-authority document may supply:

- retry counts;
- backoff intervals;
- operator steps;
- timing targets;
- error codes;
- decision branches;
- formulas;
- examples.

Retain the detail if it does not conflict with higher authority. Mark it as `candidate` when not verified.

## 8.5 Conflicting values remain explicit

Each conflict record must include:

```text
conflict_id
field_path
source_a
value_a
authority_a
source_b
value_b
authority_b
recommended_resolution
resolution_status
decision_ref
```

## 8.6 Aspirational behavior must be marked

Do not state that a component operates when evidence only shows:

- a stub;
- a plugin;
- an empty service folder;
- documentation;
- a deleted file;
- a test fixture;
- a planned configuration.

## 8.7 Examples must not become requirements

Example IDs, port numbers, thresholds, file names, and commands must be tagged as examples unless governed by a canonical source.

---

## 9. Consolidation Workflow

## Phase 1 — Deterministic inventory

1. Enumerate all files in approved process-document paths.
2. Search content for process, phase, step, flow, lifecycle, runbook, procedure, work cell, state, branch, validation, failure, input, output, trigger, and handoff.
3. Exclude archived/superseded paths by default.
4. Record every candidate in a process-document inventory.
5. Classify each by domain, scope, authority, and lifecycle status.
6. Confirm no current file is omitted.

Output:

```text
process_document_inventory.json
```

## Phase 2 — Field extraction

For every document:

1. Extract headings and structured keys.
2. Map each source field to the canonical superset field.
3. Record unique values.
4. Record duplicate values.
5. Record conflicts.
6. Record source location and hash.
7. Mark unstructured facts requiring manual review.

Output:

```text
process_field_extraction_inventory.json
```

## Phase 3 — Step and module reconciliation

For every canonical step:

1. Start with aligned process and step catalog.
2. Attach canonical module identity.
3. Add subsystem details.
4. Add module-manifest details.
5. Add work-cell activities.
6. Verify source and tests.
7. Add runtime status.
8. Add contracts, channels, stores, and timing.
9. Add validation and failure behavior.
10. Add runbook links.
11. Add conflicts and gaps.

Output:

```text
eafix_operational_process.candidate.json
```

## Phase 4 — Cross-cutting reconciliation

Reconcile once globally:

- time standard;
- identifier systems;
- checksum policy;
- idempotency;
- file sequence;
- atomic writes;
- transport hierarchy;
- retry policy;
- stale data behavior;
- health and heartbeat;
- logging and traceability;
- risk-off default;
- operator override;
- security and permissions.

## Phase 5 — Validation

Required validations:

```text
unique process IDs
unique phase IDs
unique step IDs
valid module references
valid dependency graph
no orphan inputs
no undeclared outputs
valid channel references
valid contract references
valid state transitions
every failure has behavior
every blocking gate has evidence
every implementation claim has evidence
every planned claim is marked planned
every conflict is visible
every runbook reference resolves
every source reference resolves
deterministic regeneration
```

## Phase 6 — Ratification and projection generation

After approval:

```text
eafix_operational_process.current.json
```

Generate:

```text
EAFIX_OPERATIONAL_PROCESS.generated.md
process_flow.mmd
process_flow.svg
process_contract_matrix.csv
process_failure_matrix.csv
process_implementation_gap_report.json
module_process_views/
phase_process_views/
operator_process_views/
```

## Phase 7 — Supersession

1. Update `doc_authority.json`.
2. Update routing instructions.
3. Mark old end-to-end process narratives superseded.
4. Preserve Git history.
5. Keep subsystem runbooks as referenced operational procedures.
6. Prevent manual changes to generated projections.
7. Require process changes through governance.

---

## 10. Required Final Artifacts

### One authored operational authority

```text
EAFIX_auth_docs/01_canonical_registries/
eafix_operational_process.current.json
```

### One governing schema

```text
EAFIX_auth_docs/01_canonical_registries/
eafix_operational_process.schema.json
```

### Generated human document

```text
EAFIX_auth_docs/03_process_lifecycle_and_crosswalks/
EAFIX_OPERATIONAL_PROCESS.generated.md
```

The JSON is the single source of operational truth. The Markdown is the primary readable projection.

---

## 11. Definition of Complete

The consolidation is complete only when:

- every active process-related document has an inventory record;
- every beneficial field has a canonical destination;
- every canonical process step is fully populated;
- required behavior and actual behavior are separated;
- all 34 modules are represented, including cross-cutting modules not bound to one linear step;
- work-cell details are attached to their parent steps or modules;
- every input and output resolves to a contract;
- every handoff resolves to a channel;
- every persistent artifact resolves to a store;
- every branch resolves to another step or terminal state;
- every failure has deterministic behavior;
- every safety gate declares fail-open or fail-closed;
- every implementation claim has source or test evidence;
- every conflict is resolved or explicitly open;
- every runbook is linked from the failure it handles;
- old process authorities are superseded;
- generated outputs reproduce byte-for-byte from the canonical record.

---

## 12. Final Architectural Rule

```text
One structured process authority owns operational truth.

All other process documents either:
- provide evidence,
- provide governed subsystem data,
- provide operator runbooks,
- provide module context,
- or are generated projections.

No other document may independently redefine the end-to-end process.
```

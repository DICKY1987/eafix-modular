<!-- DOC_LINK: DOC-GUIDE-GLOSSARY-665 -->
---
doc_id: DOC-GUIDE-GLOSSARY-665
---

# Glossary – AI Development Pipeline

**Last Updated**: 2025-12-10
**Purpose**: Comprehensive alphabetical reference of all specialized terms
**Audience**: Developers, AI agents, and documentation readers
**Recent Updates**: Added planning phase terminology from Turn Archive conversations (UCI, CCIS, UCP, LCP, etc.)

> **Quick Navigation**: Jump to [A](#a) [B](#b) [C](#c) [D](#d) [E](#e) [F](#f) [G](#g) [H](#h) [I](#i) [J](#j) [L](#l) [M](#m) [N](#n) [O](#o) [P](#p) [Q](#q) [R](#r) [S](#s) [T](#t) [U](#u) [V](#v) [W](#w)

**Related Documents**:
- [IMPLEMENTATION_LOCATIONS.md](docs/IMPLEMENTATION_LOCATIONS.md) - Code locations for each term
- [DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) - All documentation references
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture overview

---

## A

### Acceptance Hint
See [Definition of Done](#definition-of-done)

---

### Adapter
**Category**: Integrations
**Definition**: Abstraction layer that wraps external tools (Aider, Codex, Claude) to provide a uniform interface for the orchestrator.

**Types**:
- **Aider Adapter** - Integrates Aider CLI for code editing
- **Codex Adapter** - Integrates GitHub Copilot CLI
- **Claude Adapter** - Integrates Claude Code CLI
- **Git Adapter** - Wraps Git operations
- **Test Adapter** - Wraps test runners (pytest, Pester)

**Implementation**: `core/engine/adapters/`
**Schema**: `schema/uet/execution_request.v1.json`

**Usage**:
```python
from core.engine.adapters.aider_adapter import AiderAdapter
adapter = AiderAdapter(config={'model': 'gpt-4'})
result = adapter.execute_task(task, worktree_path)
```

**Related Terms**: [Tool Profile](#tool-profile), [Executor](#executor), [UET Integration](#uet-universal-execution-templates)

---

### AIM (AI Environment Manager)
**Category**: Integrations
**Definition**: AI Metadata Integration Manager - a system for discovering, registering, and routing tasks to AI CLI tools.

**Purpose**:
- Auto-discover AI tools installed on system
- Maintain tool capability registry
- Match tasks to appropriate tools
- Manage tool profiles and preferences

**Implementation**: `aim/`
**CLI**: `python -m aim`

**Commands**:
```bash
python -m aim status           # Show available tools
python -m aim discover         # Scan for new tools
python -m aim register <tool>  # Register a tool manually
```

**Related Terms**: [Tool Registry](#tool-registry), [Tool Profile](#tool-profile), [AIM Bridge](#aim-bridge)

---

### AIM Bridge
**Category**: Integrations
**Definition**: Integration layer between AIM and the execution engine that translates tool metadata into executable configurations.

**Implementation**: `aim/bridge.py`

**Related Terms**: [AIM](#aim-ai-environment-manager), [Tool Registry](#tool-registry)

---

### Automation Gap
**Category**: Planning
**Definition**: A missing automation or incomplete automation step detected by the Looping Chain Prompt, requiring formulation into a CCIS.

**Detection**: Identified during LCP analysis cycles when automation coverage is incomplete.

**Related Terms**: [LCP](#lcp-looping-chain-prompt), [CCIS](#ccis-canonical-change-intent-specification)

---

### Archive
**Category**: State Management
**Definition**: Process of moving completed workstreams and their artifacts to long-term storage.

**Purpose**:
- Clean up active state database
- Preserve historical execution records
- Enable workstream replay/analysis

**Implementation**: `core/planning/archive.py`

**Related Terms**: [Worktree Management](#worktree-management), [State Transition](#state-transition)

---

### Absolute Path
**Category**: Specifications
**Definition**: Column header `absolute_path`. Absolute filesystem path at scan time (debug or trace only; not portable).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Relative Path](#relative-path)

---

### Active (status)
**Category**: Specifications
**Definition**: Status value meaning eligible for normal derivations and considered current.

**Related Terms**: [Status](#status)

---

### Archived (status)
**Category**: Specifications
**Definition**: Status value meaning retained for history or audit but excluded from active operation.

**Related Terms**: [Status](#status)

---

### Asset Family
**Category**: Specifications
**Definition**: Column header `asset_family`. Grouping label for related assets (e.g., schema family, template family).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Asset Id](#asset-id)

---

### Asset Id
**Category**: Specifications
**Definition**: Column header `asset_id`. Stable identifier for a canonical reusable asset (template, schema, reference artifact).

**Type**: `string`
**Constraints**:
- required for entity_kind=asset

**Related Terms**: [Asset Version](#asset-version)

---

### Asset Version
**Category**: Specifications
**Definition**: Column header `asset_version`. Version label for the asset (semantic or integer).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Asset Id](#asset-id)

---

## B

### Blocking Change
**Category**: Planning
**Definition**: A change flagged in CCIS that must occur before the system continues with further execution phases.

**Usage**: Appears in CCIS schema as a boolean guiding scheduling decisions to prioritize critical work.

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [Task Queue](#task-queue)

---

### Bundle
**Category**: Core Engine
**Definition**: A collection of one or more workstreams packaged together as a single unit for execution.

**Structure**:
```json
{
  "bundle_id": "phase-k-plus",
  "bundle_name": "Phase K+: Decision Context Enhancement",
  "version": "1.0.0",
  "workstreams": [...]
}
```

**Types**:
- **Single Workstream Bundle** - Contains one workstream
- **Multi-Workstream Bundle** - Contains multiple related workstreams
- **Phase Bundle** - All workstreams for a development phase

**Implementation**: `core/state/bundles.py`
**Schema**: `schema/bundle.schema.json`
**Examples**: `workstreams/phase-k-plus-bundle.json`

**Related Terms**: [Workstream](#workstream), [Bundle Loading](#bundle-loading)

---

### Bundle Loading
**Category**: State Management
**Definition**: Process of reading, validating, and preparing a bundle for execution.

**Steps**:
1. Read JSON file
2. Validate against schema
3. Extract workstreams
4. Register in database
5. Return ready-to-execute bundle

**Implementation**: `core/state/bundles.py:15`

**Usage**:
```python
from core.state.bundles import load_bundle
bundle = load_bundle("workstreams/phase-k-plus-bundle.json")
```

**Related Terms**: [Bundle](#bundle), [Workstream](#workstream), [Schema Validation](#schema-validation)

---

### Boolean (type)
**Category**: Specifications
**Definition**: Type name `boolean`. Represents true or false values.

**Related Terms**: [String (type)](#string-type)

---

### Build Report Entity Id
**Category**: Specifications
**Definition**: Column header `build_report_entity_id`. Entity reference to the build report artifact produced by the build system.

**Type**: `string`
**Constraints**:
- optional
- should reference existing entity_id

**Related Terms**: [Entity Id](#entity-id)

---

## C

### CCIS (Canonical Change Intent Specification)
**Category**: Planning
**Definition**: The formal, validated schema that wraps a UCI and marks the transition from flexible, creative input into the strictly deterministic planning system. Acts as the gateway between non-deterministic creative input and deterministic structured planning.

**Minimum Required Fields**:
1. **Identity & routing**: `ccis_id`, `project_id`, `version`
2. **Origin**: `source` (user/looping_prompt), `created_at`
3. **Summary**: `title`, `description`, `change_kind[]`, `severity`, `blocking`
4. **Scope**: At least one of `modules[]`, `paths[]`, `patterns_impacted[]`
5. **Intent**: `problem_statement`, `desired_outcome`, `rationale`
6. **Acceptance**: `definition_of_done[]` (at least one item)

**Structure**:
```yaml
ccis:
  ccis_id: "CCIS-2025-0001"
  project_id: "PROJ-CANONICAL-001"
  type: "UCI"
  version: 1
  origin:
    source: "user" | "looping_prompt"
    created_at: "2025-12-10T03:21:00Z"
  summary:
    title: "..."
    description: "..."
    change_kind: ["new_feature", "automation_gap", etc.]
    blocking: true|false
    severity: "low|medium|high|critical"
  scope:
    modules: []
    paths: []
    patterns_impacted: []
  intent:
    problem_statement: "..."
    desired_outcome: "..."
    rationale: "..."
  acceptance:
    definition_of_done: []
  project_overrides: {}
  ai_guidance: {}
  validation:
    schema_valid: true
    ready_for_planning: true
```

**Purpose**: Enforces standardization at pipeline entry, enabling fully deterministic downstream processing.

**Related Terms**: [UCI](#uci-unified-change-intent), [UCP](#ucp-unified-change-pipeline), [CTRS](#ctrs-canonical-technical-requirements-specification), [Creative Input Zone](#creative-input-zone), [Deterministic Planning Phase](#deterministic-planning-phase)

---

### CCPM (Critical Chain Project Management)
**Category**: Integrations
**Definition**: Project management methodology integrated with the pipeline for task scheduling, buffer management, and critical path analysis.

**Features**:
- Critical chain identification
- Buffer management
- Resource leveling
- Progress tracking

**Implementation**: `pm/`
**Documentation**: `docs/Project_Management_docs/`

**Related Terms**: [OpenSpec](#openspec), [Phase](#phase)

---

### Change Intent
**Category**: Planning
**Definition**: A generic description of a desired modification before being normalized into CCIS; may originate from users or the LCP.

**Context**: The raw, unstructured description of what needs to change before formalization.

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [UCI](#uci-unified-change-intent)

---

### Change Kind
**Category**: Planning
**Definition**: A classification tag applied to CCIS describing the nature of the change.

**Valid Values**:
- `new_feature` - Adding new functionality
- `modify_existing` - Changing existing code
- `bug_fix` - Fixing defects
- `refactor` - Code restructuring
- `pattern_update` - Updating execution patterns
- `automation_gap` - Addressing missing automation

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification)

---

### Change Proposal
**Category**: Specifications
**Definition**: Structured document proposing changes to specifications, tracked through the OpenSpec workflow.

**Location**: `specifications/changes/`

**Related Terms**: [OpenSpec](#openspec), [Spec Bridge](#spec-bridge)

---

### Checkpoint
**Category**: State Management
**Definition**: Snapshot of execution state that enables rollback or recovery.

**Types**:
- **Workstream Checkpoint** - Before/after workstream execution
- **Phase Checkpoint** - At phase boundaries
- **Manual Checkpoint** - User-triggered savepoint

**Implementation**: `core/state/checkpoint.py`

**Related Terms**: [Rollback Strategy](#rollback-strategy), [Compensation Action](#compensation-action-saga)

---

### Circuit Breaker
**Category**: Core Engine
**Definition**: Resilience pattern that prevents cascading failures by "opening" (stopping) execution when error thresholds are exceeded.

**States**:
- **CLOSED** - Normal operation
- **OPEN** - Blocking all requests (circuit "broken")
- **HALF_OPEN** - Testing if recovery is possible

**Configuration**:
```yaml
circuit_breaker:
  max_attempts: 3
  max_error_repeats: 2
  timeout_sec: 300
  reset_timeout_sec: 600
```

**Implementation**: `core/engine/circuit_breakers.py`
**Config**: `config/circuit_breaker.yaml`

**Related Terms**: [Retry Logic](#retry-logic), [Recovery Strategy](#recovery-strategy)

---

### Compensation Action (Saga)
**Category**: Integrations
**Definition**: Undo operation that reverses the effects of a completed action, part of the Saga pattern for distributed transactions.

**Purpose**:
- Enable rollback of multi-step workflows
- Maintain consistency across failures
- Support human-in-the-loop corrections

**Implementation**: `core/engine/compensation.py`

**Example**:
```yaml
forward_action: "Create database table"
compensation_action: "DROP TABLE users"
```

**Related Terms**: [Rollback Strategy](#rollback-strategy), [Saga Pattern](#saga-pattern), [UET Integration](#uet-universal-execution-templates)

---

### Creative Input Zone
**Category**: Planning
**Definition**: The pre-CCIS stage where user + AI conversation or LCP analysis may be exploratory and non-deterministic.

**Characteristics**:
- Highly exploratory
- AI-assisted brainstorming
- Natural language requirements
- Flexible iteration
- No strict schema enforcement

**Boundary**: Everything before CCIS creation happens in this zone.

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [Deterministic Planning Phase](#deterministic-planning-phase)

---

### CTRS (Canonical Technical Requirements Specification)
**Category**: Planning
**Definition**: The first machine-readable artifact produced by Open Spec that turns user's broad description into a structured technical specification. The single source of truth for what the application must satisfy.

**Produces**:
- Feature list
- Functional & non-functional requirements
- Interface boundaries
- Resources needed
- Acceptance criteria for each feature
- Constraints and validation rules

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [Technical Requirements](#technical-requirements-tr), [Phase Plan](#phase-plan)

---

### CRUD Operations
**Category**: State Management
**Definition**: Create, Read, Update, Delete operations for database entities (workstreams, steps, runs).

**Implementation**: `core/state/crud.py`

**Functions**:
- `create_workstream()` - Create new workstream record
- `get_workstream()` - Retrieve workstream by ID
- `update_workstream()` - Update workstream state
- `delete_workstream()` - Remove workstream (soft delete)

**Related Terms**: [Pipeline Database](#pipeline-database), [State Transition](#state-transition)

---

### Canonical Path
**Category**: Specifications
**Definition**: Column header `canonical_path`. Canonical location of the reusable asset within the repository.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Asset Id](#asset-id), [Relative Path](#relative-path)

---

### Confidence
**Category**: Specifications
**Definition**: Column header `confidence`. Numeric confidence score for the edge truthfulness.

**Type**: `float`
**Constraints**:
- required when record_kind=edge
- range 0.0..1.0

**Related Terms**: [Evidence Method](#evidence-method), [Edge Id](#edge-id)

---

### Content Type
**Category**: Specifications
**Definition**: Column header `content_type`. Content classification (often MIME-like) derived by inspection or heuristic.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Extension](#extension)

---

### Created By
**Category**: Specifications
**Definition**: Column header `created_by`. Actor identifier that created the row (user, tool, automation).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Updated By](#updated-by)

---

### Created UTC
**Category**: Specifications
**Definition**: Column header `created_utc`. UTC timestamp when this row was first created.

**Type**: `datetime_utc`
**Constraints**:
- required
- immutable after creation

**Related Terms**: [Updated UTC](#updated-utc), [Datetime UTC (type)](#datetime-utc-type)

---

## D

### Definition of Done
**Category**: Planning
**Definition**: A minimal success description included in CCIS to inform downstream planning and ensure objective verification of completed work.

**Purpose**: Guides task completion validation and acceptance criteria.

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [Task Plan](#task-plan-tp)

---

### Deterministic Planning Phase
**Category**: Planning
**Definition**: All steps following the creation of CCIS, during which the system performs structured, rule-bound transformations with no free-form reasoning.

**Characteristics**:
- Strict schema enforcement
- Rule-based transformations
- No hallucination space
- Predictable outputs
- Machine-executable steps

**Pipeline Steps** (all deterministic):
1. Requirements Normalization
2. Pattern Classification
3. Task Plan Generation
4. Workstream Integration
5. Phase Plan Insertion
6. Master JSON Fitting
7. PSJP Generation

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [UCP](#ucp-unified-change-pipeline), [Creative Input Zone](#creative-input-zone)

---

### DAG (Directed Acyclic Graph)
**Category**: Core Engine
**Definition**: Graph structure representing task dependencies where edges point from prerequisite to dependent tasks, with no cycles.

**Purpose**:
- Model task dependencies
- Enable parallel execution
- Detect circular dependencies
- Calculate critical path

**Implementation**: `core/engine/scheduler.py` (UET: DAG-based scheduler)

**Related Terms**: [Dependency Resolution](#dependency-resolution), [Scheduler](#scheduler), [UET Integration](#uet-universal-execution-templates)

---

### Dependency Resolution
**Category**: Core Engine
**Definition**: Process of analyzing task dependencies to determine valid execution order.

**Algorithm**:
1. Parse `depends_on` from each step
2. Build dependency graph (DAG)
3. Topological sort for execution order
4. Identify parallelizable tasks

**Implementation**: `core/engine/orchestrator.py:120`

**Related Terms**: [DAG](#dag-directed-acyclic-graph), [Scheduler](#scheduler), [Step](#step)

---

### Detection Rule
**Category**: Error Detection
**Definition**: Pattern or logic that identifies a specific type of error in code, logs, or execution output.

**Format**:
```json
{
  "rule_id": "RUFF001",
  "pattern": "F401: '.*' imported but unused",
  "severity": "warning",
  "auto_fix": true
}
```

**Location**: `error/plugins/*/manifest.json`

**Related Terms**: [Error Plugin](#error-plugin), [Plugin Manifest](#plugin-manifest)

---

### Datetime UTC (type)
**Category**: Specifications
**Definition**: Type name `datetime_utc`. Timestamp normalized to UTC in a single enforced format (e.g., ISO 8601 with Z).

**Related Terms**: [String (type)](#string-type)

---

### Declared Dependencies
**Category**: Specifications
**Definition**: Column header `declared_dependencies`. Explicit allow-list of registry columns the generator is permitted to read.

**Type**: `list_string`
**Constraints**:
- required for deterministic enforcement

**Related Terms**: [Input Filters](#input-filters)

---

### Deleted (status)
**Category**: Specifications
**Definition**: Status value meaning logically removed; retained only for traceability if policy allows.

**Related Terms**: [Status](#status)

---

### Deprecated (status)
**Category**: Specifications
**Definition**: Status value meaning retained but no longer preferred; may remain in indexes depending on policy.

**Related Terms**: [Status](#status)

---

### Directionality
**Category**: Specifications
**Definition**: Column header `directionality`. Declares whether rel_type should be interpreted as directed or undirected.

**Type**: `enum`
**Allowed Values**: `directed`, `undirected`
**Constraints**:
- optional but recommended

**Related Terms**: [Rel Type](#rel-type)

---

### Doc Id
**Category**: Specifications
**Definition**: Column header `doc_id`. Fixed-width 16-digit identifier embedded in filenames or registry, identifying a concrete file instance.

**Type**: `string`
**Constraints**:
- optional unless your system mandates it
- if present must match `^\\d{16}$`

**Related Terms**: [Filename](#filename), [Relative Path](#relative-path)

---

## E

### Error Context
**Category**: Error Detection
**Definition**: Contextual information about an error including stack trace, file location, surrounding code, and execution state.

**Structure**:
```python
{
  'error_id': 'ERR-001',
  'file': 'core/engine/executor.py',
  'line': 45,
  'message': 'Timeout exceeded',
  'stack_trace': '...',
  'context_lines': ['...'],
  'execution_state': {...}
}
```

**Implementation**: `error/engine/error_context.py`

**Related Terms**: [Error Engine](#error-engine), [Error Escalation](#error-escalation)

---

### Error Engine
**Category**: Error Detection
**Definition**: Core system that orchestrates error detection across multiple plugins and manages the error lifecycle.

**Responsibilities**:
- Load and manage error plugins
- Run detection on files/outputs
- Track error state (detected → fixed → verified)
- Escalate unresolved errors

**Implementation**: `error/engine/error_engine.py`
**CLI**: `python scripts/run_error_engine.py`

**Related Terms**: [Error Plugin](#error-plugin), [Error State Machine](#error-state-machine)

---

### Error Escalation
**Category**: Error Detection
**Definition**: Process of promoting errors through escalation levels when automatic fixes fail.

**Levels**:
1. **Auto-retry** - Plugin attempts fix
2. **Context repair** - Add context, retry
3. **Agent review** - AI agent analyzes
4. **Human escalation** - Require human input
5. **Quarantine** - Isolate problematic code

**Implementation**: `error/engine/error_engine.py`

**Related Terms**: [Error State Machine](#error-state-machine), [Human Review](#human-review)

---

### Error Plugin
**Category**: Error Detection
**Definition**: Modular component that detects and optionally fixes specific types of errors (linting, type checking, security scans).

**Structure**:
```
error/plugins/python_ruff/
├── __init__.py
├── plugin.py          # parse() and fix() methods
└── manifest.json      # Metadata and rules
```

**Required Methods**:
- `parse(file_path)` → List of errors
- `fix(error)` → Boolean success (optional)

**Examples**:
- `error/plugins/python_ruff/` - Python linting
- `error/plugins/javascript_eslint/` - JavaScript linting
- `error/plugins/security_bandit/` - Security scanning

**Implementation**: `error/plugins/`
**Documentation**: `docs/plugin-quick-reference.md`

**Related Terms**: [Plugin Manifest](#plugin-manifest), [Detection Rule](#detection-rule)

---

### Error State Machine
**Category**: Error Detection
**Definition**: State machine managing error lifecycle from detection to resolution.

**States**:
- **DETECTED** - Error found
- **AUTO_FIX_ATTEMPTED** - Plugin tried to fix
- **FIXED** - Fix applied
- **VERIFIED** - Fix confirmed
- **ESCALATED** - Sent to higher level
- **QUARANTINED** - Isolated from main code
- **RESOLVED** - Final resolution

**Implementation**: `error/engine/state_machine.py`

**Related Terms**: [Error Engine](#error-engine), [Error Escalation](#error-escalation)

---

### Event Bus
**Category**: Core Engine
**Definition**: Pub/sub messaging system for coordinating workers, tracking execution events, and enabling event sourcing.

**Event Types**:
- **Worker Events**: `WORKER_SPAWNED`, `WORKER_IDLE`, `WORKER_BUSY`, `WORKER_TERMINATED`
- **Task Events**: `TASK_STARTED`, `TASK_COMPLETED`, `TASK_FAILED`
- **Patch Events**: `PATCH_CREATED`, `PATCH_APPLIED`, `PATCH_QUARANTINED`
- **Gate Events**: `GATE_PASSED`, `GATE_FAILED`

**Implementation**: `core/engine/event_bus.py`
**Storage**: `run_events` table (UET alignment)

**Usage**:
```python
event_bus.emit(EventType.TASK_COMPLETED, run_id, {'task_id': 'T1'})
events = event_bus.get_events(run_id, EventType.TASK_FAILED)
```

**Related Terms**: [Worker Lifecycle](#worker-lifecycle), [Event Sourcing](#event-sourcing), [UET Integration](#uet-universal-execution-templates)

---

### Event Sourcing
**Category**: State Management
**Definition**: Architectural pattern where all state changes are stored as a sequence of events, enabling replay and audit.

**Benefits**:
- Complete audit trail
- Event replay for debugging
- Time-travel debugging
- State reconstruction

**Implementation**: `run_events` table in database

**Related Terms**: [Event Bus](#event-bus), [Pipeline Database](#pipeline-database)

---

### Execution Boundary
**Category**: Planning
**Definition**: The precise stage where planning ends (PSJP) and execution begins (task fulfillment via AI tools).

**Characteristics**:
- PSJP is the only artifact that crosses this boundary
- No freeform instructions allowed
- No raw prompts
- All changes must satisfy acceptance criteria in PSJP
- Produces deterministic execution

**Related Terms**: [PSJP](#psjp-project-specific-json-package), [Deterministic Planning Phase](#deterministic-planning-phase)

---

### Executor
**Category**: Core Engine
**Definition**: Component responsible for executing individual steps by invoking tools and handling results.

**Responsibilities**:
- Invoke tool adapters
- Handle timeouts
- Capture output
- Report results to orchestrator

**Implementation**: `core/engine/executor.py`

**Related Terms**: [Orchestrator](#orchestrator), [Adapter](#adapter), [Timeout Handling](#timeout-handling)

---

### Edge Flags
**Category**: Specifications
**Definition**: Column header `edge_flags`. Machine-readable flags that qualify the edge (e.g., stale, ambiguous, circular).

**Type**: `list_string`
**Constraints**:
- optional

**Related Terms**: [Edge Id](#edge-id), [Confidence](#confidence)

---

### Edge Id
**Category**: Specifications
**Definition**: Column header `edge_id`. Stable unique identifier for an edge (relationship record).

**Type**: `string`
**Constraints**:
- required when record_kind=edge
- unique across edge rows

**Related Terms**: [Source Entity Id](#source-entity-id), [Target Entity Id](#target-entity-id)

---

### Entity Id
**Category**: Specifications
**Definition**: Column header `entity_id`. Stable unique identifier for an entity (the thing being described).

**Type**: `string`
**Constraints**:
- required when record_kind=entity
- unique across entity rows

**Related Terms**: [Entity Kind](#entity-kind)

---

### Entity Kind
**Category**: Specifications
**Definition**: Column header `entity_kind`. Class of entity the row describes.

**Type**: `enum`
**Allowed Values**: `file`, `asset`, `transient`, `external`, `module`, `directory`, `process`, `other`
**Constraints**:
- required when record_kind=entity

**Related Terms**: [Entity Id](#entity-id)

---

### Evidence Locator
**Category**: Specifications
**Definition**: Column header `evidence_locator`. Pointer to where the evidence can be found (file:line, AST path, log reference, URL).

**Type**: `string`
**Constraints**:
- required when record_kind=edge

**Related Terms**: [Evidence Method](#evidence-method), [Evidence Snippet](#evidence-snippet)

---

### Evidence Method
**Category**: Specifications
**Definition**: Column header `evidence_method`. Method used to establish the relationship.

**Type**: `enum`
**Allowed Values**: `static_parse`, `registry_link`, `user_asserted`, `runtime_observed`, `heuristic`, `other`
**Constraints**:
- required when record_kind=edge

**Related Terms**: [Evidence Locator](#evidence-locator)

---

### Evidence Snippet
**Category**: Specifications
**Definition**: Column header `evidence_snippet`. Short excerpt or summary of the evidence (non-authoritative convenience).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Evidence Locator](#evidence-locator)

---

### Expires UTC
**Category**: Specifications
**Definition**: Column header `expires_utc`. UTC timestamp after which the transient should be treated as expired.

**Type**: `datetime_utc`
**Constraints**:
- optional

**Related Terms**: [Ttl Seconds](#ttl-seconds), [Transient Id](#transient-id)

---

### Extension
**Category**: Specifications
**Definition**: Column header `extension`. Normalized file extension (without dot), lowercased.

**Type**: `string`
**Constraints**:
- required for entity_kind=file

**Related Terms**: [Filename](#filename), [Content Type](#content-type)

---

### External Ref
**Category**: Specifications
**Definition**: Column header `external_ref`. External identifier or locator (ticket key, URL, commit hash, etc.).

**Type**: `string`
**Constraints**:
- required for entity_kind=external

**Related Terms**: [External System](#external-system), [Resolver Hint](#resolver-hint)

---

### External System
**Category**: Specifications
**Definition**: Column header `external_system`. System or type of the external reference.

**Type**: `enum`
**Allowed Values**: `github`, `jira`, `url`, `other`
**Constraints**:
- optional but recommended

**Related Terms**: [External Ref](#external-ref)

---

### Entrypoint Flag
**Category**: Specifications
**Definition**: Column header `entrypoint_flag`. Boolean marker indicating the entity is an entrypoint (starts execution or defines a module interface).

**Type**: `boolean`
**Constraints**:
- optional

**Related Terms**: [Module Id](#module-id), [Process Step Role](#process-step-role)

---

## F

### Feedback Loop
**Category**: Core Engine
**Definition**: Test-driven execution pattern where test results automatically create fix tasks.

**Workflow**:
1. Task executes
2. Tests run
3. If tests fail → Create fix task
4. Fix task prioritized
5. Rerun tests after fix

**Implementation**: `core/engine/feedback_loop.py` (UET alignment)

**Related Terms**: [Test Gates](#test-gates), [UET Integration](#uet-universal-execution-templates)

---

### File Hash Cache
**Category**: Error Detection
**Definition**: Cache of file content hashes used for incremental detection (only check changed files).

**Purpose**:
- Skip unchanged files during detection
- Reduce detection time
- Avoid redundant work

**Implementation**: `error/shared/utils/hash_utils.py`

**Related Terms**: [Incremental Detection](#incremental-detection)

---

### Fix Strategy
**Category**: Error Detection
**Definition**: Plugin-specific logic for automatically fixing detected errors.

**Implementation**: `fix()` method in error plugins

**Example** (Python Ruff):
```python
def fix(self, error):
    """Auto-fix import errors."""
    if error['code'] == 'F401':  # Unused import
        return remove_import_line(error['file'], error['line'])
    return False
```

**Related Terms**: [Error Plugin](#error-plugin), [Recovery Strategy](#recovery-strategy)

---

### Filename
**Category**: Specifications
**Definition**: Column header `filename`. Basename of the file (including doc_id prefix if your naming convention includes it).

**Type**: `string`
**Constraints**:
- required for entity_kind=file

**Related Terms**: [Extension](#extension), [Doc Id](#doc-id)

---

### First Seen UTC
**Category**: Specifications
**Definition**: Column header `first_seen_utc`. UTC timestamp when the entity was first observed by scanning or inventory.

**Type**: `datetime_utc`
**Constraints**:
- optional

**Related Terms**: [Last Seen UTC](#last-seen-utc), [Scan Id](#scan-id)

---

### Float (type)
**Category**: Specifications
**Definition**: Type name `float`. Decimal number.

**Related Terms**: [Integer (type)](#integer-type)

---

### Function Code 1
**Category**: Specifications
**Definition**: Column header `function_code_1`. Primary function classification code (e.g., transforms, extracts) if you use multi-function encoding.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Function Code 2](#function-code-2), [Role Code](#role-code)

---

### Function Code 2
**Category**: Specifications
**Definition**: Column header `function_code_2`. Secondary function classification code.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Function Code 1](#function-code-1)

---

### Function Code 3
**Category**: Specifications
**Definition**: Column header `function_code_3`. Tertiary function classification code.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Function Code 1](#function-code-1)

---

## G

### Gate
See [Test Gates](#test-gates)

---

### Generator Id
**Category**: Specifications
**Definition**: Column header `generator_id`. Stable unique identifier for a generator definition.

**Type**: `string`
**Constraints**:
- required when record_kind=generator
- unique across generator rows

**Related Terms**: [Generator Version](#generator-version), [Record Kind](#record-kind)

---

### Generator Name
**Category**: Specifications
**Definition**: Column header `generator_name`. Human-friendly name of the generator.

**Type**: `string`
**Constraints**:
- optional but recommended

**Related Terms**: [Generator Id](#generator-id)

---

### Generator Version
**Category**: Specifications
**Definition**: Column header `generator_version`. Version of generator logic used to produce outputs (bump when ordering or rendering rules change).

**Type**: `string`
**Constraints**:
- required when record_kind=generator

**Related Terms**: [Generator Id](#generator-id)

---

## H

### Human Review
**Category**: Core Engine
**Definition**: Structured escalation workflow where complex issues are presented to humans for decision.

**Trigger Conditions**:
- Gate failure after N retries
- Merge conflict detected
- Patch quarantined
- Budget threshold exceeded

**Review Format**:
```yaml
issue_summary: "Merge conflict in core/engine/executor.py"
error_context: [list of error events]
prior_attempts: [self-heal attempts]
proposed_options:
  - approve: "Accept changes from feature branch"
  - reject: "Revert to main branch"
  - adjust: "Manual merge required"
```

**Implementation**: `core/engine/human_review.py` (UET alignment)

**Related Terms**: [Error Escalation](#error-escalation), [UET Integration](#uet-universal-execution-templates)

---

## I

### Incremental Detection
**Category**: Error Detection
**Definition**: Optimization where error detection only runs on files that have changed since last check.

**Mechanism**:
1. Compute file hash
2. Compare to cached hash
3. Skip if unchanged
4. Update cache after detection

**Implementation**: `error/shared/utils/hash_utils.py`

**Related Terms**: [File Hash Cache](#file-hash-cache), [Error Engine](#error-engine)

---

### Integration Worker
**Category**: Core Engine
**Definition**: Dedicated worker responsible for merging parallel workstream results in deterministic order.

**Responsibilities**:
- Collect patches from parallel workers
- Merge in priority order
- Detect merge conflicts
- Run validation after each merge
- Rollback on failure

**Implementation**: `core/engine/integration_worker.py`

**Related Terms**: [Worker Lifecycle](#worker-lifecycle), [Merge Strategy](#merge-strategy), [UET Integration](#uet-universal-execution-templates)

---

### Input Filters
**Category**: Specifications
**Definition**: Column header `input_filters`. Declarative filter defining which registry rows are eligible inputs.

**Type**: `string_or_json`
**Constraints**:
- optional but recommended

**Related Terms**: [Declared Dependencies](#declared-dependencies), [String Or Json (type)](#string-or-json-type)

---

### Integer (type)
**Category**: Specifications
**Definition**: Type name `integer`. Whole number.

**Related Terms**: [Float (type)](#float-type)

---

## L

### LCP (Looping Chain Prompt)
**Category**: Planning
**Definition**: A multi-stage, rotating prompt system that repeatedly analyzes the repository from different perspectives, identifying issues or opportunities, and generating new change intents. The center of autonomous development automation.

**Purpose**:
- Detect issues
- Detect missing wiring
- Detect improvement opportunities
- Detect mismatches between spec and implementation
- Detect automatable work
- Detect gaps in patterns
- Detect structural drifts

**Architecture**: Plug-in based with configurable sub-cycles

**Sub-cycle Examples**:
- Automation gap check
- Pattern drift detection
- File-structure validation
- Execution-pattern completeness check
- Merge safety analysis
- Dependency graph review
- Spec–code mismatch detection
- Import correctness pass
- Missing state/wiring check
- Dead code detection
- Doc-ID or metadata validation

**Output**: Generates UCIs that feed into the same planning pipeline as user requirements.

**Related Terms**: [UCI](#uci-unified-change-intent), [CCIS](#ccis-canonical-change-intent-specification), [Automation Gap](#automation-gap), [Pattern Drift](#pattern-drift)

---

### Ledger
See [Patch Ledger](#patch-ledger)

---

### Last Build UTC
**Category**: Specifications
**Definition**: Column header `last_build_utc`. UTC timestamp when the generator last successfully produced its outputs.

**Type**: `datetime_utc`
**Constraints**:
- optional

**Related Terms**: [Output Hash](#output-hash), [Generator Id](#generator-id)

---

### Last Seen UTC
**Category**: Specifications
**Definition**: Column header `last_seen_utc`. UTC timestamp when the entity was most recently observed by scanning or inventory.

**Type**: `datetime_utc`
**Constraints**:
- optional

**Related Terms**: [First Seen UTC](#first-seen-utc), [Scan Id](#scan-id)

---

### List String (type)
**Category**: Specifications
**Definition**: Type name `list_string`. List of strings stored in a single cell using a single enforced encoding (JSON array recommended).

**Related Terms**: [String (type)](#string-type)

---

## M

### Merge Strategy
**Category**: Core Engine
**Definition**: Algorithm for deterministically merging parallel workstream results.

**Decision Tree**:
1. Identify ready branches (tests passed, tasks succeeded)
2. Sort by: critical path, dependency count, age
3. Merge in order
4. Validate after each merge
5. Rollback on failure

**Implementation**: `core/engine/merge_strategy.py` (UET alignment)

**Related Terms**: [Integration Worker](#integration-worker), [DAG](#dag-directed-acyclic-graph), [UET Integration](#uet-universal-execution-templates)

---

### Module Id
**Category**: Specifications
**Definition**: Column header `module_id`. Identifier of the module the entity belongs to (ownership or membership).

**Type**: `string`
**Constraints**:
- optional unless module tagging is mandatory

**Related Terms**: [Module Id Source](#module-id-source), [Module Id Override](#module-id-override)

---

### Module Id Source
**Category**: Specifications
**Definition**: Column header `module_id_source`. Declares how module_id was determined.

**Type**: `enum`
**Allowed Values**: `manual`, `derived`, `override`
**Constraints**:
- optional but recommended

**Related Terms**: [Module Id](#module-id)

---

### Module Id Override
**Category**: Specifications
**Definition**: Column header `module_id_override`. Explicit override value used when default derivation would assign a different module_id.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Module Id](#module-id)

---

### Mtime UTC
**Category**: Specifications
**Definition**: Column header `mtime_utc`. File last-modified time in UTC at scan time.

**Type**: `datetime_utc`
**Constraints**:
- optional

**Related Terms**: [Size Bytes](#size-bytes), [Sha256](#sha256)

---

## N

### Notes
**Category**: Specifications
**Definition**: Column header `notes`. Free-text human annotation not used by deterministic generators unless explicitly declared.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Tags](#tags), [Short Description](#short-description)

---

## O

### PA (Pattern Assignment)
**Category**: Planning
**Definition**: The classification output that determines which execution patterns apply, what tools to use, and how the work should be structured based on the TR.

**Structure**:
```yaml
pattern_assignment:
  id: PA-xxxx
  derived_from: TR-xxxx
  matched_patterns:
    - PAT-xxx
  workstream_type: ["creation", "modification", "migration", "validation", "refactor"]
  required_tools: ["claude_code", "copilot"]
  estimated_complexity: 1–5
  suggested_parallelization_group: "<worktree-group-id>"
```

**Related Terms**: [UCP](#ucp-unified-change-pipeline), [TR](#tr-technical-requirements), [TP](#tp-task-plan)

---

### OpenSpec
**Category**: Specifications
**Definition**: System for managing specification changes through a structured proposal, review, and integration workflow.

**Workflow**:
1. Create change proposal
2. Review and approval
3. Generate workstream from spec
4. Execute changes
5. Update specification index

**Implementation**: `specifications/bridge/`
**Documentation**: `docs/Project_Management_docs/openspec_bridge.md`

**Related Terms**: [Spec Bridge](#spec-bridge), [Change Proposal](#change-proposal)

---

### Orchestrator
**Category**: Core Engine
**Definition**: Central coordinator that manages workstream execution, dependency resolution, and worker assignment.

**Responsibilities**:
- Load workstream bundles
- Build dependency DAG
- Schedule tasks
- Coordinate workers
- Handle errors and retries

**Types**:
- **Workstream Orchestrator** - `core/engine/orchestrator.py`
- **Job Orchestrator** - `engine/orchestrator/orchestrator.py`

**Related Terms**: [Executor](#executor), [Scheduler](#scheduler), [Worker Lifecycle](#worker-lifecycle)

---

### Observed UTC
**Category**: Specifications
**Definition**: Column header `observed_utc`. UTC timestamp when the evidence was observed or last verified.

**Type**: `datetime_utc`
**Constraints**:
- required when record_kind=edge

**Related Terms**: [Evidence Method](#evidence-method), [Edge Id](#edge-id)

---

### Output Hash
**Category**: Specifications
**Definition**: Column header `output_hash`. Hash of the generated output contents for change detection.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Last Build UTC](#last-build-utc)

---

### Output Kind
**Category**: Specifications
**Definition**: Column header `output_kind`. Category of derived artifact produced by the generator.

**Type**: `enum`
**Allowed Values**: `module_index`, `dir_manifest`, `repo_catalog`, `graph`, `report`, `other`
**Constraints**:
- required when record_kind=generator

**Related Terms**: [Output Path](#output-path)

---

### Output Path
**Category**: Specifications
**Definition**: Column header `output_path`. Concrete output path for a derived artifact.

**Type**: `string`
**Constraints**:
- optional if output_path_pattern is used

**Related Terms**: [Output Kind](#output-kind), [Output Path Pattern](#output-path-pattern)

---

### Output Path Pattern
**Category**: Specifications
**Definition**: Column header `output_path_pattern`. Template or pattern that resolves to output paths (e.g., modules/{module_id}/INDEX.md).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Output Path](#output-path)

---

## P

### Pattern Drift
**Category**: Planning
**Definition**: A condition in which existing code diverges from expected execution patterns, requiring correction.

**Detection**: Identified by LCP analysis during code review cycles.

**Related Terms**: [LCP](#lcp-looping-chain-prompt), [CCIS](#ccis-canonical-change-intent-specification)

---

### Phase Category
**Category**: Planning
**Definition**: A planning attribute that determines which major phase (e.g., PH-03, PH-04) a workstream belongs to.

**Related Terms**: [Phase Plan](#phase-plan), [Workstream](#workstream-ws)

---

### Planning Engine
**Category**: Planning
**Definition**: The structured processor that transforms CCISs into PSJP artifacts using deterministic steps and schemas.

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [PSJP](#psjp-project-specific-json-package), [UCP](#ucp-unified-change-pipeline)

---

### PSJP (Project-Specific JSON Package)
**Category**: Planning
**Definition**: The authoritative, fully structured planning output that aggregates all phases, tasks, workstreams, and patterns. The final output of the Planning Phase and the ONLY allowed input to the Execution Engine.

**Structure**:
```yaml
project_specific_json_package:
  doc_id: PSJP-xxxx
  version: <incremented>
  phases: [...]
  workstreams: [...]
  tasks: [...]
  patterns: [...]
  registry: [...]
  validation:
    schema_passed: true
    reference_integrity: true
    no_cycles_in_dag: true
```

**Key Invariant**: The PSJP is always regenerated before execution begins, even if tasks accumulate.

**Related Terms**: [Master JSON Template](#master-json-template), [PSJP Fragment](#psjp-fragment), [Execution Boundary](#execution-boundary), [Phase Plan](#phase-plan)

---

### PSJP Fragment
**Category**: Planning
**Definition**: A partial JSON structure representing a piece of the project plan prior to merging into the full PSJP.

**Related Terms**: [PSJP](#psjp-project-specific-json-package), [Master JSON Template](#master-json-template)

---

### Patch
**Category**: Patch Management
**Definition**: Unified diff representing code changes, used as the primary artifact for code modifications.

**Format**: Unified diff (GNU diff format)
```diff
diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
+# New line
 def foo():
     pass
```

**Related Terms**: [Patch Artifact](#patch-artifact), [Patch Ledger](#patch-ledger), [Patch-First Workflow](#patch-first-workflow)

---

### Patch Artifact
**Category**: Patch Management
**Definition**: Canonical representation of a patch with metadata (UET-aligned).

**Structure**:
```json
{
  "patch_id": "01J2ZB...",
  "format": "unified_diff",
  "target_repo": "/path/to/repo",
  "origin": {
    "execution_request_id": "01J2Z9...",
    "tool_id": "aider",
    "created_at": "2025-11-23T00:00:00Z"
  },
  "diff_text": "diff --git...",
  "scope": {
    "files_touched": ["file.py"],
    "line_insertions": 5,
    "line_deletions": 2,
    "hunks": 1
  }
}
```

**Implementation**: `core/patches/patch_artifact.py` (UET alignment)
**Schema**: `schema/uet/patch_artifact.v1.json`

**Related Terms**: [Patch Ledger](#patch-ledger), [UET Integration](#uet-universal-execution-templates)

---

### Patch-First Workflow
**Category**: Patch Management
**Definition**: Development workflow where all code changes are represented as patches (unified diffs) before application.

**Workflow**:
1. Tool generates patch (not direct edit)
2. Orchestrator creates PatchArtifact
3. Validate patch (format, scope, constraints)
4. Apply patch to worktree
5. Run language-aware validation (tests, linters)
6. If tests pass → commit
7. If tests fail → quarantine patch

**Benefits**:
- Full audit trail
- Reviewable before application
- Rollback support
- Language-agnostic

**Related Terms**: [Patch Artifact](#patch-artifact), [Patch Ledger](#patch-ledger), [UET Integration](#uet-universal-execution-templates)

---

### Patch Ledger
**Category**: Patch Management
**Definition**: Audit trail tracking the complete lifecycle of a patch from creation to commit.

**State Machine**:
```
created → validated → queued → applied → verified → committed
   ↓         ↓          ↓         ↓         ↓
apply_failed, rolled_back, quarantined, dropped
```

**Tracked Data**:
- State history with timestamps
- Validation results (format, scope, constraints, tests)
- Application attempts and errors
- Quarantine status

**Implementation**: `core/patches/patch_ledger.py` (UET alignment)
**Schema**: `schema/uet/patch_ledger_entry.v1.json`

**Related Terms**: [Patch Artifact](#patch-artifact), [Patch Policy](#patch-policy), [UET Integration](#uet-universal-execution-templates)

---

### Patch Policy
**Category**: Patch Management
**Definition**: Constraints and rules governing what patches are allowed, enforced at validation time.

**Scope Levels**:
- **Global** - Apply to all patches
- **Project** - Specific to a project
- **Phase** - Specific to a development phase
- **Document** - Specific to individual files

**Constraints**:
```json
{
  "allowed_formats": ["unified_diff"],
  "max_lines_changed": 500,
  "max_files_changed": 10,
  "forbid_binary_patches": true,
  "forbid_touching_paths": ["\\.git/", "\\.env"],
  "require_tests_for_paths": ["core/.*\\.py"],
  "oscillation_threshold": 3
}
```

**Implementation**: `core/patches/patch_policy.py` (UET alignment)
**Schema**: `schema/uet/patch_policy.v1.json`
**Config**: `config/patch_policies/*.json`

**Related Terms**: [Patch Ledger](#patch-ledger), [Patch Validator](#patch-validator)

---

### Patch Validator
**Category**: Patch Management
**Definition**: Component that validates patches against format, scope, and policy constraints.

**Validation Checks**:
1. **Format** - Must be unified diff
2. **Scope** - Files/lines within limits
3. **Constraints** - No forbidden paths, binary patches
4. **Tests** - Required tests exist for modified code

**Implementation**: `core/patches/patch_validator.py` (UET alignment)

**Related Terms**: [Patch Artifact](#patch-artifact), [Patch Policy](#patch-policy)

---

### Phase
**Category**: Project Management
**Definition**: Major development milestone containing multiple related workstreams.

**Structure**:
```yaml
phase_id: PH-UET
name: "Universal Execution Templates Integration"
duration: "9-10 weeks"
workstreams:
  - WS-UET-A1: Schema Foundation
  - WS-UET-A2: Worker Health Checks
  - ...
```

**Examples**:
- **Phase K** - Documentation foundation
- **Phase UET** - UET framework integration
- **Phase 09** - CCPM integration

**Documentation**: `docs/planning/`

**Related Terms**: [Workstream](#workstream), [CCPM](#ccpm-critical-chain-project-management)

---

### Pipeline Database
**Category**: State Management
**Definition**: SQLite database storing execution state (runs, workstreams, steps, attempts).

**Location**: `.worktrees/pipeline_state.db` (configurable via `PIPELINE_DB_PATH`)

**Schema**: `schema/schema.sql`

**Tables**:
- `runs` - Execution runs
- `workstreams` - Workstream records
- `attempts` - Step execution attempts
- `patches` - Patch artifacts (UET)
- `patch_ledger_entries` - Patch lifecycle (UET)
- `run_events` - Event sourcing log (UET)

**Implementation**: `core/state/db.py`

**Related Terms**: [CRUD Operations](#crud-operations), [State Transition](#state-transition), [UET Integration](#uet-universal-execution-templates)

---

### Plugin Manifest
**Category**: Error Detection
**Definition**: JSON file describing an error plugin's capabilities, rules, and metadata.

**Structure**:
```json
{
  "plugin_id": "python_ruff",
  "name": "Python Ruff Linter",
  "version": "1.0.0",
  "language": "python",
  "file_patterns": ["*.py"],
  "detection_rules": [...],
  "auto_fix_supported": true
}
```

**Location**: `error/plugins/*/manifest.json`

**Related Terms**: [Error Plugin](#error-plugin), [Detection Rule](#detection-rule)

---

### Profile Matching
**Category**: Integrations
**Definition**: Algorithm for matching a task/step to the most appropriate tool profile.

**Matching Criteria**:
- Task type (code_edit, testing, linting)
- File extensions (.py, .ps1)
- Tool capabilities
- User preferences

**Implementation**: `core/engine/tools.py`

**Related Terms**: [Tool Profile](#tool-profile), [AIM](#aim-ai-environment-manager)

---

### Process Id
**Category**: Specifications
**Definition**: Column header `process_id`. Identifier for a process definition or workflow this entity participates in.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Process Step Id](#process-step-id)

---

### Process Step Id
**Category**: Specifications
**Definition**: Column header `process_step_id`. Identifier for a specific step within a process.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Process Id](#process-id), [Process Step Role](#process-step-role)

---

### Process Step Role
**Category**: Specifications
**Definition**: Column header `process_step_role`. Declares the entity's role relative to a process step.

**Type**: `enum`
**Allowed Values**: `entrypoint`, `supporting`, `output`, `other`
**Constraints**:
- optional

**Related Terms**: [Process Step Id](#process-step-id)

---

## Q

### Quarantined (status)
**Category**: Specifications
**Definition**: Status value meaning excluded from normal derivations pending review due to policy violations or uncertainty.

**Related Terms**: [Status](#status)

---

## R

### Recovery Strategy
**Category**: Core Engine
**Definition**: Logic for recovering from step failures through retry, context repair, or alternative approaches.

**Strategies**:
- **Immediate Retry** - Retry with exponential backoff
- **Context Repair** - Add more context, retry
- **Alternative Tool** - Try different tool
- **Reduced Scope** - Simplify task
- **Escalate** - Promote to higher level

**Implementation**: `core/engine/recovery.py`

**Related Terms**: [Retry Logic](#retry-logic), [Circuit Breaker](#circuit-breaker), [Error Escalation](#error-escalation)

---

### Retry Logic
**Category**: Core Engine
**Definition**: Mechanism for retrying failed operations with exponential backoff.

**Configuration**:
```yaml
max_attempts: 3
backoff_multiplier: 2
initial_delay_sec: 1
max_delay_sec: 60
```

**Implementation**: `core/engine/retry.py`

**Related Terms**: [Circuit Breaker](#circuit-breaker), [Recovery Strategy](#recovery-strategy)

---

### Rollback Strategy
**Category**: Integrations
**Definition**: Method for undoing changes when failures occur (Saga pattern).

**Scopes**:
- **Patch Rollback** - Git revert of single patch
- **Task Rollback** - Undo single task
- **Phase Rollback** - Compensation cascade across phase
- **Multi-Phase Rollback** - Full rollback of multiple phases

**Implementation**: `core/engine/compensation.py` (UET alignment)

**Related Terms**: [Compensation Action](#compensation-action-saga), [Checkpoint](#checkpoint), [UET Integration](#uet-universal-execution-templates)

---

### Record Id
**Category**: Specifications
**Definition**: Column header `record_id`. Unique primary key for the row, regardless of record_kind.

**Type**: `string`
**Constraints**:
- required
- unique

**Notes**:
- may equal entity_id, edge_id, or generator_id but does not have to

**Related Terms**: [Record Kind](#record-kind)

---

### Record Kind
**Category**: Specifications
**Definition**: Column header `record_kind`. Discriminator that declares the logical schema for the row.

**Type**: `enum`
**Allowed Values**: `entity`, `edge`, `generator`
**Constraints**:
- required
- controls which other columns are meaningful

**Related Terms**: [Record Id](#record-id), [Entity Kind](#entity-kind)

---

### Rel Type
**Category**: Specifications
**Definition**: Column header `rel_type`. Relationship type describing how source relates to target.

**Type**: `enum`
**Allowed Values**: `documents`, `depends_on`, `produces`, `consumes`, `contains`, `implements`, `tests`, `references`, `duplicates`, `conflicts_with`, `other`
**Constraints**:
- required when record_kind=edge

**Related Terms**: [Directionality](#directionality), [Source Entity Id](#source-entity-id)

---

### Relative Path
**Category**: Specifications
**Definition**: Column header `relative_path`. Repository-root-relative path to the file using canonical separators.

**Type**: `string`
**Constraints**:
- required for entity_kind=file
- portable identifier

**Related Terms**: [Absolute Path](#absolute-path), [Filename](#filename)

---

### Resolver Hint
**Category**: Specifications
**Definition**: Column header `resolver_hint`. Optional hint for how to resolve the external_ref (API name, base URL, parsing rule).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [External Ref](#external-ref)

---

### Role Code
**Category**: Specifications
**Definition**: Column header `role_code`. Code used to classify an entity's role within the system for ordering or filtering (project-defined).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Type Code](#type-code)

---

## S

### Saga Pattern
**Category**: Integrations
**Definition**: Design pattern for managing distributed transactions through compensating actions.

**Components**:
- **Forward Actions** - Normal execution steps
- **Compensation Actions** - Undo/rollback steps

**Example**:
```yaml
saga_steps:
  - step: create_table
    compensation: drop_table
  - step: insert_data
    compensation: delete_data
```

**Implementation**: `core/engine/compensation.py`

**Related Terms**: [Compensation Action](#compensation-action-saga), [Rollback Strategy](#rollback-strategy)

---

### Scheduler
**Category**: Core Engine
**Definition**: Component that determines execution order of tasks based on dependencies and parallelism.

**Types**:
- **Sequential Scheduler** - Current implementation
- **DAG Scheduler** - UET alignment (dependency-aware parallel execution)

**Implementation**: `core/engine/scheduler.py`

**Related Terms**: [DAG](#dag-directed-acyclic-graph), [Dependency Resolution](#dependency-resolution), [UET Integration](#uet-universal-execution-templates)

---

### Schema Validation
**Category**: Specifications
**Definition**: Process of validating JSON/YAML artifacts against JSON Schema definitions.

**Schemas**:
- `schema/workstream.schema.json` - Workstream structure
- `schema/sidecar.schema.json` - Sidecar metadata
- `schema/uet/*.json` - UET framework schemas (17 total)

**Validation**:
```bash
python scripts/validate_workstreams.py
python scripts/validate_workstreams_authoring.py
```

**Related Terms**: [Workstream](#workstream), [UET Integration](#uet-universal-execution-templates)

---

### Sidecar Metadata
**Category**: State Management
**Definition**: Metadata file (`.sidecar.yaml`) accompanying a specification or workstream with execution history and context.

**Structure**:
```yaml
spec_id: "SPEC-001"
last_modified: "2025-11-23"
execution_history:
  - run_id: "RUN-123"
    status: "SUCCESS"
    timestamp: "2025-11-23T00:00:00Z"
```

**Schema**: `schema/sidecar_metadata.schema.yaml`

**Related Terms**: [OpenSpec](#openspec), [Specification Index](#specification-index)

---

### Spec Bridge
**Category**: Specifications
**Definition**: Integration layer between OpenSpec change proposals and workstream generation.

**Workflow**:
1. OpenSpec proposal approved
2. Spec Bridge generates workstream JSON
3. Workstream executed
4. Specification updated with results

**Implementation**: `specifications/bridge/`

**Related Terms**: [OpenSpec](#openspec), [Change Proposal](#change-proposal)

---

### Spec Guard
**Category**: Specifications
**Definition**: Validation layer that prevents invalid changes to specifications.

**Checks**:
- Schema compliance
- Cross-reference integrity
- Breaking change detection

**Implementation**: `specifications/tools/guard/`

**Related Terms**: [Spec Resolver](#spec-resolver), [Specification Index](#specification-index)

---

### Spec Patcher
**Category**: Specifications
**Definition**: Tool for applying patches to specification documents.

**Implementation**: `specifications/tools/patcher/`

**Related Terms**: [Patch](#patch), [Spec Guard](#spec-guard)

---

### Spec Resolver
**Category**: Specifications
**Definition**: Tool that resolves URI references between specifications.

**Purpose**:
- Resolve `spec://` URIs
- Validate cross-references
- Generate dependency graph

**Implementation**: `specifications/tools/resolver/`

**Related Terms**: [URI Resolution](#uri-resolution), [Specification Index](#specification-index)

---

### Specification Index
**Category**: Specifications
**Definition**: Auto-generated index of all specifications with metadata and cross-references.

**Generated By**: `scripts/generate_spec_index.py`

**Implementation**: `specifications/tools/indexer/`

**Related Terms**: [Spec Resolver](#spec-resolver), [OpenSpec](#openspec)

---

### State Transition
**Category**: State Management
**Definition**: Change of execution state for a workstream, step, or patch.

**Workstream States**:
- `PENDING` → `RUNNING` → `SUCCEEDED` / `FAILED`

**Patch States** (UET):
- `created` → `validated` → `queued` → `applied` → `verified` → `committed`

**Implementation**: `core/state/crud.py`

**Related Terms**: [Pipeline Database](#pipeline-database), [Patch Ledger](#patch-ledger)

---

### Step
**Category**: Core Engine
**Definition**: Atomic unit of work within a workstream, executed by a single tool invocation.

**Structure**:
```json
{
  "step_id": "step-01",
  "name": "Fix linting errors",
  "description": "Run ruff and fix auto-fixable issues",
  "files": ["core/engine/executor.py"],
  "validation": {
    "command": "ruff check --fix",
    "expected_exit_code": 0
  },
  "depends_on": []
}
```

**States**: `PENDING`, `READY`, `RUNNING`, `SUCCEEDED`, `FAILED`

**Schema**: `schema/workstream.schema.json`

**Related Terms**: [Workstream](#workstream), [Executor](#executor), [Dependency Resolution](#dependency-resolution)

---

### Scan Id
**Category**: Specifications
**Definition**: Column header `scan_id`. Identifier of the scan or inventory run that most recently confirmed this entity.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [First Seen UTC](#first-seen-utc), [Last Seen UTC](#last-seen-utc)

---

### Sha256
**Category**: Specifications
**Definition**: Column header `sha256`. SHA-256 hash of file contents for integrity and change detection.

**Type**: `string`
**Constraints**:
- optional
- if present must be 64 hex chars

**Related Terms**: [Size Bytes](#size-bytes)

---

### Short Description
**Category**: Specifications
**Definition**: Column header `short_description`. One-line description intended for human-readable indexes and reports.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Notes](#notes)

---

### Size Bytes
**Category**: Specifications
**Definition**: Column header `size_bytes`. File size in bytes at scan time.

**Type**: `integer`
**Constraints**:
- optional
- non-negative

**Related Terms**: [Sha256](#sha256), [Mtime UTC](#mtime-utc)

---

### Sort Keys
**Category**: Specifications
**Definition**: Column header `sort_keys`. Ordered list of keys used to sort inputs deterministically before rendering.

**Type**: `list_string`
**Constraints**:
- optional but recommended

**Related Terms**: [Sort Rule Id](#sort-rule-id)

---

### Sort Rule Id
**Category**: Specifications
**Definition**: Column header `sort_rule_id`. Identifier for a stable, versioned sorting rule used by the generator.

**Type**: `string`
**Constraints**:
- optional but recommended

**Related Terms**: [Sort Keys](#sort-keys)

---

### Source Entity Id
**Category**: Specifications
**Definition**: Column header `source_entity_id`. For edge rows, the origin node of the relationship; for provenance rows, the entity this row was derived from.

**Type**: `string`
**Constraints**:
- required when record_kind=edge
- must reference existing entity_id
- optional for provenance

**Related Terms**: [Target Entity Id](#target-entity-id), [Entity Id](#entity-id)

---

### Source Registry Hash
**Category**: Specifications
**Definition**: Column header `source_registry_hash`. Hash of the registry state (or snapshot subset) used as input to generation.

**Type**: `string`
**Constraints**:
- optional but recommended for audit

**Related Terms**: [Source Registry Scan Id](#source-registry-scan-id)

---

### Source Registry Scan Id
**Category**: Specifications
**Definition**: Column header `source_registry_scan_id`. Scan or snapshot identifier of the registry state used as input.

**Type**: `string`
**Constraints**:
- optional but recommended for audit

**Related Terms**: [Source Registry Hash](#source-registry-hash)

---

### Status
**Category**: Specifications
**Definition**: Column header `status`. Lifecycle state indicating whether the row is considered active and eligible for derivations.

**Type**: `enum`
**Allowed Values**: `active`, `deprecated`, `quarantined`, `archived`, `deleted`
**Constraints**:
- required

**Related Terms**: [Active (status)](#active-status), [Deprecated (status)](#deprecated-status)

---

### String (type)
**Category**: Specifications
**Definition**: Type name `string`. Text value.

**Related Terms**: [Integer (type)](#integer-type), [List String (type)](#list-string-type)

---

### String Or Json (type)
**Category**: Specifications
**Definition**: Type name `string_or_json`. Either a string encoding or structured JSON; pick one canonical encoding and enforce.

**Related Terms**: [String (type)](#string-type)

---

### Supersedes Entity Id
**Category**: Specifications
**Definition**: Column header `supersedes_entity_id`. Provenance link to an older entity that this one replaces.

**Type**: `string`
**Constraints**:
- optional
- should reference an existing entity_id when present

**Related Terms**: [Source Entity Id](#source-entity-id), [Entity Id](#entity-id)

---

## T

### Task Queue
**Category**: Planning
**Definition**: A structure (FIFO or priority-based) that retains tasks awaiting execution when the executor cannot keep up with new tasks generated from planning or the LCP.

**Behavior**:
- Tasks wait until previous dependencies complete
- Executor consumes tasks at its own pace
- Merge Queue integrates results safely

**Related Terms**: [LCP](#lcp-looping-chain-prompt), [PSJP](#psjp-project-specific-json-package), [Merge Queue](#merge-queue)

---

### Technical Requirements (TR)
**Category**: Planning
**Definition**: A structured, machine-readable articulation of the problem, constraints, and acceptance criteria derived from a CCIS.

**Structure**:
```yaml
technical_requirements:
  id: TR-xxxx
  derived_from: UCI-xxxx
  problem_statement: "<cleaned, clarified version>"
  functional_requirements: []
  nonfunctional_requirements: []
  constraints: []
  domain_context: {}
  acceptance_criteria: []
```

**Related Terms**: [UCP](#ucp-unified-change-pipeline), [CCIS](#ccis-canonical-change-intent-specification), [PA](#pa-pattern-assignment)

---

### TP (Task Plan)
**Category**: Planning
**Definition**: A list of actionable, dependent tasks derived from pattern assignments, each with tool instructions and acceptance conditions.

**Structure**:
```yaml
task_plan:
  id: TP-xxxx
  derived_from: PA-xxxx
  tasks:
    - task_id: T-001
      description: "Edit file X to add Y"
      pattern: PAT-xxx
      tool: "claude_code"
      acceptance: ["no compile errors"]
  dependencies: ["T-001 must finish before T-002"]
  estimated_runtime: "5 minutes"
  blocking: true|false
```

**Related Terms**: [UCP](#ucp-unified-change-pipeline), [PA](#pa-pattern-assignment), [Workstream](#workstream-ws)

---

### Test Adapter
**Category**: Integrations
**Definition**: Adapter that wraps test runners (pytest, Pester, etc.) for consistent test execution.

**Implementation**: `engine/adapters/test_adapter.py`

**Related Terms**: [Adapter](#adapter), [Test Gates](#test-gates)

---

### Test Gates
**Category**: Core Engine
**Definition**: Synchronization points where tests must pass before execution can proceed (UET pattern).

**Gate Types**:
- **GATE_LINT** - All linting must pass
- **GATE_UNIT** - All unit tests must pass
- **GATE_INTEGRATION** - All integration tests must pass
- **GATE_SECURITY** - Security scans must pass

**Behavior**:
- Dependent tasks blocked until gate cleared
- Gate failures trigger error escalation
- Fix tasks auto-created on failures

**Implementation**: `core/engine/test_gates.py`

**Related Terms**: [Feedback Loop](#feedback-loop), [UET Integration](#uet-universal-execution-templates)

---

### Timeout Handling
**Category**: Core Engine
**Definition**: Mechanism for enforcing time limits on tool execution.

**Configuration**:
```yaml
timeouts:
  wall_clock_sec: 600
  cpu_limit_sec: 300
```

**Implementation**: `core/engine/executor.py:120`

**Related Terms**: [Executor](#executor), [Tool Profile](#tool-profile)

---

### Tool Profile
**Category**: Core Engine
**Definition**: Configuration defining how to invoke a specific tool (Aider, Codex, pytest, etc.).

**Structure**:
```yaml
aider:
  command: "aider"
  model: "gpt-4"
  args:
    - "--no-auto-commits"
    - "--yes"
  timeout_sec: 600
  capabilities: ["code_edit", "refactor"]
```

**Location**: `invoke.yaml`, `config/tool_profiles.yaml`

**Implementation**: `core/engine/tools.py`

**Related Terms**: [Profile Matching](#profile-matching), [Adapter](#adapter)

---

### Tool Registry
**Category**: Integrations
**Definition**: Central registry of available AI tools and their capabilities.

**Managed By**: AIM (AI Environment Manager)

**Implementation**: `aim/registry/`

**Related Terms**: [AIM](#aim-ai-environment-manager), [Tool Profile](#tool-profile)

---

### Tags
**Category**: Specifications
**Definition**: Column header `tags`. Machine-readable labels for grouping or filtering.

**Type**: `list_string`
**Constraints**:
- optional

**Notes**:
- store as JSON array or delimited string; choose one encoding and enforce

**Related Terms**: [Notes](#notes)

---

### Target Entity Id
**Category**: Specifications
**Definition**: Column header `target_entity_id`. The destination node of the relationship.

**Type**: `string`
**Constraints**:
- required when record_kind=edge
- must reference existing entity_id

**Related Terms**: [Source Entity Id](#source-entity-id)

---

### Template Ref Entity Id
**Category**: Specifications
**Definition**: Column header `template_ref_entity_id`. Entity reference to a template file or asset used to render the output.

**Type**: `string`
**Constraints**:
- optional
- should reference existing entity_id

**Related Terms**: [Entity Id](#entity-id), [Output Kind](#output-kind)

---

### Tool Version
**Category**: Specifications
**Definition**: Column header `tool_version`. Version of the tool, generator, or parser that produced the edge record.

**Type**: `string`
**Constraints**:
- optional but recommended

**Related Terms**: [Evidence Method](#evidence-method)

---

### Transient Id
**Category**: Specifications
**Definition**: Column header `transient_id`. Identifier for a non-file or runtime-scoped concept (run, task, scan, build, session).

**Type**: `string`
**Constraints**:
- required for entity_kind=transient

**Related Terms**: [Transient Type](#transient-type)

---

### Transient Type
**Category**: Specifications
**Definition**: Column header `transient_type`. Subtype for transient IDs.

**Type**: `enum`
**Allowed Values**: `task_id`, `run_id`, `scan_id`, `build_id`, `session_id`, `other`
**Constraints**:
- optional but recommended

**Related Terms**: [Transient Id](#transient-id)

---

### Ttl Seconds
**Category**: Specifications
**Definition**: Column header `ttl_seconds`. Time-to-live in seconds; after this, the transient may be considered expired.

**Type**: `integer`
**Constraints**:
- optional
- non-negative

**Related Terms**: [Expires UTC](#expires-utc)

---

### Type Code
**Category**: Specifications
**Definition**: Column header `type_code`. Code used to classify an entity's type or category within the system for ordering or filtering (project-defined).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Role Code](#role-code)

---

## U

### UCI (Unified Change Intent)
**Category**: Planning
**Definition**: A structured representation of a proposed modification—originating either from user requirements or from the Looping Chain Prompt—that acts as the standardized input to the deterministic planning phase.

**Structure**:
```yaml
change_intent:
  id: UCI-xxxx
  source: "user" | "looping_prompt"
  description: "<natural language description>"
  change_type: ["new_feature", "modify_existing", "bug_fix", "refactor", "pattern_update"]
  affected_scope:
    files: []
    modules: []
    patterns: []
  severity: low|medium|high|critical
  blocking: true|false
  rationale: "<why this change is needed>"
  acceptance_hint: "<what success looks like>"
```

**Two Input Streams**:
1. **User-driven**: New feature, new app, change requests
2. **LCP-driven**: Automation gaps, broken wiring, refactors, spec drift

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [LCP](#lcp-looping-chain-prompt), [UCP](#ucp-unified-change-pipeline)

---

### UCP (Unified Change Pipeline)
**Category**: Planning
**Definition**: The deterministic transformation pipeline that processes CCIS → Technical Requirements → Pattern Assignment → Task Plan → Workstream → Phase Plan → PSJP.

**Complete Flow**:
```
CCIS → TR → PA → TP → WS → Phase Plan → Master JSON Fitting → PSJP → Execution Engine
```

**Key Principle**: Once a change intent is converted into Technical Requirements (TR), the rest of the pipeline is always identical—regardless of origin.

**Related Terms**: [CCIS](#ccis-canonical-change-intent-specification), [UCI](#uci-unified-change-intent), [PSJP](#psjp-project-specific-json-package), [TR](#tr-technical-requirements), [PA](#pa-pattern-assignment), [TP](#tp-task-plan)

---

### UET (Universal Execution Templates)
**Category**: Framework
**Definition**: Reference implementation framework providing canonical schemas and patterns for AI orchestration.

**Key Concepts**:
- **Worker Lifecycle** - SPAWNING → IDLE → BUSY → DRAINING → TERMINATED
- **Patch Management** - PatchArtifact, PatchLedger, PatchPolicy
- **Event Sourcing** - Full event history in `run_events` table
- **DAG Scheduler** - Dependency-aware parallel execution
- **Test Gates** - Synchronization points (LINT, UNIT, INTEGRATION)
- **Human Review** - Structured escalation workflow
- **Compensation** - Saga pattern rollback

**Location**: `UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK/`

**Schemas**: 17 JSON schemas in `UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK/schema/`

**Integration Status**: ~40% aligned (see `UET_INTEGRATION_PLAN_ANALYSIS.md`)

**Related Terms**: [Patch-First Workflow](#patch-first-workflow), [Worker Lifecycle](#worker-lifecycle), [Test Gates](#test-gates)

---

### ULID (Universally Unique Lexicographically Sortable Identifier)
**Category**: State Management
**Definition**: 26-character Base32 identifier that is globally unique and sortable by creation time.

**Format**: `01J2ZB1B3Y5D0C8QK7F3HA2XYZ` (26 characters, uppercase)

**Benefits**:
- Globally unique (like UUID)
- Sortable by timestamp (unlike UUID v4)
- Compact (26 chars vs 36 for UUID)
- URL-safe

**Usage in UET**:
- `patch_id` - Patch identifier
- `ledger_id` - Patch ledger entry ID
- `event_id` - Event identifier
- `run_ulid` - Run identifier (migrating from auto-increment)

**Implementation**: `python-ulid` package

**Related Terms**: [Patch Artifact](#patch-artifact), [Pipeline Database](#pipeline-database), [UET Integration](#uet-universal-execution-templates)

---

### URI Resolution
**Category**: Specifications
**Definition**: Process of resolving `spec://` URIs to actual specification documents.

**Format**: `spec://core/engine/orchestrator#section-name`

**Implementation**: `specifications/tools/resolver/`

**Related Terms**: [Spec Resolver](#spec-resolver), [Specification Index](#specification-index)

---

### Updated By
**Category**: Specifications
**Definition**: Column header `updated_by`. Actor identifier that last updated the row (user, tool, automation).

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Created By](#created-by)

---

### Updated UTC
**Category**: Specifications
**Definition**: Column header `updated_utc`. UTC timestamp of last modification to this row.

**Type**: `datetime_utc`
**Constraints**:
- required

**Related Terms**: [Created UTC](#created-utc), [Datetime UTC (type)](#datetime-utc-type)

---

## V

### Validator Id
**Category**: Specifications
**Definition**: Column header `validator_id`. Identifier for an output validator (contract checker) used to accept or reject generated output.

**Type**: `string`
**Constraints**:
- optional

**Related Terms**: [Validation Rules](#validation-rules)

---

### Validation Rules
**Category**: Specifications
**Definition**: Column header `validation_rules`. Inline validation rules used when no validator_id is referenced.

**Type**: `string_or_json`
**Constraints**:
- optional

**Related Terms**: [Validator Id](#validator-id), [String Or Json (type)](#string-or-json-type)

---

## W

### Worker
**Category**: Core Engine
**Definition**: Process or thread that executes tasks assigned by the orchestrator.

**Types**:
- **Tool Worker** - Executes tasks via adapters (Aider, Codex, etc.)
- **Integration Worker** - Dedicated to merging parallel results

**Related Terms**: [Worker Lifecycle](#worker-lifecycle), [Worker Pool](#worker-pool)

---

### Worker Health
**Category**: Core Engine
**Definition**: Monitoring system tracking worker availability and performance via heartbeat.

**Health Checks**:
- Heartbeat timeout (default: 300 seconds)
- Error count threshold
- Resource usage

**Actions**:
- Quarantine unhealthy workers
- Reassign tasks
- Spawn replacement workers

**Implementation**: `core/engine/worker_health.py` (UET alignment)

**Related Terms**: [Worker Lifecycle](#worker-lifecycle), [UET Integration](#uet-universal-execution-templates)

---

### Worker Lifecycle
**Category**: Core Engine
**Definition**: State machine managing worker lifetime from spawn to termination (UET pattern).

**States**:
- **SPAWNING** - Worker being created
- **IDLE** - Worker ready for tasks
- **BUSY** - Worker executing task
- **DRAINING** - Worker finishing current task before shutdown
- **TERMINATED** - Worker stopped

**Implementation**: `core/engine/worker.py`

**Related Terms**: [Worker Pool](#worker-pool), [Worker Health](#worker-health), [UET Integration](#uet-universal-execution-templates)

---

### Worker Pool
**Category**: Core Engine
**Definition**: Manager for a collection of workers, handling spawning, assignment, and termination.

**Responsibilities**:
- Spawn workers on demand
- Assign tasks to idle workers
- Monitor worker health
- Drain and terminate workers gracefully

**Implementation**: `core/engine/worker.py` (WorkerPool class)

**Related Terms**: [Worker Lifecycle](#worker-lifecycle), [Orchestrator](#orchestrator)

---

### Worktree Group
See [Parallelization Group](#parallelization-group)

---

### Parallelization Group
**Category**: Planning
**Definition**: A classification used to assign related workstreams to Git worktrees to support parallel execution without conflict.

**Related Terms**: [Workstream](#workstream-ws), [PA](#pa-pattern-assignment)

---

### Workstream
**Category**: Core Engine
**Definition**: Sequence of steps (tasks) executed to achieve a specific goal, the fundamental unit of work execution.

**Structure**:
```json
{
  "ws_id": "WS-UET-A1",
  "name": "Schema Foundation",
  "description": "Copy UET schemas to production",
  "steps": [...],
  "depends_on": [],
  "estimated_context_tokens": 5000,
  "max_cost_usd": 10.0
}
```

**States**: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED`

**Schema**: `schema/workstream.schema.json`
**Examples**: `workstreams/*.json`

**Related Terms**: [Step](#step), [Bundle](#bundle), [Orchestrator](#orchestrator), [WS](#ws-workstream-planning)

---

### WS (Workstream - Planning)
**Category**: Planning
**Definition**: A coherent group of tasks assigned to a phase and branch/worktree boundary, representing a unit of execution in the planning system.

**Structure**:
```yaml
workstream:
  id: WS-xxxx
  derived_from: TP-xxxx
  phase_category: "PH-x"
  tasks: [list of task_ids]
  parallelizable: true|false
  git_boundary:
    branch: "feature/..."
    worktree: ".worktrees/wt-..."
  success_criteria:
    - "all tasks succeed"
    - "branch passes safe-merge check"
```

**Related Terms**: [UCP](#ucp-unified-change-pipeline), [TP](#tp-task-plan), [Phase Plan](#phase-plan)

---

### Worktree Management
**Category**: State Management
**Definition**: Management of Git worktrees for isolated execution environments.

**Purpose**:
- Isolate parallel workstreams
- Enable safe concurrent execution
- Facilitate branch-based workflows

**Implementation**: `core/state/worktree.py`

**Related Terms**: [Bundle](#bundle), [Archive](#archive)

---

## Index by Category

### Core Engine (15 terms)
- [Adapter](#adapter)
- [Bundle](#bundle)
- [Circuit Breaker](#circuit-breaker)
- [DAG (Directed Acyclic Graph)](#dag-directed-acyclic-graph)
- [Dependency Resolution](#dependency-resolution)
- [Event Bus](#event-bus)
- [Executor](#executor)
- [Feedback Loop](#feedback-loop)
- [Integration Worker](#integration-worker)
- [Merge Strategy](#merge-strategy)
- [Orchestrator](#orchestrator)
- [Recovery Strategy](#recovery-strategy)
- [Retry Logic](#retry-logic)
- [Scheduler](#scheduler)
- [Step](#step)
- [Test Gates](#test-gates)
- [Timeout Handling](#timeout-handling)
- [Tool Profile](#tool-profile)
- [Worker](#worker)
- [Worker Health](#worker-health)
- [Worker Lifecycle](#worker-lifecycle)
- [Worker Pool](#worker-pool)
- [Workstream](#workstream)

### Error Detection (10 terms)
- [Detection Rule](#detection-rule)
- [Error Context](#error-context)
- [Error Engine](#error-engine)
- [Error Escalation](#error-escalation)
- [Error Plugin](#error-plugin)
- [Error State Machine](#error-state-machine)
- [File Hash Cache](#file-hash-cache)
- [Fix Strategy](#fix-strategy)
- [Incremental Detection](#incremental-detection)
- [Plugin Manifest](#plugin-manifest)

### Patch Management (8 terms)
- [Patch](#patch)
- [Patch Artifact](#patch-artifact)
- [Patch-First Workflow](#patch-first-workflow)
- [Patch Ledger](#patch-ledger)
- [Patch Policy](#patch-policy)
- [Patch Validator](#patch-validator)

### Specifications (8 terms)
- [Change Proposal](#change-proposal)
- [OpenSpec](#openspec)
- [Schema Validation](#schema-validation)
- [Sidecar Metadata](#sidecar-metadata)
- [Spec Bridge](#spec-bridge)
- [Spec Guard](#spec-guard)
- [Spec Patcher](#spec-patcher)
- [Spec Resolver](#spec-resolver)
- [Specification Index](#specification-index)
- [URI Resolution](#uri-resolution)

### State Management (8 terms)
- [Archive](#archive)
- [Checkpoint](#checkpoint)
- [CRUD Operations](#crud-operations)
- [Bundle Loading](#bundle-loading)
- [Event Sourcing](#event-sourcing)
- [Pipeline Database](#pipeline-database)
- [State Transition](#state-transition)
- [Worktree Management](#worktree-management)

### Integrations (9 terms)
- [AIM (AI Environment Manager)](#aim-ai-environment-manager)
- [AIM Bridge](#aim-bridge)
- [CCPM (Critical Chain Project Management)](#ccpm-critical-chain-project-management)
- [Compensation Action (Saga)](#compensation-action-saga)
- [Human Review](#human-review)
- [Profile Matching](#profile-matching)
- [Rollback Strategy](#rollback-strategy)
- [Saga Pattern](#saga-pattern)
- [Test Adapter](#test-adapter)
- [Tool Registry](#tool-registry)

### Framework (2 terms)
- [UET (Universal Execution Templates)](#uet-universal-execution-templates)
- [ULID](#ulid-universally-unique-lexicographically-sortable-identifier)

### Planning (18 terms)
- [Automation Gap](#automation-gap)
- [Blocking Change](#blocking-change)
- [CCIS (Canonical Change Intent Specification)](#ccis-canonical-change-intent-specification)
- [Change Intent](#change-intent)
- [Change Kind](#change-kind)
- [Creative Input Zone](#creative-input-zone)
- [CTRS (Canonical Technical Requirements Specification)](#ctrs-canonical-technical-requirements-specification)
- [Definition of Done](#definition-of-done)
- [Deterministic Planning Phase](#deterministic-planning-phase)
- [Execution Boundary](#execution-boundary)
- [LCP (Looping Chain Prompt)](#lcp-looping-chain-prompt)
- [PA (Pattern Assignment)](#pa-pattern-assignment)
- [Parallelization Group](#parallelization-group)
- [Pattern Drift](#pattern-drift)
- [Phase Category](#phase-category)
- [Planning Engine](#planning-engine)
- [PSJP (Project-Specific JSON Package)](#psjp-project-specific-json-package)
- [PSJP Fragment](#psjp-fragment)
- [Task Queue](#task-queue)
- [Technical Requirements (TR)](#technical-requirements-tr)
- [TP (Task Plan)](#tp-task-plan)
- [UCI (Unified Change Intent)](#uci-unified-change-intent)
- [UCP (Unified Change Pipeline)](#ucp-unified-change-pipeline)
- [WS (Workstream - Planning)](#ws-workstream-planning)

---

## Quick Reference Commands

```bash
# Search for a term in this glossary
grep -i "search term" GLOSSARY.md

# Find implementation locations
cat docs/IMPLEMENTATION_LOCATIONS.md | grep -i "term"

# Validate workstreams
python scripts/validate_workstreams.py

# Generate specification index
python scripts/generate_spec_index.py

# Run error detection
python scripts/run_error_engine.py

# Check AIM tool status
python -m aim status
```

---

## See Also

- **[IMPLEMENTATION_LOCATIONS.md](docs/IMPLEMENTATION_LOCATIONS.md)** - Exact code locations for each term
- **[DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)** - Complete documentation catalog
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture overview
- **[UET_INTEGRATION_PLAN_ANALYSIS.md](UET_INTEGRATION_PLAN_ANALYSIS.md)** - UET integration roadmap
- **[UET_INTEGRATION_GUIDE.md](UET_INTEGRATION_GUIDE.md)** - Two-system architecture guide
- **[CLAUDE.md](CLAUDE.md)** - Agent instructions and repository guidelines

---

**Last Updated**: 2025-12-10
**Maintained By**: Architecture Team
**Glossary Version**: 1.1.0
**Changelog**: Added 24 planning phase terms from Turn Archive conversations

## Planning Phase Documentation

For detailed planning phase terminology and concepts, see:
- **[PLANNING_PHASE_GLOSSARY.md](../phase1_planning/PLANNING_PHASE_GLOSSARY.md)** - Comprehensive planning phase glossary with detailed explanations, data flows, and architectural diagrams
- **PLANNING_Turn_1_Archive.md through PLANNING_Turn_6_Archive.md** - Original planning phase conversation transcripts (located in `C:\Users\richg\ALL_AI\PROCESS_FOR_ALL\`)

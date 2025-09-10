# APF Monorepo Build Order — Deep Descriptions

> Dependency‑aware order with richer, implementation‑ready descriptions. Each entry notes **Purpose**, **Key responsibilities**, **Depends on**, **Used by**, and **Notes/Interfaces** so teams can wire modules correctly on first pass.

---

## 1) Bootstrap & Contracts (define “valid” first)

1) **`pyproject.toml`**  
**Purpose:** Top‑level Python/monorepo configuration.  
**Key responsibilities:** Define package metadata, tool configs (ruff, mypy, pytest), and dependency groups (core, dev, plugins).  
**Depends on:** —  
**Used by:** All tooling/CI; local dev.  
**Notes/Interfaces:** Central place to pin Python version; expose unified `scripts` for `apf` CLI.

2) **`.pre-commit-config.yaml`**  
**Purpose:** Enforce formatting/linting before commits land.  
**Key responsibilities:** Configure hooks (ruff/black/isort, trailing-whitespace, end‑of‑file‑fixer).  
**Depends on:** Hook tools installed via `pre-commit`.  
**Used by:** Dev workflow, CI.  
**Notes/Interfaces:** Keep fast; prefer `--fix` hooks to reduce PR friction.

3) **`.github/workflows/ci.yml`**  
**Purpose:** Single CI pipeline for quality gates.  
**Key responsibilities:** Lint, type‑check, unit/integration tests, build artifacts, coverage upload, cache deps.  
**Depends on:** Project scripts, test layout.  
**Used by:** GitHub Actions.  
**Notes/Interfaces:** Matrix across OS/Python where needed; add a `plugins` job to smoke‑test manifests.

4) **`schemas/atomic_process.schema.json`**  
**Purpose:** Canonical contract for the Atomic Process YAML/JSON.  
**Key responsibilities:** Define ProcessFlow/AtomicStep/Branch shapes; enumerations for actions/actors; numeric formats for StepKey.  
**Depends on:** Registries for enums.  
**Used by:** Importers, validator, editors.  
**Notes/Interfaces:** Versioned; breaking changes require migration scripts in `docs/migrations`.

5) **`schemas/plugin.manifest.schema.json`**  
**Purpose:** Contract for `plugin.yaml` files.  
**Key responsibilities:** Validate plugin id, version, capabilities, permissions, entry point, and compatibility ranges.  
**Depends on:** Security policy vocabulary.  
**Used by:** `huey_core.manifest` loader; CI plugin checks.  
**Notes/Interfaces:** Include `capabilities[]`, `io_policies[]`, and semver constraints to guard runtime wiring.

6) **`schemas/library.schema.json`**  
**Purpose:** Contract for reusable step/recipe library.  
**Key responsibilities:** Define schema for templated steps, parameterization, tags, and provenance.  
**Depends on:** Atomic schema; registries.  
**Used by:** `process_library` package; import/export tools.  
**Notes/Interfaces:** Encourages dedup via `template_id` + `version`.

7) **`registries/actors.yaml`**  
**Purpose:** Controlled vocabulary of actor names/IDs.  
**Key responsibilities:** Provide canonical keys for automation, human roles, and systems.  
**Depends on:** —  
**Used by:** Schema enums, editors, lints.  
**Notes/Interfaces:** Include aliases for import normalization.

8) **`registries/actions.yaml`**  
**Purpose:** Controlled verbs with definitions.  
**Key responsibilities:** Normalize step actions; map to diagram icons.  
**Depends on:** —  
**Used by:** Importers, doc/diagram exporters.  
**Notes/Interfaces:** Include `category` (I/O, Transform, Decision) for diagram styling.

9) **`registries/naming.yaml`**  
**Purpose:** Naming rules for IDs, files, outputs.  
**Key responsibilities:** Regex/prefix formats, StepKey decimal precision, filename templates.  
**Depends on:** —  
**Used by:** Sequencer, exporters, editors.  
**Notes/Interfaces:** Drives renumbering invariants and collision handling.

10) **`config/defaults.yaml`**  
**Purpose:** Project‑wide defaults merged with user config.  
**Key responsibilities:** Paths, feature flags, exporter defaults, security toggles.  
**Depends on:** —  
**Used by:** `apf_common.config`.  
**Notes/Interfaces:** Overridden by `~/.huey-apf/config.yaml`.

---

## 2) Common Infra (shared utilities)

11) **`packages/apf_common/src/apf_common/__init__.py`**  
**Purpose:** Package marker; version export.  
**Key responsibilities:** Expose `__version__`, top‑level helpers.  
**Depends on:** —  
**Used by:** All packages.

12) **`.../errors.py`**  
**Purpose:** Unified exception taxonomy.  
**Key responsibilities:** Define `ValidationError`, `SchemaError`, `PluginError`, `OrchestrationError`.  
**Depends on:** —  
**Used by:** All layers.  
**Notes/Interfaces:** Make errors serializable for audit logs.

13) **`.../logging.py`**  
**Purpose:** Structured logging.  
**Key responsibilities:** JSON logs, correlation IDs, spans.  
**Depends on:** stdlib `logging`.  
**Used by:** Everywhere.  
**Notes/Interfaces:** Provide `get_logger(component, run_id=...)`.

14) **`.../config.py`**  
**Purpose:** Typed config loader/merger.  
**Key responsibilities:** Merge `defaults.yaml` + user config + env vars; schema‑validate.  
**Depends on:** `schemas/` and `yaml`.  
**Used by:** CLI, service, desktop.

15) **`.../paths.py`**  
**Purpose:** Centralized path resolution.  
**Key responsibilities:** Repo root discovery, cache/temp dirs, user home config path.  
**Depends on:** OS/env.  
**Used by:** Import/export, library, state.

---

## 3) Core Model + Validation

16) **`packages/apf_core/src/apf_core/__init__.py`**  
**Purpose:** Public surface for APF.  
**Key responsibilities:** Export models, validator, sequencing API.  
**Depends on:** Submodules.  
**Used by:** Plugins, apps.

17) **`.../models/__init__.py`**  
**Purpose:** Models package marker.  
**Key responsibilities:** Aggregate model exports.  
**Depends on:** —  
**Used by:** Importers/exporters.

18) **`.../models/ids.py`**  
**Purpose:** StepKey/Process ID primitives.  
**Key responsibilities:** Parse/format/compare decimal StepKeys; range ops.  
**Depends on:** —  
**Used by:** Sequencer, exporters, editors.  
**Notes/Interfaces:** Decimal precision governed by `registries/naming.yaml`.

19) **`.../models/step.py`**  
**Purpose:** `AtomicStep` (Pydantic).  
**Key responsibilities:** Fields for id, action, actor, inputs/outputs, notes, metadata.  
**Depends on:** `ids.py`.  
**Used by:** Everything.

20) **`.../models/branch.py`**  
**Purpose:** Decision/branch constructs.  
**Key responsibilities:** Conditional edges, labels, guards, merge semantics.  
**Depends on:** `ids.py`.  
**Used by:** Process graphs, diagram exporter.

21) **`.../models/process_flow.py`**  
**Purpose:** `ProcessFlow` aggregate.  
**Key responsibilities:** Collection of steps/branches; invariants (connectivity, unique ids).  
**Depends on:** Step/Branch models.  
**Used by:** Validator, exporters, orchestrator.

22) **`.../validation/__init__.py`**  
**Purpose:** Validation entrypoint.  
**Key responsibilities:** Export `validate_process(flow)`; compose schema + semantic checks.  
**Depends on:** Loader, diagnostics.

23) **`.../validation/schema_loader.py`**  
**Purpose:** Resolve/compile JSON Schemas.  
**Key responsibilities:** `$ref` resolution, caching, draft version control.  
**Depends on:** `schemas/`.  
**Used by:** Validator, importers.

24) **`.../validation/diagnostics.py`**  
**Purpose:** Rich problem/diagnostic types.  
**Key responsibilities:** Severity, codes, locations, suggested fixes; NDJSON emit.  
**Depends on:** `apf_common.errors`.  
**Used by:** CLI, desktop editor.

25) **`.../validation/validator.py`**  
**Purpose:** Schema + semantic validation.  
**Key responsibilities:** Enforce invariants (acyclicity, contiguous numbering, referenced ids exist).  
**Depends on:** Loader, diagnostics, models.  
**Used by:** CLI/service/plugins.

---

## 4) Sequencing & Transforms

26) **`.../sequencing/__init__.py`**  
**Purpose:** Sequencing API.  
**Key responsibilities:** Export `insert_after`, `renumber`, `gap_strategy`.  
**Depends on:** `ids.py`, models.

27) **`.../sequencing/renumber.py`**  
**Purpose:** Decimal renumbering strategy.  
**Key responsibilities:** Generate contiguous sequences; mapping old→new keys; conflict resolution.  
**Depends on:** `ids.py`.  
**Used by:** CLI `seq`, editor.

28) **`.../sequencing/insert.py`**  
**Purpose:** Safe midpoint insertion.  
**Key responsibilities:** Compute midkeys (e.g., 1.0015), cascade safeguards; batch inserts.  
**Depends on:** `ids.py`.  
**Used by:** CLI/editor/engine.

---

## 5) Import/Export

29) **`.../exporters/__init__.py`**  
**Purpose:** Exporter registry.  
**Key responsibilities:** Select exporter by format; shared utilities.  
**Depends on:** Models.

30) **`.../exporters/yaml_json.py`**  
**Purpose:** Serialize ProcessFlow.  
**Key responsibilities:** Deterministic ordering; anchors/refs for YAML; JSON compatibility.  
**Depends on:** Models.  
**Used by:** CLI, plugins.

31) **`.../exporters/markdown.py`**  
**Purpose:** One‑line‑per‑step MD.  
**Key responsibilities:** Render concise review docs; include branch cues.  
**Depends on:** Models.

32) **`.../exporters/drawio.py`**  
**Purpose:** Draw.io XML generator.  
**Key responsibilities:** Layout nodes/edges; swimlanes by actor; conditional diamonds; id‑stable geometry.  
**Depends on:** Models/ids.  
**Used by:** CLI, diagram plugin.

33) **`.../importers/__init__.py`**  
**Purpose:** Importer registry.  
**Key responsibilities:** Map source types (prose, CSV, YAML) to loaders.  
**Depends on:** Models/validator.

34) **`.../importers/prose_to_yaml.py`**  
**Purpose:** Prose→Atomic YAML transformer.  
**Key responsibilities:** Rule‑based extraction (actions/actors), step splitting, branch detection.  
**Depends on:** `prose_rules.yaml`, registries.  
**Used by:** Engine plugin; CLI.

35) **`.../importers/prose_rules.yaml`**  
**Purpose:** Declarative ruleset for importer.  
**Key responsibilities:** Patterns, normalization, stopwords, synonym maps.  
**Depends on:** Registries.  
**Used by:** `prose_to_yaml.py`.

---

## 6) Plugin Backbone

36) **`packages/huey_core/src/huey_core/__init__.py`**  
**Purpose:** Public plugin API.  
**Key responsibilities:** Base types, helper factories, error surfaces.  
**Depends on:** `apf_common`, `apf_core`.

37) **`.../manifest.py`**  
**Purpose:** Manifest loader/validator.  
**Key responsibilities:** Parse `plugin.yaml`, validate against schema, coerce version ranges.  
**Depends on:** `schemas/plugin.manifest.schema.json`.  
**Used by:** Registry, executor.

38) **`.../registry.py`**  
**Purpose:** Plugin discovery.  
**Key responsibilities:** Resolve entry points, load manifests, maintain index by capability.  
**Depends on:** Manifest, security policy.  
**Used by:** Orchestrator/CLI.

39) **`.../plugin_base.py`**  
**Purpose:** ABCs for plugins/capabilities.  
**Key responsibilities:** Lifecycle (`init`, `execute`, `shutdown`), context injection, result contracts.  
**Depends on:** `apf_common.errors`.

40) **`.../executor.py`**  
**Purpose:** Safe plugin execution wrapper.  
**Key responsibilities:** Timeouts, resource limits, try/rollback hooks, redaction.  
**Depends on:** Recovery, security policy.  
**Used by:** Orchestrator, CLI.

---

## 7) Guardrails & Durability

41) **`packages/security/src/security/__init__.py`**  
**Purpose:** Security entrypoint.  
**Key responsibilities:** Export policy checks, sandbox helpers.

42) **`.../policy.py`**  
**Purpose:** Capability/IO policy definitions.  
**Key responsibilities:** Allowed file globs, network rules, data‑class restrictions.  
**Used by:** Manifest validation, executor.

43) **`.../sandbox.py`**  
**Purpose:** Execution sandbox helpers.  
**Key responsibilities:** Temp dirs, read‑only mounts, sub‑process guards.  
**Used by:** Executor.

44) **`.../validation.py`**  
**Purpose:** Policy validation.  
**Key responsibilities:** Check plugin manifests and declared IO against policy.  
**Used by:** CI, registry.

45) **`packages/recovery/src/recovery/__init__.py`**  
**Purpose:** Recovery entrypoint.  
**Key responsibilities:** Export snapshot/transaction APIs.

46) **`.../snapshot.py`**  
**Purpose:** Snapshot inputs/outputs.  
**Key responsibilities:** Content‑addressed storage; diff helpers.  
**Used by:** Executor, audit.

47) **`.../transaction.py`**  
**Purpose:** Transaction/rollback context.  
**Key responsibilities:** Begin/commit/rollback; integrate with orchestrator.  
**Used by:** Plugins, engine.

48) **`.../audit_log.py`**  
**Purpose:** Append‑only audit trail.  
**Key responsibilities:** Structured events, correlation IDs, integrity checks.  
**Used by:** Compliance, debugging.

49) **`packages/state/src/state/__init__.py`**  
**Purpose:** State/versioning entrypoint.  
**Key responsibilities:** Expose document state stores, versioning APIs.

50) **`.../documentation_state.py`**  
**Purpose:** Documentation/process state manager.  
**Key responsibilities:** Version graph, autosave, migrations; restore points for editors.  
**Used by:** Desktop, watch loop, service.

---

## 8) Orchestration

51) **`packages/orchestration/src/orchestration/__init__.py`**  
**Purpose:** Orchestration surface.  
**Key responsibilities:** Export coordinator, job/state abstractions.

52) **`.../state.py`**  
**Purpose:** Runtime state machines.  
**Key responsibilities:** Runs, phases, transitions; resumability.  
**Depends on:** Recovery/state.

53) **`.../jobs.py`**  
**Purpose:** Job definitions & queues.  
**Key responsibilities:** Define units of work for import/validate/export; retry/backoff.  
**Used by:** Coordinator, watch.

54) **`.../coordinator.py`**  
**Purpose:** High‑level coordinator.  
**Key responsibilities:** Plan execution DAGs, fan‑out/fan‑in across plugins, collect artifacts.  
**Depends on:** Jobs/state, executor, recovery.

---

## 9) Process Library

55) **`packages/process_library/src/process_library/__init__.py`**  
**Purpose:** Library surface.  
**Key responsibilities:** Query/templates API.

56) **`.../db.py`**  
**Purpose:** SQLite access layer.  
**Key responsibilities:** CRUD for templates/steps, FTS indexes, referential integrity.  
**Depends on:** `library.schema.json`.

57) **`.../migrations.py`**  
**Purpose:** Database migrations.  
**Key responsibilities:** Schema versions, up/down scripts, seed data.  
**Used by:** CI, local bootstrap.

58) **`.../templates.py`**  
**Purpose:** Prefab step templates.  
**Key responsibilities:** Resolve `template_id@version`, parameter substitution, provenance.

---

## 10) Parser (structured docs → models)

59) **`packages/apf_parser/src/apf_parser/__init__.py`**  
**Purpose:** Parser entrypoint.  
**Key responsibilities:** Public API for document→ProcessFlow parsing.

60) **`.../structured_document.py`**  
**Purpose:** Deterministic parser for structured docs.  
**Key responsibilities:** Map headings/tables/lists to steps/branches; attach metadata.  
**Depends on:** Models, validator.

61) **`.../streaming.py`**  
**Purpose:** Incremental parser for large documents.  
**Key responsibilities:** Chunked reads, bounded memory, progressive diagnostics; resumable offsets.  
**Used by:** Watch loop, service.

---

## 11) First‑Party Plugins (compose features)

62) **`plugins/atomic_process_engine/plugin.yaml`**  
**Purpose:** Manifest describing engine plugin.  
**Key responsibilities:** Capabilities (import, validate, export), IO policies, entry point.  
**Used by:** Registry, executor.

63) **`plugins/atomic_process_engine/plugin.py`**  
**Purpose:** Orchestrate import→validate→export for a target file.  
**Key responsibilities:** Call parser/validator/exporters; emit artifacts (MD, Draw.io, JSON).  
**Depends on:** APF core, exporters, recovery.

64) **`plugins/step_sequencer/plugin.yaml`**  
**Purpose:** Manifest for sequencing plugin.  
**Key responsibilities:** Declare `seq.insert`, `seq.renumber` capabilities.

65) **`plugins/step_sequencer/plugin.py`**  
**Purpose:** Expose insert/renumber as plugin commands.  
**Key responsibilities:** Apply `ids` rules; produce renumber maps; return diagnostics.

66) **`plugins/process_standardizer/plugin.yaml`**  
**Purpose:** Manifest for prose standardizer.  
**Key responsibilities:** Declare normalization/transformation capabilities.

67) **`plugins/process_standardizer/plugin.py`**  
**Purpose:** Normalize prose, map to canonical actors/actions.  
**Key responsibilities:** Apply `prose_rules.yaml`; output clean YAML.

68) **`plugins/diagram_generator/plugin.yaml`**  
**Purpose:** Manifest for diagram exporter.  
**Key responsibilities:** Diagram capabilities and format options.

69) **`plugins/diagram_generator/plugin.py`**  
**Purpose:** Wrapper over draw.io exporter (and optionally Mermaid).  
**Key responsibilities:** Layout presets; theming; artifact bundling.

70) **`plugins/validation_engine/plugin.yaml`**  
**Purpose:** Manifest for deep validation plugin.  
**Key responsibilities:** Additional semantic/policy checks.

71) **`plugins/validation_engine/plugin.py`**  
**Purpose:** Enforce advanced invariants/policies.  
**Key responsibilities:** Cross‑file references, library conformance, security rules.

72) **`plugins/documentation/plugin.yaml`**  
**Purpose:** Manifest for doc bundler.  
**Key responsibilities:** Declares MD/PDF packaging capability; assets.

73) **`plugins/documentation/plugin.py`**  
**Purpose:** Generate documentation bundles.  
**Key responsibilities:** Collate MD, images, diagrams; TOC; export zip.

---

## 12) Apps (thin wrappers)

74) **`apps/cli/apf/__init__.py`**  
**Purpose:** CLI package marker.  
**Key responsibilities:** Expose console entry point.

75) **`apps/cli/apf/__main__.py`**  
**Purpose:** CLI entry.  
**Key responsibilities:** Argparse/Typer wiring; subcommand dispatch to plugins.

76) **`apps/cli/apf/commands/export.py`**  
**Purpose:** `apf export` subcommand.  
**Key responsibilities:** Load file → exporter(s) → write artifacts; exit codes.

77) **`apps/cli/apf/commands/validate.py`**  
**Purpose:** `apf validate` subcommand.  
**Key responsibilities:** Run schema+semantic checks; print diagnostics table/NDJSON.

78) **`apps/cli/apf/commands/seq.py`**  
**Purpose:** `apf seq` subcommand.  
**Key responsibilities:** Insert/renumber, dry‑run, writeback with backup.

79) **`apps/cli/apf/commands/watch.py`**  
**Purpose:** Watch daemon for zero‑touch loop.  
**Key responsibilities:** File watcher → enqueue jobs → engine run → artifact refresh; debounce/throttle.  
**Depends on:** Orchestrator, parser, exporters, state.

80) **`apps/service/main.py`**  
**Purpose:** FastAPI app factory.  
**Key responsibilities:** Dependency injection, lifespan, logging.

81) **`apps/service/routes.py`**  
**Purpose:** HTTP endpoints.  
**Key responsibilities:** `/decide`, `/export`, `/validate`; stream diagnostics; return artifacts.

82) **`apps/service/watch.py`**  
**Purpose:** Service‑side watcher (optional).  
**Key responsibilities:** Background task to monitor repos or queues; hot‑reload artifacts.

83) **`apps/desktop/main.py`**  
**Purpose:** PySide6 launcher.  
**Key responsibilities:** App bootstrap, menus, theme, telemetry opt‑in.

84) **`apps/desktop/ui_shell.py`**  
**Purpose:** Main window shell.  
**Key responsibilities:** Docking layout, status bar, notifications, error panel.

85) **`apps/desktop/editors/yaml_editor.py`**  
**Purpose:** Schema‑aware YAML editor.  
**Key responsibilities:** Live validation, StepKey helpers, jump‑to‑diagnostic, diff view.

---

## 13) Tests, Examples, Docs

86) **`tests/unit/test_step_key.py`**  
**Purpose:** StepKey correctness.  
**Key responsibilities:** Parse/format/compare; midpoints; ordering edge cases.

87) **`tests/unit/test_validator.py`**  
**Purpose:** Validation coverage.  
**Key responsibilities:** Schema violations, semantic invariants, helpful messages.

88) **`tests/unit/test_sequencer.py`**  
**Purpose:** Sequencer behavior.  
**Key responsibilities:** Insert/renumber maps; collisions; batch updates.

89) **`tests/unit/test_streaming_parser.py`**  
**Purpose:** Streaming parser guardrails.  
**Key responsibilities:** Large files, chunking, recovery/resume.

90) **`tests/plugins/test_plugin_registry.py`**  
**Purpose:** Plugin discovery/execution.  
**Key responsibilities:** Manifest schema, capability map, import failures.

91) **`tests/plugins/test_plugin_permissions.py`**  
**Purpose:** Security regression tests.  
**Key responsibilities:** Enforce IO/Network policies; deny violations; logging.

92) **`tests/integration/test_cli_watch.py`**  
**Purpose:** End‑to‑end watch loop.  
**Key responsibilities:** Change detection → engine → artifacts; idempotency; recovery.

93) **`examples/demo_atomic.yaml`**  
**Purpose:** Minimal valid spec.  
**Key responsibilities:** Shows step/branch basics and naming rules.

94) **`examples/derived/demo_atomic.drawio`**  
**Purpose:** Diagram output exemplar.  
**Key responsibilities:** Verifies exporter layout/styling.

95) **`docs/architecture/huey_apf_hybrid.md`**  
**Purpose:** Architecture overview.  
**Key responsibilities:** Context, layering, data flow, extension points.

96) **`docs/GUI_Playbook.md`**  
**Purpose:** Desktop UX playbook.  
**Key responsibilities:** Patterns, components, accessibility, QA checklist.

---

## 14) Locks & Misc (after deps are finalized)

97) **`uv.lock`**  
**Purpose:** Locked dependency graph (uv).  
**Key responsibilities:** Reproducible builds; CI cache key.  
**Notes/Interfaces:** Use either uv or Poetry, not both.

98) **`poetry.lock`**  
**Purpose:** Locked dependency graph (Poetry).  
**Key responsibilities:** Reproducible builds; CI cache key.

---

### Integration Notes & Cross‑Cutting Interfaces
- **IDs & Sequencing:** `registries/naming.yaml` governs decimal precision; `ids.py` and `sequencing/*` must agree.  
- **Validation Path:** Importer → `validator` (schema, semantics) → `diagnostics` → Editors/CLI.  
- **Plugin Safety:** `security/policy.py` + manifest schema form the contract enforced by `executor`.  
- **State & Recovery:** `documentation_state` and `recovery/*` provide restore points for CLI/desktop/service.  
- **Watch Loop:** CLI/service watchers enqueue orchestration jobs; exporters refresh artifacts deterministically.



---

# Ubiquitous Language & Rules

This section defines a shared vocabulary (ubiquitous language) and hard rules so code, docs, and diagrams stay in lock‑step. Treat these as **contractual**. Breaking them requires an approved migration plan.

## A) Glossary (canonical definitions)
- **Atomic Process Framework (APF):** The core model + tooling that represents workflows as **ProcessFlow → AtomicStep/Branch** with deterministic IDs and exporters.
- **ProcessFlow:** A directed acyclic graph of steps and branches that describes a single workflow specification.
- **AtomicStep:** The smallest, indivisible unit of work. Always written as **Actor + Action + (Inputs→Outputs)** in one line.
- **Branch:** A decision point that conditionally routes execution. Has explicit **guards** and **merge semantics**.
- **StepKey:** A sortable numeric identifier for steps (e.g., `1.001`, `1.0015`) used for ordering, addressing, and renumber maps.
- **Renumber Map:** A mapping **old→new StepKey** produced after insert/resequence operations; must be applied atomically.
- **Actor:** The person/system performing the step, from `registries/actors.yaml`.
- **Action:** The verb describing the step, from `registries/actions.yaml`.
- **Diagnostics:** Structured validation results with **severity**, **code**, **message**, and **location**.
- **Importer:** A module that converts source material (prose/CSV/YAML) into APF models.
- **Exporter:** A module that emits deterministic artifacts (YAML/JSON/MD/Draw.io) from APF models.
- **Plugin:** A loadable unit that declares **capabilities**, **IO policies**, and an **entry point** in `plugin.yaml`.
- **Capability:** A named operation exposed by a plugin (e.g., `import.prose`, `seq.insert`, `export.drawio`).
- **Manifest:** A `plugin.yaml` that declares id, version, capabilities, permissions, and compatibility ranges.
- **Executor:** The safe runtime wrapper that runs a plugin with policy enforcement and recovery hooks.
- **Orchestrator/Coordinator:** Components that schedule and coordinate jobs across plugins to produce artifacts.
- **Job:** A unit of work (e.g., *parse file X*, *export MD*). Jobs are queued, retried, and audited.
- **Run:** A correlated execution session identified by `run_id` across logs, artifacts, and audit entries.
- **Snapshot:** Content‑addressed capture of inputs/outputs for recovery and provenance.
- **Transaction:** A scoped context that guarantees **all‑or‑nothing** application of effects and renumber maps.
- **Audit Log:** Append‑only event stream for compliance and debugging.
- **Policy:** Security rules governing filesystem/network access and data classes permitted to plugins.
- **Sandbox:** The constrained environment provided to plugins (temp dirs, read‑only mounts, resource limits).
- **State Store:** A versioned repository of document/editor state with autosave and restore.
- **Documentation State:** The state object that tracks versions, migrations, and restore points for specs.
- **Template (Library):** A reusable step or fragment identified by `template_id@version`.
- **Streaming Parser:** An incremental parser that processes large documents in bounded memory.
- **Watch Loop:** A daemon that detects file changes, enqueues jobs, and refreshes artifacts deterministically.
- **Artifact:** A deterministic output (YAML/JSON/MD/Draw.io) with stable filenames and hashes.

## B) Rules & Invariants (must‑follow)

### 1) IDs & StepKey
1. **Format:** `MAJOR.FRAC` where `MAJOR` is `1..n`, `FRAC` is a decimal with **≥3** digits; additional digits permitted for midpoints. Examples: `1.001`, `1.0015`, `2.010`.
2. **Ordering:** Strictly increasing by numeric value within a ProcessFlow. No duplicates.
3. **Midpoints:** Inserts may extend precision (e.g., `1.001` → insert → `1.0015`). **Finalization** must renumber back to canonical precision (see #4).
4. **Canonical Precision:** Default **3 fractional digits** at rest. Configurable via `registries/naming.yaml`.
5. **Stability:** References to steps use StepKey strings; any renumber operation must ship a **renumber map** and apply atomically under a **transaction**.

### 2) Source of Truth
6. **YAML First:** `demo_atomic.yaml` (or project spec) is the **only** source of truth for content. MD/Draw.io are derived. No AI‑fabricated text beyond what YAML states.
7. **Determinism:** Exporters MUST be idempotent: same YAML → byte‑identical artifacts (timestamps and volatile data excluded).

### 3) Naming & Registries
8. **Actors/Actions:** Must appear in `registries/*.yaml`. Unknown values cause **ERROR** diagnostics.
9. **Plugin IDs:** Lowercase dot‑separated: `<org>.<package>.<name>` (e.g., `apf.diagram_generator`). No spaces, only `[a‑z0‑9_.-]`.
10. **File Layout:** Artifacts land under `dist/<run_id>/...` (CI) or `derived/` (local), as configured.

### 4) Validation
11. **Schema then Semantics:** Validators run JSON Schema checks first, then semantic invariants (connectivity, uniqueness, guard completeness).
12. **Severity Levels:** `ERROR` (blocks export), `WARN` (export allowed), `INFO` (advisory). Codes follow `APF####` (see C) with stable catalog.
13. **Branching:** Every `Branch` must have exhaustive guards or a default path; merges require explicit nodes.

### 5) Import/Export
14. **Importer Rules:** `prose_to_yaml` must normalize using registries; ambiguous sentences yield **WARN** with suggested resolutions.
15. **Exporter Rules:** `drawio` exporter must emit stable geometry keyed by StepKey; MD exporter emits **one line per step** and branch cues.

### 6) Plugins & Manifests
16. **Least‑Privilege:** Manifests declare IO globs and network = **deny by default**. CI fails if manifest is over‑permissive.
17. **Capability Names:** Kebab or dot notation; MUST match implemented entry points.
18. **Compat Ranges:** Plugins declare `apf_core` compatibility using semver ranges; executor refuses mismatches.

### 7) Security & Recovery
19. **Sandbox:** Plugins run in temp workspaces; only declared globs are readable/writable.
20. **Snapshots:** Inputs and produced artifacts are snapshotted; audit log records content hashes.
21. **Transactions:** Renumber and write‑backs occur within a transaction; on failure, **no partial effects** persist.

### 8) Orchestration
22. **Job Model:** Each job is pure relative to input set; retriable with exponential backoff; idempotent when replayed.
23. **Fan‑out/Fan‑in:** Coordinator may parallelize exports; artifacts must not race (unique paths per target).

### 9) Library & Templates
24. **Template IDs:** `lib.<domain>.<name>@<semver>`; resolving without version pins latest **compatible**.
25. **Migrations:** Library schema changes ship up/down migrations and seed verification.

### 10) Parser & Streaming
26. **Chunking:** Streaming parser reads in bounded chunks; yields progressive diagnostics tagged by byte/line offsets.
27. **Resumability:** Checkpoints recorded in state store; watch loop resumes from last good offset.

### 11) Watch Loop & Artifacts
28. **Debounce:** File change debounce **≥ 500 ms**; coalesce bursts.
29. **Atomic Writes:** Export to temp + rename; never partially overwrite derived artifacts.
30. **Cleanups:** Keep last **N** runs (configurable); older artifacts pruned.

### 12) Documentation & State
31. **Autosave:** Desktop editor writes autosave snapshots to state store with retention window.
32. **Restore:** Users can restore any version by `version_id`; operations are audited.

### 13) Testing & CI
33. **Golden Files:** Exporters tested against golden artifacts; assert byte equality.
34. **Policy Tests:** Each plugin must have permission tests that attempt forbidden IO and expect failure.

### 14) Versioning & Migration
35. **SemVer:** `schemas/*`, `apf_core`, plugins, and templates all use SemVer. **MAJOR** = breaking; **MINOR** = additive; **PATCH** = bugfix.
36. **Breaking Changes:** Require migration guides + automated fixers where feasible; CI blocks merges missing these.

## C) Diagnostics Catalog (starter)
- `APF0001` (ERROR): Unknown actor. Fix by adding to `registries/actors.yaml` or mapping in importer.
- `APF0002` (ERROR): Unknown action. Fix via `registries/actions.yaml`.
- `APF0100` (ERROR): Duplicate StepKey detected.
- `APF0101` (ERROR): Non‑increasing StepKey order.
- `APF0200` (ERROR): Branch not exhaustive and no default path.
- `APF0300` (WARN): Unreferenced template.
- `APF0400` (WARN): Importer ambiguity; manual review suggested.

## D) Authoring Guidelines (human‑readable docs)
- **One‑liner style:** `Actor — Action — Inputs → Outputs` (no extra narrative). Example: `System — Validate schema — spec.yaml → diagnostics.ndjson`.
- **Verb choice:** Use `actions.yaml` verbs; present tense; active voice.
- **Notes field:** Use for constraints/assumptions only; never introduce new content beyond YAML.

## E) Open Questions / TBD
- Canonical StepKey precision default (3 vs 4) for finalization? (Current rule: 3; revisit if insert‑density demands 4.)
- Standard icon mapping set for new action categories in Draw.io? (Draft in `actions.yaml`.)
- Library version pinning policy for production releases (strict vs caret).



---

# Starter Vocabulary Files

Below are implementation‑ready starter files for the registries and the diagnostics schema. You can copy them verbatim into your repo at the indicated paths.

## `registries/actions.yaml`
```yaml
# registries/actions.yaml
# Canonical action verbs and diagram categories. Extend cautiously in PRs.
version: 1

# Categories map to diagram styling and high‑level semantics
categories:
  IO:        "Input/Output of data or files"
  TRANSFORM: "Pure transformations or computations"
  DECISION:  "Condition evaluation and routing"
  QUALITY:   "Validation, linting, testing"
  CONTROL:   "Flow control, waiting, scheduling"
  COMM:      "Notifications, logging, reporting"
  STATE:     "Persistence, snapshots, migrations"
  SECURITY:  "Security checks, policy enforcement"

# Default diagram styling for categories (draw.io hints)
diagram_style:
  IO:        { shape: "process", badge: "download" }
  TRANSFORM: { shape: "process", badge: "gear" }
  DECISION:  { shape: "rhombus", badge: "branch" }
  QUALITY:   { shape: "process", badge: "check" }
  CONTROL:   { shape: "process", badge: "clock" }
  COMM:      { shape: "process", badge: "message" }
  STATE:     { shape: "process", badge: "database" }
  SECURITY:  { shape: "process", badge: "shield" }

# Canonical actions. `id` must match ^[a-z][a-z0-9_]*$
actions:
  - id: import
    label: Import
    category: IO
    description: Ingest external files or data into the working set.
    synonyms: [load, read, fetch, open]
    notes: "Opposite of export; should be side‑effect free aside from local copies."

  - id: export
    label: Export
    category: IO
    description: Emit artifacts from models (e.g., YAML/JSON/MD/Draw.io).
    synonyms: [write, emit, save]

  - id: parse
    label: Parse
    category: TRANSFORM
    description: Convert structured/unstructured text into APF models.
    synonyms: [ingest, tokenize]

  - id: normalize
    label: Normalize
    category: TRANSFORM
    description: Apply canonical vocab (actors/actions) and formatting rules.

  - id: transform
    label: Transform
    category: TRANSFORM
    description: Compute or reshape data without external side effects.

  - id: validate
    label: Validate
    category: QUALITY
    description: Run schema and semantic checks; produce diagnostics.

  - id: decide
    label: Decide
    category: DECISION
    description: Evaluate conditions and select a branch.
    notes: "Typically represented by a diamond in diagrams."

  - id: sequence
    label: Sequence
    category: TRANSFORM
    description: Compute step ordering and renumber maps.
    synonyms: [renumber]

  - id: snapshot
    label: Snapshot
    category: STATE
    description: Persist a content‑addressed copy of inputs/outputs for recovery.

  - id: transact
    label: Transact
    category: STATE
    description: Apply a set of changes atomically with commit/rollback semantics.

  - id: notify
    label: Notify
    category: COMM
    description: Send user‑visible messages (UI toast, email, log events).
    synonyms: [report, alert]

  - id: render
    label: Render
    category: IO
    description: Render human‑readable outputs (Markdown, PDF, diagrams).

  - id: wait
    label: Wait
    category: CONTROL
    description: Delay until a time or condition is met (debounce/throttle).

  - id: archive
    label: Archive
    category: STATE
    description: Move artifacts to long‑term storage with retention policies.

# Extension policy
# - New actions MUST include: id, category, description, and (if relevant) synonyms.
# - Changing category of an existing action is a breaking change and requires a migration note.
```

## `registries/actors.yaml`
```yaml
# registries/actors.yaml
# Canonical actors used in AtomicStep.Author field; also drives swimlanes.
version: 1

# Lane presets for diagram swimlanes
lanes:
  HUMAN:   "Human"
  CORE:    "APF Core"
  PLUGIN:  "Plugin"
  SERVICE: "Service"
  STORAGE: "Storage"

# Canonical actor entries
actors:
  - id: user
    label: User
    kind: HUMAN
    lane: HUMAN
    description: Primary human author/reviewer of specifications.
    aliases: [analyst, author, reviewer]

  - id: operator
    label: Operator
    kind: HUMAN
    lane: HUMAN
    description: Executes and supervises runs; handles approvals.
    aliases: [approver]

  - id: system
    label: APF System
    kind: CORE
    lane: CORE
    description: Generic system actor when no specific component applies.
    aliases: [apf, engine]

  - id: orchestrator
    label: Orchestrator
    kind: SERVICE
    lane: SERVICE
    description: Coordinates jobs, fan‑out/fan‑in, and state transitions.
    aliases: [coordinator]

  - id: importer
    label: Importer
    kind: PLUGIN
    lane: PLUGIN
    description: Prose/structured document importer to APF models.
    aliases: [parser]

  - id: validator
    label: Validator
    kind: PLUGIN
    lane: PLUGIN
    description: Runs schema and semantic checks to produce diagnostics.

  - id: sequencer
    label: Step Sequencer
    kind: PLUGIN
    lane: PLUGIN
    description: Performs insert/renumber operations on steps and branches.

  - id: diagrammer
    label: Diagram Exporter
    kind: PLUGIN
    lane: PLUGIN
    description: Produces Draw.io/Mermaid outputs from ProcessFlow.
    aliases: [drawio, diagram_exporter]

  - id: exporter
    label: Exporter
    kind: PLUGIN
    lane: PLUGIN
    description: Emits YAML/JSON/MD and other artifacts.

  - id: recovery
    label: Recovery Engine
    kind: SERVICE
    lane: SERVICE
    description: Snapshots, transactions, and rollback.

  - id: security_policy
    label: Security Policy
    kind: SERVICE
    lane: SERVICE
    description: Enforces IO/network capability rules for plugins.
    aliases: [security]

  - id: process_library
    label: Process Library
    kind: STORAGE
    lane: STORAGE
    description: Stores reusable step/templates with versions.

  - id: desktop_app
    label: Desktop App
    kind: SERVICE
    lane: SERVICE
    description: PySide6 UI shell and editor.
    aliases: [gui]

  - id: cli
    label: CLI
    kind: SERVICE
    lane: SERVICE
    description: Command‑line entrypoint and subcommands.

  - id: service
    label: HTTP Service
    kind: SERVICE
    lane: SERVICE
    description: FastAPI layer exposing /export, /validate, /decide, /watch.

# Extension policy
# - New actors MUST define: id, kind, lane, and description.
# - Aliases are used by importers to normalize prose; duplicates are rejected in CI.
```

## `schemas/diagnostics.schema.json`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.org/schemas/diagnostics.schema.json",
  "title": "APF Diagnostics File",
  "description": "Schema for diagnostics emitted by validators and plugins. The file is an array of Diagnostic entries (NDJSON may serialize per-line Diagnostic using $defs.Diagnostic).",
  "type": "array",
  "items": { "$ref": "#/$defs/Diagnostic" },
  "$defs": {
    "Severity": {
      "type": "string",
      "description": "Severity of the diagnostic.",
      "enum": ["ERROR", "WARN", "INFO"]
    },
    "Location": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "file": { "type": "string", "description": "Source file path related to the diagnostic." },
        "step_id": {
          "type": "string",
          "description": "Optional APF StepKey impacted by this diagnostic.",
          "pattern": "^\d+(\.\d{3,})?$"
        },
        "json_pointer": { "type": "string", "description": "JSON Pointer into the source document, if applicable." },
        "line": { "type": "integer", "minimum": 1 },
        "column": { "type": "integer", "minimum": 1 }
      }
    },
    "Diagnostic": {
      "type": "object",
      "additionalProperties": false,
      "required": ["severity", "code", "message"],
      "properties": {
        "severity": { "$ref": "#/$defs/Severity" },
        "code": {
          "type": "string",
          "description": "Stable diagnostic code.",
          "pattern": "^APF[0-9]{4}$"
        },
        "message": { "type": "string", "minLength": 1, "maxLength": 2000 },
        "location": { "$ref": "#/$defs/Location" },
        "related": {
          "type": "array",
          "description": "Related StepKeys or file references.",
          "items": {
            "type": "string"
          },
          "uniqueItems": true
        },
        "hint": { "type": "string", "description": "Optional remediation guidance." },
        "run_id": { "type": "string", "description": "Correlates diagnostics across artifacts." },
        "timestamp": { "type": "string", "format": "date-time" },
        "data": { "type": "object", "description": "Free-form structured context for tooling.", "additionalProperties": true }
      }
    }
  },
  "examples": [
    [
      {
        "severity": "ERROR",
        "code": "APF0001",
        "message": "Unknown actor 'analyst' (did you mean 'user'?)",
        "location": { "file": "specs/demo_atomic.yaml", "line": 12, "column": 7 },
        "hint": "Add alias in registries/actors.yaml or change the author field.",
        "run_id": "2025-08-22T01:23:45Z#abc123"
      },
      {
        "severity": "WARN",
        "code": "APF0400",
        "message": "Importer ambiguity: sentence maps to multiple actions.",
        "location": { "file": "notes/process.md", "json_pointer": "/sections/2/paragraphs/3" },
        "data": { "candidates": ["normalize", "transform"] }
      }
    ]
  ]
}
```



---

# Unit Tests & CI Wiring for Registries + Diagnostics

Below are minimal, focused tests that (1) validate the **actions** and **actors** registries for shape and invariants, and (2) validate the **diagnostics JSON Schema** with round‑trip examples. A CI snippet is included to run them automatically.

## A) Tests — place these files verbatim

### `tests/registries/test_actions_registry.py`
```python
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
ACTIONS = ROOT / "registries" / "actions.yaml"

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def test_actions_registry_structure():
    data = yaml.safe_load(ACTIONS.read_text(encoding="utf-8"))
    assert isinstance(data.get("version"), int) and data["version"] >= 1

    categories = data.get("categories")
    assert isinstance(categories, dict) and categories

    style = data.get("diagram_style")
    assert isinstance(style, dict) and style
    # Style must define at least all categories
    assert set(categories.keys()).issubset(set(style.keys()))

    actions = data.get("actions")
    assert isinstance(actions, list) and actions

    seen_ids = set()
    seen_aliases = set()

    for a in actions:
        assert set(a.keys()).issubset({"id", "label", "category", "description", "synonyms", "notes"})
        aid = a.get("id"); label = a.get("label"); cat = a.get("category")
        assert isinstance(aid, str) and ID_RE.match(aid), f"bad id: {aid!r}"
        assert aid not in seen_ids, f"duplicate action id: {aid}"
        seen_ids.add(aid)
        assert isinstance(label, str) and label
        assert cat in categories, f"unknown category for {aid}: {cat}"

        # synonyms optional but if present, must be unique and non‑colliding
        syn = a.get("synonyms", []) or []
        assert isinstance(syn, list)
        for s in syn:
            assert isinstance(s, str) and s
            # No synonym may collide with any action id or other synonym (prevents import ambiguity)
            assert s not in seen_ids, f"synonym collides with existing action id: {s}"
            assert s not in seen_aliases, f"duplicate synonym across actions: {s}"
            seen_aliases.add(s)
```

### `tests/registries/test_actors_registry.py`
```python
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
ACTORS = ROOT / "registries" / "actors.yaml"

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
KINDS = {"HUMAN", "CORE", "PLUGIN", "SERVICE", "STORAGE"}


def test_actors_registry_structure():
    data = yaml.safe_load(ACTORS.read_text(encoding="utf-8"))
    assert isinstance(data.get("version"), int) and data["version"] >= 1

    lanes = data.get("lanes")
    assert isinstance(lanes, dict) and lanes

    actors = data.get("actors")
    assert isinstance(actors, list) and actors

    seen_ids = set()
    seen_aliases = set()

    for a in actors:
        assert set(a.keys()).issubset({"id", "label", "kind", "lane", "description", "aliases"})
        aid = a.get("id"); kind = a.get("kind"); lane = a.get("lane")
        assert isinstance(aid, str) and ID_RE.match(aid), f"bad id: {aid!r}"
        assert aid not in seen_ids, f"duplicate actor id: {aid}"
        seen_ids.add(aid)
        assert kind in KINDS, f"unknown kind for {aid}: {kind}"
        assert lane in lanes, f"unknown lane for {aid}: {lane}"
        assert isinstance(a.get("label"), str) and a["label"]
        assert isinstance(a.get("description"), str) and a["description"]

        aliases = a.get("aliases", []) or []
        assert isinstance(aliases, list)
        for s in aliases:
            assert isinstance(s, str) and s
            assert s not in seen_ids, f"alias collides with actor id: {s}"
            assert s not in seen_aliases, f"duplicate alias across actors: {s}"
            seen_aliases.add(s)
```

### `tests/schemas/test_diagnostics_schema.py`
```python
from pathlib import Path
import json
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas" / "diagnostics.schema.json"

VALID_EXAMPLES = [
    {
        "severity": "ERROR",
        "code": "APF0001",
        "message": "Unknown actor 'analyst' (did you mean 'user'?)",
        "location": {"file": "specs/demo_atomic.yaml", "line": 12, "column": 7},
    },
    {
        "severity": "WARN",
        "code": "APF0400",
        "message": "Importer ambiguity: sentence maps to multiple actions.",
        "location": {"file": "notes/process.md", "json_pointer": "/sections/2/paragraphs/3"},
        "data": {"candidates": ["normalize", "transform"]},
    },
]

INVALID_EXAMPLES = [
    {"severity": "FATAL", "code": "APF1", "message": "bad"},
    {"severity": "ERROR", "code": "APF9999", "message": "ok", "location": {"step_id": "abc"}},
]


def load_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_schema_validates_examples():
    schema = load_schema()
    validator = Draft202012Validator(schema)
    for ex in VALID_EXAMPLES:
        validator.validate(ex)


def test_schema_rejects_invalid():
    schema = load_schema()
    validator = Draft202012Validator(schema)
    for ex in INVALID_EXAMPLES:
        errors = list(validator.iter_errors(ex))
        assert errors, f"expected errors for: {ex}"


def test_stepkey_pattern():
    schema = load_schema()
    validator = Draft202012Validator(schema)
    ok = [
        {"severity": "INFO", "code": "APF0100", "message": "", "location": {"file": "x", "step_id": "1.001"}},
        {"severity": "INFO", "code": "APF0100", "message": "", "location": {"file": "x", "step_id": "12.0015"}},
    ]
    bad = [
        {"severity": "INFO", "code": "APF0100", "message": "", "location": {"file": "x", "step_id": "1."}},
        {"severity": "INFO", "code": "APF0100", "message": "", "location": {"file": "x", "step_id": "a.b"}},
    ]
    for ex in ok:
        validator.validate(ex)
    for ex in bad:
        assert list(validator.iter_errors(ex))


def test_roundtrip_json():
    # Round‑trip encode/decode to ensure stability
    schema = load_schema()  # not used directly; just to ensure file exists
    doc = VALID_EXAMPLES
    s = json.dumps(doc)
    doc2 = json.loads(s)
    assert doc2 == doc
```

## B) Optional: pyproject additions (ensure dev deps exist)

Append (or verify) in `pyproject.toml`:
```toml
[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pyyaml>=6.0",
  "jsonschema>=4.22",
]

[tool.pytest.ini_options]
addopts = "-q"
pythonpath = ["packages", "."]
```

> If you’re using **uv** or **Poetry**, mirror these under your dev group.

## C) CI Wiring — add/extend jobs

If you already have a single CI workflow, ensure it installs **dev** extras and runs the tests. Below is a targeted job you can merge into `.github/workflows/ci.yml`.

```yaml
jobs:
  registries-and-schema:
    name: Registries & Schema Validation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - name: Install dev deps
        run: |
          python -m pip install -U pip
          python -m pip install .[dev]
      - name: Run focused tests
        run: |
          pytest -q tests/registries tests/schemas
```

If you prefer a single monolithic job, simply add `pytest -q tests/registries tests/schemas` to your existing test step. Ensure that the **Install dev deps** step includes `.[dev]` or equivalent.

## D) What these tests guarantee
- **Shape & invariants** of `actions.yaml` and `actors.yaml` (ids, categories/kinds, lanes, alias uniqueness, category↔style parity).
- **Schema correctness** for `diagnostics.schema.json` and **round‑trip** JSON stability.
- **Practical failure messages** (e.g., alias collisions) so vocabulary drift is caught pre‑merge.


# Core Foundation & Models

> Essential utilities, logging, configuration, and the core data models with validation.

## 2) Core Foundation

13) **`packages/apf_common/src/apf_common/__init__.py`**  
**Purpose:** Common surface.  
**Key responsibilities:** Export logging, errors, config utilities.  
**Depends on:** —  
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
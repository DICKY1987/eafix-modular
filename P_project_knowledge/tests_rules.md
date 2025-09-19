# Tests & System Rules

> Test infrastructure and system-wide rules and invariants.

## 13) Tests, Examples, Docs

85) **`tests/unit/test_step_key.py`**  
**Purpose:** StepKey correctness.  
**Key responsibilities:** Parse/format/compare; midpoints; ordering edge cases.

86) **`tests/unit/test_validation.py`**  
**Purpose:** Validator behavior.  
**Key responsibilities:** Schema violations, semantic errors, diagnostic formats.

87) **`tests/integration/test_import_export.py`**  
**Purpose:** End‑to‑end import/export.  
**Key responsibilities:** Prose→YAML→MD roundtrips; stability; determinism.

88) **`tests/integration/test_plugins.py`**  
**Purpose:** Plugin system.  
**Key responsibilities:** Manifest loading, sandbox enforcement, capability resolution.

89) **`tests/fixtures/`**  
**Purpose:** Test data.  
**Key responsibilities:** Sample YAML files, prose docs, expected outputs.

90) **`docs/`**  
**Purpose:** Documentation.  
**Key responsibilities:** API docs, tutorials, architecture decisions.

---

# Key Terms & Glossary

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

# Rules & Invariants (must‑follow)

## 1) IDs & StepKey
1. **Format:** `MAJOR.FRAC` where `MAJOR` is `1..n`, `FRAC` is a decimal with **≥3** digits; additional digits permitted for midpoints. Examples: `1.001`, `1.0015`, `2.010`.
2. **Ordering:** Strictly increasing by numeric value within a ProcessFlow. No duplicates.
3. **Midpoints:** Inserts may extend precision (e.g., `1.001` → insert → `1.0015`). **Finalization** must renumber back to canonical precision (see #4).
4. **Canonical Precision:** Default **3 fractional digits** at rest. Configurable via `registries/naming.yaml`.
5. **Stability:** References to steps use StepKey strings; any renumber operation must ship a **renumber map** and apply atomically under a **transaction**.

## 2) Source of Truth
6. **YAML First:** `demo_atomic.yaml` (or project spec) is the **only** source of truth for content. MD/Draw.io are derived. No AI‑fabricated text beyond what YAML states.
7. **Determinism:** Exporters MUST be idempotent: same YAML → byte‑identical artifacts (timestamps and volatile data excluded).

## 3) Naming & Registries
8. **Actors/Actions:** Must appear in `registries/*.yaml`. Unknown values cause **ERROR** diagnostics.
9. **Plugin IDs:** Lowercase dot‑separated: `<org>.<package>.<n>` (e.g., `apf.diagram_generator`). No spaces, only `[a‑z0‑9_.-]`.
10. **File Layout:** Artifacts land under `dist/<run_id>/...` (CI) or `derived/` (local), as configured.

## 4) Validation
11. **Schema then Semantics:** Validators run JSON Schema checks first, then semantic invariants (connectivity, uniqueness, guard completeness).
12. **Severity Levels:** `ERROR` (blocks export), `WARN` (export allowed), `INFO` (advisory). Codes follow `APF####` (see C) with stable catalog.
13. **Branching:** Every `Branch` must have exhaustive guards or a default path; merges require explicit nodes.

## 5) Import/Export
14. **Importer Rules:** `prose_to_yaml` must normalize using registries; ambiguous sentences yield **WARN** with suggested resolutions.
15. **Exporter Rules:** `drawio` exporter must emit stable geometry keyed by StepKey; MD exporter emits **one line per step** and branch cues.

## 6) Plugins & Manifests
16. **Least‑Privilege:** Manifests declare IO globs and network = **deny by default**. CI fails if manifest is over‑permissive.
17. **Capability Names:** Kebab or dot notation; MUST match implemented entry points.
18. **Compat Ranges:** Plugins declare `apf_core` compatibility using semver ranges; executor refuses mismatches.

## 7) Security & Recovery
19. **Sandbox:** Plugins run in temp workspaces; only declared globs are readable/writable.
20. **Snapshots:** Inputs and produced artifacts are snapshotted; audit log records content hashes.
21. **Transactions:** Renumber and write‑backs occur within a transaction; on failure, **no partial effects** persist.

## 8) Orchestration
22. **Job Model:** Each job is pure relative to input set; retriable with exponential backoff; idempotent when replayed.
23. **Fan‑out/Fan‑in:** Coordinator may parallelize exports; artifacts must not race (unique paths per target).

## 9) Library & Templates
24. **Template IDs:** `lib.<domain>.<n>@<semver>`; resolving without version pins latest **compatible**.
25. **Migrations:** Library schema changes ship up/down migrations and seed verification.

## 10) Parser & Streaming
26. **Chunking:** Streaming parser reads in bounded chunks; yields progressive diagnostics tagged by byte/line offsets.
27. **Resumability:** Checkpoints recorded in state store; watch loop resumes from last good offset.

## 11) Watch Loop & Artifacts
28. **Debounce:** File change debounce **≥ 500 ms**; coalesce bursts.
29. **Deterministic Output:** Artifacts use stable naming and exclude timestamps; enable caching/diffing.
30. **Audit Trail:** All operations produce structured audit events with `run_id` correlation.
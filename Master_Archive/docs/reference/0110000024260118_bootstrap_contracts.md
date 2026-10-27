---
doc_id: DOC-CONTRACT-0027
---

# Bootstrap & Contracts

> Foundation components that define schemas, configurations, and core contracts for the APF system.

## 1) Bootstrap & Contracts (define "valid" first)

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
**Used by:** Everywhere.  
**Notes/Interfaces:** Provide `get_logger(component, run_id=...)`.

8) **`registries/actions.yaml`**  
**Purpose:** Controlled vocabulary of action verbs.  
**Key responsibilities:** Canonical action types; aliases for flexible mapping.  
**Used by:** Parser, validator.

9) **`registries/naming.yaml`**  
**Purpose:** Naming conventions/rules.  
**Key responsibilities:** StepKey precision (default 3 digits), file patterns, prefixes.  
**Used by:** Models, sequencer, exporters.

10) **`registries/prose_rules.yaml`**  
**Purpose:** Text→action mapping rules.  
**Key responsibilities:** Pattern→canonical mapping; fuzzy match thresholds.  
**Used by:** Prose importer.

11) **`example_files/demo_atomic.yaml`**  
**Purpose:** Reference/demo process spec.  
**Key responsibilities:** Realistic example; integration test fixture; onboarding.  
**Used by:** Tests, docs, demos.

12) **`.../hello_world.yaml`**  
**Purpose:** Minimal "hello world" spec.  
**Key responsibilities:** Simplest valid ProcessFlow; quickstart.  
**Used by:** Tutorials, smoke tests.
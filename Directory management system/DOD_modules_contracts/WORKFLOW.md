# Workflow for Writing Module Contracts

Source:
C:\Users\richg\eafix-modular\Directory management system\ChatGPT-Contracts for Checkable !Done!.md

Approach
--------

Create module contracts the same way you create a stable API: define boundaries first, then harden them with executable checks, then implement. The contract is the SSOT; code is the implementation.

The workflow below is the practical "how the user develops these files" process.

* * *

Step-by-step workflow for writing module contracts
--------------------------------------------------

### 1) Identify the module boundary (one primary output)

For each system module, write (in plain language first):

* Purpose: why the module exists (1 sentence).
* Primary output: the one thing it produces that others depend on (file, dataset, service, decision, event).
* Owner: this module is the only place allowed to change that output definition.

Rule: if a module has multiple unrelated primary outputs, it is not a module yet - split it.

* * *

### 2) Declare the "contract surface"

This is the external interface. Do this before you list internal files.

* Inputs (must be objectively identifiable)
  * inbound artifact types (files, folders, db tables, API responses)
  * configuration keys
  * environment assumptions (OS, Python version, MT4 availability, etc.)
* Outputs
  * emitted artifacts + locations
  * schema/format guarantees
  * side effects (writes, network calls) if relevant

Rule: if an input/output cannot be validated, it's not a contract item; it belongs in docs.

* * *

### 3) Define the acceptance tests (this is "done")

Write 3-10 acceptance tests that are:

* deterministic pass/fail
* runnable by automation
* mapped to the contract surface

Examples of good acceptance tests:

* "Given fixtures/calendar_raw.json, produce calendar_normalized.csv matching calendar_normalized.schema.json."
* "Running python -m module.validator exits 0 and produces evidence/."

Rule: if you can't write acceptance tests, you don't understand the module boundary yet.

* * *

### 4) Specify validators (structural + semantic)

Validators are how you stop drift.

Typical validator types:

* structure: required files/paths exist
* schema: JSON Schema / CSV header contract / YAML schema
* static: lint/type checks (optional)
* runtime: "smoke run" that produces minimal output

Rule: every contract must have at least:

* 1 structure validator
* 1 output/schema validator

* * *

### 5) List required files as roles (not "whatever is there")

Do not enumerate every file in the module. Enumerate required roles.

Example roles:

* entrypoint
* config_schema
* io_schema
* validator
* tests
* fixtures
* README (optional, not contract-critical)

Then map role -> concrete path(s).

Rule: contract lists only what must exist for the module to be "done."

* * *

### 6) Lock dependency rules

Declare:

* upstream dependencies (modules you consume)
* downstream consumers (optional but useful)
* disallowed dependencies (very useful)

Rule: modules should not import across boundaries except through declared interfaces.

* * *

### 7) Implement / refactor to satisfy the contract

Only after the contract exists do you:

* implement code
* move files
* add schemas/tests

This flips the usual order and prevents "vibes-based done."

* * *

### 8) Add contract validation to your repo automation

Make it automatic:

* CI or local "pre-commit-like" runner
* "validate all module contracts"
* fail fast on violations
* emit evidence logs

If you're not using CI reliably, run it via a local orchestrator script and optionally a Git auto-sync workflow.

* * *

The actual file-writing method (what the user does in practice)
---------------------------------------------------------------

### Method A: Top-down (recommended for system modules)

Use when you're designing architecture or cleaning a messy repo.

1. Create a module list (inventory)
2. For each module:
   * write contract surface (inputs/outputs)
   * write acceptance tests
   * write required roles
   * only then implement

This is fastest for establishing order.

### Method B: Bottom-up (useful when module already exists in code)

Use when code exists but boundaries are unclear.

1. Inspect what the module actually does today
2. Extract:
   * what inputs it reads
   * what outputs it produces
3. Convert that into a contract
4. Add validators/tests
5. Refactor to remove undeclared dependencies

This is best for legacy modules.

### Method C: "Thin contract first" (minimum viable contract)

Use when you need quick progress without perfect design.

Start with:

* module identity
* primary output
* one schema
* one validator
* one acceptance test

Then iterate.

Rule: thin contracts must still be enforceable.

* * *

What makes "system modules" special (and how to handle them)
------------------------------------------------------------

System modules (registry maintainers, scanners, orchestrators, validators, id allocators, etc.) often have:

* multiple side effects
* broad access to the filesystem
* cross-cutting concerns

To keep them contractable:

### 1) Force a single primary output anyway

Examples:

* Registry maintainer -> produces FILE_ID_REGISTRY.csv with defined columns
* DAG builder -> produces repo_modules.dag.json
* Scanner -> produces scan_inventory.csv + evidence logs

Everything else is secondary.

### 2) Treat side effects as declared outputs

If it writes files, modifies names, or touches Git, the contract must declare:

* what it changes
* where
* under what conditions
* rollback behavior (if applicable)

### 3) Add "safety invariants"

System modules should declare invariants like:

* "never delete; only move to archive"
* "renames are atomic"
* "idempotent: second run makes no changes"
* "dry-run supported" (strongly recommended)

### 4) Evidence output is mandatory

System modules must emit:

* run_id
* logs
* changed_files list
* before/after snapshots (or patch file)

This becomes part of acceptance.

* * *

Template skeleton the user fills in (minimal but complete)
----------------------------------------------------------

Use this structure for each module contract:

* module_id, module_type, owner
* purpose
* inputs[] (typed)
* outputs[] (typed + paths + schemas)
* required_files{role:path}
* validators[] (command + expected artifacts)
* acceptance_tests[] (command + expected pass criteria)
* dependency_rules (allowed/disallowed)

The user creates it by filling in those sections in the order above.

* * *

Practical rule-of-thumb to keep contracts sane
----------------------------------------------

* If you can't test it automatically -> it's not in the contract.
* If it changes often -> it's implementation detail, not contract.
* If it affects other modules -> it must be in outputs/invariants.
* If it's cross-cutting -> split into a "system module" with explicit declared effects and evidence.

* * *

If you want, I can produce:

1. a canonical module.manifest.yaml schema (JSON Schema) so contracts are machine-validated, and
2. 3 worked examples for your system modules (scanner, registry maintainer, DAG builder) using your registry + mapping approach.

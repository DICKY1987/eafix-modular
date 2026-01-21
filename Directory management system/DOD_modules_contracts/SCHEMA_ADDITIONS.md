# Proposed Schema Additions (v1.1)

Source:
C:\Users\richg\eafix-modular\Directory management system\ChatGPT-Contracts for Checkable !Done!.md

Concrete schema changes I would make (v1.1 of the schema)
---------------------------------------------------------

Below are the minimal additions that implement the strongest parts of your evaluation without blowing up scope.

### 1) Add evidence convention

* Add top-level evidence_policy
* Add executable check evidence_subdir rule

Add:

* evidence_policy.root_dir (default: evidence/)
* evidence_policy.layout_version (e.g., 1)
* evidence_policy.required_subtrees (validation/, acceptance/, runs/)

### 2) Add side_effects (required for system modules)

* If module_type == system, require side_effects array.

Each side effect declares:

* kind (filesystem_mutation, git_staging, network_access, env_write, process_spawn, other)
* patterns / scope
* invariants enforced by which checks

### 3) Add contract versioning fields

* contract_version (SemVer string)
* dependency entries optionally constrain versions

In dependency_rules.allowed_modules[], allow:

* { module_id, contract_version_range, dependency_type }

### 4) Add partial migration tracking

* migration_state enum: none|partial|legacy
* migration object: blockers, uncontracted_deps, plan steps

### 5) Add tiering hint (optional but useful)

* contract_tier: tier1|tier2|tier3
  This is not enforcement by itself, but helps reporting and policy.

### 6) Add limits to executable checks (optional)

* limits object with fields you listed.
  Validator can enforce timeout always; others best-effort.

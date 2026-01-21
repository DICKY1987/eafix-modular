
---

# SPEC-UID-GEN-001

## Unified Filename Identity Framework (Generic / Reusable)

**Machine-Consumable Technical Specification (Indexed)**
**Edit policy:** patch-only (all future edits must target `section_id`)

---

## DOCUMENT META

```yaml
doc_id: SPEC-UID-GEN-001
title: Unified Filename Identity Framework (Generic)
version: 1.0.0
status: template
edit_policy: patch_only
audience: ai_review
```

---

## INDEX (PATCH TARGET MAP)

```yaml
index:
  - section_id: S1
    title: Purpose and Scope
  - section_id: S2
    title: Core Invariants
  - section_id: S3
    title: ID Grammar (Parametric)
  - section_id: S4
    title: Segment Definitions (Parametric Tables)
  - section_id: S5
    title: Identity Profiles (Project Config)
  - section_id: S6
    title: Unified Registry Architecture
  - section_id: S7
    title: Registry Schemas (record_kind contracts)
  - section_id: S8
    title: Counter and Allocation Rules
  - section_id: S9
    title: Filename Enforcement Rules
  - section_id: S10
    title: File Watcher Behavior
  - section_id: S11
    title: Migration and Backfill Rules
  - section_id: S12
    title: Validation and Failure Modes
  - section_id: S13
    title: FILE_ID_MAP Ledger Schema
  - section_id: S14
    title: Legacy Semantic ID Coexistence Policy
  - section_id: S15
    title: Project Configuration Contract
  - section_id: S16
    title: Bootstrap Checklist
  - section_id: S17
    title: Example Identity Profiles
```

---

## S1 — Purpose and Scope

Define a **single, deterministic identity system** where:

* Every file name begins with a **fixed-width, parseable ID prefix**
* The prefix encodes only **stable attributes** (by segment definition)
* Allocation is **registry-backed, monotonic, and collision-safe**
* Enforcement is automated by a **watcher**, with safe failure behavior
* Migration and reference rewrite are supported via an **append-only ledger** 

---

## S2 — Core Invariants

### S2.1 Filename invariant

```
<ID>_<basename>
```

* `<ID>` is fixed-width and matches the project’s `id_regex`
* ID is **immutable after allocation**
* Allocation is **registry-backed**
* Allocation is **monotonic within its allocation namespace**
* **Renaming on modify/save is prohibited** 

### S2.2 Identity vs semantics (separation rule)

* **Machine identity** = `<ID>` prefix (stable, routable, enforced)
* **Human/semantic identity** = optional legacy/semantic segment(s) after `<ID>_` (readable, not authoritative)

(Your original spec formalizes this separation via coexistence rules.) 

---

## S3 — ID Grammar (Parametric)

### S3.1 Generic grammar

```
ID := SEG1 || SEG2 || ... || SEGN
```

Constraints:

* Total width is fixed: `sum(segment.width) = ID_WIDTH`
* Segments are position-based (no delimiters inside the canonical ID)
* Optional “pretty display” separators are cosmetic only (not authoritative)

(Your current implementation is one concrete instance of this idea.) 

### S3.2 Segment types

Each segment MUST declare one of:

* `source: config` (constant for the project/repo)
* `source: derived` (deterministically derived from file or path)
* `source: allocated` (monotonic counter allocation under lock)

---

## S4 — Segment Definitions (Parametric Tables)

### S4.1 Segment definition record

```yaml
segment_def:
  name: string                # e.g., FT, REG, SEQ, SCOPE
  width: integer              # fixed digits/chars
  alphabet: enum              # numeric | base36 | hex | custom
  source: enum                # config | derived | allocated
  meaning: string
  derivation_rule: string|null
  reserved_values: [string]   # optional
```

### S4.2 Recommended canonical segment set (minimum viable)

Most projects need these four concepts (names are examples, not required):

* `TYPE` (derived): file-type or artifact-type classification
* `NS` (config): namespace / registry code (stable id kind)
* `SEQ` (allocated): monotonic sequence counter
* `SCOPE` (config): collision domain (repo_id / project_id / org_id)

Your original spec uses exactly this pattern: type + namespace + seq + scope, with the counter keyed by `(NS, TYPE, SCOPE)` and `SCOPE` as repo collision domain.  

---

## S5 — Identity Profiles (Project Config)

### S5.1 Definition

An **Identity Profile** is a project-local configuration that binds:

* ID width + alphabet
* Segment layout (ordered list of `segment_def`)
* File-type classification rules
* Namespace (registry) routing rules
* Allocation namespace rules (counter keys)

### S5.2 Profile invariants

* Profiles MUST be immutable once used for allocation, except via explicit migration.
* Projects MAY support multiple profiles only if the watcher can select deterministically.

---

## S6 — Unified Registry Architecture

### S6.1 Physical form

One authoritative registry file, plus append-only ledgers:

* `MASTER_ID_REGISTRY.json` (or `.jsonl`), containing record families
* `FILE_ID_MAP.jsonl` (append-only migration + rename ledger)

(Your original framework uses a single authoritative registry plus a ledger that is “source of truth” for renames.)  

### S6.2 Record families (type-discriminated)

At minimum:

* `registry_definition`
* `id_entry`
* `counter_state`

This is the same consolidated “record_kind” approach you already specified. 

---

## S7 — Registry Schemas (record_kind contracts)

### S7.1 `registry_definition`

```yaml
record_kind: registry_definition
ns_code: string                 # fixed width per profile (e.g., 3 chars)
registry_name: string
stable_id_type: string          # e.g., doc_id, schema_id, task_id
purpose: string
allowed_type_codes: [string]    # allowed TYPE/FT codes
routing_rules:
  - path_glob: string
    applies: boolean
required_fields:
  - string
status: active | deprecated
```

Constraint:

* `ns_code` (namespace code) is immutable once issued.

(Directly derived from your `registry_definition` contract.) 

### S7.2 `id_entry`

```yaml
record_kind: id_entry
id: string                      # fixed width; matches profile
segments:                        # optional explicit segment cache
  TYPE: string
  NS: string
  SEQ: string
  SCOPE: string
assigned_path: string
content_hash: string
created_at: timestamp
status: planned | active | failed
```

Rule:

* If segments are stored redundantly, `id` remains authoritative.

(Your current `id_entry` schema and redundancy rule.) 

### S7.3 `counter_state`

```yaml
record_kind: counter_state
counter_key: string             # canonical string encoding of tuple
last_seq: string                # fixed width per profile
updated_at: timestamp
lock_owner: string|null         # optional (implementation detail)
```

---

## S8 — Counter and Allocation Rules

### S8.1 Counter key (generic)

Counter namespace MUST be deterministic, and MUST prevent collisions across:

* namespace (NS)
* type code (TYPE)
* collision domain (SCOPE)

Canonical recommended key:

```
(NS, TYPE, SCOPE)
```

(This is exactly how your original counter key works.) 

### S8.2 Allocation algorithm (deterministic)

1. Acquire lock for counter key
2. Read last sequence
3. Increment by 1
4. Zero-pad / fixed-width normalize
5. Persist counter state
6. Release lock
7. Emit `id_entry(status=planned)` 

---

## S9 — Filename Enforcement Rules

### S9.1 On create

* If filename matches `id_regex` → no action
* Else:

  * Allocate ID
  * Rename atomically to `<ID>_<original_basename>`
  * Update `id_entry` to `active` 

### S9.2 On modify/save

* Observe only
* No renaming
* Identity remains fixed 

---

## S10 — File Watcher Behavior

### S10.1 Trigger set

* `CREATE`
* `MODIFY` (observe-only) 

### S10.2 Create workflow (canonical)

```
event → debounce → classify TYPE
      → route NS (directory rules only)
      → allocate ID
      → rename
      → ledger write
```

Your original watcher explicitly prohibits guessing registry/namespace and renaming on save. Keep that rule: it prevents nondeterministic routing and churn. 

### S10.3 Prohibited actions (non-negotiable)

* Guessing namespace/registry from content
* Renaming on save/modify
* Silent overwrite

(These are your current prohibitions; keep them.) 

---

## S11 — Migration and Backfill Rules

### S11.1 Natural key invariant

A stable natural key MUST exist to map `old path → new id` during migration planning and execution.

Required fields:

```yaml
natural_key:
  relative_path: string
  content_hash: string
  size_bytes: integer
  mtime: timestamp
  first_seen: timestamp
```

Natural key is computed once at inventory time and treated as immutable for the migration lifecycle. 

### S11.2 Migration phases (canonical)

* Phase 0 — Inventory (hash, size, extension, filters)
* Phase 1 — Plan (allocate IDs, write `planned`, no FS mutations)
* Phase 2 — Execute (leaf-first rename, atomic ops, retry collisions)
* Phase 3 — Reference Rewrite (replace old paths using ledger, validate) 

---

## S12 — Validation and Failure Modes

### S12.1 Validation gates

* ID grammar conformance
* Namespace existence
* Required fields per namespace contract
* Counter monotonicity
* Filename ↔ registry consistency 

### S12.2 Failure handling

* Allocation failure → rollback counter
* Rename failure → mark entry `failed`
* Validator failure → halt watcher 

---

## S13 — FILE_ID_MAP Ledger Schema

### S13.1 Purpose

`FILE_ID_MAP` is the **source of truth** for every rename and for reference rewrites. It must be append-only and audit-perfect. 

### S13.2 Schema (generic)

```yaml
record_kind: file_id_map_entry
old_rel_path: string
old_hash: string
new_id: string
new_rel_path: string
type_code: string
ns_code: string
seq: string
scope: string
status: planned | renamed | failed | skipped
created_at: timestamp
renamed_at: timestamp | null
error_message: string | null
```

### S13.3 Storage format

* Primary: JSONL (append-only)
* Secondary: compact JSON index for lookups by `old_rel_path` or `new_id` 

### S13.4 Invariants

* 1 file → exactly 1 ledger entry
* `old_rel_path` unique
* `new_id` unique
* Status transitions: `planned → renamed | failed | skipped`
* Entries immutable after `renamed` 

---

## S14 — Legacy Semantic ID Coexistence Policy (Generic)

### S14.1 Problem class

Many repos already embed human-readable semantic IDs in filenames. Replacing them breaks references and loses meaning. 

### S14.2 Decision

Use **machine ID prefix + preserve legacy semantic segment**:

```
<ID>_<LEGACY_SEMANTIC_ID>__<basename>.<ext>
```

(Your original spec uses this exact pattern with `DOC-...__`.) 

### S14.3 Rules

1. New files: watcher assigns `<ID>_` prefix; authoring flow supplies or infers legacy segment
2. Existing files: migration prepends `<ID>_` to existing legacy filename
3. Lookup: either identity may be used; registry maps between them
4. Display: tooling MAY hide `<ID>_` for humans 

### S14.4 Schema extension

Add to `id_entry`:

```yaml
legacy_id: string | null
semantic_name: string | null
```

(Your current schema extension uses `doc_id` + `semantic_name`; genericize `doc_id` → `legacy_id`.) 

---

## S15 — Project Configuration Contract

Each project adopting this framework MUST define a single config file (example name):

`IDENTITY_CONFIG.yaml`

```yaml
identity_framework: SPEC-UID-GEN-001

project:
  project_code: string              # human label (not in the ID unless you choose)
  collision_scope: string           # SCOPE segment value (repo_id / org_id)
  repo_root: string

id_profile:
  profile_id: string                # e.g., NUM16_FT_NS_SEQ_SCOPE
  id_width: integer
  alphabet: numeric | base36 | hex | custom
  delimiter_after_id: "_"           # required
  id_regex: string                  # must match ID + delimiter
  segments:
    - name: string
      width: integer
      alphabet: numeric | base36 | hex | custom
      source: config | derived | allocated
      meaning: string
      derivation_rule: string | null

type_classification:
  method: extension | path_rules | hybrid
  table:
    - match: string                 # ".py" or glob
      type_code: string             # must match TYPE segment width/alphabet

namespace_routing:
  method: directory_rules_only
  rules:
    - path_glob: string
      ns_code: string               # must match NS segment width/alphabet

allocation:
  counter_key: [NS, TYPE, SCOPE]    # ordered tuple (recommended)
  lock:
    mode: filesystem | sqlite | service
    lock_path: string

storage:
  master_registry_path: string      # e.g., MASTER_ID_REGISTRY.json
  file_id_map_path: string          # e.g., FILE_ID_MAP.jsonl
```

---

## S16 — Bootstrap Checklist (Per Project)

1. Choose collision domain value for the project (`SCOPE`) (repo_id / org_id) (must be constant). 
2. Define one `id_profile` (segment layout + width + regex). 
3. Create initial `registry_definition` records for each namespace (stable id type). 
4. Implement allocation lock + counter_state persistence. 
5. Deploy watcher with CREATE-only enforcement + MODIFY observe-only. 
6. If adopting into an existing repo: run Phase 0–3 migration using ledger + rewrite. 

---

## S17 — Example Identity Profiles

### S17.1 Example A (your current pattern, generalized names)

```yaml
profile_id: NUM16_TYPE_NS_SEQ_SCOPE
id_width: 16
alphabet: numeric
segments:
  - { name: TYPE,  width: 2, source: derived,   meaning: file type code, derivation_rule: extension }
  - { name: NS,    width: 3, source: config,    meaning: registry namespace code }
  - { name: SEQ,   width: 5, source: allocated, meaning: monotonic sequence }
  - { name: SCOPE, width: 6, source: config,    meaning: collision domain (repo_id) }
counter_key: [NS, TYPE, SCOPE]
delimiter_after_id: "_"
id_regex: "^\\d{16}_.+"
```

This corresponds directly to your concrete grammar and counter key.  

### S17.2 Example B (base36, wider IDs, no “file type” segment)

Use this when file-type encoding isn’t stable or useful:

```yaml
profile_id: B36_20_NS_SEQ_SCOPE
id_width: 20
alphabet: base36
segments:
  - { name: NS,    width: 4, source: config,    meaning: namespace }
  - { name: SEQ,   width: 10, source: allocated, meaning: monotonic sequence }
  - { name: SCOPE, width: 6, source: config,    meaning: collision domain }
counter_key: [NS, SCOPE]
delimiter_after_id: "_"
id_regex: "^[0-9A-Z]{20}_.+"
```

---

If you want this to be even more reusable across many repos, the next step is to standardize **one shared framework spec (this)** plus **per-project `IDENTITY_CONFIG.yaml`**, and treat the config file as the only thing that changes per project.

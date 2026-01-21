## SEQ Allocation Solution — Monotonic counter per (TYPE, NS, SCOPE)

```yaml
document_id: DOC-ID-SEQ-ALLOC-001
title: SEQ Allocation Contract (NUM16 TYPE+NS+SEQ+SCOPE)
version: 1.0.0
status: active
applies_to_profile: NUM16_TYPE_NS_SEQ_SCOPE
source_of_truth:
  identity_config: IDENTITY_CONFIG.yaml
  counter_store: COUNTER_STORE.json
  counter_store_schema: COUNTER_STORE.schema.json
```

### Goal
Allocate the **SEQ (5 digits)** portion of the 16-digit filename ID as:

**SEQ = next integer in the counter stream keyed by (TYPE, NS, SCOPE)**.

No buffers. No numeric ranges reserved per type. No renumbering.

---

## Definitions

### Segments
* **TYPE**: 2 digits (`^\d{2}$`) derived from extension via `IDENTITY_CONFIG.yaml/type_classification`.
* **NS**: 3 digits (`^\d{3}$`) derived from `relative_path` via `IDENTITY_CONFIG.yaml/namespace_routing`.
* **SEQ**: 5 digits (`^\d{5}$`) allocated by this contract.
* **SCOPE**: 6 digits (`^\d{6}$`) fixed constant `IDENTITY_CONFIG.yaml/scope`.

### Allocation key
`allocation_key = (TYPE, NS, SCOPE)`

### Counter stream
A **counter stream** is the monotonic SEQ sequence associated with one `allocation_key`.

---

## Hard invariants

1. **Uniqueness**: No two allocated IDs may share the same full 16-digit value.
2. **Monotonic per key**: For a given `(TYPE, NS, SCOPE)`, SEQ only increases.
3. **No renumbering**: Once an ID is allocated to a file and recorded, it must never change.
4. **Reserved value**: SEQ `00000` is invalid/reserved.
5. **Capacity**: SEQ range is `00001..99999`. If the next allocation exceeds 99999, allocation fails.

---

## Data stores

### Counter store
**File:** `COUNTER_STORE.json`

**Meaning:** tracks the last allocated SEQ for each counter stream.

**Key format (canonical):**
`counter_key_string = "{SCOPE}:{NS}:{TYPE}"`

Example: `"260118:200:20"` means `SCOPE=260118`, `NS=200`, `TYPE=20`.

**Value:** last allocated SEQ as an integer (0..99999). 0 means “no IDs issued yet for this stream”.

**Schema:** `COUNTER_STORE.schema.json`

### Lock
**File lock path:** `.identity_allocation.lock`

All allocations MUST hold the lock while reading/updating/writing `COUNTER_STORE.json`.

### Optional ledger (recommended)
**File:** `ALLOCATION_LEDGER.jsonl`

Append-only audit trail. Each allocation writes one record:

```json
{"utc":"2026-01-18T18:02:11Z","allocation_key":{"type":"20","ns":"200","scope":"260118"},"seq":6,"doc_id":"2020000006260118","relative_path":"scripts/python/foo.py","action":"allocated"}
```

Ledger is for audit/replay. It does not replace the counter store.

---

## Allocation algorithm — single file

### Inputs
* `relative_path` (portable)
* `extension` (lowercase, no dot)
* Derived via `IDENTITY_CONFIG.yaml`:
  * `TYPE` (2 digits)
  * `NS` (3 digits)
  * `SCOPE` (6 digits)

### Output
* `doc_id` (16 digits) = `TYPE + NS + SEQ(5) + SCOPE`

### Steps
1. **Derive TYPE/NS/SCOPE** from config.
2. Validate:
   * TYPE matches `^\d{2}$`
   * NS matches `^\d{3}$`
   * SCOPE matches `^\d{6}$`
3. Acquire `.identity_allocation.lock`.
4. Load and validate `COUNTER_STORE.json` against schema.
5. Build `counter_key_string = "{SCOPE}:{NS}:{TYPE}"`.
6. Read `last_seq = counters.get(counter_key_string, 0)`.
7. Compute `next_seq = last_seq + 1`.
8. Validate `1 <= next_seq <= 99999`.
9. Write back `counters[counter_key_string] = next_seq`.
10. Update `updated_utc`.
11. Persist counter store **atomically**:
    * write `COUNTER_STORE.json.tmp`
    * fsync
    * rename over `COUNTER_STORE.json`
12. Release lock.
13. Format:
    * `SEQ = next_seq` left-padded to 5 digits
    * `doc_id = TYPE + NS + SEQ + SCOPE`
14. Append to `ALLOCATION_LEDGER.jsonl` (recommended).

### Notes
* This contract does **not** require contiguous SEQ values without gaps; it requires monotonicity and uniqueness.
* If rename fails after allocation, **do not decrement** the counter. Record failure in the ledger and retry using the already-assigned planned ID (planner responsibility).

---

## Allocation algorithm — deterministic backfill (initial naming)

### Goal
Assign IDs to an existing set of files missing IDs in a deterministic way.

### Steps
1. Derive `(TYPE, NS, SCOPE)` for every file.
2. Group files by `(TYPE, NS, SCOPE)`.
3. Within each group, sort by:
   1) `relative_path.casefold()` ascending
4. Acquire the allocation lock once for the entire backfill run.
5. For each group in stable order (TYPE numeric asc, then NS numeric asc, then SCOPE numeric asc):
   * Start from `last_seq` in the counter store.
   * Allocate sequentially for each file in the sorted list.
6. Persist the counter store once at the end (atomic write).
7. Emit a planning table mapping `relative_path -> planned_id`.

---

## Validation rules

### ID format
* `doc_id` must match `^\d{16}$`.
* filename must match `^\d{16}_.+`.

### Cross-check
Given a file row (from `file_scan_*.csv`) with populated `planned_id`, the following must be true:
* `planned_id[0:2] == type_code`
* `planned_id[2:5] == ns_code`
* `planned_id[10:16] == scope`

(Positions assume `TYPE(2) + NS(3) + SEQ(5) + SCOPE(6)`.)

---

## What this eliminates

* Buffer blocks between types
* Manual range planning
* Renumbering when categories expand
* Cross-type collisions caused by overlapping ranges

---
doc_id: DOC-LEGACY-0035
---

# Orchestration

> Job coordination, state machines, and high-level execution planning.

## 8) Orchestration

50) **`packages/orchestration/src/orchestration/__init__.py`**  
**Purpose:** Orchestration surface.  
**Key responsibilities:** Export coordinator, job/state abstractions.

51) **`.../state.py`**  
**Purpose:** Runtime state machines.  
**Key responsibilities:** Runs, phases, transitions; resumability.  
**Depends on:** Recovery/state.

52) **`.../jobs.py`**  
**Purpose:** Job definitions & queues.  
**Key responsibilities:** Define units of work for import/validate/export; retry/backoff.  
**Used by:** Coordinator, watch.

53) **`.../coordinator.py`**  
**Purpose:** High‑level coordinator.  
**Key responsibilities:** Plan execution DAGs, fan‑out/fan‑in across plugins, collect artifacts.  
**Depends on:** Jobs/state, executor, recovery.
---
doc_id: DOC-LEGACY-0038
---

# Recovery & State Management

> State management, transactions, snapshots, and audit trails for system reliability.

## 7) Recovery & State

44) **`packages/recovery/src/recovery/__init__.py`**  
**Purpose:** Recovery entrypoint.  
**Key responsibilities:** Export snapshot/transaction APIs.

45) **`.../snapshot.py`**  
**Purpose:** Snapshot inputs/outputs.  
**Key responsibilities:** Content‑addressed storage; diff helpers.  
**Used by:** Executor, audit.

46) **`.../transaction.py`**  
**Purpose:** Transaction/rollback context.  
**Key responsibilities:** Begin/commit/rollback; integrate with orchestrator.  
**Used by:** Plugins, engine.

47) **`.../audit_log.py`**  
**Purpose:** Append‑only audit trail.  
**Key responsibilities:** Structured events, correlation IDs, integrity checks.  
**Used by:** Compliance, debugging.

48) **`packages/state/src/state/__init__.py`**  
**Purpose:** State/versioning entrypoint.  
**Key responsibilities:** Expose document state stores, versioning APIs.

49) **`.../documentation_state.py`**  
**Purpose:** Documentation/process state manager.  
**Key responsibilities:** Version graph, autosave, migrations; restore points for editors.  
**Used by:** Desktop, watch loop, service.
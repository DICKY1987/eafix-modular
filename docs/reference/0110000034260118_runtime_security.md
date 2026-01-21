---
doc_id: DOC-LEGACY-0041
---

# Runtime & Security

> Plugin system, execution environment, and security policy enforcement.

## 6) Runtime & Security

40) **`packages/huey_core/src/huey_core/__init__.py`**  
**Purpose:** Plugin runtime surface.  
**Key responsibilities:** Export plugin loader, executor, manifest APIs.

41) **`.../manifest.py`**  
**Purpose:** Load/validate plugin manifests.  
**Key responsibilities:** Parse `plugin.yaml`; check compat ranges; capability resolution.  
**Depends on:** Schema loader.  
**Used by:** Executor, CLI.

42) **`.../executor.py`**  
**Purpose:** Safe plugin execution wrapper.  
**Key responsibilities:** Sandbox enforcement, resource limits, recovery hooks, audit.  
**Depends on:** Manifest, policy, recovery.  
**Used by:** Orchestrator.

43) **`.../policy.py`**  
**Purpose:** Security policy enforcement.  
**Key responsibilities:** IO restrictions, data class permissions, network deny‑by‑default.  
**Depends on:** Manifest declarations.  
**Used by:** Executor.
---
doc_id: DOC-LEGACY-0042
---

# Sequencing & Editing

> Components that handle StepKey management, renumbering, and programmatic editing operations.

## 5) Sequencing & Editing

34) **`packages/sequencing/src/sequencing/__init__.py`**  
**Purpose:** Sequencing surface.  
**Key responsibilities:** Export insert/renumber APIs.

35) **`.../step_key.py`**  
**Purpose:** StepKey manipulation logic.  
**Key responsibilities:** Insert‑at, renumber‑to‑canonical, midpoint generation.  
**Depends on:** Core models.  
**Used by:** Sequencer plugin, desktop editor.

36) **`.../sequencer.py`**  
**Purpose:** High‑level sequencer operations.  
**Key responsibilities:** Apply edits; produce renumber maps; maintain invariants.  
**Depends on:** StepKey logic.  
**Used by:** CLI `seq` command, plugins.

37) **`packages/editing/src/editing/__init__.py`**  
**Purpose:** Editing surface.  
**Key responsibilities:** Export editor APIs and transaction support.

38) **`.../editor.py`**  
**Purpose:** Programmatic YAML editor.  
**Key responsibilities:** Apply transformations; atomic operations; undo/redo.  
**Depends on:** Models, sequencer.  
**Used by:** Edit scripts, desktop app.

39) **`.../edit_script.py`**  
**Purpose:** Parse/execute edit scripts.  
**Key responsibilities:** Line‑oriented DSL; backup/restore; audit log.  
**Depends on:** Editor.  
**Used by:** CLI, automation.
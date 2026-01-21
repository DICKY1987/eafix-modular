---
doc_id: DOC-LEGACY-0034
---

# Import/Export Engine

> Components responsible for converting between different formats (YAML ↔ human-readable ↔ draw.io XML).

## 4) Import/Export Engine

26) **`packages/import_export/src/import_export/__init__.py`**  
**Purpose:** Import/export surface.  
**Key responsibilities:** Export register APIs for importers/exporters.  
**Depends on:** Submodules.

27) **`.../importers/__init__.py`**  
**Purpose:** Importer registry.  
**Key responsibilities:** Register file format importers.  
**Used by:** CLI, plugins.

28) **`.../importers/prose_importer.py`**  
**Purpose:** Convert structured prose → YAML.  
**Key responsibilities:** Parse MD/docx; map headings→steps, bullets→substeps; apply `prose_rules.yaml`.  
**Depends on:** Parser, registries.  
**Used by:** CLI `import` command.

29) **`.../importers/yaml_importer.py`**  
**Purpose:** Load/normalize YAML files.  
**Key responsibilities:** Parse YAML; validate against schema; resolve `$includes`.  
**Depends on:** Schema loader.  
**Used by:** All tools loading YAML.

30) **`.../exporters/__init__.py`**  
**Purpose:** Exporter registry.  
**Key responsibilities:** Register target format exporters.  
**Used by:** CLI, plugins.

31) **`.../exporters/markdown_exporter.py`**  
**Purpose:** ProcessFlow → clean Markdown.  
**Key responsibilities:** One line per step; decision trees; numbered/bulleted formats.  
**Depends on:** Models.  
**Used by:** Human‑readable output.

32) **`.../exporters/drawio_exporter.py`**  
**Purpose:** ProcessFlow → draw.io XML.  
**Key responsibilities:** Geometry layout; stable positioning; theming.  
**Depends on:** Models, layout engine.  
**Used by:** Diagram generation.

33) **`.../exporters/json_exporter.py`**  
**Purpose:** ProcessFlow → JSON (normalized).  
**Key responsibilities:** Clean JSON representation; API‑friendly format.  
**Depends on:** Models.  
**Used by:** Service endpoints, integrations.
# Process Library & Parser

> Reusable step templates and document parsing capabilities.

## 9) Process Library

54) **`packages/process_library/src/process_library/__init__.py`**  
**Purpose:** Library surface.  
**Key responsibilities:** Query/templates API.

55) **`.../db.py`**  
**Purpose:** SQLite access layer.  
**Key responsibilities:** CRUD for templates/steps, FTS indexes, referential integrity.  
**Depends on:** `library.schema.json`.

56) **`.../migrations.py`**  
**Purpose:** Database migrations.  
**Key responsibilities:** Schema versions, up/down scripts, seed data.  
**Used by:** CI, local bootstrap.

57) **`.../templates.py`**  
**Purpose:** Prefab step templates.  
**Key responsibilities:** Resolve `template_id@version`, parameter substitution, provenance.

## 10) Parser (structured docs → models)

58) **`packages/apf_parser/src/apf_parser/__init__.py`**  
**Purpose:** Parser entrypoint.  
**Key responsibilities:** Public API for document→ProcessFlow parsing.

59) **`.../structured_document.py`**  
**Purpose:** Deterministic parser for structured docs.  
**Key responsibilities:** Map headings/tables/lists to steps/branches; attach metadata.  
**Depends on:** Models, validator.

60) **`.../streaming.py`**  
**Purpose:** Incremental parser for large documents.  
**Key responsibilities:** Chunked reads, bounded memory, progressive diagnostics; resumable offsets.  
**Used by:** Watch loop, service.
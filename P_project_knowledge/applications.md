---
doc_id: DOC-LEGACY-0028
---

# Applications

> User-facing applications: CLI tools, web service, and desktop interface.

## 12) Apps (thin wrappers)

73) **`apps/cli/apf/__init__.py`**  
**Purpose:** CLI package marker.  
**Key responsibilities:** Expose console entry point.

74) **`apps/cli/apf/__main__.py`**  
**Purpose:** CLI entry.  
**Key responsibilities:** Argparse/Typer wiring; subcommand dispatch to plugins.

75) **`apps/cli/apf/commands/export.py`**  
**Purpose:** `apf export` subcommand.  
**Key responsibilities:** Load file → exporter(s) → write artifacts; exit codes.

76) **`apps/cli/apf/commands/validate.py`**  
**Purpose:** `apf validate` subcommand.  
**Key responsibilities:** Run schema+semantic checks; print diagnostics table/NDJSON.

77) **`apps/cli/apf/commands/seq.py`**  
**Purpose:** `apf seq` subcommand.  
**Key responsibilities:** Insert/renumber, dry‑run, writeback with backup.

78) **`apps/cli/apf/commands/watch.py`**  
**Purpose:** Watch daemon for zero‑touch loop.  
**Key responsibilities:** File watcher → enqueue jobs → engine run → artifact refresh; debounce/throttle.  
**Depends on:** Orchestrator, parser, exporters, state.

79) **`apps/service/main.py`**  
**Purpose:** FastAPI app factory.  
**Key responsibilities:** Dependency injection, lifespan, logging.

80) **`apps/service/routes.py`**  
**Purpose:** HTTP endpoints.  
**Key responsibilities:** `/decide`, `/export`, `/validate`; stream diagnostics; return artifacts.

81) **`apps/service/watch.py`**  
**Purpose:** Service‑side watcher (optional).  
**Key responsibilities:** Background task to monitor repos or queues; hot‑reload artifacts.

82) **`apps/desktop/main.py`**  
**Purpose:** PySide6 launcher.  
**Key responsibilities:** App bootstrap, menus, theme, telemetry opt‑in.

83) **`apps/desktop/ui_shell.py`**  
**Purpose:** Main window shell.  
**Key responsibilities:** Docking layout, status bar, notifications, error panel.

84) **`apps/desktop/editors/yaml_editor.py`**  
**Purpose:** Schema‑aware YAML editor.  
**Key responsibilities:** Live validation, StepKey helpers, jump‑to‑diagnostic, diff view.
# Developing the GUI Terminal (Phase 1 Scaffold)

This document maps the CODEX_IMPLEMENTATION_PLAN.md to concrete next steps inside this repository.

Phase 1 — Foundation & Consolidation
- Consolidate `enhanced_pty_terminal.py` into:
  - `src/gui_terminal/core/pty_backend.py` (Windows/Unix backends)
  - `src/gui_terminal/ui/terminal_view.py` (terminal widget)
  - `src/gui_terminal/core/event_system.py` (event bus + platform integration)
  - `src/gui_terminal/core/session_manager.py` (session lifecycle)
- Integrate security framework:
  - Port logic from `security_configuration.py` into `src/gui_terminal/security/policy_manager.py`
  - Wire command filtering and resource limits where applicable
- Establish minimal main window:
  - Implement PyQt6 MainWindow and connect a basic TerminalView
  - Guard imports so headless mode continues to work without PyQt installed

Validation
- Run: `PYTHONPATH=gui_terminal/src python -m gui_terminal.main`
- Config: `gui_terminal/config/default_config.yaml`, `gui_terminal/config/security_policies.yaml`
- No changes to the main CLI or tests are required for Phase 1 scaffold.

Next Phases (at a glance)
- Phase 2: Platform websocket integration, cost tracking
- Phase 3: Plugin system, session persistence
- Phase 4: Comprehensive tests, security/performance benchmarking
- Phase 5: Docs and deployment automation


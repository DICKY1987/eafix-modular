CLI Multi-Rapid GUI Terminal (Scaffold)

Overview
- This directory contains a standalone scaffold for the GUI Terminal described in CODEX_IMPLEMENTATION_PLAN.md.
- It provides package structure, configuration files, and minimal Python stubs to unblock incremental development.
- PyQt is optional; the current main entry runs without GUI dependencies and prints a friendly message.

Run
- Module entry: `python -m gui_terminal.main` (uses safe, headless fallback if PyQt6 is not installed).
- Config files live under `gui_terminal/config`.

Structure
- `src/gui_terminal/` — package sources
- `config/` — default and security configuration YAMLs
- `requirements*.txt` — dependency pins for the GUI project only
- `legacy/` — placeholder for legacy sources (optional, to be populated as consolidation proceeds)

Notes
- This scaffold does not integrate with the main CLI yet and does not affect repo test coverage.
- Follow the implementation plan phases to progressively replace stubs with real functionality.


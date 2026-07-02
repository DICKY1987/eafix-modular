# GUI Terminal Documentation

User Guide
- Run headless mode: `PYTHONPATH=gui_terminal/src python -m gui_terminal.main`
- Configuration: edit files under `gui_terminal/config/`
- Plugins: drop `*.py` into directories listed in `plugins.plugin_directories`.

Administrator Guide
- Dependencies: see `gui_terminal/requirements.txt`
- Optional platform integrations: ensure the repository root is on `PYTHONPATH` to access `lib.cost_tracker` and `src/integrations`.
- Security policies: tune `security_policies.yaml`.

Developer Guide
- Code layout under `gui_terminal/src/gui_terminal/`:
  - `core/` — PTY backend, events, sessions, cost/platform bridges
  - `security/` — policy management
  - `ui/` — UI widgets (PyQt6 to be implemented)
  - `plugins/` — plugin system and manager
- Unit tests live in `tests/test_gui_terminal_*.py`.

Configuration Tips
- `ui.strip_ansi` (default: true): remove ANSI escape sequences from the terminal output widget for readability. Set to `false` to show raw sequences (colors/control codes).
- `security.resource_limits.enforce`: when true and `psutil` is installed, the GUI blocks commands if process memory/cpu exceed thresholds.

Deployment Notes
- For packaging as a standalone tool, create a separate `pyproject.toml` in `gui_terminal/` and publish to your package index; not included here to avoid impacting the main build.
- Containerization: install requirements and run the module with `PYTHONPATH=gui_terminal/src`.


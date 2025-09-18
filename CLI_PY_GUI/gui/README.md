# Python CLI Cockpit — Patchset v1

This bundle delivers:
- `pty_terminal_runner.py`: PTY-backed GUI terminal (parity-focused).
- `gui_test_server.py`: headless server for real PTY tests (offscreen Qt).
- `parity_test_harness.py`: connects to server and validates parity.
- `quick_actions.json`: sample Quick Actions.
- `GUI_Parity_Goals.md` and `Operator_Guide.md`: concise docs.

## Requirements
- Python 3.9+
- PyQt6
- pywinpty (Windows only, for ConPTY)
- psutil (optional)

```bash
pip install -r requirements.txt
```

## Run
- GUI: `python pty_terminal_runner.py`
- CI test: start `gui_test_server.py` then `parity_test_harness.py`.


## New panels
- **Workflows (DAG):** visualizes nodes and dependencies from `~/.python_cockpit/plan.json`. Updates live via the local JSON event server on port 45455.
- **Merge Queue:** shows serialized pre-merge checks and status per branch.

## Streaming events
The GUI starts a tiny TCP server at `127.0.0.1:45455`. Send JSON events (one per line) to update the DAG, merge queue, and budget/health.
Example:
```json
{"type":"node.update","node_id":"n2","status":"running"}
```

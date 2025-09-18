# Operator Guide (Python CLI Cockpit)

## Quick start
```bash
python pty_terminal_runner.py
```
- Opens a window with a PTY-backed terminal.
- Top strip shows the **exact command** being run.

## Controls
- **Send**: type a command in the input box and click Send (local echo).
- **Ctrl‑C / EOF / Kill**: sends signals to the subprocess (platform-aware).
- **Tabs**: use multiple terminals for parallel workflows.

## Headless testing (CI)
In one shell:
```bash
python gui_test_server.py
```
In another shell:
```bash
python parity_test_harness.py
```
The harness connects to the headless app and validates real PTY behaviors.

## Tips
- For Windows, install `pywinpty` (provides `winpty` import).
- To customize Quick Actions, edit `quick_actions.json`.

### Artifacts panel
- The left pane lists files created/modified during the run (relative to CWD). Double-click to open.

### System Terminal
- Click **Open System Terminal** to launch your OS terminal at the tab's working directory.

### Cost & Health Sidebar
- The right pane shows plan budget, burn, concurrency, and tool health.
- Update `~/.python_cockpit/health.json` to feed live data from your IPT.


### Workflows (DAG)
- The **Workflows (DAG)** tab auto-loads `~/.python_cockpit/plan.json` and updates when your IPT sends `plan.load` or `node.update` events to port 45455.
- Colors: queued (gray), running (blue), passed (green), failed (red).

### Merge Queue
- The **Merge Queue** tab lists branches queued for pre-merge checks. Send `merge.enqueue`, `merge.update`, and `merge.dequeue` events.

### Event emitter demo
- Start the GUI, then run: `python gui/emit_demo_events.py` to simulate plan updates and queue activity.

### History & Timeout
- Use Up/Down arrows in the command box to recall previous commands.
- You can set a default timeout in `~/.python_cockpit/config.json`.

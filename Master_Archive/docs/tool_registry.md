# Tool Registry v0.1

Central catalog of work tools (WT) used by IPT for planning and execution.

## Files

- `config/tools.yaml`: declarative tool definitions
- `state/tool_health.json`: last probe results written by `ipt_tools_ping.py`
- `scripts/ipt_tools_ping.py`: probes tools and emits JSON

## tools.yaml schema (v1)

```yaml
version: 1
tools:
  - name: string
    capabilities: [string]
    version_cmd: [string, ...]
    health_cmd: [string, ...]
    fallback: [string]
    cost_hint: float
    install_hint: string
```

## Usage

```bash
python scripts/ipt_tools_ping.py
# writes: state/tool_health.json
```

Planner can filter healthy tools by capability and consider `cost_hint` for cost-aware selection.


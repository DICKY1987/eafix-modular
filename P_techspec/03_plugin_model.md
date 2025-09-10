# Plugin Model (Indicators & Transforms)

**Status:** Updated • **Goal:** Add features without touching core by using declarative manifests and strict interfaces.

## 1. Plugin Types
- **Indicator**: computes values from market/calendar data; emits standardized `Signal` fields (including `p`/`n`).  
- **Transform**: enriches or normalizes pipeline events (e.g., calendar field harmonization, debounce).

## 2. Manifest (YAML)
```yaml
name: my_indicator
version: 1.0.0
type: indicator
entrypoint: indicators/my_indicator.py:Indicator
params:
  - key: lookback
    type: int
    default: 100
outputs: [value, bands]          # informs UI plots
ui:
  render_mode: overlay           # overlay | panel
  default_cell: 2x1
contracts:
  signal_schema: v1
  transport: csv                 # must respect file_seq + checksum_sha256
acceptance:
  - unit_tests: pass
  - coverage: ">=90%"
  - latency_p95_ms: "<=20"
```

## 3. Python Interfaces
```python
class Indicator:
    def __init__(self, **params): ...
    def fit(self, df): ...      # optional warmup
    def compute(self, tick): ...# returns dict with Signal fields

class Transform:
    def apply(self, event): ... # returns event or list of events
```

## 4. Lifecycle
- **Load → Validate manifest → Dependency check → Register → Health probe → Accept/Reject** (with reasons).

## 5. QA Gates
- Unit/Golden tests; schema validation; latency budgets; determinism (same input → same output).

## 6. GUI Autowiring
- The manifest powers form generation, default placement, and output plotting without custom code.

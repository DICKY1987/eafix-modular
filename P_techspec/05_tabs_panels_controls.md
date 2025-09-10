# Tabs, Panels & Controls

**Status:** Updated • **Goal:** Document every on‑screen control with its function, contract, and acceptance cues.

## 1. Signals Tab
**Panels**: Active Signals table; Event Details drawer; Quick Filters  
**Controls**:
- **Refresh**: re‑read `active_calendar_signals.csv` (verifies `file_seq` monotonic + checksum)
- **Filter: Symbol / Proximity / Impact**: server‑side predicates
- **Open in Matrix**: opens mapping view for selected Hybrid context
**Acceptance**: actions < 200ms; table reflects new file within 5s of replace.

## 2. History Tab
**Panels**: Trades table; Chain Drill‑down (O→R1→R2)  
**Controls**:
- **Export CSV**: filtered `trade_results.csv`
- **Reconcile**: compare selected range with broker statement; shows slippage delta
**Acceptance**: append‑only writes visible within 3s; reconcile completes < 10s for 10k trades.

## 3. System Status Tab
**Tiles**: Transport Uptime, Coverage %, Fallback Rate, Decision Latency p95/p99, Slippage Δ, Conflict Rate, Calendar Revisions, Breakers, CSV Integrity, **Broker Clock Skew**  
**Controls**:
- **Run Socket Test**: executes `simple_socket_test.py`; posts result to Diagnostics log
- **Probe Broker Skew**: runs `broker_skew_probe.py`; updates skew badge & state (HEALTHY/DEGRADED)
**Acceptance**: clock‑skew DEGRADED when |offset|>120s or stale>15m; decisions suppressed.

## 4. Config Tab
**Panels**: Global Settings; Per‑Indicator/Strategy forms; Comm Settings  
**Controls**:
- **Save**: validates and writes config (schema‑checked)
- **Test Bridge**: sends heartbeat over chosen adapter; expects ACK < 2s
**Acceptance**: invalid fields blocked with inline errors; bridge test result visible in Diagnostics.

## 5. Diagnostics Tab
**Panels**: Live Log; Integrity Check; Router State; Alerts  
**Controls**:
- **CSV Integrity Check**: runs `csv_integrity_check.py`; reports seq gaps/checksum failures
- **Download Logs**: bundles last 24h
**Acceptance**: integrity check reports within 3s; logs bundle < 5s.

## 6. Common Buttons (all tabs)
- **Copy Link** (deep link to current state)
- **Help** (opens context help for the tab)

# GUI Specification – Controls & Actions + Key Additions

_Export generated: 2025-09-05T20:48:26Z_

This export captures the updated **Hierarchical Index (GI)** and all newly added/modified sections including **Controls & actions (buttons)** for each tab, plus the key functional additions from the latest system spec (rev2): Emergency STOP/RESUME for Calendar, Broker Clock Skew/DEGRADED mode, expanded Health tiles, operator kill‑switches, bridge/comm settings, Manual Overrides, and alert triggers.

---


## Hierarchical Index (GI)
1) Scope & Principles
   - 1.1 Purpose & scope
   - 1.2 Design tenets
   - 1.3 Explicit exclusions (layout/engine wiring where noted)
2) Architecture Overview
   - 2.1 Core runtime services
     - 2.1.1 EventBus (pub/sub, metrics)
     - 2.1.2 StateManager (snapshots, actions)
     - 2.1.3 Feature Registry (indicators/views/tools)
     - 2.1.4 Theme System (semantic tokens)
     - 2.1.5 Toast/Alert Manager (queues, priorities)
     - 2.1.6 Risk Ribbon (risk posture summary)
   - 2.2 App layout & navigation
   - 2.3 Grid Manager (panels)
3) Indicator Plugin Model
   - 3.1 Registration
   - 3.2 Config schema (auto-forms)
   - 3.3 Execution (deterministic outputs)
   - 3.4 Display (render modes)
   - 3.5 Safety (hot reload, transactions)
4) Validation & Controls (Unified UX Layer)
   - 4.1 Control types (booleans, numbers, enums, text, dynamic)
   - 4.2 Validation behaviors (debounce, severity)
   - 4.3 Accessibility & help
   - 4.4 Reusability (forms/API/templates)
5) Normalized Signal Model
   - 5.1 Core fields
   - 5.2 Probability extension fields
   - 5.3 Contract guarantees
6) Conditional Probability Engine (Concept)
   - 6.1 Parameter axes (M/W/K/T)
   - 6.2 Outputs (p, n)
   - 6.3 Confidence tiers
   - 6.4 Policy hooks
   - 6.5 Transparency & export
7) Live Tab
   - 7.1 Key panels
   - 7.2 Filters & controls
   - 7.3 Acceptance criteria
   - 7.4 Controls & actions (buttons)
8) Config (Settings) Tab
   - 8.1 Global settings
   - 8.2 Per‑indicator/strategy forms
   - 8.3 Dependency guardrails
   - 8.4 Acceptance criteria
   - 8.5 Controls & actions (buttons)
9) Signals Tab
   - 9.1 Columns
   - 9.2 Interactions
   - 9.3 Acceptance criteria
   - 9.4 Controls & actions (buttons)
10) Templates Tab
   - 10.1 Features (versioning, diff, import/export)
   - 10.2 Acceptance criteria
   - 10.3 Controls & actions (buttons)
11) Trade History Tab
   - 11.1 Table fields
   - 11.2 Filters & KPIs
   - 11.3 Acceptance criteria
   - 11.4 Controls & actions (buttons)
12) History/Analytics Tab
   - 12.1 Logs
   - 12.2 KPIs
   - 12.3 Acceptance criteria
   - 12.4 Controls & actions (buttons)
13) DDE Price Feed Tab
   - 13.1 Prereqs & environment
   - 13.2 Controls
   - 13.3 Subscriptions & live table
   - 13.4 Data contract (UI‑level)
   - 13.5 Retry/backoff policy
   - 13.6 Troubleshooting
   - 13.7 Testing hooks & matrix
   - 13.8 Acceptance criteria
   - 13.9 Controls & actions (buttons)
14) Economic Calendar Tab
   - 14.1 Features
   - 14.2 Acceptance criteria
   - 14.3 Controls & actions (buttons)
15) System Status Tab
   - 15.1 Contents (health, incidents, resources)
   - 15.2 Operator tools
   - 15.3 Acceptance criteria
   - 15.4 Controls & actions (buttons)
16) Reentry Matrix Tab
   - 16.1 Dimensions (S/T/O/C, generation)
   - 16.2 Cell data model
   - 16.3 Performance panel
   - 16.4 Operations & versioning
   - 16.5 Visualization (heatmap)
   - 16.6 Validation & guardrails
   - 16.7 Persistence
   - 16.8 Acceptance criteria
   - 16.9 Controls & actions (buttons)
17) Re-Entry Parameter Sets Tab
   - 17.1 Required keys
   - 17.2 Risk & sizing governance
   - 17.3 Editor sections
   - 17.4 Parameter typing & controls
   - 17.5 Validation rules
   - 17.6 Bridge & storage
   - 17.7 Linkage to Matrix
   - 17.8 Acceptance criteria
   - 17.9 Controls & actions (buttons)
18) Alerts & Notification Policy
   - 18.1 Triggering
   - 18.2 Severity
   - 18.3 Lifecycle
   - 18.4 Operator controls
19) Theming & Accessibility
   - 19.1 Tokens
   - 19.2 Contrast & keyboard nav
   - 19.3 Motion/reduced motion
20) Event & State Taxonomy
   - 20.1 Event topics
   - 20.2 State keys
21) Testing & Rollout Plan
   - 21.1 Phase 1 – Foundations
   - 21.2 Phase 2 – Plugins & Validation
   - 21.3 Phase 2b – Data Operations
   - 21.4 Phase 3 – Probability & Policy
   - 21.5 Phase 4 – History & Analytics
   - 21.6 Acceptance criteria
22) Non‑Goals / Explicit Exclusions
23) Future Extensions (Non‑binding)
24) Equity & Risk Dashboard (Live)
   - 24.1 Data contract (events & fields)
   - 24.2 Panels
   - 24.3 Filters
   - 24.4 Metrics (formulas)
   - 24.5 Alerts
   - 24.6 Performance & acceptance criteria
   - 24.7 Export & share
   - 24.8 Data quality & edge cases
   - 24.9 Controls & actions (buttons)

---

## 7) Live Tab
### 7.1 Key panels
- Status cards: connectivity, latency, data-health, risk posture, open positions summary.
- Signal ticker: latest normalized signals with direction/strength/confidence (p, n when available).
- Quick actions: acknowledge alerts, pin signals, jump to related Config/History.

### 7.2 Filters & controls
- Symbol/timeframe filters; pause/resume auto-scroll; compact/detailed row density.

### 7.3 Acceptance criteria
- Live cards update ≤ 1s latency under expected load.
- Ticker deduplicates identical signals within TTL and shows ack state.
- All quick actions emit corresponding EventBus events and persist to History.

### 7.4 Controls & actions (buttons)
- **Acknowledge alert** — `alerts.acknowledge {{alert_id}}`.
- **Pin signal** — `signal.pin {{signal_id}}` (shows in Live).
- **Pause/Resume auto‑scroll** — `ui.ticker_autoscroll_toggle`.
- **Open in Config** — `ui.navigate {{target:"config", anchor}}`.
- **Copy trace id** — copies normalized trace_id.
- **Refresh snapshot** — `ui.refresh_live` (cooldown 3s).

---

## 8) Config (Settings) Tab
### 8.1 Global settings
- **Communications (bridge):** `COMM_MODE` (Auto / CSV / Socket), `ListenPort`, `CommPollSeconds`, `EnableCSVSignals`, `EnableDLLSignals`, `DebugComm` (default: off). Port-range validation and safe defaults documented.

### 8.2 Per‑indicator/strategy forms
- Auto-generated from param schemas with validation.

### 8.3 Dependency guardrails
- Prevent invalid combos; show actionable errors.

### 8.4 Acceptance criteria
- Save blocked on invalid; changes log to History.

### 8.5 Controls & actions (buttons)
- **Save**, **Revert**, **Validate now**, **Load defaults**.
- **Import JSON**, **Export JSON**, **Copy deep‑link**.
- **Reconnect Socket** (COMM_MODE=Socket), **Test Bridge** (round‑trip & error count).

---

## 9) Signals Tab
### 9.1 Columns
- Time, symbol, kind, direction, strength, confidence, p, n, horizon, tags, source.
- **Identifiers:** `hybrid_id`, `cal8`, `cal5`, and Hybrid components `GEN/SIG/DUR/OUT/PROX/SYMBOL`.
- **Provenance:** `file_seq`, `checksum`, adapter mode, last revision id.

### 9.2 Interactions
- Filters, click-through to Matrix via `hybrid_id`, and to Calendar for event rows.

### 9.3 Acceptance criteria
- Smooth paging; exports include visible identifier fields.

### 9.4 Controls & actions (buttons)
- **Save filter preset**, **Clear filters**, **Export**, **Open in Matrix**, **Open in Calendar**, **Pin to Live**, **Column picker**.

---

## 10) Templates Tab
### 10.1 Features (versioning, diff, import/export)
### 10.2 Acceptance criteria
### 10.3 Controls & actions (buttons)
- **Save template**, **Save as…**, **Load**, **Diff vs current**, **Export**, **Import**, **Rollback**.

---

## 11) Trade History Tab
### 11.1 Table fields
- Standard fields + identifiers (`hybrid_id`, `cal8`, `cal5`, `parameter_set_id`).

### 11.2 Filters & KPIs
- Win rate, avg R, expectancy; re‑entry ledger (O → R1 → R2) in drawer.

### 11.3 Acceptance criteria
- Exports match filters; totals reconcile with statements.

### 11.4 Controls & actions (buttons)
- **Export**, **Save/Clear filter preset**, **Open in Equity & Risk**, **Open re‑entry ledger**, **Copy trade**.

---

## 12) History/Analytics Tab
### 12.1 Logs
- Signals, alerts, config/template changes; calendar/matrix ingestion with `file_seq`/`checksum`, promotion/demotion reasons, sequence gaps.

### 12.2 KPIs
- Hit rate by source/kind, target time, confidence distribution.

### 12.3 Acceptance criteria
- Responsive on 100k+ rows.

### 12.4 Controls & actions (buttons)
- **Export logs**, **Add chart**, **Save chart preset**, **Clear filters**.

---

## 13) DDE Price Feed Tab
### 13.1 Prereqs & environment
### 13.2 Controls
### 13.3 Subscriptions & live table
### 13.4 Data contract (UI‑level)
### 13.5 Retry/backoff policy
### 13.6 Troubleshooting
### 13.7 Testing hooks & matrix
### 13.8 Acceptance criteria
### 13.9 Controls & actions (buttons)
- **Connect/Disconnect**, **Add/Remove symbol**, **Subscribe/Unsubscribe all**, **Retry now**, **Latency test**, **Export snapshot**.

---

## 14) Economic Calendar Tab
### 14.1 Features
- Active table columns: `symbol, cal8, cal5, signal_type, proximity, event_time_utc, state, priority_weight, file_seq, created_at_utc, checksum`.
- State chips: `SCHEDULED, ANTICIPATION, ACTIVE, COOLDOWN, EXPIRED`.
- Proximity badges: `IM, SH, LG, EX, CD` with live countdown.
- **Emergency controls:** **STOP Imports** (pause scheduler; mark rows `BLOCKED`) and **RESUME Imports**.
- **Integrity tiles:** cumulative **sequence‑gap** & **checksum‑failure** counts with drill‑down.

### 14.2 Acceptance criteria
- STOP/RESUME reflect within one poll; badges/tiles update without refresh; exports include visible cal8/cal5/priority.

### 14.3 Controls & actions (buttons)
- **Import CSV**, **Socket test**, **CSV integrity check**, **Refresh/Rescan**, **Export selection**, **Toggle live mode**, **STOP Imports**, **RESUME Imports**.

---

## 15) System Status Tab
### 15.1 Contents (health, incidents, resources)
- Health tiles: `database_connected`, `ea_bridge_connected`, `last_heartbeat`, `cpu_usage`, `memory_usage`, `win_rate`, `max_drawdown`, coverage %, fallback rate, p95/p99 latency, slippage vs expected, spread vs model, conflict rate, calendar revisions processed, circuit‑breaker triggers, **CSV integrity** counts.
- **Broker Clock Skew** badge; when |skew|>120s or offset stale>15m → **DEGRADED** (EA bridge set disconnected), decision emission disabled until **two consecutive** healthy checks.

### 15.2 Operator tools
- **Pause Decisions**, **Resume Decisions** (admin), **Flatten All**, **Cancel All Orders**, **Resync Broker Clock**, **Escalate/Page**.

### 15.3 Acceptance criteria
- In DEGRADED, decision-emitting controls disabled & labeled; alerts fire on threshold breaches.

### 15.4 Controls & actions (buttons)
- As above (admin‑gated) with confirmations where noted.

---

## 16) Reentry Matrix Tab
### 16.1–16.3 (Dimensions, Cell model, Performance)
### 16.4 Operations & versioning
- Includes **Manual Overrides**: scope, TTL, reason; auto‑revert; tag trades for separate P&L & audit.

### 16.5 Visualization (heatmap)
### 16.6 Validation & guardrails
### 16.7 Persistence
### 16.8 Acceptance criteria
### 16.9 Controls & actions (buttons)
- **Edit cell**, **Bulk copy**, **Reset slice**, **Save version**, **Compare versions**, **Rollback**, **Open decisions**, **Open re‑entry ledger**, **Export**, **New Override…**, **Revert Override**.

---

## 17) Re-Entry Parameter Sets Tab
### 17.1 Required keys
### 17.2 Risk & sizing governance
### 17.3 Editor sections
- Includes **Active Overrides (read‑only)** list affecting this set with TTL and link to Matrix.

### 17.4 Parameter typing & controls
### 17.5 Validation rules
### 17.6 Bridge & storage
### 17.7 Linkage to Matrix
### 17.8 Acceptance criteria
### 17.9 Controls & actions (buttons)
- **New set**, **Duplicate**, **Save**, **Export/Import JSON**, **Set active**, **Delete**, **Link to matrix**.

---

## 18) Alerts & Notification Policy
### 18.1 Triggering
- Probability/confidence thresholds; sample-size floors; risk posture gates; dedupe TTL.
- **Ops triggers:** coverage threshold, fallback spike, **Degraded mode (broker clock skew)**, **Emergency STOP (calendar)**, checksum/sequence failures.

### 18.2 Severity
### 18.3 Lifecycle
### 18.4 Operator controls
- **Acknowledge**/**Escalate (page)** actions available in toasts and Alerts panel.

---

## 24) Equity & Risk Dashboard (Live)
### 24.1 Data contract (events & fields)
- `trade.close`, `account.cash_adjustment`; equity/drawdown series.

### 24.2 Panels
- Equity curve, Drawdown curve, Outcome distribution, Risk cards, Recent closes.

### 24.3 Filters
- Date, symbol, strategy/tag, parameter_set_id, account, gross/net toggle, currency normalization, smoothing; compare A/B.

### 24.4 Metrics (formulas)
- Δ per trade, equity recursion, drawdown, max DD, time underwater, expectancy, profit factor, geometric growth, VaR(5%), risk of ruin proximity.

### 24.5 Alerts
- New max DD, VaR worsened, equity floor proximity, outsized single-trade loss.

### 24.6 Performance & acceptance criteria
- Update ≤ 1s after close; ≥ 50k trades interactive; KPIs reconcile with Trade History.

### 24.7 Export & share
- Export series/KPIs; snapshot PNG; deep‑links restore filters/overlays.

### 24.8 Data quality & edge cases
- Partial closes, duplicates/out‑of‑order, corrections, multi‑currency, deposits/withdrawals, session resets.

### 24.9 Controls & actions (buttons)
- **Toggle overlays**, **Save view preset**, **Export series**, **Snapshot**, **Compare mode**, **Net/Gross toggle**, **Currency normalize**.

# 0. Document Control

## 0.1 Title
Integrated Economic Calendar → Matrix → Re‑Entry System — Technical Specification (Hierarchical Indexed)

## 0.2 Purpose & Scope
Defines the architecture, identifiers, data contracts, and operational processes for integrating (A) the Economic Calendar subsystem, (B) the Multi‑Dimensional Matrix subsystem, and (C) the Re‑Entry subsystem, including Python/database components and MT4 (MQL4) bridges. Incorporates the latest fixes replacing prior inferior logic.

## 0.3 Audience
System architects, quant devs, Python engineers, MQL4 engineers, ops/SRE, QA.

## 0.4 Assumptions
- Trading execution occurs via MT4/MQL4 (no MQL5 language features).
- Calendar ingestion and decisioning run in Python/SQLite; MT4 communicates via CSV/IPC.
- All timestamps handled in UTC; UI converts for display.

## 0.5 Definitions
- **CAL5**: Legacy 5‑digit calendar strategy ID (country+impact).
- **CAL8**: Extended 8‑symbol identifier (Region|Country|Impact|EventType|RevisionFlag|Version) per §3.2.
- **Hybrid ID**: Composite key joining calendar and matrix context per §3.4.
- **PairEffect**: Per‑symbol effect model (bias/spread/cooldown) per §7.4.

---

# 1. System Overview

## 1.

## 1.x System Philosophy (Non-Implementation)

This system fuses **proactive** (calendar-driven anticipation) and **reactive** (outcome-driven re-entry) trading into a single, auditable pipeline. Signals are generated from a **calendar→matrix** path before events and from a **post‑event outcome** path after releases. Both paths converge into the **Decision Layer**, which emits decisions under strict contracts (atomic files, checksums, and health metrics). All timing and storage are **UTC-normalized**, with explicit handling for DST on acquisition schedules. Configuration determines aggressiveness and risk posture but does not change interface contracts.
1 Objectives
1) Fuse calendar awareness with outcome‑ and time‑aware re‑entries.
2) Standardize identifiers and data flows for reproducible decisions.
3) Enforce risk, exposure, and broker constraints.

## 1.2 System Components
- A) Economic Calendar Subsystem (§4)
- B) Multi‑Dimensional Matrix Subsystem (§5)
- C) Re‑Entry Subsystem (§6)
- D) Data & Storage Layer (§7)
- E) Risk & Portfolio Controls (§8)
- F) Integration & Communication Layer (§2)
- G) Monitoring, Testing, Governance (§13–§15)

## 1.3 High‑Level Data Flow
1) Calendar ingest → event 
#### Revisions Handling — Acceptance Test
- Verify same‑second reschedules are detected and merged without duplicate keys.
- Validate tolerant mapping handles vendor field renames (e.g., `act`→`actual_value`).
- Ensure matrix resolution preserves prior decisions unless new data exceeds confidence threshold.

normalization → CAL8/CAL5.
2) Real‑time proximity & state machine updates.
3) On trade‑close: compute matrix context (Outcome/Duration/Generation).
4) Build Hybrid ID; choose ParameterSet (with fallbacks & risk overlays).
5) Emit decision to MT4 via atomic CSV; MT4 executes.

---

# 2. Integration & Communication Layer

## 2.

### 2.y Communication Bridge Contracts (Interface-Level)

**Supported Transports:**
- **CSV (primary)** — atomic write + checksum; pull/poll semantics.
- **Socket (optional via PCL)** — push semantics with heartbeat/health.
- **Named Pipes (optional/future)** — MAY be enabled without changing decision schema.

**Decision CSV (contract reminder):**
- Required columns: `file_seq`, `ts_utc`, `symbol`, `side`, `size`, `price` (optional), `sl`, `tp`, `ttl`, `checksum`.
- Atomic write with temp‑rename; idempotency enforced by `file_seq` + hash.
- Health: adapter mode/state transitions recorded in `health_metrics.csv`.


## 2.x High-Level Architecture & Data Flow (Conceptual)

**Primary Flow:**  
Calendar Intake → Normalization → Matrix Resolution → Decision Layer → PCL Transport → Execution → Outcome Ingest → Re‑Entry Evaluation → Decision Layer

**Data Contracts:**  
- **Calendar/Matrix**: normalized event keys (CAL8), quality scores, debounce/min-gap rules.  
- **Decisions**: atomic CSV with `file_seq`, SHA-256, and idempotent write semantics.  
- **Health**: `health_metrics.csv` and `performance_metrics` tables for SLO tracking.

**Resilience:**  
CSV is **primary transport**; **socket** is optional via the Python Communication Layer (PCL) with automatic failover and stateful health reporting. Named pipes may be added as an optional future transport without changing decision contracts.
1 Inter‑Process Contracts
- **Transport**: CSV file drops on shared path; optional TCP/IPC later.
- **Atomicity**: Writers output `*.tmp`, include `file_seq`, `created_at_utc`, `checksum_sha256`, then rename to final path (§2.3).
- **Consumption Rule**: Readers process only strictly increasing `file_seq` with valid checksum.

## 2.2 CSV Artifacts
#### 2.2.4 `health_metrics.csv` (NEW)
Columns:
- `timestamp` (UTC ISO8601)
- `database_connected` (0/1)
- `ea_bridge_connected` (0/1)
- `last_heartbeat` (UTC ISO8601)
- `error_count` (int)
- `warning_count` (int)
- `cpu_usage` (float, %)
- `memory_usage` (float, MB)
- `win_rate` (float, %)
- `max_drawdown` (float, %)

Notes:
- Produced by the Python service, sourced from `system_status` and `
#### Coverage Alert Thresholds
- *Warn:* fallback_rate ≥ 5% for 5 consecutive minutes **or** conflict_rate ≥ 2% over last 100 decisions.
- *Page:* fallback_rate ≥ 15% for 3 consecutive minutes **or** p99_latency_ms > 2000 for 5 minutes.
- *Info:* socket_uptime_pct or csv_uptime_pct drops below 99.5% rolling 1h.

performance_metrics` tables.
- Atomic write: temp → checksum → rename.


- `active_calendar_signals.csv`: `symbol, cal8, cal5, signal_type, proximity, event_time_utc, state, priority_weight, file_seq, created_at_utc, checksum`
- `reentry_decisions.csv`: `hybrid_id, parameter_set_id, lots, sl_points, tp_points, entry_offset_points, comment, file_seq, created_at_utc, checksum`
- `trade_results.csv`: `file_seq, ts_utc, account_id, symbol, ticket, direction, lots, entry_price, close_price, profit_ccy, pips, open_time_utc, close_time_utc, sl_price, tp_price, magic_number, close_reason, signal_source, checksum`
- `health_metrics.csv`: rolling KPIs (§14.2)

## 2.3 Atomic Write Procedure
1) Serialize rows → temp file with `file_seq`.
2) Compute SHA‑256 checksum field; fsync.
3) Rename `*.tmp` → final; notify via file watcher (optional).

## 2.4 Time & Timezone
### 2.4.1 Time & Timezone — Broker Skew Rules (NEW)
**Purpose:** Ensure time alignment across UTC normalization, broker clock, and calendar triggers.

**Inputs**
- `utc_now` (system UTC time)
- `broker_time` (EA-reported time via bridge)
- `last_offset_update_ts` (UTC)
- `max_skew_seconds` = **120**
- `max_offset_age_seconds` = **900** (15 minutes)

**Rules**
1. **Offset Calculation:** `offset = broker_time - utc_now` (signed seconds).
2. **Skew Check:** If `abs(offset) > max_skew_seconds` → **DEGRADED**.
3. **Staleness Check:** If `utc_now - last_offset_update_ts > max_offset_age_seconds` → **DEGRADED**.
4. **Degraded Mode Behavior:**
   - Set `ea_bridge_connected=0` in `health_metrics.csv`.
   - **Do not** emit `reentry_decisions.csv`.
   - Re-attempt broker sync every **60s**; return to **NORMAL** only after two consecutive healthy checks.
5. **Audit:** Record transitions NORMAL↔DEGRADED in `error_log` with the measured skew.


#### 2.4 (UPDATED) Skew Handling
- **Max broker skew:** ±120 seconds vs UTC heartbeat.
- **Stale offset policy:** if offset older than **15 minutes**, mark `ea_bridge_connected=0`, pause emissions, raise `warning_count`.
- **Degraded mode:** if skew exceeds max or offset stale, do not emit new `reentry_decisions.csv`; retry sync every 60s.


- All times UTC in payloads. MT4 converts using live `broker_offset_minutes` provided by control file `broker_clock.csv` (updated hourly).

## 2.5 System‑Wide Relationship Matrix (Consolidated)

| Source Component | Target Component | Data Flow Type | Trigger | Source Doc |
|---|---|---|---|---|
| Calendar Normalizer | Calendar Events DB | SQL upsert (`calendar_events`) | New/revised event | §4.4, §7.2 |
| Calendar Events DB | Active Signal Builder | Event rows → Active set | Scheduler tick / proximity change | §4.5–§4.6 |
| Active Signal Builder | Active Calendar Signals CSV | CSV (`active_calendar_signals.csv`) | State/proximity change; revision | §2.2–§2.3, §4.3 |
| EA Trade Close Detector | Trade Results CSV | Append ACK row | Order close | §17.2, §9.201 |
| Trade Results CSV | Outcome/Duration Classifier | ETL ingest → O/D | New trade result row | §5.3–§5.4, §9.210 |
| Active Calendar Signals CSV | Signal Composer (Matrix) | CSV rows → CompositeSignal | On emission / tick | §3.6, §9.211 |
| Re‑Entry Ledger | Generation Selector | Ledger state (`O/R1/R2`) | Decision cycle | §6.5, §5.6 |
| HybridID Builder | Parameter Resolver | ID parts → lookup key | Post classification/composition | §3.4, §5.8 |
| Parameter Repository (central) | Parameter Resolver | ParameterSet JSON | On lookup | §7.3 |
| PairEffect Table | Overlay Engine | Buffers/cooldown multipliers | Pre‑decision overlay | §7.4, §6.4 |
| BrokerConstraints Repository | Overlay Engine | Lot/min‑stop/freeze/rounding | Pre‑decision overlay | §7.7, §6.4 |
| Risk Controllers (Exposure/DD/Streak) | Overlay Engine | Scalars / blocks | Risk state change | §8.1–§8.3 |
| Decision Emitter | Execution Engine (EA) | `reentry_decisions.csv` | New decision (`file_seq`↑) | §2.2–§2.3, §17.1 |
| Execution Engine (EA) | Trade Results CSV | `trade_results.csv` append | After open/modify/close | §17.2, §9.240 |
| Metrics Emitters | Metrics/Alerts | KPI rows, alert triggers | On events / thresholds | §14.1–§14.2 |
| Configuration/Change Mgmt | All Components | Hot‑reload configs / mappings | Publish/approve | §15.1 |
| Lifecycle/Restart Manager | All Components | State hydration | Startup/restart | §9.300, §4.9 |

## 2.6 Python Communication Layer (PCL)
**Purpose.** Provide a unified, pluggable transport between Python services (§4–§8) and the MT4 Execution Engine (§16.4), with automatic failover and health reporting.

**Design.**
- **Adapters:** `CSVAdapter` (file‑based) and `SocketAdapter` (DLL/port 5555/9999). Both expose the same interface:
  - `emit_decision(decision_row)`, `emit_metrics(metric_rows)`, `append_trade_result(row)`
  - `watch_signals(callback)`, `watch_health(callback)`
- **Router:** `CommRouter` selects the active adapter with policy: Socket preferred when healthy → otherwise CSV. Policy is stateful, uses heartbeats & error counters (§2.8).
- **Integrity Guard:** Validates `file_seq` monotonicity, SHA‑256 checksum (CSV), and JSON schema (socket) before delivery.

## 2.7 Transport Adapters — Contracts
**CSVAdapter (Production Default).**
- **Paths:** `<MT4_DATA_FOLDER>/eafix/` by default; alias to spec filenames: 
  - `trading_signals.csv` ⇄ **`reentry_decisions.csv`**
  - `trade_responses.csv` ⇄ **`trade_results.csv`**
  - `system_status.csv` ⇄ **`health_metrics.csv`**
- **Polling/Detection:** EA detects updates on ≤5s timer (§17.1, SLA table). Writer uses atomic temp‑rename (§2.3). 
- **Semantics:** Writer appends rows with `file_seq`, `ts_utc`, `checksum`. Reader validates then processes.

**SocketAdapter (Optional / Low‑Latency).**
- **Server:** MT4 starts DLL socket server; newline‑terminated UTF‑8 JSON messages (≤4096 bytes). Single Python client allowed.
- **Client:** Python `MT4Bridge` maintains connection, send/receive threads, and message handlers (signals, status, trade updates).
- **Health:** Heartbeats every 30s from EA; adapter demotes on missed beacons or send/recv errors.

## 2.8 Failover & Health Policy
- **Primary:** Socket when `status==CONNECTED` and last 3 cycles error‑free; otherwise CSV.
- **Demotion Triggers:** socket connect/refused, heartbeat missed, JSON parse error, queue overflow.
- **Promotion Triggers:** stable socket for ≥60s with heartbeats.
- **Metrics:** Emit adapter state, last transition reason, decision latency deltas (§14.1, §9.401).

## 2.9 Configuration Flags (EA & Python)
- EA: `EnableCSVSignals=true/false`, `EnableDLLSignals=true/false`, `ListenPort=5555`, `CommPollSeconds=5` (min 1s), `DebugComm=false` (§17.1–§17.4).
- Python: `COMM_MODE=auto|csv|socket`, `CSV_DIR=<path>`, `SOCKET_HOST=localhost`, `SOCKET_PORT=5555`, `CHECKSUM=sha256`, `SEQ_ENFORCE=true`.

## 2.10 Troubleshooting Hooks
- Ship `simple_socket_test.py` and CSV integrity checker. Health panel surfaces: seq gaps, checksum failures, socket status, last heartbeat (§14.3).

---

# 3. Identifier Systems (Standardization)
 Identifier Systems (Standardization)

## 3.1 Rationale
Earlier coarse IDs conflated distinct event types. The expanded scheme preserves learning granularity and backward compatibility.

## 3.2 CAL8 (Extended Calendar Identifier)
Format: `R1C2I1E2V1F1` → 8 symbols encoded as fields:
- **R (1)**: Region code (e.g., A=Americas, E=Europe, P=APAC).
- **C (2)**: Country/currency (e.g., US, EU, GB, JP).
- **I (1)**: Impact (H=High, M=Med).
- **E (2)**: Event type (e.g., NF=Nonfarm payrolls, CP=CPI, RD=Rate decision, PM=PMI).
- **V (1)**: Version/ingest schema rev.
- **F (1)**: Revision flag sequence (0=no revision, 1..9 revision order).

**Examples**: `AUS H NF 1 0` → `AUSHNF10`; `EGB MCP 1 0` → `EGBMCP10` (space added for readability; stored as 8 chars).

## 3.3 CAL5 (Legacy Alias)
- Maintain CAL5 for continuity; store both CAL8 and CAL5 on all records.

## 3.4 Hybrid ID (Primary Key)
Format: `[CAL8|00000000]-[GEN]-[SIG]-[DUR]-[OUT]-[PROX]-[SYMBOL]`
- **GEN**: `O|R1|R2`
- **SIG**: e.g., `ECO_HIGH_USD`, `ANTICIPATION_1HR_EUR`, `VOLATILITY_SPIKE`, `ALL_INDICATORS`.
- **DUR**: `FL|QK|MD|LG|EX|NA` (NA for durationless signals).
- **OUT**: `O1..O6` (Full SL → Beyond TP, §5.3).
- **PROX**: `IM|SH|LG|EX|CD` (Immediate/Short/Long/Extended/Cooldown).

**Example**: `AUSHNF10-O-ECO_HIGH_USD-FL-O4-IM-EURUSD`.

## 3.5 Signal Taxonomy (Families)
- Calendar: `ECO_HIGH_[CCY]`, `ECO_MED_[CCY]`
- Anticipation: `ANTICIPATION_8HR_[CCY]`, `ANTICIPATION_1HR_[CCY]` (durationless allowed)
- Sessions: `TOKYO_OPEN`, `LONDON_OPEN`, `NY_OPEN`, `NY_LUNCH`, `NY_CLOSE`
- Non‑calendar: `VOLATILITY_SPIKE`, `CORRELATION_BREAK`
- Fallback/technical bundle: `ALL_INDICATORS`

## 3.6 Priority & Composition
- **Scoring** (preferred over rigid suppression): Assign weights (e.g., High=1.0, Med=0.8, Ant1H=0.6, Ant8H=0.4, Session=0.5, VolSpike=0.4, All=0.2). Combine non‑conflicting signals; block known conflicts by rule list.

---

# 4. Economic Calendar Subsystem

## 4.1 Responsibilities

#### Default Debounce / Min‑Gap by Event Family (Configurable)

| Event Family         | Debounce Window | Min Gap Before/After |
|----------------------|-----------------|----------------------|
| Rate Decision (RD)   | 15m             | 10m / 10m            |
| Non-Farm Payroll (NF)| 10m             | 5m / 5m              |
| CPI (CP)             | 10m             | 5m / 5m              |
| GDP (GD)             | 8m              | 4m / 4m              |
| Other (OT)           | 5m              | 3m / 3m              |

> These are safe defaults; tune per broker/liquidity and archive outcomes.

- Ingest calendar feed(s); normalize events; assign CAL8/CAL5.
- Compute real‑time proximity buckets; manage event lifecycle states.
- Emit active signals per symbol with priority weights.

## 4.2 Inputs
- Primary calendar feed (e.g., ForexFactory or similar, mapped to schema).
- Holiday/session calendars (per market) for session‑type signals.

## 4.3 Outputs
- `active_calendar_signals.csv` (per §2.2) continuously updated.
- DB table `calendar_events` with state & proximity history.

## 4.4 Event Normalization & ID Assignment
- Map feed fields → (Region, Country, Impact, EventType); set `V=1` initially.
- Initialize `F` (revision flag) = `0`; increment on official revisions/reschedules; propagate to CAL8.

## 4.5 Proximity Model (Event‑Type Aware)
- Buckets are **event‑type configurable**:
  - CPI: IM=0–20m, SH=21–90m, LG=91–300m, EX=>300m
  - NFP: IM=0–30m, SH=31–120m, LG=121–360m, EX=>360m
  - PMI: IM=0–10m, SH=11–45m, LG=46–180m, EX=>180m
- Cooldown `CD`: 30–60m post `ACTIVE` per event‑type rule.

## 4.6 Lifecycle States
`SCHEDULED → ANTICIPATION_8HR → ANTICIPATION_1HR → ACTIVE (±window) → COOLDOWN → EXPIRED`.
- State transitions recompute `proximity`; emit new rows when state changes.

## 4.7 Holiday & Session Logic
- Maintain session calendar with DST/holiday rules.
- Suppress session signals (`*_OPEN`, `*_CLOSE`) if market closed or emit with reduced weight.

## 4.8 Data Quality & Revisions
- Validate ingest (schema, uniqueness, monotonicity).
- On revision: bump `F`, re‑emit proximity/state; invalidate stale projections.

## 4.9 Performance & Resilience
- Restart hydration: rebuild active set from DB (states ∈ {ANT_8H, ANT_1H, ACTIVE, COOLDOWN}).

## 4.10 Component Relationship Matrix

| Source Component | Target Component | Data Flow Type | Trigger | Source Doc |
|---|---|---|---|---|
| Primary Calendar Feed | Calendar Normalizer | Raw rows → Normalized EventModel | Scheduled import / manual refresh | §4.4 |
| Holiday/Session Calendar | Session Signal Generator | Session/Holiday tables | Daily build / DST/holiday change | §4.7 |
| Calendar Normalizer | Calendar Events DB | SQL upsert (`calendar_events`) | New or revised event | §4.4, §7.2 |
| Calendar Events DB | Active Signal Builder | Event rows → Active set | Scheduler tick / proximity change | §4.5, §4.6 |
| Active Signal Builder | Active Calendar Signals CSV | CSV (`active_calendar_signals.csv`) | State/proximity change; revision | §2.2–§2.3, §4.3 |
| Revision Listener | Calendar Events DB | CAL8 `F` bump; state/prox recompute | Upstream revision/reschedule | §4.8, §3.2 |
| Active Signal Builder | Metrics/Alerts | Counters; `calendar_revisions_processed` | On emission | §14.1–§14.2 |

## 4.11 Automatic Download & Transformation (Detailed)
#### 4.11 (UPDATED) Calendar Intake & Transformation — Implementation Details
- **Acquisition Scheduler:Every Sunday 12:00 in America/Chicago (CST/CDT), or 17:00/18:00 UTC depending on DST; retry hourly up to 24h.
- **File detection patterns:** `ff_calendar*.csv`, `*calendar*thisweek*.csv`
- **Validation:** “fresh today”, size > 1KB, schema check.
- **Filters:Include High/Medium by default; currency allow/deny list configurable (e.g., default deny CHF=true).
- **Anticipation events:** generate **5** anticipation rows per base event at **1h, 2h, 4h, 8h, 12h** before.
- **Equity events:** inject **Tokyo/London/New York** opens.
- **ID scheme:** **5-digit RCI** (Region-Country-Impact) for StrategyID.
- **Ordering & conflicts:** unified chronological sort with “offset minutes” and stable priority merge (ANTICIPATION < ORIGINAL < EQUITY_OPEN on equal timestamps).
- **Output columns:**  
  `Date, Time, Event Name, Country, Currency, Impact, Event Type, Strategy ID, Hours Before, Priority, Offset Minutes`



- **Discovery**: The importer discovers the most recent download using prioritized patterns (e.g., `*ff*calendar*.csv`, `*economic*calendar*.csv`) in the configured downloads path; newest by mtime wins. If none found, it yields an empty run and emits a health metric.
- **Parsing**: Uses a tolerant CSV reader with **flexible column mapping** (Title/Event/Name; Country/Currency; Date/Day; Time/Hour; Impact/Importance). Rows with missing required fields are skipped. Non‑strict parsers handle different vendor layouts.
- **Quality scoring**: Each parsed row receives a **quality score (0–100)**; rows under threshold are dropped. High/Medium impact rows are retained; Low impact ignored by default.
- **Normalization**: Country/currency are standardized; impact normalized to `High|Medium`. Canonical fields are derived for downstream CAL8 assignment. Event timestamps remain in UTC.
- **Anticipation generation**: For eligible families (e.g., high‑impact releases), anticipation events are generated using configured hours (default 1,2,4,8,12) and appended to the event set.
- **Trigger time computation**: For each original/anticipation event, the engine computes trigger times with event‑type offsets; results are sorted chronologically.

## 4.12 Import Scheduler, Emergency Controls & Watchers

- **Scheduler**: Cron‑style **AsyncIO** scheduler executes imports on `import_day`/`import_hour`; manual rest endpoints (or CLI flag) support ad‑hoc runs.
- **Emergency stop / resume**: Emergency **STOP** pauses jobs **and** marks current/future events `BLOCKED`; **RESUME** unblocks and restarts the schedule. State changes rebroadcast to downstream listeners.
- **File watchers**: Optional watchdog observes incoming paths (e.g., `signals_in/`) and posts work **back to the event loop** safely; debounce rules prevent repeated triggers.

## 4.13 SQLite Persistence & Idempotency (Calendar Domain)

- **Schema**: `calendar_events(event_id PK, cal8, cal5, title, ccy, impact, event_time_utc, state, proximity, revision_seq, quality_score, blocked)` with **UNIQUE** composite key across canonical fields to prevent duplicates.
- **UPSERT**: Imports use transactional **UPSERT** to update rows in place (e.g., state, revision, blocked) while preserving identity; revision bumps increment `revision_seq` and propagate to CAL8 `F`.
- **Indexes**: Covering indexes on `(state, event_time_utc)` and `(ccy, impact)` for active‑set scans.
- **Hydration**: On restart, rebuild the active set for states `{ANT_8H, ANT_1H, ACTIVE, COOLDOWN}` and recompute proximity from `now_utc`.

## 4.14 Minimum‑Gap & Debounce Policies

- **Minimum gap**: EventProcessor enforces a per‑family **minimum gap** (minutes) between triggers to avoid clustered emissions. Lower‑priority duplicates are suppressed or time‑shifted.
- **Debounce**: Emissions of identical `(symbol, cal8, signal_type, state)` within the debounce window are coalesced.

## 4.15 Signal Export/Import Integration

- **Export**: Active signals and decisions are exported with **microsecond + UUID** file naming to avoid collisions when configured for socket/CSV hybrids.
- **Import**: Optional **import inbox** allows manual or third‑party calendar CSV drops to be auto‑parsed using the discovery pipeline. Invalid files are quarantined with an error code.

## 4.16 Configuration Model

- **Config surface**: `database_path`, `signals_export_path`, `signals_import_path`, `static_dir`, `import_day`, `import_hour`, `minimum_gap_minutes`, plus environment variable overrides.
- **Defaults**: Sensible defaults are generated on first run; required folders are created as needed.

## 4.17 Web Dashboard & Telemetry Hooks

- **JSON & WebSocket** endpoints broadcast imports, state changes, and metrics to any local dashboard clients. When a static directory exists, a lightweight status page is mounted; otherwise the API runs headless.
- **Metrics**: Calendar‑specific counters (imports run, revisions processed, rows parsed/dropped by reason, active‑set size) stream to §14 and are mirrored to `health_metrics.csv`.

---

# 5. Multi‑Dimensional Matrix Subsystem

## 5.1 Dimensions
- **SignalType** (§3.5), **Outcome**, **Duration**, **Proximity**, **Generation**.

## 5.2 SignalType Governance
- Registry defines for each signal: `durationless`, `proximity_sensitive`, `priority_weight`, conflict rules.

## 5.3 Outcome Buckets (Deterministic)
- Compute realized **RR** (PnL/initial risk). Map:
  - O1: ≤ −1.0 RR (Full SL or worse)
  - O2: −1.0 < RR ≤ −0.25
  - O3: −0.25 < RR ≤ +0.25 (BE zone)
  - O4: +0.25 < RR ≤ +1.0
  - O5: +1.0 < RR ≤ +2.0 (TP)
  - O6: > +2.0 (Beyond TP)

## 5.4 Duration Categories
- `FL, QK, MD, LG, EX` by elapsed time thresholds; allow `NA` for durationless signals.

## 5.5 Proximity Categories
- `IM, SH, LG, EX, CD` from §4.5; pulled live from calendar engine.

## 5.6 Generation Limits
- `O` (original), `R1`, `R2`; enforced by **Re‑Entry Ledger** (§6.5).

## 5.7 Matrix Population Strategy
- **Lazy materialization**: create mapping row on first encounter of a Hybrid ID, seeded from family template.
- Nightly backfill for popular combos.

## 5.8 Parameter Resolution (with Fallback Tiers)
Order of attempts:
1) Exact Hybrid ID.
2) Drop `DUR` (if durationless or flagged optional).
3) Drop `PROX`.
4) Replace `SIG` with `ALL_INDICATORS`.
5) **Safe Default** per family (conservative template).
- Emit coverage alert on any fallback tier > 0.

## 5.9 Audit & Versioning
- `mapping_audit` append‑only: old/new ParameterSetID, trigger, actor, stats snapshot, risk overlay diffs.

## 5.10 Component Relationship Matrix

| Source Component | Target Component | Data Flow Type | Trigger | Source Doc |
|---|---|---|---|---|
| Trade Close Ingest (EA → PY) | Outcome/Duration Classifier | TradeResult → O/D classification | Trade close ACK | §9.201, §5.3–§5.4 |
| Active Calendar Signals CSV | Signal Composer | CSV rows → CompositeSignal | On emission / tick | §3.6, §9.211 |
| Re‑Entry Ledger | Generation Selector | Ledger state (`O/R1/R2`) | Decision cycle | §6.5, §5.6 |
| HybridID Builder | Parameter Resolver | ID parts → lookup key | Post classification/composition | §3.4, §5.8 |
| Parameter Repository | Parameter Resolver | ParameterSet JSON | On lookup | §7.3, §5.8 |
| PairEffect Table | Overlay Engine | PairEffect row (buffers, cooldown) | Pre‑decision overlay | §7.4, §6.4 |
| BrokerConstraints Repo | Overlay Engine | Constraint row (lot/min stop/freeze) | Pre‑decision overlay | §7.7, §6.4 |
| Risk Controls (DD/Streak/Exposure) | Overlay Engine | Risk scalars | Before emit | §8.1, §8.3 |
| Parameter Resolver/Overlay | Decision Emitter | Final params | After overlays | §2.2, §9.224 |
| Fallback Detector | Mapping Audit | Append change record | Fallback tier>0 or manual change | §5.8–§5.9, §14.2 |

---

# 6. Re‑Entry Subsystem

## 6.
### 6.X Risk & Performance Mapping Defaults (NEW)
**Risk Score (0–100):**
- Base=50  
- WinRate Impact: `(WinRate - 50) * 0.6`  
- ProfitFactor Impact: `(ProfitFactor - 1) * 20`  
- Drawdown Penalty: `- DrawdownPercent * 2`  
- Recency Multiplier: last-7-days weight **×1.5**  
- Optional context adjustments (examples):  
  `consecutive_win_bonus = wins * 3`,  
  `volatility_penalty = vix_like_index * -0.5`,  
  `equity_close_penalty = (minutes_to_equity_close < 30 ? -10 : 0)`  
- Clamp to **[0,100]**.

**ParameterSet Bins (defaults):**
- `0–25` → **Conservative** (Set_1)
- `26–50` → **Moderate** (Set_2)
- `51–75` → **Aggressive** (Set_3)
- `76–100` → **Max** (Set_4)

1 Responsibilities
- On trade close, classify outcome/duration; compose Hybrid ID; select ParameterSet; overlay risk; emit decision.

## 6.2 Inputs
- Trade close data from MT4 (ticket group, prices, timestamps, initial SL/TP).
- Active signals (from calendar/session/vol engines).
- Risk overlays (drawdown, streaks, exposure caps).
- Broker constraints.

## 6.3 Outputs
- `reentry_decisions.csv` rows per §2.2.
- `trade_results` records with **frozen** parameter snapshots.

## 6.4 Parameter Overlay Policies
### 6.4 Parameter Overlay Precedence & Defaults (NEW)
**Goal:** Deterministic, layered parameter resolution.

**Precedence Order (top wins; stop on first concrete override):**
1. **PairEffect** (symbol-level overrides based on calendar influence)
2. **Broker Constraints** (min lot, step, stop distance, freeze levels)
3. **Risk Overlay** (from Risk Score & performance bins)
4. **Strategy/Matrix Defaults** (HybridID → ParameterSet)
5. **Global Fallbacks** (Tiered, see §6.8)

**Default Overlay Thresholds:**

| Overlay | Key | Default | Effect |
|---|---|---:|---|
| PairEffect | `exposure_cap_pct` | 3.0 | Max % balance exposed on symbol |
| Broker | `min_stop_points` | from EA | Enforce SL/TP ≥ broker min |
| Risk | `risk_floor_score` | 15 | Block entries below floor |
| Risk | `aggressive_cutover` | 75 | Switch to Set_3+ above |
| Strategy | `entry_offset_pts` | 0 | Add to pending orders |
| Global | `sl_tp_ratio_min` | 1.2 | Skip if TP/SL < 1.2 |

**Notes**
- When two overlays conflict at the same level, prefer the stricter risk stance (lower leverage, larger SL distance).
- All resolved parameters are **frozen on emit** (see schema §7.x below).


- Apply drawdown caps, streak dampeners, spread buffer, min stop buffers, portfolio exposure scaling, and broker rounding.

## 6.5 Re‑Entry Ledger (Generation Governance)
- Keyed by `PositionGroupID` (links partials/hedges/grids) to enforce max `R2` and prevent bypass.

## 6.6 Broker Constraints & Microstructure
- Enforce min lot step, min stop distance, freeze levels, max orders. Pre‑flight validation before OrderSend (in MQL4).
- Persist broker/platform constraints in a central repository per §7.7 and join them into the decision overlay at runtime.

## 6.7 Circuit Breakers
- Global kill‑switches: max daily loss, max consecutive losers, abnormal spread/slippage.

## 6.8 Component Relationship Matrix
### 6.8 Matrix Fallback Tiers (NEW)
**Problem:** Incomplete matches when looking up a ParameterSet by HybridID (e.g., missing duration or proximity bucket).

**Tiers**  
- **Tier-0 (Exact):** `HybridID = {CalendarID, ProximityBucket, DurationBucket, OutcomeClass}` → Use mapped `ParameterSetID`.
- **Tier-1 (Drop Duration):** `{CalendarID, ProximityBucket, OutcomeClass}` → If unique mapping exists, use it.
- **Tier-2 (Drop Proximity):** `{CalendarID, DurationBucket, OutcomeClass}` → If unique mapping exists, use it.
- **Tier-3 (Calendar Only):** `{CalendarID}` → Use Strategy Default Set.
- **Tier-4 (Global):** Use **Global Fallback Set** (safe conservative).

**Resolution Algorithm**
1. Attempt Tier-0; if **no** mapping or **multi-match**, escalate to Tier-1, then Tier-2, etc.
2. On each escalation, require a **unique** mapping; else continue.
3. Log the tier used into `mapping_audit` with `signal_id`, `resolved_tier`, and keys used.
4. If Tier-4 used, attach `comment="GLOBAL_FALLBACK"` to the emitted decision.

**Examples**
- **Case A:** Missing duration bucket → matched at **Tier-1** using `{CalendarID, Proximity, OutcomeClass}`.
- **Case B:** Sparse matrix for new event → falls back to **Tier-3** Strategy Default.
- **Case C:** Conflicting Tier-1 candidates → continue to **Tier-2**; if still ambiguous → Tier-3.



| Source Component | Target Component | Data Flow Type | Trigger | Source Doc |
|---|---|---|---|---|
| EA Trade Close Detector | Re‑Entry Subsystem | Trade close event | Order close | §9.201, §17.2 |
| Re‑Entry Subsystem | Re‑Entry Ledger | Generation update (`O→R1→R2`) | After decision result | §6.5, §9.260 |
| Re‑Entry Subsystem | Execution Engine (EA) | `reentry_decisions.csv` | Decision ready | §2.2–§2.3, §17.1 |
| Execution Engine (EA) | Re‑Entry Subsystem | `trade_results.csv` | After execute/close/modify | §17.2, §9.240 |
| Risk Calculator (DD/Streak/Exposure) | Re‑Entry Subsystem | Adjusted scalars/limits | Risk state change | §8.1–§8.3 |
| BrokerConstraints & PairEffect | Re‑Entry Subsystem | Overlay inputs | Pre‑decision | §7.7, §7.4 |
| Re‑Entry Subsystem | Metrics/Alerts | Fallback tier; coverage % | On decision | §14.1–§14.2 |

---

# 7. Data & Storage Layer

## 7.

### 7.

### 7.z Signal Validation Policy (Pre‑Execution Gates)

All incoming signals MUST pass these gates before emission:
- **Symbol/Instrument Match** — instrument must be tradable and enabled.
- **Lot/Size Bounds** — within configured min/max and step increments.
- **Stop/TP Distance** — meets broker and strategy minimums.
- **Market Open/Session** — allowed session and not in restricted windows.
- **Risk Limits** — account-level drawdown and concentration limits.
- **Duplicate/Replay** — reject duplicate `file_seq` or stale TTL.

Failures are logged with a reason code; no partial emissions are permitted.


### 7.y Risk & Circuit-Breakers (Requirements-Level)

**Trigger Taxonomy (examples):**
- **Daily Drawdown**: equity drop exceeds configured % or currency amount.
- **Equity Floor Breach**: account equity below minimum threshold.
- **Consecutive Errors**: repeated adapter/bridge failures beyond tolerance.
- **Concentration Breach**: exposure per symbol/pair beyond limits.
- **Market State**: spread/volatility spikes beyond configured bounds.

**Required Actions:**
- **Pause New Decisions** (soft circuit-breaker).
- **Flatten/Close Open Positions** (hard breaker).
- **Cancel Open Orders** where applicable.
- **Escalate** via health metrics + alerting (page thresholds).

> These actions are configuration-driven and logged via `health_metrics.csv` and `system_status` tables.
x Signal Input Modes (Interface-Level, Source-Agnostic)

Accepted non-implementation signal sources (must conform to the Decision contract):
- **Calendar/Matrix** — anticipation and time-window entries.
- **Internal Indicators** — computed analytics from the indicator engine.
- **External Feeds** — CSV or socket-delivered signals from external systems.
- **Manual/Operator** — controlled inputs with the same schema and gating.
- **Time-Slot/Batch** — scheduled rebalances or routine health probes.

> All sources undergo the same **validation gates** and risk/circuit-breaker checks before emission.

### 7.2–7.7 Data Schemas (Calendar/Matrix/Params) (NEW)
All tables are **SQLite**. Text fields store UTC ISO8601 where applicable. Create indexes as noted.

#### 7.2 `calendar_events`
Columns:
- `id` INTEGER PK AUTOINCREMENT
- `cal8` TEXT NOT NULL UNIQUE
- `cal5` TEXT NOT NULL
- `event_time_utc` TEXT NOT NULL
- `country` TEXT NOT NULL
- `currency` TEXT NOT NULL
- `impact` TEXT CHECK(impact IN ('High','Medium')) NOT NULL
- `event_type` TEXT CHECK(event_type IN ('ORIGINAL','ANTICIPATION','EQUITY_OPEN')) NOT NULL
- `strategy_id_rci` TEXT NOT NULL  -- 5-digit RCI
- `hours_before` INTEGER DEFAULT 0  -- anticipation only
- `priority` INTEGER NOT NULL       -- ANT<ORIG<EQT ordering
- `offset_minutes` INTEGER DEFAULT 0
- `quality_score` REAL DEFAULT 1.0
Indexes:
- `idx_calendar_events_time` on (`event_time_utc`)
- `idx_calendar_events_country_impact` on (`country`,`impact`)

#### 7.3 `pair_effect`
Columns:
- `id` INTEGER PK
- `symbol` TEXT NOT NULL
- `cal8` TEXT NOT NULL
- `bias` TEXT CHECK(bias IN ('LONG','SHORT','NEUTRAL')) DEFAULT 'NEUTRAL'
- `exposure_cap_pct` REAL DEFAULT 3.0
- `note` TEXT
Unique:
- (`symbol`,`cal8`)
Indexes:
- `idx_pair_effect_symbol` on (`symbol`)

#### 7.4 `parameters` (versioned)
Columns:
- `id` INTEGER PK
- `parameter_set_id` TEXT NOT NULL
- `param_version` TEXT NOT NULL   -- semver "1.2.0"
- `created_at_utc` TEXT NOT NULL
- `order_type` TEXT CHECK(order_type IN('Market','Limit','Stop')) NOT NULL
- `lot_method` TEXT CHECK(lot_method IN('Fixed','RiskBased')) NOT NULL
- `lot_value` REAL NOT NULL
- `sl_points` INTEGER NOT NULL
- `tp_points` INTEGER NOT NULL
- `entry_offset_points` INTEGER DEFAULT 0
- `sl_tp_ratio_min` REAL DEFAULT 1.2
Unique:
- (`parameter_set_id`,`param_version`)
Indexes:
- `idx_parameters_set` on (`parameter_set_id`)

#### 7.5 `matrix_combinations`
Maps HybridID features to a ParameterSet **version**.
Columns:
- `id` INTEGER PK
- `calendar_id` TEXT NOT NULL   -- cal8 or cal5
- `proximity_bucket` TEXT       -- nullable for fallbacks
- `duration_bucket` TEXT        -- nullable for fallbacks
- `outcome_class` TEXT          -- nullable for fallbacks
- `parameter_set_id` TEXT NOT NULL
- `param_version` TEXT NOT NULL
- `active` INTEGER DEFAULT 1
Unique:
- (`calendar_id`,`proximity_bucket`,`duration_bucket`,`outcome_class`)
Indexes:
- `idx_matrix_calendar` on (`calendar_id`)

#### 7.6 `mapping_audit`
Columns:
- `id` INTEGER PK
- `timestamp_utc` TEXT NOT NULL
- `signal_id` TEXT NOT NULL
- `calendar_id` TEXT
- `proximity_bucket` TEXT
- `duration_bucket` TEXT
- `outcome_class` TEXT
- `resolved_tier` INTEGER NOT NULL  -- 0..4 (see §6.8)
- `parameter_set_id` TEXT
- `param_version` TEXT
- `comment` TEXT

#### 7.7 `trade_results` (augment if missing)
Add columns if not present:
- `stop_loss` REAL NULL
- `take_profit` REAL NULL
- `current_profit` REAL NULL

> **Freeze Rules:** On **emit**, copy the **exact** `parameter_set_id` + `param_version` used into the outbound CSV and any downstream persistence; never rewrite historical fills.

1 Topology
- **Per‑symbol** SQLite DBs: `EURUSD_matrix.db`, etc.
- **Central** `parameters.db` shared across symbols.

## 7.2 Core Tables (Per‑Symbol DB)
- `matrix_map(hybrid_id PK, cal8, cal5, gen, sig, dur, out, prox, symbol, parameter_set_id, active, assigned_at, assigned_by, notes)`
- `trade_results(exec_id PK, hybrid_id, parameter_set_id, param_version, params_frozen_json, open_time_utc, close_time_utc, prices..., outcome_bucket, rr, pips, duration_cat)`
- `calendar_events(event_id PK, cal8, cal5, title, ccy, impact, event_time_utc, state, proximity, revision_seq)`
- `metrics(ts_utc, key, value)`

## 7.3 Parameter Repository (Central DB)
- `parameter_sets(parameter_set_id PK, category, risk_level, version, json_config, created_at, perf_score, usage_count)`

## 7.4 PairEffect Model (Per‑Symbol)
- Table `pair_effects(symbol PK, direction_bias, expected_spread_x, cooldown_minutes, lot_multiplier)`; joined at decision time.

## 7.5 Indexing & Performance
- Composite indexes: (`sig`,`prox`), (`out`,`dur`), (`parameter_set_id`).
- Sub‑ms lookups targeted under normal load.

## 7.6 Backup & Recovery
- Daily incremental + weekly full; automated integrity checks; export scripts for DR.

---

## 7.7 Broker Constraints Repository
- **Purpose:** Central, authoritative source of broker/platform microstructure limits used across all symbols.
- **Scope:** Values may be global per account or symbol‑specific overrides.
- **Schema (central DB):**
  - `broker_id` (PK), `account_id` (nullable), `symbol` (nullable for global rows)
  - `min_lot`, `lot_step`, `max_lot`
  - `min_stop_points`, `freeze_level_points`
  - `max_orders_total`, `max_orders_symbol`
  - `slippage_limit_points`, `execution_mode` (e.g., MARKET/INSTANT)
  - `last_checked_utc`, `source` (auto‑probe/manual), `notes`
- **Indexes:** (`broker_id`,`symbol`), (`account_id`,`symbol`).
- **Usage:** Joined by `broker_id/account_id/symbol` during parameter overlay (§6.4) and pre‑flight checks (§6.6). Values clamp/round lots and distances before OrderSend.

## 7.8 Component Relationship Matrix

| Source Component | Target Component | Data Flow Type | Trigger | Source Doc |
|---|---|---|---|---|
| All Compute Services | Per‑Symbol DBs | SQL upserts/queries | Persist/read events/decisions/results | §7.2 |
| Parameter Authoring Tool | Parameter Repository (central) | ParameterSet create/update | Publish/approve | §7.3, §15.1 |
| Backup Scheduler | Storage/WAL | Snapshots & integrity checks | Daily (inc) / Weekly (full) | §7.6 |
| Metrics Emitters | Metrics Table | KPI rows | Per tick / on events | §14.1 |
| Calendar Ingest | Calendar Events Table | Upsert | Import/revision | §4.4, §4.8 |
| EA (via CSV ETL) | Trade Results Table | Appends → ETL | Order updates | §17.2, §9.240 |
| Audit Writers | Mapping Audit | Append-only diffs | On mapping change | §5.9, §15.1 |

# 8. Risk & Portfolio Controls

## 8.

## 8.x Re‑Entry Logic Model (Domain Rules)

**Outcome Classification (illustrative six-bucket model):**
- **R** — Reversal beyond tolerance
- **ML** — Minor Loss
- **B** — Baseline / Neutral
- **MG** — Minor Gain
- **G** — Gain (Meets target)
- **X** — Exceptional / Outlier

**Action Schema (per bucket):**
- `action_type` *(hold|reduce|add|exit|reenter)*
- `size_multiplier` *(real, e.g., 0.5, 1.0, 1.5)*
- `delay` *(duration, e.g., 30s, 5m)*
- `confidence_adjustment` *(−1.0..+1.0)*
- `validity_window` *(duration)*

**Profiles:** `Conservative`, `Balanced`, `Aggressive` — profiles select per-bucket parameters only; interface contracts remain unchanged.
1 Exposure Caps
- Caps by `base_ccy` and `quote_ccy`; block/scale new entries when breached.

## 8.2 Spread/Latency Modeling
- `expected_spread_x` and `min_stop_buffer_points` per signal family & proximity.

## 8.3 Drawdown & Streak Policies
- Rolling 4h/12h drawdown dampening; consecutive‑loss throttle.

## 8.4 Component Relationship Matrix

| Source Component | Target Component | Data Flow Type | Trigger | Source Doc |
|---|---|---|---|---|
| Decision Engine (Matrix/Re‑Entry) | Exposure Controller | Position intents | Before emit | §8.1, §9.222 |
| Exposure Controller | Decision Engine | Size scaling / blocks | Caps breached/cleared | §8.1 |
| Spread/Latency Model | Decision Engine & EA | `expected_spread_x`, `min_stop_buffer_points` | Proximity/session change | §8.2 |
| Circuit Breakers | Execution Engine (EA) | Trip/Reset signals | Threshold breaches | §6.7, §16.4 |
| Drawdown/Streak Monitor | Decision Engine | Risk dampeners | Rolling window updates | §8.3 |
| Metrics/Alerting | Ops/SRE | Breach notifications | On threshold | §14.2 |

---

# 9. End‑to‑End Operational Flows

**Actors:** `PY` (Python services), `EA` (MT4 Execution Engine), `DB` (SQLite stores), `BR` (CSV Bridge), `FS` (Filesystem)  
**Transports:** CSV‑only per §2.1–§2.3 (atomic write: tmp→fsync→rename, `file_seq`, `checksum`, UTC)  
**Identifiers:** `CAL8`/`CAL5` (§3.2–§3.3), `HybridID` (§3.4)  
**Dimensions:** Outcome (§5.3), Duration (§5.4), Proximity (§5.5), Generation (§5.6)  
**Risk/Constraints:** PairEffect (§7.4), BrokerConstraints (§7.7), Exposure Caps (§8.1), Circuit Breakers (§6.7)  
**MT4 Contracts:** §16.4 (Execution Engine), §17 (Read/Write/Error)

---

## 9.100 — Event Lifecycle Flow (Calendar → Active Signals)

#### Acceptance Criteria — Calendar Intake
- *Freshness:* new weekly pull available ≤ 24h after vendor publish.
- *Completeness:* ≥ 95% of expected rows for High/Medium events for G7; gaps flagged.
- *Quality Score:* ≥ 0.90 average after normalization (field coverage + type validity).
- *Idempotency:* re‑running import with identical source does not change DB row hashes.
- *Tolerance:* vendor field rename or same‑second reschedule does not break pipeline.

#### Acceptance Criteria — PCL Failover
- *Detection:* transport failure detected in ≤ 3s.
- *Switch:* adapter switches to alternate transport in ≤ 2s.
- *Recovery:* primary transport retried with exponential back‑off (≤ 60s max interval).
- *Audit:* state transitions recorded with reason codes in `health_metrics.csv`.


**Pre‑Normalization (Auto‑Download & Transform)**
- **9.100A (PY/FS)** **Discover** the latest vendor CSV in the configured downloads path using prioritized glob patterns; select newest by mtime.
- **9.100B (PY)** **Parse** with flexible column mapping; compute **quality score** per row and discard sub‑threshold entries; standardize country/impact.
- **9.100C (PY)** **Generate anticipation** events for eligible families using configured hours (default 1,2,4,8,12); compute trigger times and sort.
- **9.100D (PY/DB)** **UPSERT** into `calendar_events` with unique keys; update `revision_seq`/`blocked` as needed; commit.
- **9.100E (PY)** **Minimum‑gap/debounce** pass to suppress clustered duplicates; proceed to active‑set calculation.

- **9.101 (PY/FS)** Read normalized calendar feed; verify SHA‑256 against sidecar. If unchanged, **GOTO 9.110**. (IDs: §3.2–§3.3)
- **9.102 (PY/DB)** For each event, compute `CAL8` and keep `CAL5` alias; upsert into `calendar_events` (DB) within a transaction (§7.2).
- **9.103 (PY)** Create anticipation entries (`ANTICIPATION_8HR`, `ANTICIPATION_1HR`) with configured, event‑type proximity thresholds (§4.5) and set `state=SCHEDULED` (§4.6).
- **9.104 (PY)** Merge session signals (TOKYO/LONDON/NY opens, lunch, close) with holiday/DST rules (§4.7). Assign `priority_weight` (§3.6).
- **9.105 (PY/DB)** Commit all events with initial `state`/`proximity` and revision flags. Ensure restart hydration markers saved (§4.9).
- **9.106 (PY)** Build **active set** for `[now−X, now+Y]` using event‑type proximity; map `PROX ∈ {IM, SH, LG, EX}` or `CD` for cooldown (§4.5).
- **9.107 (PY/FS)** Emit `active_calendar_signals.csv` atomically (§2.2–§2.3) with `file_seq`, `checksum`, UTC timestamps (§2.4).
- **9.108 (PY)** Debounce duplicates by `(symbol, cal8, signal_type, state)`; suppress lower‑weight duplicates (§3.6).
- **9.109 (PY/DB)** Store last emitted `file_seq` watermark for restart hydration (§4.9).
- **9.110** **END** (await scheduler tick or revision event).

### Revisions & Reschedules
- **9.121 (PY/DB)** On upstream revision, increment CAL8 revision flag `F`; recompute `state/proximity`; mark prior emissions stale (§4.8).
- **9.122 (PY/FS)** Re‑emit `active_calendar_signals.csv` with next `file_seq`; increment `calendar_revisions_processed` (§14.1).

---

## 9.200 — Trade‑Close Decision Flow (Close → Decision → Execution)

- **9.201 (EA)** Detect trade **close**; capture open/close UTC, prices, initial SL/TP, lots, symbol (§17.2). Append ACK to `trade_results.csv` (atomic, append, UTC) (§2.2, §17.2).
- **9.210 (PY/DB)** Classify **Outcome** O1..O6 by realized **RR** (§5.3). Compute **Duration** (`FL/QK/MD/LG/EX`) or `NA` for durationless families (§5.4, §3.5).
- **9.211 (PY)** Query **active signals** for symbol; compute composite top signal via priority weights (§3.6) and blocklist conflicts. Extract `SIG`, `CAL8|00000000`, live `PROX` (§5.5).
- **9.212 (PY)** Determine **Generation** from the Re‑Entry Ledger (`O→R1→R2`); if limit exceeded, mark terminal and **GOTO 9.280** (§5.6, §6.5).
- **9.213 (PY)** Compose **HybridID** = `[CAL8|00000000]-[GEN]-[SIG]-[DUR]-[OUT]-[PROX]-[SYMBOL]` (§3.4).
- **9.220 (PY/DB)** Resolve **ParameterSet** (tiers): exact → drop `DUR` → drop `PROX` → `SIG→ALL_INDICATORS` → Safe Default (§5.8; params in §7.3). Record `fallback_tier` and raise coverage alert if `tier>0` (§14.2).
- **9.222 (PY)** Apply overlays: PairEffect (§7.4), drawdown/streak dampeners, session caps, **portfolio exposure caps** (§8.1).
- **9.223 (PY)** Apply **BrokerConstraints** rounding/min‑stops/freeze levels (§7.7) to yield final `lots, sl_points, tp_points, entry_offset_points`.
- **9.224 (PY/FS)** Emit **decision** to `reentry_decisions.csv` atomically with `file_seq`, `checksum`, UTC and `parameter_set_id@version` (§2.2–§2.3).
- **9.230 (EA/FS)** Ingest decision per §17.1: verify monotonic `file_seq` + checksum; ignore stale/non‑matching symbols.
- **9.231 (EA)** Pre‑flight: re‑apply BrokerConstraints (§7.7) + PairEffect (§7.4); apply **circuit breakers** (§6.7) and **exposure caps** (§8.1). If blocked, log non‑execution and **GOTO 9.260**.
- **9.232 (EA)** Execute order(s) per decision; use SafeOrder wrappers and slippage guards (§16.4.4). Respect MT4 limits (MQL4‑only).
- **9.240 (EA/FS)** Append final execution to `trade_results.csv` (UTC, seq, checksum) with realized slippage and broker data (§17.2).
- **9.250 (PY/DB)** Persist to per‑symbol `trade_results` with **frozen** params and HybridID (§7.2, §7.3).
- **9.260 (PY)** Update Re‑Entry Ledger; if next gen ≤ R2, loop to **9.210**; else **GOTO 9.280** (§6.5).
- **9.280 (PY)** Mark chain **CLOSED**; emit metrics and end flow (§14.1).

---

## 9.300 — Restart Hydration Flow (Cold/Warm Start)

- **9.301 (PY/DB)** Read `calendar_events` where `state ∈ {ANT_8H, ANT_1H, ACTIVE, COOLDOWN}`; rebuild active signals; recompute `PROX` from `now_utc` (§4.9).
- **9.302 (PY/DB)** Restore **Re‑Entry Ledger** for open chains (§6.5).
- **9.303 (PY/FS)** Read last `file_seq` for `active_calendar_signals.csv` and `reentry_decisions.csv`; set monotonic baselines (§2.3).
- **9.304 (PY/FS)** Validate CSV integrity (seq gaps, checksum). If gaps, re‑emit latest state with next `file_seq` and raise alert (§14.2).
- **9.305 (PY/FS)** Emit fresh `active_calendar_signals.csv` (atomic) and start timers/jobs (§4.9).

---

## 9.400 — Real‑Time Updates & Conflict Arbitration

- **9.401 (PY)** On EA heartbeat, compute decision latency (decision write → EA ACK); append to metrics (§14.1).
- **9.402 (PY)** On calendar revision, run **9.121→9.122**; recompute composite signals; if hard conflict with a running chain, pause next gen and flag for review (§3.6, §4.8).
- **9.403 (PY)** On modeled **spread spike** for current `SIG/PROX`, reduce size and widen stops; escalate if persistent (§8.2).

---

## 9.500 — Health, Metrics & Coverage

- **9.501 (PY/DB)** Update `metrics` table and `health_metrics.csv` with coverage %, fallback rate, decision latency p95/p99, slippage delta, spread vs model, conflict rate, calendar revisions processed, circuit‑breaker triggers (§14.1, §14.3).
- **9.502 (PY)** Raise alerts on thresholds: excessive fallbacks, checksum failure, broker drift, heartbeat timeout, proximity rebuild failure (§14.2).

---

## 9.600 — Error Handling & Recovery (Scope §9)

- **9.601 (PY)** On decision write contention, backoff (250–1000ms, jitter, max 10). If exhausted, queue for retry and alert (§10).
- **9.602 (EA)** On order send/modify fatal error, follow retry taxonomy then emit `REJECT_TRADE`; if repeated, trip circuit breaker and annotate metrics (§6.7, §16.4.4).
- **9.603 (PY)** On mapping miss (fallback tier>0), log coverage violation and enqueue mapping task (§5.8, §14.2).

---

## 9.700 — Test Cues (Atomic, §9 Focus)

- **9.701** Inject calendar revision mid‑chain → expect recomputed `PROX` and no seq regression in emissions (§4.8, §2.3).
- **9.702** Simulate broker min stop increase → overlays clamp; EA pre‑flight rejects if violated (§7.7, §17.3).
- **9.703** Force fallback tier 3 → expect coverage alert + Safe Default usage (§5.8, §14.2).
- **9.704** Kill EA then restart → expect hydration 9.300 and heartbeat recovery (§4.9, §17).
- **9.705** Widen spread above model → reduced size/wider stops and metric flag (§8.2, §14.1).

---

## Appendix — Owner & SLA Matrix (Selected §9 Steps)

| Step — Action | Owner / SLA |
|---|---|
| 9.101 — Verify calendar hash | PY (FS) • 300ms |
| 9.105 — Write calendar_events (txn) | PY (DB) • 100ms |
| 9.107 — Emit active_calendar_signals.csv | PY (FS) • 80ms |
| 9.121 — Apply revision & recompute | PY • 150ms |
| 9.201 — Append trade_results.csv | EA (FS) • 120ms |
| 9.210 — Classify outcome/duration | PY • 25ms |
| 9.220 — Parameter resolution (tiered) | PY (DB) • 40ms |
| 9.224 — Emit decision (atomic) | PY (FS) • 60ms |
| 9.230 — Ingest decision | EA • ≤5s detection |
| 9.232 — Execute order(s) | EA • broker latency ≤800ms |
| 9.250 — Persist trade_result to DB | PY (DB) • 50ms |
| 9.303 — Inspect last file_seq | PY (FS) • 40ms |
| 9.304 — CSV integrity check | PY • 60ms |
| 9.401 — Compute latency from heartbeat | PY • 20ms |
| 9.501 — Metrics update | PY (DB) • 30ms |
| 9.602 — Order send retry then reject | EA • per policy |
| 9.704 — Restart hydration success | PY • ≤2s |

# 10. Error Handling & Resilience

## 10.1 CSV Race Conditions
- Avoided via atomic writes, sequences, checksums.

## 10.2 Time Drift & DST
- Broker offset monitored; all core logic uses UTC.

## 10.3 Data Quality Guards
- Quarantine invalid ingest; dual‑source reconcile if available.

---

# 11. Performance Targets (SLOs)

## 11.1 Latency
- Decision time from trade close → CSV emit ≤ 150 ms (p95).

## 11.2 Throughput
- Support ≥ 50 concurrent symbols without missed emissions.

## 11.3 Availability
- 99.5% decision service availability during trading hours.

---

# 12. Security & Permissions

## 12.

### 12.y Performance Benchmarks (Targets)

- **Calendar Import**: weekly pull & normalize ≤ 5 minutes (p95).
- **Decision Latency**: end‑to‑end emit ≤ 500 ms (p95), ≤ 1000 ms (p99).
- **DB/Storage Ops**: critical queries ≤ 100 ms (p95).
- **Transport Uptime**: CSV and Socket ≥ 99.5% rolling 1h.
- **Failover Recovery**: switch to alternate transport ≤ 2 seconds.

Benchmarks are enforced via `performance_metrics` and alert thresholds defined in this spec.


## 12.x Data Model & Analytics Entities (Logical, Non-SQL)

- **`trades`** — executed orders with link to originating decision and re‑entry chain id.
- **`reentry_chains`** — chain/group identifier with generation counters and status.
- **`reentry_performance`** — per-bucket aggregates (win rate, avg MAE/MFE, expectancy).
- **`calendar_events`** — normalized events with CAL8 key and vendor lineage.
- **`system_metrics`** — operational SLOs and adapter transitions (joins `health_metrics.csv`).

**Core KPIs:** decision latency (p95/p99), fallback rate, conflict rate, socket/csv uptime %, chain expectancy per profile, and drawdown recovery time.
1 File Access
- Least‑privilege on shared folders; read‑only for MT4 where applicable.

## 12.2 Integrity
- Checksums on all outbound CSVs; audit trail for mapping/param changes.

---

# 13. Testing & Validation

## 13.1 Backtest Fidelity
- Rebuild historical proximity/state using stored schedules with `revision_seq`.

## 13.2 Property‑Based Tests
- Invariants: `lot(R2) ≤ lot(O)` under same overlays; `fallback_tier` non‑increasing with mapping completeness.

## 13.3 Canary & A/B
- Enable new signals on subset of symbols with reduced sizes until sample thresholds.

---

# 14. Monitoring & Telemetry

## 14.1 Metrics (emitted to `metrics` & `health_metrics.csv`)
- Mapping coverage %, fallback rate, decision latency, slippage vs expected, spread vs model, conflict rate, calendar revisions processed, circuit‑breaker triggers.

## 14.2 Alerts
- Coverage violation, checksum failure, broker drift > threshold, excessive fallbacks, proximity/state rebuild failures.

## 14.3 Metrics Panel (UI Contract)
- **Purpose:** Single screen for live operational health.
- **Data Source:** `metrics` table and `health_metrics.csv`.
- **Refresh Cadence:** 1s (configurable), rolling 15m/1h aggregates.
- **Core Tiles:** Mapping coverage %, fallback rate (tier>0), decision latency p95/p99, slippage delta (actual−expected), spread vs model, signal conflict rate, calendar revisions processed, circuit‑breaker triggers, CSV integrity (seq gaps / checksum failures).
- **Drill‑downs:** Per‑symbol hybrid‑ID hit distribution; top unmapped combos; per‑family performance.
- **Alarms:** Visual badges linked to §14.2 thresholds.

# 15. Change Management & Governance

## 15.1 Parameter & Mapping Changes
- PR‑style workflow; automated diffs; time‑boxed rollbacks; append‑only `mapping_audit`.

## 15.2 Manual Overrides
- Require scope, TTL, reason; auto‑revert; tag resulting trades for separate PnL.

---

# 16. Subsystem Specifications (Standardized Format)

## 16.1 Economic Calendar — Spec Summary
### 16.1.1 Inputs/Outputs
- Inputs: primary feed, session/holiday calendars.
- Outputs: `active_calendar_signals.csv`, `calendar_events` table, metrics.
### 16.1.2 IDs & States
- CAL8/CAL5; state machine per §4.6; event‑type proximity per §4.5.
### 16.1.3 Algorithms
- Normalization, proximity bucketing, lifecycle transitions, revision handling.
### 16.1.4 Constraints
- Holiday/DST suppression, revisions mandatory.
### 16.1.5 KPIs
- Timeliness of updates, revision processing latency, data quality error rate.

## 16.2 Matrix — Spec Summary
### 16.2.1 Inputs/Outputs
- Inputs: signals, trade close data; Outputs: ParameterSet mappings.
### 16.2.2 IDs & Dimensions
- Hybrid ID; Signal/Outcome/Duration/Proximity/Generation.
### 16.2.3 Algorithms
- Lazy materialization; fallback resolution; audit logging.
### 16.2.4 Constraints
- Durationless signals allowed; cooldown prox supported.
### 16.2.5 KPIs
- Coverage %, fallback tier rate, lookup latency.

## 16.3 Re‑Entry — Spec Summary
### 16.3.1 Inputs/Outputs
- Inputs: trade close info, signals, risk models, broker constraints.
- Outputs: reentry decisions; trade results with frozen params.
### 16.3.2 IDs & Governance
- Uses Hybrid ID; Re‑Entry Ledger enforcement.
### 16.3.3 Algorithms
- Outcome/duration classification; risk overlays; exposure caps; broker rounding.
### 16.3.4 Constraints
- Max R2; circuit breakers; portfolio caps.
### 16.3.5 KPIs
- Decision timeliness, slippage vs expected, breaker activations.

---

## 16.4 Execution Engine — Spec Summary
### 16.4 Execution Engine → EA Bridge (UPDATED)
**Exports (Sockets):**
- `InitializeBridge()` / `ShutdownBridge()`  
- `int SocketConnect(const char* host, int port)` → returns `handle` ≥ 1 or `-1` on failure  
- `int SocketSend(int handle, const char* message)` → bytes sent or `-1`  
- `int SocketReceive(int handle, char* buffer, int bufferSize, int timeoutMs)` → bytes received or `-1`  
- `int SocketClose(int handle)` → 0 on success, `-1` on failure  
- `int SocketIsConnected(int handle)` → `1/0`  
- `int GetConnectionStats(int handle, int* bytesSent, int* bytesReceived, int* errorCount)` → 0/−1

**Exports (Named Pipes, optional Windows local transport):**
- `int PipeConnect(const char* pipeName)`  
- `int PipeSend(int pipeHandle, const char* message)`  
- `int PipeClose(int pipeHandle)`

**Operational Notes:**
- One active handle per transport channel; heartbeat worker maintains liveness.
- On any `-1` return, emitter logs error and suppresses downstream CSV→EA commits for that tick.


### 16.4.1 Inputs/Outputs
- **Inputs:**
  - `reentry_decisions.csv` (authoritative decisions from Matrix/Re‑Entry engine)
  - `active_calendar_signals.csv` (optional display/telemetry only; no autonomous trading in listener mode)
  - `BrokerConstraints` repo snapshot (§7.7) and `PairEffect` (§7.4)
- **Outputs:**
  - `trade_results.csv` (atomic append with `file_seq`, `ts_utc`, checksum)
  - Signal/DLL response logs (if DLL mode enabled)

### 16.4.2 Modes (recommended)
- **Listener‑CSV (prod default):** `AutonomousMode=false`, `EnableCSVSignals=true`, `EnableDLLSignals=false`.
- **Listener‑DLL (optional):** `AutonomousMode=false`, `EnableDLLSignals=true`.
- **Autonomous (lab only):** `AutonomousMode=true` (internal calendar/time filters may execute; **not** for production per §4/§5 governance).

### 16.4.3 Contracts & Behaviors
- **Decision ingestion:** Poll `reentry_decisions.csv` by `file_seq`; verify checksum; ignore stale/out‑of‑order rows; execute only matching `Symbol()`.
- **Pre‑flight overlay:** Before `OrderSend`, apply `BrokerConstraints` (lot rounding, min stops, freeze level) and `PairEffect` (spread buffers, cooldown) (§6.4, §7.4, §7.7).
- **Circuit breakers & exposure:** Enforce portfolio caps (§8.1) and global breakers (§6.7) locally; refuse orders when tripped.
- **Results emission:** On close (or partial), emit `trade_results.csv` with UTC fields and exact params used (frozen snapshot ID@version, §7.3).

### 16.4.4 Algorithms
- **SafeOrderSend/Modify** wrappers with retry/backoff and structured error taxonomy.
- **Spread/latency guard:** Block entries when spread > modeled threshold for current `SIG/PROX` family (§8.2).
- **Health beacons:** Periodic status lines in `health_metrics.csv` (latency, last seq processed, slippage deltas).

### 16.4.5 Constraints
- No inference: if decision row invalid or checksum fails → skip and log (§17.3).
- Execution conforms to MT4/MQL4 only; no MQL5 APIs.

### 16.4.6 KPIs
- Decision‑to‑send latency (p95), checksum failure rate, slippage vs expected, rejected orders by constraint type, circuit‑breaker activation count.

### 16.4.7 Required Changes vs Current EA Implementation
- **Add** atomic CSV write/read: `file_seq`, SHA‑256 `checksum`, temp‑file rename.
- **Switch** timestamps to **UTC** on all emissions; include `account_id`.
- **Implement** `reentry_decisions.csv` ingestion path; bind to `Symbol()` and de‑duplicate by `file_seq`.
- **Load & apply** `BrokerConstraints` (§7.7) and `PairEffect` (§7.4) before `OrderSend`.
- **Disable** production `AutonomousMode`; keep for labs only.
- **Emit** `trade_results.csv` with **append**, not truncate; include frozen `parameter_set_id@version` if provided by decision row.

## 16.5 Component Relationship Matrix (Execution Engine)

| Source Component | Target Component | Data Flow Type | Trigger | Source Doc |
|---|---|---|---|---|
| Re‑Entry Decision Emitter (PY) | Execution Engine (EA) | `reentry_decisions.csv` | New decision (`file_seq`↑) | §2.2–§2.3, §17.1 |
| BrokerConstraints Repository | Execution Engine (EA) | Constraints snapshot | OnInit / Timer refresh | §7.7, §16.4.3 |
| PairEffect Table | Execution Engine (EA) | PairEffect snapshot | OnInit / Timer refresh | §7.4, §16.4.3 |
| Execution Engine (EA) | Trade Results CSV | `trade_results.csv` append | After order open/modify/close | §17.2 |
| Execution Engine (EA) | Health Metrics CSV | `health_metrics.csv` append | Timer heartbeat | §14.1, §14.3 |
| Execution Engine (EA) | Broker/Server | Orders (send/modify/close) | Valid decision & pre‑flight OK | §16.4.4, §17.3 |
| Execution Engine (EA) | Logs/Ops | Structured logs | Errors/executions | §17.4 |

# 17. MT4 (MQL4) Integration Contracts

## 17.0 EA Configuration Flags
- `EnableCSVSignals` (bool): enable CSV ingestion/emit. Default **true** in production.
- `EnableDLLSignals` (bool): enable socket bridge. Default **false** in production.
- `ListenPort` (int): socket port (default 5555).
- `CommPollSeconds` (int): CSV poll cadence for decisions (default 5s; min 1s).
- `DebugComm` (bool): verbose comm logs to Experts tab.

## 17.1 Read Contracts
- **Decisions:** Read `reentry_decisions.csv` (validate `file_seq` monotonicity & `checksum`). Execute only rows where `symbol == Symbol()`; ignore stale `file_seq`.
- **Signals (optional):** Read `active_calendar_signals.csv` for on‑chart display/telemetry; **never** as a trading source in production.

## 17.2 Write Contracts
- **Trade results:** Append to `trade_results.csv` using atomic write/rename with `file_seq`, `ts_utc`, and `checksum`. Include all listed fields (§2.2) plus any broker‑side fills/slippage.
- **Health metrics:** Periodically append to `health_metrics.csv` (decision latency, slippage delta, last processed `file_seq`).

## 17.3 Execution Behavior (MQL4)
- Respect `lots`, `sl_points`, `tp_points`, `entry_offset_points` from decisions.
- Apply broker rounding/min distances/freeze checks (from `BrokerConstraints`, §7.7) prior to `OrderSend`.
- Enforce exposure caps (§8.1) and circuit breakers (§6.7); if blocked, log a non‑execution response.

## 17.4 Error Handling
- If decision row invalid or checksum fails → log & skip; do not infer substitutes.
- Propagate structured error/taxonomy in logs and responses; include `last_error`, `context`, `ticket` if applicable.

# 18. Migration & Rollout Plan

## 18.1 Phased Approach
1) Introduce CAL8 parallel to CAL5; dual‑write.
2) Enable `CD` prox and `NA` duration.
3) Switch to lazy matrix materialization + coverage alerts.
4) Enforce Re‑Entry Ledger; add exposure caps and circuit breakers.
5) Replace rigid suppression with score‑based composition.

## 18.2 Rollback Strategy
- Feature flags per family; DB schema versioning; snapshot/restore of mappings.

---

# 19. Glossary
- See §0.5 and §3 for identifier acronyms; §5.3 for outcome buckets; §3.5 for signal families.

---

# 20. Appendices

## 20.1 Example Hybrid IDs
- `AUSHNF10-O-ECO_HIGH_USD-FL-O4-IM-EURUSD`
- `EGBHCP10-R1-ANTICIPATION_1HR_GBP-NA-O3-SH-GBPUSD`
- `00000000-O-VOLATILITY_SPIKE-FL-O6-EX-USDJPY`

## 20.2 Example Parameter Templates (IDs only)
- `NEWS_HIGH_CONS_V1`, `NEWS_HIGH_MOD_V1`, `NEWS_HIGH_AGGR_V1`
- `ANT_1H_CONS_V1`, `SESSION_LDN_CONS_V1`, `VOL_SPIKE_CONS_V1`, `ALL_INDICATORS_BASE_V1`

## 20.3 Coverage Queries (Pseudocode)
- **Unmapped live combos**: active signals × recent outcomes without `matrix_map` rows.
- **Fallback rate**: count(tier>0)/count(decisions) daily.
- **Latency**: p95 write‑to‑read interval for decisions.

## 20.4 Safe Defaults Policy
- Family‑scoped conservative sets; must satisfy broker min stops + spread buffers.

## 20.5 Invariants Checklist
- R2 lot ≤ R1 lot ≤ O lot after overlays.
- Cooldown `CD` always widens stops vs `IM` for same family.

— End of Specification —

### Database Tables (Referenced by Health Metrics)

**`system_status`**
- `ts_utc` *(timestamp, PK)*
- `component` *(text, PK)* — e.g., `pcl.router`, `ea.execution`
- `status` *(enum OK|WARN|ERROR|DEGRADED)*
- `message` *(text)*
- Index: `(component, ts_utc DESC)`

**`performance_metrics`**
- `ts_utc` *(timestamp, PK)*
- `p95_latency_ms` *(int)* — decision end‑to‑end
- `p99_latency_ms` *(int)*
- `fallback_rate` *(real)* — fraction of decisions using non‑primary transport
- `conflict_rate` *(real)* — fraction of matrix conflicts per 100 decisions
- `socket_uptime_pct` *(real)*, `csv_uptime_pct` *(real)*
- `decision_throughput_per_min` *(real)*
- Index: `(ts_utc DESC)`



### 19.x Glossary Additions

- **Anticipation Event** — a pre‑release calendar‑driven signal with a bounded validity window.
- **Die Roll Logic** — outcome bucketing framework producing deterministic action selection.
- **Re‑Entry Chain / Generation** — lineage of trades/actions following a single originating event.
- **State Machine** — discrete state transitions guiding decision eligibility and gating.
- **Straddle Trade** — an options‑style entry structure applicable to pre‑event positioning.

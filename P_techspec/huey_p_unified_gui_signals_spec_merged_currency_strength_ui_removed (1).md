# HUEY_P Unified GUI & Signals Specification

**Status:** Draft merged spec  
**Sources merged:** `guiimp.txt`, `ui_controls_validation.md`, `sig1.txt`, `GUI structure.txt`, `advanced currency strength and conditional probability system in the GUI.txt` (concepts only)  
**Explicit exclusion:** Practical **currency-strength layout** and **engine-hook** details

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
25) Currency Strength & Sub‑Indicators Tab
   - 25.1 Inputs & sources
   - 25.2 Core definitions
   - 25.3 Sub‑indicators
   - 25.4 Signals & probability integration
   - 25.5 Controls & validation
   - 25.6 Filters & actions
   - 25.7 KPIs & history
   - 25.8 Acceptance criteria
   - 25.9 UI widgets (sortable table & sparkline)
   - 25.10 Fixed windows & layout
   - 25.11 Controls & actions (buttons)

## 1) Scope & Principles
This document unifies the GUI modernization plan into one cohesive specification. It defines the application architecture, indicator plugin model, signal normalization, conditional-probability semantics, validation UX, navigation/tabs, alerting, theming, and test/rollout plans. It is **implementation-agnostic** (no code) and **excludes** concrete currency-strength layouts and engine wiring.

**Design tenets**
- **Safety-first:** Strong validation, guardrails, and risk transparency.
- **Extensible:** Indicator plugins, auto-forms, grid layout, and signal contracts.
- **Observable:** Unified telemetry, history, and analytics.
- **Consistent:** Single EventBus taxonomy and StateManager as source of truth.
- **Accessible:** Theme tokens, clear states, keyboard ops, and text contrast.

---

## 2) Architecture Overview
### 2.1 Core runtime services
- **EventBus (pub/sub):** Topics for data, UI, risk, signals, alerts; metrics for publish rates and subscriber counts.
- **StateManager:** Central, snapshot-oriented store (read-only views for UI components; writes via dispatched actions or events). Holds: connectivity, user prefs, risk posture, open positions summary, indicator statuses, alert stats, and selected template.
- **Feature Registry:** Registry for indicators, views, and tools. Provides discovery metadata (id, category, inputs/outputs, default params, render hints).
- **Theme System:** Semantic tokens (surface, outline, positive/neutral/negative, info/warn/error) and variants (light/dark/contrast). No hardcoded colors; tokens only.
- **Toast/Alert Manager:** Queues, priorities, cooldowns, deduplication, and persistence of last N alerts. Emits via EventBus; visible in UI and stored to history.
- **Risk Ribbon:** Compact, always-visible summary of risk posture (latency, data-health, leverage bands, exposure, guard flags). Integrates with alerts.

### 2.2 App layout & navigation
- **Global frame:** Header (status/quick actions) → left navigation (tabs) → content area (grid-based panels).
- **Primary tabs:**
  1) **Live** — real-time overview & operator console
  2) **Config (Settings)** — global and per-indicator/strategy parameters
  3) **Signals** — normalized signal stream with probability fields
  4) **Templates** — save/load layouts & parameter bundles
  5) **Trade History** — executed orders, P/L metrics, filters & KPIs
  6) **History/Analytics** — logs, KPIs, exports (signals/alerts/config)
  7) **DDE Price Feed** — data feed controls, subscriptions, live table
  8) **Economic Calendar** — event ingestion, filters, exports
  9) **System Status** — health, diagnostics, controls

### 2.3 Grid Manager (panels)
- **Cells:** 1×1, 2×1, 2×2 (extensible sizes). Drag/drop, resize, add/remove panels.
- **Panel contract:** `panel_id`, `title`, `render_mode` (overlay/inline/table/chart), `inputs` (symbols, timeframe), `outputs` (values/bands/states), `params` (schema), and `events_subscribed`.
- **Lifecycle hooks:** `mount`, `update(params/state)`, `unmount`.
- **Persistence:** Layout & params are versioned and stored per Template.

---

## 3) Indicator Plugin Model
- **Registration:** Each indicator registers with id, category (trend/oscillator/volatility/volume/custom/other), required feeds, and display hints.
- **Config schema:** Parameter spec with types, bounds, defaults, and dependencies. Used to auto-generate forms (see §4).
- **Execution:** Deterministic `calculate` producing typed outputs (values, bands, states). Performance budget per tick to protect UI.
- **Display:** Indicators render via the Grid Manager with their declared `render_mode` and `outputs`.
- **Safety:** Hot reload of params re-initializes internal buffers safely; param changes are transactional.

---

## 4) Validation & Controls (Unified UX Layer)
**Goal:** One canonical validation spec applied app-wide (Config, Templates, Indicator params, Strategy rules).

### 4.1 Control types
- **Booleans:** Toggle or checkbox; inline help text; grouped by feature.
- **Numbers:** Min/max, step, units (pips, %, seconds); soft warnings vs hard errors; inter-field constraints (e.g., `TakeProfit > StopLoss`).
- **Enums:** Radio/select with descriptions; searchable for long lists.
- **Text:** Length and regex constraints; placeholders with examples.
- **Dynamic sections:** Conditional show/hide based on other fields or data availability.

### 4.2 Validation behaviors
- **Debounced validation** on change; immediate validation on apply.
- **Severity levels:** info, warn, error (with consistent toast styling).

### 4.3 Accessibility & help
- Inline descriptions, tooltips, error regions announced to screen readers.

### 4.4 Reusability
- Parameter specs power: form generation, import/export, API validation, and template diffs.

---

## 5) Normalized Signal Model
A single envelope for all signal-producing components, enabling consistent routing, filtering, display, and analytics.

### 5.1 Core fields
- `id`, `ts`, `source` (indicator/strategy id), `symbol` (or basket), `kind` (e.g., breakout/momentum/mean_reversion/squeeze/other), `direction` (long/short/neutral), `strength` (0–100), `confidence` (LOW/MED/HIGH/VERY_HIGH), `ttl` (optional), `tags` (list).

### 5.2 Probability extension fields
- `trigger` (human-readable description), `target` (price move/threshold evaluated), `p` (probability 0–1), `n` (sample size), `state` (optional snapshot of relevant indicator states), `horizon` (evaluation window), `notes`.

### 5.3 Contract guarantees
- Versioned schema; missing optional fields → null; strict types; units included for quantitative values; trace id for data lineage.

---

## 6) Conditional Probability Engine (Concept)
**Purpose:** Compute empirical probabilities for (trigger → target within horizon) across parameter grids to enrich signals and drive alerts/policies.

### 6.1 Parameter axes (M/W/K/T)
- **M** (trigger move size, pips)
- **W** (trigger detection window, minutes)
- **K** (target move size, pips)
- **T** (target evaluation window, minutes)

### 6.2 Outputs (p, n)
- `p` (success probability), `n` (sample count), confidence tier derived from (`p`, `n`), plus optional conditioning on states (e.g., volatility regime).

### 6.3 Confidence tiers
- **VERY_HIGH:** `p ≥ 0.70` and `n ≥ 500`
- **HIGH:** `p ≥ 0.60` and `n ≥ 250`
- **MEDIUM:** `p ≥ 0.55` and `n ≥ 150`
- **LOW:** below thresholds

### 6.4 Policy hooks
- Minimum sample size (`n_min`) per market/timeframe; optional cooling-off after regime shifts; outlier trimming rules; stale-data TTL.

### 6.5 Transparency & export
- Show `p` and `n` with last-updated timestamp; enable export of probability tables; log methodology and data coverage.

> Note: Only the **concept** is defined here—no concrete UI layout, panel placement, or engine wiring is specified.

---

## 7) Live Tab
**Purpose:** Give operators a real-time, at-a-glance view and quick actions.

### 7.1 Key panels
- Status cards: connectivity, latency, data-health, risk posture, open positions summary.
- Signal ticker: latest normalized signals with direction/strength/confidence (`p`, `n` when available).
- Quick actions: acknowledge alerts, pin signals, jump to related Config/History.

### 7.2 Filters & controls
- Symbol/timeframe filters; pause/resume auto-scroll; compact/detailed row density.

### 7.3 Acceptance criteria
- Live cards update ≤ 1s latency under expected load.
- Ticker deduplicates identical signals within TTL and shows ack state.
- All quick actions emit corresponding EventBus events and persist to History.

### 7.4 Controls & actions (buttons)
- **Acknowledge alert** (row & toolbar) — *Ack selected alert* → `alerts.acknowledge {alert_id}`; disables when none selected; side‑effect: ticker row marked ACK, toast confirms (tid:`live_ack_alert`).
- **Pin signal** (row) — *Pin to Live* → `signal.pin {signal_id}`; appears in Live ticker/cards; undo via row menu (tid:`live_pin_signal`).
- **Pause/Resume auto‑scroll** (toolbar toggle, ␣) — `ui.ticker_autoscroll_toggle`; persists in user prefs (tid:`live_autoscroll_toggle`).
- **Open in Config** (row) — navigate to source indicator/strategy form → `ui.navigate {target:"config", anchor}` (tid:`live_open_config`).
- **Copy trace id** (row) — copies normalized `trace_id` to clipboard (tid:`live_copy_trace`).
- **Refresh snapshot** (toolbar, ⟳) — force refresh Live cards → `ui.refresh_live` (guard: cooldown 3s) (tid:`live_refresh`).

---

## 8) Config (Settings) Tab
**Purpose:** Centralize global settings and per-indicator/strategy parameters with strong validation.

### 8.1 Global settings
- Data sources, update intervals, alert thresholds, theme, hotkeys.
- **Communications (bridge):** `COMM_MODE` (Auto / CSV / Socket), `ListenPort`, `CommPollSeconds`, `EnableCSVSignals`, `EnableDLLSignals`, `DebugComm` (default: off). Document safe defaults and validation (e.g., port range).


### 8.2 Per‑indicator/strategy forms
- Auto-generated forms from parameter specs with inline validation.

### 8.3 Dependency guardrails
- Disable/hide fields when upstream feeds or modes are incompatible.

### 8.4 Acceptance criteria
- Debounced validation on change; hard errors block Save; warnings allow Save with toast.
- Parameter changes are transactional and logged; rollback via Templates or History.
- Form generation is driven solely by parameter specs; no custom hand-wired fields.

### 8.5 Controls & actions (buttons)
- **Save** (primary, ⌘/Ctrl+S) — validate then persist params; emits `config.changed` on success; disabled on invalid (tid:`config_save`).
- **Revert** — discard unsaved edits in current form; confirmation dialog (tid:`config_revert`).
- **Validate now** — run full validation without saving; surfaces toasts (tid:`config_validate_now`).
- **Load defaults** — restore registered defaults for the current plugin (tid:`config_load_defaults`).
- **Import JSON** — load parameter JSON; schema check + diff preview (tid:`config_import_json`).
- **Export JSON** — export current parameters with checksum (tid:`config_export_json`).
- **Copy deep‑link** — copies URL to this form/section for sharing (tid:`config_copy_link`).
- **Reconnect Socket** — drop & re-establish socket (guard: COMM_MODE=Socket) (tid:`config_comm_reconnect`).
- **Test Bridge** — send ping through current COMM_MODE and show round-trip & error count (tid:`config_comm_test`).

---

## 9) Signals Tab
**Purpose:** Provide a unified, filterable stream/table of normalized signals.

### 9.1 Columns
- Time, symbol, kind, direction, strength, confidence, `p`, `n`, horizon, tags, source.
- **Identifiers (visible):** `hybrid_id`, `cal8`, `cal5`, and the Hybrid ID components: `GEN`, `SIG`, `DUR`, `OUT`, `PROX`, `SYMBOL`.
- **Provenance (detail drawer):** `file_seq`, `checksum` (for calendar/matrix-derived rows), adapter mode (CSV/socket), and last revision id.

### 9.2 Interactions
- Multi-filter (symbol, timeframe, kind, confidence tier, `p`/`n` ranges, tags).
- **Click-throughs:**
  - From any signal row → open corresponding **Reentry Matrix** slice using the `hybrid_id`/components.
  - From calendar-sourced rows → open **Economic Calendar** event detail.
- Actions: flag, copy, export selection, open in History/Analytics, pin to Live.

### 9.3 Acceptance criteria
- Infinite scroll/pagination without UI jank; stable column widths.
- Filters persist per user/session; exports respect filters and include visible identifier fields.
- Every row resolves to a source (trace id) for auditability, including `file_seq`/`checksum` when present.

### 9.4 Controls & actions (buttons)
- **Save filter preset** — stores current filters under a name (tid:`signals_filter_save`).
- **Clear filters** — reset all filters to defaults (tid:`signals_filter_clear`).
- **Export** (CSV/JSON) — exports visible rows incl. identifiers (tid:`signals_export`).
- **Open in Matrix** (row) — navigate using `hybrid_id` (tid:`signals_open_matrix`).
- **Open in Calendar** (row, when applicable) — open event drawer (tid:`signals_open_calendar`).
- **Pin to Live** (row) — `signal.pin` (tid:`signals_pin_live`).
- **Column picker** — show/hide columns, persist per user (tid:`signals_column_picker`).

---

## 10) Templates Tab
**Purpose:** Save/load dashboard layouts and parameter bundles.

### 10.1 Features (versioning, diff, import/export)
- Versioned templates; diff & rollback; import/export with integrity checks.
- Graceful handling of missing plugins with clear remediation prompts.

### 10.2 Acceptance criteria
- Applying a template updates layout and params atomically.
- Import fails safely with a readable error when checksums or required plugins mismatch.

### 10.3 Controls & actions (buttons)
- **Save template** (primary) — write over current version (tid:`tpl_save`).
- **Save as…** — create new version with notes (tid:`tpl_save_as`).
- **Load** — apply selected template atomically (tid:`tpl_load`).
- **Diff vs current** — side‑by‑side param/layout diff (tid:`tpl_diff`).
- **Export** / **Import** — with integrity checks (tid:`tpl_export`, `tpl_import`).
- **Rollback** — restore a previous version (tid:`tpl_rollback`).

---

## 11) Trade History Tab
**Purpose:** Dedicated view for executed trades and performance KPIs.

### 11.1 Table fields
- Time, symbol, side, size, entry/exit price, SL/TP, realized P/L (amount & %), fees, tags, strategy/indicator origin (if available).
- **Identifiers (visible):** `hybrid_id`, `cal8`, `cal5`, `parameter_set_id`; detail drawer shows Hybrid components `GEN/SIG/DUR/OUT/PROX/SYMBOL`.

### 11.2 Filters & KPIs
- Date range, symbol, side, strategy/tag; KPIs: win rate, avg R, expectancy, P/L by bucket.
- **Re-entry ledger view:** In the detail drawer, show chain **O → R1 → R2** with overlay flags and enforcement indicator (e.g., “max R2 reached”).

### 11.3 Acceptance criteria
- Exports (CSV/JSON) reflect current filters; totals reconcile with broker statements.
- Row click opens a detail drawer with timeline, identifiers (CAL8/CAL5/Hybrid), and linked matrix slice.

### 11.4 Controls & actions (buttons)
- **Export** (CSV/JSON) — filtered trades with identifiers (tid:`hist_export`).
- **Save filter preset** / **Clear** — manage history filters (tid:`hist_filter_save`, `hist_filter_clear`).
- **Open in Equity & Risk** — deep‑link current filters to §24 (tid:`hist_open_equity_dashboard`).
- **Open re‑entry ledger** (row) — show O→R1→R2 chain (tid:`hist_open_ledger`).
- **Copy trade** (row) — copy minimal trade summary to clipboard (tid:`hist_copy_trade`).

---

## 12) History/Analytics Tab
**Purpose:** Logs and analytics for signals, alerts, and configuration changes.

### 12.1 Logs
- Signal emissions, alert lifecycle, config/template changes.
- **Data integrity:** log calendar/matrix file ingestion with `file_seq`/`checksum`, promotion/demotion reasons, and detected sequence gaps.

### 12.2 KPIs
- Hit rate by source/kind, average target time, confidence distribution, false-positive analysis.

### 12.3 Acceptance criteria
- Time-bucketed charts and tables remain responsive on 100k+ rows (virtualized).
- Drill-down preserves filter context when navigating from Signals or Live.

### 12.4 Controls & actions (buttons)
- **Export logs** — CSV/JSON of current log view (tid:`analytics_export_logs`).
- **Add chart** — create a KPI chart from current query (tid:`analytics_add_chart`).
- **Save chart preset** — store visualization + query (tid:`analytics_save_preset`).
- **Clear filters** — reset analytics query (tid:`analytics_clear`).

---

## 13) DDE Price Feed Tab
**Purpose:** Operate market data connections and symbol subscriptions (UI-level only; no engine wiring specified here).

### 13.1 Prereqs & environment
- Windows OS; MetaTrader 4 (MT4) with **Enable DDE server** checked.
- Python dependency: `pywin32` for DDE client access.
- Symbols must be visible in MT4 **Market Watch**; names must match exactly.

### 13.2 Controls
- Connect/Disconnect; endpoint/profile selector; heartbeat/latency indicator; retry policy toggle.

### 13.3 Subscriptions & live table
- Symbol list with add/remove; per-symbol subscribe/unsubscribe; live table of **Symbol, Bid, Ask, Spread, Last Update (ISO8601), Status, Latency (ms)**; status badges per symbol.

### 13.4 Data contract (UI-level)
- `symbol: str`, `bid: float`, `ask: float`, `spread: float` (points/pips), `ts: datetime` (UTC ISO8601), `status: {ACTIVE, STALE, ERROR}`, `latency_ms: float`, `source: "MT4_DDE"`.
- Validation: `bid < ask`; non-negative `spread`; `ts` monotonic per symbol; stale if no update within TTL.

### 13.5 Retry/backoff policy
- Exponential backoff on disconnect: start 1s, ×2 up to 60s; reset on success.
- After 5 consecutive failures: WARN toast with troubleshooting tips; continue backoff attempts.
- All transitions (connect, retry, success, give-up) emit auditable events.

### 13.6 Troubleshooting
- Ensure MT4 is running and DDE enabled; confirm symbols in Market Watch.
- Check profile server name and firewall permissions.
- Restart MT4/app if handshake fails repeatedly.

### 13.7 Testing hooks & matrix
- **Unit:** connect success/fail, add/remove subscription, schema validation.
- **Integration:** simulate disconnects; verify auto-reconnect/backoff; stale detection; toast lifecycle.
- **Performance:** under N symbols, table updates ≤ 1s; CPU/memory within budget.

### 13.8 Acceptance criteria
- Connection state reflects accurately within ≤ 1s; retries surface as toasts with backoff info.
- Adding/removing a symbol updates the live table immediately and persists across sessions.
- Data contract validation enforced with actionable errors.

### 13.9 Controls & actions (buttons)
- **Connect** / **Disconnect** — manage session (tid:`dde_connect`, `dde_disconnect`).
- **Add symbol** / **Remove** — modify watchlist (tid:`dde_add_symbol`, `dde_remove_symbol`).
- **Subscribe all** / **Unsubscribe all** — toggle subscriptions (tid:`dde_sub_all`, `dde_unsub_all`).
- **Retry now** — trigger immediate reconnect/backoff reset (tid:`dde_retry_now`).
- **Latency test** — send ping request; shows round‑trip (tid:`dde_latency_test`).
- **Export snapshot** — CSV of current table (tid:`dde_export_snapshot`).

---

## 14) Economic Calendar Tab
**Purpose:** Ingest, filter, and review scheduled events with export support. Reflects lifecycle state, proximity buckets, and data integrity for CSV↔socket adapters.

### 14.1 Features
- Import (CSV/API when available); filters by date range, currency, impact, category; search.
- **Active Calendar Signals table (CSV-aligned):** columns exactly → `symbol`, `cal8`, `cal5`, `signal_type`, `proximity`, `event_time_utc`, `state`, `priority_weight`, `file_seq`, `created_at_utc`, `checksum`.
- **State chips:** `SCHEDULED`, `ANTICIPATION`, `ACTIVE`, `COOLDOWN`, `EXPIRED` (filterable).
- **Proximity badges:** `IM`, `SH`, `LG`, `EX`, `CD` with a live **countdown to event_time_utc** per row.
- **Revisions & priority:** surface current revision id and apply priority weighting in sort; show last promotion/demotion reason.
- **Communication & Health panel:** adapter mode (CSV/socket), heartbeat, sequence/checksum status; quick actions **Run Socket Test** and **Run CSV Integrity Check**.
- **Alerts:** checksum mismatch or sequence-gap triggers a WARN/ERROR toast and a log entry in §12.
- Event detail drawer; export selected to CSV/JSON; optional auto-refresh schedule.
- **Emergency controls:** operator can **STOP Imports** (pause scheduler; newly ingested/current/future rows marked `BLOCKED`) and **RESUME Imports** (unblock and restart schedule). Emergency state is visible in header.
- **Integrity tiles:** show **sequence-gap** and **checksum-failure** cumulative counts sourced from metrics; link to System Status drill‑down.


### 14.2 Acceptance criteria
- Filters compose (AND) and persist; import shows row counts and validation summary.
- **Integrity checks** report results inline; state chips and proximity badges update without refresh.
- Exports include the active filter metadata and currently visible columns (including cal8/cal5/priority).

### 14.3 Controls & actions (buttons)
- **Import CSV** — ingest events; shows validation summary (tid:`cal_import_csv`).
- **Socket test** — end‑to‑end adapter check (tid:`cal_socket_test`).
- **CSV integrity check** — sequence + checksum audit (tid:`cal_integrity_check`).
- **Refresh/Rescan** — reload active set & revisions (tid:`cal_refresh`).
- **Export selection** — CSV/JSON with visible columns (tid:`cal_export`).
- **Toggle live mode** — auto‑refresh on/off (tid:`cal_live_toggle`).
- **STOP Imports** — enter emergency stop; pause jobs and mark `BLOCKED` (admin‑gated) (tid:`cal_stop_imports`).
- **RESUME Imports** — clear emergency; resume schedule (tid:`cal_resume_imports`).
- Emergency **STOP** takes effect within one poll interval; UI badges/tiles flip to *Stopped*; **RESUME** restarts within one interval.
- Integrity tiles reflect running counts for **seq gaps** and **checksum failures** and link to logs.

---

## 15) System Status Tab
**Purpose:** Central health dashboard for services, queues, tasks, and data feeds.

### 15.1 Contents (health, incidents, resources)
- Service health (OK/Degraded/Down), recent incidents, queue depths, CPU/memory footprints, disk/network alerts.
- **Operational metrics tiles:** mapping coverage %, fallback rate, decision latency p95/p99, slippage vs expected, spread vs model, signal conflict rate, calendar revisions processed, circuit‑breaker triggers.
- **Broker Clock Skew badge** with offset; when |skew| > **120s** or offset stale > **15m**, system enters **DEGRADED** (EA bridge set disconnected), decision emission disabled until **two consecutive** healthy checks.
- **Health metrics tiles:** `database_connected`, `ea_bridge_connected`, `last_heartbeat`, `cpu_usage`, `memory_usage`, `win_rate`, `max_drawdown`, plus existing coverage/latency/fallback/conflict/transport uptime and **CSV integrity** (seq gaps/checksums).

### 15.2 Operator tools
- Restart a non-critical service, clear cache (with confirmation), download diagnostics bundle.
- **Broker/microstructure constraints (read‑only/admin):** show `min_stop`, `lot_step`, `freeze_level`, symbol/account caps, and the latest **pre‑flight** result for the selected symbol.
- **Pause Decisions** — stop emitting new decisions (admin‑gated) (tid:`sys_pause_decisions`).
- **Flatten All** — close all open positions (admin‑gated, confirmation) (tid:`sys_flatten_all`).
- **Cancel All Orders** — cancel all working orders (admin‑gated, confirmation) (tid:`sys_cancel_all`).
- **Resync Broker Clock** — force time resync (tid:`sys_resync_clock`).
- **Escalate / Page** — trigger on‑call alert (tid:`sys_escalate`).

### 15.3 Acceptance criteria
- Health states reconcile with EventBus telemetry; actions emit auditable events.
- **Alerts** fire on coverage/latency threshold breaches and checksum/sequence failures; tiles show last updated timestamps.
- Diagnostics bundle includes timestamps, versions, and redacts secrets.

### 15.4 Controls & actions (buttons)
- **Restart service** — guarded action with confirmation (tid:`sys_restart_service`).
- **Clear cache** — flush non‑critical caches (tid:`sys_clear_cache`).
- **Download diagnostics** — bundle logs/versions (tid:`sys_download_diag`).
- **Acknowledge incident** — mark as reviewed (tid:`sys_ack_incident`).
- **Refresh metrics** — manual update (tid:`sys_refresh_metrics`).
- **Auto‑refresh** — toggle polling (tid:`sys_autorefresh_toggle`).
- In **DEGRADED**, decision‑emitting controls are disabled and labeled with reason; return to **HEALTHY** only after two consecutive good checks.
- Health tiles show thresholds and raise alerts on breaches (coverage/latency/fallback/conflict/transport uptime; CSV integrity counts).
- **Pause Decisions** / **Resume Decisions** (admin) (tid:`sys_pause_decisions`, `sys_resume_decisions`).
- **Flatten All** (admin, confirm) (tid:`sys_flatten_all`).
- **Cancel All Orders** (admin, confirm) (tid:`sys_cancel_all`).
- **Resync Broker Clock** (tid:`sys_resync_clock`).
- **Escalate / Page** (tid:`sys_escalate`).

---

## 16) Reentry Matrix Tab
**Purpose:** Central console to view, edit, and govern the multi‑dimensional **Reentry Matrix** that maps trading context → action + **parameter_set_id**, with performance tracking and versioning.

### 16.1 Dimensions (S/T/O/C, generation)
- **Signal Type (S):** ECO_HIGH, ECO_MED, ANTICIPATION (1h/8h), EQUITY_OPEN_* regions, TECHNICAL/MOMENTUM/REVERSAL, etc. (extensible).
- **Timing / Duration (T):** Time categories for original trades and reentries. For economic signals, duration buckets (e.g., FLASH/QUICK/LONG/EXTENDED) apply conditionally; other signals use NO_DURATION.
- **Outcome (O):** 1–6 buckets (FULL_SL → BEYOND_TP).
- **Context / Proximity (C):** Either **Future Event Proximity** buckets (IMMEDIATE/SHORT/LONG/EXTENDED) or **Market Context** (NEWS_WINDOW, POST_NEWS, SESSION_OPEN, NORMAL). Implementation may support one mode at a time.
- **Generation:** O (original), R1, R2 (**hard stop after R2** by default).

### 16.2 Cell data model
- **parameter_set_id**, **action_type** (NO_REENTRY, SAME_TRADE, REVERSE, INCREASE_SIZE), **size_multiplier**, **confidence_adjustment**, **delay_minutes**, **max_attempts**, **conditions** (JSON), **notes**, **user_override** flag.

### 16.3 Performance panel
- Stats per cell: total executions, wins, win rate, total/avg P&L, best/worst, avg/median duration, current streak, last execution; sample‑size indicator.
- **Coverage & fallback:** display **mapping coverage %** and **fallback tier usage rate**; flag decisions that used fallback tiers (0→5).
- **Unmapped combos:** drill-down table of **top unmapped S/T/O/C/GEN** combinations and the tier used when decisions occur.

### 16.4 Operations & versioning
- Navigate & edit; bulk copy/paste; reset slice defaults; underperformer finder; save/list/compare/rollback versions with notes.
- **Click-throughs:** from a matrix cell to the list of executed decisions (History) and to the **Re-entry ledger** for the most recent chain.
- **Manual Overrides:** create ad‑hoc override entries capturing **scope** (symbol/pair, strategy, cell slice), **TTL** (duration or until next session), and **reason**; overrides auto‑revert on TTL expiry; all resulting trades tagged for separate P&L and audit.


### 16.5 Visualization (heatmap)
- Heatmap by win rate or profit factor with overlays for sample size, overrides, confidence tier, and **fallback tier**.

### 16.6 Validation & guardrails
- Enforce **R2 hard stop**; block unbounded chains; require valid `parameter_set_id`; warn on low sample size; prevent unsafe edits.
- **Fallback policy:** editing cannot remove required fallback tiers; warn on coverage decreases beyond threshold.

### 16.7 Persistence
- Versioned files per symbol with a stable `current_matrix` pointer; log performance per coordinate.

### 16.8 Acceptance criteria
- Cell edits update UI instantly and emit auditable events.
- Version save/rollback is atomic; diffs highlight changed cells.
- Heatmap remains interactive on large matrices; filtering targets 60 FPS.

### 16.9 Controls & actions (buttons)
- **Edit cell** — open editor for selected S/T/O/C/GEN (tid:`mx_edit_cell`).
- **Bulk copy** — copy range to another slice (tid:`mx_bulk_copy`).
- **Reset slice** — restore defaults for a slice (tid:`mx_reset_slice`).
- **Save version** — commit current matrix with notes (tid:`mx_save_version`).
- **Compare versions** — diff two versions (tid:`mx_compare_versions`).
- **Rollback** — restore older version (tid:`mx_rollback`).
- **Open decisions** — list executions for the cell (tid:`mx_open_decisions`).
- **Open re‑entry ledger** — jump to latest chain (tid:`mx_open_ledger`).
- **Export** — CSV/JSON for current slice (tid:`mx_export`).
- **New Override…** — open dialog (scope, TTL, reason) (tid:`mx_new_override`).
- **Revert Override** — immediately remove selected override (tid:`mx_revert_override`).

---

## 17) Re-Entry Parameter Sets Tab
**Purpose:** Authoring workspace for **parameter sets** used by matrix cells and strategies—show required fields first, validate in real time, and provide governed export to runtime.

### 17.1 Required keys
- `parameter_set_id`, `name`, **risk/size** inputs (governed), `stop_loss_pips`, `take_profit_pips`, `entry_order_type`.

### 17.2 Risk & sizing governance
- Risk‑first sizing with a per‑trade cap (**3.5%**); lots derived from risk and SL pips. **Direct lot-size inputs are hidden** unless admin mode is enabled; risk‑based sizing prevails.
- Display **Effective Risk** preview with cap enforcement.

### 17.3 Editor sections
- **Repository table (overview):** columns **version**, **perf_score**, **usage_count**, **last_execution**; sortable/filterable and linked to History.
- **Risk Management:** risk_percent, caps/limits, position limits, daily/weekly guards.
- **SL/TP Methods:** stop_loss_method (FIXED/ATR/PERCENT), take_profit_method (FIXED/RR/ATR), RR ratio, partial TP levels.
- **Entry Orders:** market settings (slippage/retries), pending order settings (type/distance/expiration/method), **straddle** configuration (distances, per‑leg types/ratios, cancel rules).
- **Reentry Controls:** size multipliers/progression, confidence adjustments/decay, delay logic, order type overrides for reentries.
- **Market Conditions:** news/session/volatility rules and multipliers.
- **Chain Management:** generation limits, loss streak/drawdown stops, max chain duration, success‑rate thresholds.
- **Safety & Circuit Breakers:** emergency stops, cool‑downs, trade‑rate limits.
- **Metadata:** description, versioning, created/updated, flags (active, backtest_verified, live_verified).
- **Active Overrides (read‑only):** list overrides that affect this parameter set with remaining TTL and links to revert in Matrix.


### 17.4 Parameter typing & controls
- Binary/toggles for on/off features; Numeric with units, min/max/step; Choice/Enum via radios/selects; String with patterns (e.g., `partial_tp_levels` "50|80"). Sections show/hide based on primary choices.

### 17.5 Validation rules
- Requireds not empty; **TP > SL** when fixed; trailing ≥ SL warns; spread guard vs entry method checks; schema conformance for lists/regex fields; dependency guards.

### 17.6 Bridge & storage
- Persist sets as JSON; emit to runtime via bridge row carrying `parameter_set_id` + checksummed payload; audit log changes; keep version history.

### 17.7 Linkage to Matrix
- Assign sets to cells; warn on delete/rename while in use; quick‑jump from cell to edit linked set.

### 17.8 Acceptance criteria
- Editor surfaces required fields first and blocks save until valid.
- Effective Risk preview reflects caps; exports include only validated fields.
- Changes are logged with who/when/what and can be reverted.

### 17.9 Controls & actions (buttons)
- **New set** — start with required fields only (tid:`ps_new`).
- **Duplicate** — clone from selected (tid:`ps_duplicate`).
- **Save** (primary) — validate and persist (tid:`ps_save`).
- **Export JSON** / **Import JSON** — schema‑checked (tid:`ps_export_json`, `ps_import_json`).
- **Set active** — mark as active/default (tid:`ps_set_active`).
- **Delete** — guarded with dependency checks (tid:`ps_delete`).
- **Link to matrix** — assign to selected cell(s) (tid:`ps_link_matrix`).

---

## 18) Alerts & Notification Policy

### 18.1 Triggering
- Probability/confidence thresholds; sample-size floors; risk posture gates; duplicated-signal suppression within TTL.
- **Ops triggers:** mapping coverage below threshold; fallback usage spike; checksum mismatch or sequence-gap detected by calendar intake.
- **Degraded mode** (broker clock skew/stale offset) and **Emergency STOP** engaged raise WARN/ERROR alerts with remediation links.


### 18.2 Severity
- info/warn/error mapped to toast priority and color tokens.

### 18.3 Lifecycle
- queued → visible → acknowledged → archived; retained in History with context.

### 18.4 Operator controls
- per-source mute, snooze, and escalation path.

### 18.5 Sound cues & preferences
- Ship alert sounds for **warning/danger/emergency** under `/assets/sounds`; user preference to enable/disable and set volume.

### 18.6 Toast types & queue policy
- Toast types: **info/success/warning/danger**. Max on screen: 3; auto‑dismiss after 4–8s depending on severity; deduplicate identical messages within TTL.

### 18.7 Helper API
- `toast.info(msg, opts)`, `toast.success(...)`, `toast.warn(...)`, `toast.danger(...)`; all return a handle for manual dismiss.
- **Acknowledge** and **Escalate (page)** actions are available from alert toasts and the Alerts panel; escalations log the incident id and recipient.

---

## 19) Theming & Accessibility
- **Tokens:** base (surface, text), semantic (positive/neutral/negative), status (info/warn/error), and intensity scales.
- **Contrast:** minimum AA large-text contrast; accessible focus rings; keyboard navigation; tooltip delay and readable sizes.
- **Motion:** reduced-motion mode; avoid critical meaning encoded solely by color.

---

## 20) Event & State Taxonomy (Illustrative)

### 20.1 Event topics
- **Data:** `data.tick`, `data.snapshot`, `data.feed_status`
- **Signals:** `signal.emit`, `signal.update`, `signal.clear`
- **Risk:** `risk.posture_update`, `risk.guard_flag`
- **UI:** `ui.toast`, `ui.template_loaded`, `ui.panel_added`, `ui.panel_updated`
- **Config:** `config.changed`, `config.validation_error`

### 20.2 State keys
State keys (top-level): `app`, `user_prefs`, `risk`, `data_feeds`, `indicators`, `signals`, `alerts`, `templates`, `layout`.

---

## 21) Testing & Rollout Plan

### 21.1 Phase 1 – Foundations
- EventBus, StateManager, Theme tokens, Toast/Alert manager.
- Minimal **Live** + **Config** tabs; basic **Signals** stream (no probability fields yet).

### 21.2 Phase 2 – Plugins & Validation
- Indicator registration + auto-forms from param specs; validation rules wired to toasts; template persistence.

### 21.3 Phase 2b – Data Operations
- **DDE Price Feed** tab (connection UX, subscriptions, live table) and **Economic Calendar** tab (import/filter/export) surfaced with stub backends.

### 21.4 Phase 3 – Probability & Policy
- Introduce Conditional Probability Engine concepts: compute/store `p` and `n`; extend signal schema; add alert thresholds and confidence tiers.

### 21.5 Phase 4 – History & Analytics
- **Trade History** and **History/Analytics** enhancements (KPIs, exports, diffs, audits); performance budgets; profile & optimize UI latency.

### 21.6 Acceptance criteria
- Stable FPS under load; deterministic param updates; no uncaught validation errors; alert dedupe verified; schema versioning documented.

---

## 22) Non‑Goals / Explicit Exclusions
- Concrete currency‑strength **layouts** or **engine wiring** (kept out of this spec; conceptual contracts only).
- Direct broker/exchange API specifics beyond UI data contracts and events.
- Backend persistence schemas beyond what’s required for UI features (templates, matrix versions, parameter sets).

## 23) Future Extensions (Non‑binding)
- Role-based permissions; multi-profile templates; layout preset library.
- Scenario simulation (what‑if thresholds); incident playbooks; per-asset-class overrides.
- Advanced analytics modules (e.g., regime detection), once base KPIs stabilize.

## 24) Equity & Risk Dashboard (Live)
**Purpose:** Real‑time view of account equity and risk derived from **actual trade closes** as the system records them. This tab is analytical (not an order console) and reconciles with **§11 Trade History**.

### 24.9 Controls & actions (buttons)
- **Toggle overlays** — show/hide comparison series (tid:`eq_toggle_overlays`).
- **Save view preset** — store filters/layout (tid:`eq_save_view`).
- **Export series** — equity/drawdown CSV/JSON (tid:`eq_export_series`).
- **Snapshot** — download PNG of charts (tid:`eq_snapshot_png`).
- **Compare mode** — enable A/B selection (tid:`eq_compare_mode`).
- **Net/Gross toggle** — switch P/L basis (tid:`eq_net_gross`).
- **Currency normalize** — convert to base currency view (tid:`eq_currency_norm`).

### 24.1 Data contract (events & fields)
**Input events** (via EventBus):
- `trade.close` — close of a trade/position.
  - Fields (UI‑level): `trade_id`, `position_id` (optional), `account_id`, `strategy_id` (optional), `parameter_set_id` (optional), `symbol`, `side` (LONG/SHORT), `qty`, `entry_price`, `exit_price`, `fees`, `taxes` (optional), `slippage_cost` (optional), `ts_close` (UTC ISO8601), `pl_gross`, `pl_net` (if not provided, compute), `r_multiple` (optional), `currency`.
- `account.cash_adjustment` — deposit/withdrawal or non‑trade P/L. Fields: `amount`, `currency`, `ts`, `note`.

**Derived series**:
- `equity_t` — running equity in **base currency**: `equity_t = equity_{t-1} + pl_net + cash_adjustments_t`.
- `peak_t` — running peak of `equity_t` per filter context.
- `drawdown_t` — `(peak_t - equity_t) / peak_t`.

**Normalization**:
- If trades are multi‑currency, convert `pl` at the close timestamp using feed/FX tables; display conversion source in tooltip.
- Store and display both **gross** and **net** variants (user toggle), with default to **net**.

### 24.2 Panels
- **Equity Curve (live):** streaming line of `equity_t` with markers for deposits/withdrawals; optional overlays (by strategy/tag/account/time window).
- **Drawdown Curve:** concurrent plot of `drawdown_t`; hover shows time underwater since last peak.
- **Outcome Distribution:** bar/pie of per‑trade Δ buckets (e.g., MaxLoss/HalfLoss/BE/HalfGain/MaxGain/ExtendedGain) or R‑buckets if available.
- **Risk Panel (cards):** Max DD, Time Underwater (95th pct), Risk‑of‑Ruin proximity, VaR(5%) per trade, Profit Factor, Expectancy.
- **Recent Closes Table:** last N trades with fields from **§11.1**; clicking a row highlights the point on charts.

### 24.3 Filters
- Date range (absolute/relative), symbol(s), strategy/tag, `parameter_set_id`, account, gross/net toggle, currency normalization, series smoothing (off/1m/5m downsample for performance).
- Comparison mode: A vs B (e.g., two strategies or two time windows) with color‑coded overlays.

### 24.4 Metrics (formulas)
- **Per‑trade net change:** `Δ_i = pl_net_i` (ensure fees/taxes/slippage applied).
- **Equity recursion:** `equity_i = equity_{i-1} + Δ_i + cash_adj_i`.
- **Drawdown:** `dd_i = (max_{k ≤ i} equity_k - equity_i) / max_{k ≤ i} equity_k`.
- **Max DD:** `max(dd_i)` over the filter window.
- **Time Underwater:** sum of durations where `equity < peak` since last peak; report mean/median/95th pct.
- **Expectancy (per trade):** `E[Δ] = p_win·avg_win + p_loss·avg_loss + p_be·0`.
- **Profit Factor:** `PF = sum(Δ_i | Δ_i>0) / |sum(Δ_i | Δ_i<0)|`.
- **Geometric growth (approx.):** with `r_i = Δ_i / equity_{i-1}`, `G = exp( avg( ln(1 + r_i) ) ) - 1` over the window.
- **VaR 5% (empirical):** the 5th percentile of `{Δ_i}` over the chosen sample.
- **Risk of ruin (operational):** flag if equity crosses configured floor (e.g., 50% of initial) or distance to floor ≤ threshold.

### 24.5 Alerts
- Threshold breaches emit `ui.toast` + persist to History: new **max DD**, VaR(5%) worse than limit, equity floor proximity, single‑trade loss beyond X·R.
- Alerts respect **§18** severity mapping and deduplication TTL.

### 24.6 Performance & acceptance criteria
- New `trade.close` event appears in charts/cards **≤ 1s** after receipt under expected load.
- Charts remain interactive with **≥ 50k trades** (downsampling & virtualization where needed).
- KPIs reconcile with **§11 Trade History** totals for the active filter window.
- Comparison overlays support at least **3** simultaneous series without frame drops.

### 24.7 Export & share
- Export filtered **equity/drawdown series** + KPIs to **CSV/JSON**; copy chart snapshot (PNG) with legend & filters embedded.
- Deep‑link: generate a link that restores filters/time window and selected overlays.

### 24.8 Data quality & edge cases
- **Partial closes:** group by `position_id` for equity accounting.
- **Duplicates/out‑of‑order:** de‑dupe by `trade_id`; reorder by `ts_close` before computing series.
- **Corrections:** accept `trade.amend` events that restate fields; recompute downstream series deterministically.
- **Multi‑currency:** show both native and base‑currency P/L in tooltips; list conversion source.
- **Deposits/withdrawals:** render as labeled markers, excluded from expectancy/PF unless the user opts in.
- **Session resets:** preserve last filter context and chart zoom across sessions.


## 25) Currency Strength & Sub‑Indicators Tab
**Purpose:** Dedicated tab to visualize and act on multi‑horizon currency strength, including sub‑indicators (e.g., % change, normalized z‑scores, momentum/mean‑reversion flags) and integration with signal probability.

### 25.1 Inputs & sources
- Price feeds from DDE/bridge (mid or bid/ask); roll‑up per currency from constituent pairs.
- Configurable base currency and normalization method (z‑score vs percentile rank).

### 25.2 Core definitions
- **Strength**: normalized measure across pairs for a currency within a time window.
- **Delta/Velocity**: short‑window change; **Acceleration**: change of change.
- **Z‑score**: (value − mean)/stdev per window; **Rank**: ordinal within G‑10/selected set.

### 25.3 Sub‑indicators
- Windowed strengths for **15m/1h/4h/8h/12h/24h**.
- Cross‑window consensus (e.g., majority strong/weak), divergence flags, and reversal candidates.

### 25.4 Signals & probability integration
- Emits normalized signals with optional `p`/`n` from Conditional Probability Engine when enabled; maps to **Signals** and **Live** tabs.

### 25.5 Controls & validation
- Select currency universe, windows, normalization; validation on required feed symbols and minimum sample points.

### 25.6 Filters & actions
- Filter by currency, min z‑score/strength, divergence type; actions to pin signals or open linked charts.

### 25.7 KPIs & history
- Top movers, persistence score, reversal hit‑rate; export KPIs.

### 25.8 Acceptance criteria
- Updates < 2s after incoming ticks; table and sparklines virtualized for large universes; numeric stability across sparse windows.

### 25.9 UI widgets (sortable table & sparkline)
- Sortable table with per‑row sparklines; tooltips show raw/normalized values and contributing pairs.

### 25.10 Fixed windows & layout
- Fixed columns for 15m/1h/4h/8h/12h/24h; responsive layout with sticky header and horizontal scroll.

### 25.11 Controls & actions (buttons)
- **Toggle windows** — show/hide columns 15m/1h/4h/8h/12h/24h (tid:`cs_toggle_windows`).
- **Export table** — CSV/JSON with strength/%‑change (tid:`cs_export_table`).
- **Toggle sparkline** — per‑row micro‑trend on/off (tid:`cs_toggle_spark`).
- **Pin signals** (row) — send to Live (tid:`cs_pin_live`).
- **Set alerts** — open thresholds dialog for strength/z‑score (tid:`cs_set_alerts`).


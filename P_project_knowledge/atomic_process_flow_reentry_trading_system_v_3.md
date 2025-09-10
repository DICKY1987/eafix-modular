# Atomic Process Flow — Reentry Trading System (v3.0)

**Date:** 2025-08-21  
**Actors:** `PY` (Python), `EA` (MT4 Expert Advisor), `BR` (CSV Bridge), `FS` (Filesystem)  
**Transport:** CSV-only (`Common\Files\reentry\...`)  
**ID Conventions:** See Matrix Grammar in Canonical Spec (Canvas)

**Legend:** Each step is atomic (one action). Conditional flow uses `IF/ELSE` with explicit `GOTO` targets.

---

## 0.000 — System Bootstrap (One-Time on Service Start)

- **0.001 (PY)** — Load `Common\\Files\\reentry\\config\\parameters.schema.json` into memory.
- **0.002 (PY)** — Validate schema self-integrity (`$id`, `$schema` fields present). If fail → log local error and **GOTO 11.010**.
- **0.003 (PY)** — Ensure directories exist:  
  `Common\\Files\\reentry\\bridge`, `...\\logs`, `...\\config`, `...\\data`. Create if missing.
- **0.004 (PY)** — Open append handles (with retry) for:  
  `bridge\\trading_signals.csv`, `bridge\\trade_responses.csv` (read tail), `logs\\parameter_log.csv`.
- **0.005 (PY)** — Initialize offsets: `last_read_offset_responses=EOF`.
- **0.006 (PY)** — Load `config\\matrix_map.csv` into memory (hash→cache). If missing → create empty file with header.
- **0.007 (PY)** — Initialize health timers: `heartbeat_tx_due_in=30s`, `heartbeat_rx_timeout=90s`.

---

## 1.000 — Economic Calendar Ingestion (Hourly From Sunday 12:00 Local)

- **1.001 (PY)** — At scheduler tick, scan `%USERPROFILE%\\Downloads` for newest `economic_calendar*.csv`/`.xlsx`.
- **1.002 (PY/FS)** — If none found **GOTO 1.010**. Else copy-as-new to `data\\economic_calendar_raw_YYYYMMDD_HHMMSS.ext` (write→fsync→rename atomic).
- **1.003 (PY)** — Compute SHA-256 of raw file; compare with `data\\economic_calendar_raw.latest.sha256`. If identical **GOTO 1.010**.
- **1.004 (PY)** — Transform raw → normalized rows: columns `[timestamp_utc, currency, impact, title, actual, forecast, previous]`.
- **1.005 (PY)** — **Filter**: keep only `impact ∈ {HIGH, MED}`.
- **1.006 (PY)** — **Inject weekly recurring events** (session opens, etc.): resolve weekday-only entries to the **next concrete date** in the target week.
- **1.007 (PY)** — **Add anticipation rows** for each event: `ANTICIPATION_1HR`, `ANTICIPATION_8HR` at `event_time - {60, 480} minutes`.
- **1.008 (PY)** — **Chronologically sort** all rows (anticipation + events) by `timestamp_utc`.
- **1.009 (PY/FS)** — Write `data\\economic_calendar.csv` (tmp→fsync→rename). Update `.latest.sha256`.
- **1.010 (PY)** — Update in-memory `calendar_index` (time-keyed) for fast lookups.

---

## 2.000 — Signal Detection & Debounce (Continuous Loop)

- **2.001 (PY)** — Read `now_utc`. Query `calendar_index` for rows within detection windows.
- **2.002 (PY)** — Build candidate signals: `ECO_HIGH`, `ECO_MED`, `ANTICIPATION_1HR`, `ANTICIPATION_8HR`, `EQUITY_OPEN_*`, `ALL_INDICATORS` (if enabled).
- **2.003 (PY)** — Debounce: drop duplicates already emitted in last `N` minutes per `(symbol, signal, event_id)` key.
- **2.004 (PY)** — For each candidate, compute **proximity bucket**: `IMMEDIATE/SHORT/LONG/EXTENDED` based on time to (or since) event.
- **2.005 (PY)** — For **original generation** (`O`), set `outcome=SKIP` by convention (no prior outcome).
- **2.006 (PY)** — For ECO signals at **reentry generations** (`R1/R2`), compute **duration category** (`FLASH/QUICK/LONG/EXTENDED`) from the **previous leg’s open→close minutes**.
- **2.007 (PY)** — Compose `combination_id` per grammar (include duration **only** when ECO and gen∈{R1,R2}).
- **2.008 (PY)** — Emit internal event: `NEW_SIGNAL_READY(symbol, combination_id, context)`.

---

## 3.000 — Matrix Routing & Parameter Resolution

- **3.001 (PY)** — Lookup `combination_id` in `matrix_map.csv`.
- **3.002 (PY)** — If **not found**, route to default rule: `parameter_set_id = PS-default`, `next_decision = CONTINUE` and log warning.
- **3.003 (PY)** — If mapping exists and `next_decision == END_TRADING`, mark chain terminal for `(symbol, event_id)` and **GOTO 9.010**.
- **3.004 (PY)** — Load parameter template for `parameter_set_id`.
- **3.005 (PY)** — Apply dynamic overlays (symbol/session/volatility multipliers) if configured.
- **3.006 (PY)** — Compute `effective_risk = min(global_risk_percent * risk_multiplier, 3.50)`.
- **3.007 (PY)** — Validate parameter JSON against `parameters.schema.json`.
- **3.008 (PY)** — If validation fails, record local error and **GOTO 4.010** with `action=UPDATE_PARAMS` + marked invalid (expect `REJECT_SET`).

---

## 4.000 — Emit to Bridge (Python → EA)

- **4.001 (PY)** — Build `json_payload` (pretty-compact) for `UPDATE_PARAMS`.
- **4.002 (PY)** — Compute `json_payload_sha256`.
- **4.003 (PY/FS)** — Append one CSV row to `bridge\\trading_signals.csv` with fields:  
  `version,timestamp_utc,symbol,combination_id,action=UPDATE_PARAMS,parameter_set_id,json_payload_sha256,json_payload` (atomic append semantics).
- **4.004 (PY)** — Immediately append a second row `action=TRADE_SIGNAL` with minimal `signal_context` (reason, event_id) **only if** strategy dictates entry.
- **4.005 (PY)** — Start response timer `awaiting_ack_ttl=10s`.
- **4.006 (PY)** — **GOTO 5.001** to await EA responses.
- **4.010 (PY)** — (From 3.008) Emit `UPDATE_PARAMS` anyway for visibility; set `detail_json.reason="pre-validated-fail"`. **GOTO 5.001**.

---

## 5.000 — Consume Responses (EA ↔ Python)

- **5.001 (PY/FS)** — Tail-read new lines from `bridge\\trade_responses.csv` since `last_read_offset_responses`.
- **5.002 (PY)** — For each line, parse CSV → JSON. If partial/incomplete, **skip** until newline completes.
- **5.003 (PY)** — Match by `(symbol, combination_id, action)` to correlate outstanding requests.
- **5.004 (PY)** — If `action=ACK_UPDATE && status=OK`, clear `awaiting_ack_ttl`.
- **5.005 (PY)** — If `action=REJECT_SET`, record schema/EA code; decide whether to **halt** or **fallback parameter_set_id** per policy; **GOTO 9.001**.
- **5.006 (PY)** — If `action=ACK_TRADE`, store `order_ids` and start trade lifecycle monitor.
- **5.007 (PY)** — If `action=REJECT_TRADE`, record and **GOTO 9.001**.

---

## 6.000 — EA Side: Validation & Acknowledgement (On Every UPDATE_PARAMS)

- **6.001 (EA)** — Detect new line in `trading_signals.csv` (poll every 2–5s).
- **6.002 (EA)** — Parse row; verify `version==3.0`. If mismatch, **emit** `REJECT_SET` with `ea_code=E0000` and **RETURN**.
- **6.003 (EA)** — Validate JSON against embedded mirror of `parameters.schema.json`.
- **6.004 (EA)** — Compute `effective_risk` from inputs; ensure `≤ 3.50`. If violated → `REJECT_SET (E1001)`.
- **6.005 (EA)** — If `take_profit_method=FIXED`, require `take_profit_pips > stop_loss_pips` else `REJECT_SET (E1012)`.
- **6.006 (EA)** — Range-check ATR fields when method is ATR; else `REJECT_SET (E1020)`.
- **6.007 (EA)** — Clamp soft fields (e.g., retries, timeouts) and note warnings `W200*`.
- **6.008 (EA/FS)** — Append `ACK_UPDATE` to `trade_responses.csv` with `status=OK` or `ERROR` and any `ea_code`.

---

## 7.000 — EA Side: Order Workflow (On TRADE_SIGNAL)

- **7.001 (EA)** — Evaluate time/news gates (`eco_cutoff_minutes_*`). If blocked → `REJECT_TRADE (E1040)`.
- **7.002 (EA)** — Derive lot size from `effective_risk` and symbol contract; round to broker step.
- **7.003 (EA)** — If `entry_order_type=MARKET`, send market order with `sl/tp` per methods; honor `market_slippage_tolerance`.
- **7.004 (EA)** — If `STRADDLE`, place **both** pending orders at configured distances.
- **7.005 (EA)** — If `BUY_STOP_ONLY` or `SELL_STOP_ONLY`, place respective pending order.
- **7.006 (EA)** — If any order send fails, obey retry policy (`order_retry_attempts`, `order_retry_delay_ms`). On repeated fail → `REJECT_TRADE (E1050)`.
- **7.007 (EA/FS)** — Append `ACK_TRADE` with `order_ids` to `trade_responses.csv`.

---

## 8.000 — EA Side: Post-Entry Management

- **8.001 (EA)** — If `straddle_auto_cancel_opposite=true` and one leg fills, cancel the opposite pending.
- **8.002 (EA)** — Enforce `pending_order_timeout_min`: delete stale pending; append `CANCELLED` response with reason.
- **8.003 (EA)** — Apply trailing rules when enabled; update SL accordingly (internal, no CSV spam).
- **8.004 (EA/FS)** — On close (manual/SL/TP): append `ACK_TRADE` with `detail_json={result: WIN|LOSS|BE, pips: N, minutes_open: M}`.
- **8.005 (EA/FS)** — Echo parameter snapshot to `logs\\parameter_log.csv`.

---

## 9.000 — Chain Progression & Outcome Propagation

- **9.001 (PY)** — On receive `ACK_TRADE` with final outcome, compute **next generation**: `O→R1`, `R1→R2`, `R2→terminal`.
- **9.002 (PY)** — For ECO signals, derive **duration category** from `minutes_open` (FLASH 0–15, QUICK 16–60, LONG 61–480, EXTENDED >480).
- **9.003 (PY)** — Compose next `combination_id` using **previous leg outcome** and (for ECO) computed **duration**.
- **9.004 (PY)** — **IF** next gen is `R3` (would exceed cap) → mark terminal and **GOTO 9.010**.
- **9.005 (PY)** — **GOTO 3.001** to resolve parameters for the next leg.
- **9.010 (PY)** — Mark chain **CLOSED**; stop emitting further signals for `(symbol,event_id)`.

---

## 10.000 — Heartbeat & Health Monitoring

- **10.001 (PY)** — Every 30s append `HEARTBEAT` row to `trading_signals.csv`.
- **10.002 (EA)** — On read heartbeat, append `HEARTBEAT` echo to `trade_responses.csv`.
- **10.003 (PY)** — If no heartbeat echo within `heartbeat_rx_timeout`, raise alert and **GOTO 11.020**.

---

## 11.000 — Error Handling & Recovery

- **11.001 (PY)** — On CSV parse error (partial line), **skip** until newline; do not crash loop.
- **11.002 (PY/FS)** — On file lock failure, backoff (250–1000ms jitter) and retry up to 10 times.
- **11.003 (PY)** — On `REJECT_SET`, log `ea_code` and decide policy: (a) halt chain, (b) switch to `PS-failsafe`, or (c) request human review.
- **11.004 (PY)** — On `REJECT_TRADE`, record outcome as `REJECT`; proceed to **9.003** for next-gen logic if policy allows.
- **11.005 (EA)** — On broker error (trade context busy, off quotes), apply retry policy; otherwise emit `REJECT_TRADE (E105x)`.
- **11.006 (PY)** — If `bridge\\trade_responses.csv` grows beyond size threshold, **GOTO 12.001** (rotation).
- **11.010 (PY)** — (From 0.002) Attempt to regenerate JSON Schema from YAML (if available). If still failing, set service state `DEGRADED` and continue with last-known-good.
- **11.020 (PY)** — Health alert: escalate to notification channel; increase polling to detect recovery; no destructive action.

---

## 12.000 — Log & Data Rotation

- **12.001 (PY/FS)** — At UTC midnight or size>100MB, rotate `trading_signals.csv` and `trade_responses.csv`: close → rename with date suffix → compress (`.gz`).
- **12.002 (PY)** — Write fresh header lines to new CSVs.
- **12.003 (PY/FS)** — Purge archives older than retention (e.g., 30 days).

---

## 13.000 — Graceful Shutdown / Restart

- **13.001 (PY)** — Flush and close open file handles.
- **13.002 (EA)** — Finish in-flight validations; stop polling after final heartbeat.
- **13.003 (PY)** — Persist checkpoints: `last_read_offset_responses`, chain states, open orders map.
- **13.004 (PY)** — On restart, resume from checkpoints; re-emit `HEARTBEAT` and verify EA echo.

---

## 14.000 — Test Cues (Atomic)

- **14.001 (TEST)** — Inject invalid `global_risk_percent=5.0` → expect `REJECT_SET (E1001)`.
- **14.002 (TEST)** — Send `SL=50` & `TP=30` (FIXED) → expect `REJECT_SET (E1012)`.
- **14.003 (TEST)** — ATR period `2` → expect `REJECT_SET (E1020)`.
- **14.004 (TEST)** — Pending timeout `0` → expect clamp + `W2003`.
- **14.005 (TEST)** — Attempt `R3` progression → expect `REJECT_TRADE (E1030)` and chain terminal.

---

## Appendix A — File Paths & Headers (for quick reference)

- `bridge\\trading_signals.csv`  
  `version,timestamp_utc,symbol,combination_id,action,parameter_set_id,json_payload_sha256,json_payload`

- `bridge\\trade_responses.csv`  
  `version,timestamp_utc,symbol,combination_id,action,status,ea_code,detail_json`

- `logs\\parameter_log.csv`  
  `version,timestamp_utc,symbol,parameter_set_id,effective_risk,sl,sl_units,tp,tp_units,entry_order_type,trail_method,breakeven,notes`



---

## 15.000 — Owner & SLA Matrix (All Steps)

> SLA = target max completion time **after the step is triggered** (not poll interval). Owners reflect the actor in parentheses: PY=Python, EA=Expert Advisor, FS=Filesystem, BR=CSV Bridge, TEST=QA. Combined entries indicate primary owner (first) with dependency in parentheses.

| Step — Action | Owner / SLA |
|---|---|
| 0.001 — Load parameters.schema.json | PY • 500ms |
| 0.002 — Validate schema self-integrity | PY • 200ms |
| 0.003 — Ensure directory tree exists | PY (FS) • 1s |
| 0.004 — Open append/tail handles | PY (FS) • 1s |
| 0.005 — Initialize offsets | PY • 50ms |
| 0.006 — Load matrix_map.csv | PY (FS) • 500ms |
| 0.007 — Init health timers | PY • 50ms |
| 1.001 — Scan Downloads for new calendar | PY (FS) • 1s |
| 1.002 — Copy raw calendar to /data (atomic) | PY (FS) • 500ms |
| 1.003 — Hash raw file & compare | PY • 300ms |
| 1.004 — Transform raw→normalized | PY • 2s |
| 1.005 — Filter to HIGH/MED | PY • 200ms |
| 1.006 — Resolve weekly recurring events to dates | PY • 500ms |
| 1.007 — Inject ANTICIPATION rows | PY • 300ms |
| 1.008 — Chronologically sort | PY • 300ms |
| 1.009 — Write economic_calendar.csv (atomic) | PY (FS) • 300ms |
| 1.010 — Update in-memory calendar index | PY • 200ms |
| 2.001 — Read now_utc & query windows | PY • 50ms |
| 2.002 — Build candidate signals | PY • 100ms |
| 2.003 — Debounce duplicates | PY • 100ms |
| 2.004 — Compute proximity bucket | PY • 50ms |
| 2.005 — Set outcome=SKIP for O-gen | PY • 10ms |
| 2.006 — Compute ECO duration from prior leg | PY • 50ms |
| 2.007 — Compose combination_id | PY • 10ms |
| 2.008 — Emit NEW_SIGNAL_READY | PY • 10ms |
| 3.001 — Lookup combination_id in matrix_map | PY • 20ms |
| 3.002 — Apply default when missing | PY • 20ms |
| 3.003 — END_TRADING short-circuit | PY • 10ms |
| 3.004 — Load parameter template | PY (FS/cache) • 50ms |
| 3.005 — Apply dynamic overlays | PY • 30ms |
| 3.006 — Compute effective_risk | PY • 5ms |
| 3.007 — Validate parameter JSON vs schema | PY • 30ms |
| 3.008 — Mark invalid & route for visibility | PY • 10ms |
| 4.001 — Build json_payload | PY • 20ms |
| 4.002 — Compute SHA-256 | PY • 20ms |
| 4.003 — Append UPDATE_PARAMS row | PY (FS) • 50ms |
| 4.004 — Append TRADE_SIGNAL row (if entry) | PY (FS) • 50ms |
| 4.005 — Start response timer | PY • 10ms |
| 4.006 — Await responses | PY • N/A (event-driven) |
| 4.010 — Emit invalid UPDATE_PARAMS for visibility | PY (FS) • 50ms |
| 5.001 — Tail-read trade_responses.csv | PY (FS) • 50ms |
| 5.002 — Parse CSV lines | PY • 5ms |
| 5.003 — Correlate by (symbol, combo, action) | PY • 10ms |
| 5.004 — ACK_UPDATE OK → clear timer | PY • 5ms |
| 5.005 — REJECT_SET handling | PY • 50ms |
| 5.006 — ACK_TRADE store order_ids | PY • 10ms |
| 5.007 — REJECT_TRADE handling | PY • 50ms |
| 6.001 — Detect new line in trading_signals (poll) | EA • SLA: ≤5s detection |
| 6.002 — Verify version | EA • 5ms |
| 6.003 — Validate JSON vs schema mirror | EA • 50ms |
| 6.004 — Enforce risk cap | EA • 5ms |
| 6.005 — Enforce TP>SL when FIXED | EA • 5ms |
| 6.006 — Range-check ATR fields | EA • 10ms |
| 6.007 — Clamp soft fields (retries/timeouts) | EA • 5ms |
| 6.008 — Append ACK_UPDATE/ERROR | EA (FS) • 50ms |
| 7.001 — Evaluate time/news gates | EA • 10ms |
| 7.002 — Derive lot size from effective_risk | EA • 5ms |
| 7.003 — Place MARKET order (if applicable) | EA • Broker latency-dependent (target ≤500ms) |
| 7.004 — Place STRADDLE pending orders | EA • Broker latency-dependent (target ≤800ms) |
| 7.005 — Place single pending order | EA • Broker latency-dependent (target ≤500ms) |
| 7.006 — Apply retry policy on send failures | EA • Per policy (≤ order_retry_attempts × delay) |
| 7.007 — Append ACK_TRADE with order_ids | EA (FS) • 50ms |
| 8.001 — Auto-cancel opposite straddle leg | EA • 300ms |
| 8.002 — Timeout stale pending → cancel | EA • ≤ 5s from timeout point |
| 8.003 — Apply trailing rules | EA • 10ms per tick |
| 8.004 — On close, append result | EA (FS) • 100ms |
| 8.005 — Echo parameter snapshot to log | EA (FS) • 50ms |
| 9.001 — Compute next generation | PY • 10ms |
| 9.002 — Derive ECO duration from minutes_open | PY • 10ms |
| 9.003 — Compose next combination_id | PY • 10ms |
| 9.004 — Prevent R3 (cap at R2) | PY • 5ms |
| 9.005 — Route back to mapping | PY • 5ms |
| 9.010 — Mark chain CLOSED | PY • 10ms |
| 10.001 — Send HEARTBEAT row | PY (FS) • 50ms |
| 10.002 — Echo HEARTBEAT | EA (FS) • 50ms (≤5s from read) |
| 10.003 — Detect heartbeat timeout | PY • 10ms (≤90s from last echo) |
| 11.001 — Skip partial CSV line | PY • 1ms |
| 11.002 — Backoff & retry file lock | PY (FS) • per backoff (≤10s total) |
| 11.003 — REJECT_SET policy decision | PY • 50ms |
| 11.004 — REJECT_TRADE policy decision | PY • 50ms |
| 11.005 — Broker error → retries / reject | EA • per policy |
| 11.006 — Trigger log rotation threshold | PY (FS) • 100ms |
| 11.010 — Regenerate schema from YAML | PY • 1s |
| 11.020 — Health alert escalation | PY • 500ms |
| 12.001 — Rotate CSVs & compress | PY (FS) • 2s |
| 12.002 — Write fresh headers | PY (FS) • 100ms |
| 12.003 — Purge old archives | PY (FS) • 1s |
| 13.001 — Flush/close handles | PY • 300ms |
| 13.002 — EA finish inflight & stop poll | EA • ≤5s |
| 13.003 — Persist checkpoints | PY • 300ms |
| 13.004 — Resume & verify heartbeat | PY • 1s |
| 14.001 — TEST invalid risk → E1001 | TEST • 2s |
| 14.002 — TEST TP≤SL → E1012 | TEST • 2s |
| 14.003 — TEST ATR period 2 → E1020 | TEST • 2s |
| 14.004 — TEST timeout clamp → W2003 | TEST • 2s |
| 14.005 — TEST R3 progression → E1030 | TEST • 2s |


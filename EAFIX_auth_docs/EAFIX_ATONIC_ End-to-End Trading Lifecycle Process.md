# HUEY_P / EAFIX End-to-End Trading Lifecycle Process
## Atomic Step-by-Step Operational Blueprint

---

## **PHASE 1: ECONOMIC CALENDAR INTAKE**

### **Step 1: Calendar Source Discovery**
- **Responsible:** `calendar_service.py`
- **Input:** Configuration file (`calendar_sources.yaml`)
- **Output:** Active source endpoints list
- **Validation:** Source availability check (HTTP 200), SSL validity
- **Failure:** Log unavailable source, fallback to secondary source if configured, else alert and skip polling cycle

### **Step 2: Calendar Data Polling**
- **Responsible:** `calendar_service.py::poll_scheduler`
- **Input:** Active source endpoints, last poll timestamp
- **Output:** Raw calendar JSON/XML response
- **Validation:** Response size > 0, valid JSON/XML structure, timestamp freshness
- **Failure:** Retry 3x with exponential backoff (2s, 4s, 8s), then log failure and skip cycle

### **Step 3: Raw Calendar Parsing**
- **Responsible:** `calendar_service.py::parse_raw_calendar`
- **Input:** Raw calendar response
- **Output:** List of raw event dictionaries
- **Validation:** Required fields present (datetime, currency, impact, event_name), datetime parsable
- **Failure:** Discard malformed events individually, log parsing errors, continue with valid events

### **Step 4: Event Normalization**
- **Responsible:** `calendar_service.py::normalize_events`
- **Input:** Raw event dictionaries
- **Output:** Normalized event objects (ISO 8601 timestamp, standardized impact levels, sanitized event names)
- **Validation:** Impact level in [HIGH, MEDIUM, LOW], timezone conversion success, duplicate timestamp+currency check
- **Failure:** Demote unparseable events to UNKNOWN impact, log anomalies

### **Step 5: CAL8 Identifier Assignment**
- **Responsible:** `calendar_service.py::assign_cal8`
- **Input:** Normalized event objects
- **Output:** Event objects with unique CAL8 ID (format: `CAL8-YYYYMMDD-HHMM-CCC-NNN`)
- **Validation:** CAL8 uniqueness check against existing registry, no collisions
- **Failure:** If collision detected, append incremental suffix (-001, -002), alert on >10 collisions/day

### **Step 6: Calendar Registry Update**
- **Responsible:** `calendar_service.py::update_registry`
- **Input:** CAL8-tagged events
- **Output:** Updated `calendar_registry.db` (append-only SQLite table)
- **Validation:** Transaction commit success, foreign key integrity
- **Failure:** Rollback transaction, log database error, retry once, then halt calendar intake cycle

### **Step 7: Calendar CSV Artifact Creation**
- **Responsible:** `calendar_service.py::write_calendar_csv`
- **Input:** CAL8-tagged events
- **Output:** `calendar_YYYYMMDD.csv` in `DATA/calendar/` directory
- **Validation:** File write success, row count matches event count, CSV parsable
- **Failure:** Retry write once, alert on persistent failure, continue without CSV (DB is source of truth)

### **Step 8: Calendar Signal Emission**
- **Responsible:** `calendar_service.py::emit_signals`
- **Input:** CAL8-tagged events
- **Output:** Internal message queue event (`calendar.event.registered`)
- **Validation:** Message queue acknowledgment received
- **Failure:** Buffer event locally, attempt re-emission on next cycle, alert if buffer >100 events

---

## **PHASE 2: CALENDAR ANTICIPATION & TRIGGERING**

### **Step 9: Event Proximity Window Calculation**
- **Responsible:** `calendar_anticipator.py::calculate_windows`
- **Input:** Current system time, calendar registry events
- **Output:** Events segmented into PRE (-30min to -5min), AT (-5min to +5min), POST (+5min to +60min) windows
- **Validation:** Event timestamp in future or recent past (<60min), no NaT timestamps
- **Failure:** Discard events with invalid timestamps, continue with valid events

### **Step 10: Symbol Impact Resolution**
- **Responsible:** `calendar_anticipator.py::resolve_symbol_impact`
- **Input:** Windowed events, currency-to-symbol mapping table
- **Output:** Affected symbol list per event (e.g., USD event → EURUSD, GBPUSD, USDJPY)
- **Validation:** Symbol mapping table non-empty, currency code exists in mapping
- **Failure:** If unmapped currency, assign conservative impact to major pairs, log unknown currency

### **Step 11: Signal TTL and Freshness Validation**
- **Responsible:** `calendar_anticipator.py::validate_freshness`
- **Input:** Windowed events with timestamps
- **Output:** Events marked FRESH or STALE
- **Validation:** Event timestamp within configured TTL (default: events >60min old marked STALE)
- **Failure:** STALE events excluded from further processing, logged for audit

### **Step 12: High-Impact Event Suppression Logic**
- **Responsible:** `calendar_anticipator.py::apply_suppression_rules`
- **Input:** FRESH events with impact levels
- **Output:** Suppression flags (SUPPRESS_TRADING, REDUCE_SIZE, ALLOW)
- **Validation:** Impact level = HIGH and window = AT → SUPPRESS_TRADING
- **Failure:** If rule engine fails, default to SUPPRESS_TRADING for safety, alert

### **Step 13: Calendar Context Signal Creation**
- **Responsible:** `calendar_anticipator.py::create_context_signal`
- **Input:** Windowed events with suppression flags
- **Output:** `CalendarContextSignal` objects (CAL8 ID, symbol list, window type, suppression flag, timestamp)
- **Validation:** Schema validation (all required fields present), no duplicate CAL8 IDs in same window
- **Failure:** Discard malformed signals, log validation errors

---

## **PHASE 3: SIGNAL GENERATION & CONTEXT ASSEMBLY**

### **Step 14: Market State Acquisition**
- **Responsible:** `market_state_service.py::get_current_state`
- **Input:** Symbol list from calendar context
- **Output:** Current OHLC, spread, volatility, trend for each symbol
- **Validation:** Quote timestamp <5 seconds old, bid/ask spread <max allowed
- **Failure:** If stale quotes, skip symbol from signal generation, log data feed issue

### **Step 15: Hybrid Context Construction**
- **Responsible:** `signal_generator.py::build_hybrid_context`
- **Input:** `CalendarContextSignal` + market state
- **Output:** `HybridContext` object (calendar data + market data + metadata)
- **Validation:** Both calendar and market components present, timestamp alignment within 1 minute
- **Failure:** If timestamp misalignment, discard context, log synchronization error

### **Step 16: Direction Determination**
- **Responsible:** `signal_generator.py::determine_direction`
- **Input:** `HybridContext` object
- **Output:** Direction flag (LONG, SHORT, NEUTRAL)
- **Validation:** Trend strength above threshold, volatility within acceptable range
- **Failure:** If indeterminate, output NEUTRAL and skip trade signal generation

### **Step 17: Normalized Signal Object Creation**
- **Responsible:** `signal_generator.py::create_signal`
- **Input:** `HybridContext` + direction
- **Output:** `TradeSignal` object (SIG8 ID, CAL8 ID, symbol, direction, entry_price, SL, TP, lot_size, timestamp)
- **Validation:** SIG8 uniqueness, SL/TP spread ratios valid, lot_size >0
- **Failure:** Reject signal if validation fails, log detailed error, halt signal for this symbol

### **Step 18: Signal Schema Validation**
- **Responsible:** `signal_generator.py::validate_schema`
- **Input:** `TradeSignal` object
- **Output:** VALID or INVALID flag
- **Validation:** All required fields present, data types correct, business rules satisfied (e.g., TP > entry for LONG)
- **Failure:** INVALID signals discarded, logged with detailed reason

### **Step 19: Signal Deduplication Check**
- **Responsible:** `signal_generator.py::check_duplicates`
- **Input:** `TradeSignal` object, signal registry
- **Output:** UNIQUE or DUPLICATE flag
- **Validation:** SIG8 ID not in registry, (symbol + direction + timestamp) combination unique within 5 minutes
- **Failure:** DUPLICATE signals discarded, log duplicate detection

### **Step 20: Signal Registry Append**
- **Responsible:** `signal_generator.py::append_to_registry`
- **Input:** VALID and UNIQUE `TradeSignal`
- **Output:** Updated `signal_registry.db` (append-only)
- **Validation:** DB transaction success, foreign key to calendar registry
- **Failure:** Rollback, retry once, halt signal processing if persistent failure

---

## **PHASE 4: RISK & PORTFOLIO GATING (HARD STOP POINTS)**

### **Step 21: Per-Symbol Position Limit Check**
- **Responsible:** `risk_manager.py::check_symbol_limits`
- **Input:** `TradeSignal`, current open positions registry
- **Output:** PASS or BLOCK_SYMBOL_LIMIT
- **Validation:** Current open positions for symbol < max_positions_per_symbol (default: 1)
- **Failure:** BLOCK outcome recorded, signal marked NO_TRADE, logged, process halts for this signal

### **Step 22: Portfolio Exposure Limit Check**
- **Responsible:** `risk_manager.py::check_portfolio_exposure`
- **Input:** `TradeSignal`, portfolio exposure registry
- **Output:** PASS or BLOCK_PORTFOLIO_LIMIT
- **Validation:** Total portfolio exposure (sum of all open position lot sizes) + new signal lot size < max_portfolio_exposure
- **Failure:** BLOCK outcome, signal marked NO_TRADE, logged, process halts

### **Step 23: Circuit Breaker Evaluation**
- **Responsible:** `risk_manager.py::evaluate_circuit_breakers`
- **Input:** `TradeSignal`, recent P&L history
- **Output:** PASS or BLOCK_CIRCUIT_BREAKER
- **Validation:** Not in daily loss limit breach state, consecutive loss count < threshold
- **Failure:** BLOCK outcome, ALL trading halted, alert sent, process terminates

### **Step 24: Idempotency / Duplicate Order Prevention**
- **Responsible:** `risk_manager.py::check_idempotency`
- **Input:** `TradeSignal`, execution registry
- **Output:** PASS or BLOCK_DUPLICATE
- **Validation:** SIG8 ID not in execution registry, no pending execution for same signal
- **Failure:** BLOCK outcome, signal marked DUPLICATE_EXECUTION, logged, process halts

### **Step 25: Explicit Trade Authorization Record**
- **Responsible:** `risk_manager.py::record_authorization`
- **Input:** `TradeSignal` that passed all gates
- **Output:** Authorization record in `execution_authorization.db` (SIG8 ID, timestamp, authorization_hash)
- **Validation:** Unique authorization hash generated, DB commit success
- **Failure:** No authorization record = no execution, retry DB write once, then halt

---

## **PHASE 5: TRANSPORT FROM PYTHON → MT (EXECUTION PATH)**

### **Step 26: Execution CSV Row Construction**
- **Responsible:** `transport_service.py::build_execution_row`
- **Input:** Authorized `TradeSignal`
- **Output:** CSV row string (SIG8,SYMBOL,DIRECTION,ENTRY,SL,TP,LOTS,TIMESTAMP,HASH)
- **Validation:** All fields non-empty, numeric fields parsable, hash computed correctly
- **Failure:** If row construction fails, log error, signal moved to FAILED_TRANSPORT state

### **Step 27: Execution CSV File Append**
- **Responsible:** `transport_service.py::append_to_execution_csv`
- **Input:** Execution CSV row
- **Output:** Updated `execution_queue.csv` in `DATA/MT_BRIDGE/`
- **Validation:** File write success, file lock acquired/released, row count incremented
- **Failure:** Retry write 3x, if all fail, buffer locally and alert, signal marked TRANSPORT_FAILED

### **Step 28: Transport Integrity Hash Computation**
- **Responsible:** `transport_service.py::compute_transport_hash`
- **Input:** Complete `execution_queue.csv` content
- **Output:** SHA256 hash written to `execution_queue.csv.hash`
- **Validation:** Hash file written successfully
- **Failure:** Retry hash write once, continue without hash (EA will detect missing hash)

### **Step 29: Transport Sequence Number Update**
- **Responsible:** `transport_service.py::update_sequence`
- **Input:** Current sequence number
- **Output:** Incremented sequence in `transport_sequence.txt`
- **Validation:** Sequence monotonically increasing, no gaps
- **Failure:** If sequence file corrupt, reinitialize from last known good state, alert

### **Step 30: Transport Heartbeat Emission**
- **Responsible:** `transport_service.py::emit_heartbeat`
- **Input:** Current timestamp
- **Output:** `heartbeat.txt` with ISO timestamp
- **Validation:** Heartbeat timestamp within last 10 seconds
- **Failure:** If heartbeat write fails, alert, continue (EA monitors heartbeat staleness)

### **Step 31: EA Polling Detection (Passive Wait)**
- **Responsible:** External (EA reads CSV), Python observes file lock/modification
- **Input:** File system events on `execution_queue.csv`
- **Output:** Lock release detection
- **Validation:** Lock held by EA <30 seconds
- **Failure:** If lock timeout, alert possible EA hang, do not modify file

---

## **PHASE 6: MT / EA TRADE EXECUTION**

### **Step 32: EA Pre-Flight CSV Read**
- **Responsible:** `EAFIX.mq4::ReadExecutionQueue()`
- **Input:** `execution_queue.csv`
- **Output:** Array of execution instructions in EA memory
- **Validation:** CSV parsable, hash matches, sequence number incremented
- **Failure:** If hash mismatch or parse error, reject entire file, log error, skip execution cycle

### **Step 33: EA Signal-Level Validation**
- **Responsible:** `EAFIX.mq4::ValidateSignal()`
- **Input:** Individual signal from execution array
- **Output:** VALID or INVALID per signal
- **Validation:** Symbol exists, lot size within broker limits, SL/TP within max distance
- **Failure:** INVALID signals logged, skipped, remainder processed

### **Step 34: EA Order Placement**
- **Responsible:** `EAFIX.mq4::PlaceOrder()`
- **Input:** Validated signal
- **Output:** MT4 OrderSend() call, returns ticket number or error code
- **Validation:** Ticket number >0, order visible in terminal
- **Failure:** Log MT4 error code, classify error (retriable vs terminal), retry if retriable (max 3x)

### **Step 35: EA Execution Confirmation Write**
- **Responsible:** `EAFIX.mq4::WriteExecutionResult()`
- **Input:** Order ticket, SIG8 ID, execution status (SUCCESS/FAILED)
- **Output:** Row appended to `execution_results.csv`
- **Validation:** Row write success, file accessible
- **Failure:** Buffer result in EA memory, retry write on next tick, alert if buffer >50 results

### **Step 36: EA Error Classification**
- **Responsible:** `EAFIX.mq4::ClassifyError()`
- **Input:** MT4 error code
- **Output:** Error category (RETRIABLE, TERMINAL, BROKER_REJECT)
- **Validation:** Error code in known error map
- **Failure:** Unknown errors classified as TERMINAL for safety

### **Step 37: EA Retry or Abort Logic**
- **Responsible:** `EAFIX.mq4::RetryOrAbort()`
- **Input:** Error category, retry count
- **Output:** RETRY or ABORT decision
- **Validation:** Retry count <3, error is RETRIABLE
- **Failure:** ABORT triggers immediate write to execution_results.csv with ABORTED status

---

## **PHASE 7: TRADE RESULT CAPTURE (MT → PYTHON)**

### **Step 38: Position Monitoring (EA Continuous)**
- **Responsible:** `EAFIX.mq4::MonitorPositions()`
- **Input:** Open position tickets
- **Output:** Position state (OPEN, CLOSED_TP, CLOSED_SL, CLOSED_MANUAL)
- **Validation:** Position still exists in terminal
- **Failure:** If position disappears unexpectedly, log phantom close, record as CLOSED_UNKNOWN

### **Step 39: Trade Close Detection**
- **Responsible:** `EAFIX.mq4::OnTradeClose()`
- **Input:** Closed position ticket
- **Output:** Close detection flag
- **Validation:** Position no longer in open positions list, close time populated
- **Failure:** N/A (close detection is event-driven)

### **Step 40: P&L Computation**
- **Responsible:** `EAFIX.mq4::ComputePnL()`
- **Input:** Closed position ticket
- **Output:** Realized P&L in account currency
- **Validation:** P&L = (close_price - open_price) * lot_size * point_value * direction_multiplier
- **Failure:** If computation fails, log error, record P&L as 0 with flag COMPUTATION_ERROR

### **Step 41: Duration Classification**
- **Responsible:** `EAFIX.mq4::ClassifyDuration()`
- **Input:** Open time, close time
- **Output:** Duration bucket (SCALP <5min, INTRADAY <4hr, SWING >4hr)
- **Validation:** Close time > open time
- **Failure:** If negative duration, log error, classify as UNKNOWN

### **Step 42: Trade Result Row Construction**
- **Responsible:** `EAFIX.mq4::BuildResultRow()`
- **Input:** Ticket, SIG8 ID, P&L, duration, close reason
- **Output:** CSV row (SIG8,TICKET,OPEN_TIME,CLOSE_TIME,PNL,DURATION_BUCKET,CLOSE_REASON)
- **Validation:** All fields populated, SIG8 linkage verified
- **Failure:** If SIG8 missing, log orphan trade, continue with partial data

### **Step 43: Append to Trade Results CSV**
- **Responsible:** `EAFIX.mq4::AppendTradeResult()`
- **Input:** Trade result CSV row
- **Output:** Updated `trade_results.csv` in `DATA/MT_BRIDGE/`
- **Validation:** File write success, append-only maintained
- **Failure:** Retry write 3x, buffer in EA if all fail, alert

### **Step 44: Result Transport Hash Update**
- **Responsible:** `EAFIX.mq4::UpdateResultHash()`
- **Input:** `trade_results.csv` content
- **Output:** `trade_results.csv.hash` file
- **Validation:** Hash file updated successfully
- **Failure:** Continue without hash, Python will detect missing/stale hash

---

## **PHASE 8: OUTCOME CLASSIFICATION**

### **Step 45: Python Trade Result Polling**
- **Responsible:** `result_processor.py::poll_trade_results`
- **Input:** `trade_results.csv`, last processed row index
- **Output:** New result rows since last poll
- **Validation:** Hash matches, no duplicate rows
- **Failure:** If hash mismatch, reject file update, log corruption alert, retry next cycle

### **Step 46: Result Row Parsing**
- **Responsible:** `result_processor.py::parse_result_row`
- **Input:** Raw CSV row
- **Output:** `TradeResult` object
- **Validation:** All fields parsable, SIG8 ID exists in signal registry
- **Failure:** Discard unparseable rows, log parsing error

### **Step 47: WIN/LOSS/BREAKEVEN Classification**
- **Responsible:** `result_processor.py::classify_outcome`
- **Input:** `TradeResult` object with P&L
- **Output:** Outcome category (WIN if P&L >0, LOSS if P&L <0, BREAKEVEN if P&L ==0)
- **Validation:** P&L is numeric
- **Failure:** If P&L non-numeric, classify as UNKNOWN, log error

### **Step 48: Execution Quality Metrics Computation**
- **Responsible:** `result_processor.py::compute_quality_metrics`
- **Input:** `TradeResult` object
- **Output:** Slippage, hold time vs expected, close reason classification
- **Validation:** Open/close prices available, timestamps valid
- **Failure:** Partial metrics if data incomplete, flag as PARTIAL_METRICS

### **Step 49: Outcome Integrity Verification**
- **Responsible:** `result_processor.py::verify_integrity`
- **Input:** `TradeResult` object
- **Output:** VERIFIED or SUSPECT flag
- **Validation:** P&L matches manual calculation, ticket exists in execution registry
- **Failure:** SUSPECT results quarantined, human review required, logged

### **Step 50: Classified Outcome Registry Update**
- **Responsible:** `result_processor.py::update_outcome_registry`
- **Input:** Verified `TradeResult`
- **Output:** Updated `outcome_registry.db` (append-only)
- **Validation:** DB transaction success, foreign key to signal registry
- **Failure:** Rollback, retry once, halt result processing if persistent

---

## **PHASE 9: RE-ENTRY EVALUATION**

### **Step 51: Re-Entry Context Reconstruction**
- **Responsible:** `reentry_evaluator.py::reconstruct_context`
- **Input:** `TradeResult` object, original signal (via SIG8 linkage)
- **Output:** `ReEntryContext` object (original signal + outcome + current market state)
- **Validation:** Original signal found in registry, market data current (<5 sec)
- **Failure:** If signal not found or stale market data, skip re-entry evaluation, log error

### **Step 52: Outcome-Based Parameter Resolution**
- **Responsible:** `reentry_evaluator.py::resolve_parameters`
- **Input:** `ReEntryContext` with outcome classification
- **Output:** Re-entry parameters (SAME_DIR, REVERSE_DIR, SCALE_UP, SCALE_DOWN, NONE)
- **Validation:** Parameter set exists for outcome+duration+symbol combination
- **Failure:** If no parameter set, default to NONE (no re-entry), log missing configuration

### **Step 53: Calendar Context Re-Validation**
- **Responsible:** `reentry_evaluator.py::revalidate_calendar`
- **Input:** Original CAL8 ID, current time
- **Output:** Calendar freshness flag (STILL_RELEVANT, EXPIRED)
- **Validation:** Original event still within POST window or new relevant event exists
- **Failure:** EXPIRED calendar context → re-entry blocked, log expiration

### **Step 54: Re-Entry Risk Overlay Application**
- **Responsible:** `reentry_evaluator.py::apply_risk_overlay`
- **Input:** `ReEntryContext`, resolved parameters
- **Output:** Risk-adjusted re-entry parameters or NO_REENTRY
- **Validation:** Re-entry would not violate portfolio limits, circuit breakers not active
- **Failure:** If risk violation, output NO_REENTRY, log blocked reason

### **Step 55: Cooldown vs Re-Entry Decision Logic**
- **Responsible:** `reentry_evaluator.py::decide_reentry_or_cooldown`
- **Input:** Risk-adjusted re-entry parameters, recent trade velocity
- **Output:** Decision (RE_ENTER, COOLDOWN_5MIN, COOLDOWN_30MIN, BLOCK_INDEFINITE)
- **Validation:** Trade velocity <max_trades_per_hour, no recent re-entry on same signal
- **Failure:** If velocity exceeded, enforce COOLDOWN, log throttle event

---

## **PHASE 10: RE-ENTRY DECISION EMISSION**

### **Step 56: Deterministic Decision Record Creation**
- **Responsible:** `reentry_decision_service.py::create_decision_record`
- **Input:** Re-entry decision output
- **Output:** `ReEntryDecision` object (SIG8_ORIGINAL, decision type, timestamp, rationale)
- **Validation:** Decision type in allowed set, rationale non-empty
- **Failure:** If validation fails, reject decision, log error, halt re-entry path

### **Step 57: Re-Entry Decision Registry Update**
- **Responsible:** `reentry_decision_service.py::update_registry`
- **Input:** `ReEntryDecision` object
- **Output:** Updated `reentry_decision_registry.db` (append-only)
- **Validation:** DB transaction success, foreign key to outcome registry
- **Failure:** Rollback, retry once, halt if persistent

### **Step 58: Cooldown State Enforcement (If Applicable)**
- **Responsible:** `reentry_decision_service.py::enforce_cooldown`
- **Input:** `ReEntryDecision` with COOLDOWN type
- **Output:** Cooldown timer entry in `cooldown_registry.db` (symbol, expiry_time)
- **Validation:** Cooldown expiry time in future, no duplicate cooldown entries
- **Failure:** If duplicate, extend existing cooldown, log extension

### **Step 59: Re-Entry Signal Generation (If Approved)**
- **Responsible:** `reentry_decision_service.py::generate_reentry_signal`
- **Input:** `ReEntryDecision` with RE_ENTER type, resolved parameters
- **Output:** New `TradeSignal` object (new SIG8 ID, linked to original SIG8 via parent_signal field)
- **Validation:** All signal fields valid, parent linkage recorded
- **Failure:** If generation fails, log error, move to COOLDOWN state

### **Step 60: Re-Entry Signal Ledger Append**
- **Responsible:** `reentry_decision_service.py::append_to_ledger`
- **Input:** Re-entry `TradeSignal`
- **Output:** Updated `reentry_signal_ledger.db` (tracks re-entry chain depth)
- **Validation:** Chain depth <max_reentry_depth (default: 2), no circular references
- **Failure:** If depth exceeded, reject signal, enforce BLOCK_INDEFINITE, alert infinite loop risk

---

## **PHASE 11: RE-ENTRY TRADE EXECUTION (IF APPROVED)**

### **Step 61: Re-Entry Signal Risk Gate Re-Application**
- **Responsible:** `risk_manager.py::check_symbol_limits` (same as Step 21)
- **Input:** Re-entry `TradeSignal`
- **Output:** PASS or BLOCK_SYMBOL_LIMIT
- **Validation:** Current positions <max (same validation as primary entry)
- **Failure:** BLOCK outcome, signal marked NO_TRADE, logged

### **Step 62: Re-Entry Portfolio Exposure Re-Check**
- **Responsible:** `risk_manager.py::check_portfolio_exposure` (same as Step 22)
- **Input:** Re-entry `TradeSignal`
- **Output:** PASS or BLOCK_PORTFOLIO_LIMIT
- **Validation:** Total exposure within limits
- **Failure:** BLOCK outcome, halt re-entry

### **Step 63: Re-Entry Circuit Breaker Re-Evaluation**
- **Responsible:** `risk_manager.py::evaluate_circuit_breakers` (same as Step 23)
- **Input:** Re-entry `TradeSignal`, recent P&L
- **Output:** PASS or BLOCK_CIRCUIT_BREAKER
- **Validation:** Circuit breakers not tripped
- **Failure:** BLOCK outcome, ALL trading halted

### **Step 64: Re-Entry Idempotency Check**
- **Responsible:** `risk_manager.py::check_idempotency` (same as Step 24)
- **Input:** Re-entry `TradeSignal` with new SIG8 ID
- **Output:** PASS or BLOCK_DUPLICATE
- **Validation:** New SIG8 ID not in execution registry
- **Failure:** BLOCK outcome, signal discarded

### **Step 65: Re-Entry Authorization Record**
- **Responsible:** `risk_manager.py::record_authorization` (same as Step 25)
- **Input:** Authorized re-entry `TradeSignal`
- **Output:** Authorization record in DB
- **Validation:** Unique authorization hash
- **Failure:** No record = no execution

### **Step 66: Re-Entry Transport to MT**
- **Responsible:** `transport_service.py` (same as Steps 26-30)
- **Input:** Authorized re-entry `TradeSignal`
- **Output:** Row in `execution_queue.csv`
- **Validation:** Same transport validation as primary entry
- **Failure:** Same failure handling as primary entry

### **Step 67: Re-Entry EA Execution**
- **Responsible:** `EAFIX.mq4` (same as Steps 32-37)
- **Input:** Re-entry signal from CSV
- **Output:** Order placement and execution result
- **Validation:** Same EA validation as primary entry
- **Failure:** Same EA failure handling as primary entry

### **Step 68: Re-Entry Loop Prevention Check**
- **Responsible:** `reentry_decision_service.py::check_loop_prevention`
- **Input:** Completed re-entry execution result
- **Output:** CONTINUE or HALT_REENTRY_CHAIN
- **Validation:** If re-entry closed within <1 minute with LOSS, increment rapid-loss counter; if counter >3, HALT chain
- **Failure:** HALT outcome triggers indefinite cooldown, alert sent, manual review required

### **Step 69: Re-Entry Result Capture**
- **Responsible:** Same as Phase 7 (Steps 38-44)
- **Input:** Closed re-entry position
- **Output:** Trade result in `trade_results.csv`
- **Validation:** Same as primary trade
- **Failure:** Same as primary trade

### **Step 70: Re-Entry Outcome Classification**
- **Responsible:** Same as Phase 8 (Steps 45-50)
- **Input:** Re-entry trade result
- **Output:** Classified outcome in registry
- **Validation:** Outcome linked to re-entry signal, chain depth recorded
- **Failure:** Same as primary trade

### **Step 71: Recursive Re-Entry Evaluation (Conditional)**
- **Responsible:** Return to Phase 9 (Step 51) IF chain depth <max_depth
- **Input:** Re-entry outcome
- **Output:** Either new re-entry decision OR terminal cooldown
- **Validation:** Chain depth check, velocity check
- **Failure:** If depth or velocity exceeded, enforce terminal cooldown, exit re-entry loop

---

## **STATE TRANSITION MAP**

```
IDLE 
  → [Calendar Event Detected] → 
CALENDAR_CONTEXT_ACTIVE
  → [Signal Generated & Validated] → 
SIGNAL_AUTHORIZED
  → [Risk Gates PASS] → 
TRANSPORT_QUEUED
  → [EA Executes] → 
POSITIONED
  → [Trade Closes] → 
EXITED
  → [Result Classified] → 
RE_ENTRY_EVAL
  → [Decision: RE_ENTER] → SIGNAL_AUTHORIZED (loop back)
  → [Decision: COOLDOWN] → COOLDOWN_ACTIVE → IDLE
  → [Decision: BLOCK] → IDLE

CRITICAL HALT POINTS (Trading Stops):
- Step 21-24: Risk gate failures → NO_TRADE state
- Step 23: Circuit breaker → ALL_TRADING_HALTED
- Step 60: Max re-entry depth → BLOCK_INDEFINITE
- Step 68: Rapid loss loop → HALT_REENTRY_CHAIN + manual intervention
```

---

## **CONTROL POINTS WHERE TRADING CAN BE BLOCKED**

| Step | Control Point | Block Condition | Recovery Path |
|------|---------------|-----------------|---------------|
| 21 | Per-Symbol Limit | Position count ≥ max | Wait for position close |
| 22 | Portfolio Exposure | Total exposure ≥ max | Close positions or increase limit |
| 23 | Circuit Breaker | Loss threshold breached | Manual reset or EOD reset |
| 24 | Idempotency | Duplicate SIG8 | Signal discarded, investigate |
| 31 | Transport Lock Timeout | EA unresponsive | Restart EA, clear lock file |
| 32 | Hash Mismatch | File corruption | Regenerate CSV, verify integrity |
| 45 | Result Hash Mismatch | File corruption | Re-poll from EA, verify |
| 55 | Velocity Throttle | Too many trades/hour | Wait for cooldown expiry |
| 60 | Re-Entry Depth | Chain depth ≥ max | Terminal block, manual review |
| 68 | Loop Prevention | Rapid repeated losses | Terminal block, strategy review |

---

## **ARTIFACTS & AUDIT TRAIL**

**Immutable Identifiers:**
- CAL8: Calendar event ID
- SIG8: Signal ID
- Ticket: MT4 order ticket

**Append-Only Artifacts:**
- `calendar_registry.db`
- `signal_registry.db`
- `execution_authorization.db`
- `trade_results.csv`
- `outcome_registry.db`
- `reentry_decision_registry.db`
- `reentry_signal_ledger.db`

**Transport Files (Mutable):**
- `execution_queue.csv` (cleared after EA read)
- `trade_results.csv` (append-only from EA)
- Hash files (`.hash` suffix)
- Heartbeat files

**Full Replay Capability:**
Given CAL8 → reconstruct entire decision chain through signal generation, execution, outcome, and re-entry decisions via foreign key linkages across all registries.

---

## **END OF PROCESS BLUEPRINT**

This blueprint provides 71 atomic steps covering the complete lifecycle from economic calendar ingestion through recursive re-entry execution, with explicit failure modes, validation gates, and control points. All steps align with the HUEY_P / EAFIX architecture using CSV-first transport, append-only registries, and deterministic decision flows.
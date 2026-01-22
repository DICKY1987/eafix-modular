# Traceability Matrix: Process Steps ↔ Implementation Files

**Generated:** 2026-01-22T01:36:17Z  
**Total Steps:** 26  
**Implemented:** 18/26 (69.2%)  

---

## Step 1: Resolve configuration snapshot

- **Module:** `F1_CONFIG_PREFERENCES` (other)
- **Inputs:** ConfigSource (defaults + overrides)
- **Outputs:** ResolvedConfig (immutable snapshot)
- **Implementation:** ⚠️ Not mapped

## Step 2: Emit schedule tick (calendar polling cadence)

- **Module:** `F3_CLOCK_SCHEDULER` (other)
- **Inputs:** ResolvedConfig
- **Outputs:** ScheduleTick
- **Implementation:**
  - `services/calendar-ingestor/src/2099900093260118_main.py`
    - doc_id: `2099900093260118`

## Step 3: Poll calendar source(s)

- **Module:** `D2_CALENDAR_SOURCE_ADAPTER` (other)
- **Inputs:** CalendarSourceConfig + ScheduleTick
- **Outputs:** CalendarRaw
- **Implementation:**
  - `services/calendar-ingestor/src/2099900093260118_main.py`
    - doc_id: `2099900093260118`

## Step 4: Normalize raw calendar entries

- **Module:** `D3_CALENDAR_NORMALIZER` (other)
- **Inputs:** CalendarRaw + ResolvedConfig
- **Outputs:** CalendarEvent (UTC timestamps, standardized impact, dedup keys)
- **Implementation:**
  - `services/calendar-ingestor/src/2099900093260118_main.py`
    - doc_id: `2099900093260118`

## Step 5: Persist calendar events (append-only)

- **Module:** `F2_EVENT_LOG` (other)
- **Inputs:** CalendarEvent
- **Outputs:** EventStream (calendar.* events)
- **Implementation:**
  - `services/calendar-ingestor/src/2099900093260118_main.py`
    - doc_id: `2099900093260118`

## Step 6: Build anticipation triggers from calendar

- **Module:** `D4_CALENDAR_TRIGGER_BUILDER` (other)
- **Inputs:** CalendarEvent + ScheduleTick + ResolvedConfig
- **Outputs:** CalendarTrigger (symbol set + window + suppression metadata)
- **Implementation:**
  - `services/calendar-ingestor/src/2099900093260118_main.py`
    - doc_id: `2099900093260118`

## Step 7: Ingest market ticks

- **Module:** `D1_MARKET_FEED_ADAPTER` (other)
- **Inputs:** RawTick + ResolvedConfig
- **Outputs:** MarketTick
- **Implementation:**
  - `services/data-ingestor/src/2099900112260118_main.py`
    - doc_id: `2099900112260118`

## Step 8: Aggregate ticks into bars

- **Module:** `C1_BAR_BUILDER` (other)
- **Inputs:** MarketTick + ResolvedConfig
- **Outputs:** Bar
- **Implementation:** ⚠️ Not mapped

## Step 9: Compute indicators

- **Module:** `C2_INDICATOR_ENGINE` (other)
- **Inputs:** Bar + ResolvedConfig
- **Outputs:** IndicatorSnapshot
- **Implementation:**
  - `services/desktop-ui/2099900128260118_expiry_indicator_service.py`
    - doc_id: `2099900128260118`

## Step 10: Assemble strategy feature frame

- **Module:** `C3_FEATURE_PACKAGER` (other)
- **Inputs:** IndicatorSnapshot + CalendarTrigger + ResolvedConfig
- **Outputs:** FeatureFrame
- **Implementation:** ⚠️ Not mapped

## Step 11: Generate signal (or suppression)

- **Module:** `S1_SIGNAL_ENGINE` (other)
- **Inputs:** FeatureFrame + PositionSummary + ResolvedConfig
- **Outputs:** Signal OR SignalSuppressed
- **Implementation:**
  - `compliance/auto-remediation/2099900012260118_remediation-engine.py`
    - doc_id: `2099900012260118`

## Step 12: Convert signal to trade intent

- **Module:** `S2_INTENT_BUILDER` (other)
- **Inputs:** Signal + ResolvedConfig
- **Outputs:** TradeIntent
- **Implementation:** ⚠️ Not mapped

## Step 13: Evaluate risk and size

- **Module:** `R1_RISK_EVALUATOR` (other)
- **Inputs:** TradeIntent + PortfolioState + RiskPolicy + ResolvedConfig
- **Outputs:** RiskDecision (APPROVE/REJECT + reason codes + sized params)
- **Implementation:** ⚠️ Not mapped

## Step 14: Compile order intent

- **Module:** `R2_ORDER_INTENT_COMPILER` (other)
- **Inputs:** RiskDecision + ResolvedConfig
- **Outputs:** OrderIntent
- **Implementation:**
  - `services/transport-router/src/2099900199260118_main.py`
    - doc_id: `2099900199260118`

## Step 15: Route order to broker

- **Module:** `O1_ORDER_ROUTER` (other)
- **Inputs:** OrderIntent + BrokerPolicy + ResolvedConfig
- **Outputs:** RoutedOrderIntent
- **Implementation:**
  - `services/transport-router/src/2099900199260118_main.py`
    - doc_id: `2099900199260118`

## Step 16: Serialize and send to MT4 adapter

- **Module:** `B1_MT4_ADAPTER_TRANSPORT` (other)
- **Inputs:** RoutedOrderIntent + ResolvedConfig
- **Outputs:** BrokerOrderEnvelope + AdapterAck
- **Implementation:**
  - `services/transport-router/src/2099900199260118_main.py`
    - doc_id: `2099900199260118`

## Step 17: EA executes broker order

- **Module:** `B2_MT4_EA_EXECUTOR` (other)
- **Inputs:** BrokerOrderEnvelope
- **Outputs:** BrokerExecEvent (accept/fill/reject/close) + EAHealth
- **Implementation:**
  - `services/transport-router/src/2099900199260118_main.py`
    - doc_id: `2099900199260118`

## Step 18: Normalize broker events to canonical reports

- **Module:** `B3_EXEC_EVENT_NORMALIZER` (other)
- **Inputs:** BrokerExecEvent + ResolvedConfig
- **Outputs:** ExecutionReport + PositionSnapshot
- **Implementation:**
  - `services/event-gateway/src/2099900141260118_main.py`
    - doc_id: `2099900141260118`

## Step 19: Apply execution reports to OMS state

- **Module:** `O2_OMS_STATE_MACHINE` (other)
- **Inputs:** RoutedOrderIntent + ExecutionReport + PositionSnapshot + ResolvedConfig
- **Outputs:** OrderStateChanged + PositionStateChanged + TradeClosedRaw
- **Implementation:** ⚠️ Not mapped

## Step 20: Classify trade close and compute canonical PnL

- **Module:** `O3_TRADE_CLOSE_CLASSIFIER` (other)
- **Inputs:** TradeClosedRaw + ResolvedConfig
- **Outputs:** TradeClosed
- **Implementation:** ⚠️ Not mapped

## Step 21: Bucketize outcome

- **Module:** `E1_OUTCOME_BUCKETIZER` (other)
- **Inputs:** TradeClosed + ResolvedConfig
- **Outputs:** OutcomeBucket
- **Implementation:** ⚠️ Not mapped

## Step 22: Compute event proximity

- **Module:** `E2_PROXIMITY_EVALUATOR` (other)
- **Inputs:** CalendarEvent + ClockTick + ResolvedConfig
- **Outputs:** EventProximity
- **Implementation:**
  - `services/event-gateway/src/2099900141260118_main.py`
    - doc_id: `2099900141260118`

## Step 23: Lookup matrix decision

- **Module:** `E3_MATRIX_LOOKUP` (other)
- **Inputs:** OutcomeBucket + EventProximity + SignalContext + MatrixProfile + ResolvedConfig
- **Outputs:** MatrixDecision (or MatrixFallbackUsed)
- **Implementation:**
  - `services/reentry-matrix-svc/src/2099900174260118_main.py`
    - doc_id: `2099900174260118`

## Step 24: Build reentry trade intent (or suppress)

- **Module:** `E4_REENTRY_INTENT_BUILDER` (other)
- **Inputs:** MatrixDecision + ReentryChainState + ResolvedConfig
- **Outputs:** TradeIntent OR ReentrySuppressed
- **Implementation:**
  - `services/reentry-engine/src/2099900166260118_main.py`
    - doc_id: `2099900166260118`

## Step 25: Loop: reentry intent follows same risk->order->route->transport->execute chain

- **Module:** `(loop)` (unknown)
- **Inputs:** TradeIntent from Step 24
- **Outputs:** Either (a) new RoutedOrderIntent executed, producing new OutcomeBucket, or (b) suppression/cooldown state update
- **Implementation:**
  - `services/transport-router/src/2099900199260118_main.py`
    - doc_id: `2099900199260118`

## Step 26: Health aggregation + SLO evaluation

- **Module:** `P1_HEALTH_AGGREGATOR` (other)
- **Inputs:** AdapterHealth + ModuleHealth + ResolvedConfig
- **Outputs:** HealthReport
- **Implementation:**
  - `services/telemetry-daemon/src/2099900192260118_main.py`
    - doc_id: `2099900192260118`


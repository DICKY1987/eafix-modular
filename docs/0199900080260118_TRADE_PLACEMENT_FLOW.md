---
doc_id: DOC-DOC-0103
---

# Trade Placement End-to-End Data Flow

**Version:** 1.0.0  
**Last Updated:** 2026-01-09  
**Document Type:** Technical Reference  
**Audience:** Developers, Traders, Operations

---

## Table of Contents

1. [Overview](#1-overview)
2. [Communication Architecture](#2-communication-architecture)
3. [Complete Data Flow](#3-complete-data-flow)
4. [MT4 Bridge Integration](#4-mt4-bridge-integration)
5. [Failure Modes & Recovery](#5-failure-modes--recovery)
6. [Timing & Performance](#6-timing--performance)

---

## 1. Overview

### 1.1 How Trades Are Placed

The EAFIX system uses a **Python-to-MT4 bridge** to execute trades. The Python backend generates trading decisions, and MetaTrader 4 (MT4) executes them via an Expert Advisor (EA).

**Key Points**:
- ✅ **Python decides, MT4 executes**: Decision logic runs in Python microservices
- ✅ **Two-way communication**: Python → MT4 (trade orders), MT4 → Python (results)
- ✅ **Dual transport**: CSV files (primary) + TCP sockets (optional, faster)
- ✅ **Atomic writes**: All data transfers use checksums and sequence numbers
- ✅ **Idempotent**: Duplicate prevention via hybrid_id tracking

### 1.2 Why This Architecture?

**Separation of Concerns**:
- **Python**: Complex decision logic, matrix calculations, calendar integration
- **MT4**: Broker connectivity, order execution, tick streaming

**Benefits**:
- Modern development tools (Python) for business logic
- Reliable broker integration (MT4 is industry standard)
- Testable without broker connection
- Easy to switch brokers (just change MT4 account)

---

## 2. Communication Architecture

### 2.1 CSV Bridge (Primary Transport)

**How It Works**:
1. Python writes decision CSV to shared directory
2. MT4 EA polls directory every 1-5 seconds
3. EA reads new file, validates checksum, executes orders
4. EA writes results CSV back to shared directory
5. Python polls for results, validates, processes

**Directory Structure**:
```
shared_data/
├── incoming/           # MT4 → Python
│   ├── price_ticks/    # Real-time price data from MT4
│   └── trade_results/  # Execution confirmations
└── outgoing/           # Python → MT4
    ├── reentry_decisions/  # Trade orders to execute
    └── active_calendar_signals/  # Calendar alerts
```

**CSV Format** (reentry_decisions.csv):
```csv
file_seq,checksum,hybrid_id,symbol,action,lot_size,sl_points,tp_points,comment
1,abc123def456,FF-USD-NFP-O-1,EURUSD,OPEN,0.01,20,40,"Calendar trade"
2,def456ghi789,FF-EUR-CPI-R1-1,GBPUSD,INCREASE,0.015,25,50,"Re-entry R1"
```

**Atomic Write Process**:
```
Step 1: Write to reentry_decisions.tmp
Step 2: Calculate SHA-256 checksum for each row
Step 3: Call fsync() to flush to disk
Step 4: Atomic rename .tmp → .csv
Step 5: MT4 sees new file appear atomically
```

**Why CSV?**:
- ✅ **Simplicity**: No DLL dependencies, works on any MT4
- ✅ **Reliability**: Atomic file operations prevent corruption
- ✅ **Debuggable**: Human-readable for troubleshooting
- ✅ **Portable**: Works on Windows, Wine, etc.

### 2.2 Socket Bridge (Optional, High-Speed)

**How It Works**:
1. MT4 EA starts TCP server on localhost:8888
2. Python client connects and maintains persistent connection
3. JSON messages sent over TCP with heartbeats every 30s
4. Sub-millisecond latency (vs. 1-5s polling for CSV)

**Message Format** (JSON):
```json
{
  "type": "ORDER_INTENT",
  "seq": 42,
  "timestamp": "2026-01-09T18:30:45.123Z",
  "payload": {
    "hybrid_id": "FF-USD-NFP-O-1",
    "symbol": "EURUSD",
    "action": "OPEN",
    "lot_size": 0.01,
    "sl_points": 20,
    "tp_points": 40,
    "comment": "Calendar trade"
  }
}
```

**Heartbeat Protocol**:
```json
// Python → MT4 (every 30s)
{"type": "HEARTBEAT", "timestamp": "2026-01-09T18:30:00Z"}

// MT4 → Python (response)
{"type": "HEARTBEAT_ACK", "timestamp": "2026-01-09T18:30:00.050Z"}
```

**Automatic Failover**:
```python
class TransportRouter:
    """Manages CSV/Socket transport with automatic failover."""
    
    def __init__(self):
        self.mode = "AUTO"  # AUTO, CSV, SOCKET
        self.socket_healthy = False
        self.csv_healthy = True
        self.last_heartbeat = None
    
    def send_decision(self, decision: ReentryDecision):
        """Send decision using best available transport."""
        
        if self.mode == "AUTO":
            # Try socket first (faster)
            if self.socket_healthy:
                try:
                    self._send_via_socket(decision)
                    return
                except SocketError:
                    self._demote_socket()
            
            # Fall back to CSV
            self._send_via_csv(decision)
        
        elif self.mode == "SOCKET":
            self._send_via_socket(decision)
        
        elif self.mode == "CSV":
            self._send_via_csv(decision)
    
    def _demote_socket(self):
        """Demote socket after error."""
        self.socket_healthy = False
        log.warning("Socket demoted, using CSV fallback")
        # Retry socket after 60s
    
    def _promote_socket(self):
        """Promote socket after stable period."""
        if self._stable_for_60s():
            self.socket_healthy = True
            log.info("Socket promoted to primary")
```

**Health Monitoring**:
- Heartbeat timeout: 60 seconds → demote socket
- Connection refused: 3 consecutive → demote socket
- JSON parse error: immediate demotion
- Queue overflow: demote socket
- Stable 60s: promote socket back to primary

### 2.3 Transport Comparison

| Feature | CSV | Socket | Notes |
|---------|-----|--------|-------|
| **Latency** | 1-5s | <10ms | Socket 100-500x faster |
| **Setup** | None | DLL required | CSV works out-of-box |
| **Reliability** | High | Medium | CSV more stable |
| **Debugging** | Easy | Harder | CSV files human-readable |
| **Real-time** | No | Yes | Socket for HFT scenarios |
| **Default** | ✅ Primary | Optional | CSV is production default |

---

## 3. Complete Data Flow

### 3.1 End-to-End Trading Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Price Data Arrives                                         │
└─────────────────────────────────────────────────────────────────────┘
MT4 Terminal (Broker Feed)
    ↓ DDE or CSV export
data-ingestor (Python)
    ├─ Normalize: EURUSD bid=1.0852, ask=1.0853
    ├─ Validate: spread check, timestamp check
    ├─ Idempotency: check duplicate (key: EURUSD:2026-01-09T18:30:45)
    └─ Publish: redis:prices_stream
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Calculate Indicators                                        │
└─────────────────────────────────────────────────────────────────────┘
indicator-engine (Python)
    ├─ Subscribe: redis:prices_stream
    ├─ Calculate: RSI=28.5, MACD_HIST=0.0012, ADX=35.2
    ├─ Evaluate: Rolling buffers (200 ticks per symbol)
    └─ Publish: redis:indicators_stream
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: Generate Trading Signal                                     │
└─────────────────────────────────────────────────────────────────────┘
signal-generator (Python)
    ├─ Subscribe: redis:indicators_stream
    ├─ Apply rules:
    │   • RSI < 30 → Oversold (BUY signal)
    │   • MACD_HIST > 0 → Momentum confirmed
    │   • ADX > 20 → Trending market
    ├─ Calculate confidence: 0.85 (strong signal)
    └─ Publish: redis:signals_stream
        Signal {
            signal_id: "SIG-20260109-183045-001",
            symbol: "EURUSD",
            side: BUY,
            confidence: 0.85,
            indicators: ["RSI_14", "MACD_HIST", "ADX_14"]
        }
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: Risk Validation (HTTP Sync Call)                           │
└─────────────────────────────────────────────────────────────────────┘
risk-manager (Python)
    ├─ Check position limits:
    │   • Current exposure: 0.02 lots
    │   • Max exposure: 0.10 lots
    │   • Requested: 0.01 lots → ✅ APPROVED
    ├─ Check margin:
    │   • Free margin: $5,000
    │   • Required: $100 → ✅ APPROVED
    └─ Return: {"approved": true, "reason": null}
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: Calendar Proximity Check                                    │
└─────────────────────────────────────────────────────────────────────┘
flow-orchestrator (Python)
    ├─ Subscribe: redis:signals_stream
    ├─ Query calendar:
    │   • Check next 30 minutes for USD events
    │   • Result: No high-impact events → ✅ CLEAR
    ├─ Check matrix state:
    │   • Existing position: None (this is original O trade)
    │   • Matrix allows: OPEN action
    └─ Decision: PROCEED TO EXECUTION
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: Re-Entry Matrix Evaluation                                  │
└─────────────────────────────────────────────────────────────────────┘
reentry-engine (Python)
    ├─ Check if existing position for EURUSD
    ├─ If yes:
    │   • Classify outcome: WIN/LOSS (from last trade)
    │   • Classify duration: SHORT/MEDIUM/LONG
    │   • Classify proximity: NEAR/FAR to next event
    │   • Query matrix: What action for (outcome, duration, proximity)?
    │   • Generate hybrid_id: {event_id}-{chain_pos}-{instance}
    └─ If no (first trade):
        • Generate hybrid_id: FF-USD-NFP-O-1 (Original, instance 1)
        • Set action: OPEN
        • Set lot_size: 0.01 (from risk manager)
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: Compose Reentry Decision                                    │
└─────────────────────────────────────────────────────────────────────┘
reentry-engine (Python)
    └─ Create ReentryDecision:
        {
            decision_id: "DEC-20260109-183045-001",
            hybrid_id: "FF-USD-NFP-O-1",
            symbol: "EURUSD",
            chain_position: "O",
            action: "OPEN",
            lot_size: 0.01,
            sl_points: 20,
            tp_points: 40,
            parameter_set_id: "PS_EURUSD_DEFAULT",
            resolved_tier: "EXACT",
            timestamp: "2026-01-09T18:30:45Z"
        }
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 8: Write Decision to CSV (Atomic)                              │
└─────────────────────────────────────────────────────────────────────┘
transport-router (Python)
    ├─ Mode: AUTO (prefer socket, fallback CSV)
    ├─ Check socket_healthy: false → Use CSV
    ├─ Write to: shared_data/outgoing/reentry_decisions.tmp
    ├─ Calculate SHA-256 checksum for row
    ├─ Add file_seq: 42 (monotonically increasing)
    ├─ Call fsync() to force disk write
    └─ Atomic rename: .tmp → .csv
        File appears atomically: reentry_decisions_20260109_183045.csv
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 9: MT4 EA Polls for New Files                                  │
└─────────────────────────────────────────────────────────────────────┘
MT4 Expert Advisor (MQL4)
    ├─ Timer: Check shared_data/outgoing/ every 5 seconds
    ├─ Detect: reentry_decisions_20260109_183045.csv (new file)
    ├─ Read CSV into memory
    ├─ Validate:
    │   • file_seq: 42 > previous 41 → ✅ OK
    │   • checksum: Recompute SHA-256 → ✅ MATCH
    │   • symbol: EURUSD == Symbol() → ✅ MATCH
    │   • hybrid_id: Not in processed_ids set → ✅ NEW
    └─ Decision: EXECUTE ORDER
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 10: MT4 Places Order with Broker                               │
└─────────────────────────────────────────────────────────────────────┘
MT4 EA → Broker API
    ├─ Construct order:
    │   OrderSend(
    │       Symbol: "EURUSD",
    │       Cmd: OP_BUY,
    │       Volume: 0.01,
    │       Price: Ask (1.0853),
    │       Slippage: 3,
    │       StopLoss: Ask - 20 pips (1.0833),
    │       TakeProfit: Ask + 40 pips (1.0893),
    │       Comment: "FF-USD-NFP-O-1",
    │       MagicNumber: 12345
    │   )
    ├─ Wait for broker response...
    └─ Response: ticket=987654321, fill_price=1.08535
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 11: MT4 Writes Execution Result                                │
└─────────────────────────────────────────────────────────────────────┘
MT4 EA
    ├─ Create result row:
    │   {
    │       file_seq: 101,
    │       timestamp: "2026-01-09T18:30:46Z",
    │       account_id: "MT4-12345",
    │       symbol: "EURUSD",
    │       ticket: 987654321,
    │       direction: "BUY",
    │       lots: 0.01,
    │       entry_price: 1.08535,
    │       sl_price: 1.0833,
    │       tp_price: 1.0893,
    │       magic_number: 12345,
    │       signal_source: "FF-USD-NFP-O-1",
    │       checksum: "def789ghi012..."
    │   }
    ├─ Append to: shared_data/incoming/trade_results.tmp
    ├─ Calculate checksum
    ├─ fsync()
    └─ Atomic rename: .tmp → .csv
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 12: Python Reads Execution Confirmation                        │
└─────────────────────────────────────────────────────────────────────┘
flow-orchestrator (Python)
    ├─ Poll: shared_data/incoming/trade_results/ every 2 seconds
    ├─ Detect: trade_results_20260109_183046.csv
    ├─ Read and validate:
    │   • file_seq: 101 > previous 100 → ✅ OK
    │   • checksum: Recompute → ✅ MATCH
    │   • hybrid_id: FF-USD-NFP-O-1 matches pending order → ✅ FOUND
    ├─ Update internal state:
    │   • Mark order as FILLED
    │   • Record ticket: 987654321
    │   • Start monitoring position
    └─ Publish: redis:execution_reports
        ExecutionReport {
            report_id: "REP-20260109-183046-001",
            order_id: "DEC-20260109-183045-001",
            status: FILLED,
            filled_quantity: 0.01,
            average_price: 1.08535,
            commission: 0.07,
            timestamp: "2026-01-09T18:30:46Z"
        }
        ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 13: Audit Trail & Monitoring                                   │
└─────────────────────────────────────────────────────────────────────┘
compliance-monitor (Python)
    ├─ Log to audit_log table:
    │   INSERT INTO audit_log (
    │       hybrid_id: "FF-USD-NFP-O-1",
    │       event_type: "ORDER_EXECUTED",
    │       event_data: {signal, decision, execution},
    │       created_at: NOW()
    │   )
    └─ Track compliance: MiFID II transaction reporting

telemetry-daemon (Python)
    ├─ Record metrics:
    │   • trades_executed_total: +1
    │   • execution_latency_seconds: 1.2s
    │   • slippage_pips: 0.35
    └─ Write: health_metrics.csv

dashboard-backend (Python)
    ├─ Update UI:
    │   • New position: EURUSD BUY 0.01 @ 1.08535
    │   • P&L: $0.00 (just opened)
    │   • Risk exposure: $10.85
    └─ WebSocket: Notify GUI clients

gui-gateway (WebSocket)
    └─ Push to UI:
        {
            channel: "positions",
            event: "new_position",
            payload: {
                symbol: "EURUSD",
                side: "BUY",
                size: 0.01,
                entry: 1.08535,
                sl: 1.0833,
                tp: 1.0893,
                pnl: 0.00
            }
        }
```

### 3.2 Data Flow Diagram

```
┌────────────┐
│   MT4      │
│  Broker    │ Price feed (DDE/CSV)
└──────┬─────┘
       │
       ↓
┌─────────────────────────────────────────────────────────────┐
│ PYTHON BACKEND (Event-Driven Microservices)                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                          │
│  │data-ingestor │ → redis:prices_stream                    │
│  └──────┬───────┘                                           │
│         ↓                                                   │
│  ┌──────────────────┐                                       │
│  │indicator-engine  │ → redis:indicators_stream            │
│  └──────┬───────────┘                                       │
│         ↓                                                   │
│  ┌──────────────────┐                                       │
│  │signal-generator  │ → redis:signals_stream               │
│  └──────┬───────────┘                                       │
│         ↓                                                   │
│  ┌──────────────────┐    ┌──────────────┐                  │
│  │flow-orchestrator │ ←→ │risk-manager  │ (HTTP sync)      │
│  └──────┬───────────┘    └──────────────┘                  │
│         ↓                                                   │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │reentry-engine    │ ←→ │reentry-matrix-svc│              │
│  └──────┬───────────┘    └──────────────────┘              │
│         ↓                                                   │
│  ┌──────────────────┐                                       │
│  │transport-router  │ Write: reentry_decisions.csv         │
│  └──────┬───────────┘                                       │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          ↓
   ┌──────────────────────────────────┐
   │ SHARED FILE SYSTEM (CSV Bridge)  │
   │                                  │
   │  outgoing/reentry_decisions.csv  │ ← Python writes
   │  incoming/trade_results.csv      │ ← MT4 writes
   └──────────────────────────────────┘
          │
          ↓
   ┌─────────────────┐
   │  MT4 EA (MQL4)  │
   ├─────────────────┤
   │ • Poll for CSV  │
   │ • Validate      │
   │ • OrderSend()   │
   │ • Write results │
   └────────┬────────┘
            │
            ↓
   ┌─────────────────┐
   │  Broker API     │
   │  (Order fill)   │
   └─────────────────┘
```

---

## 4. MT4 Bridge Integration

### 4.1 CSV File Formats

#### reentry_decisions.csv (Python → MT4)

**Purpose**: Trading orders generated by Python, executed by MT4

**Schema**:
```csv
file_seq,checksum,hybrid_id,symbol,action,lot_size,sl_points,tp_points,entry_offset,comment,parameter_set_id,timestamp
42,abc123def456,FF-USD-NFP-O-1,EURUSD,OPEN,0.01,20,40,0,"Cal trade",PS_EURUSD_001,2026-01-09T18:30:45Z
43,def456ghi789,FF-EUR-CPI-R1-1,GBPUSD,INCREASE,0.015,25,50,0,"Re-entry R1",PS_GBPUSD_002,2026-01-09T18:31:12Z
```

**Field Definitions**:
- `file_seq`: Monotonically increasing (42, 43, 44, ...)
- `checksum`: SHA-256 of all other fields (prevents corruption)
- `hybrid_id`: Unique trade identifier (trace to original event)
- `symbol`: Currency pair (must match MT4 symbol exactly)
- `action`: OPEN, INCREASE, DECREASE, HOLD, CLOSE
- `lot_size`: Trade size (0.01 = micro lot)
- `sl_points`: Stop loss in points (20 points = 2.0 pips for EURUSD)
- `tp_points`: Take profit in points
- `entry_offset`: Points from current price (0 = market order)
- `comment`: Displayed in MT4 terminal
- `parameter_set_id`: Links to parameter configuration
- `timestamp`: Decision time (UTC, ISO 8601)

**Validation Rules** (MT4 EA):
1. `file_seq` > last processed sequence → Reject duplicates
2. Recompute `checksum` → Must match → Reject if corrupted
3. `symbol` == Symbol() → Only trade configured pair
4. `hybrid_id` not in processed set → Prevent duplicate execution
5. `lot_size` within broker min/max → Reject invalid sizes

#### trade_results.csv (MT4 → Python)

**Purpose**: Execution confirmations from MT4 back to Python

**Schema**:
```csv
file_seq,checksum,timestamp,account_id,symbol,ticket,direction,lots,entry_price,close_price,profit_ccy,pips,open_time,close_time,sl_price,tp_price,magic_number,close_reason,signal_source
101,ghi789jkl012,2026-01-09T18:30:46Z,MT4-12345,EURUSD,987654321,BUY,0.01,1.08535,,,,,1.0833,1.0893,12345,,FF-USD-NFP-O-1
102,jkl012mno345,2026-01-09T19:15:23Z,MT4-12345,EURUSD,987654321,BUY,0.01,1.08535,1.08935,4.00,40.0,2026-01-09T18:30:46Z,2026-01-09T19:15:23Z,1.0833,1.0893,12345,TP_HIT,FF-USD-NFP-O-1
```

**Event Types**:
1. **Order Opened**: close_price/profit/pips/close_time are empty
2. **Order Closed**: All fields populated, close_reason explains why

**Close Reasons**:
- `TP_HIT`: Take profit reached
- `SL_HIT`: Stop loss hit
- `MANUAL_CLOSE`: Trader closed manually
- `TRAILING_STOP`: Trailing stop triggered
- `MARGIN_CALL`: Broker closed due to margin
- `EA_COMMAND`: Closed by EA logic

### 4.2 MT4 EA Pseudo-Code

```mql4
// Simplified MT4 Expert Advisor logic

// Global variables
string g_processed_hybrids[];  // Track processed hybrid_ids
int g_last_file_seq = 0;       // Last processed sequence number
string g_shared_dir = "C:\\shared_data\\";

// Timer function (called every 5 seconds)
void OnTimer() {
    // Poll for new decision files
    string files[] = FindFiles(g_shared_dir + "outgoing\\reentry_decisions_*.csv");
    
    for (int i = 0; i < ArraySize(files); i++) {
        ProcessDecisionFile(files[i]);
    }
    
    // Check for closed positions
    CheckClosedPositions();
}

// Process decision file
void ProcessDecisionFile(string filename) {
    // Read CSV file
    string rows[][] = ReadCSV(filename);
    
    for (int row = 1; row < ArraySize(rows); row++) {  // Skip header
        int file_seq = StrToInteger(rows[row][0]);
        string checksum = rows[row][1];
        string hybrid_id = rows[row][2];
        string symbol = rows[row][3];
        string action = rows[row][4];
        double lot_size = StrToDouble(rows[row][5]);
        int sl_points = StrToInteger(rows[row][6]);
        int tp_points = StrToInteger(rows[row][7]);
        
        // Validation 1: Sequence must be increasing
        if (file_seq <= g_last_file_seq) {
            Print("ERROR: file_seq not increasing: ", file_seq);
            continue;
        }
        
        // Validation 2: Checksum must match
        string computed = ComputeChecksum(rows[row]);
        if (computed != checksum) {
            Print("ERROR: Checksum mismatch for seq ", file_seq);
            continue;
        }
        
        // Validation 3: Symbol must match
        if (symbol != Symbol()) {
            Print("INFO: Skipping wrong symbol: ", symbol);
            continue;
        }
        
        // Validation 4: hybrid_id not already processed
        if (ArrayContains(g_processed_hybrids, hybrid_id)) {
            Print("WARN: Duplicate hybrid_id: ", hybrid_id);
            continue;
        }
        
        // Execute order
        bool success = ExecuteOrder(hybrid_id, action, lot_size, sl_points, tp_points);
        
        if (success) {
            // Mark as processed
            ArrayAppend(g_processed_hybrids, hybrid_id);
            g_last_file_seq = file_seq;
        }
    }
}

// Execute trading order
bool ExecuteOrder(string hybrid_id, string action, double lots, int sl, int tp) {
    if (action == "OPEN" || action == "INCREASE") {
        // Calculate prices
        double entry_price = Ask;
        double sl_price = entry_price - sl * Point * 10;  // Convert points to price
        double tp_price = entry_price + tp * Point * 10;
        
        // Place order
        int ticket = OrderSend(
            Symbol(),              // Symbol
            OP_BUY,               // Command (BUY)
            lots,                 // Volume
            entry_price,          // Price
            3,                    // Slippage (3 points)
            sl_price,             // Stop loss
            tp_price,             // Take profit
            hybrid_id,            // Comment (for tracking)
            12345,                // Magic number
            0,                    // Expiration
            clrGreen              // Arrow color
        );
        
        if (ticket > 0) {
            Print("Order opened: ticket=", ticket, " hybrid_id=", hybrid_id);
            
            // Write result to CSV
            WriteTradeResult(ticket, hybrid_id, "OPENED", 0.0, 0.0);
            return true;
        } else {
            Print("OrderSend failed: ", GetLastError());
            return false;
        }
    }
    
    else if (action == "CLOSE") {
        // Find open order by hybrid_id
        for (int i = 0; i < OrdersTotal(); i++) {
            if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) {
                if (OrderComment() == hybrid_id) {
                    bool closed = OrderClose(
                        OrderTicket(),
                        OrderLots(),
                        Bid,
                        3,
                        clrRed
                    );
                    
                    if (closed) {
                        Print("Order closed: ticket=", OrderTicket());
                        WriteTradeResult(OrderTicket(), hybrid_id, "CLOSED", 
                                       OrderClosePrice(), OrderProfit());
                        return true;
                    }
                }
            }
        }
        
        Print("Order not found for hybrid_id: ", hybrid_id);
        return false;
    }
    
    return false;
}

// Write trade result to CSV
void WriteTradeResult(int ticket, string hybrid_id, string status, 
                      double close_price, double profit) {
    string filename = g_shared_dir + "incoming\\trade_results_" + 
                      TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS) + ".tmp";
    
    int handle = FileOpen(filename, FILE_WRITE|FILE_CSV);
    
    if (handle != INVALID_HANDLE) {
        // Write header
        FileWrite(handle, "file_seq,checksum,timestamp,account_id,symbol," +
                         "ticket,direction,lots,entry_price,close_price," +
                         "profit_ccy,pips,open_time,close_time,sl_price," +
                         "tp_price,magic_number,close_reason,signal_source");
        
        // Write data row
        string row = IntegerToString(g_trade_result_seq++) + "," +
                     "CHECKSUM_PLACEHOLDER," +  // Computed after
                     TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "," +
                     IntegerToString(AccountNumber()) + "," +
                     Symbol() + "," +
                     IntegerToString(ticket) + "," +
                     "BUY," +
                     DoubleToStr(OrderLots(), 2) + "," +
                     DoubleToStr(OrderOpenPrice(), 5) + "," +
                     (close_price > 0 ? DoubleToStr(close_price, 5) : "") + "," +
                     (profit != 0 ? DoubleToStr(profit, 2) : "") + "," +
                     "," +  // pips (calculated by Python)
                     TimeToStr(OrderOpenTime(), TIME_DATE|TIME_SECONDS) + "," +
                     (close_price > 0 ? TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS) : "") + "," +
                     DoubleToStr(OrderStopLoss(), 5) + "," +
                     DoubleToStr(OrderTakeProfit(), 5) + "," +
                     IntegerToString(OrderMagicNumber()) + "," +
                     (status == "CLOSED" ? "TP_HIT" : "") + "," +
                     hybrid_id;
        
        FileWrite(handle, row);
        FileClose(handle);
        
        // Atomic rename
        string final_name = StringReplace(filename, ".tmp", ".csv");
        FileMove(filename, final_name, FILE_REWRITE);
        
        Print("Trade result written: ", final_name);
    }
}

// Check for closed positions
void CheckClosedPositions() {
    // Iterate through history
    for (int i = 0; i < OrdersHistoryTotal(); i++) {
        if (OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) {
            string hybrid_id = OrderComment();
            
            // Check if already reported
            if (!ArrayContains(g_reported_closes, hybrid_id)) {
                // Write close result
                WriteTradeResult(
                    OrderTicket(),
                    hybrid_id,
                    "CLOSED",
                    OrderClosePrice(),
                    OrderProfit()
                );
                
                ArrayAppend(g_reported_closes, hybrid_id);
            }
        }
    }
}
```

---

## 5. Failure Modes & Recovery

### 5.1 Common Failures

#### Failure 1: CSV File Corruption

**Scenario**: Power loss during CSV write, partial file

**Detection**:
```python
# MT4 EA validation
if computed_checksum != stored_checksum:
    log.error(f"Checksum mismatch: file={filename} seq={file_seq}")
    # Skip this file
    # Python will retry on next poll cycle
```

**Recovery**:
- Python: Atomic write ensures either complete file or no file
- MT4: Rejects corrupted files, waits for next valid file
- Monitoring: Alert on repeated checksum failures

#### Failure 2: Sequence Gap

**Scenario**: File seq 42 → 44 (missing 43)

**Detection**:
```python
if file_seq != last_seq + 1:
    log.warning(f"Sequence gap detected: expected={last_seq+1} got={file_seq}")
    alert("SEQUENCE_GAP", {"expected": last_seq+1, "got": file_seq})
```

**Recovery**:
- Manual investigation required
- Check if decision 43 was critical
- May need to regenerate missing decision

#### Failure 3: Broker Rejection

**Scenario**: MT4 OrderSend() fails (invalid volume, market closed, etc.)

**Detection**:
```mql4
int ticket = OrderSend(...);
if (ticket <= 0) {
    int error = GetLastError();
    Print("OrderSend failed: error=", error);
    WriteTradeResult(0, hybrid_id, "REJECTED", 0, 0);
}
```

**Recovery**:
- Python sees REJECTED status in trade_results.csv
- Logs failure reason
- May retry with adjusted parameters
- Alerts trader if critical

#### Failure 4: Socket Disconnect

**Scenario**: TCP connection drops mid-transaction

**Detection**:
```python
try:
    socket.send(json.dumps(decision))
except socket.error as e:
    log.error(f"Socket error: {e}")
    self._demote_socket()  # Fall back to CSV
```

**Recovery**:
- Automatic failover to CSV transport
- Socket retries after 60s
- No data loss (CSV is always available)

### 5.2 Health Monitoring

**health_metrics.csv** (Updated every 30 seconds):
```csv
timestamp,ea_bridge_connected,csv_uptime_pct,socket_uptime_pct,p99_latency_ms,conflict_rate,file_seq
2026-01-09T18:30:00Z,1,100.0,95.2,1200,0.0,1001
2026-01-09T18:30:30Z,1,100.0,95.5,1150,0.0,1002
2026-01-09T18:31:00Z,0,100.0,0.0,5000,0.0,1003  # Socket down, CSV still working
```

**Alerts Triggered**:
- `ea_bridge_connected=0`: CRITICAL - Trading stopped
- `csv_uptime_pct < 99.5%`: WARNING - CSV reliability degraded
- `p99_latency_ms > 5000`: WARNING - Slow execution
- `conflict_rate > 0.01`: WARNING - Duplicate prevention working

---

## 6. Timing & Performance

### 6.1 Latency Breakdown

**CSV Transport** (Typical):
```
Python decision generated:          T+0ms
Write to CSV file:                  T+50ms  (disk I/O)
MT4 EA poll detects file:           T+2500ms (next 5s poll cycle)
MT4 validates & parses:             T+2520ms
MT4 OrderSend() to broker:          T+2620ms (broker latency)
Broker confirms fill:               T+2720ms
MT4 writes trade_results.csv:       T+2770ms
Python poll detects result:         T+4770ms (next 2s poll cycle)
Python processes result:            T+4790ms

TOTAL: ~4.8 seconds (decision → confirmation)
```

**Socket Transport** (Optimized):
```
Python decision generated:          T+0ms
Send via TCP socket:                T+5ms   (no disk I/O)
MT4 receives instantly:             T+6ms   (persistent connection)
MT4 validates & parses:             T+8ms
MT4 OrderSend() to broker:          T+108ms
Broker confirms fill:               T+208ms
MT4 sends result via socket:        T+213ms
Python receives instantly:          T+214ms
Python processes result:            T+216ms

TOTAL: ~220ms (decision → confirmation)
```

**Improvement**: Socket is **22x faster** than CSV polling

### 6.2 Throughput

**CSV Transport**:
- Max decisions/second: ~0.2 (limited by 5s poll cycle)
- Suitable for: Position trading, swing trading
- Not suitable for: Scalping, high-frequency

**Socket Transport**:
- Max decisions/second: ~50 (limited by broker, not transport)
- Suitable for: All trading styles including HFT
- Requires: DLL support in MT4

### 6.3 When to Use Each Transport

| Scenario | Recommended | Rationale |
|----------|-------------|-----------|
| **Production (stable)** | CSV + Socket (AUTO mode) | Best of both worlds |
| **Development/Testing** | CSV only | Easier debugging |
| **High-frequency trading** | Socket required | Sub-second latency needed |
| **Multi-broker setup** | CSV | Not all brokers allow DLLs |
| **Remote MT4 (VPS)** | CSV + network share | Sockets harder over network |
| **Mac/Linux (Wine)** | CSV only | DLL sockets may not work |

---

## Summary

### Trade Placement Flow (One Sentence)

**Python microservices generate trading decisions based on indicators and calendar events, write them to CSV files (or send via socket), MT4 EA polls for new files (or receives via socket), validates and executes orders with the broker, then writes execution confirmations back to CSV files that Python polls and processes.**

### Key Takeaways

✅ **Separation**: Python decides, MT4 executes  
✅ **Dual Transport**: CSV (reliable) + Socket (fast)  
✅ **Atomic Operations**: Checksums prevent corruption  
✅ **Idempotent**: Duplicate prevention via hybrid_id  
✅ **Auditable**: Complete trace from signal to fill  
✅ **Resilient**: Automatic failover, health monitoring  
✅ **Tested**: Contract validation ensures compatibility  

**End-to-End Latency**:
- CSV mode: ~5 seconds
- Socket mode: ~200ms
- Production (AUTO): Socket when healthy, CSV as fallback


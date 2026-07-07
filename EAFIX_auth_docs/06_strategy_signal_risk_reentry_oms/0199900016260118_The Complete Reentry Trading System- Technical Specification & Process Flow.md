The Complete Reentry Trading System- Technical Specification & Process Flow.md
35.70 KB •733 lines
•
Formatting may be inconsistent from source

The Complete Reentry Trading System- Technical Specification & Process Flow
System Architecture Overview
The reentry trading system operates as a deterministic finite state machine with three core components operating in synchronized orchestration:

Python Controller - Signal detection, matrix routing, and orchestration engine
MetaTrader EA - Trade execution, position management, and broker interface
Matrix Database - Decision rulebook containing 11,680+ predefined scenarios

Complete Atomic Process Flow with All Branches
PHASE 0: System Initialization & Bootstrap
0.000 â†’ SYSTEM_START
â”‚
â”œâ”€[0.001] Load Configuration Files
â”‚  â”œâ”€SUCCESSâ†’ Load parameters.schema.json
â”‚  â”‚  â”œâ”€[0.001a] Validate JSON structure
â”‚  â”‚  â”œâ”€[0.001b] Check required fields: $id, $schema, definitions
â”‚  â”‚  â””â”€[0.001c] Cache schema in memory
â”‚  â””â”€FAILUREâ†’ Schema Loading Error
â”‚     â”œâ”€[0.001d] Log error: "CRITICAL: Schema load failed"
â”‚     â”œâ”€[0.001e] Attempt fallback to cached schema
â”‚     â”‚  â”œâ”€EXISTSâ†’ Use cached version, log warning
â”‚     â”‚  â””â”€NOT_EXISTSâ†’ System halt with code E_INIT_001
â”‚     â””â”€[0.001f] Send alert to monitoring system
â”‚
â”œâ”€[0.002] Initialize File System
â”‚  â”œâ”€[0.002a] Check directory structure
â”‚  â”‚  â”œâ”€Common\Files\reentry\bridge\
â”‚  â”‚  â”œâ”€Common\Files\reentry\logs\
â”‚  â”‚  â”œâ”€Common\Files\reentry\config\
â”‚  â”‚  â””â”€Common\Files\reentry\data\
â”‚  â”œâ”€[0.002b] Create missing directories
â”‚  â”‚  â””â”€PERMISSION_ERRORâ†’ 
â”‚  â”‚     â”œâ”€Retry with elevated permissions
â”‚  â”‚     â””â”€FAILâ†’ Alert and fallback to temp directories
â”‚  â””â”€[0.002c] Set file permissions (read/write for system)
â”‚
â”œâ”€[0.003] Initialize Communication Channels
â”‚  â”œâ”€[0.003a] Open CSV file handles
â”‚  â”‚  â”œâ”€trading_signals.csv (write mode, append)
â”‚  â”‚  â”œâ”€trade_responses.csv (read mode, tail)
â”‚  â”‚  â””â”€parameter_log.csv (write mode, append)
â”‚  â”œâ”€[0.003b] Handle file lock scenarios
â”‚  â”‚  â”œâ”€FILE_LOCKEDâ†’ 
â”‚  â”‚  â”‚  â”œâ”€Wait 100ms, retry (max 10 attempts)
â”‚  â”‚  â”‚  â””â”€PERSISTENT_LOCKâ†’ Kill orphaned processes
â”‚  â”‚  â””â”€FILE_CORRUPTEDâ†’
â”‚  â”‚     â”œâ”€Backup corrupted file with timestamp
â”‚  â”‚     â””â”€Create new file with headers
â”‚  â””â”€[0.003c] Set read offsets to EOF
â”‚
â”œâ”€[0.004] Load Matrix Database
â”‚  â”œâ”€[0.004a] Read matrix_map.csv
â”‚  â”‚  â”œâ”€Validate CSV structure (3 columns minimum)
â”‚  â”‚  â””â”€ERRORâ†’ Use backup matrix or halt
â”‚  â”œâ”€[0.004b] Build hash-cache index
â”‚  â”‚  â”œâ”€Key: combination_id
â”‚  â”‚  â”œâ”€Value: {parameter_set_id, next_decision}
â”‚  â”‚  â””â”€Collision handling: Log and use latest
â”‚  â””â”€[0.004c] Validate matrix completeness
â”‚     â”œâ”€Check for required base combinations
â”‚     â””â”€MISSINGâ†’ Log gaps, use defaults
â”‚
â””â”€[0.005] Start Health Monitoring
   â”œâ”€[0.005a] Initialize timers
   â”‚  â”œâ”€heartbeat_tx_interval = 30s
   â”‚  â”œâ”€heartbeat_rx_timeout = 90s
   â”‚  â””â”€system_health_check = 60s
   â””â”€[0.005b] Start background threads
      â”œâ”€Thread 1: Heartbeat sender
      â”œâ”€Thread 2: Response monitor
      â””â”€Thread 3: Resource cleanup
PHASE 1: Economic Calendar Processing & Signal Generation
1.000 â†’ CALENDAR_SCAN_START (runs every 60 seconds)
â”‚
â”œâ”€[1.001] File Discovery
â”‚  â”œâ”€[1.001a] Scan %USERPROFILE%\Downloads
â”‚  â”‚  â”œâ”€Pattern: economic_calendar*.{csv,xlsx,xls}
â”‚  â”‚  â””â”€NO_FILESâ†’ 
â”‚  â”‚     â”œâ”€Check alternative directories
â”‚  â”‚     â””â”€Wait for next scan cycle
â”‚  â”œâ”€[1.001b] File validation
â”‚  â”‚  â”œâ”€Check file size (>0, <100MB)
â”‚  â”‚  â”œâ”€Check modification time (<24 hours old)
â”‚  â”‚  â””â”€INVALIDâ†’ Archive and skip
â”‚  â””â”€[1.001c] Lock file for processing
â”‚
â”œâ”€[1.002] File Processing
â”‚  â”œâ”€[1.002a] Copy to data\ with timestamp
â”‚  â”‚  â””â”€COPY_FAILâ†’ 
â”‚  â”‚     â”œâ”€Check disk space
â”‚  â”‚     â””â”€Use in-place processing
â”‚  â”œâ”€[1.002b] Compute SHA-256 hash
â”‚  â”œâ”€[1.002c] Compare with last processed
â”‚  â”‚  â””â”€DUPLICATEâ†’ Skip processing
â”‚  â””â”€[1.002d] Parse file format
â”‚     â”œâ”€CSVâ†’ Use csv.DictReader
â”‚     â”œâ”€XLSXâ†’ Use openpyxl
â”‚     â””â”€PARSE_ERRORâ†’ 
â”‚        â”œâ”€Try alternative encodings
â”‚        â””â”€Manual intervention required
â”‚
â”œâ”€[1.003] Data Transformation
â”‚  â”œâ”€[1.003a] Normalize columns
â”‚  â”‚  â”œâ”€Map source columns to standard
â”‚  â”‚  â”œâ”€Handle missing fields with defaults
â”‚  â”‚  â””â”€Validate data types
â”‚  â”œâ”€[1.003b] Filter by impact
â”‚  â”‚  â”œâ”€Keep: HIGH, MED
â”‚  â”‚  â”œâ”€Drop: LOW, HOLIDAY, TENTATIVE
â”‚  â”‚  â””â”€Log filtered count
â”‚  â””â”€[1.003c] Time zone conversion
â”‚     â”œâ”€Convert all to UTC
â”‚     â””â”€Handle DST transitions
â”‚
â”œâ”€[1.004] Event Enrichment
â”‚  â”œâ”€[1.004a] Add recurring events
â”‚  â”‚  â”œâ”€EQUITY_OPEN_USA (14:30 UTC daily)
â”‚  â”‚  â”œâ”€EQUITY_OPEN_EU (08:00 UTC daily)
â”‚  â”‚  â”œâ”€EQUITY_OPEN_ASIA (00:00 UTC daily)
â”‚  â”‚  â””â”€Session overlaps
â”‚  â”œâ”€[1.004b] Generate anticipation events
â”‚  â”‚  â”œâ”€For each HIGH impact:
â”‚  â”‚  â”‚  â”œâ”€ANTICIPATION_8HR at T-480min
â”‚  â”‚  â”‚  â””â”€ANTICIPATION_1HR at T-60min
â”‚  â”‚  â””â”€For each MED impact:
â”‚  â”‚     â””â”€ANTICIPATION_1HR at T-60min only
â”‚  â””â”€[1.004c] Deduplicate events
â”‚     â””â”€Keep earliest if conflicts
â”‚
â””â”€[1.005] Calendar Activation
   â”œâ”€[1.005a] Write economic_calendar.csv
   â”‚  â””â”€Use atomic rename operation
   â”œâ”€[1.005b] Update memory index
   â””â”€[1.005c] Broadcast update notification
PHASE 2: Signal Detection & Debouncing
2.000 â†’ SIGNAL_DETECTION_LOOP (runs every 100ms)
â”‚
â”œâ”€[2.001] Time Window Analysis
â”‚  â”œâ”€[2.001a] Get current UTC time
â”‚  â”œâ”€[2.001b] Define detection windows
â”‚  â”‚  â”œâ”€IMMEDIATE: now to now+5min
â”‚  â”‚  â”œâ”€SHORT: now+5min to now+15min
â”‚  â”‚  â”œâ”€LONG: now+15min to now+60min
â”‚  â”‚  â””â”€EXTENDED: now+60min to now+480min
â”‚  â””â”€[2.001c] Query calendar index
â”‚     â””â”€Returns: List of upcoming events
â”‚
â”œâ”€[2.002] Signal Candidate Generation
â”‚  â”œâ”€[2.002a] Economic signals
â”‚  â”‚  â”œâ”€ECO_HIGH from high impact events
â”‚  â”‚  â”œâ”€ECO_MED from medium impact events
â”‚  â”‚  â””â”€Check news blackout periods
â”‚  â”œâ”€[2.002b] Anticipation signals
â”‚  â”‚  â”œâ”€ANTICIPATION_8HR (8 hours before)
â”‚  â”‚  â””â”€ANTICIPATION_1HR (1 hour before)
â”‚  â”œâ”€[2.002c] Session signals
â”‚  â”‚  â”œâ”€EQUITY_OPEN_USA
â”‚  â”‚  â”œâ”€EQUITY_OPEN_EU
â”‚  â”‚  â””â”€EQUITY_OPEN_ASIA
â”‚  â””â”€[2.002d] Technical signals
â”‚     â””â”€ALL_INDICATORS (from external system)
â”‚
â”œâ”€[2.003] Debounce Logic
â”‚  â”œâ”€[2.003a] Check recent signals (last 15min)
â”‚  â”‚  â””â”€Key: (symbol, signal_type, event_id)
â”‚  â”œâ”€[2.003b] Apply cooldown rules
â”‚  â”‚  â”œâ”€Same signal/symbol: 15min cooldown
â”‚  â”‚  â”œâ”€Any signal/symbol: 5min cooldown
â”‚  â”‚  â””â”€OVERRIDEâ†’ VIP events bypass cooldown
â”‚  â””â”€[2.003c] Check active positions
â”‚     â”œâ”€If position open for symbolâ†’ 
â”‚     â”‚  â”œâ”€Allow if chaining enabled
â”‚     â”‚  â””â”€Skip if max positions reached
â”‚     â””â”€Global position limit check
â”‚
â”œâ”€[2.004] Context Building
â”‚  â”œâ”€[2.004a] Determine generation
â”‚  â”‚  â”œâ”€O: Original (no parent trade)
â”‚  â”‚  â”œâ”€R1: First reentry
â”‚  â”‚  â”œâ”€R2: Second reentry
â”‚  â”‚  â””â”€R3+: Terminal (not allowed)
â”‚  â”œâ”€[2.004b] Calculate proximity
â”‚  â”‚  â””â”€Time to nearest event determines bucket
â”‚  â”œâ”€[2.004c] Set initial outcome
â”‚  â”‚  â”œâ”€Original trades: outcome=SKIP
â”‚  â”‚  â””â”€Reentries: inherit from parent
â”‚  â””â”€[2.004d] Compute duration (reentries only)
â”‚     â”œâ”€FLASH: 0-15 minutes
â”‚     â”œâ”€QUICK: 16-60 minutes
â”‚     â”œâ”€LONG: 61-480 minutes
â”‚     â””â”€EXTENDED: >480 minutes
â”‚
â””â”€[2.005] Signal Emission
   â”œâ”€[2.005a] Build combination_id
   â”‚  â”œâ”€Grammar: gen:signal[:duration]:proximity:outcome
   â”‚  â””â”€Validate against regex pattern
   â”œâ”€[2.005b] Check signal gates
   â”‚  â”œâ”€Time of day restrictions
   â”‚  â”œâ”€Day of week restrictions
   â”‚  â””â”€Holiday calendar check
   â””â”€[2.005c] Queue for processing
      â””â”€Priority: VIP > HIGH > MED > LOW
PHASE 3: Matrix Resolution & Parameter Loading
3.000 â†’ MATRIX_LOOKUP_START
â”‚
â”œâ”€[3.001] Primary Lookup
â”‚  â”œâ”€[3.001a] Hash combination_id
â”‚  â”œâ”€[3.001b] Query matrix_map cache
â”‚  â”‚  â”œâ”€FOUNDâ†’ Extract parameter_set_id
â”‚  â”‚  â””â”€NOT_FOUNDâ†’ Fallback logic
â”‚  â””â”€[3.001c] Check next_decision field
â”‚     â”œâ”€CONTINUEâ†’ Proceed to parameter loading
â”‚     â””â”€END_TRADINGâ†’ Terminal state
â”‚
â”œâ”€[3.002] Fallback Hierarchy
â”‚  â”œâ”€[3.002a] Try wildcard patterns
â”‚  â”‚  â”œâ”€Replace outcome with *
â”‚  â”‚  â”œâ”€Replace duration with *
â”‚  â”‚  â””â”€Replace signal with category
â”‚  â”œâ”€[3.002b] Try parent combinations
â”‚  â”‚  â””â”€Strip components right-to-left
â”‚  â””â”€[3.002c] Use absolute default
â”‚     â””â”€parameter_set_id = PS-default
â”‚
â”œâ”€[3.003] Parameter Set Loading
â”‚  â”œâ”€[3.003a] Load from parameters.json
â”‚  â”‚  â””â”€FILE_ERRORâ†’ Use cached version
â”‚  â”œâ”€[3.003b] Find parameter_set by ID
â”‚  â”‚  â””â”€NOT_FOUNDâ†’ Use template default
â”‚  â””â”€[3.003c] Clone for modification
â”‚
â”œâ”€[3.004] Dynamic Overlays
â”‚  â”œâ”€[3.004a] Symbol-specific adjustments
â”‚  â”‚  â”œâ”€Spread multipliers for exotics
â”‚  â”‚  â”œâ”€Pip value corrections
â”‚  â”‚  â””â”€Broker-specific tweaks
â”‚  â”œâ”€[3.004b] Session overlays
â”‚  â”‚  â”œâ”€Asian session: reduce distances
â”‚  â”‚  â”œâ”€London open: increase ranges
â”‚  â”‚  â””â”€NY session: standard ranges
â”‚  â”œâ”€[3.004c] Volatility adjustments
â”‚  â”‚  â”œâ”€Query recent ATR
â”‚  â”‚  â”œâ”€Apply volatility multiplier
â”‚  â”‚  â””â”€Cap at max thresholds
â”‚  â””â”€[3.004d] Risk scaling
â”‚     â”œâ”€Account equity check
â”‚     â”œâ”€Drawdown adjustment
â”‚     â””â”€Correlation risk (multi-pair)
â”‚
â””â”€[3.005] Validation Pipeline
   â”œâ”€[3.005a] Schema validation
   â”‚  â”œâ”€Check required fields
   â”‚  â”œâ”€Validate data types
   â”‚  â””â”€Range checking
   â”œâ”€[3.005b] Business rules
   â”‚  â”œâ”€Risk â‰¤ 3.5% hard cap
   â”‚  â”œâ”€TP > SL for fixed methods
   â”‚  â””â”€Logical consistency
   â””â”€[3.005c] Broker compatibility
      â”œâ”€Minimum lot sizes
      â”œâ”€Tick size compliance
      â””â”€Symbol availability
PHASE 4: Bridge Communication (Python â†’ EA)
4.000 â†’ SIGNAL_TRANSMISSION_START
â”‚
â”œâ”€[4.001] Message Construction
â”‚  â”œâ”€[4.001a] Build UPDATE_PARAMS message
â”‚  â”‚  â”œâ”€version: "3.0"
â”‚  â”‚  â”œâ”€timestamp_utc: ISO-8601
â”‚  â”‚  â”œâ”€symbol: normalized pair
â”‚  â”‚  â”œâ”€combination_id: full context
â”‚  â”‚  â”œâ”€action: "UPDATE_PARAMS"
â”‚  â”‚  â”œâ”€parameter_set_id: reference
â”‚  â”‚  â”œâ”€json_payload_sha256: checksum
â”‚  â”‚  â””â”€json_payload: full parameters
â”‚  â””â”€[4.001b] Compress if > 64KB
â”‚     â””â”€Use gzip, set compression flag
â”‚
â”œâ”€[4.002] Write Operations
â”‚  â”œâ”€[4.002a] Acquire file lock
â”‚  â”‚  â””â”€TIMEOUTâ†’ Force unlock and retry
â”‚  â”œâ”€[4.002b] Write to temp file first
â”‚  â”œâ”€[4.002c] Fsync to ensure disk write
â”‚  â”œâ”€[4.002d] Atomic rename to target
â”‚  â””â”€[4.002e] Release file lock
â”‚
â”œâ”€[4.003] Signal Triggering
â”‚  â”œâ”€[4.003a] Evaluate entry conditions
â”‚  â”‚  â”œâ”€Immediate entry signals
â”‚  â”‚  â”œâ”€Delayed entry signals
â”‚  â”‚  â””â”€Conditional entry signals
â”‚  â”œâ”€[4.003b] Build TRADE_SIGNAL message
â”‚  â”‚  â””â”€Include signal context
â”‚  â””â”€[4.003c] Append to CSV
â”‚
â””â”€[4.004] Response Monitoring Setup
   â”œâ”€[4.004a] Start acknowledgment timer
   â”‚  â”œâ”€Timeout: 10 seconds
   â”‚  â””â”€Retry count: 3
   â”œâ”€[4.004b] Register callback handlers
   â””â”€[4.004c] Log transmission event
PHASE 5: EA Reception & Validation
5.000 â†’ EA_MESSAGE_PROCESSING
â”‚
â”œâ”€[5.001] File Monitoring
â”‚  â”œâ”€[5.001a] Poll trading_signals.csv
â”‚  â”‚  â”œâ”€Interval: 100ms active, 2s idle
â”‚  â”‚  â””â”€Use file change notification API
â”‚  â”œâ”€[5.001b] Detect new lines
â”‚  â”‚  â”œâ”€Compare file size
â”‚  â”‚  â””â”€Read from last offset
â”‚  â””â”€[5.001c] Parse CSV row
â”‚     â””â”€ERRORâ†’ Log and skip row
â”‚
â”œâ”€[5.002] Message Validation
â”‚  â”œâ”€[5.002a] Version check
â”‚  â”‚  â”œâ”€v3.0â†’ Current protocol
â”‚  â”‚  â”œâ”€v2.xâ†’ Legacy adapter
â”‚  â”‚  â””â”€Unknownâ†’ REJECT_SET(E0000)
â”‚  â”œâ”€[5.002b] Checksum verification
â”‚  â”‚  â”œâ”€Compute SHA-256
â”‚  â”‚  â”œâ”€Compare with provided
â”‚  â”‚  â””â”€MISMATCHâ†’ Request retransmit
â”‚  â””â”€[5.002c] Symbol validation
â”‚     â”œâ”€Check if tradeable
â”‚     â”œâ”€Market hours check
â”‚     â””â”€Spread threshold check
â”‚
â”œâ”€[5.003] Parameter Validation
â”‚  â”œâ”€[5.003a] Schema compliance
â”‚  â”‚  â”œâ”€Parse JSON payload
â”‚  â”‚  â”œâ”€Validate against schema
â”‚  â”‚  â””â”€INVALIDâ†’ REJECT_SET(E1000)
â”‚  â”œâ”€[5.003b] Risk validation
â”‚  â”‚  â”œâ”€Calculate position size
â”‚  â”‚  â”œâ”€Check risk percentage â‰¤ 3.5%
â”‚  â”‚  â””â”€EXCEEDâ†’ REJECT_SET(E1001)
â”‚  â”œâ”€[5.003c] Stop/Target validation
â”‚  â”‚  â”œâ”€Minimum distance from market
â”‚  â”‚  â”œâ”€TP > SL for winners
â”‚  â”‚  â””â”€INVALIDâ†’ REJECT_SET(E1012)
â”‚  â””â”€[5.003d] Account validation
â”‚     â”œâ”€Sufficient margin
â”‚     â”œâ”€Max positions check
â”‚     â””â”€Daily loss limit check
â”‚
â””â”€[5.004] State Update
   â”œâ”€[5.004a] Store parameters
   â”‚  â””â”€Key: (symbol, combination_id)
   â”œâ”€[5.004b] Update EA state
   â”‚  â”œâ”€IDLEâ†’ PARAMS_LOADED
   â”‚  â””â”€Log state transition
   â””â”€[5.004c] Send acknowledgment
      â””â”€ACK_UPDATE or REJECT_SET
PHASE 6: Trade Execution
6.000 â†’ TRADE_EXECUTION_START
â”‚
â”œâ”€[6.001] Pre-Flight Checks
â”‚  â”œâ”€[6.001a] News embargo check
â”‚  â”‚  â”œâ”€eco_cutoff_minutes_before
â”‚  â”‚  â”œâ”€eco_cutoff_minutes_after
â”‚  â”‚  â””â”€BLOCKEDâ†’ REJECT_TRADE(E1040)
â”‚  â”œâ”€[6.001b] Spread check
â”‚  â”‚  â”œâ”€Current vs max_spread_pips
â”‚  â”‚  â””â”€EXCEEDâ†’ Wait or reject
â”‚  â”œâ”€[6.001c] Connection check
â”‚  â”‚  â”œâ”€Broker connection status
â”‚  â”‚  â””â”€OFFLINEâ†’ Queue for retry
â”‚  â””â”€[6.001d] Account check
â”‚     â”œâ”€Free margin available
â”‚     â””â”€Position limit check
â”‚
â”œâ”€[6.002] Lot Size Calculation
â”‚  â”œâ”€[6.002a] Get account currency
â”‚  â”œâ”€[6.002b] Calculate pip value
â”‚  â”‚  â”œâ”€Standard pairs: 10 units
â”‚  â”‚  â”œâ”€JPY pairs: 1000 units
â”‚  â”‚  â””â”€Exotic adjustments
â”‚  â”œâ”€[6.002c] Apply risk formula
â”‚  â”‚  â””â”€Lots = (Risk% Ã— Balance) / (SL_pips Ã— PipValue)
â”‚  â””â”€[6.002d] Round to broker step
â”‚     â”œâ”€Micro lots: 0.01
â”‚     â”œâ”€Mini lots: 0.1
â”‚     â””â”€Standard lots: 1.0
â”‚
â”œâ”€[6.003] Order Placement
â”‚  â”œâ”€MARKET Orders
â”‚  â”‚  â”œâ”€[6.003a] Get current price
â”‚  â”‚  â”œâ”€[6.003b] Check slippage
â”‚  â”‚  â”‚  â””â”€EXCEEDâ†’ Retry with new price
â”‚  â”‚  â”œâ”€[6.003c] Send OrderSend()
â”‚  â”‚  â””â”€[6.003d] Handle requotes
â”‚  â”œâ”€PENDING Orders (Straddle)
â”‚  â”‚  â”œâ”€[6.003e] Calculate entry levels
â”‚  â”‚  â”‚  â”œâ”€BUY_STOP = Ask + distance
â”‚  â”‚  â”‚  â””â”€SELL_STOP = Bid - distance
â”‚  â”‚  â”œâ”€[6.003f] Place both orders
â”‚  â”‚  â””â”€[6.003g] Link orders (OCO)
â”‚  â””â”€Order Failures
â”‚     â”œâ”€[6.003h] Retry logic
â”‚     â”‚  â”œâ”€Max attempts: order_retry_attempts
â”‚     â”‚  â”œâ”€Delay: order_retry_delay_ms
â”‚     â”‚  â””â”€Exponential backoff
â”‚     â””â”€[6.003i] Final failure
â”‚        â””â”€REJECT_TRADE(E1050)
â”‚
â””â”€[6.004] Post-Execution
   â”œâ”€[6.004a] Capture order IDs
   â”œâ”€[6.004b] Set EA state
   â”‚  â””â”€ORDERS_PLACED or TRADE_TRIGGERED
   â”œâ”€[6.004c] Start monitors
   â”‚  â”œâ”€Trailing stop monitor
   â”‚  â”œâ”€Timeout monitor
   â”‚  â””â”€News monitor
   â””â”€[6.004d] Send confirmation
      â””â”€ACK_TRADE with order details
PHASE 7: Position Management
7.000 â†’ POSITION_MONITORING_LOOP
â”‚
â”œâ”€[7.001] Straddle Management
â”‚  â”œâ”€[7.001a] Monitor pending orders
â”‚  â”‚  â”œâ”€Check if triggered
â”‚  â”‚  â””â”€Update state on trigger
â”‚  â”œâ”€[7.001b] OCO cancellation
â”‚  â”‚  â”œâ”€If one side fillsâ†’
â”‚  â”‚  â”œâ”€Cancel opposite pending
â”‚  â”‚  â””â”€Log cancellation
â”‚  â””â”€[7.001c] Timeout handling
â”‚     â”œâ”€Check pending_order_timeout_min
â”‚     â”œâ”€Delete expired pendings
â”‚     â””â”€Send CANCELLED response
â”‚
â”œâ”€[7.002] Active Position Management
â”‚  â”œâ”€[7.002a] Trailing stop logic
â”‚  â”‚  â”œâ”€FIXED trailing
â”‚  â”‚  â”‚  â”œâ”€Trail by fixed pips
â”‚  â”‚  â”‚  â””â”€Only trail profits
â”‚  â”‚  â”œâ”€ATR trailing
â”‚  â”‚  â”‚  â”œâ”€Calculate current ATR
â”‚  â”‚  â”‚  â””â”€Trail by ATR multiple
â”‚  â”‚  â””â”€PERCENT trailing
â”‚  â”‚     â””â”€Trail by profit percentage
â”‚  â”œâ”€[7.002b] Breakeven logic
â”‚  â”‚  â”œâ”€Check if in profit â‰¥ BE pips
â”‚  â”‚  â”œâ”€Move SL to entry + 1
â”‚  â”‚  â””â”€Lock in commission coverage
â”‚  â””â”€[7.002c] Emergency stop
â”‚     â”œâ”€Max loss per position
â”‚     â”œâ”€Time-based stops
â”‚     â””â”€Correlation stops
â”‚
â”œâ”€[7.003] Exit Detection
â”‚  â”œâ”€[7.003a] Monitor OrderClose events
â”‚  â”‚  â”œâ”€Stop loss hitâ†’ LOSS
â”‚  â”‚  â”œâ”€Take profit hitâ†’ WIN
â”‚  â”‚  â”œâ”€Manual closeâ†’ MANUAL
â”‚  â”‚  â””â”€Timeout closeâ†’ TIMEOUT
â”‚  â”œâ”€[7.003b] Calculate metrics
â”‚  â”‚  â”œâ”€Pips gained/lost
â”‚  â”‚  â”œâ”€Time in trade (minutes)
â”‚  â”‚  â”œâ”€Peak profit/drawdown
â”‚  â”‚  â””â”€Slippage on exit
â”‚  â””â”€[7.003c] Categorize outcome
â”‚     â”œâ”€1: Big loss (< -50 pips)
â”‚     â”œâ”€2: Loss (-50 to -10)
â”‚     â”œâ”€3: Small loss (-10 to -1)
â”‚     â”œâ”€4: Breakeven (-1 to +1)
â”‚     â”œâ”€5: Win (+1 to +50)
â”‚     â””â”€6: Big win (> +50)
â”‚
â””â”€[7.004] Exit Reporting
   â”œâ”€[7.004a] Build close message
   â”‚  â”œâ”€Result: WIN/LOSS/BE
   â”‚  â”œâ”€Pips: actual P/L
   â”‚  â”œâ”€Minutes: duration
   â”‚  â””â”€Exit reason
   â”œâ”€[7.004b] Write to responses
   â””â”€[7.004c] Update EA state
      â””â”€TRADE_CLOSEDâ†’ IDLE
PHASE 8: Reentry Decision Engine
8.000 â†’ REENTRY_EVALUATION_START
â”‚
â”œâ”€[8.001] Trade Outcome Processing
â”‚  â”œâ”€[8.001a] Receive close notification
â”‚  â”œâ”€[8.001b] Parse outcome details
â”‚  â”‚  â”œâ”€Extract pips
â”‚  â”‚  â”œâ”€Extract duration
â”‚  â”‚  â””â”€Extract exit type
â”‚  â””â”€[8.001c] Validate outcome
â”‚     â””â”€Ensure all required fields
â”‚
â”œâ”€[8.002] Chain Context Building
â”‚  â”œâ”€[8.002a] Retrieve chain history
â”‚  â”‚  â”œâ”€Original trade context
â”‚  â”‚  â”œâ”€Previous reentry contexts
â”‚  â”‚  â””â”€Cumulative metrics
â”‚  â”œâ”€[8.002b] Determine next generation
â”‚  â”‚  â”œâ”€Oâ†’R1 transition
â”‚  â”‚  â”œâ”€R1â†’R2 transition
â”‚  â”‚  â””â”€R2â†’Terminal
â”‚  â””â”€[8.002c] Apply generation rules
â”‚     â”œâ”€Max 2 reentries (R2 cap)
â”‚     â”œâ”€Degrading risk per level
â”‚     â””â”€Tightening parameters
â”‚
â”œâ”€[8.003] Combination ID Construction
â”‚  â”œâ”€[8.003a] For ECO signals
â”‚  â”‚  â”œâ”€Include duration category
â”‚  â”‚  â””â”€Format: gen:signal:duration:proximity:outcome
â”‚  â”œâ”€[8.003b] For non-ECO signals
â”‚  â”‚  â”œâ”€Exclude duration
â”‚  â”‚  â””â”€Format: gen:signal:proximity:outcome
â”‚  â””â”€[8.003c] Special combinations
â”‚     â”œâ”€ALL pattern matching
â”‚     â”œâ”€Category wildcards
â”‚     â””â”€Override combinations
â”‚
â”œâ”€[8.004] Matrix Decision
â”‚  â”œâ”€[8.004a] Query matrix_map
â”‚  â”‚  â”œâ”€Exact match lookup
â”‚  â”‚  â””â”€Fallback patterns
â”‚  â”œâ”€[8.004b] Evaluate decision
â”‚  â”‚  â”œâ”€CONTINUEâ†’ Get new parameters
â”‚  â”‚  â”œâ”€END_TRADINGâ†’ Stop chain
â”‚  â”‚  â””â”€PAUSEâ†’ Delay reentry
â”‚  â””â”€[8.004c] Apply overrides
â”‚     â”œâ”€Account state overrides
â”‚     â”œâ”€Time-based overrides
â”‚     â””â”€Risk limit overrides
â”‚
â””â”€[8.005] Reentry Execution
   â”œâ”€[8.005a] If CONTINUE
   â”‚  â”œâ”€Load new parameter set
   â”‚  â”œâ”€Apply generation modifiers
   â”‚  â””â”€GOTO Phase 3 with new context
   â”œâ”€[8.005b] If END_TRADING
   â”‚  â”œâ”€Mark chain complete
   â”‚  â”œâ”€Log chain summary
   â”‚  â””â”€Clear chain context
   â””â”€[8.005c] If PAUSE
      â”œâ”€Set timer for retry
      â””â”€Maintain chain context
PHASE 9: Error Recovery & Resilience
9.000 â†’ ERROR_HANDLING_FRAMEWORK
â”‚
â”œâ”€[9.001] Communication Failures
â”‚  â”œâ”€[9.001a] Missing ACK timeout
â”‚  â”‚  â”œâ”€Retry transmission (3x)
â”‚  â”‚  â”œâ”€Use backup channel
â”‚  â”‚  â””â”€Alert and manual intervention
â”‚  â”œâ”€[9.001b] Corrupted messages
â”‚  â”‚  â”œâ”€Request retransmission
â”‚  â”‚  â”œâ”€Use error correction
â”‚  â”‚  â””â”€Skip and continue
â”‚  â””â”€[9.001c] File lock issues
â”‚     â”œâ”€Force unlock after timeout
â”‚     â”œâ”€Use lock-free alternatives
â”‚     â””â”€Restart file handles
â”‚
â”œâ”€[9.002] Execution Failures
â”‚  â”œâ”€[9.002a] Order rejections
â”‚  â”‚  â”œâ”€Invalid price: Requote
â”‚  â”‚  â”œâ”€No money: Reduce size
â”‚  â”‚  â”œâ”€Market closed: Queue
â”‚  â”‚  â””â”€Symbol halted: Cancel
â”‚  â”œâ”€[9.002b] Partial fills
â”‚  â”‚  â”œâ”€Accept partial
â”‚  â”‚  â”œâ”€Complete remainder
â”‚  â”‚  â””â”€Cancel remainder
â”‚  â””â”€[9.002c] Slippage handling
â”‚     â”œâ”€Accept if < threshold
â”‚     â”œâ”€Reject if excessive
â”‚     â””â”€Adjust parameters
â”‚
â”œâ”€[9.003] System Failures
â”‚  â”œâ”€[9.003a] Python crash recovery
â”‚  â”‚  â”œâ”€Persist state to disk
â”‚  â”‚  â”œâ”€Reload on restart
â”‚  â”‚  â””â”€Resume from checkpoint
â”‚  â”œâ”€[9.003b] EA crash recovery
â”‚  â”‚  â”œâ”€Detect via heartbeat
â”‚  â”‚  â”œâ”€Restart EA
â”‚  â”‚  â””â”€Resync positions
â”‚  â””â”€[9.003c] Matrix corruption
â”‚     â”œâ”€Detect via checksums
â”‚     â”œâ”€Load backup matrix
â”‚     â””â”€Rebuild from source
â”‚
â””â”€[9.004] Monitoring & Alerting
   â”œâ”€[9.004a] Health checks
   â”‚  â”œâ”€Heartbeat monitoring
   â”‚  â”œâ”€Resource usage
   â”‚  â””â”€Performance metrics
   â”œâ”€[9.004b] Alert triggers
   â”‚  â”œâ”€Critical errors
   â”‚  â”œâ”€Unusual patterns
   â”‚  â””â”€Limit breaches
   â””â”€[9.004c] Reporting
      â”œâ”€Real-time dashboards
      â”œâ”€Email notifications
      â””â”€SMS for critical
PHASE 10: Audit & Compliance
10.000 â†’ AUDIT_TRAIL_SYSTEM
â”‚
â”œâ”€[10.001] Transaction Logging
â”‚  â”œâ”€Every parameter set loaded
â”‚  â”œâ”€Every signal generated
â”‚  â”œâ”€Every order placed
â”‚  â”œâ”€Every position closed
â”‚  â””â”€Every error encountered
â”‚
â”œâ”€[10.002] Compliance Checks
â”‚  â”œâ”€Risk limit enforcement
â”‚  â”œâ”€Regulatory compliance
â”‚  â”œâ”€Broker rules adherence
â”‚  â””â”€Internal policy checks
â”‚
â””â”€[10.003] Performance Analytics
   â”œâ”€Win/loss ratios by combination
   â”œâ”€Profitability by signal type
   â”œâ”€Reentry effectiveness metrics
   â””â”€System optimization data
State Machine Definitions
EA States
IDLE â†’ Waiting for parameters
PARAMS_LOADED â†’ Parameters received, awaiting signal
ORDERS_PLACED â†’ Pending orders active
TRADE_TRIGGERED â†’ Position active
TRADE_CLOSED â†’ Position closed, awaiting cleanup
ERROR â†’ Error state requiring intervention
DISABLED â†’ System disabled
Chain States
INACTIVE â†’ No chain active
ORIGINAL_ACTIVE â†’ Original trade running
REENTRY_1_ACTIVE â†’ First reentry running
REENTRY_2_ACTIVE â†’ Second reentry running
CHAIN_COMPLETE â†’ Terminal state reached
CHAIN_PAUSED â†’ Temporary pause in chain
Critical Integration Points
1. Synchronization Mechanisms

File-based locks with timeout recovery
Atomic operations using tempâ†’rename pattern
Heartbeat protocol for liveness detection
Checksum validation for data integrity

2. Risk Management Layers

Parameter validation at multiple points
Hard-coded 3.5% risk limit enforced by EA
Position sizing with account percentage
Drawdown monitoring with circuit breakers

3. Recovery Mechanisms

State persistence across restarts
Checkpoint recovery for long operations
Automatic retry with exponential backoff
Fallback parameters for missing configs

4. Performance Optimizations

In-memory caching of matrix and parameters
Lazy loading of large datasets
Batch processing of multiple signals
Async I/O for file operations

Matrix Grammar Specification
Combination ID Format
generation:signal_type[:duration]:proximity:outcome

Where:
- generation âˆˆ {O, R1, R2}
- signal_type âˆˆ {ECO_HIGH, ECO_MED, ANTICIPATION_1HR, ANTICIPATION_8HR, 
                 EQUITY_OPEN_USA, EQUITY_OPEN_EU, EQUITY_OPEN_ASIA, 
                 ALL_INDICATORS}
- duration âˆˆ {FLASH, QUICK, LONG, EXTENDED} (ECO signals only)
- proximity âˆˆ {IMMEDIATE, SHORT, LONG, EXTENDED}
- outcome âˆˆ {1, 2, 3, 4, 5, 6, SKIP, WIN, LOSS, BE}
Matrix Coverage

Total combinations: ~11,680 per currency pair
Supported pairs: 20 major and minor pairs
Default fallbacks: Every path has a default
Override capability: VIP combinations for special events

System Boundaries & Limits
Performance Limits

Max signals/second: 10
Max positions: 10 concurrent
Max reentries: 2 (R2 terminal)
Max risk: 3.5% per position

Time Constraints

Signal detection: 100ms cycle
EA response: 10 second timeout
Heartbeat: 30 second interval
File polling: 100ms active, 2s idle

Resource Limits

Memory: 2GB Python, 512MB EA
Disk: 10GB for logs/data
CPU: 4 cores recommended
Network: 10 Mbps minimum

Failure Modes & Mitigations
Critical Failures

Complete matrix corruption â†’ Load backup, alert operator
Broker connection loss â†’ Pause trading, attempt reconnect
Account margin call â†’ Emergency close all, disable system
Schema version mismatch â†’ Compatibility mode or halt

Degraded Operations

Slow file I/O â†’ Increase timeouts, reduce frequency
High CPU usage â†’ Disable non-critical features
Network latency â†’ Increase slippage tolerance
Missing heartbeats â†’ Switch to degraded monitoring

Conclusion
This reentry trading system represents a complete automated trading solution with:

Deterministic behavior through the matrix system
Robust error handling at every level
Complete audit trail for compliance
Recursive reentry logic for trade chains
Multiple safety mechanisms for risk control

The system operates as a synchronized state machine ensuring consistent, predictable, and traceable execution of trading strategies while maintaining strict risk controls and comprehensive error recovery capabilities.
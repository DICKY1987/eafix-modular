# HUEY_P Trading System - Unified Complete Specification

**Status:** Production Specification v3.0  
**Document Type:** Unified Frontend GUI & Backend System Specification  
**Sources Merged:** 
- `huey_p_unified_gui_signals_spec_merged_currency_strength_ui_removed (1).md` 
- `integrated_economic_calendar_matrix_re_entry_system_spec_UPDATED__rev2.md`
**Generated:** 2025-09-06  
**Scope:** Complete system architecture covering frontend GUI, backend processing, and all integration components

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Identifier Systems](#2-identifier-systems)
3. [Architecture Components](#3-architecture-components)
4. [Signal Processing](#4-signal-processing)
5. [Economic Calendar System](#5-economic-calendar-system)
6. [Matrix Re-Entry System](#6-matrix-re-entry-system)
7. [Frontend GUI Specification](#7-frontend-gui-specification)
8. [Data Storage & Management](#8-data-storage--management)
9. [Risk & Portfolio Controls](#9-risk--portfolio-controls)
10. [Integration & Communication](#10-integration--communication)
11. [Monitoring & Testing](#11-monitoring--testing)
12. [Deployment & Operations](#12-deployment--operations)

---

# §1. System Overview

## §1.1 Purpose & Scope

This specification defines the complete HUEY_P trading system, integrating economic calendar processing, signal generation, currency strength analysis, and matrix re-entry capabilities into a unified trading environment. The system combines proactive (calendar-driven anticipation) and reactive (outcome-driven re-entry) trading strategies through a comprehensive GUI interface backed by robust processing systems.

### §1.1.1 Design Tenets
- **Unified Data Model**: Single source of truth for all trading decisions
- **Hierarchical Architecture**: Clear separation between presentation and business logic
- **Event-Driven Communication**: Pub/sub messaging for system coordination
- **Risk-First Design**: All decisions subject to risk and exposure controls
- **Audit Trail Integrity**: Complete traceability of all trading actions

### §1.1.2 System Objectives
1. Fuse calendar awareness with outcome and time-aware re-entries
2. Standardize identifiers and data flows for reproducible decisions
3. Enforce risk, exposure, and broker constraints
4. Provide comprehensive GUI for real-time trading operations
5. Enable advanced probability-based decision making

## §1.2 System Components

### §1.2.1 Frontend Components
- **Live Trading Dashboard**: Real-time signal monitoring and trade execution
- **Configuration Management**: Indicator and strategy parameter control
- **Signal Analysis Interface**: Historical and current signal evaluation
- **Template Management**: Trading strategy template versioning
- **Analytics Dashboard**: Performance tracking and KPI monitoring
- **System Status Console**: Health monitoring and operational controls

### §1.2.2 Backend Components
- **Economic Calendar Subsystem**: Event ingestion and processing
- **Multi-Dimensional Matrix Subsystem**: Complex decision matrix management
- **Re-Entry Subsystem**: Post-trade outcome analysis and re-entry logic
- **Signal Generation Engine**: Core trading signal computation
- **Risk Management Engine**: Portfolio-wide risk assessment and controls
- **Data Storage Layer**: Persistent storage and retrieval systems

### §1.2.3 Integration Components
- **MT4 Communication Bridge**: MQL4 integration for trade execution
- **DDE Price Feed Interface**: Real-time market data integration  
- **External API Connectors**: Third-party service integrations
- **Event Bus System**: Internal pub/sub messaging infrastructure

## §1.3 High-Level Data Flow

1. **Calendar Ingestion**: External economic events → CAL8 normalization → database storage
2. **Signal Generation**: Market conditions + calendar context → normalized signals → decision matrix
3. **Risk Assessment**: Signal evaluation → portfolio impact analysis → risk-adjusted decisions
4. **Trade Execution**: Decision output → MT4 integration → trade placement
5. **Outcome Analysis**: Trade results → matrix context computation → re-entry evaluation
6. **Continuous Monitoring**: Real-time system health → alerts → operator intervention

---

# §2. Identifier Systems

## §2.1 CAL8 Identifier System

### §2.1.1 Format Specification
The CAL8 system provides 8-character economic calendar identifiers with the following structure:
- **Position 1-3**: Currency code (e.g., "AUS", "USD", "EUR")
- **Position 4**: Impact level ("H" for high-impact events only)
- **Position 5-6**: Event type classification
- **Position 7-8**: Revision and version indicators

**Example**: `AUSHNF10` represents Australian high-impact non-farm employment data, revision 1, version 0.

### §2.1.2 Frontend Implementation
- **Display Format**: CAL8 identifiers shown with full event context in user interface
- **Validation**: Real-time format validation with immediate user feedback
- **Cross-Reference**: Clickable identifiers link to related calendar events and signals

### §2.1.3 Backend Implementation
The backend system implements comprehensive CAL8 identifier processing for economic calendar event management and cross-system correlation.

**Format Validation**:
- Input Validation: All calendar ingestion validates CAL8 format before database storage
- Normalization: Legacy CAL5 identifiers are upgraded to CAL8 format during migration
- Referential Integrity: CAL8 identifiers maintain foreign key relationships across all system tables

**Processing Pipeline**:
- Event Ingestion: Raw calendar events are assigned CAL8 identifiers during normalization
- Signal Generation: Trading signals reference originating CAL8 identifiers for traceability
- Matrix Integration: CAL8 identifiers are incorporated into Hybrid ID generation for matrix operations

**Database Schema**:
```sql
CREATE TABLE calendar_events (
    cal8_id CHAR(8) PRIMARY KEY CHECK (cal8_id GLOB '[A-Z][A-Z][A-Z]H[A-Z][A-Z][0-9][0-9]'),
    event_timestamp DATETIME NOT NULL,
    currency_code CHAR(3) NOT NULL,
    impact_level CHAR(1) CHECK (impact_level = 'H'),
    event_type CHAR(2) NOT NULL,
    revision_flag CHAR(1) DEFAULT '0',
    version_flag CHAR(1) DEFAULT '0'
);
```

## §2.2 Hybrid ID System

### §2.2.1 Composite Key Structure
Hybrid IDs link calendar events with matrix context for complete traceability:
- **Format**: `{CAL8}#{MATRIX_CONTEXT}#{TIMESTAMP}`
- **Example**: `AUSHNF10#LONG_EUR_15MIN#20250306T143000Z`

### §2.2.2 Frontend Integration
- **Context Display**: Hybrid IDs shown with expanded context information
- **Navigation**: Hybrid ID components clickable for drill-down analysis
- **Filtering**: Advanced filtering by Hybrid ID components

### §2.2.3 Backend Management
The backend manages Hybrid ID composite keys for comprehensive context preservation across calendar, matrix, and re-entry operations.

**Composite Key Generation**:
- Context Assembly: Hybrid IDs are constructed from validated CAL8 + matrix context + timestamp
- Uniqueness Enforcement: Database constraints ensure system-wide Hybrid ID uniqueness
- Referential Integrity: Foreign key relationships maintained across all dependent tables

**Usage Patterns**:
- Trade Correlation: All trade decisions linked to originating Hybrid ID
- Re-entry Logic: Post-trade analysis uses Hybrid ID for context reconstruction
- Audit Trails: Complete decision history traceable through Hybrid ID chains

---

# §3. Architecture Components

## §3.1 Core Runtime Services

### §3.1.1 EventBus (Pub/Sub System)
**Purpose**: Central messaging system for component communication

**Frontend Implementation**:
- Event Types: `signal_update`, `trade_executed`, `risk_alert`, `system_status`
- Subscriber Management: Components register for specific event types
- Message Queuing: Buffered delivery with retry logic for failed subscribers
- Metrics Collection: Event throughput and latency monitoring

**Backend Implementation**:
- Message Routing: Topic-based routing with pattern matching
- Persistence: Critical events stored for audit and replay
- Cross-Process Communication: Inter-service messaging via message queues
- Error Handling: Dead letter queues for undeliverable messages

### §3.1.2 StateManager (Application State)
**Purpose**: Centralized state management with snapshot capabilities

**Frontend Features**:
- State Snapshots: Point-in-time application state capture
- Action Replay: State reconstruction from action history
- Component Synchronization: Automatic UI updates on state changes
- Persistence: State preservation across application restarts

**Backend Features**:
- Transaction Management: ACID compliance for state modifications
- Concurrent Access: Multi-user state coordination
- Change Tracking: Complete audit trail of state modifications
- Backup/Recovery: Automated state backup and restoration procedures

### §3.1.3 Feature Registry
**Purpose**: Dynamic registration and management of indicators, views, and tools

**Registration System**:
- Plugin Discovery: Automatic detection of available features
- Dependency Resolution: Feature dependency management and validation
- Version Management: Feature versioning and compatibility checking
- Hot Loading: Runtime feature addition and removal without restart

**Schema Management**:
- Parameter Definitions: Typed parameter schemas for each feature
- Validation Rules: Runtime parameter validation and constraint checking
- Default Values: Sensible default configurations for new features
- Documentation Integration: Inline help and documentation for all parameters

### §3.1.4 Theme System
**Purpose**: Consistent visual styling and semantic tokens

**Token System**:
- Color Palettes: Semantic color definitions (primary, secondary, error, warning)
- Typography: Font families, sizes, and weights for different contexts
- Spacing: Consistent spacing units and layout measurements
- Component Styles: Reusable style definitions for UI components

**Dynamic Theming**:
- User Preferences: Individual theme customization and persistence
- System Integration: OS theme detection and automatic switching
- Accessibility: High contrast and accessibility-compliant color schemes
- Custom Themes: User-defined theme creation and sharing

### §3.1.5 Toast/Alert Manager
**Purpose**: User notification and alert management

**Message Queuing**:
- Priority Levels: Critical, warning, info, and success message types
- Queue Management: Message ordering and automatic dismissal
- Rate Limiting: Prevention of notification spam and flooding
- Persistence: Critical alerts preserved across sessions

**Alert Types**:
- System Alerts: Infrastructure and connectivity issues
- Trading Alerts: Trade execution, profit/loss, and position updates
- Risk Alerts: Margin, exposure, and risk limit notifications
- Informational: General system status and operational updates

### §3.1.6 Risk Ribbon
**Purpose**: Real-time risk posture summary display

**Risk Metrics**:
- Portfolio Exposure: Current total exposure across all positions
- Margin Utilization: Used vs. available margin percentages
- Risk Limits: Proximity to configured risk thresholds
- P&L Summary: Current profit/loss and daily performance metrics

**Visual Indicators**:
- Color Coding: Green (safe), yellow (caution), red (critical) status indicators
- Trend Arrows: Direction of risk metric changes over time
- Alert Integration: Direct connection to alert system for threshold breaches
- Historical Context: Short-term trend information for context

## §3.2 App Layout & Navigation

### §3.2.1 Main Interface Structure
**Layout Type**: Tabbed interface with persistent header and status ribbon

**Header Components**:
- System Status: Connection status indicators for MT4, data feeds, and external services  
- Risk Ribbon: Real-time risk metrics display
- User Controls: Account selection, emergency stop, and system controls
- Navigation: Tab switching and quick access to critical functions

**Tab Organization**:
- Primary Tabs: Live, Config, Signals, Templates, Trade History, History/Analytics
- Secondary Tabs: DDE Price Feed, Economic Calendar, System Status, Reentry Matrix
- Context-Sensitive: Additional tabs appear based on active features and user permissions

### §3.2.2 Grid Manager (Panel System)
**Purpose**: Flexible panel arrangement within tabs

**Panel Types**:
- Data Panels: Tables, charts, and data visualization components
- Control Panels: Configuration, settings, and input forms
- Status Panels: Monitoring, alerts, and system health information
- Custom Panels: User-defined panel configurations

**Management Features**:
- Drag & Drop: Panel repositioning and resizing
- Layout Persistence: User layout preferences saved and restored
- Default Layouts: Predefined optimal layouts for different use cases
- Responsive Design: Automatic layout adaptation for different screen sizes

---

# §4. Signal Processing

## §4.1 Normalized Signal Model

### §4.1.1 Core Fields
All signals conform to standardized structure for consistent processing:

**Required Fields**:
```yaml
id: unique_signal_identifier
timestamp: ISO8601_UTC_timestamp  
source: signal_generation_system
symbol: trading_pair (e.g., "EURUSD", "GBPJPY")
kind: signal_type ("ENTRY", "EXIT", "MODIFY")
direction: trade_direction ("LONG", "SHORT", "NEUTRAL")
strength: signal_strength (0.0-1.0)
confidence: confidence_level (0.0-1.0)
```

**Optional Fields**:
```yaml
entry_price: suggested_entry_level
stop_loss: risk_management_level  
take_profit: profit_target_level
expiry_time: signal_validity_period
volume_suggestion: position_size_hint
```

### §4.1.2 Frontend Signal Display
**Signal Table Columns**:
- Timestamp: Local time conversion with UTC tooltip
- Symbol: Trading pair with current price display
- Direction: Visual indicators (↑ LONG, ↓ SHORT, — NEUTRAL)
- Strength: Progress bar visualization (0-100%)
- Confidence: Color-coded indicator (red/yellow/green)
- Actions: Execute, modify, dismiss buttons

**Real-Time Updates**:
- Live Streaming: WebSocket updates every 500ms maximum
- Batch Processing: Maximum 50 signals per update to prevent UI lag
- Visual Feedback: Smooth transitions for signal updates
- Alert Integration: High-priority signals trigger toast notifications

### §4.1.3 Backend Signal Generation
**Processing Pipeline**:
1. Market Data Ingestion: Real-time price and volume data collection
2. Technical Analysis: Indicator calculations and pattern recognition
3. Calendar Integration: Economic event impact assessment
4. Risk Assessment: Position sizing and risk-adjusted strength calculation
5. Signal Validation: Format compliance and business rule verification
6. Distribution: Signal routing to frontend and execution systems

**Validation Rules**:
- Schema Compliance: 100% adherence to normalized signal structure
- Business Rules: Symbol validity, direction consistency, reasonable price levels
- Temporal Constraints: Signal freshness and expiry validation
- Risk Limits: Position sizing within portfolio constraints

## §4.2 Probability Extension Fields

### §4.2.1 Advanced Analytics Fields
Extended signal structure for probability-based decision making:

**Probability Metrics**:
```yaml
success_probability: estimated_probability_of_profit (0.0-1.0)
risk_reward_ratio: expected_risk_vs_reward_multiple
win_rate_historical: historical_success_rate_for_similar_signals
drawdown_risk: maximum_expected_adverse_excursion
correlation_factors: market_correlation_influences
```

**Statistical Context**:
```yaml
sample_size: number_of_historical_similar_signals
confidence_interval: statistical_confidence_bounds
data_quality_score: reliability_of_underlying_data
model_version: algorithm_version_for_reproducibility
```

### §4.2.2 Frontend Probability Display
**Probability Visualization**:
- Success Rate: Percentage display with historical comparison
- Risk/Reward: Visual ratio with break-even analysis
- Confidence Bands: Statistical uncertainty ranges
- Historical Context: Similar signal performance data

**Advanced Controls**:
- Probability Thresholds: User-configurable minimum probability requirements
- Model Selection: Choice between different probability calculation methods
- Backtesting Integration: Historical performance analysis for signal types
- Custom Weighting: User adjustment of probability factors

### §4.2.3 Backend Probability Calculation
**Calculation Engine**:
- Historical Analysis: Statistical analysis of similar market conditions
- Machine Learning: Pattern recognition and outcome prediction
- Risk Modeling: Monte Carlo simulation for risk assessment
- Real-Time Adaptation: Model updates based on recent market behavior

**Data Sources**:
- Price History: Historical price and volume data
- Economic Events: Calendar event outcomes and market reactions
- Portfolio Performance: Historical trade results and patterns
- Market Conditions: Volatility, correlation, and market regime indicators

## §4.3 Contract Guarantees

### §4.3.1 Signal Delivery Guarantees
**Reliability Standards**:
- Delivery Assurance: 99.9% signal delivery within SLA timeframes
- Order Preservation: Signals delivered in chronological order
- Duplicate Prevention: Unique signal identification prevents duplicates
- Error Handling: Graceful degradation and error recovery procedures

**Quality Assurance**:
- Format Validation: 100% schema compliance before delivery
- Content Validation: Business rule verification for all signal fields
- Timeliness Validation: Signal freshness and relevance checking
- Integrity Verification: Checksums and tamper detection

### §4.3.2 Processing Time Commitments
**Performance SLAs**:
- Signal Generation: Maximum 1 second from trigger event to signal creation
- Frontend Update: Maximum 500ms from signal creation to UI display
- Risk Assessment: Maximum 2 seconds for complete risk analysis
- Historical Analysis: Maximum 5 seconds for probability calculations

**Monitoring and Alerting**:
- Performance Metrics: Real-time latency and throughput monitoring
- SLA Violations: Automatic alerts for performance threshold breaches  
- Trend Analysis: Historical performance trend tracking
- Capacity Planning: Proactive scaling based on performance metrics

---

# §5. Economic Calendar System

## §5.1 Event Ingestion & Processing

### §5.1.1 Data Sources
**Primary Sources**:
- Forex Factory: Primary economic event data provider
- Bloomberg API: Institutional-grade event details and revisions
- Reuters: News and event confirmation services
- Central Bank Feeds: Direct feeds from major central banks

**Data Validation**:
- Source Correlation: Cross-validation between multiple data providers
- Timestamp Normalization: UTC conversion with DST handling
- Event Deduplication: Duplicate event detection and consolidation
- Data Quality Scoring: Reliability assessment for each data source

### §5.1.2 CAL8 Event Processing
**Ingestion Pipeline**:
1. Raw Event Acquisition: Scheduled polling and real-time webhook processing
2. Format Normalization: Conversion to standardized event structure
3. CAL8 Assignment: Unique identifier generation per specification
4. Validation: Format compliance and business rule verification
5. Database Storage: Persistent storage with indexing and relationships

**Event Normalization Rules**:
- Currency Standardization: ISO 4217 currency code enforcement
- Impact Classification: Consistent high/medium/low impact scoring
- Event Type Mapping: Standardized event category assignment
- Time Zone Handling: UTC normalization with original timezone preservation

### §5.1.3 Real-Time Event Updates
**Update Processing**:
- Event Revisions: Handling of revised forecasts and actual values
- Last-Minute Changes: Schedule changes and event cancellations
- Flash Updates: Breaking news and unscheduled announcements
- Market Impact Assessment: Real-time market reaction analysis

**Frontend Event Display**:
- Live Calendar: Real-time event schedule with countdown timers
- Impact Indicators: Visual impact level representation
- Revision Tracking: Historical revision display and change highlighting
- Market Reaction: Live price movement correlation with events

## §5.2 High-Impact Event Processing

### §5.2.1 Event Classification
**High-Impact Criteria**:
- Market Moving Potential: Historical price movement analysis
- Trading Volume Impact: Expected volume increase measurement
- Currency Correlation: Multi-currency pair impact assessment
- Time Sensitivity: Market reaction timing and duration analysis

**Classification Algorithm**:
- Historical Analysis: Statistical analysis of past event impacts
- Market Conditions: Current volatility and liquidity considerations
- Economic Significance: GDP impact and economic indicator importance
- Central Bank Relevance: Monetary policy decision influence

### §5.2.2 Alert System
**Alert Generation**:
- Pre-Event Alerts: Configurable advance warning times
- Real-Time Alerts: Live event occurrence notifications
- Post-Event Analysis: Market reaction summaries and analysis
- Impact Assessment: Actual vs. expected impact evaluation

**Alert Delivery**:
- GUI Notifications: In-application toast and modal alerts
- Audio Alerts: Configurable sound notifications for critical events
- External Notifications: Email, SMS, and push notification support
- Trading System Integration: Direct alerts to automated trading systems

### §5.2.3 Trading Impact Analysis
**Market Reaction Tracking**:
- Price Movement: Real-time price change correlation with events
- Volume Analysis: Trading volume spikes and duration measurement
- Spread Monitoring: Bid-ask spread widening during event periods
- Volatility Assessment: Implied and realized volatility changes

**Decision Support**:
- Trade Timing: Optimal entry and exit timing around events
- Position Sizing: Risk-adjusted position sizing for event periods
- Hedge Requirements: Hedging strategies for event exposure
- Recovery Analysis: Post-event market normalization patterns

## §5.3 Event Correlation & Signal Integration

### §5.3.1 Signal-Event Correlation
**Correlation Analysis**:
- Event Proximity: Signal generation timing relative to events
- Market Condition Context: Correlation with overall market conditions
- Historical Performance: Similar event and signal combination outcomes
- Risk Adjustment: Event-based risk factor modifications

**Integration Rules**:
- Signal Filtering: Event-based signal suppression or enhancement
- Timing Adjustments: Signal execution timing around major events
- Risk Scaling: Position size adjustments based on event schedules
- Alert Coordination: Combined signal and event notification strategies

### §5.3.2 Calendar-Driven Strategy Adjustments
**Strategy Modifications**:
- Pre-Event Positioning: Proactive position adjustments before events
- Event Window Trading: Specialized strategies for event periods
- Post-Event Analysis: Outcome-based strategy refinement
- Long-Term Adaptation: Strategy evolution based on event performance

**Risk Management Integration**:
- Event Risk Limits: Special risk limits during high-impact periods
- Exposure Controls: Maximum exposure limits around major events
- Stop-Loss Adjustments: Modified stop-loss levels for event periods
- Portfolio Hedging: Portfolio-wide hedging strategies for event clusters

---

# §6. Matrix Re-Entry System

## §6.1 Matrix Context Framework

### §6.1.1 Multi-Dimensional Matrix Structure
**Primary Dimensions**:
- **Outcome Dimension**: Trade result classification (WIN, LOSS, BREAKEVEN)
- **Duration Dimension**: Trade holding period categories (SCALP, INTRADAY, SWING, POSITION)
- **Generation Dimension**: Signal source and methodology (CALENDAR, TECHNICAL, FUNDAMENTAL)
- **Time Dimension**: Market session and time-of-day factors

**Secondary Dimensions**:
- Market Conditions: Volatility regime (LOW, MEDIUM, HIGH)
- Economic Context: Event proximity and impact level
- Portfolio State: Current exposure and risk levels
- Correlation Factors: Inter-currency and inter-asset correlations

### §6.1.2 Context State Machine
**State Definitions**:
- **IDLE**: No active positions, waiting for signals
- **POSITIONED**: Active position held, monitoring for exit signals
- **EXITED**: Position closed, evaluating outcome for re-entry
- **RE_ENTRY_EVAL**: Analyzing conditions for potential re-entry
- **COOLDOWN**: Temporary restriction period before next entry

**State Transitions**:
- IDLE → POSITIONED: Signal execution and position opening
- POSITIONED → EXITED: Position closure (stop-loss, take-profit, or manual)
- EXITED → RE_ENTRY_EVAL: Outcome analysis and re-entry assessment
- RE_ENTRY_EVAL → POSITIONED: Re-entry signal execution
- RE_ENTRY_EVAL → COOLDOWN: No re-entry, waiting period imposed
- COOLDOWN → IDLE: Cooldown period completion

### §6.1.3 Parameter Set Selection
**Selection Criteria**:
- Historical Performance: Parameter effectiveness in similar contexts
- Risk Tolerance: Current portfolio risk capacity
- Market Conditions: Volatility and liquidity considerations
- Time Constraints: Available trading time and session factors

**Fallback Strategies**:
- Primary Parameters: Optimal parameters for current context
- Secondary Parameters: Alternative parameters if primary unavailable
- Default Parameters: Conservative fallback for undefined contexts
- Emergency Parameters: Crisis-mode parameters for extreme conditions

## §6.2 Re-Entry Logic Engine

### §6.2.1 Outcome Analysis
**Trade Result Processing**:
- P&L Calculation: Precise profit/loss calculation including fees
- Duration Analysis: Actual vs. expected holding period evaluation
- Execution Quality: Slippage and execution efficiency assessment
- Market Impact: Trade's influence on subsequent market movement

**Context Reconstruction**:
- Entry Conditions: Original market conditions and signals
- Exit Triggers: Reason for position closure and trigger analysis
- Market Evolution: How market conditions changed during trade
- Correlation Effects: Impact of correlated positions and events

### §6.2.2 Re-Entry Decision Matrix
**Decision Factors**:
- Outcome Quality: Trade result relative to expectations
- Market Conditions: Current vs. original entry conditions
- Time Factors: Time elapsed since exit and market session
- Risk Factors: Current portfolio exposure and risk capacity

**Decision Algorithm**:
```yaml
if outcome == WIN and market_conditions_similar:
    probability_modifier = +0.2
elif outcome == LOSS and market_conditions_changed:
    probability_modifier = -0.1
elif outcome == BREAKEVEN:
    probability_modifier = 0.0

base_probability = historical_success_rate
adjusted_probability = base_probability + probability_modifier

if adjusted_probability > re_entry_threshold:
    initiate_re_entry_process()
else:
    enter_cooldown_period()
```

### §6.2.3 Risk-Adjusted Re-Entry
**Risk Assessment**:
- Portfolio Impact: Effect on overall portfolio risk profile
- Concentration Limits: Currency and sector concentration checks
- Correlation Analysis: Impact of correlated positions
- Drawdown Considerations: Current drawdown vs. limits

**Position Sizing**:
- Outcome-Based Sizing: Larger positions after wins, smaller after losses
- Volatility Adjustment: Size adjustment based on current market volatility
- Risk Budget Allocation: Position sizing within available risk budget
- Kelly Criterion: Optimal sizing based on probability and risk-reward

## §6.3 Hybrid ID Integration

### §6.3.1 Context Preservation
**Data Continuity**:
- Original Context: Complete preservation of initial trade context
- Evolution Tracking: Changes in context over time
- Relationship Mapping: Connections between related trades and decisions
- Audit Trail: Complete history of all re-entry decisions and outcomes

**Context Inheritance**:
- Parameter Inheritance: Relevant parameters passed to re-entry decisions
- Risk Inheritance: Risk factors and limits carried forward
- Performance Inheritance: Historical performance context preservation
- Strategy Inheritance: Strategic context and methodology continuity

### §6.3.2 Traceability Framework
**Decision Lineage**:
- Original Decision: Initial trade decision with full context
- Re-Entry Decisions: Subsequent re-entry decisions and rationale
- Parameter Evolution: How parameters changed over re-entry cycles
- Outcome Correlation: Performance correlation across re-entry cycles

**Audit Capabilities**:
- Complete History: Full decision history for any trade sequence
- Performance Attribution: Contribution analysis for each re-entry
- Risk Attribution: Risk contribution tracking across cycles
- Strategy Effectiveness: Overall strategy performance across sequences

---

# §7. Frontend GUI Specification

## §7.1 Live Trading Tab

### §7.1.1 Key Panels
**Signal Monitor Panel**:
- Active Signals: Currently valid trading signals with real-time updates
- Signal Queue: Pending signals awaiting execution decisions
- Signal History: Recently processed signals with outcomes
- Filter Controls: Symbol, timeframe, strategy, and confidence filtering

**Position Status Panel**:
- Open Positions: Current positions with P&L, risk metrics, and exit options
- Position Summary: Total exposure, margin usage, and risk metrics
- Pending Orders: Unfilled orders with modification and cancellation options
- Account Summary: Account balance, equity, and available margin

**Market Data Panel**:
- Price Feeds: Real-time price data for configured symbols
- Economic Events: Upcoming high-impact economic events
- Market News: Relevant news and market-moving information
- Correlation Matrix: Inter-currency correlation coefficients

### §7.1.2 Filters & Controls
**Signal Filtering**:
- Confidence Threshold: Minimum confidence level slider (0-100%)
- Symbol Selection: Multi-select dropdown for trading pairs
- Strategy Filter: Checkbox selection for signal generation methods
- Time Range: Date/time range picker for historical analysis

**Risk Controls**:
- Maximum Position Size: Global position size limit controls
- Risk Per Trade: Percentage risk per individual trade setting
- Daily Loss Limit: Maximum daily loss before trading halt
- Emergency Stop: One-click position closure and trading halt

**Display Options**:
- Refresh Rate: Update frequency selection (1s, 5s, 10s, 30s)
- Chart Integration: Toggle price charts for selected symbols
- Alert Settings: Audio and visual alert configuration
- Color Scheme: Light/dark theme selection with custom options

### §7.1.3 Control Buttons & Actions
**Trade Execution**:
- Execute Signal: Single-click signal execution with confirmation
- Modify Order: Order modification with new parameters
- Close Position: Immediate position closure options
- Close All: Emergency closure of all open positions

**Risk Management**:
- Set Stop Loss: Drag-and-drop or numeric stop loss setting
- Set Take Profit: Profit target setting with R:R calculation
- Position Sizing: Kelly criterion or fixed percentage sizing
- Risk Assessment: Real-time position risk analysis

### §7.1.4 Acceptance Criteria
**Performance Requirements**:
- Signal Display: All valid signals displayed within 500ms of generation
- Position Updates: Real-time P&L updates every second
- Order Execution: Trade orders processed within 2 seconds
- Risk Calculations: Risk metrics updated within 100ms of position changes

**Reliability Requirements**:
- Data Integrity: 100% accuracy in displayed position and P&L data
- Signal Validity: Only valid, unexpired signals displayed
- Risk Compliance: All trades subject to configured risk limits
- Audit Trail: All user actions logged with timestamps

## §7.2 Configuration Tab

### §7.2.1 Global Settings
**System Configuration**:
- Connection Settings: MT4 connection parameters and authentication
- Data Feed Settings: Price feed configuration and failover options
- Time Zone Settings: Local time zone and UTC offset configuration
- Logging Level: System logging verbosity and retention settings

**Risk Settings**:
- Global Risk Limits: Maximum portfolio exposure and leverage limits
- Position Limits: Maximum position size per symbol and total
- Drawdown Limits: Maximum daily, weekly, and monthly loss limits
- Margin Settings: Minimum margin requirements and buffer settings

**Notification Settings**:
- Alert Preferences: Audio, visual, and external notification settings
- Event Notifications: Economic event and news alert configuration
- Risk Alerts: Risk limit breach notification preferences
- Performance Alerts: Profit/loss milestone notifications

### §7.2.2 Indicator & Strategy Configuration
**Parameter Management**:
- Indicator Parameters: Technical indicator settings and optimization
- Strategy Parameters: Trading strategy configuration and backtesting
- Signal Filters: Signal filtering and ranking criteria
- Execution Parameters: Order execution and slippage settings

**Auto-Generated Forms**:
- Dynamic Forms: Automatic form generation from parameter schemas
- Validation Rules: Real-time parameter validation and constraint checking
- Default Values: Intelligent default parameter suggestions
- Help Integration: Context-sensitive help and documentation

**Template Integration**:
- Configuration Templates: Predefined configuration sets for different strategies
- Template Versioning: Version control for configuration templates
- Import/Export: Configuration backup and sharing capabilities
- Rollback Options: Configuration change history and rollback functionality

### §7.2.3 Dependency Management
**Parameter Dependencies**:
- Dependency Validation: Automatic checking of parameter interdependencies
- Conflict Resolution: Detection and resolution of conflicting settings
- Impact Analysis: Assessment of configuration change impacts
- Change Propagation: Automatic updating of dependent parameters

**Configuration Validation**:
- Pre-Deployment Testing: Configuration testing before activation
- Simulation Mode: Risk-free testing of new configurations
- Rollback Capability: Instant rollback to previous working configurations
- Change Approval: Multi-step approval process for critical changes

### §7.2.4 Control Buttons & Actions
**Configuration Management**:
- Save Configuration: Persistent storage of current settings
- Load Template: Application of predefined configuration templates
- Export Settings: Configuration backup and sharing functionality
- Reset to Defaults: Restoration of factory default settings

**Validation & Testing**:
- Validate Settings: Comprehensive configuration validation
- Test Connection: Connection testing for external services
- Simulate Strategy: Risk-free strategy simulation with historical data
- Deploy Configuration: Activation of new configuration settings

## §7.3 Signals Tab

### §7.3.1 Signal Table Columns
**Core Information**:
- Timestamp: Signal generation time with local and UTC display
- Symbol: Trading pair with current market price
- Direction: Visual directional indicators (LONG/SHORT/NEUTRAL)
- Strength: Numerical and bar chart strength representation (0-100%)
- Confidence: Color-coded confidence levels with tooltips

**Advanced Metrics**:
- Success Probability: Historical success rate for similar signals
- Risk/Reward: Expected risk-to-reward ratio
- Entry Price: Suggested entry level with current price comparison
- Stop Loss: Recommended stop loss level with risk calculation
- Take Profit: Profit target with potential reward calculation

**Contextual Data**:
- Signal Source: Generation method (Technical, Calendar, Fundamental)
- Economic Context: Relevant upcoming economic events
- Market Conditions: Current volatility and liquidity assessment
- Correlation Factors: Related currency and market correlations

### §7.3.2 Interactive Features
**Signal Actions**:
- Execute: Direct signal execution with position sizing options
- Modify: Signal parameter modification before execution
- Dismiss: Signal rejection with reason code selection
- Save: Signal bookmarking for future reference

**Analysis Tools**:
- Historical Performance: Past performance of similar signals
- Backtest Results: Strategy backtesting data for signal type
- Risk Analysis: Comprehensive risk assessment before execution
- Market Impact: Expected market impact of signal execution

**Filtering & Sorting**:
- Multi-Column Sorting: Complex sorting by multiple criteria
- Advanced Filtering: Complex filter combinations with saved presets
- Search Functionality: Text search across all signal attributes
- Group By Options: Signal grouping by symbol, strategy, or time

### §7.3.3 Signal Lifecycle Management
**Status Tracking**:
- Active: Currently valid and executable signals
- Executed: Signals converted to open positions
- Expired: Signals that have passed validity period
- Rejected: Manually or automatically rejected signals

**Performance Tracking**:
- Execution Rate: Percentage of signals actually executed
- Success Rate: Percentage of executed signals resulting in profit
- Average Return: Mean return per executed signal
- Risk-Adjusted Return: Return adjusted for risk taken

### §7.3.4 Control Buttons & Actions
**Bulk Operations**:
- Execute Selected: Batch execution of multiple selected signals
- Dismiss All: Bulk dismissal of unwanted signals
- Export Signals: Signal data export for external analysis
- Import Filters: Import of predefined filter configurations

**Analysis Functions**:
- Performance Report: Comprehensive signal performance analysis
- Strategy Comparison: Comparative analysis of different signal sources
- Risk Assessment: Portfolio-level risk analysis of selected signals
- Optimization: Signal parameter optimization based on historical performance

## §7.4 Templates Tab

### §7.4.1 Template Management Features
**Template Operations**:
- Create Template: New template creation from current configuration
- Edit Template: Modification of existing template parameters
- Duplicate Template: Template copying with customization options
- Delete Template: Safe template removal with dependency checking

**Version Control**:
- Version History: Complete history of template modifications
- Diff Visualization: Side-by-side comparison of template versions
- Rollback Options: Restoration of previous template versions
- Branch Management: Template branching for experimental modifications

**Import/Export**:
- Template Export: Backup and sharing of template configurations
- Template Import: Import of external template files
- Bulk Operations: Mass import/export of multiple templates
- Format Conversion: Conversion between different template formats

### §7.4.2 Template Validation
**Validation Rules**:
- Parameter Validation: Checking of all template parameters
- Dependency Checking: Validation of template dependencies
- Performance Testing: Backtesting of template configurations
- Risk Assessment: Risk analysis of template-based strategies

**Quality Assurance**:
- Best Practice Checking: Comparison against established best practices
- Performance Benchmarking: Comparison with baseline performance metrics
- Risk Compliance: Verification of risk management compliance
- Documentation Requirements: Completeness of template documentation

### §7.4.3 Template Usage Analytics
**Usage Tracking**:
- Usage Frequency: Tracking of template usage patterns
- Performance Metrics: Real-time performance of active templates
- User Feedback: User ratings and feedback on template effectiveness
- Optimization Suggestions: AI-driven template improvement recommendations

**Comparative Analysis**:
- Template Comparison: Side-by-side performance comparison
- A/B Testing: Controlled testing of template variations
- Performance Attribution: Analysis of template contribution to overall performance
- Market Condition Analysis: Template performance under different market conditions

### §7.4.4 Control Buttons & Actions
**Template Management**:
- Apply Template: Application of template to current configuration
- Save as Template: Conversion of current settings to reusable template
- Share Template: Template sharing with other users or teams
- Archive Template: Long-term storage of unused templates

**Testing & Validation**:
- Test Template: Risk-free testing of template configurations
- Validate Template: Comprehensive template validation
- Optimize Template: Automated template parameter optimization
- Deploy Template: Activation of template for live trading

## §7.5 Additional Tabs

### §7.5.1 Trade History Tab
**Trade Data Display**:
- Trade List: Complete history of all executed trades
- P&L Analysis: Profit/loss breakdown by time period, symbol, and strategy
- Performance Metrics: Key performance indicators and statistics
- Risk Metrics: Risk-adjusted returns and drawdown analysis

**Filtering & Analysis**:
- Date Range Filtering: Custom date range selection for analysis
- Symbol Filtering: Analysis by specific trading pairs
- Strategy Performance: Performance breakdown by strategy type
- Export Options: Data export in multiple formats (CSV, Excel, PDF)

### §7.5.2 History/Analytics Tab
**System Logs**:
- Application Logs: System events and error logs
- Trade Logs: Detailed trade execution logs
- Performance Logs: System performance and latency logs
- Error Logs: Error events and resolution tracking

**Analytics Dashboard**:
- Performance KPIs: Key performance indicators and trends
- Risk Analytics: Risk metrics and compliance monitoring
- Strategy Analytics: Strategy performance and optimization metrics
- System Analytics: System health and performance metrics

### §7.5.3 DDE Price Feed Tab
**Connection Management**:
- Connection Status: Real-time connection status to DDE sources
- Feed Configuration: Price feed source configuration and settings
- Subscription Management: Symbol subscription and management
- Error Handling: Connection error detection and recovery

**Data Display**:
- Live Price Table: Real-time price data for subscribed symbols
- Historical Data: Historical price data access and analysis
- Data Quality Metrics: Data completeness and accuracy metrics
- Export Functions: Price data export and analysis tools

### §7.5.4 Economic Calendar Tab
**Event Display**:
- Calendar View: Economic events in calendar format
- Event List: Detailed list of upcoming and past events
- Event Filtering: Filtering by currency, impact level, and event type
- Event Details: Comprehensive event information and analysis

**Integration Features**:
- Trading Integration: Direct integration with trading signals and decisions
- Alert Configuration: Event-based alert and notification setup
- Historical Analysis: Historical event impact analysis
- Market Correlation: Analysis of event impact on market movements

### §7.5.5 System Status Tab
**Health Monitoring**:
- System Health: Overall system health and status indicators
- Component Status: Individual component health monitoring
- Performance Metrics: System performance and resource utilization
- Alert Management: System alert configuration and management

**Operational Tools**:
- Log Viewer: Real-time log viewing and analysis
- Configuration Management: System configuration and settings management
- Backup/Recovery: System backup and recovery operations
- Maintenance Tools: System maintenance and optimization tools

### §7.5.6 Re-entry Matrix Tab
**Matrix Visualization**:
- Decision Matrix: Visual representation of re-entry decision matrix
- Context Analysis: Analysis of market context and conditions
- Parameter Display: Current parameter settings and adjustments
- Performance Tracking: Re-entry strategy performance monitoring

**Configuration Tools**:
- Matrix Configuration: Re-entry matrix parameter configuration
- Rule Management: Re-entry rule creation and management
- Testing Tools: Re-entry strategy testing and validation
- Optimization Tools: Automated optimization of re-entry parameters

---

# §8. Data Storage & Management

## §8.1 Database Architecture

### §8.1.1 Core Database Schema
**Primary Tables**:

```sql
-- Calendar Events with CAL8 identifiers
CREATE TABLE calendar_events (
    cal8_id CHAR(8) PRIMARY KEY,
    event_timestamp DATETIME NOT NULL,
    currency_code CHAR(3) NOT NULL,
    impact_level CHAR(1) CHECK (impact_level = 'H'),
    event_type CHAR(2) NOT NULL,
    event_description TEXT,
    forecast_value DECIMAL(15,4),
    actual_value DECIMAL(15,4),
    previous_value DECIMAL(15,4),
    revision_flag CHAR(1) DEFAULT '0',
    version_flag CHAR(1) DEFAULT '0',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Trading Signals
CREATE TABLE trading_signals (
    signal_id VARCHAR(64) PRIMARY KEY,
    cal8_id CHAR(8),
    hybrid_id VARCHAR(128),
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    direction VARCHAR(10) CHECK (direction IN ('LONG', 'SHORT', 'NEUTRAL')),
    strength DECIMAL(3,2) CHECK (strength BETWEEN 0.0 AND 1.0),
    confidence DECIMAL(3,2) CHECK (confidence BETWEEN 0.0 AND 1.0),
    entry_price DECIMAL(15,5),
    stop_loss DECIMAL(15,5),
    take_profit DECIMAL(15,5),
    expiry_time DATETIME,
    success_probability DECIMAL(3,2),
    risk_reward_ratio DECIMAL(5,2),
    signal_source VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cal8_id) REFERENCES calendar_events(cal8_id)
);

-- Trade Executions
CREATE TABLE trade_executions (
    trade_id VARCHAR(64) PRIMARY KEY,
    signal_id VARCHAR(64),
    hybrid_id VARCHAR(128),
    symbol VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    entry_price DECIMAL(15,5) NOT NULL,
    exit_price DECIMAL(15,5),
    position_size DECIMAL(15,2) NOT NULL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME,
    pnl DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'OPEN',
    trade_context TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (signal_id) REFERENCES trading_signals(signal_id)
);

-- Matrix Parameters
CREATE TABLE matrix_parameters (
    parameter_id VARCHAR(64) PRIMARY KEY,
    parameter_set_name VARCHAR(100) NOT NULL,
    outcome_dimension VARCHAR(20),
    duration_dimension VARCHAR(20),
    generation_dimension VARCHAR(20),
    time_dimension VARCHAR(20),
    parameter_values JSON NOT NULL,
    effectiveness_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Re-entry Decisions
CREATE TABLE reentry_decisions (
    decision_id VARCHAR(64) PRIMARY KEY,
    parent_trade_id VARCHAR(64) NOT NULL,
    hybrid_id VARCHAR(128),
    decision_type VARCHAR(20) NOT NULL,
    decision_timestamp DATETIME NOT NULL,
    market_context JSON,
    probability_factors JSON,
    decision_rationale TEXT,
    approved BOOLEAN DEFAULT FALSE,
    executed BOOLEAN DEFAULT FALSE,
    outcome_analysis JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_trade_id) REFERENCES trade_executions(trade_id)
);
```

### §8.1.2 Indexing Strategy
**Primary Indexes**:
```sql
-- Performance-critical indexes
CREATE INDEX idx_calendar_events_timestamp ON calendar_events(event_timestamp);
CREATE INDEX idx_calendar_events_currency ON calendar_events(currency_code);
CREATE INDEX idx_trading_signals_timestamp ON trading_signals(timestamp);
CREATE INDEX idx_trading_signals_symbol ON trading_signals(symbol);
CREATE INDEX idx_trade_executions_entry_time ON trade_executions(entry_time);
CREATE INDEX idx_trade_executions_symbol ON trade_executions(symbol);

-- Composite indexes for common queries
CREATE INDEX idx_signals_symbol_timestamp ON trading_signals(symbol, timestamp);
CREATE INDEX idx_trades_symbol_status ON trade_executions(symbol, status);
CREATE INDEX idx_calendar_currency_impact ON calendar_events(currency_code, impact_level);

-- Full-text indexes for search functionality
CREATE VIRTUAL TABLE calendar_events_fts USING fts5(
    cal8_id, event_description, content=calendar_events
);
```

### §8.1.3 Data Integrity & Constraints
**Referential Integrity**:
- Foreign key constraints ensure data consistency across all related tables
- Cascade delete rules prevent orphaned records
- Check constraints validate data ranges and enum values
- Unique constraints prevent duplicate key violations

**Data Validation Rules**:
- CAL8 format validation: Regular expression pattern matching
- Signal strength/confidence: Range validation (0.0-1.0)
- Price data: Positive value constraints and reasonable range checking
- Timestamp validation: UTC format enforcement and future date restrictions

## §8.2 Data Lifecycle Management

### §8.2.1 Data Retention Policies
**Calendar Events**:
- Historical Events: Retain indefinitely for backtesting and analysis
- Future Events: Retain until 30 days after event occurrence
- Cancelled Events: Retain for 90 days for audit purposes
- Data Cleanup: Automated cleanup of obsolete revision records

**Trading Data**:
- Active Signals: Retain until expiry + 30 days
- Historical Signals: Retain for 2 years for analysis
- Trade Records: Permanent retention for regulatory compliance
- Performance Data: Permanent retention for strategy development

**System Data**:
- Application Logs: 90-day retention with archival to cold storage
- Error Logs: 1-year retention for troubleshooting
- Performance Metrics: 6-month detailed retention, 2-year summarized
- Configuration History: Permanent retention for audit trails

### §8.2.2 Backup & Recovery
**Backup Strategy**:
- Real-time Backup: Continuous replication to secondary database
- Daily Backup: Full database backup with verification
- Weekly Backup: Compressed backup to remote storage
- Monthly Backup: Long-term archival to cold storage

**Recovery Procedures**:
- Point-in-Time Recovery: Restore to any point within 30 days
- Partial Recovery: Individual table or record recovery
- Disaster Recovery: Full system recovery from remote backup
- Recovery Testing: Monthly recovery procedure validation

### §8.2.3 Data Migration & Versioning
**Schema Evolution**:
- Version-Controlled Schema: Database schema version management
- Migration Scripts: Automated migration between schema versions
- Backward Compatibility: Support for previous schema versions during transition
- Rollback Procedures: Safe rollback to previous schema versions

**Data Format Evolution**:
- Format Versioning: Data format version tracking in metadata
- Legacy Support: Continued support for legacy data formats
- Conversion Utilities: Automated conversion between data formats
- Validation: Data integrity validation after format conversions

## §8.3 Performance Optimization

### §8.3.1 Query Optimization
**Query Performance**:
- Execution Plan Analysis: Regular analysis of query execution plans
- Index Optimization: Automated index recommendation and creation
- Query Caching: Intelligent caching of frequently executed queries
- Connection Pooling: Optimized database connection management

**Data Access Patterns**:
- Read Optimization: Optimized queries for common read patterns
- Write Optimization: Batch processing for bulk data operations
- Real-time Access: Optimized queries for real-time data requirements
- Analytical Queries: Specialized indexes and views for analytics

### §8.3.2 Storage Optimization
**Data Compression**:
- Table Compression: Automated compression for historical data
- Index Compression: Compressed indexes for large tables
- Archive Compression: High-compression for archived data
- Selective Compression: Compression based on data age and access patterns

**Partitioning Strategy**:
- Date-Based Partitioning: Partition by date for time-series data
- Symbol-Based Partitioning: Partition by trading symbol for parallel processing
- Hybrid Partitioning: Combined date and symbol partitioning for optimal performance
- Automated Maintenance: Automatic partition creation and cleanup

---

# §9. Risk & Portfolio Controls

## §9.1 Risk Management Framework

### §9.1.1 Risk Limit Types
**Position-Level Limits**:
- Maximum Position Size: Individual position size limits per symbol
- Leverage Limits: Maximum leverage allowed per position and overall
- Concentration Limits: Maximum exposure to single currency or sector
- Correlation Limits: Maximum exposure to highly correlated positions

**Portfolio-Level Limits**:
- Total Exposure: Maximum total portfolio exposure across all positions
- Daily Loss Limits: Maximum acceptable loss per trading day
- Drawdown Limits: Maximum portfolio drawdown from peak
- Margin Utilization: Maximum percentage of available margin usage

**Time-Based Limits**:
- Trading Hours: Restricted trading during specific time periods
- Event Restrictions: Limited trading around major economic events
- Overnight Positions: Rules for carrying positions overnight
- Weekend Exposure: Limits on positions held over weekends

### §9.1.2 Risk Calculation Engine
**Real-Time Risk Metrics**:
- Value at Risk (VaR): Statistical risk measurement using historical data
- Expected Shortfall: Expected loss beyond VaR threshold
- Position Greeks: Delta, gamma, theta calculations for option positions
- Correlation-Adjusted Risk: Risk calculations considering position correlations

**Risk Attribution**:
- Currency Risk: Risk breakdown by base currency exposure
- Strategy Risk: Risk attribution by trading strategy
- Time Risk: Risk analysis by position holding periods
- Sector Risk: Risk analysis by economic sector exposure

### §9.1.3 Dynamic Risk Adjustment
**Market Condition Adjustments**:
- Volatility Regime: Risk limit adjustments based on market volatility
- Liquidity Conditions: Position size adjustments for illiquid markets
- Event-Driven Adjustments: Temporary risk reductions around major events
- Correlation Regime: Risk adjustments based on correlation breakdowns

**Performance-Based Adjustments**:
- Winning Streaks: Gradual risk increases during profitable periods
- Losing Streaks: Progressive risk reductions during loss periods
- Drawdown Response: Automatic risk reduction during drawdown periods
- Recovery Protocols: Risk restoration procedures after drawdown recovery

## §9.2 Portfolio Controls

### §9.2.1 Exposure Management
**Currency Exposure**:
- Net Currency Exposure: Real-time monitoring of net currency positions
- Gross Currency Exposure: Total long and short exposure by currency
- Cross-Currency Correlation: Correlation-adjusted exposure calculations
- Currency Hedging: Automatic hedging for excessive currency exposure

**Sector Exposure**:
- Economic Sector: Exposure monitoring by economic sectors
- Geographic Exposure: Risk monitoring by geographic regions
- Asset Class Exposure: Diversification across different asset classes
- Strategy Exposure: Exposure limits by trading strategy type

### §9.2.2 Position Sizing
**Kelly Criterion Implementation**:
- Optimal Position Sizing: Kelly criterion-based position size calculation
- Risk-Adjusted Kelly: Modified Kelly criterion with risk adjustments
- Fractional Kelly: Conservative position sizing using fractional Kelly
- Dynamic Adjustment: Real-time position size adjustment based on performance

**Risk Parity Approaches**:
- Equal Risk Contribution: Position sizing for equal risk contribution
- Volatility-Adjusted Sizing: Position sizing inversely proportional to volatility
- Correlation-Adjusted Sizing: Position sizing considering correlation effects
- Risk Budget Allocation: Position sizing within predefined risk budgets

### §9.2.3 Portfolio Optimization
**Mean Reversion Strategies**:
- Portfolio Rebalancing: Systematic rebalancing to target allocations
- Risk Target Maintenance: Maintaining constant portfolio risk levels
- Correlation Monitoring: Dynamic adjustment for changing correlations
- Performance Attribution: Analysis of portfolio performance sources

**Momentum Strategies**:
- Trend Following: Portfolio adjustments based on trend identification
- Momentum Scoring: Portfolio weighting based on momentum indicators
- Regime Detection: Portfolio adjustment for different market regimes
- Breakout Strategies: Position adjustments for breakout confirmations

## §9.3 Circuit Breakers & Emergency Controls

### §9.3.1 Automated Circuit Breakers
**Loss-Based Triggers**:
- Daily Loss Limits: Automatic trading halt after daily loss threshold
- Portfolio Drawdown: Trading suspension during excessive drawdown
- Position Loss Limits: Automatic position closure for large individual losses
- Consecutive Loss Limits: Trading pause after consecutive losing trades

**Risk-Based Triggers**:
- Margin Call Prevention: Preemptive position reduction before margin calls
- Volatility Spikes: Trading suspension during extreme volatility
- Liquidity Crises: Position reduction during liquidity shortages
- System Error Protection: Trading halt during system malfunction detection

### §9.3.2 Manual Override Controls
**Emergency Stop Functions**:
- Immediate Stop: Instant cessation of all trading activity
- Position Closure: Immediate closure of all open positions
- Partial Stop: Selective stopping of specific strategies or symbols
- Override Codes: Secure access codes for emergency interventions

**Recovery Procedures**:
- System Reset: Controlled restart of trading systems
- Position Reconciliation: Verification of position accuracy after interruption
- Risk Assessment: Comprehensive risk evaluation before trading resumption
- Approval Process: Multi-level approval for trading resumption

### §9.3.3 Regulatory Compliance
**Reporting Requirements**:
- Position Reporting: Automated regulatory position reporting
- Large Trader Reporting: Compliance with large trader identification rules
- Risk Reporting: Regular risk assessment reporting to regulators
- Audit Trail Maintenance: Complete audit trail preservation

**Compliance Monitoring**:
- Rule Validation: Real-time validation of regulatory compliance
- Limit Monitoring: Continuous monitoring of regulatory limits
- Violation Alerts: Immediate alerts for regulatory violations
- Corrective Actions: Automated corrective actions for violations

---

# §10. Integration & Communication

## §10.1 MT4 Integration Layer

### §10.1.1 MQL4 Communication Bridge
**Communication Protocols**:
- Socket Communication: Primary communication via TCP sockets
- File-Based Communication: Fallback communication using CSV files
- Named Pipes: High-speed local communication for same-machine deployment
- HTTP API: RESTful API interface for web-based integration

**Data Exchange Formats**:
- Signal Transmission: Standardized signal format for MT4 consumption
- Position Updates: Real-time position status updates from MT4
- Market Data: Bid/ask price and volume data transmission
- Error Reporting: Comprehensive error reporting and status updates

**Connection Management**:
- Connection Pooling: Efficient management of multiple MT4 connections
- Heartbeat Monitoring: Regular connectivity checks and status updates
- Automatic Reconnection: Intelligent reconnection logic with exponential backoff
- Failover Mechanisms: Automatic failover to backup communication methods

### §10.1.2 Trade Execution Interface
**Order Management**:
- Order Placement: Direct order placement through MT4 platform
- Order Modification: Real-time order parameter modification
- Order Cancellation: Immediate order cancellation capabilities
- Order Status Tracking: Real-time order status monitoring and reporting

**Position Management**:
- Position Opening: New position creation with specified parameters
- Position Modification: Stop-loss and take-profit level adjustments
- Position Closing: Partial and complete position closure options
- Position Monitoring: Real-time position tracking and P&L calculation

**Risk Integration**:
- Pre-Trade Risk Checks: Risk validation before order submission
- Position Size Validation: Automatic position size validation and adjustment
- Margin Calculation: Real-time margin requirement calculation
- Risk Override: Manual risk override for exceptional circumstances

### §10.1.3 Error Handling & Recovery
**Error Classification**:
- Connection Errors: Network and connectivity issue handling
- Execution Errors: Trade execution failure handling
- Data Errors: Market data and pricing error management
- System Errors: Platform and system-level error handling

**Recovery Procedures**:
- Automatic Retry: Intelligent retry logic with configurable parameters
- Manual Intervention: Procedures for manual error resolution
- Error Escalation: Escalation procedures for unresolved errors
- Audit Logging: Comprehensive logging of all errors and recovery actions

## §10.2 External Data Interfaces

### §10.2.1 Economic Calendar Integration
**Data Source APIs**:
- Multiple Providers: Integration with multiple calendar data providers
- Real-Time Updates: Live updates for event changes and new releases
- Historical Data: Access to historical economic event data
- Data Validation: Cross-validation between multiple data sources

**Event Processing**:
- Event Normalization: Standardization of event data across providers
- Impact Assessment: Automated event impact level classification
- Schedule Management: Event schedule processing and notification
- Revision Tracking: Handling of event forecast and actual value revisions

### §10.2.2 Market Data Integration
**Price Feed Management**:
- Multiple Feed Sources: Integration with multiple price data providers
- Feed Failover: Automatic switching between data sources
- Data Quality Monitoring: Real-time data quality assessment and alerting
- Latency Optimization: Optimization for minimal data transmission delays

**Data Normalization**:
- Format Standardization: Consistent data format across all sources
- Time Synchronization: UTC timestamp normalization and synchronization
- Data Validation: Real-time validation of price data integrity
- Gap Detection: Detection and handling of data gaps and interruptions

### §10.2.3 Third-Party Service Integration
**API Management**:
- Rate Limiting: Intelligent rate limiting and request throttling
- Authentication Management: Secure API key and authentication handling
- Response Caching: Intelligent caching of API responses for performance
- Error Handling: Comprehensive API error handling and retry logic

**Service Monitoring**:
- Availability Monitoring: Continuous monitoring of service availability
- Performance Monitoring: Tracking of API response times and reliability
- Usage Tracking: Monitoring of API usage against service limits
- Cost Management: Tracking and optimization of API usage costs

## §10.3 Internal Communication Architecture

### §10.3.1 Event-Driven Architecture
**Message Bus Implementation**:
- Topic-Based Routing: Message routing based on topic subscriptions
- Message Persistence: Persistent message storage for reliable delivery
- Message Ordering: Guaranteed message ordering for critical sequences
- Dead Letter Handling: Management of undeliverable messages

**Event Types**:
- Trading Events: Signal generation, execution, and position updates
- Risk Events: Risk limit breaches and portfolio status changes
- System Events: System health, connectivity, and operational status
- User Events: User actions, configuration changes, and manual interventions

### §10.3.2 Service Communication
**Inter-Service Communication**:
- Synchronous Communication: Direct API calls for immediate responses
- Asynchronous Communication: Message-based communication for batch processing
- Service Discovery: Automatic service registration and discovery
- Load Balancing: Intelligent request routing and load distribution

**Data Consistency**:
- Transaction Management: Distributed transaction coordination
- Event Sourcing: Event-based state reconstruction and consistency
- Conflict Resolution: Automated conflict detection and resolution
- Data Synchronization: Multi-service data synchronization and consistency

### §10.3.3 Security & Authentication
**Security Framework**:
- Authentication: Multi-factor authentication and session management
- Authorization: Role-based access control and permission management
- Encryption: End-to-end encryption for sensitive data transmission
- Audit Logging: Comprehensive security event logging and monitoring

**API Security**:
- API Key Management: Secure API key generation and rotation
- Rate Limiting: Protection against API abuse and DoS attacks
- Input Validation: Comprehensive input validation and sanitization
- Security Monitoring: Real-time security threat detection and response

---

# §11. Monitoring & Testing

## §11.1 System Monitoring

### §11.1.1 Performance Monitoring
**Real-Time Metrics**:
- System Latency: End-to-end latency measurement for critical operations
- Throughput Monitoring: Transaction and message processing rates
- Resource Utilization: CPU, memory, and disk usage monitoring
- Network Performance: Network latency and bandwidth utilization

**Performance Baselines**:
- Baseline Establishment: Historical performance baseline creation
- Trend Analysis: Long-term performance trend identification
- Anomaly Detection: Automated detection of performance anomalies
- Capacity Planning: Predictive analysis for capacity requirements

**Alert Thresholds**:
- Performance Alerts: Configurable thresholds for performance metrics
- Escalation Procedures: Tiered alert escalation based on severity
- Alert Correlation: Intelligent correlation of related alerts
- False Positive Reduction: Machine learning-based alert optimization

### §11.1.2 Business Logic Monitoring
**Trading Performance**:
- Strategy Performance: Real-time strategy performance monitoring
- Signal Quality: Signal accuracy and effectiveness tracking
- Execution Quality: Trade execution performance and slippage analysis
- Risk Compliance: Continuous monitoring of risk limit adherence

**Market Data Monitoring**:
- Data Quality: Real-time assessment of market data quality
- Data Completeness: Monitoring of data gaps and missing information
- Data Latency: Measurement of data delivery timeliness
- Source Reliability: Monitoring of data source availability and accuracy

### §11.1.3 Health Monitoring Dashboard
**System Health Indicators**:
- Service Status: Real-time status of all system components
- Connectivity Status: Status of external connections and integrations
- Data Flow Status: Monitoring of data pipeline health and throughput
- Error Rate Monitoring: Tracking of error rates and types across services

**Operational Dashboards**:
- Executive Dashboard: High-level system and business metrics
- Operations Dashboard: Detailed operational metrics and controls
- Technical Dashboard: System performance and technical metrics
- Risk Dashboard: Real-time risk metrics and compliance status

## §11.2 Testing Framework

### §11.2.1 Automated Testing Suite
**Unit Testing**:
- Component Testing: Individual component functionality testing
- Mock Integration: Testing with mocked external dependencies
- Data Validation: Comprehensive data validation and integrity testing
- Edge Case Testing: Testing of boundary conditions and error scenarios

**Integration Testing**:
- Service Integration: Testing of inter-service communication
- Database Integration: Database interaction and data integrity testing
- External API Integration: Testing of third-party service integrations
- End-to-End Testing: Complete workflow testing from start to finish

**Performance Testing**:
- Load Testing: System performance under normal load conditions
- Stress Testing: System behavior under extreme load conditions
- Volume Testing: Testing with large volumes of data and transactions
- Scalability Testing: Testing of system scaling capabilities

### §11.2.2 Trading Strategy Testing
**Backtesting Framework**:
- Historical Data Testing: Strategy testing with historical market data
- Multiple Timeframes: Testing across different timeframes and periods
- Market Condition Testing: Strategy performance in different market conditions
- Statistical Analysis: Comprehensive statistical analysis of backtest results

**Forward Testing**:
- Paper Trading: Risk-free testing with live market data
- Limited Live Testing: Small-scale live testing with real money
- A/B Testing: Comparative testing of strategy variations
- Performance Validation: Validation of backtesting results in live conditions

**Risk Testing**:
- Scenario Testing: Testing under various market scenarios
- Stress Testing: Strategy behavior during market stress periods
- Drawdown Testing: Maximum drawdown analysis and recovery testing
- Risk Model Validation: Validation of risk calculation accuracy

### §11.2.3 Regression Testing
**Automated Regression Suite**:
- Code Change Testing: Automated testing of code modifications
- Configuration Testing: Testing of configuration changes and updates
- Data Migration Testing: Testing of database schema and data migrations
- API Compatibility Testing: Testing of API backward compatibility

**Continuous Integration**:
- Build Automation: Automated build and deployment processes
- Test Automation: Automated execution of test suites
- Quality Gates: Quality threshold enforcement before deployment
- Deployment Validation: Automated validation of successful deployments

## §11.3 Quality Assurance

### §11.3.1 Code Quality Management
**Code Review Process**:
- Peer Review: Mandatory peer review for all code changes
- Automated Analysis: Static code analysis and quality metrics
- Security Review: Security-focused code review and vulnerability scanning
- Documentation Review: Documentation completeness and accuracy validation

**Quality Metrics**:
- Code Coverage: Test coverage measurement and reporting
- Complexity Metrics: Code complexity analysis and optimization recommendations
- Technical Debt: Technical debt identification and management
- Performance Metrics: Code performance analysis and optimization

### §11.3.2 Data Quality Assurance
**Data Validation**:
- Schema Validation: Automated validation of data schema compliance
- Business Rule Validation: Validation of business logic and constraints
- Data Completeness: Monitoring and validation of data completeness
- Data Accuracy: Cross-validation of data accuracy across sources

**Data Lineage**:
- Data Tracking: Complete tracking of data flow and transformations
- Change Tracking: Monitoring of data changes and modifications
- Audit Trails: Comprehensive audit trails for all data operations
- Impact Analysis: Analysis of data change impacts on downstream processes

### §11.3.3 Operational Quality
**Deployment Quality**:
- Deployment Validation: Comprehensive validation of deployment success
- Configuration Management: Validation of configuration accuracy and completeness
- Environment Consistency: Ensuring consistency across different environments
- Rollback Testing: Testing of rollback procedures and capabilities

**Operational Procedures**:
- Process Documentation: Comprehensive documentation of operational procedures
- Training Programs: Staff training on system operations and procedures
- Emergency Procedures: Well-defined emergency response procedures
- Regular Reviews: Periodic review and update of operational procedures

---

# §12. Deployment & Operations

## §12.1 Deployment Architecture

### §12.1.1 Environment Management
**Environment Types**:
- Development Environment: Individual developer workspaces with full system access
- Testing Environment: Integrated testing environment with realistic data volumes
- Staging Environment: Production-like environment for final validation
- Production Environment: Live trading environment with full monitoring and backup

**Environment Configuration**:
- Infrastructure as Code: Automated environment provisioning and configuration
- Configuration Management: Centralized configuration management across environments
- Secret Management: Secure management of sensitive configuration data
- Environment Promotion: Automated promotion of configurations between environments

**Environment Isolation**:
- Network Segmentation: Network-level isolation between environments
- Data Isolation: Separate data stores for each environment
- Service Isolation: Isolated service instances for each environment
- Access Controls: Environment-specific access controls and permissions

### §12.1.2 Deployment Pipeline
**Continuous Integration**:
- Source Control Integration: Automated builds triggered by code commits
- Automated Testing: Comprehensive test suite execution for all changes
- Quality Gates: Quality threshold enforcement before deployment advancement
- Artifact Management: Secure management and versioning of deployment artifacts

**Continuous Deployment**:
- Automated Deployment: Push-button deployment to any environment
- Blue-Green Deployment: Zero-downtime deployment using parallel environments
- Canary Deployment: Gradual rollout with automated monitoring and rollback
- Feature Flags: Runtime feature toggling for controlled feature releases

**Deployment Validation**:
- Health Checks: Automated validation of deployment success
- Integration Testing: Post-deployment integration testing
- Performance Validation: Performance regression testing after deployment
- Business Validation: Automated validation of critical business functions

### §12.1.3 Rollback Procedures
**Automated Rollback**:
- Health-Based Rollback: Automatic rollback on health check failures
- Performance-Based Rollback: Automatic rollback on performance degradation
- Error-Based Rollback: Automatic rollback on error rate increases
- User-Initiated Rollback: Manual rollback triggers for operational teams

**Rollback Validation**:
- Rollback Testing: Regular testing of rollback procedures
- Data Consistency: Ensuring data consistency during rollback operations
- Service Recovery: Validation of service recovery after rollback
- Communication: Automated notification of rollback events

## §12.2 Operations Management

### §12.2.1 System Administration
**Infrastructure Management**:
- Server Monitoring: Comprehensive monitoring of server health and performance
- Capacity Management: Proactive capacity planning and resource allocation
- Security Management: Continuous security monitoring and threat detection
- Backup Management: Automated backup procedures and recovery testing

**Service Management**:
- Service Monitoring: Real-time monitoring of service health and availability
- Performance Tuning: Continuous optimization of service performance
- Log Management: Centralized log collection, analysis, and retention
- Configuration Management: Centralized management of service configurations

### §12.2.2 Incident Management
**Incident Response**:
- Incident Detection: Automated detection of system incidents and anomalies
- Alert Management: Intelligent alerting with proper escalation procedures
- Response Procedures: Well-defined incident response and resolution procedures
- Communication: Clear communication channels and stakeholder notification

**Incident Resolution**:
- Root Cause Analysis: Comprehensive analysis of incident causes
- Resolution Tracking: Tracking of resolution progress and effectiveness
- Post-Incident Review: Detailed review and lessons learned documentation
- Process Improvement: Continuous improvement of incident response procedures

### §12.2.3 Change Management
**Change Control Process**:
- Change Request: Standardized change request and approval process
- Impact Assessment: Comprehensive assessment of change impacts
- Risk Assessment: Risk analysis and mitigation planning for changes
- Approval Workflow: Multi-level approval workflow for different change types

**Change Implementation**:
- Implementation Planning: Detailed implementation planning and scheduling
- Rollback Planning: Comprehensive rollback planning for all changes
- Communication: Clear communication of change schedules and impacts
- Validation: Post-implementation validation and sign-off procedures

## §12.3 Business Continuity

### §12.3.1 Disaster Recovery
**Recovery Planning**:
- Business Impact Analysis: Analysis of system outage impacts on business operations
- Recovery Time Objectives: Definition of acceptable recovery timeframes
- Recovery Point Objectives: Definition of acceptable data loss limits
- Recovery Procedures: Detailed procedures for system recovery

**Backup Strategy**:
- Data Backup: Comprehensive backup of all critical system data
- Configuration Backup: Backup of system configurations and settings
- Application Backup: Backup of application code and dependencies
- Offsite Storage: Secure offsite storage of all backup data

**Recovery Testing**:
- Regular Testing: Regular testing of recovery procedures and capabilities
- Scenario Testing: Testing of different disaster scenarios
- Performance Validation: Validation of recovery performance objectives
- Process Refinement: Continuous refinement of recovery procedures

### §12.3.2 High Availability
**Redundancy Design**:
- Component Redundancy: Redundant instances of all critical components
- Geographic Redundancy: Geographically distributed system components
- Data Redundancy: Real-time data replication and synchronization
- Network Redundancy: Multiple network paths and failover capabilities

**Failover Procedures**:
- Automated Failover: Automatic failover for detected component failures
- Manual Failover: Procedures for manual failover initiation
- Failover Testing: Regular testing of failover procedures and capabilities
- Recovery Procedures: Procedures for recovering from failover events

### §12.3.3 Risk Management
**Operational Risk Assessment**:
- Risk Identification: Systematic identification of operational risks
- Risk Analysis: Quantitative and qualitative analysis of identified risks
- Risk Mitigation: Implementation of risk mitigation strategies and controls
- Risk Monitoring: Continuous monitoring of operational risk levels

**Compliance Management**:
- Regulatory Compliance: Ensuring compliance with all applicable regulations
- Audit Preparation: Maintaining audit-ready documentation and evidence
- Compliance Monitoring: Continuous monitoring of compliance status
- Violation Response: Procedures for responding to compliance violations

---

# Appendices

## Appendix A: Data Schemas

### A.1 Signal Schema Definition
```json
{
  "signal_schema": {
    "version": "1.0",
    "required_fields": {
      "id": {"type": "string", "max_length": 64},
      "timestamp": {"type": "datetime", "format": "ISO8601_UTC"},
      "source": {"type": "string", "max_length": 50},
      "symbol": {"type": "string", "pattern": "[A-Z]{6}"},
      "kind": {"type": "enum", "values": ["ENTRY", "EXIT", "MODIFY"]},
      "direction": {"type": "enum", "values": ["LONG", "SHORT", "NEUTRAL"]},
      "strength": {"type": "decimal", "min": 0.0, "max": 1.0},
      "confidence": {"type": "decimal", "min": 0.0, "max": 1.0}
    },
    "optional_fields": {
      "entry_price": {"type": "decimal", "min": 0.0},
      "stop_loss": {"type": "decimal", "min": 0.0},
      "take_profit": {"type": "decimal", "min": 0.0},
      "expiry_time": {"type": "datetime", "format": "ISO8601_UTC"},
      "success_probability": {"type": "decimal", "min": 0.0, "max": 1.0},
      "risk_reward_ratio": {"type": "decimal", "min": 0.0}
    }
  }
}
```

### A.2 CAL8 Identifier Schema
```json
{
  "cal8_schema": {
    "format": "^[A-Z]{3}H[A-Z]{2}[0-9]{2}$",
    "description": "8-character economic calendar identifier",
    "components": {
      "currency_code": {"position": "1-3", "format": "[A-Z]{3}"},
      "impact_level": {"position": "4", "value": "H"},
      "event_type": {"position": "5-6", "format": "[A-Z]{2}"},
      "revision_version": {"position": "7-8", "format": "[0-9]{2}"}
    },
    "examples": ["AUSHNF10", "USDCPI01", "EURNFP20"]
  }
}
```

### A.3 Hybrid ID Schema
```json
{
  "hybrid_id_schema": {
    "format": "{CAL8}#{MATRIX_CONTEXT}#{TIMESTAMP}",
    "max_length": 128,
    "components": {
      "cal8_id": {"type": "string", "length": 8},
      "matrix_context": {"type": "string", "max_length": 50},
      "timestamp": {"type": "string", "format": "yyyyMMddTHHmmssZ"}
    },
    "example": "AUSHNF10#LONG_EUR_15MIN#20250306T143000Z"
  }
}
```

## Appendix B: API Specifications

### B.1 Signal API Endpoints
```yaml
signal_api:
  base_url: "/api/v1/signals"
  endpoints:
    get_signals:
      method: GET
      path: "/signals"
      parameters:
        - symbol: optional string
        - start_time: optional datetime
        - end_time: optional datetime
        - limit: optional integer (default: 100)
      response: array of signal objects
    
    create_signal:
      method: POST
      path: "/signals"
      body: signal object
      response: created signal with ID
    
    get_signal:
      method: GET
      path: "/signals/{signal_id}"
      response: signal object
    
    update_signal:
      method: PUT
      path: "/signals/{signal_id}"
      body: updated signal fields
      response: updated signal object
    
    delete_signal:
      method: DELETE
      path: "/signals/{signal_id}"
      response: success confirmation
```

### B.2 Trading API Endpoints
```yaml
trading_api:
  base_url: "/api/v1/trading"
  endpoints:
    get_positions:
      method: GET
      path: "/positions"
      response: array of position objects
    
    execute_trade:
      method: POST
      path: "/execute"
      body:
        signal_id: string
        position_size: decimal
        override_params: optional object
      response: execution result
    
    close_position:
      method: POST
      path: "/positions/{position_id}/close"
      body:
        close_type: enum [FULL, PARTIAL]
        quantity: optional decimal
      response: closure result
    
    get_trade_history:
      method: GET
      path: "/trades"
      parameters:
        - symbol: optional string
        - start_date: optional date
        - end_date: optional date
      response: array of trade objects
```

## Appendix C: Configuration Templates

### C.1 Risk Management Configuration
```yaml
risk_management:
  global_limits:
    max_portfolio_exposure: 15.0  # percentage
    max_daily_loss: 2.0           # percentage
    max_drawdown: 10.0            # percentage
    margin_utilization_limit: 80.0 # percentage
  
  position_limits:
    max_position_size: 5.0        # percentage of portfolio
    max_positions_per_symbol: 3
    max_correlated_exposure: 8.0  # percentage
  
  risk_adjustments:
    volatility_multiplier: 1.5
    correlation_adjustment: true
    event_risk_reduction: 0.5     # reduction factor during events
  
  circuit_breakers:
    daily_loss_halt: 3.0          # percentage
    consecutive_loss_limit: 5
    volatility_spike_threshold: 3.0 # standard deviations
```

### C.2 Signal Generation Configuration
```yaml
signal_generation:
  technical_analysis:
    indicators:
      - name: "moving_average"
        periods: [20, 50, 200]
        weight: 0.3
      - name: "rsi"
        period: 14
        overbought: 70
        oversold: 30
        weight: 0.2
      - name: "macd"
        fast: 12
        slow: 26
        signal: 9
        weight: 0.25
  
  calendar_integration:
    high_impact_multiplier: 1.5
    medium_impact_multiplier: 1.2
    event_proximity_hours: 2
    post_event_cooldown: 1        # hours
  
  signal_filtering:
    min_confidence: 0.6
    min_strength: 0.4
    max_signals_per_hour: 10
    duplicate_suppression: true
```

## Appendix D: Testing Specifications

### D.1 Performance Benchmarks
```yaml
performance_benchmarks:
  signal_generation:
    max_latency: 1000            # milliseconds
    throughput: 1000             # signals per minute
    availability: 99.9           # percentage
  
  trade_execution:
    max_latency: 2000            # milliseconds
    success_rate: 99.5           # percentage
    slippage_tolerance: 1.0      # pips
  
  data_processing:
    calendar_ingestion: 5000     # events per minute
    price_data_latency: 100      # milliseconds
    database_query_time: 50      # milliseconds
  
  user_interface:
    page_load_time: 2000         # milliseconds
    real_time_updates: 500       # milliseconds
    user_interaction_response: 200 # milliseconds
```

### D.2 Test Scenarios
```yaml
test_scenarios:
  normal_operations:
    - name: "Standard Trading Day"
      description: "Normal market conditions with regular signal generation"
      duration: "8 hours"
      expected_signals: 50
      expected_trades: 10
  
  stress_conditions:
    - name: "High Volatility Event"
      description: "Major economic event causing high volatility"
      market_condition: "high_volatility"
      risk_adjustment: true
      expected_behavior: "reduced position sizing"
  
  failure_scenarios:
    - name: "MT4 Connection Loss"
      description: "Loss of connection to MT4 platform"
      expected_behavior: "switch to backup communication"
      recovery_time: "< 30 seconds"
  
  edge_cases:
    - name: "Simultaneous Major Events"
      description: "Multiple high-impact events occurring simultaneously"
      expected_behavior: "enhanced risk controls"
      signal_filtering: "increased thresholds"
```

---

**Document Version:** 3.0  
**Last Updated:** 2025-09-06  
**Review Schedule:** Quarterly  
**Approval Status:** Draft for Review

*This document represents the complete unified specification for the HUEY_P Trading System, combining all frontend GUI and backend processing requirements into a single comprehensive reference.*
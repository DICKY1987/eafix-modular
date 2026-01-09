---
doc_id: DOC-CONFIG-0077
---

# EAFIX Trading Desktop Application
## Product Design Requirements (PDR)

**Document Status:** Production Specification v1.0  
**Classification:** Enterprise-Grade Financial Application  
**Target Release:** Q2 2025  
**Last Updated:** 2025-11-25  
**Document Owner:** EAFIX Development Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Strategy](#2-product-vision--strategy)
3. [Target Users & Personas](#3-target-users--personas)
4. [Functional Requirements](#4-functional-requirements)
5. [Desktop Application Architecture](#5-desktop-application-architecture)
6. [User Interface Specifications](#6-user-interface-specifications)
7. [Security & Compliance](#7-security--compliance)
8. [Performance Requirements](#8-performance-requirements)
9. [Integration Requirements](#9-integration-requirements)
10. [Quality Assurance](#10-quality-assurance)
11. [Deployment & Distribution](#11-deployment--distribution)
12. [Risk Assessment](#12-risk-assessment)
13. [Success Metrics](#13-success-metrics)
14. [Release Timeline](#14-release-timeline)

---

## 1. Executive Summary

### 1.1 Purpose

This Product Design Requirements document defines the specifications for the EAFIX Trading Desktop Application—a complete, user-ready desktop trading platform built on enterprise-grade microservices architecture. The application provides professional forex traders with comprehensive tools for economic calendar-driven trading, matrix-based re-entry strategies, and real-time risk management.

### 1.2 Product Overview

**EAFIX Desktop** is a cross-platform desktop application that delivers:
- Real-time trading signal monitoring and execution
- Advanced economic calendar integration with anticipation windows
- Multi-dimensional re-entry matrix decision support
- Professional-grade risk management controls
- Seamless MetaTrader 4 (MT4) integration via CSV/Socket bridge
- Enterprise-class monitoring, logging, and observability

### 1.3 Business Objectives

| Objective | Target | Measurement |
|-----------|--------|-------------|
| Trading Efficiency | 40% reduction in signal-to-execution time | Time-to-trade metrics |
| Risk Management | Zero unintended position exposure | Audit trail verification |
| User Adoption | 90% feature utilization within 30 days | Analytics dashboard |
| System Reliability | 99.9% uptime during trading hours | Monitoring metrics |
| Regulatory Compliance | Full audit trail for all decisions | Compliance reports |

### 1.4 Key Differentiators

1. **Matrix-Based Decision Support**: Unique multi-dimensional re-entry system with outcome/duration/proximity context
2. **Economic Calendar Fusion**: Integrated anticipation and post-event analysis
3. **Enterprise Security**: Financial-grade security with complete audit trails
4. **Professional UI/UX**: Designed for high-frequency decision making
5. **Extensible Architecture**: Plugin-ready for custom indicators and strategies

---

## 2. Product Vision & Strategy

### 2.1 Vision Statement

> "To provide professional forex traders with an intelligent, reliable, and comprehensive desktop trading platform that seamlessly integrates economic calendar awareness with sophisticated re-entry strategies, enabling consistent execution while maintaining rigorous risk controls."

### 2.2 Strategic Goals

#### 2.2.1 Phase 1: Foundation (Q1 2025)
- Core desktop application framework
- Essential trading functionality (Live, Signals, Config tabs)
- MT4 bridge integration
- Basic monitoring and health checks

#### 2.2.2 Phase 2: Intelligence (Q2 2025)
- Economic Calendar integration
- Re-Entry Matrix system
- Advanced signal processing
- Probability-based decision support

#### 2.2.3 Phase 3: Enterprise (Q3 2025)
- Multi-account support
- Advanced analytics and reporting
- Plugin ecosystem
- Team collaboration features

### 2.3 Competitive Landscape

| Feature | EAFIX Desktop | Traditional MT4 | Competitor A |
|---------|--------------|-----------------|--------------|
| Economic Calendar Integration | Native | Manual | Limited |
| Matrix Re-Entry System | ✓ | ✗ | ✗ |
| Anticipation Windows | ✓ | ✗ | ✗ |
| Hybrid ID Traceability | ✓ | ✗ | Partial |
| Enterprise Monitoring | ✓ | ✗ | ✗ |
| Cross-Platform Desktop | ✓ | Windows Only | Web Only |

---

## 3. Target Users & Personas

### 3.1 Primary Persona: Professional Day Trader

**Name:** Marcus Chen  
**Role:** Independent Professional Forex Trader  
**Experience:** 5+ years forex trading

**Goals:**
- Execute high-probability trades around economic events
- Manage risk across multiple currency pairs
- Track performance and optimize strategies
- Reduce emotional decision-making through systematic approach

**Pain Points:**
- Manual correlation between calendar events and trading decisions
- Difficulty tracking re-entry conditions across timeframes
- Lack of comprehensive audit trail for trade decisions
- Fragmented tools requiring multiple screens

**Technical Profile:**
- Comfortable with MT4/MT5 platforms
- Uses multiple monitors (2-4)
- Prefers keyboard shortcuts for speed
- Values customization and theming

### 3.2 Secondary Persona: Trading Desk Manager

**Name:** Sarah Williams  
**Role:** Prop Trading Desk Manager  
**Experience:** 10+ years in institutional trading

**Goals:**
- Monitor trader activity and risk exposure
- Ensure compliance with firm policies
- Generate reports for stakeholders
- Standardize trading procedures

**Pain Points:**
- Limited visibility into individual trader decisions
- Manual compliance checking
- Delayed risk alerts
- Inconsistent reporting across traders

### 3.3 Tertiary Persona: Algorithmic Strategy Developer

**Name:** Dr. James Liu  
**Role:** Quantitative Strategy Developer  
**Experience:** Ph.D. Mathematics, 7 years quant trading

**Goals:**
- Test and deploy custom indicators
- Backtest re-entry strategies
- Integrate statistical models
- Export data for analysis

**Pain Points:**
- Rigid platforms that don't allow customization
- Limited API access for custom integrations
- Poor data export capabilities
- Lack of scientific reproducibility

---

## 4. Functional Requirements

### 4.1 Core Trading Functions

#### 4.1.1 Signal Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-001 | Display real-time trading signals with direction, strength, and confidence | Must Have | Signals update ≤500ms from generation |
| FR-002 | Support signal filtering by symbol, timeframe, strength, source | Must Have | All filters combinable with AND logic |
| FR-003 | Enable signal acknowledgment and dismissal with audit trail | Must Have | All actions logged with timestamp and user |
| FR-004 | Pin critical signals for persistent visibility | Should Have | Pinned signals persist across sessions |
| FR-005 | Export signal history in CSV/JSON format | Should Have | Export includes all metadata fields |

#### 4.1.2 Economic Calendar Integration

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-010 | Display economic calendar with CAL8 identifiers | Must Have | All events show normalized CAL8 ID |
| FR-011 | Show anticipation windows (1HR, 8HR before events) | Must Have | Windows displayed with countdown timers |
| FR-012 | Filter events by currency, impact level, proximity | Must Have | Combined filtering supported |
| FR-013 | Emergency STOP/RESUME calendar imports | Must Have | STOP blocks all imports within 1 poll cycle |
| FR-014 | Display sequence gap and checksum failure counts | Should Have | Drill-down to specific errors available |

#### 4.1.3 Re-Entry Matrix System

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-020 | Display multi-dimensional re-entry matrix (S/T/O/C/Gen) | Must Have | All dimensions navigable |
| FR-021 | Edit matrix cells with validation and audit | Must Have | Changes logged with reason code |
| FR-022 | Support manual overrides with TTL and auto-revert | Must Have | Overrides tracked separately in P&L |
| FR-023 | Visualize matrix as heatmap | Should Have | Color gradient reflects performance |
| FR-024 | Compare matrix versions | Should Have | Side-by-side diff available |

#### 4.1.4 Risk Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-030 | Display real-time portfolio risk metrics | Must Have | Update within 1 second of position change |
| FR-031 | Enforce position size limits | Must Have | Orders blocked if exceeding limits |
| FR-032 | Implement circuit breakers (daily loss, consecutive losses) | Must Have | Circuit breakers trigger automatically |
| FR-033 | Support emergency position flatten | Must Have | All positions closed within 5 seconds |
| FR-034 | Display risk ribbon with color-coded status | Must Have | Green/Yellow/Red status visible at all times |

### 4.2 Configuration & Settings

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-040 | Auto-generate forms from parameter schemas | Must Have | All indicator params editable |
| FR-041 | Support configuration templates | Must Have | Templates versionable |
| FR-042 | Import/export settings as JSON | Must Have | Round-trip without data loss |
| FR-043 | Configure bridge communication (CSV/Socket modes) | Must Have | Mode switch without restart |
| FR-044 | Validate dependencies between settings | Must Have | Invalid combinations blocked |

### 4.3 Analytics & Reporting

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-050 | Display equity curve with drawdown overlay | Must Have | Interactive zoom and pan |
| FR-051 | Calculate key performance metrics (win rate, expectancy, Sharpe) | Must Have | Metrics match independent calculation |
| FR-052 | Generate performance reports (PDF/HTML) | Should Have | Reports include all required metrics |
| FR-053 | Export trade history with full traceability | Must Have | Hybrid IDs included in export |
| FR-054 | Support A/B strategy comparison | Nice to Have | Statistical significance indicated |

### 4.4 System Operations

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-060 | Display system health status | Must Have | All service statuses visible |
| FR-061 | Show broker clock skew with DEGRADED mode | Must Have | DEGRADED triggers on >120s skew |
| FR-062 | Provide operator kill-switches | Must Have | Admin-gated with confirmation |
| FR-063 | Display comprehensive logs | Must Have | Filterable by level and source |
| FR-064 | Support diagnostic data export | Should Have | Bundle includes logs and state |

---

## 5. Desktop Application Architecture

### 5.1 Technology Stack

#### 5.1.1 Desktop Framework Options

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **PyQt6** | Native performance, rich widgets, cross-platform | Larger bundle, licensing | **Primary Choice** |
| Electron | Web tech familiarity, ecosystem | Memory footprint, slower | Secondary |
| Tauri | Small bundle, Rust backend | Newer ecosystem | Future consideration |

**Selected Stack:**
- **Frontend:** PyQt6 with QML for complex visualizations
- **Local Backend:** FastAPI for local services
- **Database:** SQLite for local persistence, with Redis for caching
- **Charts:** PyQtGraph for real-time charting
- **Packaging:** PyInstaller with code signing

#### 5.1.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EAFIX Desktop Application                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   UI Layer  │  │   UI Layer  │  │   UI Layer  │              │
│  │   (PyQt6)   │  │   (Charts)  │  │   (Tables)  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│  ┌───────────────────────▼───────────────────────┐              │
│  │              Application Controller            │              │
│  │         (State Management, Event Bus)          │              │
│  └───────────────────────┬───────────────────────┘              │
│                          │                                       │
│  ┌──────────┬────────────┼────────────┬──────────┐              │
│  │          │            │            │          │              │
│  ▼          ▼            ▼            ▼          ▼              │
│ ┌────┐   ┌────┐      ┌────┐      ┌────┐     ┌────┐             │
│ │Sig-│   │Cal-│      │Mat-│      │Risk│     │Conf│             │
│ │nals│   │endar│     │rix │      │Mgr │     │ig  │             │
│ └──┬─┘   └──┬─┘      └──┬─┘      └──┬─┘     └──┬─┘             │
│    │        │           │           │          │                │
│    └────────┴───────────┼───────────┴──────────┘                │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────┐              │
│  │              Bridge Adapter Layer             │              │
│  │         (CSV Writer/Reader, Socket)           │              │
│  └───────────────────────┬───────────────────────┘              │
│                          │                                       │
└──────────────────────────│───────────────────────────────────────┘
                           │
                           ▼
             ┌─────────────────────────┐
             │    MT4 Expert Advisor   │
             │   (Common\Files\reentry)│
             └─────────────────────────┘
```

### 5.2 Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Data Flow Pipeline                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   [Economic Calendar]     [DDE Price Feeds]     [User Input]         │
│          │                       │                   │                │
│          ▼                       ▼                   ▼                │
│   ┌─────────────┐        ┌─────────────┐     ┌─────────────┐         │
│   │  Calendar   │        │    Data     │     │    GUI      │         │
│   │  Ingestor   │        │  Ingestor   │     │  Gateway    │         │
│   └──────┬──────┘        └──────┬──────┘     └──────┬──────┘         │
│          │                      │                   │                 │
│          ▼                      ▼                   │                 │
│   ┌─────────────────────────────────────────┐      │                 │
│   │              Event Bus (Redis)          │◄─────┘                 │
│   └─────────────┬───────────────────────────┘                        │
│                 │                                                     │
│       ┌─────────┼─────────┬─────────────────┐                        │
│       │         │         │                 │                        │
│       ▼         ▼         ▼                 ▼                        │
│  ┌─────────┐ ┌──────┐ ┌───────┐      ┌──────────┐                   │
│  │Indicator│ │Signal│ │Reentry│      │   Risk   │                   │
│  │ Engine  │ │ Gen  │ │Matrix │      │ Manager  │                   │
│  └────┬────┘ └──┬───┘ └───┬───┘      └────┬─────┘                   │
│       │         │         │               │                          │
│       └─────────┼─────────┼───────────────┘                          │
│                 │         │                                           │
│                 ▼         ▼                                           │
│          ┌─────────────────────┐                                     │
│          │   Decision Engine   │                                     │
│          │   (Trading Logic)   │                                     │
│          └──────────┬──────────┘                                     │
│                     │                                                 │
│                     ▼                                                 │
│          ┌─────────────────────┐                                     │
│          │   CSV Bridge Layer  │                                     │
│          │ (trading_signals.csv)│                                    │
│          └──────────┬──────────┘                                     │
│                     │                                                 │
└─────────────────────│─────────────────────────────────────────────────┘
                      │
                      ▼
             ┌─────────────────────┐
             │   MT4 EA Reader     │
             │  (Order Execution)  │
             └─────────────────────┘
```

### 5.3 State Management

#### 5.3.1 Application State Structure

```python
ApplicationState = {
    "session": {
        "user_id": str,
        "session_start": datetime,
        "active_account": str,
        "theme": str,
        "locale": str
    },
    "trading": {
        "signals": List[Signal],
        "positions": List[Position],
        "pending_orders": List[Order],
        "alerts": List[Alert]
    },
    "calendar": {
        "events": List[CalendarEvent],
        "anticipations": List[Anticipation],
        "import_status": str,  # RUNNING, STOPPED, DEGRADED
        "last_import": datetime
    },
    "matrix": {
        "current_version": str,
        "cells": Dict[HybridId, MatrixCell],
        "overrides": List[Override],
        "parameter_sets": Dict[str, ParameterSet]
    },
    "risk": {
        "portfolio_exposure": Decimal,
        "margin_usage": Decimal,
        "daily_pnl": Decimal,
        "drawdown": Decimal,
        "circuit_breaker_status": str
    },
    "system": {
        "services_health": Dict[str, HealthStatus],
        "bridge_status": str,
        "broker_clock_skew": int,
        "degraded_mode": bool
    }
}
```

#### 5.3.2 Event Types

| Event | Payload | Source | Subscribers |
|-------|---------|--------|-------------|
| `signal.new` | Signal object | Signal Generator | Live Tab, Alerts |
| `signal.ack` | signal_id, user_id | User Action | History, Audit |
| `position.open` | Position object | Execution Engine | Risk Manager, Live |
| `position.close` | Position + P/L | Execution Engine | Analytics, History |
| `calendar.event` | CalendarEvent | Calendar Ingestor | Signal Generator |
| `matrix.update` | Cell + version | Matrix Editor | Decision Engine |
| `risk.alert` | Alert details | Risk Manager | UI, Notifications |
| `system.health` | Service status | Health Monitor | System Status Tab |

### 5.4 Database Schema (Local SQLite)

```sql
-- User preferences and settings
CREATE TABLE user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Local signal cache
CREATE TABLE signal_cache (
    signal_id TEXT PRIMARY KEY,
    hybrid_id TEXT,
    cal8_id TEXT,
    timestamp_utc TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT CHECK (direction IN ('LONG', 'SHORT', 'NEUTRAL')),
    strength REAL CHECK (strength BETWEEN 0.0 AND 1.0),
    confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
    acknowledged BOOLEAN DEFAULT FALSE,
    ack_timestamp TIMESTAMP,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade history cache
CREATE TABLE trade_history (
    trade_id TEXT PRIMARY KEY,
    signal_id TEXT REFERENCES signal_cache(signal_id),
    hybrid_id TEXT,
    parameter_set_id TEXT,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    position_size REAL NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    pnl REAL,
    outcome TEXT CHECK (outcome IN ('WIN', 'LOSS', 'BREAKEVEN', 'OPEN')),
    duration_minutes INTEGER,
    metadata JSON,
    synced BOOLEAN DEFAULT FALSE
);

-- Matrix overrides
CREATE TABLE matrix_overrides (
    override_id TEXT PRIMARY KEY,
    cell_key TEXT NOT NULL,
    original_value JSON NOT NULL,
    override_value JSON NOT NULL,
    reason TEXT NOT NULL,
    ttl_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    reverted BOOLEAN DEFAULT FALSE,
    reverted_at TIMESTAMP
);

-- Audit log
CREATE TABLE audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_data JSON NOT NULL,
    user_id TEXT,
    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    correlation_id TEXT
);

-- Indexes
CREATE INDEX idx_signals_timestamp ON signal_cache(timestamp_utc);
CREATE INDEX idx_signals_symbol ON signal_cache(symbol);
CREATE INDEX idx_trades_entry_time ON trade_history(entry_time);
CREATE INDEX idx_trades_symbol ON trade_history(symbol);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp_utc);
CREATE INDEX idx_audit_type ON audit_log(event_type);
```

---

## 6. User Interface Specifications

### 6.1 Design Principles

1. **Information Density**: Maximize actionable information per screen area
2. **Progressive Disclosure**: Show essential info first, details on demand
3. **Consistent Patterns**: Unified interaction patterns across all views
4. **Accessibility**: WCAG 2.1 AA compliance minimum
5. **Performance**: Sub-100ms response for all user interactions

### 6.2 Color System

#### 6.2.1 Semantic Colors

| Token | Light Theme | Dark Theme | Usage |
|-------|-------------|------------|-------|
| `--color-long` | #22C55E | #4ADE80 | Buy/Long positions |
| `--color-short` | #EF4444 | #F87171 | Sell/Short positions |
| `--color-neutral` | #6B7280 | #9CA3AF | Neutral signals |
| `--color-warning` | #F59E0B | #FBBF24 | Warning states |
| `--color-danger` | #DC2626 | #EF4444 | Critical/Error states |
| `--color-success` | #16A34A | #22C55E | Success states |
| `--color-info` | #0EA5E9 | #38BDF8 | Informational |

#### 6.2.2 Status Indicators

| Status | Color | Icon | Animation |
|--------|-------|------|-----------|
| Connected | Green | ● | None |
| Connecting | Yellow | ◐ | Pulse |
| Disconnected | Red | ○ | None |
| Degraded | Orange | ◑ | Slow pulse |
| Error | Red | ✖ | Flash |

### 6.3 Tab Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ EAFIX Desktop                                    [_][□][×] │
├─────────────────────────────────────────────────────────────────────┤
│ ┌──────┬─────────┬─────────┬──────────┬────────┬──────────┬───────┐ │
│ │ Live │ Signals │ Config  │ Calendar │ Matrix │ History  │ System│ │
│ └──────┴─────────┴─────────┴──────────┴────────┴──────────┴───────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                     [Risk Ribbon - Always Visible]              │ │
│ │ Exposure: $12,500 | Margin: 45% | P&L: +$340 | DD: 2.1% | ● OK  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                         [Tab Content Area]                          │
│                                                                     │
│                                                                     │
│                                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.4 Tab Specifications

#### 6.4.1 Live Tab

**Purpose:** Real-time trading dashboard with signal ticker and position monitor

**Layout:**
```
┌────────────────────────────────────────────────────────────────┐
│ LIVE TRADING                                       [⚙] [↻]    │
├────────────────────┬───────────────────────────────────────────┤
│ SIGNAL TICKER      │ OPEN POSITIONS                           │
│ ┌────────────────┐ │ ┌───────────────────────────────────────┐ │
│ │↑ EURUSD LONG   │ │ │ Symbol │ Dir │ Size │ Entry │ P&L    │ │
│ │  STR: 85%      │ │ ├────────┼─────┼──────┼───────┼────────┤ │
│ │  CNF: 72%      │ │ │ EURUSD │ BUY │ 0.5  │1.0850 │ +$125  │ │
│ │  [ACK] [PIN]   │ │ │ GBPUSD │ SELL│ 0.3  │1.2650 │ -$42   │ │
│ ├────────────────┤ │ │        │     │      │       │        │ │
│ │↓ GBPJPY SHORT  │ │ └───────────────────────────────────────┘ │
│ │  STR: 62%      │ │                                           │
│ │  CNF: 58%      │ │ PENDING ORDERS                            │
│ │  [ACK] [PIN]   │ │ ┌───────────────────────────────────────┐ │
│ └────────────────┘ │ │ No pending orders                     │ │
│                    │ └───────────────────────────────────────┘ │
├────────────────────┴───────────────────────────────────────────┤
│ SYSTEM STATUS                                                   │
│ ┌──────────┬──────────┬──────────┬──────────┬──────────┐       │
│ │● Database│● Bridge  │● MT4 Conn│● Calendar│● Risk OK │       │
│ └──────────┴──────────┴──────────┴──────────┴──────────┘       │
└────────────────────────────────────────────────────────────────┘
```

**Interactions:**
- Click signal → Show detail panel
- [ACK] → Acknowledge signal (logs to audit)
- [PIN] → Pin to persistent view
- Double-click position → Show trade detail
- Right-click position → Context menu (Modify SL/TP, Close)

#### 6.4.2 Signals Tab

**Purpose:** Comprehensive signal history with filtering and analysis

**Columns:**
| Column | Width | Sort | Filter | Notes |
|--------|-------|------|--------|-------|
| Time | 100px | ✓ | Date range | Local time, UTC tooltip |
| Symbol | 80px | ✓ | Multi-select | e.g., EURUSD |
| Hybrid ID | 150px | - | Text search | CAL8#CONTEXT#TS |
| Direction | 70px | ✓ | Multi-select | ↑/↓/— indicators |
| Strength | 80px | ✓ | Range slider | 0-100% with bar |
| Confidence | 80px | ✓ | Range slider | Color-coded |
| p (probability) | 60px | ✓ | Range | When available |
| n (sample size) | 60px | ✓ | Range | When available |
| Source | 100px | ✓ | Multi-select | ECO, TECH, etc. |
| Status | 80px | ✓ | Multi-select | ACK, EXEC, DISMISS |

#### 6.4.3 Config Tab

**Purpose:** System configuration and parameter management

**Sections:**
1. **Global Settings**: Risk limits, communication modes
2. **Bridge Configuration**: CSV/Socket settings, paths
3. **Indicator Parameters**: Auto-generated from schemas
4. **Strategy Settings**: Parameter sets, templates
5. **Notification Preferences**: Alerts, sounds, thresholds

**Validation:**
- Real-time validation as user types
- Dependency checks before save
- Undo/Revert capabilities
- Import/Export JSON

#### 6.4.4 Calendar Tab

**Purpose:** Economic event management and monitoring

**Features:**
- Timeline view with anticipation windows
- Event detail panel with historical impact
- Import status with sequence/checksum tracking
- Emergency STOP/RESUME controls

**State Chips:**
| State | Color | Description |
|-------|-------|-------------|
| SCHEDULED | Blue | Future event |
| ANTICIPATION | Yellow | Within anticipation window |
| ACTIVE | Green | Currently active |
| COOLDOWN | Orange | Post-event cooldown |
| EXPIRED | Gray | Past event |

#### 6.4.5 Matrix Tab

**Purpose:** Re-entry decision matrix configuration and visualization

**Dimensions:**
- **Signal Type (S)**: ECO_HIGH, ECO_MED, ANTICIPATION, TECHNICAL
- **Timeframe (T)**: M1, M5, M15, M30, H1, H4, D1
- **Outcome (O)**: WIN, LOSS, BREAKEVEN
- **Context (C)**: Various market conditions
- **Generation**: O, R1, R2

**Visualization:** Heatmap with performance-based coloring

#### 6.4.6 History Tab

**Purpose:** Complete trade history and performance analytics

**Features:**
- Trade list with full traceability
- Equity curve chart
- Drawdown analysis
- Performance metrics (win rate, expectancy, Sharpe)
- Export capabilities

#### 6.4.7 System Tab

**Purpose:** System health and operational controls

**Panels:**
1. **Service Health Grid**: Status of all services
2. **Broker Connection**: Clock skew, latency, DEGRADED mode
3. **Performance Metrics**: CPU, memory, latency percentiles
4. **Operator Controls**: Pause/Resume, Flatten All, Kill Switches
5. **Log Viewer**: Real-time log stream with filtering

### 6.5 Keyboard Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| `Ctrl+1-7` | Switch tabs (1=Live, 2=Signals, etc.) | Global |
| `Ctrl+S` | Save current settings | Config Tab |
| `Ctrl+F` | Focus filter/search | Signals, History |
| `Ctrl+E` | Export current view | Tables |
| `Space` | Acknowledge selected signal | Live, Signals |
| `P` | Pin/Unpin selected signal | Live, Signals |
| `Esc` | Close modal/popup | Global |
| `F5` | Refresh current view | Global |
| `Ctrl+Shift+F` | Emergency Flatten All | Global (with confirm) |

### 6.6 Responsive Behavior

| Breakpoint | Layout Adaptation |
|------------|-------------------|
| ≥1920px | Full multi-column layouts |
| 1280-1919px | Condensed panels, smaller fonts |
| 1024-1279px | Stacked panels, collapsible sections |
| <1024px | Single column, essential info only |

---

## 7. Security & Compliance

### 7.1 Security Requirements

#### 7.1.1 Authentication & Authorization

| Requirement | Implementation | Priority |
|-------------|----------------|----------|
| Local credential storage | OS keychain (Windows Credential Manager, macOS Keychain) | Must Have |
| Session management | JWT tokens with 24hr expiry, refresh tokens | Must Have |
| Role-based access | Admin, Trader, Viewer roles | Should Have |
| Multi-factor authentication | TOTP support for admin actions | Nice to Have |

#### 7.1.2 Data Protection

| Requirement | Implementation | Priority |
|-------------|----------------|----------|
| Local database encryption | SQLCipher AES-256 | Must Have |
| Transport encryption | TLS 1.3 for all network calls | Must Have |
| Sensitive data masking | Mask account numbers in logs | Must Have |
| Secure configuration | Encrypted settings file | Must Have |

#### 7.1.3 Audit & Compliance

| Requirement | Implementation | Priority |
|-------------|----------------|----------|
| Complete audit trail | All user actions logged | Must Have |
| Immutable audit logs | Append-only log files | Must Have |
| Regulatory reporting | MiFID II compatible exports | Should Have |
| Data retention | Configurable retention policies | Should Have |

### 7.2 Threat Model

#### 7.2.1 Attack Vectors

| Vector | Risk Level | Mitigation |
|--------|------------|------------|
| Credential theft | High | OS keychain, MFA |
| Man-in-the-middle | Medium | TLS pinning, cert validation |
| Malicious plugins | Medium | Plugin sandboxing, code signing |
| Local file tampering | Medium | File integrity checks, encryption |
| Memory scraping | Low | Secure memory handling |

#### 7.2.2 Security Testing Requirements

- Static Application Security Testing (SAST) on every build
- Dynamic Application Security Testing (DAST) quarterly
- Penetration testing annually
- Dependency vulnerability scanning continuous

### 7.3 Compliance Requirements

| Regulation | Requirement | Implementation |
|------------|-------------|----------------|
| GDPR | Data portability, right to delete | Export/delete user data |
| MiFID II | Transaction reporting | Complete audit trail |
| SOC 2 | Security controls | Enterprise architecture |
| PCI DSS | Card data protection | N/A (no card data) |

---

## 8. Performance Requirements

### 8.1 Response Time Targets

| Operation | Target | Maximum | Measurement |
|-----------|--------|---------|-------------|
| Signal display update | 100ms | 500ms | From signal generation |
| Position P&L update | 200ms | 1000ms | From price tick |
| Configuration save | 500ms | 2000ms | From user action |
| Chart render | 200ms | 1000ms | 10k data points |
| Table sort/filter | 100ms | 500ms | 50k rows |
| Application startup | 3s | 10s | Cold start |

### 8.2 Resource Utilization

| Resource | Target | Maximum | Notes |
|----------|--------|---------|-------|
| Memory (idle) | 200MB | 500MB | After 1hr operation |
| Memory (active) | 400MB | 1GB | With all tabs open |
| CPU (idle) | 1% | 5% | Background processing |
| CPU (active) | 15% | 50% | Heavy trading activity |
| Disk (database) | 100MB | 1GB | 1 year data |
| Disk (logs) | 50MB | 500MB | With rotation |

### 8.3 Scalability Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Concurrent signals | 500+ | Real-time display |
| Trade history rows | 100,000+ | Responsive filtering |
| Matrix cells | 10,000+ | Smooth navigation |
| Calendar events | 1,000+ | Per week view |
| Audit log entries | 1M+ | With archival |

### 8.4 Network Requirements

| Scenario | Bandwidth | Latency |
|----------|-----------|---------|
| Normal operation | 100 Kbps | <100ms |
| High activity | 500 Kbps | <200ms |
| Initial sync | 2 Mbps | N/A |
| Offline mode | 0 | N/A (local only) |

---

## 9. Integration Requirements

### 9.1 MT4 Integration

#### 9.1.1 CSV Bridge Protocol

**File Locations:**
```
Common\Files\reentry\
├── bridge\
│   ├── trading_signals.csv    # Python → EA
│   └── trade_responses.csv    # EA → Python
├── config\
│   ├── parameters.schema.json
│   └── matrix_map.csv
├── data\
│   └── economic_calendar.csv
└── logs\
    └── parameter_log.csv
```

**Trading Signals Format:**
```csv
version,timestamp_utc,symbol,combination_id,action,parameter_set_id,json_payload_sha256,json_payload
3.0,2025-01-15T14:30:00Z,EURUSD,AUSHNF10#LONG#15MIN,UPDATE_PARAMS,PS-001,abc123...,"{"effective_risk":2.5,...}"
```

**Trade Responses Format:**
```csv
version,timestamp_utc,symbol,combination_id,action,status,ea_code,detail_json
3.0,2025-01-15T14:30:01Z,EURUSD,AUSHNF10#LONG#15MIN,ACK_UPDATE,OK,,"{"order_id":12345}"
```

#### 9.1.2 Socket Protocol (Alternative)

- **Port:** Configurable (default 5555)
- **Protocol:** JSON-RPC 2.0 over TCP
- **Heartbeat:** Every 30 seconds
- **Timeout:** 90 seconds before DEGRADED

### 9.2 Backend Services Integration

#### 9.2.1 API Endpoints

| Service | Endpoint | Method | Purpose |
|---------|----------|--------|---------|
| Calendar Ingestor | `/api/v1/calendar/events` | GET | Fetch calendar events |
| Signal Generator | `/api/v1/signals` | GET | Fetch signals |
| Risk Manager | `/api/v1/risk/assess` | POST | Risk assessment |
| Reporter | `/api/v1/reports` | GET/POST | Generate reports |
| GUI Gateway | `/api/v1/*` | Various | Aggregated APIs |

#### 9.2.2 WebSocket Streams

| Stream | Endpoint | Events |
|--------|----------|--------|
| Signals | `/ws/signals` | signal.new, signal.update |
| Positions | `/ws/positions` | position.open, position.update, position.close |
| Alerts | `/ws/alerts` | risk.alert, system.alert |
| Health | `/ws/health` | service.status |

### 9.3 External Data Sources

| Source | Integration | Frequency | Failover |
|--------|-------------|-----------|----------|
| Forex Factory | CSV download | Weekly (scheduled) | Manual import |
| DDE Price Feed | Real-time subscription | Continuous | Socket fallback |
| Economic APIs | REST polling | 15 minutes | Cache + stale data |

---

## 10. Quality Assurance

### 10.1 Testing Strategy

#### 10.1.1 Testing Pyramid

```
                    ┌─────────┐
                   │   E2E   │  10%
                  │  Tests   │
                 ├───────────┤
                │ Integration│  20%
               │    Tests    │
              ├───────────────┤
             │     Unit       │  70%
            │     Tests       │
           └───────────────────┘
```

#### 10.1.2 Test Categories

| Category | Coverage Target | Tools | Frequency |
|----------|-----------------|-------|-----------|
| Unit Tests | 80% | pytest, pytest-qt | Every commit |
| Integration Tests | 60% | pytest, Docker | Every PR |
| E2E Tests | Core flows | pytest-playwright | Nightly |
| Performance Tests | Key paths | locust, pytest-benchmark | Weekly |
| Security Tests | OWASP Top 10 | bandit, safety | Every PR |

### 10.2 Acceptance Criteria

#### 10.2.1 Functional Acceptance

| Feature | Criteria | Verification |
|---------|----------|--------------|
| Signal Display | Updates within 500ms | Automated timing tests |
| Trade Execution | Correct parameters sent | Bridge validation |
| Risk Limits | Enforced on all orders | Unit + integration tests |
| Data Persistence | No data loss on crash | Recovery tests |
| Audit Trail | All actions logged | Log verification |

#### 10.2.2 Non-Functional Acceptance

| Aspect | Criteria | Verification |
|--------|----------|--------------|
| Startup Time | <10s cold start | Automated timing |
| Memory | <1GB under load | Profiling |
| CPU | <50% sustained | Profiling |
| Accessibility | WCAG 2.1 AA | Axe testing |
| Localization | UTF-8 support | Character tests |

### 10.3 Quality Gates

| Gate | Criteria | Block Merge |
|------|----------|-------------|
| Build | Compiles successfully | Yes |
| Unit Tests | 80% pass rate | Yes |
| Coverage | 80% minimum | Yes |
| Security Scan | No high/critical | Yes |
| Linting | No errors | Yes |
| Integration Tests | 90% pass rate | Yes |
| Performance | No regression >10% | Yes |

---

## 11. Deployment & Distribution

### 11.1 Packaging

#### 11.1.1 Build Artifacts

| Platform | Format | Size Target | Signing |
|----------|--------|-------------|---------|
| Windows | .exe (installer) | <150MB | EV Code Signing |
| macOS | .dmg | <150MB | Apple Notarization |
| Linux | .AppImage, .deb | <150MB | GPG signed |

#### 11.1.2 Auto-Update

- **Mechanism:** Electron-like delta updates
- **Channel:** Stable, Beta, Alpha
- **Frequency:** Check on startup, optional background
- **Rollback:** Keep previous 2 versions

### 11.2 Distribution Channels

| Channel | Audience | Update Frequency |
|---------|----------|------------------|
| Direct Download | All users | On release |
| GitHub Releases | Technical users | On release |
| Beta Program | Early adopters | Weekly |
| Enterprise | Business customers | On request |

### 11.3 System Requirements

#### 11.3.1 Minimum Requirements

| Component | Windows | macOS | Linux |
|-----------|---------|-------|-------|
| OS | Windows 10 64-bit | macOS 10.15+ | Ubuntu 20.04+ |
| CPU | Intel i3 / AMD Ryzen 3 | Apple Silicon or Intel | x86_64 |
| RAM | 4GB | 4GB | 4GB |
| Storage | 500MB | 500MB | 500MB |
| Display | 1280x720 | 1280x720 | 1280x720 |

#### 11.3.2 Recommended Requirements

| Component | Specification |
|-----------|---------------|
| CPU | Intel i5 / AMD Ryzen 5 or better |
| RAM | 8GB+ |
| Storage | SSD with 2GB free |
| Display | 1920x1080 or higher, multiple monitors |
| Network | Stable broadband connection |

### 11.4 Installation Process

1. **Download** installer from secure source
2. **Verify** code signature (automatic on Windows/macOS)
3. **Run** installer with admin privileges (if required)
4. **Configure** initial settings wizard
5. **Connect** to MT4 terminal
6. **Validate** bridge communication
7. **Start** trading

---

## 12. Risk Assessment

### 12.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Bridge communication failure | Medium | High | Fallback modes, retry logic |
| Data corruption | Low | High | Checksums, backups, validation |
| Performance degradation | Medium | Medium | Profiling, optimization |
| Security vulnerability | Low | Critical | Security testing, updates |
| Third-party dependency issues | Medium | Medium | Vendoring, monitoring |

### 12.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| User adoption challenges | Medium | High | UX testing, documentation |
| Regulatory changes | Low | High | Modular compliance framework |
| Competitive pressure | Medium | Medium | Feature differentiation |
| Support burden | Medium | Medium | Self-service documentation |

### 12.3 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data loss during trading | Low | Critical | Redundant storage, audit logs |
| System unavailability | Low | High | Monitoring, quick recovery |
| Configuration errors | Medium | Medium | Validation, defaults |
| User errors | High | Medium | Confirmation dialogs, undo |

---

## 13. Success Metrics

### 13.1 Key Performance Indicators

#### 13.1.1 User Engagement

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily Active Users | 80% of installations | Analytics |
| Average Session Duration | >2 hours | Session tracking |
| Feature Utilization | >70% of features used | Feature flags |
| Signal Acknowledgment Rate | >90% | Signal tracking |

#### 13.1.2 Technical Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Signal Latency | <500ms p95 | Application metrics |
| Crash Rate | <0.1% sessions | Error reporting |
| Update Adoption | >80% within 7 days | Version tracking |
| Support Tickets | <5 per 100 users/month | Help desk |

#### 13.1.3 Business Outcomes

| Metric | Target | Measurement |
|--------|--------|-------------|
| User Retention (30-day) | >85% | Cohort analysis |
| NPS Score | >50 | User surveys |
| Feature Requests Implemented | >60% | Roadmap tracking |
| Trading Volume Increase | >25% | Trading metrics |

### 13.2 Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Bug Escape Rate | <5% | Post-release bugs |
| Test Coverage | >80% | Coverage reports |
| Technical Debt Ratio | <10% | Code analysis |
| Documentation Coverage | 100% public APIs | Doc generation |

---

## 14. Release Timeline

### 14.1 Milestone Schedule

```
Q1 2025 ─────────────────────────────────────────────────────────
│
├── Week 1-4: Foundation Phase
│   ├── Desktop framework setup (PyQt6)
│   ├── Core UI components (Live Tab, Risk Ribbon)
│   └── Basic bridge integration
│
├── Week 5-8: Core Features
│   ├── Signals Tab implementation
│   ├── Config Tab with validation
│   ├── Local database integration
│   └── Unit test coverage to 80%
│
├── Week 9-12: Alpha Release
│   ├── Calendar Tab integration
│   ├── Matrix Tab basic functionality
│   ├── E2E test suite
│   └── Alpha release to internal testers
│
Q2 2025 ─────────────────────────────────────────────────────────
│
├── Week 13-16: Beta Features
│   ├── History Tab with analytics
│   ├── System Status Tab
│   ├── Performance optimization
│   └── Security hardening
│
├── Week 17-20: Beta Release
│   ├── Beta release to external testers
│   ├── Bug fixes and UX refinements
│   ├── Documentation completion
│   └── Installer and auto-update
│
├── Week 21-24: GA Release
│   ├── Final testing and validation
│   ├── Release candidate
│   ├── Production release
│   └── Post-launch support
│
Q3 2025 ─────────────────────────────────────────────────────────
│
├── Phase 3: Enterprise Features
│   ├── Multi-account support
│   ├── Plugin ecosystem
│   ├── Advanced analytics
│   └── Team collaboration
```

### 14.2 Release Criteria

#### 14.2.1 Alpha Release Criteria

- [ ] Core trading functionality operational
- [ ] Bridge communication stable
- [ ] Basic monitoring in place
- [ ] 70% unit test coverage
- [ ] Internal documentation complete

#### 14.2.2 Beta Release Criteria

- [ ] All major features implemented
- [ ] 80% test coverage across categories
- [ ] Performance targets met
- [ ] Security audit completed
- [ ] User documentation draft

#### 14.2.3 GA Release Criteria

- [ ] All acceptance criteria passed
- [ ] Zero P0/P1 bugs open
- [ ] Performance validated under load
- [ ] Security vulnerabilities addressed
- [ ] Complete documentation
- [ ] Support processes in place

---

## Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| CAL8 | 8-character economic calendar identifier |
| Hybrid ID | Composite key linking calendar event to matrix context |
| Signal Strength | Numeric indicator of signal quality (0-1) |
| Confidence | Statistical confidence in signal (0-1) |
| Re-Entry | Trading decision based on previous trade outcome |
| Matrix Cell | Configuration for specific trading context |
| Circuit Breaker | Automatic trading halt mechanism |
| DEGRADED Mode | Reduced functionality due to system issues |

### Appendix B: Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| HUEY_P Unified Specification | `P_techspec/HUEY_P_UNIFIED_SPECIFICATION.md` | Complete system spec |
| GUI Controls Specification | `P_GUI/GUI_Spec_Controls_Sections.md` | UI component details |
| Atomic Process Flow | `P_project_knowledge/atomic_process_flow_reentry_trading_system_v_3.md` | Detailed process steps |
| ADR-0001 | `docs/adr/ADR-0001-service-decomposition.md` | Architecture decisions |
| Service Catalog | `docs/modernization/01_service_catalog.md` | Service definitions |

### Appendix C: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-25 | EAFIX Team | Initial PDR release |

---

**Document Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| QA Lead | | | |
| Security Lead | | | |

---

*This document is the authoritative source for EAFIX Desktop Application requirements. All implementation decisions should reference this document. For clarifications or change requests, contact the Product Owner.*

---
doc_id: DOC-CONFIG-0078
---

# EAFIX Desktop Application
## Technical Design Document (TDD)

**Document Status:** Production Specification v1.0  
**Classification:** Enterprise-Grade Technical Architecture  
**Last Updated:** 2025-11-25  

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Technology Stack](#2-technology-stack)
3. [Component Design](#3-component-design)
4. [Data Architecture](#4-data-architecture)
5. [Integration Specifications](#5-integration-specifications)
6. [Security Architecture](#6-security-architecture)
7. [Performance Engineering](#7-performance-engineering)
8. [Testing Architecture](#8-testing-architecture)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Monitoring & Observability](#10-monitoring--observability)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EAFIX Desktop Application                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Presentation Layer (PyQt6)                    │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │  Live   │ │ Signals │ │ Config  │ │Calendar │ │ Matrix  │   │   │
│  │  │   Tab   │ │   Tab   │ │   Tab   │ │   Tab   │ │   Tab   │   │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │   │
│  │       └───────────┴──────────┬┴──────────┴───────────┘         │   │
│  └───────────────────────────────┼───────────────────────────────────┘   │
│                                  │                                       │
│  ┌───────────────────────────────▼───────────────────────────────────┐   │
│  │                   Application Controller Layer                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │ State Manager│  │  Event Bus   │  │Feature Flags │            │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  └───────────────────────────────┬───────────────────────────────────┘   │
│                                  │                                       │
│  ┌───────────────────────────────▼───────────────────────────────────┐   │
│  │                      Business Logic Layer                         │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │   │
│  │  │Signal  │ │Calendar│ │ Matrix │ │  Risk  │ │Analytics│          │   │
│  │  │Manager │ │Manager │ │Manager │ │Manager │ │ Engine │          │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘          │   │
│  └───────────────────────────────┬───────────────────────────────────┘   │
│                                  │                                       │
│  ┌───────────────────────────────▼───────────────────────────────────┐   │
│  │                       Data Access Layer                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │SQLite (Local)│  │ Redis Cache  │  │  File I/O   │            │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  └───────────────────────────────┬───────────────────────────────────┘   │
│                                  │                                       │
│  ┌───────────────────────────────▼───────────────────────────────────┐   │
│  │                    Integration Layer                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │   │
│  │  │ CSV Bridge   │  │Socket Bridge │  │  REST API   │            │   │
│  │  │ (MT4 Files)  │  │ (Optional)   │  │  (Backend)  │            │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        External Systems                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │   MT4 EA     │  │   Backend    │  │     Economic Calendar        │  │
│  │  (Bridge)    │  │  Services    │  │        Data Sources          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Separation of Concerns** | Layered architecture with clear boundaries |
| **Single Responsibility** | Each component has one well-defined purpose |
| **Dependency Injection** | Components receive dependencies via constructor |
| **Event-Driven** | Loose coupling through pub/sub messaging |
| **Fail-Safe Defaults** | Conservative defaults, fail closed on errors |
| **Audit Everything** | Complete traceability for all decisions |

---

## 2. Technology Stack

### 2.1 Core Technologies

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Desktop Framework** | PyQt6 | 6.6+ | Native performance, rich widgets |
| **Language** | Python | 3.11+ | Existing codebase compatibility |
| **Local Database** | SQLite | 3.40+ | Lightweight, embedded |
| **Cache** | Redis | 7.0+ | Fast pub/sub, data structures |
| **Charts** | PyQtGraph | 0.13+ | High-performance real-time |
| **Packaging** | PyInstaller | 6.0+ | Cross-platform bundling |

### 2.2 Supporting Libraries

```python
# requirements.txt (desktop application)
PyQt6>=6.6.0
PyQt6-Charts>=6.6.0
pyqtgraph>=0.13.0
sqlalchemy>=2.0.0
redis>=5.0.0
pydantic>=2.0.0
structlog>=23.0.0
httpx>=0.25.0
websockets>=12.0
cryptography>=41.0.0
keyring>=24.0.0
appdirs>=1.4.4
```

### 2.3 Development Tools

| Tool | Purpose |
|------|---------|
| Poetry | Dependency management |
| pytest | Testing framework |
| pytest-qt | Qt testing |
| black | Code formatting |
| ruff | Linting |
| mypy | Type checking |
| pre-commit | Git hooks |

---

## 3. Component Design

### 3.1 State Manager

```python
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal
import asyncio

@dataclass
class TradingState:
    signals: List[dict] = field(default_factory=list)
    positions: List[dict] = field(default_factory=list)
    pending_orders: List[dict] = field(default_factory=list)
    alerts: List[dict] = field(default_factory=list)

@dataclass  
class RiskState:
    portfolio_exposure: Decimal = Decimal("0")
    margin_usage: Decimal = Decimal("0")
    daily_pnl: Decimal = Decimal("0")
    drawdown: Decimal = Decimal("0")
    circuit_breaker_status: str = "OK"

@dataclass
class SystemState:
    services_health: Dict[str, str] = field(default_factory=dict)
    bridge_status: str = "DISCONNECTED"
    broker_clock_skew: int = 0
    degraded_mode: bool = False

@dataclass
class ApplicationState:
    trading: TradingState = field(default_factory=TradingState)
    risk: RiskState = field(default_factory=RiskState)
    system: SystemState = field(default_factory=SystemState)
    calendar_events: List[dict] = field(default_factory=list)
    matrix_cells: Dict[str, dict] = field(default_factory=dict)

class StateManager:
    """Centralized state management with change notification."""
    
    def __init__(self):
        self._state = ApplicationState()
        self._subscribers: Dict[str, List[callable]] = {}
        self._lock = asyncio.Lock()
    
    async def update(self, path: str, value: Any) -> None:
        """Update state at path and notify subscribers."""
        async with self._lock:
            self._set_nested(self._state, path, value)
            await self._notify(path, value)
    
    def subscribe(self, path: str, callback: callable) -> callable:
        """Subscribe to state changes at path."""
        if path not in self._subscribers:
            self._subscribers[path] = []
        self._subscribers[path].append(callback)
        return lambda: self._subscribers[path].remove(callback)
    
    async def _notify(self, path: str, value: Any) -> None:
        """Notify all subscribers of state change."""
        for sub_path, callbacks in self._subscribers.items():
            if path.startswith(sub_path) or sub_path.startswith(path):
                for callback in callbacks:
                    await callback(path, value)
```

### 3.2 Event Bus

```python
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import uuid

@dataclass
class Event:
    type: str
    payload: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class EventBus:
    """Pub/sub event bus for component communication."""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
    
    def subscribe(self, event_type: str, handler: Callable) -> Callable:
        """Subscribe to event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        return lambda: self._handlers[event_type].remove(handler)
    
    async def publish(self, event: Event) -> None:
        """Publish event to all subscribers."""
        await self._queue.put(event)
    
    async def start(self) -> None:
        """Start event processing loop."""
        self._running = True
        while self._running:
            event = await self._queue.get()
            handlers = self._handlers.get(event.type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    # Log error but continue processing
                    pass
    
    async def stop(self) -> None:
        """Stop event processing."""
        self._running = False
```

### 3.3 Bridge Adapter

```python
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio

class CSVBridgeAdapter:
    """CSV-based communication with MT4 Expert Advisor."""
    
    BRIDGE_VERSION = "3.0"
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.signals_file = base_path / "bridge" / "trading_signals.csv"
        self.responses_file = base_path / "bridge" / "trade_responses.csv"
        self._last_response_offset = 0
        self._file_seq = 0
    
    async def write_signal(
        self,
        symbol: str,
        combination_id: str,
        action: str,
        parameter_set_id: str,
        payload: Dict[str, Any]
    ) -> str:
        """Write signal to CSV bridge file."""
        json_payload = json.dumps(payload, separators=(',', ':'))
        payload_hash = hashlib.sha256(json_payload.encode()).hexdigest()[:16]
        
        self._file_seq += 1
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        row = [
            self.BRIDGE_VERSION,
            timestamp,
            symbol,
            combination_id,
            action,
            parameter_set_id,
            payload_hash,
            json_payload
        ]
        
        # Atomic write: write to temp, then rename
        temp_file = self.signals_file.with_suffix('.tmp')
        with open(temp_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        
        temp_file.replace(self.signals_file)
        
        return f"{self._file_seq}:{payload_hash}"
    
    async def read_responses(self) -> list:
        """Read new responses from EA."""
        responses = []
        
        if not self.responses_file.exists():
            return responses
        
        with open(self.responses_file, 'r') as f:
            f.seek(self._last_response_offset)
            reader = csv.DictReader(f)
            for row in reader:
                responses.append(row)
            self._last_response_offset = f.tell()
        
        return responses
    
    async def send_heartbeat(self) -> None:
        """Send heartbeat signal."""
        await self.write_signal(
            symbol="HEARTBEAT",
            combination_id="SYSTEM",
            action="HEARTBEAT",
            parameter_set_id="",
            payload={"timestamp": datetime.utcnow().isoformat()}
        )
```

### 3.4 Risk Manager

```python
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class RiskLimits:
    max_position_size: Decimal = Decimal("5.0")  # % of portfolio
    max_portfolio_exposure: Decimal = Decimal("15.0")  # %
    max_daily_loss: Decimal = Decimal("2.0")  # %
    max_drawdown: Decimal = Decimal("10.0")  # %
    margin_limit: Decimal = Decimal("80.0")  # %
    consecutive_loss_limit: int = 5

class RiskManager:
    """Real-time risk management and circuit breakers."""
    
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self._daily_pnl = Decimal("0")
        self._consecutive_losses = 0
        self._peak_equity = Decimal("0")
        self._circuit_breaker_triggered = False
    
    def assess_trade(self, position_size: Decimal, current_exposure: Decimal) -> tuple[bool, str]:
        """Assess if trade is within risk limits."""
        
        # Check circuit breaker
        if self._circuit_breaker_triggered:
            return False, "Circuit breaker active"
        
        # Check position size
        if position_size > self.limits.max_position_size:
            return False, f"Position size {position_size}% exceeds limit {self.limits.max_position_size}%"
        
        # Check total exposure
        new_exposure = current_exposure + position_size
        if new_exposure > self.limits.max_portfolio_exposure:
            return False, f"Total exposure {new_exposure}% exceeds limit {self.limits.max_portfolio_exposure}%"
        
        return True, "OK"
    
    def update_pnl(self, pnl: Decimal, is_loss: bool) -> None:
        """Update P&L and check circuit breakers."""
        self._daily_pnl += pnl
        
        if is_loss:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0
        
        # Check daily loss limit
        if self._daily_pnl < -self.limits.max_daily_loss:
            self._trigger_circuit_breaker("Daily loss limit exceeded")
        
        # Check consecutive losses
        if self._consecutive_losses >= self.limits.consecutive_loss_limit:
            self._trigger_circuit_breaker("Consecutive loss limit exceeded")
    
    def _trigger_circuit_breaker(self, reason: str) -> None:
        """Trigger circuit breaker."""
        self._circuit_breaker_triggered = True
        # Emit alert event
```

---

## 4. Data Architecture

### 4.1 Local Database Schema

```sql
-- Core tables for local persistence

-- Signals cache with full traceability
CREATE TABLE signals (
    id TEXT PRIMARY KEY,
    hybrid_id TEXT,
    cal8_id TEXT,
    timestamp_utc TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT CHECK (direction IN ('LONG', 'SHORT', 'NEUTRAL')),
    strength REAL CHECK (strength BETWEEN 0.0 AND 1.0),
    confidence REAL CHECK (confidence BETWEEN 0.0 AND 1.0),
    probability REAL,
    sample_size INTEGER,
    source TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    executed BOOLEAN DEFAULT FALSE,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade history with complete audit trail
CREATE TABLE trades (
    id TEXT PRIMARY KEY,
    signal_id TEXT REFERENCES signals(id),
    hybrid_id TEXT,
    parameter_set_id TEXT,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    position_size REAL NOT NULL,
    stop_loss REAL,
    take_profit REAL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    pnl REAL,
    pnl_pips REAL,
    outcome TEXT CHECK (outcome IN ('WIN', 'LOSS', 'BREAKEVEN', 'OPEN')),
    duration_minutes INTEGER,
    generation TEXT CHECK (generation IN ('O', 'R1', 'R2')),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Calendar events
CREATE TABLE calendar_events (
    cal8_id TEXT PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL,
    currency TEXT NOT NULL,
    impact TEXT CHECK (impact IN ('HIGH', 'MEDIUM', 'LOW')),
    title TEXT,
    forecast TEXT,
    actual TEXT,
    previous TEXT,
    state TEXT DEFAULT 'SCHEDULED',
    file_seq INTEGER,
    checksum TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matrix configuration
CREATE TABLE matrix_cells (
    cell_key TEXT PRIMARY KEY,
    signal_type TEXT NOT NULL,
    timeframe TEXT,
    outcome TEXT,
    context TEXT,
    generation TEXT,
    parameter_set_id TEXT,
    performance_score REAL,
    sample_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP,
    metadata JSON
);

-- Parameter sets
CREATE TABLE parameter_sets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    effective_risk REAL NOT NULL,
    stop_loss_pips REAL,
    take_profit_pips REAL,
    entry_order_type TEXT,
    trailing_stop BOOLEAN DEFAULT FALSE,
    breakeven_pips REAL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Audit log (append-only)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    action TEXT NOT NULL,
    old_value JSON,
    new_value JSON,
    user_id TEXT,
    correlation_id TEXT,
    timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX idx_signals_timestamp ON signals(timestamp_utc);
CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_hybrid ON signals(hybrid_id);
CREATE INDEX idx_trades_entry ON trades(entry_time);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_calendar_timestamp ON calendar_events(timestamp_utc);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp_utc);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
```

### 4.2 Data Flow Diagrams

```
Signal Processing Flow:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Signal    │────▶│    State    │────▶│     UI      │
│  Generator  │     │   Manager   │     │   Update    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   SQLite    │
                   │   (Cache)   │
                   └─────────────┘

Trade Execution Flow:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Signal    │────▶│    Risk     │────▶│   Bridge    │
│  Selection  │     │  Assessment │     │   Writer    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  CSV File   │
                                        │  (MT4 EA)   │
                                        └─────────────┘
```

---

## 5. Integration Specifications

### 5.1 MT4 Bridge Protocol

#### Signal File Format (trading_signals.csv)
```csv
version,timestamp_utc,symbol,combination_id,action,parameter_set_id,json_payload_sha256,json_payload
3.0,2025-01-15T14:30:00Z,EURUSD,AUSHNF10#LONG#15MIN,UPDATE_PARAMS,PS-001,a1b2c3...,"{"effective_risk":2.5,...}"
3.0,2025-01-15T14:30:00Z,EURUSD,AUSHNF10#LONG#15MIN,TRADE_SIGNAL,PS-001,d4e5f6...,"{"reason":"ECO_HIGH"}"
```

#### Response File Format (trade_responses.csv)
```csv
version,timestamp_utc,symbol,combination_id,action,status,ea_code,detail_json
3.0,2025-01-15T14:30:01Z,EURUSD,AUSHNF10#LONG#15MIN,ACK_UPDATE,OK,,"{"validated":true}"
3.0,2025-01-15T14:30:02Z,EURUSD,AUSHNF10#LONG#15MIN,ACK_TRADE,OK,,"{"order_id":12345,"ticket":67890}"
```

#### Error Codes
| Code | Description | Action |
|------|-------------|--------|
| E0000 | Version mismatch | Update bridge |
| E1001 | Risk limit exceeded | Reduce position |
| E1012 | TP < SL invalid | Fix parameters |
| E1020 | ATR validation fail | Check ATR settings |
| E1030 | Generation cap (R3) | End chain |
| E1040 | Time gate blocked | Wait for gate |
| E1050 | Order send failed | Retry or escalate |

### 5.2 Backend API Integration

```python
# API client for backend services
class BackendClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    async def get_signals(self, symbol: str = None, limit: int = 100) -> list:
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/signals",
                headers=self.headers,
                params=params
            )
            return response.json()
    
    async def get_calendar_events(self, currency: str = None) -> list:
        params = {}
        if currency:
            params["currency"] = currency
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/calendar/events",
                headers=self.headers,
                params=params
            )
            return response.json()
```

---

## 6. Security Architecture

### 6.1 Credential Management

```python
import keyring
from cryptography.fernet import Fernet

class SecureStorage:
    """Secure storage using OS keychain."""
    
    SERVICE_NAME = "eafix-desktop"
    
    @staticmethod
    def store_credential(key: str, value: str) -> None:
        """Store credential in OS keychain."""
        keyring.set_password(SecureStorage.SERVICE_NAME, key, value)
    
    @staticmethod
    def get_credential(key: str) -> Optional[str]:
        """Retrieve credential from OS keychain."""
        return keyring.get_password(SecureStorage.SERVICE_NAME, key)
    
    @staticmethod
    def delete_credential(key: str) -> None:
        """Delete credential from OS keychain."""
        keyring.delete_password(SecureStorage.SERVICE_NAME, key)
```

### 6.2 Database Encryption

```python
# Using SQLCipher for database encryption
from sqlcipher3 import dbapi2 as sqlite

def get_encrypted_connection(db_path: str, key: str):
    """Get encrypted database connection."""
    conn = sqlite.connect(db_path)
    conn.execute(f"PRAGMA key = '{key}'")
    conn.execute("PRAGMA cipher_compatibility = 4")
    return conn
```

---

## 7. Performance Engineering

### 7.1 Optimization Strategies

| Area | Strategy | Target |
|------|----------|--------|
| UI Rendering | Virtual scrolling for large tables | 60 FPS |
| Data Loading | Lazy loading with pagination | <100ms |
| Charts | Downsampling for large datasets | <50ms updates |
| Database | Connection pooling, prepared statements | <10ms queries |
| Memory | Weak references for cached data | <500MB baseline |

### 7.2 Caching Strategy

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CacheManager:
    """Multi-tier caching for performance."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self._local_cache = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def get(self, key: str) -> Optional[Any]:
        # L1: Local memory cache
        if key in self._local_cache:
            entry = self._local_cache[key]
            if entry['expires'] > datetime.utcnow():
                return entry['value']
        
        # L2: Redis cache
        value = await self.redis.get(key)
        if value:
            self._local_cache[key] = {
                'value': value,
                'expires': datetime.utcnow() + self._cache_ttl
            }
        
        return value
```

---

## 8. Testing Architecture

### 8.1 Test Structure

```
tests/
├── unit/
│   ├── test_state_manager.py
│   ├── test_event_bus.py
│   ├── test_risk_manager.py
│   └── test_bridge_adapter.py
├── integration/
│   ├── test_database.py
│   ├── test_bridge_communication.py
│   └── test_api_client.py
├── e2e/
│   ├── test_signal_flow.py
│   ├── test_trade_execution.py
│   └── test_ui_workflows.py
├── performance/
│   ├── test_table_rendering.py
│   └── test_data_loading.py
└── fixtures/
    ├── signals.json
    ├── trades.json
    └── calendar_events.json
```

### 8.2 Test Examples

```python
# Unit test example
import pytest
from decimal import Decimal
from app.risk_manager import RiskManager, RiskLimits

class TestRiskManager:
    @pytest.fixture
    def risk_manager(self):
        limits = RiskLimits(
            max_position_size=Decimal("5.0"),
            max_portfolio_exposure=Decimal("15.0")
        )
        return RiskManager(limits)
    
    def test_assess_trade_within_limits(self, risk_manager):
        allowed, msg = risk_manager.assess_trade(
            position_size=Decimal("2.0"),
            current_exposure=Decimal("5.0")
        )
        assert allowed is True
        assert msg == "OK"
    
    def test_assess_trade_exceeds_position_limit(self, risk_manager):
        allowed, msg = risk_manager.assess_trade(
            position_size=Decimal("10.0"),
            current_exposure=Decimal("0")
        )
        assert allowed is False
        assert "Position size" in msg
```

---

## 9. Deployment Architecture

### 9.1 Build Pipeline

```yaml
# .github/workflows/desktop-build.yml
name: Desktop Build

on:
  push:
    tags: ['v*']

jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      
      - name: Run tests
        run: poetry run pytest
      
      - name: Build executable
        run: poetry run pyinstaller --onefile --windowed app.spec
      
      - name: Sign executable
        if: matrix.os == 'windows-latest'
        run: signtool sign /f cert.pfx /p ${{ secrets.CERT_PASSWORD }} dist/eafix.exe
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: eafix-${{ matrix.os }}
          path: dist/
```

### 9.2 Auto-Update System

```python
import httpx
from packaging import version

class AutoUpdater:
    """Check and download application updates."""
    
    UPDATE_URL = "https://releases.eafix.io/desktop"
    
    async def check_for_updates(self, current_version: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.UPDATE_URL}/latest.json")
            latest = response.json()
        
        if version.parse(latest['version']) > version.parse(current_version):
            return latest
        return None
    
    async def download_update(self, update_info: dict, progress_callback) -> Path:
        download_url = update_info['download_url']
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', download_url) as response:
                total = int(response.headers['content-length'])
                downloaded = 0
                
                with open('update.tmp', 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress_callback(downloaded / total)
        
        return Path('update.tmp')
```

---

## 10. Monitoring & Observability

### 10.1 Logging Configuration

```python
import structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### 10.2 Health Monitoring

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

@dataclass
class HealthStatus:
    service: str
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    last_check: datetime
    details: Dict[str, Any]

class HealthMonitor:
    """Monitor system and service health."""
    
    def __init__(self):
        self._checks = {}
        self._status = {}
    
    def register_check(self, name: str, check_fn: callable):
        self._checks[name] = check_fn
    
    async def run_checks(self) -> Dict[str, HealthStatus]:
        for name, check_fn in self._checks.items():
            try:
                result = await check_fn()
                self._status[name] = HealthStatus(
                    service=name,
                    status="HEALTHY" if result['healthy'] else "UNHEALTHY",
                    last_check=datetime.utcnow(),
                    details=result
                )
            except Exception as e:
                self._status[name] = HealthStatus(
                    service=name,
                    status="UNHEALTHY",
                    last_check=datetime.utcnow(),
                    details={"error": str(e)}
                )
        
        return self._status
```

---

## Appendices

### Appendix A: Error Handling Matrix

| Error Type | Severity | User Action | System Action |
|------------|----------|-------------|---------------|
| Network timeout | Warning | Retry available | Auto-retry 3x |
| Bridge disconnected | Error | Check MT4 | Attempt reconnect |
| Risk limit exceeded | Error | Reduce size | Block trade |
| Database error | Critical | Contact support | Log and alert |
| Authentication failed | Error | Re-login | Clear session |

### Appendix B: Configuration Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "bridge": {
      "type": "object",
      "properties": {
        "mode": {"enum": ["CSV", "SOCKET", "AUTO"]},
        "csv_path": {"type": "string"},
        "socket_port": {"type": "integer", "minimum": 1024, "maximum": 65535},
        "heartbeat_interval": {"type": "integer", "minimum": 10, "maximum": 300}
      }
    },
    "risk": {
      "type": "object",
      "properties": {
        "max_position_size": {"type": "number", "minimum": 0.1, "maximum": 10},
        "max_daily_loss": {"type": "number", "minimum": 0.5, "maximum": 10},
        "circuit_breaker_enabled": {"type": "boolean"}
      }
    }
  }
}
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-25  
**Status:** Production Ready

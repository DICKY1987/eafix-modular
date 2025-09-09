# Service Catalog

## Overview

This document defines the microservices that comprise the modularized EAFIX trading system. Each service has distinct responsibilities, well-defined contracts, and specific service-level objectives.

## Service Definitions

### data-ingestor

**Purpose**: Normalize broker price feed data from MT4/DDE interfaces

**Inputs**: 
- MT4 DDE price feeds
- Socket-based broker data
- CSV price files

**Outputs**: 
- `PriceTick@1.0` events to message bus

**Dependencies**: 
- MT4 terminal (external)
- Message bus (Redis)

**Scaling Profile**: Stateless, single instance (price feed is sequential)

**SLOs**:
- Latency: < 10ms price tick processing
- Availability: 99.5%
- Throughput: 1000+ ticks/second

---

### indicator-engine

**Purpose**: Compute technical indicators from price data

**Inputs**: 
- `PriceTick@1.0` events from data-ingestor

**Outputs**: 
- `IndicatorVector@1.1` events to message bus

**Dependencies**: 
- Message bus (Redis)
- Time-series database (optional)

**Scaling Profile**: Stateless, horizontally scalable by symbol

**SLOs**:
- Latency: < 50ms indicator calculation
- Availability: 99.9%
- Throughput: 500+ calculations/second

---

### signal-generator

**Purpose**: Apply trading rules and generate signals

**Inputs**: 
- `IndicatorVector@1.1` events
- `CalendarEvent@1.0` events
- Configuration from GUI

**Outputs**: 
- `Signal@1.0` events to message bus

**Dependencies**: 
- Message bus (Redis)
- Configuration database

**Scaling Profile**: Stateless, horizontally scalable

**SLOs**:
- Latency: < 100ms signal generation
- Availability: 99.95%
- Accuracy: > 95% rule application

---

### risk-manager

**Purpose**: Position sizing, risk checks, and portfolio management

**Inputs**: 
- HTTP requests with `Signal@1.0` data
- Portfolio state queries

**Outputs**: 
- `OrderIntent@1.2` responses
- Risk metrics to monitoring

**Dependencies**: 
- Portfolio database
- Risk configuration store

**Scaling Profile**: Stateful, requires sticky sessions

**SLOs**:
- Latency: < 200ms risk assessment
- Availability: 99.99%
- Data consistency: ACID compliance

---

### execution-engine

**Purpose**: Execute orders with broker interfaces

**Inputs**: 
- `OrderIntent@1.2` from risk-manager
- Order management commands

**Outputs**: 
- `ExecutionReport@1.0` events
- Broker API calls

**Dependencies**: 
- Broker APIs (MT4, etc.)
- Order state database

**Scaling Profile**: Stateful, single instance per broker

**SLOs**:
- Latency: < 500ms order execution
- Availability: 99.95%
- Fill rate: > 98%

---

### calendar-ingestor

**Purpose**: Ingest and normalize economic calendar data

**Inputs**: 
- Vendor CSV files
- Economic data APIs

**Outputs**: 
- `CalendarEvent@1.0` events
- Normalized calendar database

**Dependencies**: 
- External data vendors
- File system or cloud storage

**Scaling Profile**: Scheduled batch processing

**SLOs**:
- Latency: < 1 minute data ingestion
- Availability: 99.0%
- Data freshness: < 15 minutes

---

### reentry-matrix-svc

**Purpose**: Manage re-entry trading decisions

**Inputs**: 
- Historical trade outcomes
- Current market conditions
- Matrix configuration

**Outputs**: 
- `ReentryDecision@1.0` events
- Decision audit logs

**Dependencies**: 
- Trade history database
- Decision matrix configuration

**Scaling Profile**: Stateful, single instance

**SLOs**:
- Latency: < 300ms decision processing
- Availability: 99.9%
- Decision accuracy: > 90%

---

### reporter

**Purpose**: Generate metrics, reports, and P&L analysis

**Inputs**: 
- Trade execution data
- Performance metrics
- Portfolio state

**Outputs**: 
- HTML/PDF reports
- Metrics dashboards
- Alert notifications

**Dependencies**: 
- Trade database
- Reporting templates

**Scaling Profile**: Batch processing, horizontally scalable

**SLOs**:
- Report generation: < 5 minutes
- Availability: 99.5%
- Data accuracy: 100%

---

### gui-gateway

**Purpose**: API gateway for operator user interface

**Inputs**: 
- HTTP requests from web UI
- WebSocket connections for real-time data

**Outputs**: 
- REST API responses
- WebSocket event streams
- Static UI assets

**Dependencies**: 
- All other services (aggregation)
- Session store

**Scaling Profile**: Stateless, load balanced

**SLOs**:
- Latency: < 100ms API response
- Availability: 99.95%
- Concurrent users: 50+

## Inter-Service Communication

### Event Flow
```
data-ingestor → indicator-engine → signal-generator → risk-manager → execution-engine
                                        ↑
                                calendar-ingestor
                                        ↑
                              reentry-matrix-svc
```

### Synchronous Calls
- GUI → gui-gateway (HTTP)
- signal-generator → risk-manager (HTTP)
- risk-manager → execution-engine (HTTP)

### Asynchronous Events
- All other communication via Redis pub/sub
- Event sourcing for audit trails
- Dead letter queues for error handling
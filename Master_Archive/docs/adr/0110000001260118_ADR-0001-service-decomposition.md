---
doc_id: DOC-CONFIG-0067
---

# ADR-0001: Service Decomposition Strategy

## Status
Accepted

## Context

The EAFIX trading system was initially developed as a monolithic application with tight coupling between components. As the system grew, several challenges emerged:

1. **Deployment Complexity**: Changes to any component required redeploying the entire system
2. **Scaling Limitations**: Unable to scale individual components based on load patterns
3. **Development Bottlenecks**: Multiple teams working on shared codebase caused conflicts
4. **Technology Lock-in**: Difficult to adopt new technologies for specific use cases
5. **Risk Concentration**: Single point of failure affected entire trading system

The system processes critical financial data with strict requirements for:
- **Determinism & Idempotence**: Identical inputs must produce identical outputs
- **Single Source of Truth**: All components must validate against canonical schemas
- **Defensive Posture**: Fail closed on integrity errors, suppress decisions until healthy
- **Explicit Fallbacks**: Tiered parameter resolution with audit trails

## Decision

We will decompose the monolithic EAFIX system into 9 distinct microservices:

### Service Boundaries

1. **Data Ingestor**: Normalizes broker price feeds (MT4/DDE/CSV)
2. **Indicator Engine**: Computes technical indicators from price data
3. **Signal Generator**: Applies trading rules and generates signals
4. **Risk Manager**: Position sizing and risk validation
5. **Execution Engine**: Broker order management
6. **Calendar Ingestor**: Economic calendar data processing
7. **Reentry Matrix Service**: Re-entry decision matrix management
8. **Reporter**: Metrics and P&L reporting
9. **GUI Gateway**: User interface API aggregation

### Communication Patterns

**Asynchronous Events** (via Redis pub/sub):
- Price data flow: data-ingestor → indicator-engine → signal-generator
- Calendar events: calendar-ingestor → signal-generator
- Execution reports: execution-engine → reporter

**Synchronous HTTP APIs**:
- Risk validation: signal-generator → risk-manager
- Order placement: risk-manager → execution-engine
- UI operations: GUI → gui-gateway → services

### Data Consistency

- **Event Sourcing**: All state changes captured as immutable events
- **Schema Versioning**: All contracts versioned (e.g., PriceTick@1.0)
- **Circuit Breakers**: Services fail closed when dependencies unhealthy
- **Audit Logging**: All decisions logged with full context

## Rationale

### Service Boundary Decisions

**Data Ingestor**: Isolated to handle MT4/DDE complexities without affecting other services. Single responsibility for price normalization.

**Indicator Engine**: Computationally intensive, benefits from horizontal scaling. Clear input/output contract with price data.

**Signal Generator**: Business logic hub requiring frequent updates. Isolated to minimize deployment impact.

**Risk Manager**: Critical path requiring high availability and data consistency. Stateful service with strict SLAs.

**Execution Engine**: Broker interface isolation. Single instance per broker to manage connection state.

### Technology Choices

- **Python**: Maintains compatibility with existing codebase and quantitative libraries
- **Redis**: High-performance message bus with pub/sub and persistence
- **PostgreSQL**: ACID compliance for critical financial data
- **Docker**: Consistent deployment across environments
- **Kubernetes**: Production orchestration with auto-scaling

### Event Schema Design

All events include:
- Timestamp (UTC) for audit trails
- Version identifier for schema evolution
- Required fields for data integrity
- Optional metadata for observability

## Consequences

### Positive
- **Independent Deployment**: Services can be updated without system-wide downtime
- **Horizontal Scaling**: Compute-intensive services (indicators) can scale independently
- **Technology Flexibility**: Services can adopt different technologies as needed
- **Fault Isolation**: Failures contained to individual services
- **Team Autonomy**: Clear service ownership and development boundaries
- **Observability**: Fine-grained metrics and logging per service

### Negative
- **Increased Complexity**: Distributed system challenges (network, consistency)
- **Operational Overhead**: More services to monitor and maintain
- **Network Latency**: Inter-service communication adds latency
- **Data Consistency**: Eventually consistent patterns may complicate debugging
- **Development Overhead**: Contract management and versioning required

### Risks & Mitigations

**Risk**: Network partitions between services
**Mitigation**: Circuit breakers, timeout handling, graceful degradation

**Risk**: Message ordering in event streams
**Mitigation**: Timestamp-based ordering, idempotent event processing

**Risk**: Schema evolution breaking compatibility
**Mitigation**: Semantic versioning, backward-compatible changes only

**Risk**: Configuration drift between environments
**Mitigation**: Infrastructure as Code, environment parity validation

## References

- [EAFIX Scope Principles](https://raw.githubusercontent.com/DICKY1987/eafix/main/01_scope_principles.md)
- [Runtime Architecture](https://raw.githubusercontent.com/DICKY1987/eafix/main/02_runtime_architecture.md)
- [Risk & Portfolio Controls](https://raw.githubusercontent.com/DICKY1987/eafix/main/07_risk_portfolio_controls.md)
- [QC & Acceptance Telemetry](https://raw.githubusercontent.com/DICKY1987/eafix/main/08_qc_acceptance_telemetry.md)
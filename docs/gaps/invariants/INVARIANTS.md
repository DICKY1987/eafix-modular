---
doc_id: DOC-CONFIG-0096
---

# Invariants (Executable Specifications)

Each invariant must include: **Context**, **Statement**, **Proof (test)**, **Signals (metrics)**, **Alert**.

## Example — Idempotent order requests
**Context:** execution-engine  
**Statement:** For a given `correlation_id`, exactly one broker order is created.  
**Proof:** Unit test mocks broker; sending duplicates yields 1 call.  
**Signals:** counter `order_dedup_hits_total`.  
**Alert:** if rate > 1% of orders over 5 min.

## Trading System Invariants

### INV-001 — Signal Time-to-Live Enforcement
**Context:** signal-generator → risk-manager  
**Statement:** No trading signal older than 30 seconds may generate an order.  
**Proof:** Unit test creates aged signal, verifies risk-manager rejects with TTL error.  
**Signals:** counter `signal_ttl_violations_total`.  
**Alert:** if any TTL violation occurs (should be zero).

### INV-002 — Position Size Limits
**Context:** risk-manager  
**Statement:** Total position size per symbol cannot exceed configured max_position_size.  
**Proof:** Integration test attempts oversized position, verifies rejection.  
**Signals:** gauge `current_position_size_by_symbol`, counter `risk_limit_breaches_total`.  
**Alert:** if position_size > 0.95 * max_position_size.

### INV-003 — Price Data Freshness
**Context:** indicator-engine  
**Statement:** No indicator calculation uses price data older than 5 seconds.  
**Proof:** Unit test injects stale price tick, verifies indicator calculation skipped.  
**Signals:** histogram `price_data_age_seconds`, counter `stale_data_rejections_total`.  
**Alert:** if p95 price_data_age > 2 seconds for 1 minute.

### INV-004 — Order Correlation Uniqueness
**Context:** execution-engine  
**Statement:** Each order must have unique correlation_id; duplicates are rejected.  
**Proof:** Unit test sends duplicate correlation_id, verifies only first order processed.  
**Signals:** counter `duplicate_correlation_id_total`.  
**Alert:** if duplicate rate > 0.1% of orders over 5 minutes.

### INV-005 — Risk Limits Before Execution
**Context:** signal-generator → risk-manager  
**Statement:** Every trading signal must pass risk validation before execution.  
**Proof:** Integration test bypasses risk validation, verifies order rejection.  
**Signals:** counter `unvalidated_signals_total`, counter `risk_validations_total`.  
**Alert:** if unvalidated_signals > 0 (should always be zero).

### INV-006 — Market Hours Trading Only
**Context:** signal-generator  
**Statement:** No trading signals generated outside configured market hours.  
**Proof:** Unit test runs during off-hours, verifies no signals generated.  
**Signals:** counter `off_hours_signal_attempts_total`.  
**Alert:** if any off-hours trading attempts detected.

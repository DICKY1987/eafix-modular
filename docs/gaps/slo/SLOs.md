# SLOs & Alerts (EAFIX Trading System)

## Core Trading SLOs
- **System Availability:** 99.9% uptime during market hours (6 AM - 6 PM EST)
- **Price Feed Latency:** p95 < 100ms from MT4/DDE to price tick ingestion
- **Signal Generation Latency:** p95 < 500ms from price tick to trading signal
- **Order Execution Latency:** p95 < 2s from signal to broker order submission
- **Data Freshness:** Price data must be < 2s old when used for signal generation

## Service-Level SLOs
- **data-ingestor:** 99.95% availability, p95 latency < 50ms for /healthz
- **indicator-engine:** Process indicators within 200ms of price tick receipt
- **signal-generator:** Generate signals within 300ms of indicator update
- **risk-manager:** Risk validation < 100ms, 99.9% availability
- **execution-engine:** Order placement < 1s, position sync accuracy > 99.5%

## Alert Configuration
- `service_unavailable_ratio > 0.5%` for 2m → page on-call
- `price_tick_gap_seconds > 2` for 30s → immediate alert
- `signal_generation_p95_latency > 1s` for 5m → warn trading team
- `order_execution_p95_latency > 3s` for 2m → critical alert
- `position_sync_drift_total > 0` → immediate reconciliation required
- `risk_limit_breach_total > 0` → halt trading, page risk manager

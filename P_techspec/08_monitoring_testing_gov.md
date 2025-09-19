# Monitoring, Testing & Governance

**Status:** Updated • **Goal:** Make reliability measurable and releases predictable.

## 1. Metrics (emit to DB + `health_metrics.csv`)
- Mapping coverage %, fallback rate, decision latency p95/p99, slippage delta, spread vs model, conflict rate,
  calendar revisions processed, breaker triggers, CSV integrity (seq gaps/checksum failures), router state transitions.

## 2. Alerts
- WARN/PAGE thresholds for coverage, integrity, broker skew, router flapping, decision latency.

## 3. Testing
- **Unit/Golden** for parsers, mappers, overlays.
- **Integration**: calendar revision mid‑chain; forced Tier‑3 fallback; broker min‑stop increase; spread spike.
- **Synthetic**: socket drop, CSV corruption, EA restart hydration.

## 4. Acceptance Gates
- Feature merges blocked unless acceptance tests pass and metrics stay within SLO windows.

## 5. Governance
- Change requests require: risk impact, roll‑out/roll‑back plan, test evidence, owner sign‑off.
- Weekly ops review: incidents, coverage trends, false‑positive/negative analysis.

## 6. Data Retention
- CSV artifacts: 30 days; metrics and audits: 180 days (configurable).

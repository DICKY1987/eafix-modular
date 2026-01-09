---
doc_id: DOC-LEGACY-0057
---

# QC, Acceptance, Telemetry & Alerts

**Status:** Updated • **Goal:** Make health and coverage visible; gate releases with deterministic checks. (Master §9.700, §11–§15) fileciteturn2file0

## 1. Acceptance (Selected)
- **Calendar Intake:** freshness ≤24h; ≥95% expected rows; avg quality ≥0.90; idempotent; tolerant to field renames and same‑second reschedules. (Master §9.100) fileciteturn2file0  
- **PCL Failover:** detect ≤3s; switch ≤2s; retry with expo backoff; audit transitions. (Master §9.100 Acceptance) fileciteturn2file0

## 2. Metrics & Health
Emit to DB + `health_metrics.csv`: mapping coverage %, fallback rate, decision latency p95/p99, slippage delta, spread vs model, conflict rate, calendar revisions processed, breaker triggers, CSV integrity (seq gaps/checksum failures). (Master §14.1–§14.3) fileciteturn2file0

## 3. Alerts (Thresholds)
- **Coverage WARN/PAGE** on fallback or conflict spikes; **Integrity ERROR** on checksum/seq failures; **Broker Drift/Skew** on thresholds. (Master §14.2, §2.4.1) fileciteturn2file0

## 4. Test Cues
Calendar revision mid‑chain, broker min stop increase, forced Tier‑3 fallback, EA kill/restart hydration, spread spike response. (Master §9.700) fileciteturn2file0

## 5. System Status UI Contract
Tiles for transport uptime, coverage%, fallback rate, latency, slippage delta, conflict rate, calendar revisions, breaker triggers, CSV integrity; **Broker Clock Skew badge** with DEGRADED rules. (Master GUI §15.1–§15.4) fileciteturn2file1

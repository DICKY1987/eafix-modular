---
doc_id: DOC-CONFIG-0095
---

# Mini-FMEA (Failure Modes & Effects Analysis)

| Failure | Cause | Detection | Effect | Mitigation | Residual Risk |
|---------|------|-----------|--------|------------|---------------|
| Price feed gap > 2s | MT4/DDE connection loss | `price_tick_gap_seconds` metric | Stale indicators/signals | Failover to backup feed; alert at 1s gap | Low |
| Signal generation stops | Indicator engine crash | No `Signal@1.0` events for 30s | No new trades | Service auto-restart; health check monitoring | Medium |
| Broker API rejection | Invalid order params | `order_reject_total` counter | Missed trading opportunities | Pre-trade validation; parameter checking | Medium |
| Redis message loss | Redis restart/network | Missing event correlation IDs | Incomplete trade pipeline | Redis persistence; event replay capability | Low |
| Position sync drift | Manual trades in MT4 | Position reconciliation alerts | P&L calculation errors | Automated position sync every 5min | High |
| Risk limits exceeded | Market volatility spike | `risk_limit_breach_total` | System trading halt | Dynamic risk adjustment; circuit breakers | Low |
| Database corruption | Disk failure/corruption | Health check failures | Historical data loss | Automated backups; RAID configuration | Medium |

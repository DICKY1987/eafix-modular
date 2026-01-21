---
doc_id: DOC-CONFIG-0069
---

# Gap Register

| ID | Area (Logic/Arch/Process) | Title | Evidence | Impact | Root Cause | RPN (S×O×D) | Owner | Fix PR/Plan | Due |
|----|----------------------------|-------|----------|--------|------------|-------------|-------|-------------|-----|
| G-001 | Logic | Signal TTL enforcement | Signals can age > 30s before order execution | Stale trades | Missing TTL validation | 8×4×3=96 | risk-manager | Add signal timestamp checks | 2025-09-15 |
| G-002 | Arch | Redis failover | Single Redis instance - no failover | Service outage | No clustering setup | 9×2×2=36 | infra | Redis cluster config | 2025-09-30 |
| G-003 | Process | Position reconciliation | No automated position sync with broker | Trade discrepancies | Manual reconciliation only | 7×3×5=105 | execution-engine | Automated position sync | 2025-09-22 |
| G-004 | Logic | Duplicate order prevention | Race condition allows duplicate orders | Double positions | Missing idempotency keys | 8×3×2=48 | execution-engine | Implement correlation IDs | 2025-09-18 |
| G-005 | Arch | Database backups | No automated DB backup strategy | Data loss risk | Missing backup automation | 9×1×1=9 | infra | Automated backup scripts | 2025-10-15 |

> RPN = Severity × Occurrence × Detectability (1–10 each). Sort by highest first.

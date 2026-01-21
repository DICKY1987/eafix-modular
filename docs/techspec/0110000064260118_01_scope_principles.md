---
doc_id: DOC-LEGACY-0045
---

# Scope Principles

**Status:** Updated • **Intent:** Provide the guardrails that shape design decisions and reviews.

## 1. Determinism & Idempotence
- Each emitter writes atomically (`*.tmp` → fsync → rename); reruns produce identical artifacts for identical inputs.

## 2. Single Source of Truth
- CSV contracts + schemas are canonical; EA, services, and GUI all validate against the same definitions.

## 3. Defensive Posture
- Fail **closed** on integrity errors; enter **DEGRADED** mode on broker clock‑skew; suppress decisions until healthy.

## 4. Explicit Fallbacks
- Tiered resolution in Matrix (exact → relaxed → calendar‑only → global default) with audit trails and coverage metrics.

## 5. Observability First
- Every feature ships with metrics, thresholds, and an operator surface (System Status tiles + diagnostics).

## 6. Backward Compatibility (Pragmatic)
- CAL5 retained as alias; CAL8 + Hybrid ID are primary. Readers remain tolerant to renamed vendor fields.

## 7. Minimal Footprint in EA
- EA reads strictly, writes append‑only, and surfaces health; no business logic duplication.

## 8. Security & Audit
- Append‑only ledgers; signed releases; checksum verification at ingestion points.

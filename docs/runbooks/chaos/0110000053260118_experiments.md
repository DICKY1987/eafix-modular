---
doc_id: DOC-CONFIG-0098
---

# Chaos Experiments

Objective: Validate resilience to common failure modes in staging before production.

## Safety
- Run only in non-production unless explicitly approved.
- Announce experiment window and rollback plan.

## Experiments
1. Pod Kill
   - Randomly delete a pod from a stateless service; observe recovery time.
   - Success: HPA/ReplicaSet replaces pod; no SLO breach.
2. Latency Injection (Downstream)
   - Introduce 200–500ms latency to a dependency; verify timeouts and fallbacks.
3. Resource Pressure
   - Constrain CPU to force throttling; validate backpressure and queue handling.

## Observability
- Record metrics (latency, error rate, saturation) and logs.
- Link dashboards and traces for each experiment.

## Findings
- Document impact, mitigations, and follow-up actions.


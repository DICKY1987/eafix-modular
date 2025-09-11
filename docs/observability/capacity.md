# Capacity Planning Guide

This document captures baseline capacity assumptions and guidance for sizing services.

## Goals
- Define CPU/memory requests and limits per service.
- Establish initial autoscaling targets (e.g., CPU%, RPS, queue depth).
- Document measurement methodology and acceptance gates.

## Methodology
- Use perf scripts in `scripts/perf/` to drive synthetic load.
- Measure latency SLOs (p50/p95/p99), error rate, saturation, and utilization.
- Iterate requests/limits and HPA settings until SLOs hold over soak duration.

## Outputs
- Per-service sizing table maintained alongside Helm values:
  - `deploy/helm/<service>/values.yaml`
  - `deploy/kubernetes/` (if applicable)

## Acceptance
- Baseline load meets latency/error SLOs without exhausting error budget.
- HPA scales within guardrails under step and ramp loads.


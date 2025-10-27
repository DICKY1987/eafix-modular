# Chaos Scripts

This folder contains helpers and docs to run small, safe chaos experiments in staging.

Examples:
- Pod kill via `kubectl delete pod` on a stateless deployment
- Latency injection using a sidecar or `tc` in a test environment

Refer to `docs/runbooks/chaos/experiments.md` for experiment design and safety.


GDW Troubleshooting

- `gdw list` shows empty: ensure `catalog/index.json` exists or the `gdw/` tree has `spec.json` under `v<semver>/`.
- Orchestrator does not defer: check `config/gdw_policies.json` (`deferral.enabled=true`, `mode=prefer|only`) or use CLI flags `--gdw-prefer` / `--gdw-only`.
- No events: set `GDW_BROADCAST=1` and run `uvicorn services.event_bus.main:app --port 8001`, then tail `/events/recent`.
- No metrics: ensure processes exposing `/metrics` run; Prometheus config in `monitoring/prometheus.yml` and compose stack are up.
- Windows tests: use `nox -s gdw_tests` (minimal deps; optional tests gated by `RUN_GDW_OPTIONAL=1`).


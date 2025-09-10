# Runtime Architecture

**Status:** Updated • **Goal:** Clear process topology, start‑up/shutdown, failure domains, and recovery.

## 1. Processes & Roles
- **calendar_intake**: discover → parse (tolerant) → normalize → anticipation → DB UPSERT → export `active_calendar_signals.csv`.
- **matrix_mapper**: resolve Hybrid context → ParameterSet (+ tier/fallback) → coverage telemetry.
- **reentry_engine**: classify outcome/duration → overlays → emit `reentry_decisions.csv` respecting breakers/ledger.
- **transport_router**: CSV primary; optional socket; health/heartbeat; promotions/demotions; integrity guard.
- **ea_bridge**: EA reader/writer; symbol guards; broker skew checks; trade result append.
- **telemetry_daemon**: aggregate metrics → `health_metrics.csv` + DB; fire alerts; maintain status cache for GUI.
- **gui_app**: operator UX; System Status; Signals/History/Config/Diagnostics tabs.

## 2. Data Stores
- **SQLite** (calendar_events, mapping_audit, reentry_ledger, metrics) — WAL mode, periodic VACUUM.
- **CSV artifacts** (signals, decisions, trade_results, health) — append or atomic replace, with `file_seq` + sha256.

## 3. Scheduling & Lifecycles
- Weekly calendar job (Sun 12:00 America/Chicago).  
- On start, services **hydrate** from DB and latest CSV to rebuild in‑memory state.

## 4. Fault Tolerance
- Circuit‑breaker library (per transport, mapping coverage, integrity, broker skew).  
- Router demotes on heartbeat/parse/overflow/connect errors; promotes after stable window (≥60s).

## 5. Start‑up/Shutdown Order
1) telemetry_daemon → 2) calendar_intake → 3) matrix_mapper → 4) reentry_engine → 5) transport_router → 6) gui_app → 7) EA.  
Shutdown: reverse; ensure final flush and close cleanly.

## 6. Runbook Hooks
- `simple_socket_test.py`, `csv_integrity_check.py`, `broker_skew_probe.py` — all feed Diagnostics tab and metrics.

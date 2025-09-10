# Scope Overview

**Status:** Updated • **Masters:** `integrated_economic_calendar_matrix_re_entry_system_spec_UPDATED__rev2.md`, `huey_p_unified_gui_signals_spec_merged_currency_strength_ui_removed.md`  
**Primary Goal:** End‑to‑end, resilient pipeline from **Economic Calendar → Matrix/Signals → Re‑Entry Decisions → EA Execution → Outcomes → Telemetry** with strict contracts and operator‑grade UX.

## 1. In‑Scope
- **Economic Calendar ingestion & normalization** (weekly scheduled, tolerant parsing, revision handling)
- **Signal matrix mapping** (Hybrid ID, score‑based composition, tiered fallbacks)
- **Re‑Entry governance** (Outcome/Duration classification, overlay precedence, O→R1→R2 caps)
- **Transport & Bridge** (**CSV‑first**, optional socket, automatic failover, atomic write/rename, `file_seq`, `checksum_sha256`)
- **EA integration** (strict readers/writers, UTC, guards, broker clock‑skew handling)
- **Observability & Ops** (metrics, health, coverage, alerts, acceptance tests)
- **GUI** (operator workflow, System Status, Signals/History/Config/Diagnostics)

## 2. Out‑of‑Scope / Non‑Goals
- **Excel/VBA dashboards** (removed) — all visuals are Python GUI.
- **Currency Strength UI** (explicitly excluded from v1 of the unified GUI).
- **Multi‑broker order routing** (single active broker per EA instance).
- **Strategy research notebooks** (development artifacts, not productized).

## 3. Subsystems
1) **Calendar** (intake → normalize → anticipate → export active signals)  
2) **Matrix** (lookup Hybrid context → ParameterSet with audit)  
3) **Re‑Entry** (decisioning with overlays, limits, breakers)  
4) **Transport/Comm** (CSV primary + optional socket, failover)  
5) **EA Bridge** (read decisions, write results; guardrails)  
6) **Observability** (metrics, alerts, acceptance gates)  
7) **GUI** (tabs, panels, controls tied to contracts)

## 4. Data Contracts (Authoritative)
- All transports emit **UTC ISO8601**, **monotonic `file_seq`**, and **`checksum_sha256`**.
- Readers MUST ignore out‑of‑order sequences and fail closed on checksum mismatch.

## 5. Time & Locale
- Scheduler aligned to **America/Chicago**; all persisted times are **UTC**.

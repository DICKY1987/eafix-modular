# CSV Contracts & Atomic Write Policy

**Status:** Updated • **Transport:** CSV is **primary**; Socket optional. (Master §2.1–§2.3) fileciteturn2file0

## 1. Shared Rules
- **Atomic write:** write `*.tmp` → compute **SHA‑256** → fsync → rename to final. (Master §2.3) fileciteturn2file0  
- **Sequencing:** monotonic **`file_seq`** per artifact; readers ignore out‑of‑order. (Master §2.2–§2.3) fileciteturn2file0  
- **Timestamps:** all **UTC ISO8601**. (Master §0.4, §2.4) fileciteturn2file0  
- **Integrity:** use **`checksum_sha256`** (standardized).

## 2. `active_calendar_signals.csv`
**Columns:**  
`symbol, cal8, cal5, signal_type, proximity, event_time_utc, state, priority_weight, file_seq, created_at_utc, checksum_sha256`  
**Notes:** Emitted on state/proximity change and on revisions. (Master §2.2, §4.3–§4.6, §4.8) fileciteturn2file0

## 3. `reentry_decisions.csv`
**Columns:**  
`hybrid_id, parameter_set_id, param_version, lots, sl_points, tp_points, entry_offset_points, comment, file_seq, created_at_utc, checksum_sha256`  
**Notes:** Emission is blocked in **DEGRADED** clock‑skew mode. (Master §2.2, §2.4.1) fileciteturn2file0

## 4. `trade_results.csv`
**Columns:**  
`file_seq, ts_utc, account_id, symbol, ticket, direction, lots, entry_price, close_price, profit_ccy, pips, open_time_utc, close_time_utc, sl_price, tp_price, magic_number, close_reason, signal_source, parameter_set_id, param_version, checksum_sha256`  
**Notes:** **Append‑only**, atomic; include **frozen** parameter set ID@version. (Master §2.2, §7.7 Freeze Rules, §16.4.3) fileciteturn2file0

## 5. `health_metrics.csv`
**Columns:**  
`timestamp, database_connected, ea_bridge_connected, last_heartbeat, error_count, warning_count, cpu_usage, memory_usage, win_rate, max_drawdown`  
Add transport uptime and integrity counters as needed. (Master §2.2.4, §14.1–§14.3) fileciteturn2file0

## 6. Reader Behavior (EA & Services)
- Verify **`file_seq`** strictly increases; verify **`checksum_sha256`**.  
- **Symbol guard:** EA executes only when `symbol == Symbol()`.  
- **Pre‑flight:** reapply BrokerConstraints & PairEffect; enforce circuit breakers. (Master §16.4.3, §7.7, §8.1, §6.7) fileciteturn2file0

---
doc_id: DOC-CONTRACT-0029
---

# Transport & EA Bridge Contracts

**Status:** Updated • **Goal:** CSV‑first bridge with optional DLL socket and strict ingestion on EA side. (Master §2.7–§2.10, §16.4–§17) fileciteturn2file0

## 1. CSVAdapter (Production Default)
- Paths within `<MT4_DATA_FOLDER>`; poll ≤5s; atomic read with `file_seq` + **SHA‑256**. (Master §2.7, §17.1) fileciteturn2file0

## 2. SocketAdapter (Optional)
- EA hosts DLL server (port 5555); Python client sends newline‑delimited JSON; heartbeat every 30s; single client. (Master §2.7) fileciteturn2file0

## 3. Failover
- Prefer Socket; demote on heartbeat/parse/overflow/connect error; promote after ≥60s healthy; metrics record state & reason. (Master §2.8) fileciteturn2file0

## 4. EA Contracts
- **Read:** `reentry_decisions.csv` (seq+checksum; `symbol == Symbol()`), optionally `active_calendar_signals.csv` for display.  
- **Write:** `trade_results.csv` (append, UTC, checksum). (Master §17.1–§17.2) fileciteturn2file0

## 5. Broker Clock Skew
- DEGRADED when |offset| > **120s** or offset stale > **15m**; suppress decisions; require two consecutive healthy checks to restore. (Master §2.4.1, §15.1) fileciteturn2file0

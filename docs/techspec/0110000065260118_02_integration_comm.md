---
doc_id: DOC-LEGACY-0046
---

# Integration & Communication Layer (PCL)

**Status:** Updated • **Goal:** Unified, pluggable transport with automatic failover and health reporting. (Master §2.6–§2.9) fileciteturn2file0

## 1. Adapters
- **CSVAdapter (primary):** file‑based, atomic, polled by EA (≤5s).  
- **SocketAdapter (optional):** DLL socket server (EA) with a single Python client; JSON lines; heartbeats every 30s. (Master §2.7) fileciteturn2file0

## 2. Router Policy
- Prefer **Socket** when healthy; demote on connect/heartbeat/parse/overflow errors; promote after ≥60s healthy. Emit state + reason. (Master §2.8) fileciteturn2file0

## 3. Integrity Guard
- Enforce `file_seq` monotonicity; validate **SHA‑256** (CSV) and JSON schema (Socket) before delivery. (Master §2.6) fileciteturn2file0

## 4. Configuration Flags
- EA: `EnableCSVSignals`, `EnableDLLSignals`, `ListenPort`, `CommPollSeconds`, `DebugComm`.  
- PY: `COMM_MODE=auto|csv|socket`, `CSV_DIR`, `SOCKET_HOST/PORT`, `CHECKSUM=sha256`, `SEQ_ENFORCE=true`. (Master §2.9) fileciteturn2file0

## 5. Troubleshooting Hooks
- Ship `simple_socket_test.py` and a CSV integrity checker; surface seq gaps, checksum failures, socket status, heartbeats in UI. (Master §2.10, §14.3) fileciteturn2file0

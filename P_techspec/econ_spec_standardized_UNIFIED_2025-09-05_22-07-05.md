# 0. Document Control

<!-- BEGIN:ECON.000.001.001.CTRL.doc_metadata -->
## 0.1 Title
Integrated Economic Calendar → Matrix → Re‑Entry System — Technical Specification (Hierarchical Indexed)

**Document ID:** ECON  
**Version:** 2.0  
**Last Modified:** 2024-01-15  
**Dependencies:** None  
**Affects:** All subsystems
<!-- END:ECON.000.001.001.CTRL.doc_metadata -->

<!-- BEGIN:ECON.000.002.001.REQ.scope_definition -->
## 0.2 Purpose & Scope
Defines the architecture, identifiers, data contracts, and operational processes for integrating (A) the Economic Calendar subsystem, (B) the Multi‑Dimensional Matrix subsystem, and (C) the Re‑Entry subsystem, including Python/database components and MT4 (MQL4) bridges. Incorporates the latest fixes replacing prior inferior logic.
<!-- END:ECON.000.002.001.REQ.scope_definition -->

<!-- BEGIN:ECON.000.005.001.DEF.glossary -->
## 0.5 Definitions
- **CAL5**: Legacy 5‑digit calendar strategy ID (country+impact).
- **CAL8**: Extended 8‑symbol identifier (Region|Country|Impact|EventType|RevisionFlag|Version) per @ECON.003.002.
- **Hybrid ID**: Composite key joining calendar and matrix context per @ECON.003.004.
- **PairEffect**: Per‑symbol effect model (bias/spread/cooldown) per @ECON.007.003.
<!-- END:ECON.000.005.001.DEF.glossary -->

---

# 1. System Overview

<!-- BEGIN:ECON.001.001.001.REQ.objectives -->
## 1.1 Objectives
1) Fuse calendar awareness with outcome‑ and time‑aware re‑entries.
2) Standardize identifiers and data flows for reproducible decisions.
3) Enforce risk, exposure, and broker constraints.
<!-- DEPS: None -->
<!-- AFFECTS: ECON.002, ECON.003, ECON.004, ECON.005, ECON.006 -->
<!-- END:ECON.001.001.001.REQ.objectives -->

<!-- BEGIN:ECON.001.002.001.ARCH.system_components -->
## 1.2 System Components
- A) Economic Calendar Subsystem (@ECON.004)
- B) Multi‑Dimensional Matrix Subsystem (@ECON.005)
- C) Re‑Entry Subsystem (@ECON.006)
- D) Data & Storage Layer (@ECON.007)
- E) Risk & Portfolio Controls (@ECON.008)
- F) Integration & Communication Layer (@ECON.002)
- G) Monitoring, Testing, Governance (@ECON.013–@ECON.015)
<!-- DEPS: None -->
<!-- AFFECTS: All subsystems -->
<!-- END:ECON.001.002.001.ARCH.system_components -->

---

# 2. Integration & Communication Layer

<!-- BEGIN:ECON.002.001.001.REQ.transport_contracts -->
## 2.1 Inter‑Process Contracts
- **Transport**: CSV file drops on shared path; optional TCP/IPC later.
- **Atomicity**: Writers output `*.tmp`, include `file_seq`, `created_at_utc`, `checksum_sha256`, then rename to final path (@ECON.002.003).
- **Consumption Rule**: Readers process only strictly increasing `file_seq` with valid checksum_sha256.
<!-- DEPS: None -->
<!-- AFFECTS: ECON.002.002, ECON.002.003, ECON.017 -->
<!-- END:ECON.002.001.001.REQ.transport_contracts -->

<!-- BEGIN:ECON.002.002.001.TABLE.csv_artifacts -->
## 2.2 CSV Artifacts
- `active_calendar_signals.csv`: `symbol, cal8, cal5, signal_type, proximity, event_time_utc, state, priority_weight, file_seq, created_at_utc, checksum_sha256`
- `reentry_decisions.csv`: `hybrid_id, parameter_set_id, lots, sl_points, tp_points, entry_offset_points, comment, file_seq, created_at_utc, checksum_sha256`
- `trade_results.csv`: `file_seq, ts_utc, account_id, symbol, ticket, direction, lots, entry_price, close_price, profit_ccy, pips, open_time_utc, close_time_utc, sl_price, tp_price, magic_number, close_reason, signal_source, checksum_sha256`
- `health_metrics.csv`: rolling KPIs (@ECON.014.002)
<!-- DEPS: ECON.002.001 -->
<!-- AFFECTS: ECON.002.003, ECON.017.001, ECON.017.002 -->
<!-- END:ECON.002.002.001.TABLE.csv_artifacts -->

<!-- BEGIN:ECON.002.003.001.FLOW.atomic_write -->
## 2.3 Atomic Write Procedure
1) Serialize rows → temp file with `file_seq`.
2) Compute SHA‑256 checksum_sha256 field; fsync.
3) Rename `*.tmp` → final; notify via file watcher (optional).
<!-- DEPS: ECON.002.001 -->
<!-- AFFECTS: ECON.002.002, ECON.017.001, ECON.017.002 -->
<!-- END:ECON.002.003.001.FLOW.atomic_write -->

<!-- BEGIN:ECON.002.004.001.REQ.time_timezone -->
### 2.4.1 Time & Timezone — Broker Skew Rules
**Purpose:** Ensure time alignment across UTC normalization, broker clock, and calendar triggers.

**Inputs**
- `utc_now` (system UTC time)
- `broker_time` (EA-reported time via bridge)
- `last_offset_update_ts` (UTC)
- `max_skew_seconds` = **120**
- `max_offset_age_seconds` = **900** (15 minutes)

**Rules**
1. **Offset Calculation:** `offset = broker_time - utc_now` (signed seconds).
2. **Skew Check:** If `abs(offset) > max_skew_seconds` → **DEGRADED**.
3. **Staleness Check:** If `utc_now - last_offset_update_ts > max_offset_age_seconds` → **DEGRADED**.
4. **Degraded Mode Behavior:**
   - Set `ea_bridge_connected=0` in `health_metrics.csv`.
   - **Do not** emit `reentry_decisions.csv`.
   - Re-attempt broker sync every **60s**; return to **NORMAL** only after two consecutive healthy checks.
5. **Audit:** Record transitions NORMAL↔DEGRADED in `error_log` with the measured skew.
<!-- DEPS: ECON.002.002 -->
<!-- AFFECTS: ECON.014.001, ECON.017.001 -->
<!-- END:ECON.002.004.001.REQ.time_timezone -->

---

# 3. Identifier Systems (Standardization)

<!-- BEGIN:ECON.003.002.001.DEF.cal8_format -->
## 3.2 CAL8 (Extended Calendar Identifier)
Format: `R1C2I1E2V1F1` → 8 symbols encoded as fields:
- **R (1)**: Region code (e.g., A=Americas, E=Europe, P=APAC).
- **C (2)**: Country/currency (e.g., US, EU, GB, JP).
- **I (1)**: Impact (H=High, M=Med).
- **E (2)**: Event type (e.g., NF=Nonfarm payrolls, CP=CPI, RD=Rate decision, PM=PMI).
- **V (1)**: Version/ingest schema rev.
- **F (1)**: Revision flag sequence (0=no revision, 1..9 revision order).

**Examples**: `AUS H NF 1 0` → `AUSHNF10`; `EGB MCP 1 0` → `EGBMCP10` (space added for readability; stored as 8 chars).
<!-- DEPS: None -->
<!-- AFFECTS: ECON.003.003, ECON.003.004, ECON.004.004, ECON.007.002 -->
<!-- END:ECON.003.002.001.DEF.cal8_format -->

<!-- BEGIN:ECON.003.004.001.DEF.hybrid_id -->
## 3.4 Hybrid ID (Primary Key)
Format: `[CAL8|00000000]-[GEN]-[SIG]-[DUR]-[OUT]-[PROX]-[SYMBOL]`
- **GEN**: `O|R1|R2`
- **SIG**: e.g., `ECO_HIGH_USD`, `ANTICIPATION_1HR_EUR`, `VOLATILITY_SPIKE`, `ALL_INDICATORS`.
- **DUR**: `FL|QK|MD|LG|EX|NA` (NA for durationless signals).
- **OUT**: `O1..O6` (Full SL → Beyond TP, @ECON.005.003).
- **PROX**: `IM|SH|LG|EX|CD` (Immediate/Short/Long/Extended/Cooldown).

**Example**: `AUSHNF10-O-ECO_HIGH_USD-FL-O4-IM-EURUSD`.
<!-- DEPS: ECON.003.002, ECON.005.003, ECON.005.004, ECON.005.005, ECON.005.006 -->
<!-- AFFECTS: ECON.005.008, ECON.006.005, ECON.007.002, ECON.009.213 -->
<!-- END:ECON.003.004.001.DEF.hybrid_id -->

---

# 7. Data & Storage Layer

<!-- BEGIN:ECON.007.002.001.TABLE.calendar_events -->
#### 7.2 `calendar_events`
Columns:
- `id` INTEGER PK AUTOINCREMENT
- `cal8` TEXT NOT NULL UNIQUE
- `cal5` TEXT NOT NULL
- `event_time_utc` TEXT NOT NULL
- `country` TEXT NOT NULL
- `currency` TEXT NOT NULL
- `impact` TEXT CHECK(impact IN ('High','Medium')) NOT NULL
- `event_type` TEXT CHECK(event_type IN ('ORIGINAL','ANTICIPATION','EQUITY_OPEN')) NOT NULL
- `strategy_id_rci` TEXT NOT NULL  -- 5-digit RCI
- `hours_before` INTEGER DEFAULT 0  -- anticipation only
- `priority` INTEGER NOT NULL       -- ANT<ORIG<EQT ordering
- `offset_minutes` INTEGER DEFAULT 0
- `quality_score` REAL DEFAULT 1.0
Indexes:
- `idx_calendar_events_time` on (`event_time_utc`)
- `idx_calendar_events_country_impact` on (`country`,`impact`)
<!-- DEPS: ECON.003.002, ECON.004.004 -->
<!-- AFFECTS: ECON.004.005, ECON.004.006, ECON.009.102 -->
<!-- END:ECON.007.002.001.TABLE.calendar_events -->

<!-- BEGIN:ECON.007.003.001.TABLE.pair_effect -->
#### 7.3 `pair_effect`
Columns:
- `id` INTEGER PK
- `symbol` TEXT NOT NULL
- `cal8` TEXT NOT NULL
- `bias` TEXT CHECK(bias IN ('LONG','SHORT','NEUTRAL')) DEFAULT 'NEUTRAL'
- `exposure_cap_pct` REAL DEFAULT 3.0
- `note` TEXT
Unique:
- (`symbol`,`cal8`)
Indexes:
- `idx_pair_effect_symbol` on (`symbol`)
<!-- DEPS: ECON.003.002 -->
<!-- AFFECTS: ECON.006.004, ECON.009.222 -->
<!-- END:ECON.007.003.001.TABLE.pair_effect -->

---

# 9. End‑to‑End Operational Flows

<!-- BEGIN:ECON.009.201.001.FLOW.trade_close_detect -->
- **9.201 (EA)** Detect trade **close**; capture open/close UTC, prices, initial SL/TP, lots, symbol (@ECON.017.002). Append ACK to `trade_results.csv` (atomic, append, UTC) (@ECON.002.002, @ECON.017.002).
<!-- DEPS: ECON.002.002, ECON.017.002 -->
<!-- AFFECTS: ECON.009.210 -->
<!-- END:ECON.009.201.001.FLOW.trade_close_detect -->

<!-- BEGIN:ECON.009.213.001.FLOW.hybrid_id_compose -->
- **9.213 (PY)** Compose **HybridID** = `[CAL8|00000000]-[GEN]-[SIG]-[DUR]-[OUT]-[PROX]-[SYMBOL]` (@ECON.003.004).
<!-- DEPS: ECON.003.004, ECON.009.210, ECON.009.211, ECON.009.212 -->
<!-- AFFECTS: ECON.009.220 -->
<!-- END:ECON.009.213.001.FLOW.hybrid_id_compose -->

---

# 14. Monitoring & Telemetry

<!-- BEGIN:ECON.014.002.001.ALERT.coverage_thresholds -->
#### Coverage Alert Thresholds
- *Warn:* fallback_rate ≥ 5% for 5 consecutive minutes **or** conflict_rate ≥ 2% over last 100 decisions.
- *Page:* fallback_rate ≥ 15% for 3 consecutive minutes **or** p99_latency_ms > 2000 for 5 minutes.
- *Info:* socket_uptime_pct or csv_uptime_pct drops below 99.5% rolling 1h.
<!-- DEPS: ECON.005.008, ECON.002.008 -->
<!-- AFFECTS: ECON.015.001, ECON.018.001 -->
<!-- END:ECON.014.002.001.ALERT.coverage_thresholds -->

---

# 20. Appendices

<!-- BEGIN:ECON.020.001.001.EXAMPLE.hybrid_ids -->
## 20.1 Example Hybrid IDs
- `AUSHNF10-O-ECO_HIGH_USD-FL-O4-IM-EURUSD`
- `EGBHCP10-R1-ANTICIPATION_1HR_GBP-NA-O3-SH-GBPUSD`
- `00000000-O-VOLATILITY_SPIKE-FL-O6-EX-USDJPY`
<!-- DEPS: ECON.003.004 -->
<!-- AFFECTS: None -->
<!-- END:ECON.020.001.001.EXAMPLE.hybrid_ids -->

<!-- BEGIN:ECON.020.005.001.REQ.invariants_checklist -->
## 20.5 Invariants Checklist
- R2 lot ≤ R1 lot ≤ O lot after overlays.
- Cooldown `CD` always widens stops vs `IM` for same family.
<!-- DEPS: ECON.005.006, ECON.006.004 -->
<!-- AFFECTS: ECON.013.002 -->
<!-- END:ECON.020.005.001.REQ.invariants_checklist -->


---
<!-- BEGIN:ECON.APPEND.2025-09-05 22:07:05 -->

### Appended Gap-Closure Blocks

<!-- BEGIN:ECON.003.001.001.DEF.addressing_scheme -->
**Addressing Scheme (Canonical)**
- Grammar: `[DOC].[MAJOR].[MINOR].[PATCH].[TYPE].[ITEM_ID]`
- Example IDs:
  - `ECON.004.002.001.TABLE.calendar_events`
  - `ECON.007.003.002.ACCEPTANCE.pair_effect_integrity`
- TYPE ∈ { DEF, REQ, TABLE, FLOW, ALERT, ARCH, CTRL, EXAMPLE, ACCEPTANCE }
- ITEM_ID: lowercase snake_case

**Rules**
1. IDs are immutable once published (only PATCH increments).
2. Every BEGIN must have matching END with the same ID.
3. Every block MUST include `DEPS:` and `AFFECTS:` metadata (may be empty).

<!-- DEPS:  -->
<!-- AFFECTS: ECON.*** -->
<!-- END:ECON.003.001.001.DEF.addressing_scheme -->

---

<!-- BEGIN:ECON.003.005.001.DEF.enum_registry -->
**Enum Registry (Single Source of Truth)**

```yaml
impact:
  canonical: [High, Medium]
  aliases:
    H: High
    M: Medium

proximity:
  canonical: [IM, SH, MD, LG, EX, CD]   # Immediate, Short, Medium, Long, Extended, Cooldown
  descriptions:
    IM: "Event window ±0–5m"
    SH: "±5–30m"
    MD: "±30–120m"
    LG: "±2–8h"
    EX: "±8–24h"
    CD: "24h+ post-event stabilization"

duration:
  canonical: [FL, QK, MD, LG, EX, NA]   # Flash, Quick, Medium, Long, Extended, NotApplicable

outcome:
  canonical: [O1, O2, O3, O4, O5, O6]
  descriptions:
    O1: "Max loss"
    O2: "Half loss"
    O3: "Scratch/neutral"
    O4: "Half gain"
    O5: "Max gain"
    O6: "Extended gain (trail)"

event_type:
  canonical: [NF, CP, RD, PM, GDP, CPI, NFP, RATE, PMI, RETAIL, EMP, CB]
  notes: "Extend as needed; ensure CSV/DB/code share this source."

bias:
  canonical: [Long, Short, Neutral]

symbol:
  canonical: "Configured currency pairs universe, e.g., [EURUSD, GBPUSD, USDJPY, ...]"
```

**Contract**
- CSVs and DB constraints MUST use the canonical values.
- Aliases may appear in rendering but must map to canonical on write.

<!-- DEPS: ECON.003.001.001.DEF.addressing_scheme -->
<!-- AFFECTS: ECON.007.002.*, ECON.007.003.*, ECON.020.002.* -->
<!-- END:ECON.003.005.001.DEF.enum_registry -->

---

<!-- BEGIN:ECON.002.005.001.REQ.csv_dialect -->
**CSV Dialect & Timestamp Contract**
- delimiter: `,`
- quoting: `minimal`
- newline: `LF` (\n)
- encoding: `UTF-8`
- decimal: `.`
- timestamps: ISO-8601 UTC `YYYY-MM-DDTHH:MM:SSZ`
- required meta fields for all artifacts: `file_seq` (uint, monotonic per artifact), `created_at_utc` (UTC), `checksum_sha256` (lowercase hex)

<!-- DEPS:  -->
<!-- AFFECTS: ECON.002.002.*, ECON.020.002.* -->
<!-- END:ECON.002.005.001.REQ.csv_dialect -->

---

<!-- BEGIN:ECON.002.002.002.TABLE.health_metrics -->
**health_metrics.csv — Schema**
| column             | type      | unit/format           | constraints                                  | description |
|--------------------|-----------|-----------------------|----------------------------------------------|-------------|
| ts_utc             | TIMESTAMP | ISO-8601 UTC          | NOT NULL                                     | Metric time |
| ea_bridge_connected| BOOLEAN   |                       | NOT NULL                                     | EA bridge connectivity |
| csv_uptime_pct     | REAL      | % (0–100)             | 0 ≤ v ≤ 100                                  | CSV writer uptime |
| socket_uptime_pct  | REAL      | % (0–100)             | 0 ≤ v ≤ 100                                  | Socket uptime |
| p99_latency_ms     | INTEGER   | ms                    | v ≥ 0                                        | End-to-end ingest p99 |
| fallback_rate      | REAL      | % (0–100)             | 0 ≤ v ≤ 100                                  | Fraction of ops in fallback mode |
| conflict_rate      | REAL      | % (0–100)             | 0 ≤ v ≤ 100                                  | File/seq conflicts per hour |
| file_seq           | INTEGER   |                       | NOT NULL, monotonic                          | Artifact sequence counter |
| created_at_utc     | TIMESTAMP | ISO-8601 UTC          | NOT NULL                                     | Row creation time |
| checksum_sha256    | TEXT      | lowercase hex         | NOT NULL, len=64                             | Row checksum |

**Indexes**
- `(ts_utc)`
- `(file_seq)` unique

<!-- DEPS: ECON.002.005.001.REQ.csv_dialect -->
<!-- AFFECTS: ECON.002.007.*, ECON.020.002.* -->
<!-- END:ECON.002.002.002.TABLE.health_metrics -->

---

<!-- BEGIN:ECON.002.006.001.ACCEPTANCE.atomic_write -->
**Acceptance — Atomic CSV Write**
- Writer MUST:
  1) Write to `*.tmp`
  2) fsync()
  3) Atomic rename to final path
- Reader MUST:
  - Ignore files with missing/invalid `checksum_sha256`.
  - Ignore rows with `file_seq` ≤ last processed `file_seq`.
  - Fail closed on malformed timestamps (not `...Z`).
- Tests:
  - Simulate power loss before/after rename.
  - Corrupt checksum → reader discards.
  - Non-monotonic `file_seq` → reader ignores.

<!-- DEPS: ECON.002.005.001.REQ.csv_dialect -->
<!-- AFFECTS: ECON.020.002.* -->
<!-- END:ECON.002.006.001.ACCEPTANCE.atomic_write -->

---

<!-- BEGIN:ECON.002.007.001.ACCEPTANCE.skew_rules -->
**Acceptance — Time Skew & Degraded Mode**
- Broker vs system UTC skew:
  - |skew| ≤ 1s: NORMAL
  - 1s < |skew| ≤ 5s: WARN → write `health_metrics.csv` with elevated `p99_latency_ms`
  - |skew| > 5s or monotonic clock violation: DEGRADED
- In DEGRADED:
  - Halt new trade signals
  - Continue ingest with `fallback_rate` increment
  - Emit runtime health signal: `runtime.skew.degraded=true`

**Tests**
- Inject 6s positive skew → system transitions to DEGRADED and writes metrics row.
- Restore skew → system returns to NORMAL and logs recovery.

<!-- DEPS: ECON.002.002.002.TABLE.health_metrics -->
<!-- AFFECTS: ECON.014.*, ECON.020.002.* -->
<!-- END:ECON.002.007.001.ACCEPTANCE.skew_rules -->

---

<!-- BEGIN:ECON.002.008.001.REQ.runtime_health_signals -->
**Runtime Health Signals (for Alerts)**
- `runtime.skew.degraded` ∈ {true,false}
- `runtime.csv.writer_uptime_pct` ∈ [0,100]
- `runtime.socket.uptime_pct` ∈ [0,100]
- `runtime.ea_bridge.connected` ∈ {true,false}
- `runtime.conflict.rate` per hour

**Emission**
- Signals derived from `health_metrics.csv` at least once per minute.

<!-- DEPS: ECON.002.002.002.TABLE.health_metrics -->
<!-- AFFECTS: ECON.015.*, ECON.016.* -->
<!-- END:ECON.002.008.001.REQ.runtime_health_signals -->

---

<!-- BEGIN:ECON.003.006.001.ACCEPTANCE.hybrid_id_valid -->
**Acceptance — HybridID Validation**
- Pattern (PCRE): `^(?P<SIG>[A-Z0-9_]+)\.(?P<SYMBOL>[A-Z]{3,6})\.(?P<DUR>FL|QK|MD|LG|EX|NA)\.(?P<OUT>O[1-6])\.(?P<PROX>IM|SH|MD|LG|EX|CD)$`
- Constraints:
  - `SIG` ∈ configured signal set
  - `SYMBOL` ∈ enum `symbol`
  - `DUR`, `OUT`, `PROX` ∈ enum registry

**Tests**
- Valid: `RSI_BREAKOUT.EURUSD.MD.O4.SH`
- Invalid: wrong prox `ZZ` → reject

<!-- DEPS: ECON.003.005.001.DEF.enum_registry -->
<!-- AFFECTS: ECON.020.002.* -->
<!-- END:ECON.003.006.001.ACCEPTANCE.hybrid_id_valid -->

---

<!-- BEGIN:ECON.007.002.002.ACCEPTANCE.calendar_events_integrity -->
**Acceptance — calendar_events Integrity**
- `cal8` is unique per event; parseable; `impact` ∈ enum impact
- `event_time_utc` parseable ISO-8601 UTC
- Foreign key to `event_type` ∈ enum registry

**Tests**
- Row with `impact='H'` maps to `High` and passes.
- Row with `impact='Low'` fails (not in enum).

<!-- DEPS: ECON.003.005.001.DEF.enum_registry -->
<!-- AFFECTS: ECON.007.003.* -->
<!-- END:ECON.007.002.002.ACCEPTANCE.calendar_events_integrity -->

---

<!-- BEGIN:ECON.007.003.002.ACCEPTANCE.pair_effect_integrity -->
**Acceptance — pair_effect Integrity**
- Unique (`symbol`,`cal8`)
- `bias` ∈ enum bias
- `exposure_cap_pct` ∈ [0,100]

**Tests**
- Duplicate (`EURUSD`,`20250131...`) rejected.
- `exposure_cap_pct=150` rejected.

<!-- DEPS: ECON.003.005.001.DEF.enum_registry -->
<!-- AFFECTS: ECON.014.* -->
<!-- END:ECON.007.003.002.ACCEPTANCE.pair_effect_integrity -->

---

<!-- BEGIN:ECON.020.002.001.EXAMPLE.csv_rows -->
**Canonical CSV Row Examples**

*calendar_events.csv*
```csv
file_seq,created_at_utc,checksum_sha256,cal8,event_time_utc,event_type,impact,title
1,2025-01-31T12:00:00Z,5c3b...e1,20250131_US_CPI_H,2025-01-31T13:30:00Z,CPI,High,US CPI (YoY)
```

*pair_effect.csv*
```csv
file_seq,created_at_utc,checksum_sha256,symbol,cal8,bias,exposure_cap_pct
42,2025-01-31T12:05:00Z,ab19...77,EURUSD,20250131_US_CPI_H,Long,15.0
```

*trade_results.csv*
```csv
file_seq,created_at_utc,checksum_sha256,hybrid_id,order_id,pl_pips,closed_at_utc
77,2025-01-31T15:00:00Z,9f0a...cc,RSI_BREAKOUT.EURUSD.MD.O4.SH,1002345,18.4,2025-01-31T14:59:58Z
```

*health_metrics.csv*
```csv
file_seq,created_at_utc,checksum_sha256,ts_utc,ea_bridge_connected,csv_uptime_pct,socket_uptime_pct,p99_latency_ms,fallback_rate,conflict_rate
9,2025-01-31T12:10:00Z,7d1e...aa,2025-01-31T12:10:00Z,true,99.9,99.5,210,0.0,0.0
```
<!-- DEPS: ECON.002.005.001.REQ.csv_dialect, ECON.002.002.002.TABLE.health_metrics -->
<!-- AFFECTS: ECON.020.*** -->
<!-- END:ECON.020.002.001.EXAMPLE.csv_rows -->

<!-- END:ECON.APPEND.2025-09-05 22:07:05 -->


<!-- BEGIN:ECON.005.003.001.DEF.placeholder_crossref -->
**Placeholder Section for ECON.005.003**
This stub satisfies cross-reference resolution and should be replaced with the real content.
<!-- DEPS:  -->
<!-- AFFECTS:  -->
<!-- END:ECON.005.003.001.DEF.placeholder_crossref -->

<!-- BEGIN:ECON.017.002.001.DEF.placeholder_crossref -->
**Placeholder Section for ECON.017.002**
This stub satisfies cross-reference resolution and should be replaced with the real content.
<!-- DEPS:  -->
<!-- AFFECTS:  -->
<!-- END:ECON.017.002.001.DEF.placeholder_crossref -->

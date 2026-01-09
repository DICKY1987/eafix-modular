---
doc_id: DOC-LEGACY-0051
---

# Economic Calendar — Ingest & Transform

**Status:** Updated • **Goal:** Robust weekly intake → normalized events → active signals with revisions and proximity. (Master §4.1–§4.14, §9.100) fileciteturn2file0

## 1. Acquisition & Discovery
- Weekly scheduler: **Sunday 12:00 America/Chicago** (17:00/18:00 UTC DST‑aware).  
- Discover latest vendor CSV via prioritized patterns; newest by **mtime** wins; emit health metric if none. (Master §4.11) fileciteturn2file0

## 2. Parsing (Tolerant)
- Flexible column mapping (Title/Event/Name; Country/Currency; Date/Day; Time/Hour; Impact/Importance).  
- Rows scored by **quality (0–100)**; drop sub‑threshold. (Master §4.11) fileciteturn2file0

## 3. Normalization & IDs
- Standardize country/ccy; normalize impact to High/Medium; assign **CAL8/CAL5**; revision bumps increment **F**. (Master §3.2–§3.4, §4.4, §4.8) fileciteturn2file0

## 4. Anticipation & Proximity
- Generate anticipation events (default **1,2,4,8,12h**).  
- Event‑type proximity buckets: `IM, SH, LG, EX`; post‑event **CD** cooldown. (Master §4.5–§4.6) fileciteturn2file0

## 5. Debounce & Min‑Gap
Suppress clustered duplicates by per‑family **min‑gap**; coalesce identical `(symbol, cal8, signal_type, state)` within debounce. (Master §4.14, §9.108) fileciteturn2file0

## 6. Persistence & Hydration
Transactional **UPSERT** into `calendar_events`; restart hydration rebuilds active set for states `{ANT_8H, ANT_1H, ACTIVE, COOLDOWN}`. (Master §4.9, §4.13) fileciteturn2file0

## 7. Export
Emit `active_calendar_signals.csv` atomically with `file_seq` and **checksum_sha256**. (Master §2.2–§2.3) fileciteturn2file0

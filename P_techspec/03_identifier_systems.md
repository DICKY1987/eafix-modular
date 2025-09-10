# Identifier Systems (Standardization)

**Status:** Updated • **Scope:** Canonical IDs used across Calendar → Matrix → Re‑Entry → EA flows.

## 1. Rationale
Earlier coarse IDs conflated distinct event types and complicated learning. We standardize on **CAL8** with **CAL5** for backward compatibility and introduce **Hybrid ID** as the primary context key. (Aligned with master spec §3.1–§3.6) fileciteturn2file0

## 2. CAL8 (Extended Calendar Identifier)
**Format:** `R(1) C(2) I(1) E(2) V(1) F(1)` → 8 characters total  
- **R:** Region (A=Americas, E=Europe, P=APAC)  
- **C:** Country/Currency (US, EU, GB, JP, …)  
- **I:** Impact (H=High, M=Med)  
- **E:** Event type (NF, CP, RD, PM, …)  
- **V:** Ingest schema rev (1..9)  
- **F:** Revision sequence (0=no revision, 1..9 for reschedules/revisions)  
**Examples:** `AUSHNF10`, `EGBMCP10`. (Master §3.2) fileciteturn2file0

## 3. CAL5 (Legacy Alias)
A 5‑digit Region+Country+Impact code retained for continuity; always store **both** CAL8 and CAL5. (Master §3.3) fileciteturn2file0

## 4. Hybrid ID (Primary Context Key)
**Format:** `[CAL8|00000000]-[GEN]-[SIG]-[DUR]-[OUT]-[PROX]-[SYMBOL]`  
- **GEN:** `O|R1|R2`  
- **SIG:** Signal family (e.g., `ECO_HIGH_USD`, `ANTICIPATION_1HR_GBP`)  
- **DUR:** `FL|QK|MD|LG|EX|NA`  
- **OUT:** `O1..O6` (outcome buckets)  
- **PROX:** `IM|SH|LG|EX|CD`  
**Example:** `AUSHNF10-O-ECO_HIGH_USD-FL-O4-IM-EURUSD`. (Master §3.4, §5.3–§5.5) fileciteturn2file0

## 5. Signal Taxonomy & Composition
Signal families and weights are standardized. Prefer **score‑based composition** and a small **blocklist** of hard conflicts. (Master §3.5–§3.6) fileciteturn2file0

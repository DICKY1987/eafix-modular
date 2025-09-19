# Signal Model & Matrix Mapping

**Status:** Updated • **Goal:** Deterministic lookup from Hybrid context → ParameterSet with auditable fallbacks. (Master §3.5–§3.6, §5.1–§5.10, §6.8) fileciteturn2file0

## 1. Dimensions & Taxonomy
- **SignalType, Outcome (O1..O6), Duration (FL/QK/MD/LG/EX/NA), Proximity (IM/SH/LG/EX/CD), Generation (O/R1/R2)**. (Master §5.1–§5.6) fileciteturn2file0

## 2. Composition Policy
Score‑based composition with family weights; maintain a conflict blocklist for known exclusives. (Master §3.6) fileciteturn2file0

## 3. Parameter Resolution (Tiered)
Tier‑0 exact → Tier‑1 (drop DUR) → Tier‑2 (drop PROX) → Tier‑3 (calendar only) → Tier‑4 (global safe default). Log `resolved_tier` to **mapping_audit**. (Master §5.8–§5.9, §6.8) fileciteturn2file0

## 4. Audit & Coverage
- Append mapping changes with before/after + actor + reason.  
- Emit coverage % and fallback rate to metrics. (Master §5.9, §14.1–§14.2) fileciteturn2file0

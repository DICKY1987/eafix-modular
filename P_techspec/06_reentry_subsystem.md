# Re‑Entry Subsystem

**Status:** Updated • **Goal:** Classify outcomes and issue governed follow‑ups with overlays and generation limits. (Master §6.*, §9.200) fileciteturn2file0

## 1. Responsibilities & Inputs/Outputs
On trade close, classify Outcome/Duration → build Hybrid ID → resolve ParameterSet (+ overlays) → emit decision (**O→R1→R2** max). (Master §6.1–§6.6, §9.200) fileciteturn2file0

## 2. Overlay Precedence (Top‑Wins)
1) **PairEffect** → 2) **Broker Constraints** → 3) **Risk Overlay** → 4) **Strategy/Matrix Defaults** → 5) **Global Fallbacks**. Prefer stricter risk stance on ties. (Master §6.4) fileciteturn2file0

## 3. Risk Score → Parameter Bins
Compute risk score (0–100) from WinRate/ProfitFactor/DD/Recency; map to Conservative/Moderate/Aggressive/Max bins. (Master §6.X Risk & Performance) fileciteturn2file0

## 4. Ledger & Limits
Per‑chain **Re‑Entry Ledger** enforces `O → R1 → R2` cap; prevents bypass. (Master §6.5) fileciteturn2file0

## 5. Circuit Breakers
Daily loss/equity floor/consecutive errors/concentration/market state; actions: pause, flatten, cancel, escalate. (Master §6.7, §7.y) fileciteturn2file0

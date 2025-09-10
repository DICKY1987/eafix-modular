# Risk & Portfolio Controls

**Status:** Updated • **Goal:** Bound exposure at symbol and portfolio levels with automatic brakes and overlays.

## 1. Per‑Symbol Limits
- Max concurrent positions, per‑symbol daily loss, max leverage, min SL distance (broker‑aware).

## 2. Portfolio Controls
- Max total exposure (notional/% equity), asset/ccy concentration caps, correlated basket caps.

## 3. Performance‑Aware Overlays
- Risk score (0–100) → bins (Conservative/Moderate/Aggressive/Max) scaling lots/SL/TP.
- Automatic derate on drawdown, breaker triggers, or mapping fallback rates rising.

## 4. Circuit Breakers
- Triggers: daily loss, equity floor, consecutive errors, integrity failures, broker skew.
- Actions: pause decisions, flatten positions, cancel pending orders, escalate alert.

## 5. Governance
- Append‑only **Risk Decisions Log** with actor/reason.
- Change control requires linked acceptance evidence and sign‑off.

## 6. EA Enforcement
- Pre‑flight checks gate order send; mismatch or breaker → no trade and alert.

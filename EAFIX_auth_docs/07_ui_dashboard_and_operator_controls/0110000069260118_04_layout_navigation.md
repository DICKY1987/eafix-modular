---
doc_id: DOC-LEGACY-0050
---

# GUI Layout & Navigation

**Status:** Updated • **Goal:** Minimal, operator‑first layout aligned to contracts and health telemetry.

## 1. Global Layout
- **Top Nav**: Signals • History • System Status • Config • Diagnostics
- **Left Rail (contextual)**: filters & quick actions
- **Main Grid**: responsive cards (2xl rounded, soft shadows), keyboard shortcuts (Ctrl+F focus filter)

## 2. Navigation Rules
- ESC closes modals; CTRL+/ opens command palette with actions (Reload CSV, Run Socket Test, Export Logs).
- Deep‑linkable views with `?tab=signals&symbol=EURUSD&cal8=AUSHNF10`.

## 3. Placement Standards
- System Status is first‑class and always visible in the nav.
- **Currency Strength UI is excluded** from this layout by design.

## 4. Accessibility & Ops
- Color‑agnostic signaling (icons + text); large hit targets; latency badges on tiles.

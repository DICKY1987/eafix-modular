---
doc_id: DOC-CONFIG-0102
---

Dde + Currency Strength Tab — Brainstorm Spec
DDE + Currency Strength Tab — Brainstorm Spec

This spec turns your two mockups (DDE price feed + Currency Strength Indicator on one tab) into a concrete, buildable plan. It also generalizes the pattern so subsequent Indicator tabs reuse the same visual grammar.

1) Goals

Single-glance situational awareness: live quotes, spreads, and connection health next to a compact currency-strength heatmap.

Multi‑timeframe clarity: switch TFs fast; per‑TF strength and recent change visible.

Low‑latency & readable: color encodings, subtle motion (sparklines), and clear alerts without visual noise.

Reusable shell: the same tab skeleton powers “other indicators” (MACD, RSI, ATR, etc.).

2) High‑Level Layout (Grid)
┌────────────────────────────────────────────────────────────────────────────┐
│ Header: [Conn Status] [Broker/Account] [Latency] [Last Sync] [Refresh TFs] │
├────────────────────────────────────────────────────────────────────────────┤
│ Left Column (DDE)                         │ Right Column (Currency Strength)│
│ ┌───────────────────────────────────────┐ │ ┌──────────────────────────────┐ │
│ │ DDE Live Ticker Table                │ │ │ TF Switcher: M1 M5 M15 M30 H1 │ │
│ │  • Symbol  • Bid  • Ask  • Spread   │ │ │            H4 D1 W1           │ │
│ │  • ΔPips   • Δ%   • Vol   • Status  │ │ ├──────────────────────────────┤ │
│ │  • Latency badge (ms)               │ │ │ Heatmap (Currency x Currency) │ │
│ └───────────────────────────────────────┘ │ │  • Cell = strength A→B        │ │
│ ┌───────────────────────────────────────┐ │ │  • Arrows for recent change   │ │
│ │ Mini‑Sparklines per symbol (1xN)    │ │ └──────────────────────────────┘ │
│ │  • last N bars of M5                 │ │ ┌──────────────────────────────┐ │
│ └───────────────────────────────────────┘ │ │ Per‑Currency strength bars    │ │
│                                           │ │  • USD, EUR, GBP, JPY, ...    │ │
│                                           │ └──────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────┤
│ Footer: [Filter: majors/exotics] [Alert rules] [Export] [Open full chart]   │
└────────────────────────────────────────────────────────────────────────────┘

Why this works

DDE table is dense but scannable; latencies/spreads trigger attention.

Heatmap exposes relative strength and pair direction at once.

TF switcher modifies all right‑column visuals for consistent context.

3) Visual Encodings
DDE Table (Left)

Row = Symbol (EURUSD, GBPUSD, …)

Columns:

Bid/Ask: numeric, right‑aligned; recent change flash (fade over 500ms).

Spread: colored bar (green < 1 pip, amber 1–2, red > 2; thresholds configurable).

ΔPips / Δ%: small chip with up/down arrow; background weak green/red.

Volume: sparkline (last N ticks) as a tiny inline glyph.

Latency: badge (ms); red > 250ms, amber 150–250, green < 150.

Status: icon (✔ live, ! stale, × disconnected).

Currency Strength (Right)

TF Switcher: segmented buttons; active TF is highlighted.

Heatmap (NxN without diagonal): cell(i,j) shows strength of base i vs quote j.

Color: green = i strong vs j, red = weak, yellow = neutral.

Intensity = |z‑score| or normalized momentum in active TF.

Tiny overlay arrow shows recent delta (↑ stronger, ↓ weaker; fade in/out on change).

Per‑Currency Bars: Each currency gets an aggregate strength bar (−100..+100), stacked green/red around a neutral midline.

4) Interactions

Hover a heatmap cell → tooltip: EUR→USD: +38 (M15) • Δ+6 in last 5m + mini‑sparkline.

Click a cell → focus that pair across the app (route to chart, open symbol details, or pin in a mini‑panel).

Ctrl+Click multiple cells → compare panel (side drawer) with deltas and spreads.

Right‑click rows/cells → context menu: create alert, open depth of market, copy symbol.

Filter chips (footer): Majors / Minors / Exotics toggle, plus broker‑available only.

5) Data Model & Update Flow
Sources

DDE feed → symbols: bid/ask, last price, tick ts, volume; heartbeat for latency.

Strength engine (in your microservices): per TF currency scores and pair deltas.

Client‑side cache
{
  "dde": {
    "EURUSD": {"bid":1.08643,"ask":1.08647,"spread":0.4,"last":1.08645,
                "delta_pips": 2.6, "delta_pct": 0.12, "volume": [..], "latency_ms": 72,
                "updated_at": 1695153032}
  },
  "strength": {
    "TF":"M15",
    "currency_score": {"USD": +42, "EUR": -15, ...},
    "pair_matrix": {"EUR":{"USD": -38, "GBP": +12, ...}, ...},
    "pair_delta_5m": {"EURUSD": +6, ...}
  }
}
Update cadence

DDE table: per tick (throttle paints to 10–20 Hz max; aggregate changes per frame).

Strength: per bar close or rolling calculation (e.g., every 5s for M1/M5; 30–60s for M15+).

6) Scoring & Normalization (Currency Strength)

Compute per‑currency score as weighted sum across its major pairs in TF:

For currency C, score = Σ zscore(returns(C/X)) + Σ −zscore(returns(X/C)) over selected X.

Normalize to [−100, +100].

Pair cell(i,j) = score(i) − score(j).

Recent change arrow = sign of Δ cell(i,j) over the last short window (e.g., 5m), magnitude mapped to arrow thickness/length.

7) Alerting (optional but useful)

Spread spike: when spread > threshold for N seconds.

Strength crossover: currency score crosses ±K.

Pair dominance: cell(i,j) exceeds ±T and rising.

Staleness: DDE latency > L or no tick in N seconds.

Alerts appear as small badges in the header and as row/cell pills. Clicking opens the alert rule; Alt+Click silences.

8) Componentization (PyQt6)

DDETableWidget — virtualized QTableView for large symbol lists; custom delegate paints spread bars and latency badges.

StrengthHeatmapWidget — QWidget with custom paint for NxN grid; supports hover and click hit‑testing; per‑cell animation layer for arrows.

CurrencyBarsWidget — horizontal bar list (USD, EUR, ...); smooth transitions.

TFSwitcher — QButtonGroup of QPushButtons.

OverviewTab — puts it all together with a responsive QGridLayout.

Signals/slots

OverviewTab.setData(dde_snapshot, strength_snapshot) → diff + repaint.

onCellClicked(base, quote) → emits pairSelected(base+quote) to the app.

9) Performance & UX Notes

Throttle paints (QTimer 50–100ms); coalesce updates.

Use QAbstractTableModel + QStyledItemDelegate for DDE table to avoid per‑cell widgets.

Cache heatmap color tiles; only repaint dirty cells.

Prefer subtle fades over large animations; avoid flashing red/green.

10) Theming

Dark‑first palette. Ensure contrast for red/green vs neutral yellow.

Color‑blind safe alternate scheme: blue/orange vs gray.

Settings toggle: High contrast, Reduce motion.

11) Reusing the Pattern for Other Indicator Tabs

Each Indicator Tab reuses the same header and left column; right column changes:

RSI Tab: right panel shows multi‑TF RSI tiles per symbol, with bands (30/70) and % distance to band; aggregate per‑watchlist.

MACD Tab: heatmap becomes signal vs histogram state per pair; arrows show signal line crosses.

ATR/Vol Tab: strength bars become volatility bars; highlight elevated ATR vs baseline.

All share a common widget contract:

class IndicatorPanel(QWidget):
    def setTimeframe(self, tf: str) -> None: ...
    def setData(self, payload: dict) -> None: ...
12) Minimal Build Plan (MVP → Plus)

MVP (2–4 days of focused build)

DDETableWidget with live updates, spread & latency badges.

TFSwitcher controlling a static StrengthHeatmapWidget fed by mock data.

CurrencyBarsWidget reflecting the active heatmap TF.

PLUS (next iteration) 4. Per‑cell delta arrows with fade. 5. Hover tooltips with mini sparkline. 6. Alerts + header badges.

13) JSON Config (extensible)
{
  "tab": {
    "id": "overview",
    "title": "Overview",
    "dde": {
      "symbols": ["EURUSD","GBPUSD","USDJPY","AUDUSD"],
      "columns": ["bid","ask","spread","delta_pips","delta_pct","volume","latency","status"],
      "spread_thresholds": {"green":1.0, "amber":2.0}
    },
    "strength": {
      "currencies": ["USD","EUR","GBP","JPY","AUD","CAD","CHF","NZD"],
      "timeframes": ["M1","M5","M15","M30","H1","H4","D1"],
      "normalize_to": 100,
      "delta_window_sec": 300
    }
  }
}
14) Pseudocode Wiring (PyQt6)
class OverviewTab(QWidget):
    def __init__(self):
        ...
        self.dde = DDETableWidget()
        self.heat = StrengthHeatmapWidget()
        self.bars = CurrencyBarsWidget()
        self.tfs = TFSwitcher(["M1","M5","M15","M30","H1","H4","D1"])
        self.tfs.changed.connect(self.on_tf_changed)


    def setData(self, dde_snapshot: dict, strength_snapshot: dict):
        self.dde.update(dde_snapshot)
        if strength_snapshot["TF"] == self.tfs.active():
            self.heat.update(strength_snapshot["pair_matrix"])
            self.bars.update(strength_snapshot["currency_score"])  


    def on_tf_changed(self, tf):
        # request strength snapshot for tf from backend; update widgets on arrival
        pass
15) Open Questions

Pair universe: majors only or full broker list? (affects heatmap size)

TF calculation cadence: rolling or bar‑close only?

Backfill on app launch: how many minutes of history for sparklines?

Alert defaults: ship a sane starter set?

16) Next Steps

Confirm TF list and currency set.

Pick color scheme (standard vs color‑blind friendly).

I’ll generate a starter PyQt6 code with mock data providers for DDE and strength so you can run the MVP tab immediately, then we can wire it to your real microservices.

Love this direction. I turned your two mockups into a concrete plan you can build on. Check the canvas—there’s a document called “DDE + Currency Strength Tab — Brainstorm Spec” with:

a clean layout (DDE table on the left; currency-strength heatmap + per-currency bars on the right),

TF switcher behavior,

color/encoding rules,

interactions (hover tooltips, click-to-focus pair, alert chips),

a simple data model,

normalization math for strength,

PyQt6 component breakdown,

an MVP → Plus build plan,

and a JSON config skeleton you can feed from your services.

If you want, I can spin up a runnable PyQt6 MVP (widgets + mock providers) next so you can see it live and tweak the feel before we wire it to your real data.

You said:
Proceed
ChatGPT said:
Thought for 5s
Py Qt6 Mvp — Dde + Currency Strength Overview Tab (overview Tab
· python
from __future__ import annotations
        self.table.setAlternatingRowColors(True)


        self.heat = StrengthHeatmapWidget(CURRENCIES)
        self.bars = CurrencyBarsWidget(CURRENCIES)
        self.tf = TFSwitcher(TIMEFRAMES)
        self.tf.on_changed(self.on_tf_changed)


        # Header
        header = QHBoxLayout()
        self.lbl_status = QLabel("Conn: LIVE  •  Latency: 80ms  •  Last Sync: —")
        header.addWidget(self.lbl_status)
        header.addStretch(1)
        header.addWidget(QLabel("TF:"))
        header.addWidget(self.tf)


        # Layout
        root = QVBoxLayout(self)
        root.addLayout(header)


        grid = QGridLayout(); grid.setContentsMargins(0,0,0,0); grid.setHorizontalSpacing(12)
        grid.addWidget(self.table, 0, 0, 2, 1)
        grid.addWidget(self.heat, 0, 1)
        grid.addWidget(self.bars, 1, 1)
        root.addLayout(grid, 1)


        # Timers
        self.timer_dde = QTimer(self); self.timer_dde.timeout.connect(self._tick_dde); self.timer_dde.start(100)
        self.timer_strength = QTimer(self); self.timer_strength.timeout.connect(self._tick_strength); self.timer_strength.start(800)


        # Initial paint
        self._tick_dde(); self._tick_strength()


    def on_tf_changed(self, tf: str):
        self.strength.set_tf(tf)
        self._tick_strength()


    def _tick_dde(self):
        snapshot = self.dde.tick()
        self.model.update(snapshot)
        # fake connection label
        lat = int(sum(r.latency_ms for r in snapshot.values())/max(1,len(snapshot)))
        self.lbl_status.setText(f"Conn: LIVE  •  Latency: {lat}ms  •  Last Sync: {time.strftime('%H:%M:%S')}")


    def _tick_strength(self):
        snap = self.strength.snapshot()
        self.heat.update_matrix(snap["pair_matrix"])
        self.bars.update_scores(snap["currency_score"])




# ------------------------------
# Run demo
# ------------------------------


def run_demo():
    app = QApplication([])
    w = OverviewTab()
    w.setWindowTitle("Trading — DDE + Currency Strength (MVP)")
    w.resize(1100, 640)
    w.show()
    app.exec()




if __name__ == "__main__":
    run_demo()



Done! I dropped a runnable PyQt6 MVP in the canvas: overview_tab.py.

What’s included

DDE table (QTableView + model): symbol, bid/ask, spread, Δpips, Δ%, latency, status; updates ~10 Hz with mock ticks.

Currency strength heatmap (custom paint): NxN grid (USD, EUR, GBP, JPY, AUD, CAD, CHF, NZD), colored −100..+100.

Per-currency bars: horizontal bars centered at 0 with dynamic green/red.

TF switcher: M1…D1; switching changes the strength stream.

Header status: fake connection + average latency + last sync time.

Clean layout and throttled timers so it feels live without being noisy.

Run it
python overview_tab.py
Py Qt6 Trading Signals Dashboard Tab (dashboard Tab
· python
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import random
import time


from PyQt6.QtCore import Qt, QTimer, QRect, QSize
from PyQt6.QtGui import QColor, QBrush, QPainter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QApplication, QFrame, QSizePolicy
)


# ------------------------------
# Domain model & utilities
# ------------------------------


Signal = str  # "Strong Buy", "Weak Buy", "No Signal", "Weak Sell", "Strong Sell" or RSI: "Buy"/"Sell"


SIGNAL_SCORES: Dict[Signal, int] = {
    "Strong Buy": 2,
    "Weak Buy": 1,
    "No Signal": 0,
    "Weak Sell": -1,
    "Strong Sell": -2,
    # RSI (bullish/bearish only)
    "Buy": 1,
    "Sell": -1,
}


# Visual palette
COLORS = {
    "bull_strong": QColor(0, 160, 70),    # deeper green
    "bull_weak": QColor(120, 200, 120),   # light green
    "bear_strong": QColor(200, 60, 60),   # deep red
    "bear_weak": QColor(230, 150, 150),   # light red
    "neutral": QColor(220, 200, 60),      # yellow-ish
    "changed": QColor(255, 235, 120),     # highlight for changed cells
}


# Default indicators & timeframes
DEFAULT_INDICATORS: List[str] = [
    "RSI", "MACD", "Stochastic", "CCI", "ATR", "ADX", "EMA_Cross", "Bollinger"
]
DEFAULT_TIMEFRAMES: List[str] = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]


SHORT_TERM_SET = {"M1", "M5", "M15", "M30", "H1"}




@dataclass
class CellState:
    signal: Signal
    last_changed_ts: float = 0.0





I built you a drop-in PyQt6 widget for this: a “Signals Dashboard” tab with the matrix, summary, short/long outlook bars, auto-refresh, and change-highlighting. It’s in the canvas as a single file called DashboardTab.py (open it on the right).

What you get

Matrix: Indicators × Timeframes with color-coded cells
(green = buy, red = sell, yellow = neutral; strong vs weak shades).

Per-TF Summary: Bottom “TF Summary” row shows Buy/Sell/No Signal + confidence %.

ADX-weighted confidence: Confidence per timeframe uses an ADX multiplier (1.0–2.0 as ADX rises from ~20→60+).

Short-term & Long-term bars: Horizontal bars summarizing ≤H1 and ≥H4 outlooks.

Auto-update: Timer with adjustable seconds; “Refresh Now” button.

Signal change highlighting: Optional; recently changed cells are softly tinted.

Plug it into your app
from dashboard_tab import DashboardTab

tab = DashboardTab(
    indicators=["RSI","MACD","Stochastic","CCI","ATR","ADX","EMA_Cross","Bollinger"],
    timeframes=["M1","M5","M15","M30","H1","H4","D1"],
)
tab.set_data_provider(my_provider)  # see below
parent_tabwidget.addTab(tab, "Dashboard")

Data provider contract (your real signals go here)

Provide a callable returning (signals_map, adx_map):

def my_provider():
    # signals_map[indicator][timeframe] -> one of:
    # "Strong Buy", "Weak Buy", "No Signal", "Weak Sell", "Strong Sell"
    # RSI may return "Buy"/"Sell" only (handled automatically)
    signals_map = {
        "RSI": {"M1":"Buy","M5":"Sell", ...},
        "MACD": {"M1":"Weak Buy", ...},
        ...
    }
    # adx_map["ADX"][timeframe] -> float ADX value (e.g., 18..50)
    adx_map = {"ADX": {"M1": 24.3, "M5": 31.0, ...}}
    return signals_map, adx_map


No ADX yet? Return {"ADX": {}}—it will default to neutral weighting.

Tuning & notes

Update interval: top-left spinbox (seconds).

Highlighting: toggle on/off next to the interval.

Confidence math: each indicator contributes a score (Strong ±2, Weak ±1, No 0; RSI Buy/Sell ±1). We weight non-neutral signals with w = 1 + clamp((ADX−20)/40, 0, 1) so higher ADX increases confidence. Confidence% = abs(sum(w*score)) / (max_per_tf) * 100.

Short vs long: short-term = M1..H1; long-term = H4, D1 (easy to change: SHORT_TERM_SET).

Try the demo

You can run it standalone:

python DashboardTab.py
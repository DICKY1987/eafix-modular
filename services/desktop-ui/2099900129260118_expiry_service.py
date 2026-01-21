# doc_id: DOC-LEGACY-0067
# DOC_ID: DOC-LEGACY-0003

"""
Expiry Service (Python + FastAPI) — FX Options Expiry → MT4
- Serves expiry records and computed features as JSON or CSV
- No Excel. Local-only by default (http://127.0.0.1:5001)
Run:
  pip install fastapi uvicorn pydantic
  python expiry_service.py
Add to MT4: Tools → Options → Expert Advisors → "Allow WebRequest for listed URL"
  http://127.0.0.1:5001
"""

from __future__ import annotations
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime, timezone, timedelta
import math

app = FastAPI(title="FX Expiry Service", version="0.1.0")

# -------------------------------
# Models
# -------------------------------

class ExpiryRecord(BaseModel):
    symbol: str = Field(..., description="e.g., EURUSD, USDJPY (no slash)")
    strike: float
    ccy: str = Field(..., description="Notional currency, e.g., EUR, USD, JPY")
    notional: float = Field(..., description="Notional amount in 'ccy' units (e.g., 1.1e9)")
    size_rank: Literal["S", "M", "L", "XL"]
    expiry_ts_utc: datetime
    source_url: Optional[str] = None

    # Runtime/derived (optional)
    spot: Optional[float] = None
    distance_pips: Optional[float] = None
    pin_score: Optional[float] = None
    pre_post: Optional[Literal["PRE", "POST"]] = None


class Snapshot(BaseModel):
    symbol: str
    ts_utc: datetime
    pre_post: Literal["PRE", "POST"]
    records: List[ExpiryRecord]
    features: Dict[str, float]


class SignalState(BaseModel):
    active: bool
    context: Optional[str] = ""


class Signals(BaseModel):
    symbol: str
    ts_utc: datetime
    S1_pin_reversion: SignalState
    S2_gamma_wall_touch: SignalState
    S4_post_expiry_burst: SignalState
    S5_compression_expansion: SignalState


# -------------------------------
# In-memory store (replace with SQLite in production)
# -------------------------------

STORE: Dict[str, List[ExpiryRecord]] = {}
SPOT_CACHE: Dict[str, float] = {}
CONFIG = {
    "pin_pips_max": 22.0,
    "pin_min": 65.0,
    "wall_touch": 10.0,
    "burst_trigger_pips": 18.0,
    "burst_window_mins": 60.0,
    "comp_low": 0.5,
    "pre_window_hours": 8.0,
    "post_window_hours": 6.0,
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def pip_in_price(symbol: str, digits: Optional[int] = None) -> float:
    """
    Return 1 pip in price terms (approx). For 5-digit (EURUSD 1.23456) -> 0.0001
    For 3-digit JPY (USDJPY 156.123) -> 0.01
    If you know broker digits you can override; this is a safe general guess.
    """
    sym = symbol.upper()
    if "JPY" in sym and not sym.startswith("XAU"):  # crude but practical
        return 0.01
    return 0.0001


def pips_between(symbol: str, a: float, b: float) -> float:
    return abs(a - b) / pip_in_price(symbol)


def size_weight(size_rank: str) -> float:
    return {"S": 1.0, "M": 1.5, "L": 2.0, "XL": 2.5}.get(size_rank, 1.0)


def time_weight(expiry_ts: datetime) -> float:
    # Closer to expiry => higher weight, bounded [0.1 .. 1.5]
    hrs = max(0.0, (expiry_ts - now_utc()).total_seconds() / 3600.0)
    if hrs <= 0:
        return 0.3
    return max(0.1, min(1.5, 1.0 / (0.2 + math.log10(hrs + 1.0))))


def compute_pin_score(symbol: str, strike: float, spot: float, size_rank: str, expiry_ts: datetime) -> float:
    dist_pips = pips_between(symbol, spot, strike)
    # Proximity factor in [0..1], saturates at ~pin_pips_cap
    pin_pips_cap = 35.0
    proximity = max(0.0, 1.0 - min(1.0, dist_pips / pin_pips_cap))
    w_size = size_weight(size_rank)
    w_time = time_weight(expiry_ts)
    raw = 100.0 * proximity * (0.6 * w_size + 0.4 * w_time) / 2.5  # soft scale
    return max(0.0, min(100.0, raw))


def nearest_record(symbol: str, records: List[ExpiryRecord], spot: float) -> Optional[ExpiryRecord]:
    if not records:
        return None
    return min(records, key=lambda r: pips_between(symbol, spot, r.strike))


def ensure_demo_data() -> None:
    if STORE:
        return
    # Simple demo strikes (today expiry ~ at 15:00 UTC)
    expiry_dt = (now_utc().replace(hour=15, minute=0, second=0, microsecond=0))
    eurusd_spot = 1.0830
    usdjpy_spot = 156.90
    SPOT_CACHE["EURUSD"] = eurusd_spot
    SPOT_CACHE["USDJPY"] = usdjpy_spot
    STORE["EURUSD"] = [
        ExpiryRecord(symbol="EURUSD", strike=1.0850, ccy="EUR", notional=1.1e9, size_rank="XL",
                     expiry_ts_utc=expiry_dt, source_url="demo"),
        ExpiryRecord(symbol="EURUSD", strike=1.0800, ccy="EUR", notional=8.0e8, size_rank="L",
                     expiry_ts_utc=expiry_dt, source_url="demo"),
    ]
    STORE["USDJPY"] = [
        ExpiryRecord(symbol="USDJPY", strike=156.50, ccy="USD", notional=6.2e8, size_rank="L",
                     expiry_ts_utc=expiry_dt, source_url="demo"),
        ExpiryRecord(symbol="USDJPY", strike=157.00, ccy="USD", notional=4.0e8, size_rank="M",
                     expiry_ts_utc=expiry_dt, source_url="demo"),
    ]


def enrich(symbol: str, records: List[ExpiryRecord]) -> List[ExpiryRecord]:
    spot = SPOT_CACHE.get(symbol.upper(), None)
    if spot is None:
        # In production, query your price feed here.
        # Fallback to last strike mean to keep charts alive.
        if records:
            spot = sum(r.strike for r in records) / float(len(records))
        else:
            spot = 1.0
    out = []
    for r in records:
        r2 = r.copy()
        r2.spot = float(spot)
        r2.distance_pips = round(pips_between(symbol, r2.spot, r2.strike), 1)
        r2.pin_score = round(compute_pin_score(symbol, r2.strike, r2.spot, r2.size_rank, r2.expiry_ts_utc), 1)
        r2.pre_post = "PRE" if now_utc() < r2.expiry_ts_utc else "POST"
        out.append(r2)
    return out


def compression_ratio_stub(symbol: str) -> float:
    # Replace with real RV calc. < 0.5 means compression.
    return 0.45


# -------------------------------
# API
# -------------------------------

@app.get("/health")
def health() -> Dict[str, object]:
    ensure_demo_data()
    return {"ok": True, "ts": now_utc().isoformat(), "symbols": list(STORE.keys())}


@app.get("/spot")
def set_spot(symbol: str = Query(...), price: float = Query(...)) -> Dict[str, object]:
    """
    Simple spot setter to simulate a live feed (optional).
    Example:
      GET /spot?symbol=EURUSD&price=1.0832
    """
    SPOT_CACHE[symbol.upper()] = float(price)
    return {"ok": True, "symbol": symbol.upper(), "spot": float(price)}


@app.get("/expiries", response_model=Snapshot)
def expiries(symbol: str = Query(...)) -> Snapshot:
    ensure_demo_data()
    sym = symbol.upper().replace("/", "")
    records = enrich(sym, STORE.get(sym, []))
    pre_post = "PRE"
    if any(r.pre_post == "POST" for r in records):
        pre_post = "POST"
    features = {}
    nr = nearest_record(sym, records, records[0].spot if records else 0.0)
    if nr:
        features["nearest_strike"] = nr.strike
        features["distance_pips"] = nr.distance_pips or 0.0
        features["pin_pressure"] = nr.pin_score or 0.0
    features["compression_ratio"] = compression_ratio_stub(sym)
    return Snapshot(symbol=sym, ts_utc=now_utc(), pre_post=pre_post, records=records, features=features)


@app.get("/expiries.csv")
def expiries_csv(symbol: str = Query(...)) -> str:
    snap = expiries(symbol)  # reuse logic
    lines = [
        "symbol,strike,ccy,notional,size_rank,expiry_ts_utc,spot,distance_pips,pin_score,pre_post"
    ]
    for r in snap.records:
        lines.append(",".join([
            r.symbol,
            f"{r.strike}",
            r.ccy,
            f"{int(r.notional)}",
            r.size_rank,
            r.expiry_ts_utc.isoformat(),
            f"{r.spot if r.spot is not None else ''}",
            f"{r.distance_pips if r.distance_pips is not None else ''}",
            f"{r.pin_score if r.pin_score is not None else ''}",
            r.pre_post or ""
        ]))
    return "\n".join(lines)


@app.get("/signals", response_model=Signals)
def signals(symbol: str = Query(...)) -> Signals:
    snap = expiries(symbol)
    sym = snap.symbol
    features = snap.features
    pre_post = snap.pre_post

    pin_min = CONFIG["pin_min"]
    pin_pips_max = CONFIG["pin_pips_max"]
    wall_touch = CONFIG["wall_touch"]
    burst_trigger_pips = CONFIG["burst_trigger_pips"]
    comp_low = CONFIG["comp_low"]

    # Defaults
    s1 = SignalState(active=False)
    s2 = SignalState(active=False)
    s4 = SignalState(active=False)
    s5 = SignalState(active=False)

    # Nearest
    nearest = None
    if snap.records:
        spot = snap.records[0].spot or 0.0
        nearest = nearest_record(sym, snap.records, spot)

    # S1: Pin Reversion (PRE)
    if pre_post == "PRE" and nearest:
        if (nearest.pin_score or 0.0) >= pin_min and (nearest.distance_pips or 1e9) <= pin_pips_max:
            s1 = SignalState(active=True, context=f"pin={nearest.pin_score} dist={nearest.distance_pips}")

    # S2: Gamma Wall Touch (PRE, big size + close)
    if pre_post == "PRE" and nearest:
        if nearest.size_rank in ("L", "XL") and (nearest.distance_pips or 1e9) <= wall_touch:
            s2 = SignalState(active=True, context=f"{nearest.size_rank}@{nearest.strike} dist={nearest.distance_pips}")

    # S4: Post-Expiry Burst (POST)
    if pre_post == "POST" and nearest:
        # naive: if distance grew beyond burst_trigger_pips after POST
        if (nearest.distance_pips or 0.0) >= burst_trigger_pips:
            s4 = SignalState(active=True, context=f"escape={nearest.distance_pips}p")

    # S5: Compression→Expansion
    cr = features.get("compression_ratio", 1.0)
    if cr <= comp_low and pre_post == "POST":
        s5 = SignalState(active=True, context=f"CR={cr}")

    return Signals(
        symbol=sym, ts_utc=now_utc(),
        S1_pin_reversion=s1,
        S2_gamma_wall_touch=s2,
        S4_post_expiry_burst=s4,
        S5_compression_expansion=s5
    )


if __name__ == "__main__":
    import uvicorn
    print("Starting on http://127.0.0.1:5001 ...")
    uvicorn.run("expiry_service:app", host="127.0.0.1", port=5001, reload=False)

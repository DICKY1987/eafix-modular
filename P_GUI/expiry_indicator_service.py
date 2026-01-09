# DOC_ID: DOC-LEGACY-0002
"""
Expiry Indicator Service (Python + FastAPI) — FX Options Expiry Indicators
- Serves expiry records and computed indicator states as JSON or CSV
- Pure indicator service - provides signal states without execution logic
- No Excel. Local-only by default (http://127.0.0.1:5001)

Run:
  pip install fastapi uvicorn pydantic
  python expiry_indicator_service.py

Add to MT4: Tools → Options → Expert Advisors → "Allow WebRequest for listed URL"
  http://127.0.0.1:5001
"""

from __future__ import annotations
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime, timezone, timedelta
import math

app = FastAPI(title="FX Expiry Indicator Service", version="0.1.0")

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


class IndicatorSnapshot(BaseModel):
    symbol: str
    ts_utc: datetime
    pre_post: Literal["PRE", "POST"]
    records: List[ExpiryRecord]
    features: Dict[str, float]


class IndicatorState(BaseModel):
    """Represents the state of a single indicator"""
    active: bool
    strength: Optional[float] = 0.0  # 0-100 scale
    context: Optional[str] = ""
    last_triggered: Optional[datetime] = None


class ExpiryIndicators(BaseModel):
    """Collection of expiry-related indicators for a symbol"""
    symbol: str
    ts_utc: datetime
    market_phase: Literal["PRE", "POST"]
    
    # Individual indicators
    pin_reversion: IndicatorState = Field(..., description="I1: Pin reversion pressure")
    gamma_wall_proximity: IndicatorState = Field(..., description="I2: Gamma wall proximity")
    post_expiry_breakout: IndicatorState = Field(..., description="I3: Post-expiry breakout potential")
    volatility_compression: IndicatorState = Field(..., description="I4: Volatility compression/expansion")
    
    # Aggregate metrics
    overall_strength: float = Field(0.0, description="Combined indicator strength 0-100")
    active_indicators: int = Field(0, description="Count of active indicators")


# -------------------------------
# In-memory store (replace with SQLite in production)
# -------------------------------

STORE: Dict[str, List[ExpiryRecord]] = {}
SPOT_CACHE: Dict[str, float] = {}
INDICATOR_HISTORY: Dict[str, List[ExpiryIndicators]] = {}

CONFIG = {
    "pin_pips_max": 22.0,
    "pin_min_score": 65.0,
    "wall_proximity_pips": 10.0,
    "breakout_threshold_pips": 18.0,
    "breakout_window_hours": 6.0,
    "volatility_compression_threshold": 0.5,
    "pre_window_hours": 8.0,
    "post_window_hours": 6.0,
    "history_retention_hours": 24.0,
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def pip_in_price(symbol: str, digits: Optional[int] = None) -> float:
    """
    Return 1 pip in price terms (approx). For 5-digit (EURUSD 1.23456) -> 0.0001
    For 3-digit JPY (USDJPY 156.123) -> 0.01
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
        # Fallback to last strike mean to keep indicators alive.
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


def get_volatility_ratio_stub(symbol: str) -> float:
    # Replace with real RV calc. < 0.5 means compression.
    return 0.45


def store_indicator_history(symbol: str, indicators: ExpiryIndicators) -> None:
    """Store indicator states for historical analysis"""
    if symbol not in INDICATOR_HISTORY:
        INDICATOR_HISTORY[symbol] = []
    
    INDICATOR_HISTORY[symbol].append(indicators)
    
    # Cleanup old history
    cutoff = now_utc() - timedelta(hours=CONFIG["history_retention_hours"])
    INDICATOR_HISTORY[symbol] = [
        i for i in INDICATOR_HISTORY[symbol] 
        if i.ts_utc > cutoff
    ]


def compute_indicators(symbol: str, records: List[ExpiryRecord], market_phase: str) -> ExpiryIndicators:
    """
    Compute all expiry-related indicators for the symbol.
    This is pure indicator logic - no execution decisions.
    """
    
    # Initialize all indicators as inactive
    pin_reversion = IndicatorState(active=False, strength=0.0)
    gamma_wall_proximity = IndicatorState(active=False, strength=0.0)
    post_expiry_breakout = IndicatorState(active=False, strength=0.0)
    volatility_compression = IndicatorState(active=False, strength=0.0)
    
    if not records:
        return ExpiryIndicators(
            symbol=symbol,
            ts_utc=now_utc(),
            market_phase=market_phase,
            pin_reversion=pin_reversion,
            gamma_wall_proximity=gamma_wall_proximity,
            post_expiry_breakout=post_expiry_breakout,
            volatility_compression=volatility_compression,
            overall_strength=0.0,
            active_indicators=0
        )
    
    spot = records[0].spot or 0.0
    nearest = nearest_record(symbol, records, spot)
    
    # I1: Pin Reversion Indicator (PRE-expiry)
    if market_phase == "PRE" and nearest:
        pin_score = nearest.pin_score or 0.0
        distance = nearest.distance_pips or 1000.0
        
        if pin_score >= CONFIG["pin_min_score"] and distance <= CONFIG["pin_pips_max"]:
            pin_reversion = IndicatorState(
                active=True,
                strength=min(100.0, pin_score),
                context=f"Strike: {nearest.strike}, Pin Score: {pin_score}, Distance: {distance}p",
                last_triggered=now_utc()
            )
    
    # I2: Gamma Wall Proximity Indicator (PRE-expiry, large strikes)
    if market_phase == "PRE" and nearest:
        distance = nearest.distance_pips or 1000.0
        if nearest.size_rank in ("L", "XL") and distance <= CONFIG["wall_proximity_pips"]:
            # Strength inversely related to distance
            strength = max(50.0, 100.0 - (distance * 5))  # Closer = stronger
            gamma_wall_proximity = IndicatorState(
                active=True,
                strength=strength,
                context=f"{nearest.size_rank} Strike: {nearest.strike}, Distance: {distance}p",
                last_triggered=now_utc()
            )
    
    # I3: Post-Expiry Breakout Indicator (POST-expiry)
    if market_phase == "POST" and nearest:
        distance = nearest.distance_pips or 0.0
        if distance >= CONFIG["breakout_threshold_pips"]:
            # Strength proportional to breakout distance
            strength = min(100.0, (distance / CONFIG["breakout_threshold_pips"]) * 60)
            post_expiry_breakout = IndicatorState(
                active=True,
                strength=strength,
                context=f"Breakout Distance: {distance}p from {nearest.strike}",
                last_triggered=now_utc()
            )
    
    # I4: Volatility Compression/Expansion Indicator
    vol_ratio = get_volatility_ratio_stub(symbol)
    if vol_ratio <= CONFIG["volatility_compression_threshold"]:
        # Lower ratio = more compression = higher expansion potential
        strength = max(30.0, (1.0 - vol_ratio) * 120)  # Scale compression to strength
        volatility_compression = IndicatorState(
            active=True,
            strength=min(100.0, strength),
            context=f"Vol Ratio: {vol_ratio:.3f} (Compressed)",
            last_triggered=now_utc()
        )
    
    # Calculate aggregate metrics
    active_indicators = sum([
        pin_reversion.active,
        gamma_wall_proximity.active,
        post_expiry_breakout.active,
        volatility_compression.active
    ])
    
    # Overall strength is weighted average of active indicators
    strengths = []
    if pin_reversion.active:
        strengths.append(pin_reversion.strength * 1.2)  # Pin gets higher weight
    if gamma_wall_proximity.active:
        strengths.append(gamma_wall_proximity.strength * 1.0)
    if post_expiry_breakout.active:
        strengths.append(post_expiry_breakout.strength * 0.8)
    if volatility_compression.active:
        strengths.append(volatility_compression.strength * 0.9)
    
    overall_strength = sum(strengths) / len(strengths) if strengths else 0.0
    
    return ExpiryIndicators(
        symbol=symbol,
        ts_utc=now_utc(),
        market_phase=market_phase,
        pin_reversion=pin_reversion,
        gamma_wall_proximity=gamma_wall_proximity,
        post_expiry_breakout=post_expiry_breakout,
        volatility_compression=volatility_compression,
        overall_strength=round(overall_strength, 1),
        active_indicators=active_indicators
    )


# -------------------------------
# API Endpoints
# -------------------------------

@app.get("/health")
def health() -> Dict[str, object]:
    ensure_demo_data()
    return {"ok": True, "ts": now_utc().isoformat(), "symbols": list(STORE.keys())}


@app.get("/spot")
def set_spot(symbol: str = Query(...), price: float = Query(...)) -> Dict[str, object]:
    """
    Simple spot setter to simulate a live feed (optional).
    Example: GET /spot?symbol=EURUSD&price=1.0832
    """
    SPOT_CACHE[symbol.upper()] = float(price)
    return {"ok": True, "symbol": symbol.upper(), "spot": float(price)}


@app.get("/expiries", response_model=IndicatorSnapshot)
def expiries(symbol: str = Query(...)) -> IndicatorSnapshot:
    """Get enriched expiry data for indicator calculations"""
    ensure_demo_data()
    sym = symbol.upper().replace("/", "")
    records = enrich(sym, STORE.get(sym, []))
    
    market_phase = "PRE"
    if any(r.pre_post == "POST" for r in records):
        market_phase = "POST"
    
    features = {}
    nr = nearest_record(sym, records, records[0].spot if records else 0.0)
    if nr:
        features["nearest_strike"] = nr.strike
        features["distance_pips"] = nr.distance_pips or 0.0
        features["pin_score"] = nr.pin_score or 0.0
    features["volatility_ratio"] = get_volatility_ratio_stub(sym)
    
    return IndicatorSnapshot(
        symbol=sym, 
        ts_utc=now_utc(), 
        pre_post=market_phase, 
        records=records, 
        features=features
    )


@app.get("/expiries.csv")
def expiries_csv(symbol: str = Query(...)) -> str:
    """Get expiry data as CSV for MT4 consumption"""
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


@app.get("/indicators", response_model=ExpiryIndicators)
def indicators(symbol: str = Query(...)) -> ExpiryIndicators:
    """
    Get current indicator states for the symbol.
    This is the main endpoint for indicator status.
    """
    snap = expiries(symbol)
    indicators = compute_indicators(snap.symbol, snap.records, snap.pre_post)
    
    # Store for historical analysis
    store_indicator_history(snap.symbol, indicators)
    
    return indicators


@app.get("/indicators.csv")
def indicators_csv(symbol: str = Query(...)) -> str:
    """Get indicator states as CSV for MT4 consumption"""
    ind = indicators(symbol)
    
    lines = [
        "symbol,timestamp_utc,market_phase,indicator_name,active,strength,context"
    ]
    
    # Add each indicator as a row
    indicators_list = [
        ("pin_reversion", ind.pin_reversion),
        ("gamma_wall_proximity", ind.gamma_wall_proximity), 
        ("post_expiry_breakout", ind.post_expiry_breakout),
        ("volatility_compression", ind.volatility_compression)
    ]
    
    for ind_name, ind_state in indicators_list:
        lines.append(",".join([
            ind.symbol,
            ind.ts_utc.isoformat(),
            ind.market_phase,
            ind_name,
            str(ind_state.active).lower(),
            f"{ind_state.strength}",
            f'"{ind_state.context}"'  # Quote context to handle commas
        ]))
    
    return "\n".join(lines)


@app.get("/indicators/summary")
def indicators_summary(symbol: str = Query(...)) -> Dict[str, object]:
    """Get a simplified summary of active indicators"""
    ind = indicators(symbol)
    
    active_list = []
    if ind.pin_reversion.active:
        active_list.append(f"Pin Reversion ({ind.pin_reversion.strength:.0f}%)")
    if ind.gamma_wall_proximity.active:
        active_list.append(f"Gamma Wall ({ind.gamma_wall_proximity.strength:.0f}%)")
    if ind.post_expiry_breakout.active:
        active_list.append(f"Breakout ({ind.post_expiry_breakout.strength:.0f}%)")
    if ind.volatility_compression.active:
        active_list.append(f"Vol Compression ({ind.volatility_compression.strength:.0f}%)")
    
    return {
        "symbol": ind.symbol,
        "timestamp": ind.ts_utc.isoformat(),
        "market_phase": ind.market_phase,
        "active_count": ind.active_indicators,
        "overall_strength": ind.overall_strength,
        "active_indicators": active_list,
        "any_active": ind.active_indicators > 0
    }


@app.get("/indicators/history")
def indicators_history(
    symbol: str = Query(...), 
    hours: int = Query(24, description="Hours of history to return")
) -> List[ExpiryIndicators]:
    """Get historical indicator states"""
    if symbol not in INDICATOR_HISTORY:
        return []
    
    cutoff = now_utc() - timedelta(hours=hours)
    return [
        i for i in INDICATOR_HISTORY[symbol] 
        if i.ts_utc > cutoff
    ]


if __name__ == "__main__":
    import uvicorn
    print("Starting Expiry Indicator Service on http://127.0.0.1:5001 ...")
    print("Endpoints:")
    print("  /indicators?symbol=EURUSD - Current indicator states")
    print("  /indicators.csv?symbol=EURUSD - CSV format for MT4")
    print("  /indicators/summary?symbol=EURUSD - Simple active summary")
    print("  /expiries?symbol=EURUSD - Raw expiry data")
    uvicorn.run("expiry_indicator_service:app", host="127.0.0.1", port=5001, reload=False)
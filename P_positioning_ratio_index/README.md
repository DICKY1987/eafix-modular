
# Positioning Ratio Index (COT + Retail Sentiment)

This project builds **time-series features and trainable labels** that summarize **institutional vs. retail positioning** for FX pairs by blending:

- **Institutional**: CFTC Commitment of Traders (COT) – weekly, by currency futures.
- **Retail**: OANDA Client Positioning (via API) and/or IG Client Sentiment (via API or DailyFX sentiment mirror).

Outputs:
- `data/processed/features.parquet` – engineered features (ratios, z-scores, divergences).
- `data/processed/labels.parquet` – optional labels for model training.
- `artifacts/plots/` – quick-look charts.

> Note: This repository focuses on **open/free endpoints**. Some endpoints (OANDA/IG) require **free demo credentials**.
> CFTC COT is public and free.

---

## Quick Start

1. **Install** (Python 3.10+ recommended)
```bash
pip install -r requirements.txt
```

2. **Configure**
- Copy `config.example.yaml` to `config.yaml` and fill in tokens if available.
- Pick your symbols in `config.yaml` (e.g., `EURUSD`, `GBPUSD`, `USDJPY`).

3. **Run**
```bash
python main.py
```

4. **Results**
- `data/processed/features.parquet`
- `artifacts/plots/positioning_index_EURUSD.png`

---

## Data Sources

### 1) CFTC COT (Institutional)
- Uses weekly **Disaggregated** or **Legacy** reports (CSV/ZIP) published by CFTC.
- This project defaults to a robust **CSV fetch with retry** from CFTC.
- If you prefer a more stable API, you can switch to **Nasdaq Data Link (Quandl)** in `config.yaml` (optional API key).

### 2) OANDA Retail Positioning
- Requires a free **OANDA v20** token.
- Pulls **PositionBook/OrderBook** or **Open Positions** per instrument.
- Aggregates to **%Long / %Short** and **Long-Short Ratio** time series.

### 3) IG Client Sentiment / DailyFX
- If you have an **IG API key**, use it.
- Otherwise, we fall back to **DailyFX sentiment JSON** (no auth) for select pairs.

> You can use either OANDA or IG or both. If both enabled, we compute a **blended retail sentiment index**.

---

## Features Created

- **Institutional Net Ratio**: (Longs − Shorts) / Open Interest (−1 to +1).
- **Retail Long/Short Ratio**: Longs / Shorts (or %Long − %Short).
- **Divergence**: Institutional trend vs Retail bias.
- **Z-scores** (robust, rolling) for comparability.
- **Extremes**: rolling percentiles for contrarian or breakout filters.

---

## Labels (Optional)

- Simple **k-bar directional label** (configurable horizon).
- **Triple-barrier** labels (time + profit/stop) for robust supervision.

---

## File Tree

```
positioning_ratio_index/
├─ data/
│  ├─ raw/
│  └─ processed/
├─ artifacts/
│  └─ plots/
├─ src/
│  ├─ data_sources/
│  │  ├─ cftc_cot.py
│  │  ├─ oanda_sentiment.py
│  │  └─ ig_sentiment.py
│  ├─ features/
│  │  └─ positioning.py
│  ├─ utils/
│  │  ├─ io.py
│  │  └─ time.py
│  └─ labeling/
│     └─ labels.py
├─ config.example.yaml
├─ requirements.txt
├─ main.py
└─ README.md
```

---

## Notes & Caveats

- **No look-ahead**: all features are shifted by 1 period.
- **Timezones**: COT is weekly (Friday publish for Tuesday positions) – we align **at end of week**. Retail can be intraday.
- **Mapping**: Futures symbols (e.g., EUR) map to FX pairs (e.g., EURUSD). See `cftc_cot.py` for mappings and adjust if needed.
- **Resampling**: You can choose your bar (`1h`, `4h`, `1d`) in `config.yaml`.

---

## License

MIT

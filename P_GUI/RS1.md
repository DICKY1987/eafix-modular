---
doc_id: DOC-LEGACY-0025
---

Definitive Archival Summary

Cross-Asset Signal Generation & Feature Engineering (sig2/sig3)

Pipeline Architecture

Six-step workflow: ingest → align & clean → engineer → synthesize → validate → serve

sig2

.

Emphasis on leakage prevention (purged walk-forward CV, embargo periods).

Latency and failover design: fallback to last-good source, historical averages, or drop signals when stale.

Indicator & Signal Catalog

Rates & Curves

2y Rate Differential Momentum (e.g., US2Y vs DE2Y, z-scored differentials → EURUSD bias).

OIS/Fed Funds vs €STR Differential Slope (term-structure slope differences as directional bias).

Futures Basis & Carry

FX Futures Fair-Value Basis Deviation (spot vs CME futures vs covered interest parity).

Carry Strength Proxy (normalized forward points or short-rate differential).

Options & Volatility

Volatility Spillover (VIX, MOVE; JPY strength on risk-off).

Risk Reversal Skew Proxy (ETF/futures IV spreads).

Equities & Commodities

SPX/DAX/NKY regime indicators.

Commodity linkages (Brent→CAD, Copper→AUD, Gold→AUD & XAUUSD).

Funding & Stress

FRA-OIS, CP-OIS spreads as risk-off signals.

CFTC COT Positioning Pressure as mean-reversion trigger.

Microstructure Proxies

Multi-feed tick-volume composites.

Spot-Futures Lead–Lag Residual (futures predictive edge).

Feature Engineering Rules

Always use stationarity transforms (returns, z-scores).

Strict lag discipline: shift indicators ≥1 bar.

Session/timezone alignment (Tokyo/London/NY).

Robust z-scoring (median/IQR).

Cross-term interactions for conditional edges.

Labels & Targets

Directional k-bar, triple-barrier, meta-labeling, vol-adjusted

sig3

.

Python Implementation Sketch

Functions for z-scoring, merging aligned feeds, feature generation (RateDiff, VIX spillover, futures residual).

Label generator: directional outcome classification.

Example manifests for GUI auto-integration (JSON style).

Governance

Data freshness tracking.

Feature drift statistics.

Retraining triggers.

Logging slippage/spread in backtests.

Identified Gaps

Lack of regime change detection.

Correlation instability across asset linkages.

Missing execution integration (risk sizing, cross-signal budgeting).

Proposed Solutions (sig4)

CUSUM-based structural break detection module.

Adaptive Window Manager to recalibrate z-score windows dynamically.

Smart money/liquidity detection via stop cluster mapping.

Execution extensions: position sizing by confidence, risk budgeting, and session-aware execution logic.

Technical Indicator & Signal System (sig1)

Core Indicator Engine

Moving Averages: SMA, EMA, WMA, HMA, SMMA.

Oscillators: RSI, MACD, Stochastic, Williams %R, CCI.

Volatility: Bollinger Bands, ATR, StdDev, Keltner Channels, custom Volatility Index.

Price-Derived Signal Systems

Friday Volatility Signal (FridayMove)

Detects % change 7:30AM–2PM CST Friday; DST-safe; outputs EXECUTE messages.

Currency Strength Indicators (CSI)

StrengthRSI, StrengthStochastic, StrengthZScore, StrengthMACD across multiple time windows (15m–24h).

Conditional Probability Engine

Triggers on price bursts, indicator zones, or confluences.

Outcomes: continuation, reversal, or compression.

Grid parameterized by burst size (M), time window (W), move size (K), horizon (T).

Empirical Probability Engine

Stores P(Y|X) tables for historical conditional outcomes.

Examples: “+12 pips in <10m → +25 pips next 2h” with empirical probability.

Transformations

Indicator events → states: RSI OB/OS, BB %B, MACD crossovers, ATR regimes, Stochastic crossovers.

Advanced Features

Options Expiry Microstructure: pin pressure, gamma walls, expiry bursts.

DST/Time Handling: signals adjust automatically.

Architecture

MT4 DDE → Price Manager → Indicator Engine → Signal Detection → Execution

sig1

.

Circular buffers for efficient history.

JSON-formatted EXECUTE outputs including source, symbol, direction, strength, probability, sample size, expected move, and risk profile.

System Advantages

Empirical foundation (data-driven, not assumption-based).

Fully configurable thresholds (JSON).

Multi-timeframe operation.

Seamless MT4–Python integration.

UI/UX Brainstorm

Grid layout (indicators as 1x1, 2x1, 2x2 cells).

Tabs: Live View, Config, Signals, Templates, History.

Parameter config panels (with real-time signal integration).

Indicator toggle controls with per-symbol assignment.

Drag-and-drop library with manifest-driven auto-discovery.

Template system (Scalping, Swing, Momentum, Mean Reversion).

Performance panels tracking hit rate, avg P&L, indicator contribution.

Trading Strategy Framework & Market Thinking (sig4 continuation + sig1/sig2 cross-tie)

Taxonomy Expansion

From 11 archetypes → 53+ distinct strategies across Technical, Quantitative, Fundamental, Behavioral branches

sig4

.

Each defined by “DNA” attributes: signal persistence, strength, volatility preference, trend environment, edge source.

Levels of Market Thinking

Level 1 (Retail): Direct info→price reaction (buy good news, sell bad news).

Level 2 (Contrarian): Fades obvious moves, exploits overcrowding (“buy rumor, sell news”).

Level 3 (Institutional): Engineers traps/liquidity, orchestrates L1 & L2.

Dynamics: L1 creates momentum, L2 fades, L3 exploits both.

Execution Logic

Taxonomy of entry/exit orders, stop/take-profit structures, dynamic order management, multi-leg handling.

Idea Capture

Framework to systematize trading insights into structured, testable components.

Quantification Concepts

Market Obviousness Index (MOI) – measures “obviousness” of moves (breakout clarity, volume, news direction).

Contrarian Overcrowding Index (COI) – sentiment extremes, divergence, low fear complacency.

Smart Money Activity Index (SMAI) – price/volume divergence, order flow patterns.

Data Sources & Access (sig2/sig3/sig4 with reinforcement from sig1)

Free/Open Data

Dukascopy, TrueFX, HistData.com (ticks, candles).

FRED, CFTC COT, Yahoo Finance, CME futures, ETF IV proxies.

OANDA/FXCM APIs for streaming ticks, order book, sentiment

sig3

.

Synthesis Methods

Multi-broker aggregation for spreads/tick frequency.

Futures volume + spot tick volume = synthetic depth/volume proxies.

Order book approximations via broker APIs.

Integration Challenge

MQL4 cannot directly fetch APIs → requires preprocessing (Python/batch→CSV) then FileOpen/FileReadString.

✅ Key Takeaways

The four documents collectively define a complete multi-layer trading architecture:

sig1: Technical indicators & empirical signal system, with UI/UX brainstorm.

sig2/sig3: Cross-asset feature factory, indicator recipes, data pipelines, manifests, governance.

sig4: Extensions—gap analysis, regime detection modules, adaptive windows, and market-thinking taxonomy turned into quantifiable indicators.

Together, they show a unified design blending:

Traditional TA → empirical probability.

Cross-asset/macro drivers → engineered features.

Psychological/behavioral frameworks → quantified thresholds.

Implementation blueprints in both Python and MQL4.

Would you like me to now merge this archival summary into a structured master index document (with IDs, metadata, and cross-references) so it can serve as the canonical “single source of truth” across all subsystems?

Sources
You said:
yes
ChatGPT said:

Great — I’ll take the archival summary and promote it into a structured master index document that is machine-readable, auditable, and cross-referenced. This will serve as the canonical “single source of truth” for your HUEY_P subsystems.

Here’s the Master Index Document (Hybrid Markdown with embedded JSON-LD style IDs for programmability):

📚 HUEY_P Master Index Specification (Archival Canonical Document)
<!-- MASTER_INDEX { "version": "1.0.0", "project": "HUEY_P Trading System", "date_created": "2025-09-06", "maintainer": "Synoptic-Archive AI", "purpose": "Canonical cross-reference of all subsystems, indicators, strategies, and governance." } -->
1. Technical Indicator & Signal System (sig1)

Core Indicator Engine

SMA, EMA, WMA, HMA, SMMA

RSI, MACD, Stochastic, Williams %R, CCI

Bollinger Bands, ATR, StdDev, Keltner, Volatility Index

Specialized Signal Systems

Friday Volatility Signal (DST-safe, % change window, normalized EXECUTE output)

Currency Strength Indicators (CSI) – multi-timeframe RSI, Stochastic, MACD, Z-Score

Conditional Probability Engine – burst triggers, indicator states, outcome probabilities

Empirical Probability Engine – P(Y|X) tables for historical outcome likelihoods

Implementation

MT4 DDE → Price Manager → Indicator Engine → Signal Detection → Execution

JSON-based EXECUTE messages for downstream systems

UI/UX Framework

Grid layout (indicators as 1x1, 2x1, 2x2)

Tabs: Live View, Config, Signals, Templates, History

Drag-and-drop library, manifest-driven auto-discovery

Templates (Scalping, Swing, Momentum, Mean Reversion)

Performance panel: hit rate, avg P&L, indicator contribution

2. Cross-Asset Feature Factory (sig2/sig3)

Pipeline

Ingest → Align/Clean → Engineer → Synthesize → Validate → Serve

Leakage prevention: walk-forward CV, embargo

Latency fallbacks: last-good, historical averages

Indicator Catalog

Rates & Curves – RateDiff momentum, OIS/€STR slope

Futures Basis – FX Futures Fair-Value, Carry Strength

Volatility – VIX/MOVE spillover, risk reversal skew

Equities/Commodities – SPX/DAX/NKY risk regimes, Brent/Copper/Gold FX linkages

Funding/Stress – FRA-OIS spreads, COT positioning

Microstructure – tick-volume composites, futures lead-lag residual

Feature Engineering Rules

Stationarity transforms, robust z-scores

Strict lagging discipline

Session/timezone alignment

Regime conditioning with volatility dummies

Interaction terms (RateDiff×RiskOn)

Training Labels

Directional k-bar, triple-barrier, meta-labeling, vol-adjusted

Implementation Sketch

Python dataclasses, robust z-scoring, align_merge utility

Indicator manifests (JSON) for GUI auto-integration

Governance

Drift monitoring, retraining triggers

Freshness checks per source

Slippage/spread logging

3. Strategy Framework & Market Thinking (sig4, extended)

Taxonomy

From 11 archetypes → 53+ types

Branches: Technical, Quantitative, Fundamental, Behavioral

DNA attributes: persistence, strength, volatility preference, trend environment, edge source

Levels of Market Thinking

L1 (Retail): direct info→price reactions

L2 (Contrarian): fade obvious moves, exploit overcrowding

L3 (Institutional): engineer traps, orchestrate both L1/L2

Dynamic interplay: L1 momentum → L2 fade → L3 orchestration

Execution Taxonomy

Entry orders, SL/TP structures

Dynamic order adjustments

Multi-leg coordination

Idea Capture

AI-assisted framework: capture → structure → standardize → systematize

Quantified Indicators

Market Obviousness Index (MOI) – breakout clarity, news alignment, volume confirmation

Contrarian Overcrowding Index (COI) – sentiment extremes, divergence, complacency

Smart Money Activity Index (SMAI) – volume-price divergence, order flow imbalance

4. Identified Gaps & Solutions (sig4)

Gap 1: No regime-change adaptation

Solution: CUSUM-based structural break detector, adaptive rolling windows

Gap 2: Cross-asset correlation instability

Solution: Correlation stability monitors; fallback when linkages break

Gap 3: Execution integration missing

Solution: Position sizing by confidence, session-aware execution, risk budgeting across signals

5. Data & Integration Layer

Sources

Dukascopy, TrueFX, HistData (ticks/candles)

FRED, CFTC, CME futures, Yahoo Finance ETFs

OANDA/FXCM APIs for sentiment, tick volume, DOM snapshots

Synthetic Metrics

Depth-of-market proxies (multi-broker aggregation)

Tick volume + futures volume cross-validation

Order book approximations (heatmaps from broker APIs)

Integration with MQL4

External preprocessing via Python → CSV

FileOpen/FileReadString in MQL4 for feature ingestion

✅ Canonical Use

This index serves as:

Executive Review Document: single authoritative picture

Legal Discovery Record: exhaustive archival of technical details

Development Guide: blueprint for coders (Python + MQL4)

Governance Map: oversight of drift, retraining, data integrity
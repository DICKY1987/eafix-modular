Here's the overview of C:\Users\richg\eafix-modular\services:

  ---
  Services Directory Overview

  Architecture Patterns

  - Dual-naming convention: Each service has a hyphenated directory (e.g., data-ingestor) with implementation files, and
   an underscore directory (e.g., data_ingestor) as a stable import wrapper.
  - ID-prefixed files: All implementation files carry numeric IDs (e.g., 2099900112260118_config.py) for traceability.
  - Plugin architecture: Every service exposes a plugin.py inheriting from BasePlugin.
  - Standard structure per service: config.py, health.py, metrics.py, main.py (FastAPI), plugin.py.

  ---
  Service Inventory

  ┌────────────────────┬─────────┬─────────────────────────────────────────────────────────────┐
  │      Service       │ Status  │                           Purpose                           │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ calendar-ingestor  │ Active  │ Calendar event ingestion                                    │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ common             │ Active  │ Shared base classes, startup_health_gate, BaseService       │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ compliance-monitor │ Stub    │ Only a requirements.txt                                     │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ dashboard-backend  │ Active  │ FastAPI backend + React frontend dashboard                  │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ data-ingestor      │ Active  │ Normalizes MT4/DDE broker feeds → PriceTick events          │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ data-validator     │ Stub    │ Minimal source files                                        │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ desktop-ui         │ Active  │ Tkinter GUI, MQ4 scripts, indicator overlays                │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ event-gateway      │ Active  │ Event broker/gateway                                        │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ execution-engine   │ Active  │ OMS, trade outcome classification                           │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ flow-monitor       │ Active  │ Workflow monitoring                                         │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ flow-orchestrator  │ Active  │ Service workflow coordination                               │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ gui-gateway        │ Active  │ GUI communication gateway                                   │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ indicator-engine   │ Active  │ Currency strength, advanced indicators                      │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ reentry-engine     │ Active  │ Processes TradeResult → ReentryDecision events              │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ reentry-matrix-svc │ Active  │ Re-entry decision matrix                                    │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ reporter           │ Active  │ Report generation/publishing                                │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ risk-manager       │ Active  │ Risk management and mitigation                              │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ scripts            │ Utility │ Shell scripts for enterprise service integration/validation │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ signal-generator   │ Active  │ Signal processing from indicators                           │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ telemetry-daemon   │ Active  │ System-wide health monitoring, alerting, observability      │
  ├────────────────────┼─────────┼─────────────────────────────────────────────────────────────┤
  │ transport-router   │ Active  │ Event routing and validation between services               │
  └────────────────────┴─────────┴─────────────────────────────────────────────────────────────┘

  ---
  Key Service Flow

  data-ingestor → indicator-engine → signal-generator → execution-engine
                                                       ↓
                                                risk-manager
                                                       ↓
                                             reentry-engine ← reentry-matrix-svc
                                                       ↓
                                              transport-router
                                                       ↓
                                            telemetry-daemon (cross-cutting)
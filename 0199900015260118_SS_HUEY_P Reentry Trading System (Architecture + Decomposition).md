SS_HUEY_P Reentry Trading System (Architecture + Decomposition).md
15.40 KB •335 lines
•
Formatting may be inconsistent from source

Software Requirements Specification (IEEE-830 Style)
For: HUEY_P Reentry Trading System (Architecture + Decomposition)
1. Introduction
1.1 Purpose

Define a precise, machine-readable SRS that consolidates the attached reentry and signal-pipeline documents into a single architectural source of truth. It delivers a complete decomposition (Systems â†’ Subsystems â†’ Components â†’ Modules), explicit data/communication contracts, and end-to-end traceability to the originating specs/manuals. 

1.2 Scope

The scope covers: parameter schema/governance for reentry; signal generation/validation/export; communication bridges (CSV, enhanced signals, sockets/FastAPI); EA execution & feedback; persistence and analytics (SQLite schema, KPI exports); configuration/profile rotation; monitoring/logging and deployment. Non-goals include prescribing trading strategies/indicators beyond the interfaces/constraints. 

1.3 Definitions, Acronyms, Abbreviations

EA: MetaTrader 4 Expert Advisor.

Reentry: Automated post-closure trade action guided by a matrix/profile.

Enhanced Signals: Rich CSV line(s) with embedded JSON context for downstream consumption.

Persona/Profile: Per-symbol CSV mapping of six outcome buckets to actions/parameters.

Matrix: Multi-dimensional decision surface used by the reentry engine. 

1.4 References

Reentry Trading System â€” Single Source of Truth (v3.0) (â€œCanonical Spec / Specâ€) â€” 2025-08-20. 

REENTRY_COMMUNICATION_INTEGRATION.md (â€œComm Integration / Manualâ€). 

Signal System â€” Complete Process Flow Document (â€œSignal Flow / Manualâ€). 

Reentry Automation & Analytics Pack â€” Technical Specification (â€œAutomation Pack / Specâ€). 

the projectâ€™s parameter sets.md (â€œParameter Sets / Manualâ€). 

1.5 Overview

Sections 2â€“3 map the system layers and decompose the architecture; each element lists role, dependencies (inputs/outputs), and cites the source(s). Section 3 also codifies functional, performance, and design constraints with traceability. 

2. Overall Description
2.1 Product Perspective

The Reentry System is a cross-cutting capability embedded in the broader HUEY_P pipeline. It consumes upstream signal/closure events and/or EA feedback, evaluates reentry decisions via a matrix/profile, communicates decisions to EA, executes, and records lineage/KPIs in SQLite with scheduled profile rotation and exports. 
 

2.2 Product Functions (High-Level)

Govern reentry via executable parameter schema, invariants, and EA validation checklist. 

Transport decisions through a tiered comms hierarchy (sockets/FastAPI â†’ enhanced_signals.csv â†’ static CSV profile fallback). 

Execute & log reentry actions in EA; persist trades, chains, executions; export KPIs; rotate profiles on schedule. 

2.3 Architecture Layers (Layered Decomposition)

Data Sources: Calendar/Indicators/Manual triggers; EA trade closures. 

Data Processing: Excel/VBA Signal pipeline (validation, conflict resolution, transactional export). 

Communication/Bridges:

Tier-1 sockets via bridge + FastAPI;

Tier-2 enhanced signals (CSV + JSON payload);

Tier-3 static CSV profile. 

Execution & Reentry: EA decision intake, gating, enforcement, feedback files. 

Persistence: SQLite schema (trades, reentry_executions, chains, performance) + views. 

Configuration Management: reentry_pack_config.json, persona cycle maps, per-symbol CSV provisioning. 

Monitoring, Logging, Deployment: Health checks, installer/verifier, Windows Task Scheduler tasks, freeze logic in pipeline. 
 

2.4 User Characteristics

System operators (quant/ops) maintain config, profiles, and schedules; EA developers maintain MQL4 integration; data/automation engineers maintain Python/FastAPI/SQLite and tasks. 

2.5 Constraints, Assumptions, Dependencies (Overview)

Transport: Canonical Spec v3.0 fixes a CSV_ONLY baseline profile contract; integration manual introduces tiered sockets/enhanced signals as future-friendly upgrades with graceful degradation. (Constraint + Roadmap tension noted.) 
 

Atomic I/O: Signal export uses temp-file â†’ atomic rename; strict multi-tier validation and freeze-on-fail protections. 

Idempotent DB: Migrator and views must be rerunnable; tasks must be schedulable and verifiable. 

2.6 Architectural Decomposition (Systems â†’ Subsystems â†’ Components â†’ Modules)

For each element: Name & Role, Dependencies (consumes â†’ produces), Sources (Manual/Spec).

2.6.1 System A â€” Signal & Trigger Pipeline (Manual)

Role: Normalize upstream triggers; validate; resolve conflicts; export transactional CSV for EA. 

Consumes â†’ Produces: Calendar/Indicators/Manual â†’ signals.csv (+ feedback files). 

Subsystems:
A1) SignalTriggerHandler (extract metadata, build CompositeKey). 

A2) SignalValidator (Tier-1/2/3 validation). 

A3) ConflictManager (Â±5-min window; drop second). 

A4) SignalExporter (temp file â†’ atomic rename). 

A5) MT4 Feedback Monitor (status/results/rejections; timeouts). 

2.6.2 System B â€” Communication Bridges (Manual)

Role: Deliver reentry requests/decisions between EA and Python service; degrade gracefully. 

Consumes â†’ Produces: EA closure events â†’ decision req/resp; fallback to enhanced_signals.csv or static profiles. 

Subsystems:
B1) Socket Bridge + FastAPI (primary; sub-second). Modules: EA socket client; Python EAConnector; FastAPI /reentry/decide & /reentry/execute. 

B2) Enhanced Signals Path (fallback; CSV with embedded JSON). Modules: ReentrySignalProcessor; EA parser. 

B3) Static CSV Profile (legacy fallback). Module: EA CSV reader applying bucket rules. 

2.6.3 System C â€” Reentry Decision Engine (Spec + Manual)

Role: Classify outcome bucket; evaluate matrix; output action, multiplier, delay, confidence, combination_id. 

Consumes â†’ Produces: EA trade context (ticket, outcome) â†’ decision payload (+ combination_id). 

Components/Modules:
C1) Matrix Evaluator (multi-dimensional lookup & performance feedback). 

C2) EA Gate & Validator (enforce min confidence, max generations, spread guard). 

C3) Decision Serializer (to socket JSON / enhanced signal / CSV profile fields). 

2.6.4 System D â€” EA Execution & Feedback (Manual)

Role: Receive decision; execute reentry; ACK/record results; write feedback (status/results). 

Consumes â†’ Produces: Decision payload â†’ execution + trade_results.csv/DB updates. 

Modules: ProcessReentryDecision, ExecuteReentryAction, FeedbackWriter. 

2.6.5 System E â€” Persistence & Analytics (Spec)

Role: Maintain per-symbol schema; record trades, reentry_executions, chains; create views; export KPIs. 

Consumes â†’ Produces: EA writes DB rows â†’ KPI CSVs & dashboards. 

Components:
E1) SQLite Migrator & Views (idempotent). 

E2) KPI Export Jobs (weekly snapshots). 

E3) Governance Mapping (controls â†” telemetry). 

2.6.6 System F â€” Configuration & Profile Management (Spec)

Role: Single JSON config drives paths, symbols, personas; daily profile rotation to EA config. 

Consumes â†’ Produces: reentry_pack_config.json â†’ <SYMBOL>_reentry.csv in EA config path. 

Modules: Profile Rotate (Task/XML), Install/Verify scripts, Config Apply. 

2.6.7 System G â€” Monitoring, Logging & Deployment (Spec + Manual)

Role: Health verification, task scheduling, error/freeze logic, MT4 integration status and dashboard hooks. 

Modules: verify_reentry_install.ps1, Task_ProfileRotate.xml, Task_KPIWeekly.xml, freeze logic counters. 

2.7 Relationship Mapping (Cross-Layer Flows)

Flow-1 (Signals â†’ EA): Calendar/Indicators/Manual â†’ Validation/Conflict â†’ atomic export signals.csv â†’ EA consumes â†’ EA writes feedback CSVs. 

Flow-2 (Reentry Primary): EA trade closes â†’ Socket bridge â†’ FastAPI /reentry/decide â†’ Matrix evaluate â†’ EA executes â†’ DB updated. 

Flow-3 (Reentry Fallbacks):
(a) Enhanced signals: EA â†’ enhanced_signals.csv â†’ Python processor â†’ DB;
(b) Static profile: EA reads <SYMBOL>_reentry.csv â†’ executes with predefined parameters. 

Flow-4 (Ops/Analytics): Daily profile rotation â†’ EA runtime reads profiles â†’ weekly KPI export from SQLite views. 

3. Specific Requirements
3.1 Functional Requirements
3.1.1 Parameter Schema & Governance (Spec)

FR-P1: Validate all parameter sets against the authoritative schema (risk percent, SL/TP units, ATR options) before acceptance; violations trigger REJECT_SET and no execution. 

FR-P2: Enforce max_risk_cap_percent = 3.50 at EA gate time. 

FR-P3: Map governance controls to EA inputs/CSV columns and telemetry fields (min delay, max generations, spread guard, etc.). 

3.1.2 Signal Pipeline & Export (Manual)

FR-S1: Perform 3-tier validation (structural, business logic, market context). 

FR-S2: Resolve conflicts within Â±5 minutes by dropping the second signal and logging reason. 

FR-S3: Export via temp file and atomic rename; on failure, retry/delete temp/raise freeze counters. 

3.1.3 Communication & Bridges (Manual + Spec)

FR-C1: Support Tier-1 socket decision path with protocol message types: REENTRY_DECISION_REQUEST/RESPONSE, REENTRY_EXECUTION_RESULT, REENTRY_MATRIX_UPDATE. 

FR-C2: Support Tier-2 enhanced signals with embedded JSON fields (action, confidence, multiplier, delay, combination_id). 

FR-C3: Maintain Tier-3 static CSV profile compatibility for legacy fallback. 

Traceability note: Canonical Spec v3.0 constrains a CSV-only baseline for profiles; Comm Integration expands to sockets/enhanced signals with fallbacks. (Spec adds stricter contracts; Manual adds performance and topology.) 
 

3.1.4 Reentry Decision Engine (Spec + Manual)

FR-R1: Compute outcome bucket and evaluate matrix for action type, size multiplier, delay, confidence, and combination_id. 

FR-R2: Gate execution by MinReentryConfidence, MaxReentryGenerations, and spread guard. 

FR-R3: Serialize the decision per active transport (socket JSON / enhanced signal / CSV fields). 

3.1.5 EA Execution & Feedback (Manual)

FR-E1: On receipt, validate decision, enforce caps, execute, and ACK; write results to feedback CSVs and/or DB. 

FR-E2: If socket timeout, attempt enhanced signal path; if unavailable, consult static profile. 

3.1.6 Persistence & Analytics (Spec)

FR-DB1: Maintain per-symbol tables (trades, executions, chains, performance) and create analytics views; migrations must be idempotent. 

FR-DB2: Weekly KPI exports to CSV for operator review. 

3.1.7 Configuration & Profile Rotation (Spec)

FR-CFG1: reentry_pack_config.json is the single source of truth for paths/schedules/personas. 

FR-CFG2: Daily task copies persona CSVs into EA config path; verify success via installer/verifier. 

3.1.8 Monitoring, Health & Deployment (Spec + Manual)

FR-OPS1: Provide installer, verifier, and scheduled tasks; capture errors and suggested operator actions. 

FR-OPS2: Track MT4 integration status, consecutive failure counters, and freeze/unfreeze lifecycle hooks. 

3.2 Performance Requirements

PR-1: Tier-1 socket path should return decisions with sub-second latency under nominal conditions. 

PR-2: Enhanced signals path must meet EA polling cadence; CSV write/read must complete within EA cycle without contention. 

PR-3: Atomic export must avoid partial writes; retries capped as specified in the manual. 

3.3 Design Constraints

DC-1: CSV-only baseline profile contract per Canonical Spec v3.0 (strict keys/units; EA must reject invalid sets). 

DC-2: Idempotent DB migrations/views; config-driven scheduling; Windows environment paths as specified. 

DC-3: Message protocol types and EA input parameters fixed as enumerated in the integration manual. 

3.4 Traceability Annotations (Spec vs Manual)

Transport & Contracts
Spec adds binding constraints: CSV-only baseline, executable schema, explicit units and caps. Manual extends topology: sockets/enhanced signals tiers with graceful degradation and protocol enumerations. 
 

Validation & Safety
Manual provides operational gates: 3-tier validation, conflict rules, atomic export, freeze logic. Spec aligns with EA checklist/invariants. 
 

Ops & Analytics
Spec (Automation Pack) adds non-functional operations: installer, verifier, tasks, KPI exports, governance mapping. 

Parameter Management Risks
Manual (Parameter Sets) flags governance/observability gaps and clarifies â€œon-the-wireâ€ update flows (socket JSON primary; CSV bridge fallback) with ACKs and schema mirrorsâ€”requirements captured above in FR-C1..C3 and FR-E1. 

3.5 Complete Coverage & Consolidation Notes

Represented Systems/Subsystems: Signal pipeline (A1â€“A5); Communication bridges (B1â€“B3); Reentry engine (C1â€“C3); EA execution & feedback (D); Persistence & analytics (E1â€“E3); Config/profile mgmt (F); Monitoring/deploy (G). All appear in at least one source; duplicates consolidated with dual citations. 
 
 
 

Spec-only Constraints: Risk cap 3.50%, units, reject-on-violation, CSV-only baseline contract. 

Manual-only Details: Tiered transports, protocol enums, validation tiers, atomic export, operational freeze rules. 
 

Ops/Analytics: Installer, verifier, tasks, KPI exports, governance mapping and acceptance criteria captured as functional requirements. 

3.6 Dependencies (Upstream/Downstream Links)

Upstream: Calendar/Indicator/Manual events; EA trade closures. Downstream: EA execution; DB rows; KPI CSVs; dashboards/ops logs. 
 

3.7 Relationship Diagrams (Textual)

Calendar/Indicators/Manual â†’ Validation â†’ ConflictMgr â†’ Atomic Export â†’ signals.csv â†’ EA â†’ signals_status.csv, trade_results.csv, signal_rejections.csv. (Transactional export + feedback timeouts.) 

EA Trade Close â†’ Socket Bridge â†’ FastAPI â†’ Matrix â†’ EA Execute â†’ DB Update (fallbacks: Enhanced Signals â†’ DB; Static Profile). 

4. Acceptance & Non-Functional

Acceptance: AC-1..AC-5 from Automation Pack (installer creates schema; rotation works; KPIs export; verifier passes; schedules match config). 

Operability: Provide command interfaces for install/migrate/views/profile-rotate/KPI/verify; include error matrix with remedies. 

Observability: MT4IntegrationStatus fields + dashboard triggers. 

Performance: Sub-second sockets; bounded retries and timeouts for CSV paths; atomic I/O required. 
 

5. Completeness Check (This SRS vs Sources)

All systems/subsystems enumerated and mapped to layers; duplicates merged with traceability to both Spec/Manual where applicable. âœ”ï¸ 
 
 
 

Contracts & paths captured (profiles/config/db/tasks; enhanced_signals/feedback CSVs; sockets endpoints). âœ”ï¸ 
 

Validation & safety rules integrated (tiers, freeze). âœ”ï¸ 

Governance & KPIs aligned to controls/telemetry. âœ”ï¸ 

Appendix A â€” Source-to-Section Trace Guide (Examples)

CSV-only baseline & schema/units â†’ Â§3.1.1, Â§3.3. (Spec v3.0). 

Tiered transports + protocol enums â†’ Â§2.3, Â§2.6.2, Â§3.1.3, Â§3.2. (Comm Integration). 

Validation/atomic export/freeze â†’ Â§2.6.1, Â§3.1.2. (Signal Flow). 

DB/KPI/Tasks/Governance â†’ Â§2.6.5â€“2.6.7, Â§3.1.6â€“3.1.8, Â§4. (Automation Pack).
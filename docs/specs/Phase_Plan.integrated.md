# Phase Plan â€” Integrated with Overall Implementation

> This document integrates the status/evaluation from **Overall Implementation.md** into the execution roadmap defined in **Phase_Plan.md**. It keeps the original phase plan intact and adds a status baseline, a crosswalk from recommendationsâ†’phases, and a few additive subâ€‘phases to cover gaps (P_ folder integration, compliance monitoring & remediation, and legacy bridge).

---

## Status Baseline (from â€œOverall Implementation.mdâ€)

### Major Accomplishments (âœ…)
- **Microservices Architecture (100%)** â€” 17 services implemented with Docker Compose, schema registry, and modern FastAPI/Redis patterns.
- **Testing Framework (95%)** â€” Integration tests, contract validation with golden fixtures, performance/tick replay, and E2E pipeline tests.
- **Configuration Management (90%)** â€” Poetry, envâ€‘based configuration, Docker Compose; Makefile ops.
- **Documentation & Standards (85%)** â€” CLAUDE.md, perâ€‘service READMEs, and consistent patterns.

### Partially Addressed (âš ï¸)
- **P_ Folder Integration (60%)** â€” P_* content not fully merged (e.g., P_positioning_ratio_index, P_GUI, P_INDICATOR_REENTRY).
- **Crossâ€‘Language Standards (40%)** â€” Limited PowerShell/MQL4 integration; SQL standards not unified.
- **Realâ€‘Time Compliance Monitoring (30%)** â€” No live compliance dashboards, autoâ€‘remediation, or emergency recovery runbooks.

### Not Addressed (âŒ)
- **Standards Enforcement Framework** â€” preâ€‘commit enforcement, CI/CD compliance gates.
- **Crossâ€‘Language Bridge** â€” robust bridge across Python â‡„ MQL4 â‡„ PowerShell, unified config/errâ€‘handling.
- **Productionâ€‘Readiness** â€” emergency recovery procedures, realâ€‘time perf monitoring with alerts, automated rollback.

### Recommendations (ðŸŽ¯)
1) **P_ Folder Content Integration** (audit/migrate/map/update imports).  
2) **Standards Framework** (compliance service, preâ€‘commit, CI gates).  
3) **Bridge Integration** (legacy bridge, unified config propagation, crossâ€‘system health checks).

---

## Crosswalk: Recommendations â†” Phases in this Plan

- **P_ Folder Integration â†’ _New Phase 2A_** (runs parallel to Phase 2).  
- **Standards Enforcement & Compliance â†’ _Extend Phase 3_ and _New Phase 5A_** (CI gates plus live compliance & remediation).  
- **Legacy Bridge / Crossâ€‘Language Integration â†’ _New Phase 7A_** (after initial K8s path).  
- **Emergency Recovery / Rollback â†’ _Augment Phase 6_ (release) and _Phase 10_ (runbooks)**.

---

## Phases

> Phases 0â€“12 below preserve the structure and intent of the original plan, with targeted additions where noted.

### Phase 0 â€” Project Baseline & Branch Protection (Day 0)

**Goal:** lock in a safe working baseline and guardrails.  
**Why:** prevents drift during the hardening work.

**Tasks**
- Protect default branch (PRs required, linear history, status checks).
- Create working branch `rel/v0.1.0-hardening`.
- Add Taskfile/Makefile with **up/test/lint/build/sbom/release:dry**.
- Enable Issues & Projects for tracking.


#### Scope
- Repository baseline, branch protection, formatting and hooks
- No service logic changes; scaffolding and guardrails only

#### Deliverables
- .pre-commit-config.yaml installed and enforced
- CODEOWNERS and branch protection on main with required checks
- Makefile baseline targets wired

#### Milestones
- Day 0: Baseline config merged to main
- Day 0: Branch protection applied

#### Dependencies
- GitHub admin permissions to set protection rules
- Developer machines with pre-commit installed

#### Risks & Mitigations
- Misconfigured required checks can block merges | Mitigation: dry-run on a staging branch then apply
- Secrets committed by mistake | Mitigation: enable secret scanning, add pre-commit secrets hook
**Acceptance**
- Protected default branch; feature branches via PR only.
- `task up` brings up current compose stack.

**Deliverables** â€” Branch protection, Taskfile/Makefile.  
**Effort/Deps** â€” 0.5 day; none.

---

### Phase 1 â€” Repo Hygiene & Legal (Day 1)

**Goal:** formalize licensing, contribution, ownership, and support paths.  
**Why:** legal clarity and faster code review.

**Tasks**
- Add **LICENSE (MIT)** to match README claim.
- Add **.github/**: CODEOWNERS, CONTRIBUTING.md, SECURITY.md, issue templates.
- Add **docs/README.md** to explain docs layout.


#### Scope
- Repository hygiene and legal basics (license, security, contributing)

#### Deliverables
- LICENSE (MIT) and NOTICE or third-party attributions as needed
- CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md
- Dependabot configuration active for ecosystems in use

#### Milestones
- Day 1: Legal docs reviewed and merged
- Day 1: Dependabot opened initial PRs

#### Dependencies
- Legal approval of chosen license and policies
- Repository admin to enable security features

#### Risks & Mitigations
- License mismatch with upstream components | Mitigation: audit dependencies and align on MIT compatibility
- Bot PR noise | Mitigation: group updates and schedule windows
**Acceptance**
- LICENSE recognized by GitHub; issue templates in effect; PRs route via CODEOWNERS.

**Deliverables** â€” `/LICENSE`, `/.github/*`, `/docs/README.md`.  
**Effort/Deps** â€” 0.5â€“1 day; Phase 0 complete.

---

### Phase 2 â€” Canonical Contracts & Codegen (Days 2â€“4)

**Goal:** JSON Schemas become singleâ€‘sourceâ€‘ofâ€‘truth for all contracts.  
**Why:** prevent Pythonâ‡„MQL4 drift and runtime failures.

**Tasks**
- Define schemas under `/contracts/events/`: `PriceTick@1.0`, `IndicatorVector@1.1`, `Signal@1.0`, `OrderIntent@1.2`, `ExecutionReport@1.0`, `CalendarEvent@1.0`, `ReentryDecision@1.0`.
- Generate Python models (Pydantic v2) into each service.
- Add MQL4 helpers: `/P_mql4/helpers/contract_parsers.mq4` for schemaâ€‘aware parse/serialize with numeric/text safety.
- Roundâ€‘trip golden tests in `/P_tests/contracts/`: JSON â†’ Py â†’ JSON; JSON â†’ MQL4 â†’ JSON.
- Document in `docs/modernization/01_service_catalog.md`.


#### Scope
- Define canonical contracts (JSON, CSV) and validators; integrate with tests and CI

#### Deliverables
- contracts/schemas/*.json plus validation scripts (contracts/validate_json_schemas.py)
- CSV models and validators (contracts/models/csv_models.py, validate_csv_artifacts.py)
- CI wiring via ci/validate_schemas.py and tests/contracts

#### Milestones
- Day 2: Core schemas drafted and reviewed
- Day 3: Validators pass on fixtures; contract tests green
- Day 4: Code generation hooks prepared (where applicable)

#### Dependencies
- Domain inputs for schema fields and invariants
- Fixture data for CSV and JSON samples

#### Risks & Mitigations
- Schema churn destabilizes services | Mitigation: version schemas, add compatibility checks (ci/check_schema_compat.py)
- Ambiguity in CSV typing | Mitigation: explicit converters and strict validation
**Acceptance**
- Schema change fails tests until models/helpers regenerated.
- Python & MQL4 roundâ€‘trip tests pass.

**Deliverables** â€” `/contracts/events/*.json`, generated models, helpers, tests.  
**Effort/Deps** â€” 2â€“3 days; Phases 0â€“1.

---

### **Phase 2A â€” P_ Folder Content Integration (Days 2â€“4, parallel)**

**Goal:** integrate P_* content into the main codebase.  
**Why:** remove duplication and align legacy assets with contracts & services.

**Tasks**
- Audit all **P_** folders (e.g., `P_positioning_ratio_index`, `P_GUI`, `P_INDICATOR_REENTRY`).  
- Migrate missing components to canonical locations (e.g., `/shared/reentry/`, `/src/eafix/positioning/`, GUI assets into `gui-gateway`).  
- Update imports, configs, and docs references; remove obsolete copies.  
- Add smoke tests for migrated modules; update Taskfile targets.

**Acceptance**
- No dangling imports; P_* functionality accessible via services.  
- CI green on migration PR; golden tests for reentry/positioning pass.

**Deliverables** â€” migration PRs, updated docs, removal of duplicates.  
**Effort/Deps** â€” 1â€“2 days; Phase 2 in progress.

---

### Phase 3 â€” CI/CD Foundations (Days 4â€“6)

**Goal:** CI as source of truth for quality gates and artifacts.  
**Why:** repeatable, provable builds.

**Tasks**
- **preâ€‘commit**: ruff, black, mypy `--strict`, detectâ€‘secrets (baseline committed).  
- **ci.yml**: matrix (Py 3.11/3.12), run preâ€‘commit, unit + contract tests, build images.  
- **buildâ€‘publish.yml**: on tag `v*`, build perâ€‘service images, **SBOM (Syft)**, **scan (Grype)**, **sign (Cosign)**, push to GHCR.  
- **release.yml**: create GitHub Release with conventionalâ€‘commit notes; attach SBOMs.  
- Require CI checks in branch protection.


#### Scope
- CI for tests, lint, type-check; CD hooks for container builds where applicable

#### Deliverables
- GitHub Actions: .github/workflows/contract-tests.yml, scorecards.yml, security.yml
- CodeQL configured (.github/codeql) and scorecards enabled
- Makefile targets executed in CI

#### Milestones
- Day 4: CI green on PR open and merge
- Day 6: Required checks enforced on main

#### Dependencies
- GitHub runner resources and permissions
- Docker registry access for image publishing (if enabled)

#### Risks & Mitigations
- Flaky tests | Mitigation: isolate, mark, and stabilize before gating
- Long pipelines | Mitigation: incremental caches, matrix split
**Acceptance**
- PRs blocked on lint/type/tests.  
- Tagging `vX.Y.Z` builds signed, SBOMâ€‘ed images in GHCR.

**Deliverables** â€” `.pre-commit-config.yaml`, CI/Release workflows.  
**Effort/Deps** â€” 2 days; Phases 0â€“2.

> **Addition:** CI must include **compliance gates** that read the rules from Phase 5A (below) and fail PRs on violations.

---

### Phase 4 â€” Security Baseline (Days 6â€“7, parallel)

**Goal:** reduce supplyâ€‘chain and secret risks.  
**Why:** trading systems are highâ€‘value targets.

**Tasks**
- Enable **CodeQL**, **secret scanning**, **Dependabot** (Python & Actions).  
- Harden Dockerfiles: nonâ€‘root, readâ€‘only FS, drop Linux caps, pin slim base images.  
- Pin image **digests** in Compose; refuse `:latest`.  
- Add **Scorecards** policy checks.


#### Scope
- Security baseline: code scanning, dependency audit, secret scanning, branch protections

#### Deliverables
- Security workflow active (security.yml), secret scanning on, dependency review enabled
- SECURITY.md with disclosure process
- Basic SBOM generation scripted (stretch)

#### Milestones
- Days 6-7: CodeQL baseline captured; actionable findings triaged

#### Dependencies
- GitHub Advanced Security availability (public repos supported)

#### Risks & Mitigations
- False positives | Mitigation: suppress with justification; track debt
- Secrets in history | Mitigation: rotate and purge if discovered
**Acceptance**
- Security PRs appear automatically; nonâ€‘root containers; digests pinned.

**Deliverables** â€” hardened Dockerfiles/compose, security actions.  
**Effort/Deps** â€” 1 day; after Phase 3 (can start in parallel).

---

### Phase 5 â€” Observability & SLOs (Days 7â€“10)

**Goal:** make SLOs executable for each service.  
**Why:** fast detection, low MTTR.

**Tasks**
- **Structured JSON logs** with correlation IDs.  
- **/metrics** (Prometheus): req/sec, error rate, p50/p95 latency, queue depth, KPIs (fills, slippage, reâ€‘entries).  
- **OpenTelemetry tracing** for HTTP boundaries (signal â†’ risk â†’ execution).  
- Grafana dashboards & alert rules; document SLOs and thresholds.


#### Scope
- Observability: structured logging, metrics endpoints, initial SLOs and dashboards

#### Deliverables
- Metrics via prometheus-client; logs via structlog across services
- SLO definitions (docs/gaps/slo/SLOs.md) and run-time health endpoints
- Sample Grafana dashboards and alert rules (observability/)

#### Milestones
- Days 7-10: Golden signals emitted; dashboards render baseline

#### Dependencies
- Prometheus and Grafana stack availability

#### Risks & Mitigations
- Metrics cardinality blow-up | Mitigation: guidelines, label budgets
- Inconsistent log context | Mitigation: logging adapter with shared fields
**Acceptance**
- `/metrics` exposes counters/histos; dashboards render; test alert fires.

**Deliverables** â€” shared logging/metrics libs, deployable observability stack.  
**Effort/Deps** â€” 2â€“3 days; after Phase 3; parallel with Phase 4.

---

### **Phase 5A â€” Compliance Monitoring, Autoâ€‘Remediation & Recovery (Days 9â€“11)**

**Goal:** realâ€‘time **compliance** against standards with **automated remediation** hooks and **emergency recovery** playbooks.  
**Why:** closes the gap identified in the evaluation and turns policies into executable guardrails.

**Tasks**
- Implement a **compliance service** that evaluates: coding standards, contract versions, secret usage patterns, container hardening, and deployment policies (digests/no `:latest`).  
- Surface **live dashboards** (Grafana panels) for compliance posture; emit alerts on drift.  
- Wire **autoâ€‘remediation hooks** (e.g., open PRs to bump schema/model versions, revert insecure config, quarantine images without SBOM/signature).  
- Draft **Emergency Recovery Procedures**: how to pause trading safely, rollback images, drain queues, and recover state.  
- Export **compliance rules** as JSON consumed by CI (Phase 3) to enforce **PR gates**.

**Acceptance**
- Deliberate rule violation triggers alert and CI failure.  
- Tabletop â€œemergency rollbackâ€ succeeds per runbook.

**Deliverables** â€” compliance service, dashboards, rules JSON, recovery runbook.  
**Effort/Deps** â€” 1â€“2 days; needs Phases 3â€“5 signals.

---

### Phase 6 â€” Release v0.1.0 (Day 10)

**Goal:** establish the first rollbackâ€‘able, signed, SBOMâ€‘ed release.  
**Why:** minimal viable â€œproductionâ€‘ishâ€ artifacts.

**Tasks**
- Update CHANGELOG & version; tag `v0.1.0`.  
- Verify buildâ€‘publish pipeline (images + SBOM + signatures).  
- Publish release notes with container digests.


#### Scope
- Cut and publish v0.1.0 release, containers, and notes

#### Deliverables
- Tag rel/v0.1.0 with CHANGELOG and VERSION updated
- Built images via docker compose; pushed to registry
- Release notes drafted and published

#### Milestones
- Day 10: Tag created; artifacts available

#### Dependencies
- Registry credentials and publishing permissions

#### Risks & Mitigations
- Regressions post-tag | Mitigation: smoke tests, rollback playbook
- Version drift | Mitigation: single VERSION source wired into builds
**Acceptance**
- Release visible with signed images/SBOMs; changelog links PRs.

**Deliverables** â€” GitHub Release `v0.1.0`.  
**Effort/Deps** â€” 0.5 day; Phases 2â€“5.

> **Addition:** Link **Emergency Recovery Procedure** (Phase 5A) into the release notes and runbooks.

---

### Phase 7 â€” Kubernetes/Helm Production Path (Days 11â€“14)

**Goal:** codify production deployment docs and artifacts.  
**Why:** clear path from dev to prod.

**Tasks**
- Create `/deploy/k8s/helm/` (one chart per service + umbrella).  
- Add probes & resources; HPA for stateless services.  
- NetworkPolicies: allowâ€‘lists between services; restrict Redis.  
- External Secrets provider (Vault/ESO); document mounts (no secrets in repo).  
- Deployment runbook with `helm upgrade`/rollback and health checks.


#### Scope
- Helm packaging and Kubernetes manifests for production path

#### Deliverables
- deploy/helm charts with values files; deploy/kubernetes manifests
- Readiness/liveness probes, resource requests/limits, HPA stubs
- Deployment runbook for cluster rollouts

#### Milestones
- Days 11-14: Helm lint and test install in staging

#### Dependencies
- Kubernetes cluster access and secrets management

#### Risks & Mitigations
- Misconfigured resources cause instability | Mitigation: apply quotas, staged rollouts
- Drift between compose and Helm | Mitigation: shared env var catalog
**Acceptance**
- `helm template` and `helm lint` pass; dryâ€‘run in kind/Minikube OK.

**Deliverables** â€” Helm charts + umbrella; deployment runbook.  
**Effort/Deps** â€” 2â€“3 days; needs Phases 4â€“5.

---

### **Phase 7A â€” Legacy Bridge & Crossâ€‘Language Standards (Days 14â€“16)**

**Goal:** productionâ€‘grade **bridge** across Python â‡„ MQL4 â‡„ PowerShell and unified **SQL standards**.  
**Why:** eliminate drift and unify error handling/config propagation.

**Tasks**
- Define **bridge contracts** for IPC/REST/fileâ€‘drop between EA (MQL4) and microservices; align with `/contracts/events/`.  
- Ship MQL4 **helper snippets** for building/parsing shared keys (e.g., `ReentryDecision`), with numeric rounding and text encoding safety.  
- Create **PowerShell** standards (logging, error codes, retries), and a small module to interact with services via REST/CLI.  
- Unify **SQL standards** (PostgreSQL canonical); add migration guidelines from SQLite where present.  
- Crossâ€‘system **health checks** and **config propagation** flows (single source of truth).

**Acceptance**
- Roundâ€‘trip tests cover Pythonâ‡„MQL4 for each shared contract; PS module smoke tests pass.  
- Bridge health dashboard green in steady state; failure injection recovers cleanly.

**Deliverables** â€” bridge library, MQL4/PS helpers, SQL standards doc.  
**Effort/Deps** â€” 2 days; after Phase 7.

---

### Phase 8 â€” Idempotency & Exactlyâ€‘Once Semantics (Days 14â€“16)

**Goal:** stop duplicate orders and handle network flaps safely.  
**Why:** business correctness.

**Tasks**
- **Order nonce** key `(account, symbol, strategy, nonce)`; persist last processed nonce.  
- Idempotent consumers & deâ€‘dupe at executionâ€‘engine message boundaries.  
- Circuit breaker & exponential backoff; bounded queues between indicator â†’ signal â†’ execution.


#### Scope
- Idempotency keys and exactly-once processing where feasible

#### Deliverables
- shared/idempotency helpers integrated; retries are safe
- Idempotent endpoints/messaging for core flows with dedupe stores
- docs/idempotency with patterns and tradeoffs

#### Milestones
- Days 14-16: Idempotency in hot paths verified by tests

#### Dependencies
- Data store support (Redis/DB) for idempotency windows

#### Risks & Mitigations
- Key collisions or hot partitions | Mitigation: composite keys, TTLs, hashing
- Hidden side effects break idempotence | Mitigation: command query separation
**Acceptance**
- Replay tests show no duplicate broker orders; chaos tests (network drop) recover without dupes.

**Deliverables** â€” persistence changes, integration tests.  
**Effort/Deps** â€” 1â€“2 days; after Phases 2 & 5.

---

### Phase 9 â€” Contract & Scenario Testing (Days 16â€“18)

**Goal:** harden correctness of calendar/reâ€‘entry/indicator pipelines.  
**Why:** businessâ€‘critical logic must be deterministic.

**Tasks**
- Scenario tests with realistic OHLCV slices + calendar sequences; assert expected signals and reâ€‘entry decisions.  
- **Propertyâ€‘based tests** (Hypothesis) for indicators.  
- Versioned golden fixtures under `/P_tests/fixtures/`.


#### Scope
- Contract tests (consumer/provider), scenario and property tests

#### Deliverables
- tests/contracts/ consumer, provider, scenarios, properties suites
- CI coverage reports and gating thresholds

#### Milestones
- Days 16-18: All contract suites green with coverage targets met

#### Dependencies
- Stable schemas and service endpoints

#### Risks & Mitigations
- Flaky scenario timing | Mitigation: deterministic fixtures and time controls
- Overfitting tests to implementation | Mitigation: assert public contracts only
**Acceptance**
- Scenario packs pass deterministically; invariants hold.

**Deliverables** â€” test suites + fixtures.  
**Effort/Deps** â€” 2 days; after Phase 2.

---

### Phase 10 â€” Runbooks & Onâ€‘Call (Days 18â€“19, parallel)

**Goal:** make ops repeatable with low cognitive load.  
**Why:** MTTR and auditability.

**Tasks**
- Perâ€‘service runbooks (`docs/runbooks/<service>.md`): start/stop, health checks, common errors, log queries, dashboards, escalation paths.  
- Incident & postmortem templates in `.github/ISSUE_TEMPLATE/`.  
- **Add Emergency Recovery Procedures** from Phase 5A (pause trading, rollback, queue drain, state restore).


#### Scope
- Operational runbooks, on-call setup, health checks and escalation

#### Deliverables
- docs/runbooks with incident response, trading incidents, escalation procedures
- Make targets: runbooks, health-check; smoke tests
- On-call rotation and escalation policy in docs/on-call

#### Milestones
- Days 18-19: On-call ready with drills executed

#### Dependencies
- Monitoring and alerting system integrated

#### Risks & Mitigations
- Alert fatigue | Mitigation: SLO-based alerting, tuning and quiet hours
- Gaps in runbooks | Mitigation: post-incident updates and ownership mapping
**Acceptance**
- Onâ€‘call resolves 3 simulated incidents using docs only.

**Deliverables** â€” runbooks, templates.  
**Effort/Deps** â€” 1â€“1.5 days; after Phases 5 & 7.

---

### Phase 11 â€” Developer Experience (Days 19â€“20, parallel)

**Goal:** reduce friction and standardize workflows.  
**Why:** faster iteration, fewer mistakes.

**Tasks**
- Dev containers/Codespaces with Python 3.11/3.12, poetry, preâ€‘commit.  
- Extend Taskfile/Makefile targets for common tasks.  
- Autoâ€‘labeler, PR title lint, and conventional commits.



#### Scope
- Production hardening: performance profiling, load testing, reliability and DR readiness

#### Deliverables
- Load and soak test plans and scripts (scripts/perf, k6 or locust)
- Resource limits/requests and autoscaling policies finalized
- Backup, restore and DR runbooks validated; recovery objectives documented
- Chaos experiments in staging for failure modes

#### Milestones
- Baseline load passes within SLOs; no error budget burn-up under target load
- DR restore test completed and documented

#### Dependencies
- Staging environment representative of production
- Access to storage/backup services and monitoring data

#### Risks & Mitigations
- Underestimated capacity leading to throttling | Mitigation: capacity model and autoscale tests
- DR procedures untested | Mitigation: game days with timed restores
**Acceptance**
- New contributor can run tests, start stack, and PR in <30 minutes.

**Deliverables** â€” .devcontainer or setup docs; Taskfile; PR automation.  
**Effort/Deps** â€” 1 day; Phase 3 first.

---

### Phase 12 â€” Governance & Roadmap (Day 21)

**Goal:** keep improvements sustainable.  
**Why:** ongoing clarity.

**Tasks**
- `/docs/roadmap.md` for the next minor releases.  
- Required reviewers via CODEOWNERS; review SLAs.  
- GitHub Project board with swimlanes: security, observability, contracts, releases.



#### Scope
- Program closeout, handover and forward roadmap with cost optimization opportunities

#### Deliverables
- ROADMAP.md for next phases and backlog issues created
- Release calendar and change management process documented
- Knowledge transfer sessions and training materials for operations

#### Milestones
- Handover completed; owners and SLAs recorded
- Kickoff scheduled for next minor release

#### Dependencies
- Stakeholder availability for reviews and sign-off
- Documentation completeness from prior phases

#### Risks & Mitigations
- Knowledge gaps after handover | Mitigation: recorded sessions and shadowing period
- Scope creep into new work | Mitigation: freeze criteria and backlog triage
**Acceptance**
- Board populated with epics/issues for next 2 sprints.

**Deliverables** â€” roadmap + project board.  
**Effort/Deps** â€” 0.5 day; after Phase 6.

---

## Suggested Timeline (Aggressive: ~3 weeks)

- **Week 1:** Phases 0â€“3, start 4 & 5 (+ 2A in parallel).  
- **Week 2:** Finish 4â€“5; Phase 6 release; Phase 7; start 5A.  
- **Week 3:** Phases 7A, 8â€“11; Phase 12 wrapâ€‘up.

---

## Acceptance Criteria Summary (Updated)

- **Releases:** Signed GHCR images + SBOMs; versioned `v0.1.0` and later; recovery docs linked.  
- **Security:** CodeQL/Dependabot/secret scanning active; no `:latest`; digests pinned.  
- **Quality Gates:** CI blocks merges on lint/type/unit/contract/integration **and compliance rules**.  
- **Contracts:** JSON Schemas canonical; Python & MQL4 generated/validated; roundâ€‘trips tested.  
- **Observability:** Metrics/logs/traces present; dashboards/alerts operational; SLOs measurable.  
- **Compliance:** Live dashboards; autoâ€‘remediation; emergency recovery runbooks verified.  
- **Deployability:** Helm charts lint & dryâ€‘run; runbooks documented.  
- **Correctness:** Idempotent execution; scenario tests green.  
- **DX:** Preâ€‘commit + Taskfile streamline contributor flow.

---

*Integrated on: 2025-09-10 (America/Chicago)*

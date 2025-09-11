
# CycleSync – Technical Specification Document (Patched)

**Version**: v1.1  
**Date**: 2025-08-13  
**Author**: Agentic AI Orchestrator  
**Purpose**: Deliver a complete, respectful, consent-first menstrual cycle awareness application designed for male users to track and support women in their lives.

---

## 📘 Table of Contents

1. [Project Overview](#project-overview)  
2. [System Architecture](#system-architecture)  
3. [Data Models](#data-models)  
4. [Backend Specification](#backend-specification)  
5. [Mobile App Specification](#mobile-app-specification)  
6. [Consent & Privacy Engine](#consent--privacy-engine)  
7. [Tips & Intelligence Engine](#tips--intelligence-engine)  
8. [Third-Party Sync Integration](#third-party-sync-integration)  
9. [Deployment Infrastructure](#deployment-infrastructure)  
10. [Testing & QA](#testing--qa)  
11. [Release Strategy](#release-strategy)

---

## 🧭 Project Overview

CycleSync is a cross-platform mobile and web application enabling men to:
- Track menstrual cycles of women in their lives (with consent)
- Predict cycle phases and moods
- Receive supportive tips
- Respect privacy, boundaries, and data ethics

**Target Users:** Male partners, fathers, friends, and respectful colleagues  
**Core Value:** Empathy through information and consent  

---

## 🏗 System Architecture

```plaintext
+-------------------+       +-------------------------+
|   Mobile App UI   | <-->  |    RESTful API Server   |
+-------------------+       +-------------------------+
        |                            |
        v                            v
+-------------------+       +-------------------------+
|     Auth Layer    |       |     Cycle Calculator    |
| (JWT / Firebase)  |       |     + Tip Engine        |
+-------------------+       +-------------------------+
        |                            |
        v                            v
+-------------------+       +-------------------------+
| Encrypted Database|       | Notification Scheduler  |
|   PostgreSQL      |       |  (FCM / APNs)           |
+-------------------+       +-------------------------+
                                |
                                v
                        +-------------------------+
                        | Async Job Queue (Redis) |
                        +-------------------------+
```

---

## 📦 Data Models

### User
```python
User:
  id: UUID
  email: str
  password_hash: str
  created_at: datetime
```

### PartnerProfile
```python
PartnerProfile:
  id: UUID
  user_id: UUID
  name: str
  relationship: enum
  consent_status: bool
  cycle_length: int
  last_period_start: date
  sync_source: Optional[str]
```

### CycleEvent
```python
CycleEvent:
  id: UUID
  partner_id: UUID
  date: date
  type: enum('period_start', 'symptom', 'note')
  note: Optional[str]
```

### ConsentToken
```python
ConsentToken:
  id: UUID
  partner_id: UUID
  user_id: UUID
  permissions: List[str]
  issued_at: datetime
  revoked: bool
```

### SyncLog
```python
SyncLog:
  id: UUID
  partner_id: UUID
  source: str
  status: enum('pending', 'success', 'failed')
  timestamp: datetime
```

---

## 🔧 Backend Specification

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy
- **Auth**: OAuth2 / Firebase JWT
- **Rate Limiting**: Redis-based token bucket per user
- **Versioning**: Prefix routes with `/api/v1/...`
- **APIs**:
  - `POST /auth/login`
  - `POST /partners`
  - `GET /partners/:id/cycle`
  - `GET /tips/:phase`
  - `POST /events`
  - `DELETE /partners/:id/consent`
- **CI/CD**: GitHub Actions for linting, tests, staging deployments

---

## 📱 Mobile App Specification

- **Framework**: Flutter (iOS + Android)
- **State Mgmt**: Riverpod
- **Networking**: `dio`
- **Screens**:
  - Home
  - Add Partner (QR / Invite Link)
  - Partner Details
  - Cycle Calendar View
  - Tips and Gestures
  - Settings + Consent View
- **Notifications**: FCM for cloud and local alerts
- **Fallback**: Responsive web app (Flutter Web)

---

## 🔐 Consent & Privacy Engine

- Consent-based token required to create/view profiles
- Revoking consent invalidates:
  - Future syncing
  - Tip display
  - Data access by user
- Consent UI shows scope + revocation
- Audit logging per access
- Data retention policy: partner data is purged 30 days post-consent revocation

---

## 💡 Tips & Intelligence Engine

- **Phase → Energy Mapping** (rule-based)
- **Static Tips** (fallback/MVP)
- **LLM Tips** (optional with opt-in toggle)
  - GPT-4 or Claude prompt structure provided
  - Tips cached by phase to reduce cost

---

## 🔄 Third-Party Sync Integration

- Flo, Clue via OAuth2
- HealthKit via Apple API (iOS-only)
- Sync polling + webhook support
- Sync retry: exponential backoff on failure
- Status tracked in `SyncLog`

---

## ☁️ Deployment Infrastructure

| Component     | Stack                      |
|---------------|----------------------------|
| API Backend   | FastAPI on Render or AWS   |
| DB            | PostgreSQL (Supabase)      |
| Secrets Mgmt  | Firebase + `.env`          |
| CI/CD         | GitHub Actions             |
| Monitoring    | Sentry (errors) + PostHog  |
| Infra-as-Code | Terraform / Pulumi         |
| Queue System  | Redis for background jobs  |
| Observability | Grafana dashboard          |

---

## 🧪 Testing & QA

- Unit + integration test suite:
  - Pytest (backend)
  - Flutter test (mobile)
- Edge Cases:
  - Consent denial
  - Revocation in mid-sync
  - Partner profile deletion
- CI gating: All commits require test pass and lint pass

---

## 🚀 Release Strategy

- iOS TestFlight + Google Play Beta
- Screenshots and demo for App Stores
- Feature flags for experimental modules (LLM tips, sync polling)
- Privacy Policy, Terms of Service linked on signup
- Launch blog post + video + social

---

## 🔁 Post-Launch Operations

- Claude-based Self-Optimizer agent generates weekly feedback reports
- Auto-opens GitHub issues for:
  - Feature requests
  - Abandoned partners
  - Tips performance
- Monthly roadmap review

---

## ✅ Status: Enterprise Build Spec Approved
This patched version includes:
- Full backend scaffolding
- Privacy-ready data model
- AI-ready tips engine
- Scalable consent model
- Sync strategy and audit integrity

---

## 🔚 End of Document

# CycleSync Technical Spec — v1.2 Addendum (Agentic DevOps Integration)

This addendum describes **non-invasive** integrations to adopt a **parallel, agentic CLI workflow** while keeping CycleSync's core intact.

## A. Objectives
- Enable parallel development with **Claude Code, Aider, Cline, Gemini CLI, ChatGPT Agent**, and **GitHub Copilot**.
- Maintain **tight version control** via branches, worktrees, pre-commit, and merge queue.
- Ensure **repeatability** with a declarative job manifest and CI policies.

## B. New Operational Files (Repo Root)
- `.ai/workflows/agent_jobs.yaml` — Declarative jobs (tool, branch, worktree, tests).
- `.ai/scripts/orchestrate.ps1` — Orchestrates rebase → tool run → tests → auto-commit/push.
- `.vscode/tasks.json` — VS Code tasks to launch jobs in parallel.
- `.gitmessage.txt` — Enforced commit trailers (`Tool:`, `Job:`).
- `.github/workflows/ci.yml` — Pre-commit, tests, coverage as required checks.

## C. Branch & Worktree Conventions
- One **branch/worktree per job**: `feat/ui-aider`, `fix/api-cline`, `refactor/core-claude`.
- All agents run inside their worktree to avoid collisions.
- Commits are **atomic** and **signed**; merge via **queue** only.

## D. Quality Gates
- **Pre-commit**: format, lint, type check, secrets scan.
- **CI**: repeat the same checks; enforce coverage threshold.
- **Commit policy**: commit on green tests (or time-boxed WIP with label).

## E. Integration Points with CycleSync
- **Build/Test Hooks**: orchestrator invokes CycleSync’s existing test commands.
- **Docs/Specs**: ChatGPT/Gemini generate ADRs & specs → committed to `docs/` via dedicated generator branches.
- **Artifacts**: Any generated files managed by a single `gen/*` branch to avoid conflicts.

## F. Rollback & Safety
- Cline snapshots workspace; Git handles reverts.
- Feature flags guard risky changes; gradual rollout via PRs.

## G. Next Steps
1. Add files in Section B.
2. Configure branch protection & merge queue on `main`.
3. Start with 2–3 jobs in parallel and expand as stable.

---
doc_id: DOC-CONFIG-0080
---

# Change Management Process

Defines how changes are proposed, approved, and released.

## Proposal
- Use PR templates; link issues and risk notes.

## Approval
- Required reviewers: code owner + on-call rep (if operational impact).
- Security review for sensitive changes.

## Release
- Follow release calendar; respect freeze windows.
- Ensure smoke tests and health checks pass post-deploy.

## Rollback
- Criteria for rollback; documented playbooks per service.


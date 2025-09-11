# Backup and Restore Runbook

Purpose: Ensure data can be backed up and restored within RTO/RPO targets.

## Scope
- Persistent stores (e.g., Postgres, Redis snapshots, object storage artifacts)
- Configuration backups (Helm values, secrets references)

## Procedures
1. Backup
   - Trigger scheduled backups; verify completion and retention.
   - Store metadata (timestamp, version, checksum) in backup index.
2. Restore (Drill)
   - Provision clean environment (namespace or cluster).
   - Restore from latest backup; validate integrity and version compatibility.
   - Run smoke tests and contract tests.

## Validation Checklist
- [ ] Backup artifacts present and accessible
- [ ] Checksums verified
- [ ] Restore completes within RTO
- [ ] Data recency within RPO
- [ ] Post-restore health checks pass

## Evidence
- Link to drill logs, timestamps, and outcomes.


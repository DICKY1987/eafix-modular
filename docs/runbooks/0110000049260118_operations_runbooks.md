---
doc_id: DOC-CONFIG-0054
---

# EAFIX Operations Runbooks

## Table of Contents

1. [Deployment Procedures](#deployment-procedures)
2. [Monitoring and Alerting](#monitoring-and-alerting)
3. [Troubleshooting Guide](#troubleshooting-guide)
4. [Disaster Recovery](#disaster-recovery)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Security Incident Response](#security-incident-response)

---

## Deployment Procedures

### Prerequisites Checklist

Before any deployment, ensure:

- [ ] All tests pass in CI/CD pipeline
- [ ] Security scans show no critical vulnerabilities
- [ ] Database migrations are prepared and tested
- [ ] Rollback plan is documented and tested
- [ ] Stakeholders are notified of deployment window
- [ ] Monitoring dashboards are ready
- [ ] Support team is available during deployment

### Production Deployment Process

#### Step 1: Pre-Deployment Preparation

```bash
# 1. Verify environment
eafix-cli doctor --environment=production

# 2. Check current system status
eafix-cli status --verbose

# 3. Create deployment backup
kubectl create backup eafix-backup-$(date +%Y%m%d-%H%M%S)

# 4. Verify backup integrity
kubectl verify backup eafix-backup-$(date +%Y%m%d-%H%M%S)
```

#### Step 2: Database Migration (if required)

```bash
# 1. Put system in maintenance mode
eafix-cli maintenance enable --message="System maintenance in progress"

# 2. Stop trading activities
eafix-cli trading stop --graceful

# 3. Run database migrations
alembic upgrade head

# 4. Verify migration success
eafix-cli database verify
```

#### Step 3: Blue-Green Deployment

```bash
# 1. Deploy to green environment
kubectl apply -f deploy/kubernetes/green/

# 2. Wait for green environment to be ready
kubectl wait --for=condition=ready pod -l version=green --timeout=300s

# 3. Run smoke tests against green
eafix-cli test smoke --environment=green

# 4. Switch traffic to green (zero-downtime)
kubectl patch service eafix-gateway -p '{"spec":{"selector":{"version":"green"}}}'

# 5. Monitor for 5 minutes
eafix-cli monitor --duration=5m --environment=green

# 6. If successful, scale down blue environment
kubectl scale deployment eafix-blue --replicas=0
```

#### Step 4: Post-Deployment Verification

```bash
# 1. Run full health checks
eafix-cli health-check --comprehensive

# 2. Verify trading functionality
eafix-cli test trading --environment=production

# 3. Check monitoring dashboards
eafix-cli dashboard verify

# 4. Re-enable trading
eafix-cli trading start

# 5. Disable maintenance mode
eafix-cli maintenance disable
```

### Rollback Procedures

#### Immediate Rollback (Emergency)

```bash
# 1. Switch traffic back to blue environment
kubectl patch service eafix-gateway -p '{"spec":{"selector":{"version":"blue"}}}'

# 2. Scale up blue environment if needed
kubectl scale deployment eafix-blue --replicas=3

# 3. Verify rollback success
eafix-cli status --environment=production

# 4. Document incident
eafix-cli incident create --title="Emergency rollback" --severity=high
```

#### Database Rollback

```bash
# 1. Stop all services
eafix-cli services stop --all

# 2. Restore database from backup
kubectl restore backup eafix-backup-YYYYMMDD-HHMMSS

# 3. Verify database integrity
eafix-cli database verify

# 4. Restart services with previous version
kubectl apply -f deploy/kubernetes/blue/
```

---

## Monitoring and Alerting

### Key Performance Indicators (KPIs)

#### System Health Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| API Response Time | < 100ms | > 200ms | > 500ms |
| Error Rate | < 0.1% | > 1% | > 5% |
| CPU Usage | < 70% | > 80% | > 90% |
| Memory Usage | < 80% | > 85% | > 95% |
| Disk Usage | < 80% | > 85% | > 95% |

#### Trading Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Signal Generation Latency | < 50ms | > 100ms | > 200ms |
| Order Execution Time | < 500ms | > 1s | > 2s |
| Data Feed Latency | < 10ms | > 50ms | > 100ms |
| Risk Check Time | < 100ms | > 200ms | > 500ms |

### Alert Configuration

#### Critical Alerts (Page Immediately)

```yaml
# High Severity - Page Immediately
alerts:
  - name: service_down
    condition: up == 0
    duration: 30s
    severity: critical
    
  - name: high_error_rate
    condition: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    duration: 2m
    severity: critical
    
  - name: trading_system_failure
    condition: trading_orders_failed_total > 5
    duration: 1m
    severity: critical

  - name: data_feed_failure
    condition: market_data_age_seconds > 60
    duration: 30s
    severity: critical
```

#### Warning Alerts (Investigate Soon)

```yaml
# Medium Severity - Investigate Soon
alerts:
  - name: high_response_time
    condition: histogram_quantile(0.95, http_request_duration_seconds) > 0.5
    duration: 5m
    severity: warning
    
  - name: high_cpu_usage
    condition: cpu_usage_percent > 80
    duration: 10m
    severity: warning
    
  - name: disk_space_low
    condition: disk_free_percent < 20
    duration: 5m
    severity: warning
```

### Monitoring Dashboard Setup

#### Grafana Dashboard Configuration

```bash
# Import EAFIX dashboards
grafana-cli admin import-dashboard \
  --file=monitoring/dashboards/eafix-system-overview.json

grafana-cli admin import-dashboard \
  --file=monitoring/dashboards/eafix-trading-metrics.json

grafana-cli admin import-dashboard \
  --file=monitoring/dashboards/eafix-performance.json
```

#### Essential Monitoring Views

1. **System Overview Dashboard**
   - Service health status grid
   - Request rate and latency trends
   - Error rate by service
   - Resource utilization (CPU, Memory, Disk)

2. **Trading Dashboard**
   - Active positions summary
   - Order execution metrics
   - P&L tracking
   - Risk metrics real-time view

3. **Performance Dashboard**
   - Response time percentiles
   - Throughput metrics
   - Database performance
   - Cache hit rates

---

## Troubleshooting Guide

### Common Issues and Resolution

#### Issue: Service Not Responding

**Symptoms:**
- HTTP 503 errors
- Health check failures
- Timeout errors

**Diagnosis Steps:**
```bash
# 1. Check service status
kubectl get pods -l app=eafix-service-name

# 2. Check service logs
kubectl logs -f deployment/eafix-service-name --tail=100

# 3. Check resource usage
kubectl top pods -l app=eafix-service-name

# 4. Check service dependencies
eafix-cli dependencies check --service=service-name
```

**Resolution:**
```bash
# If resource exhaustion:
kubectl scale deployment eafix-service-name --replicas=3

# If configuration issue:
kubectl edit configmap eafix-service-name-config

# If corrupt state:
kubectl delete pod -l app=eafix-service-name  # Force restart
```

#### Issue: High API Latency

**Symptoms:**
- Slow response times (> 500ms)
- Request queue buildup
- User complaints about system slowness

**Diagnosis Steps:**
```bash
# 1. Check current latency metrics
eafix-cli metrics query 'histogram_quantile(0.95, http_request_duration_seconds)'

# 2. Identify slow endpoints
eafix-cli metrics query 'rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])'

# 3. Check database performance
eafix-cli database performance

# 4. Check cache hit rates
eafix-cli metrics query 'redis_cache_hit_rate'
```

**Resolution:**
```bash
# Scale up affected services
kubectl scale deployment eafix-slow-service --replicas=5

# Optimize database queries
eafix-cli database optimize --analyze

# Clear cache if needed
eafix-cli cache clear --pattern="slow_query_*"

# Enable request throttling
kubectl patch deployment eafix-gateway --patch='{"spec":{"template":{"spec":{"containers":[{"name":"gateway","env":[{"name":"RATE_LIMIT","value":"1000"}]}]}}}}'
```

#### Issue: Trading Orders Failing

**Symptoms:**
- Order rejection errors
- Broker connection failures
- Risk management blocks

**Diagnosis Steps:**
```bash
# 1. Check broker connectivity
eafix-cli broker status --all

# 2. Check risk manager status
eafix-cli risk status

# 3. Review recent failed orders
eafix-cli orders list --status=failed --limit=20

# 4. Check account balances
eafix-cli account balance --all
```

**Resolution:**
```bash
# Reconnect to broker
eafix-cli broker reconnect --broker=mt4_live

# Reset risk limits if needed
eafix-cli risk limits reset --confirm

# Clear stuck orders
eafix-cli orders cleanup --stuck

# Restart execution engine
kubectl rollout restart deployment/eafix-execution-engine
```

#### Issue: Data Feed Interruption

**Symptoms:**
- Stale market data warnings
- No new price updates
- Trading signals not generating

**Diagnosis Steps:**
```bash
# 1. Check data feed status
eafix-cli data-feed status

# 2. Check last data timestamp
eafix-cli data latest --symbol=EURUSD

# 3. Test data provider connection
eafix-cli data-feed test --provider=all

# 4. Check ingestion service logs
kubectl logs deployment/eafix-data-ingestor --since=10m
```

**Resolution:**
```bash
# Restart data feed connections
eafix-cli data-feed restart --provider=primary

# Switch to backup data provider
eafix-cli data-feed switch --to=backup

# Clear data cache
eafix-cli cache clear --pattern="market_data_*"

# Restart data ingestor
kubectl rollout restart deployment/eafix-data-ingestor
```

### Escalation Procedures

#### Level 1: Self-Service (0-15 minutes)
- Check monitoring dashboards
- Review recent deployments
- Run basic diagnostic commands
- Attempt standard remediation steps

#### Level 2: On-Call Engineer (15-30 minutes)
- Page on-call engineer via PagerDuty
- Provide incident details and steps taken
- Collaborate on advanced troubleshooting
- Consider rollback if recent deployment

#### Level 3: Senior Engineering (30+ minutes)
- Escalate to senior engineering team
- Consider emergency maintenance window
- Engage vendor support if needed
- Implement temporary workarounds

---

## Disaster Recovery

### Backup Strategy

#### Automated Backups

```bash
# Daily full backups
0 2 * * * /scripts/backup-full.sh

# Hourly incremental backups during trading hours
0 9-17 * * 1-5 /scripts/backup-incremental.sh

# Real-time transaction log backups
*/5 * * * * /scripts/backup-transaction-log.sh
```

#### Backup Verification

```bash
# Daily backup verification
#!/bin/bash
BACKUP_DATE=$(date +%Y%m%d)
BACKUP_FILE="/backups/eafix-full-${BACKUP_DATE}.tar.gz"

# Test backup integrity
if tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "✓ Backup integrity verified"
    # Test restore to staging environment
    kubectl create namespace eafix-restore-test
    restore-test.sh "$BACKUP_FILE" eafix-restore-test
else
    echo "✗ Backup integrity check failed"
    alert-send.sh "CRITICAL: Backup integrity check failed for $BACKUP_DATE"
fi
```

### Recovery Time Objectives (RTO)

| Disaster Type | RTO Target | RPO Target |
|---------------|------------|------------|
| Service Failure | 5 minutes | 0 (real-time replication) |
| Database Corruption | 30 minutes | 5 minutes |
| Data Center Outage | 2 hours | 15 minutes |
| Complete Infrastructure Loss | 8 hours | 1 hour |

### Disaster Recovery Procedures

#### Scenario 1: Primary Database Failure

```bash
# 1. Detect failure
if ! eafix-cli database ping --timeout=5; then
    echo "Database failure detected"
    
    # 2. Promote read replica to primary
    kubectl patch statefulset eafix-postgres-replica \
        --patch='{"spec":{"template":{"spec":{"containers":[{"name":"postgres","env":[{"name":"POSTGRES_ROLE","value":"primary"}]}]}}}}'
    
    # 3. Update service endpoints
    kubectl patch service eafix-postgres \
        --patch='{"spec":{"selector":{"role":"primary"}}}'
    
    # 4. Verify recovery
    eafix-cli database verify --full-check
    
    # 5. Restart dependent services
    kubectl rollout restart deployment/eafix-data-ingestor
    kubectl rollout restart deployment/eafix-portfolio-manager
fi
```

#### Scenario 2: Complete Data Center Outage

```bash
# 1. Activate secondary data center
./scripts/activate-dr-site.sh

# 2. Restore from latest backup
restore-from-backup.sh --latest --site=dr

# 3. Update DNS to point to DR site
aws route53 change-resource-record-sets \
    --hosted-zone-id Z123456789 \
    --change-batch file://dns-failover.json

# 4. Verify all services
eafix-cli doctor --environment=dr

# 5. Enable trading on DR site
eafix-cli trading enable --site=dr --confirm-dr
```

### Recovery Testing

#### Monthly DR Drills

```bash
#!/bin/bash
# Monthly disaster recovery drill
echo "Starting DR drill: $(date)"

# 1. Create isolated DR environment
kubectl create namespace eafix-dr-drill

# 2. Restore from backup
restore-from-backup.sh --target=eafix-dr-drill

# 3. Run integration tests
eafix-cli test integration --namespace=eafix-dr-drill

# 4. Measure recovery time
RECOVERY_TIME=$(calculate-recovery-time.sh)
echo "Recovery completed in: $RECOVERY_TIME"

# 5. Document results
echo "DR Drill Results: $RECOVERY_TIME" >> /logs/dr-drill-results.log

# 6. Cleanup
kubectl delete namespace eafix-dr-drill
```

---

## Maintenance Procedures

### Scheduled Maintenance Windows

#### Weekly Maintenance (Sundays 02:00-04:00 UTC)

```bash
#!/bin/bash
# Weekly maintenance routine

echo "Starting weekly maintenance: $(date)"

# 1. Enable maintenance mode
eafix-cli maintenance enable --scheduled

# 2. Database maintenance
eafix-cli database vacuum --analyze
eafix-cli database reindex --critical-only

# 3. Clear old logs and metrics
eafix-cli logs cleanup --older-than=30d
prometheus-cleanup.sh --retention=30d

# 4. Update system packages (non-critical)
kubectl apply -f maintenance/security-patches.yaml

# 5. Verify system health
eafix-cli doctor --comprehensive

# 6. Disable maintenance mode
eafix-cli maintenance disable

echo "Weekly maintenance completed: $(date)"
```

#### Monthly Maintenance (First Sunday 01:00-05:00 UTC)

```bash
#!/bin/bash
# Monthly comprehensive maintenance

# 1. Full system backup
backup-full.sh --verify

# 2. Database optimization
eafix-cli database optimize --full

# 3. Certificate renewal check
cert-manager-check.sh --renew-if-needed

# 4. Security updates
kubectl apply -f maintenance/security-updates.yaml

# 5. Performance benchmarking
eafix-cli benchmark run --save-results

# 6. Capacity planning review
eafix-cli capacity analyze --generate-report
```

### Configuration Changes

#### Standard Configuration Change Process

1. **Preparation**
   ```bash
   # Create configuration branch
   git checkout -b config/update-risk-limits
   
   # Update configuration files
   vim config/production/risk-manager.yaml
   
   # Validate configuration
   eafix-cli config validate --file=config/production/risk-manager.yaml
   ```

2. **Testing**
   ```bash
   # Deploy to staging
   kubectl apply -f config/production/risk-manager.yaml --namespace=staging
   
   # Run configuration tests
   eafix-cli test config --namespace=staging
   ```

3. **Deployment**
   ```bash
   # Create change ticket
   eafix-cli change-request create --config-change
   
   # Deploy to production
   kubectl apply -f config/production/risk-manager.yaml
   
   # Verify configuration applied
   eafix-cli config verify --service=risk-manager
   ```

---

## Security Incident Response

### Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| Critical | Active security breach | 15 minutes | Unauthorized access, data theft |
| High | Potential security threat | 1 hour | Failed login attempts, suspicious activity |
| Medium | Security policy violation | 4 hours | Policy non-compliance, weak passwords |
| Low | Security awareness issue | 24 hours | Phishing attempts, training issues |

### Incident Response Procedures

#### Phase 1: Detection and Analysis (0-30 minutes)

```bash
# 1. Identify incident type
eafix-cli security analyze --incident-id=$INCIDENT_ID

# 2. Collect evidence
kubectl logs deployment/eafix-auth-service --since=1h > /tmp/auth-logs.txt
eafix-cli audit export --since=1h --format=json > /tmp/audit-trail.json

# 3. Assess impact
eafix-cli security impact-assessment --incident-id=$INCIDENT_ID

# 4. Document incident
eafix-cli incident create --type=security --severity=high --description="$DESCRIPTION"
```

#### Phase 2: Containment (30-60 minutes)

```bash
# 1. Isolate affected systems
kubectl patch deployment eafix-affected-service --patch='{"spec":{"replicas":0}}'

# 2. Revoke compromised credentials
eafix-cli auth revoke --user-id=$COMPROMISED_USER
eafix-cli tokens revoke --pattern="compromised_*"

# 3. Block suspicious IP addresses
kubectl apply -f security/block-ips.yaml

# 4. Enable enhanced monitoring
eafix-cli monitoring enhance --security-mode
```

#### Phase 3: Eradication (1-4 hours)

```bash
# 1. Remove malicious artifacts
eafix-cli security scan --remove-threats

# 2. Patch vulnerabilities
kubectl apply -f security/patches/

# 3. Update security policies
kubectl apply -f security/enhanced-policies.yaml

# 4. Reset compromised accounts
eafix-cli auth reset --compromised-accounts
```

#### Phase 4: Recovery (4-24 hours)

```bash
# 1. Restore services gradually
kubectl scale deployment eafix-affected-service --replicas=1
# Wait and verify before scaling up
kubectl scale deployment eafix-affected-service --replicas=3

# 2. Verify security measures
eafix-cli security verify --comprehensive

# 3. Resume normal operations
eafix-cli maintenance disable --security-incident

# 4. Monitor for recurring issues
eafix-cli monitoring watch --security-focus --duration=24h
```

#### Phase 5: Lessons Learned (24-48 hours)

```bash
# 1. Generate incident report
eafix-cli incident report --incident-id=$INCIDENT_ID --format=pdf

# 2. Conduct post-mortem
eafix-cli postmortem create --incident-id=$INCIDENT_ID

# 3. Update security procedures
git commit -m "Update security procedures based on incident $INCIDENT_ID"

# 4. Schedule security training
eafix-cli training schedule --type=security --mandatory
```

### Security Monitoring

#### Real-time Security Alerts

```yaml
# security-alerts.yaml
alerts:
  - name: brute_force_attack
    condition: rate(failed_login_attempts[5m]) > 10
    action: block_ip_and_notify
    
  - name: privilege_escalation
    condition: unauthorized_admin_access == 1
    action: immediate_lockout
    
  - name: data_exfiltration
    condition: unusual_data_transfer > threshold
    action: quarantine_and_investigate
    
  - name: malware_detected
    condition: security_scan_threats > 0
    action: isolate_and_remediate
```

#### Daily Security Checklist

```bash
#!/bin/bash
# Daily security verification

echo "Daily Security Check: $(date)"

# 1. Check for failed login attempts
FAILED_LOGINS=$(eafix-cli audit query "event_type=login_failed" --count --since=24h)
echo "Failed logins (24h): $FAILED_LOGINS"

# 2. Verify certificate status
eafix-cli certificates check --expiring-within=30d

# 3. Check for security updates
eafix-cli security updates --check-only

# 4. Verify backup encryption
eafix-cli backup verify-encryption --latest

# 5. Review access logs
eafix-cli audit review --suspicious-only --since=24h

# 6. Check intrusion detection
eafix-cli security ids-status

echo "Daily security check completed: $(date)"
```

### Emergency Contacts

#### Security Incident Escalation

1. **Security Team Lead**: +1-555-SEC-TEAM
2. **CISO**: +1-555-CISO-123
3. **Legal Counsel**: +1-555-LEGAL-01
4. **External Security Firm**: +1-555-EXT-SEC

#### Notification Templates

```bash
# Critical Security Alert Template
SUBJECT="CRITICAL: Security Incident - $INCIDENT_TYPE"
BODY="
Incident ID: $INCIDENT_ID
Severity: Critical
Type: $INCIDENT_TYPE
Time: $(date)
Affected Systems: $AFFECTED_SYSTEMS
Current Status: $STATUS
Response Team: $RESPONSE_TEAM
Next Update: In 30 minutes
"
```

---

## Performance Optimization

### Regular Performance Reviews

#### Weekly Performance Analysis

```bash
#!/bin/bash
# Weekly performance review

echo "Weekly Performance Report: $(date)"

# 1. API response time analysis
eafix-cli metrics report --metric=response_time --period=7d

# 2. Database performance review
eafix-cli database performance-report --period=7d

# 3. Resource utilization trends
eafix-cli resources report --period=7d

# 4. Trading system performance
eafix-cli trading performance-report --period=7d

# 5. Generate optimization recommendations
eafix-cli optimize recommend --based-on=7d-data
```

### Capacity Planning

#### Monthly Capacity Review

```bash
# Capacity planning and forecasting
eafix-cli capacity plan --forecast=3m --based-on=historical-data

# Resource scaling recommendations
eafix-cli scaling recommend --services=all --timeframe=30d

# Cost optimization analysis
eafix-cli cost analyze --optimization-opportunities
```

This comprehensive operations runbook provides the foundation for maintaining a robust, secure, and highly available EAFIX trading system. Regular review and updates of these procedures ensure they remain current with system evolution and operational experience.
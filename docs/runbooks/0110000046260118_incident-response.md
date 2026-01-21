---
doc_id: DOC-CONFIG-0088
---

# Incident Response Runbook

## 🚨 Emergency Response Overview

This runbook provides the primary incident response procedures for the EAFIX trading system. Follow these procedures for any system incident that impacts trading operations or system availability.

## 📞 Immediate Actions (0-5 minutes)

### 1. Alert Acknowledgment
```bash
# Acknowledge PagerDuty alert
# - Log into PagerDuty dashboard
# - Acknowledge the incident
# - Set status to "Investigating"
```

### 2. Initial Assessment
**Questions to answer immediately:**
- Is trading currently active? (Check market hours)
- Are positions at risk? (Check open positions)
- Is data flowing? (Check recent price updates)
- Are orders executing? (Check recent order activity)

### 3. Safety Measures
```bash
# If trading must be stopped immediately
curl -X POST http://localhost:8080/emergency/stop-trading

# If specific service must be isolated
docker compose stop <service-name>

# Check system status
make smoke
```

## 🔍 Triage Phase (5-15 minutes)

### Incident Classification
Classify incident severity:

**P0 - Critical** (Page immediately, all hands)
- Complete system outage during market hours
- Data corruption affecting positions
- Security breach with active exploitation
- Risk management system failure

**P1 - High** (Page immediately, dev team)
- Partial system outage affecting trading
- Significant latency increase (>5s for signals)
- Position reconciliation failure
- Market data feed interruption

**P2 - Medium** (Page during business hours)
- Individual service outage (non-critical path)
- Performance degradation (<5s latency)
- Data quality issues
- Monitoring system issues

**P3 - Low** (Handle during business hours)
- Minor feature issues
- Cosmetic problems
- Documentation issues

### Initial Diagnosis
```bash
# 1. Check service health status
curl http://localhost:8080/health | jq .

# 2. Check Docker container status
docker compose ps

# 3. Check recent logs for errors
docker compose logs --tail=100 --since=15m | grep -i error

# 4. Check system resources
docker stats --no-stream

# 5. Check database connectivity
psql -h localhost -p 5432 -U eafix -d eafix_prod -c "SELECT now();"

# 6. Check Redis connectivity
redis-cli ping
```

### Immediate Containment
Based on initial findings:

**Service Failure:**
```bash
# Restart specific service
docker compose restart <service-name>

# Check service logs
docker compose logs <service-name> --tail=50
```

**Database Issues:**
```bash
# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size and locks
psql -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

**Network/Connectivity:**
```bash
# Test internal connectivity
docker exec <container> ping <target-container>

# Check external connectivity
curl -I https://api.external-broker.com/
```

## 📊 Investigation Phase (15-60 minutes)

### Data Collection
```bash
# 1. Collect system snapshots
docker compose logs --since=1h > incident_logs_$(date +%Y%m%d_%H%M%S).txt

# 2. Export metrics (if Prometheus available)
curl http://localhost:9090/api/v1/query_range?query=up&start=$(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%SZ)&end=$(date -u +%Y-%m-%dT%H:%M:%SZ)&step=60s

# 3. Database performance snapshot
psql -c "\x" -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# 4. Check recent deployments
git log --oneline --since="24 hours ago"
```

### Trading Impact Assessment
```bash
# Check recent trading activity
curl http://localhost:8080/api/positions | jq '.[] | select(.status == "open")'

# Check recent signals
curl http://localhost:8083/api/signals?since=1h

# Check recent executions
curl http://localhost:8085/api/executions?since=1h

# Verify position reconciliation
curl http://localhost:8080/api/reconcile/positions
```

### Root Cause Analysis
Follow these investigation paths:

**Performance Issues:**
1. Check resource utilization (CPU, memory, disk)
2. Analyze slow queries in database
3. Review message queue depths
4. Check network latency between services

**Data Issues:**
1. Validate data integrity with checksums
2. Check for missing or delayed market data
3. Verify contract schema compliance
4. Review data transformation pipelines

**Service Failures:**
1. Analyze service logs for exceptions
2. Check dependency health
3. Review configuration changes
4. Validate service discovery

## 🛠️ Resolution Phase (60+ minutes)

### Temporary Fixes
Priority order for temporary fixes:
1. **Stop losses** - Prevent further damage
2. **Service restart** - Quick recovery attempt  
3. **Traffic routing** - Bypass failed components
4. **Rollback** - Return to known good state
5. **Manual intervention** - Execute critical functions manually

### Permanent Fixes
```bash
# 1. Code fix deployment
git checkout hotfix/incident-fix
make docker-build
make docker-up

# 2. Configuration changes
# Update environment variables
# Restart affected services
docker compose restart <service-name>

# 3. Infrastructure changes
# Scale services if needed
docker compose up -d --scale <service>=3

# 4. Data repair (if needed)
# Run data integrity scripts
python scripts/data-repair/fix_positions.py --dry-run
```

### Validation
```bash
# 1. Smoke test all critical paths
make smoke

# 2. Contract validation
make contracts-validate-full

# 3. Trading flow test
curl -X POST http://localhost:8081/test/simulate-tick
sleep 2
curl http://localhost:8083/api/signals?limit=1

# 4. Performance test
python scripts/performance/latency-test.py --duration=300
```

## 📋 Communication Protocol

### Internal Communication
**Slack Channels:**
- `#eafix-incidents` - Primary incident channel
- `#eafix-dev` - Development team coordination
- `#trading-operations` - Trading desk notifications

**Status Updates:**
- Initial: Within 15 minutes of incident start
- Progress: Every 30 minutes during active investigation
- Resolution: Immediate notification when resolved

**Update Template:**
```
🚨 INCIDENT UPDATE - [Incident ID]
Status: [Investigating/Identified/Monitoring/Resolved]
Impact: [Service affected, user impact]
Actions: [What's being done]
ETA: [Expected resolution time]
Next Update: [When next update will be provided]
```

### External Communication
**Trading Desk:**
- Immediate notification for P0/P1 incidents during market hours
- Phone call for critical trading impacts
- Email summary within 1 hour of resolution

**Management:**
- P0 incidents: Immediate notification
- P1 incidents: Within 30 minutes
- P2/P3 incidents: Next business day summary

## 📈 Post-Incident Procedures

### Immediate Post-Resolution (0-24 hours)
1. **Monitoring**: Increased monitoring for 24 hours
2. **Documentation**: Complete incident timeline
3. **Preliminary findings**: Initial root cause assessment
4. **Stakeholder notification**: Resolution communication

### Post-Incident Review (1-7 days)
1. **Detailed analysis**: Complete root cause analysis
2. **Timeline review**: Accurate incident timeline
3. **Response evaluation**: Review response effectiveness
4. **Action items**: Identify improvements and fixes

### Long-term Follow-up (1-4 weeks)
1. **Process improvements**: Update runbooks and procedures
2. **System improvements**: Implement preventive measures
3. **Training updates**: Share learnings with team
4. **Monitoring enhancements**: Improve alerting and detection

## 📊 Incident Metrics

### Response Times (Target SLAs)
- **P0**: Acknowledge < 5 minutes, Respond < 15 minutes
- **P1**: Acknowledge < 15 minutes, Respond < 30 minutes  
- **P2**: Acknowledge < 1 hour, Respond < 4 hours
- **P3**: Acknowledge < 4 hours, Respond < 24 hours

### Resolution Times (Target SLAs)
- **P0**: < 2 hours (during market hours)
- **P1**: < 8 hours (during market hours)
- **P2**: < 24 hours
- **P3**: < 5 business days

### Communication SLAs
- Initial update: Within response time SLA
- Progress updates: Every 30 minutes (P0/P1), Every 2 hours (P2/P3)
- Resolution notification: Within 15 minutes of fix

## 🎓 Training & Preparation

### Required Knowledge
- Understanding of EAFIX system architecture
- Familiarity with Docker and container orchestration
- Basic SQL and database troubleshooting
- Linux command line proficiency
- Understanding of trading domain concepts

### Game Day Exercises
- Monthly incident simulation exercises
- Quarterly disaster recovery tests
- Annual business continuity tests
- Regular runbook validation exercises

### Tools and Access
- PagerDuty access for alert management
- Grafana/Prometheus for monitoring
- Docker access for service management
- Database access for data investigation
- Git access for code changes
- Slack for team communication

## 🔧 Troubleshooting Quick Reference

### Common Commands
```bash
# Service health checks
for service in gui-gateway data-ingestor indicator-engine signal-generator risk-manager execution-engine; do
  echo "=== $service ==="
  curl -s http://localhost:808${service#*-}/healthz | jq .status || echo "Failed"
done

# Resource usage
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Error search in logs
docker compose logs --since=30m | grep -E "(ERROR|CRITICAL|Exception)" | tail -20

# Database queries
psql -c "SELECT pid, usename, application_name, state, query_start, query FROM pg_stat_activity WHERE state != 'idle';"
```

### Emergency Contacts
```yaml
Primary On-Call: [Phone/Slack]
Secondary On-Call: [Phone/Slack]
Engineering Manager: [Phone/Email]
Trading Desk: [Phone - Market Hours Only]
Security Team: [24/7 Phone]
CTO: [Phone - P0 Only]
```

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Next Review**: January 2025  
**Approved By**: Platform Engineering Team
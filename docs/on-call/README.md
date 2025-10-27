# On-Call Guide for EAFIX Trading System

## 👋 Welcome to On-Call

This guide provides everything you need to know for effective on-call operations for the EAFIX trading system. Whether you're new to on-call or an experienced engineer, this guide will help you respond effectively to incidents and maintain system reliability.

## 🎯 On-Call Responsibilities

### Primary Responsibilities
- **Incident Response**: Respond to alerts within SLA timeframes
- **System Monitoring**: Proactive monitoring and issue detection
- **Escalation Management**: Proper escalation following established procedures
- **Documentation**: Accurate incident documentation and post-incident reviews
- **Communication**: Clear communication with stakeholders

### Secondary Responsibilities
- **System Maintenance**: Routine maintenance during low-traffic periods
- **Monitoring Improvements**: Identify and address monitoring gaps
- **Runbook Updates**: Keep runbooks current based on operational learnings
- **Knowledge Sharing**: Share insights and learnings with the team

## 📅 On-Call Schedule

### Rotation Schedule
- **Duration**: 1 week rotations (Monday 9 AM to Monday 9 AM)
- **Primary**: First responder for all alerts
- **Secondary**: Backup support, automatic escalation after 15 minutes
- **Rotation**: Team members rotate through primary and secondary roles

### Handoff Procedures
```bash
# Monday handoff checklist
# 1. Review open incidents from previous week
curl http://localhost:8080/api/incidents?status=open

# 2. Check system health
make smoke

# 3. Review recent alerts and trends
python scripts/monitoring/weekly-alert-summary.py

# 4. Update on-call calendar
# 5. Test PagerDuty connectivity
# 6. Review any scheduled maintenance
```

## 📱 On-Call Tools & Access

### Required Tools
- **PagerDuty**: Alert management and escalation
- **Slack**: Team communication and incident coordination
- **VPN**: Secure access to production systems
- **Grafana**: Monitoring dashboards and metrics
- **kubectl**: Kubernetes cluster management
- **Database Access**: Production database read access

### Setup Checklist
```bash
# Verify tool access
- [ ] PagerDuty app installed and notifications enabled
- [ ] Slack notifications configured
- [ ] VPN client configured and tested
- [ ] SSH keys configured for production access
- [ ] kubectl configured for production cluster
- [ ] Database client configured with read-only access
- [ ] Emergency contacts saved in phone
```

### Mobile Setup
- Install PagerDuty mobile app
- Configure high-priority notifications to bypass Do Not Disturb
- Save emergency contacts with "Emergency" prefix
- Test phone reception in your primary locations

## 🚨 Alert Types & Response

### Trading System Alerts

**Service Down (P0)**
```
Alert: ServiceDown - signal-generator
Impact: No trading signals generated
Response: Immediate (2 minutes)
Action: Restart service, escalate if not resolved in 15 minutes
```

**High Error Rate (P1)**
```
Alert: HighErrorRate - execution-engine  
Impact: Orders failing to execute
Response: 5 minutes
Action: Check logs, identify root cause, implement fix
```

**Performance Degradation (P2)**
```
Alert: HighLatency - indicator-engine
Impact: Slow signal generation
Response: 15 minutes  
Action: Check resource usage, optimize if possible
```

### Infrastructure Alerts

**Database Issues (P0/P1)**
```
Alert: DatabaseConnectionFailure
Response: Immediate
Action: Check database health, restart connections, escalate to DBA
```

**Redis Issues (P1)**
```
Alert: RedisConnectionFailure
Response: 5 minutes
Action: Check Redis health, restart if needed, verify message flow
```

## 🔧 Common Response Procedures

### Service Restart Procedure
```bash
# 1. Identify failing service
docker compose ps | grep "unhealthy\|exited"

# 2. Check service logs
docker compose logs <service-name> --tail=50

# 3. Restart service
docker compose restart <service-name>

# 4. Verify health
curl http://localhost:808X/healthz

# 5. Monitor for stability (5 minutes)
watch -n 10 "curl -s http://localhost:808X/healthz | jq .status"
```

### Database Connection Issues
```bash
# 1. Test database connectivity
psql -h prod-db -U eafix -d eafix_prod -c "SELECT now();"

# 2. Check connection pool
psql -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Check for blocking queries
psql -c "SELECT pid, query_start, query FROM pg_stat_activity WHERE state = 'active';"

# 4. Restart application if needed
docker compose restart <affected-services>
```

### Performance Investigation
```bash
# 1. Check resource usage
docker stats --no-stream

# 2. Check recent error logs
docker compose logs --since=30m | grep -i error | tail -20

# 3. Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8083/api/signals

# 4. Check database performance
psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 5;"
```

## 📊 Monitoring & Dashboards

### Key Dashboards
1. **EAFIX System Overview** - High-level system health
2. **Trading Performance** - Signal generation, execution metrics
3. **Infrastructure Health** - Resource usage, connectivity
4. **Error Tracking** - Error rates, types, trends

### Critical Metrics to Monitor
```yaml
Service Health:
  - up{job="eafix-services"} == 1
  - rate(http_requests_total{status=~"5.."}[5m]) < 0.05

Trading Performance:
  - rate(trading_signals_generated_total[5m]) > 0.1
  - histogram_quantile(0.95, http_request_duration_seconds) < 1.0

Infrastructure:
  - node_memory_usage_bytes / node_memory_total_bytes < 0.8
  - rate(redis_connected_clients[5m]) > 0
```

### Proactive Monitoring Tasks
```bash
# Hourly health check (if no recent alerts)
make smoke

# Check for growing error patterns
python scripts/monitoring/error-trend-analysis.py --period=4h

# Validate recent deployments
python scripts/monitoring/deployment-health-check.py --since=24h

# Check capacity trends
python scripts/monitoring/capacity-trend-check.py --period=7d
```

## 🗣️ Communication Guidelines

### Initial Response Communication
```
Template for #eafix-incidents:
🚨 ALERT: [Alert Name] - [Severity]
Service: [Affected Service]  
Impact: [Brief impact description]
Status: Investigating
Assigned: @[your-username]
ETA: [Initial estimate or "TBD"]
```

### Progress Updates
```
Template for updates (every 15-30 minutes):
🔧 UPDATE: [Alert Name]
Status: [Investigating/Identified/Fixing/Monitoring]
Progress: [What's been done]
Next: [What's being done next]
ETA: [Updated estimate]
```

### Resolution Communication
```
Template for resolution:
✅ RESOLVED: [Alert Name]
Duration: [Total time]
Root Cause: [Brief explanation]
Fix: [What was done]
Prevention: [Steps to prevent recurrence]
```

### Trading Desk Communication
- **When to call**: P0/P1 incidents during market hours (6 AM - 6 PM EST)
- **What to say**: Service affected, impact on trading, expected resolution time
- **Follow-up**: Updates every 15 minutes until resolved

## 🔍 Troubleshooting Quick Reference

### Service Won't Start
```bash
# Check dependencies first
curl http://localhost:6379/  # Redis
psql -h localhost -U eafix -c "SELECT 1;"  # PostgreSQL

# Check configuration
docker compose config --quiet || echo "Configuration error"

# Check resource availability
df -h  # Disk space
free -h  # Memory
```

### High Latency Issues
```bash
# Check system load
uptime

# Check slow database queries
psql -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Check message queue depth
redis-cli llen trading_signals_queue

# Check network connectivity
ping external-api.broker.com
```

### Data Quality Issues
```bash
# Check recent data timestamps
curl http://localhost:8081/api/latest-prices | jq '.[] | {symbol, timestamp, age: (now - (.timestamp | fromdate))}'

# Validate data integrity
make contracts-validate

# Check data source health
curl http://localhost:8081/api/data-sources
```

## 🎯 Escalation Decision Tree

```
Is service completely down?
├─ Yes → P0, escalate to L2 immediately
└─ No → Continue assessment

Is trading affected during market hours?
├─ Yes → P0/P1, notify trading desk
└─ No → Continue assessment

Can you resolve in 30 minutes?
├─ Yes → Continue working, set 30min timer
└─ No → Escalate to L2

Is root cause identified?
├─ Yes → Continue with fix
└─ No → Consider escalation for expertise

Has issue been ongoing >1 hour?
├─ Yes → Escalate to L3
└─ No → Continue assessment
```

## 📚 Knowledge Base

### Common Issues & Solutions

**Issue**: Signal generator not producing signals
**Cause**: Indicator engine not providing data
**Solution**: Check indicator engine health, restart if needed
**Prevention**: Monitor indicator processing latency

**Issue**: Orders not executing
**Cause**: Broker API connectivity issues
**Solution**: Check broker API health, verify credentials
**Prevention**: Monitor broker API response times

**Issue**: Position reconciliation failures
**Cause**: Timing issues between systems
**Solution**: Manual reconciliation, check system clocks
**Prevention**: Implement position sync monitoring

### Useful Commands
```bash
# Quick system overview
make smoke && docker stats --no-stream

# Find recent errors across all services
docker compose logs --since=1h | grep -i error | tail -20

# Check if all services are processing
for service in data-ingestor indicator-engine signal-generator risk-manager execution-engine; do
  echo "$service: $(curl -s http://localhost:808x/metrics | grep -E 'requests_total|processed_total' | tail -1)"
done

# Emergency trading halt
curl -X POST http://localhost:8080/emergency/stop-trading
```

## 🎓 On-Call Training

### Required Knowledge
- EAFIX system architecture overview
- Docker and container management
- Basic database operations (PostgreSQL)
- Linux system administration
- Trading domain basics

### Recommended Training
- Complete incident response simulation
- Shadow experienced on-call engineer
- Review past incident post-mortems
- Practice with monitoring tools

### Continuous Learning
- Monthly post-incident review participation
- Quarterly architecture overview updates
- Annual disaster recovery exercises

## 📋 On-Call Checklist

### Start of Shift
- [ ] Acknowledge on-call status in PagerDuty
- [ ] Review open incidents from previous shift
- [ ] Check system health with `make smoke`
- [ ] Review overnight alerts and trends
- [ ] Verify communication channels working
- [ ] Check scheduled maintenance/deployments
- [ ] Update team on any ongoing issues

### During Shift
- [ ] Respond to alerts within SLA timeframes
- [ ] Document all incidents and actions taken
- [ ] Provide regular updates during active incidents
- [ ] Escalate appropriately when needed
- [ ] Monitor system health trends
- [ ] Update runbooks based on learnings

### End of Shift
- [ ] Hand off any ongoing incidents
- [ ] Update incident documentation
- [ ] Brief incoming on-call on system status
- [ ] Note any concerns or trends observed
- [ ] Clear PagerDuty status
- [ ] File any improvement suggestions

## 🆘 Emergency Contacts

**Primary Escalation**
- Secondary On-Call: +1-555-0124
- Platform Lead: +1-555-0125  

**Specialized Teams**
- Trading Desk (Market Hours): +1-555-0200
- Security Team: +1-555-0300
- DBA Team: +1-555-0400

**Executive Escalation (P0 only)**
- Engineering Manager: +1-555-0126
- VP Engineering: +1-555-0127

---

**Remember**: When in doubt, escalate. It's better to engage additional help than to struggle alone with a critical issue.

**Document Owner**: Platform Engineering Team  
**Last Updated**: December 2024  
**Next Review**: January 2025
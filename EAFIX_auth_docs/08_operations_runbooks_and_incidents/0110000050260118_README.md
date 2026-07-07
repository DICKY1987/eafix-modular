---
doc_id: DOC-DOC-0014
---

# EAFIX Trading System Runbooks

This directory contains operational runbooks for the EAFIX trading system. These runbooks provide step-by-step procedures for common operational tasks, incident response, and system maintenance.

## 🚨 Emergency Contacts & Escalation

**Critical Trading Issues**: Contact trading desk immediately during market hours
**System Outages**: Follow escalation procedures in `incident-response.md`
**Security Incidents**: Invoke security incident response plan immediately

## 📚 Runbook Categories

### Incident Response
- **[incident-response.md](incident-response.md)** - Primary incident response procedures
- **[trading-incidents.md](trading-incidents.md)** - Trading-specific incident handling
- **[security-incidents.md](security-incidents.md)** - Security incident response
- **[escalation-procedures.md](escalation-procedures.md)** - Contact and escalation procedures

### System Operations
- **[service-health.md](service-health.md)** - Health checks and monitoring procedures
- **[deployment.md](deployment.md)** - Deployment and rollback procedures
- **[backup-recovery.md](backup-recovery.md)** - Data backup and recovery procedures
- **[capacity-management.md](capacity-management.md)** - Capacity planning and scaling

### Trading Operations
- **[market-open-close.md](market-open-close.md)** - Market session procedures
- **[position-reconciliation.md](position-reconciliation.md)** - Position reconciliation procedures
- **[signal-validation.md](signal-validation.md)** - Trading signal validation
- **[risk-limit-breach.md](risk-limit-breach.md)** - Risk limit breach response

### Troubleshooting
- **[common-issues.md](common-issues.md)** - Common issues and solutions
- **[performance-issues.md](performance-issues.md)** - Performance troubleshooting
- **[data-quality.md](data-quality.md)** - Data quality issue resolution
- **[connectivity-issues.md](connectivity-issues.md)** - Network and connectivity issues

### Maintenance
- **[scheduled-maintenance.md](scheduled-maintenance.md)** - Planned maintenance procedures
- **[database-maintenance.md](database-maintenance.md)** - Database maintenance tasks
- **[log-rotation.md](log-rotation.md)** - Log management and rotation
- **[certificate-renewal.md](certificate-renewal.md)** - Certificate management

## 🔧 Quick Reference

### Service Status Commands
```bash
# Check all service health
make smoke

# Check specific service
curl http://localhost:8080/healthz  # GUI Gateway
curl http://localhost:8081/healthz  # Data Ingestor
curl http://localhost:8082/healthz  # Indicator Engine
curl http://localhost:8083/healthz  # Signal Generator
curl http://localhost:8084/healthz  # Risk Manager

# Check Docker container status
docker compose -f deploy/compose/docker-compose.yml ps
```

### Emergency Commands
```bash
# Stop all trading (emergency)
curl -X POST http://localhost:8080/emergency/stop-trading

# Restart all services
make docker-down && make docker-up

# Check recent errors
docker compose -f deploy/compose/docker-compose.yml logs --tail=100 --since=1h

# Validate system integrity
make contracts-validate-full
```

### Monitoring Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Service Health**: http://localhost:8080/health

## 📋 On-Call Procedures

### Primary Response (0-15 minutes)
1. Acknowledge alert within 5 minutes
2. Assess severity using incident classification
3. Begin initial triage and containment
4. Notify secondary on-call if P0/P1 incident

### Secondary Response (15-60 minutes)
1. Detailed investigation and diagnosis
2. Implement temporary fixes if possible
3. Escalate to development team if needed
4. Document findings and actions taken

### Follow-up (60+ minutes)
1. Implement permanent fixes
2. Conduct post-incident review
3. Update runbooks based on learnings
4. Communicate resolution to stakeholders

## 🎯 Incident Classifications

### P0 - Critical (Response: Immediate)
- Complete system outage
- Data corruption or loss
- Security breach
- Trading halt required

### P1 - High (Response: 15 minutes)
- Partial system outage
- Significant performance degradation
- Failed position reconciliation
- Risk limit breaches

### P2 - Medium (Response: 1 hour)
- Service degradation
- Non-critical feature failure
- Data quality issues
- Monitoring alerts

### P3 - Low (Response: Next business day)
- Minor bugs
- Documentation issues
- Enhancement requests
- Cosmetic issues

## 🔍 Diagnostic Tools

### Health Checks
```bash
# System health overview
curl http://localhost:8080/health | jq .

# Database connectivity
psql -h localhost -p 5432 -U eafix -d eafix_prod -c "SELECT version();"

# Redis connectivity
redis-cli -h localhost -p 6379 ping

# Message bus status
redis-cli -h localhost -p 6379 info replication
```

### Performance Monitoring
```bash
# Service response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8080/healthz

# Resource usage
docker stats

# Database performance
psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### Log Analysis
```bash
# Search for errors in last hour
docker compose logs --since=1h | grep -i error

# Trading-specific logs
docker compose logs signal-generator --since=30m | grep -i "signal"

# Performance logs
docker compose logs --since=1h | grep -E "(slow|timeout|latency)"
```

## 📚 Reference Materials

### Architecture Documentation
- System architecture diagrams in `/docs/architecture/`
- Service API documentation in `/docs/api/`
- Database schema in `/docs/database/`

### Configuration Files
- Docker Compose: `/deploy/compose/docker-compose.yml`
- Kubernetes: `/deploy/k8s/`
- Environment variables: `.env` files per service

### Monitoring Configuration
- Prometheus configuration: `/deploy/monitoring/prometheus/`
- Grafana dashboards: `/deploy/monitoring/grafana/`
- Alert rules: `/deploy/monitoring/alerts/`

## 🚀 Getting Help

### Internal Resources
- **Development Team**: #eafix-dev Slack channel
- **Operations Team**: #eafix-ops Slack channel  
- **Trading Desk**: Direct phone line during market hours

### External Resources
- **Cloud Provider**: AWS Support (Enterprise)
- **Database**: PostgreSQL community forums
- **Monitoring**: Prometheus/Grafana documentation

### Emergency Escalation
1. **Immediate**: Page on-call engineer (PagerDuty)
2. **15 minutes**: Escalate to senior engineer
3. **30 minutes**: Escalate to engineering manager
4. **1 hour**: Escalate to CTO for P0 incidents

## 📝 Runbook Maintenance

### Regular Updates
- Review and update runbooks monthly
- Test procedures during game day exercises
- Incorporate learnings from incidents
- Keep contact information current

### Quality Standards
- All procedures must be tested
- Include expected outcomes and timings
- Provide rollback procedures
- Use clear, actionable language

### Version Control
- All runbooks are version controlled
- Changes require peer review
- Tag versions for releases
- Maintain change log

---

**Last Updated**: December 2024  
**Next Review**: January 2025  
**Owner**: Platform Engineering Team  
**Reviewers**: Trading Operations, Security Team